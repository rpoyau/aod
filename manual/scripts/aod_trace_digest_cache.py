"""Bounded, value-keyed digest reuse for the single-threaded anchor replay.

Every miss invokes the original Trace.trace_digest getter. Admission and witness
validation are untouched. Keys contain only copied, typed builtin values; no
trace or mutable object is retained. Unsupported values use the original getter.
The pickle bytes are an in-process key only and are never deserialized or used
as an AOD identity. Canonical digest bytes still come from the original getter.
"""
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import fields
from pathlib import Path
import pickle
import runpy
import sys
from threading import RLock, get_ident

_CACHE_LOCK = RLock()


_TRACE_FIELDS = ('scope', 'scale', 'lineage', 'event_ids', 'vertices', 'indices',
                 'roles', 'turn', 'ancestor', 'reflection', 'reflected_comparison')
_REFLECTION_FIELDS = ('scope', 'lineage', 'turnaround_id', 'outbound_ids',
                      'return_ids', 'target_start_id', 'committed_at',
                      'turnaround_committed_at')


def _primitive_tuple(value, item_type):
    return type(value) is tuple and all(type(item) is item_type for item in value)


def _key(trace, trace_type, reflection_type):
    if type(trace) is not trace_type:
        return None
    if not (all(type(getattr(trace, name)) is str for name in ('scope', 'lineage', 'ancestor'))
            and all(type(getattr(trace, name)) is int for name in ('scale', 'turn'))
            and type(trace.reflected_comparison) is bool
            and _primitive_tuple(trace.event_ids, str)
            and all(_primitive_tuple(getattr(trace, name), int)
                    for name in ('vertices', 'indices', 'roles'))):
        return None
    reflection = trace.reflection
    if reflection is not None:
        if not (type(reflection) is reflection_type
                and all(type(getattr(reflection, name)) is str
                        for name in ('scope', 'lineage', 'turnaround_id', 'target_start_id'))
                and all(type(getattr(reflection, name)) is int
                        for name in ('committed_at', 'turnaround_committed_at'))
                and all(_primitive_tuple(getattr(reflection, name), str)
                        for name in ('outbound_ids', 'return_ids'))):
            return None
        reflection = tuple(getattr(reflection, name) for name in _REFLECTION_FIELDS)
    values = tuple(reflection if name == 'reflection' else getattr(trace, name)
                   for name in _TRACE_FIELDS)
    return pickle.dumps(values, protocol=5)


@contextmanager
def trace_digest_cache(module, *, max_entries=16384, max_key_bytes=16 * 1024 * 1024,
                       max_entry_bytes=64 * 1024):
    """Temporarily reuse exact digests, restoring the descriptor on every exit.

    Retained keys are bounded by max_key_bytes; entry count bounds dict metadata
    and digest strings separately. Oversize serialized keys are never retained.
    This bounds retained cache storage, not transient serialization or model RAM.
    Contexts serialize descriptor ownership; unrelated threads use the original
    getter without entering or waiting on this cache. Same-thread nesting is safe.
    """
    for value in (max_entries, max_key_bytes, max_entry_bytes):
        if type(value) is not int or value <= 0:
            raise ValueError('positive integer cache bounds required')
    with _CACHE_LOCK:
        trace_type, reflection_type = module.Trace, module.ReflectionWitness
        original = trace_type.trace_digest
        owner = get_ident()
        supported = (tuple(field.name for field in fields(trace_type)) == _TRACE_FIELDS
                     and tuple(field.name for field in fields(reflection_type)) == _REFLECTION_FIELDS)
        cache = OrderedDict()
        used_bytes = 0
        stats = dict(hits=0, misses=0, fallbacks=0, evictions=0,
                     peak_entries=0, peak_key_bytes=0)

        def cached(trace):
            nonlocal used_bytes
            if get_ident() != owner:
                return original.fget(trace)
            key = _key(trace, trace_type, reflection_type) if supported else None
            if key is None or len(key) > min(max_entry_bytes, max_key_bytes):
                stats['fallbacks'] += 1
                return original.fget(trace)
            if key in cache:
                stats['hits'] += 1
                cache.move_to_end(key)
                return cache[key]
            stats['misses'] += 1
            result = original.fget(trace)
            while cache and (len(cache) >= max_entries or used_bytes + len(key) > max_key_bytes):
                evicted, _ = cache.popitem(last=False)
                used_bytes -= len(evicted)
                stats['evictions'] += 1
            cache[key] = result
            used_bytes += len(key)
            stats['peak_entries'] = max(stats['peak_entries'], len(cache))
            stats['peak_key_bytes'] = max(stats['peak_key_bytes'], used_bytes)
            return result

        trace_type.trace_digest = property(cached, doc=original.__doc__)
        try:
            yield stats
        finally:
            trace_type.trace_digest = original
            cache.clear()


def historical_audit(folder, output):
    """Run the authenticated audit bytes under the digest-only adapter.

    The caller authenticates the archive before extraction; the audit also checks
    its own inputs. Its validators, computations and output comparisons remain.
    """
    folder, output = Path(folder).resolve(), Path(output).resolve()
    sys.path.insert(0, str(folder / 'baseline'))
    import si_bridge
    script = folder / 'audit_anchor.py'
    sys.argv = [str(script), '--output', str(output)]
    with trace_digest_cache(si_bridge.p.n):
        runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: aod_trace_digest_cache.py HISTORICAL_FOLDER OUTPUT')
    historical_audit(*sys.argv[1:])
