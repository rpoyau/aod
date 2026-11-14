"""Digest reuse preserves exact values, mutation checks and bounded lifetime."""
from dataclasses import replace
from pathlib import Path
import sys
from threading import Event, Thread
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'manual/scripts'))
import aod_native_closure_wave as n
from aod_trace_digest_cache import trace_digest_cache


class TraceDigestCacheTests(unittest.TestCase):
    def test_exact_values_and_equivalent_objects_reuse_digest(self):
        traces = [n.trace('cache-fixture', k) for k in range(8)]
        expected = [t.trace_digest for t in traces]
        with trace_digest_cache(n) as stats:
            self.assertEqual([t.trace_digest for t in traces], expected)
            self.assertEqual([replace(t).trace_digest for t in traces], expected)
            self.assertEqual(stats['misses'], 8)
            self.assertEqual(stats['hits'], 8)

    def test_changed_value_and_hostile_frozen_mutation_do_not_reuse_old_digest(self):
        t = n.trace('mutated-cache')
        certificate = n.certify(t)
        getter = n.Trace.trace_digest.fget
        with trace_digest_cache(n) as stats:
            original = t.trace_digest
            object.__setattr__(t, 'vertices', (0, 2, 0))
            self.assertNotEqual(t.trace_digest, original)
            self.assertEqual(t.trace_digest, getter(t))
            with self.assertRaises(n.AdmissionError):
                n.admitted(t, certificate, {certificate.certificate_digest: certificate})
            self.assertGreaterEqual(stats['misses'], 2)

    def test_reflection_mutation_is_snapshotted_by_value(self):
        t = n.trace('reflection-cache')
        getter = n.Trace.trace_digest.fget
        with trace_digest_cache(n):
            original = t.trace_digest
            object.__setattr__(t.reflection, 'turnaround_id', 'changed')
            self.assertNotEqual(t.trace_digest, original)
            self.assertEqual(t.trace_digest, getter(t))
            with self.assertRaises(n.AdmissionError):
                n.validate_trace(t)

    def test_boolean_integer_and_signed_float_zero_fall_back_exactly(self):
        t = n.trace('typed-cache')
        variants = [replace(t, scale=True), replace(t, scale=1),
                    replace(t, scale=0.0), replace(t, scale=-0.0)]
        expected = [item.trace_digest for item in variants]
        self.assertNotEqual(expected[0], expected[1])
        self.assertNotEqual(expected[2], expected[3])
        with trace_digest_cache(n) as stats:
            self.assertEqual([item.trace_digest for item in variants], expected)
            self.assertEqual(stats['fallbacks'], 3)
            self.assertEqual(stats['misses'], 1)

    def test_nested_mutable_values_never_enter_cache(self):
        t = replace(n.trace('mutable-cache'), vertices=[0, 1, 0])
        getter = n.Trace.trace_digest.fget
        with trace_digest_cache(n) as stats:
            original = t.trace_digest
            t.vertices[1] = 2
            self.assertNotEqual(t.trace_digest, original)
            self.assertEqual(t.trace_digest, getter(t))
            self.assertEqual(stats['peak_entries'], 0)
            self.assertEqual(stats['fallbacks'], 3)

    def test_entry_and_key_byte_bounds_evict_and_oversize_falls_back(self):
        traces = [n.trace('bounded-cache', k) for k in range(5)]
        expected = [t.trace_digest for t in traces]
        with trace_digest_cache(n, max_entries=2, max_key_bytes=1024) as stats:
            self.assertEqual([t.trace_digest for t in traces], expected)
            self.assertEqual([t.trace_digest for t in traces], expected)
            self.assertLessEqual(stats['peak_entries'], 2)
            self.assertLessEqual(stats['peak_key_bytes'], 1024)
            self.assertGreater(stats['evictions'], 0)
        with trace_digest_cache(n, max_entry_bytes=1) as stats:
            self.assertEqual([t.trace_digest for t in traces], expected)
            self.assertEqual(stats['peak_entries'], 0)
            self.assertEqual(stats['fallbacks'], 5)

    def test_descriptor_restores_after_exception_and_nested_context(self):
        descriptor = n.Trace.trace_digest
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            with trace_digest_cache(n):
                outer = n.Trace.trace_digest
                with trace_digest_cache(n):
                    self.assertEqual(n.trace().trace_digest, descriptor.fget(n.trace()))
                self.assertIs(n.Trace.trace_digest, outer)
                raise RuntimeError('stop')
        self.assertIs(n.Trace.trace_digest, descriptor)

    def test_invalid_limits_are_rejected_before_descriptor_change(self):
        descriptor = n.Trace.trace_digest
        for value in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                with trace_digest_cache(n, max_entries=value):
                    self.fail('invalid cache bound admitted')
        self.assertIs(n.Trace.trace_digest, descriptor)

    def test_overlapping_threads_restore_descriptor_and_nonowner_calls_do_not_wait(self):
        descriptor = n.Trace.trace_digest
        trace = n.trace('thread-cache')
        expected = trace.trace_digest
        first_entered, release_first = Event(), Event()
        nonowner_done, second_entered, release_second = Event(), Event(), Event()
        failures = []

        def first():
            try:
                with trace_digest_cache(n):
                    first_entered.set()
                    if not release_first.wait(5):
                        raise RuntimeError('first context was not released')
            except BaseException as exc:
                failures.append(exc)

        def second():
            try:
                if trace.trace_digest != expected:
                    raise RuntimeError('nonowner digest differs')
                nonowner_done.set()
                with trace_digest_cache(n):
                    second_entered.set()
                    if not release_second.wait(5):
                        raise RuntimeError('second context was not released')
                    if trace.trace_digest != expected:
                        raise RuntimeError('second context digest differs')
            except BaseException as exc:
                failures.append(exc)

        a, b = Thread(target=first), Thread(target=second)
        try:
            a.start()
            self.assertTrue(first_entered.wait(5))
            b.start()
            self.assertTrue(nonowner_done.wait(5))
            self.assertFalse(second_entered.wait(0.1))
            release_first.set()
            a.join(5)
            self.assertTrue(second_entered.wait(5))
            release_second.set()
            b.join(5)
            self.assertFalse(a.is_alive() or b.is_alive())
            self.assertEqual(failures, [])
            self.assertIs(n.Trace.trace_digest, descriptor)
        finally:
            release_first.set()
            release_second.set()
            a.join(5)
            if b.ident is not None:
                b.join(5)


if __name__ == '__main__':
    unittest.main()
