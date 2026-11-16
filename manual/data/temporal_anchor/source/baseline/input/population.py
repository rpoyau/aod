"""Finite population-driven closure dynamics with exact source-bound admission."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field, replace
from fractions import Fraction as Q
import gzip
import hashlib
import heapq
import io
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "upstream/manual/scripts"))
import aod_native_closure_wave as n

SCOPE = "declared:population-coupled:common-scope"
CS = Q(9192631770)
START = 2000


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def plain(obj):
    return json.loads(canonical(obj))


def check_sources():
    binding = json.loads((HERE / "SOURCE_BINDING.json").read_text())
    for name, expected in binding["sha256"].items():
        require(hashlib.sha256((HERE / "upstream" / name).read_bytes()).hexdigest() == expected,
                "upstream source changed: " + name)
    return binding


def catalogue(p, q):
    words = [("word", *word) for word in product(range(q), repeat=p)]
    shell = [("shell", axis) for axis in range(q)]
    return tuple(words + shell)


def route(p, q):
    cat = catalogue(p, q)
    axes = [item[-1] for item in cat]
    vertex = 0
    vertices = [vertex]
    for axis in axes + list(reversed(axes)):
        vertex ^= 1 << axis
        vertices.append(vertex)
    require(vertex == 0 and all(n.hamming(a, b) == 1 for a, b in zip(vertices, vertices[1:])),
            "route must return through Hamming-1 edges")
    return cat, tuple(vertices)


def trace_with_indices(lineage, occurrence, vertices, indices, turn):
    t = n.trace(lineage, occurrence, vertices=vertices, scope=SCOPE,
                turn=turn, start_index=indices[0])
    witness = replace(t.reflection, committed_at=indices[-1],
                      turnaround_committed_at=indices[turn])
    t = replace(t, indices=tuple(indices), reflection=witness)
    n.validate_trace(t)
    return t


def support_indices(start, branch, extra=0):
    # One hinge event and any extra directional reflection events occur
    # between the outward endpoint and the first returned traversal.
    return [start + i + (1 + extra if i > branch else 0) for i in range(2 * branch + 1)]


@dataclass
class Node:
    name: str
    p: int
    q: int
    records: list = field(default_factory=list)
    motifs: list = field(default_factory=list)
    returns: list = field(default_factory=list)
    prefix_hashes: list = field(default_factory=list)
    current_indices: list = field(default_factory=list)
    action: int = -1
    occurrence: int = 2
    due: int = START
    pressure_used: int = 1
    pressure_bindings: tuple = ()

    def __post_init__(self):
        self.cat, self.vertices = route(self.p, self.q)
        self.branch = len(self.cat)
        self.rd = self.branch + 1 + self.branch
        require(self.rd == n.rd(self.p, self.q), "enumerated support and RD reduction disagree")
        self.lineage = "population:" + self.name
        ts = [n.trace(self.lineage, j, scope=SCOPE, start_index=3*j) for j in range(self.q)]
        self.components = tuple((tr, n.certify(tr)) for tr in ts)
        ids = tuple(c.return_id for _, c in self.components)
        self.construction = (tuple(ids for _ in range(self.p)), ids)
        for occurrence in range(2):
            start = 30 + occurrence * (self.rd + 3)
            tr = trace_with_indices(self.lineage, occurrence, self.vertices,
                                    support_indices(start, self.branch), self.branch)
            self.add_return(tr)
        self.identity = self.wave().identity

    def add_return(self, tr):
        c = n.certify(tr)
        registry = {x.certificate_digest: x for _, x in self.components}
        registry[c.certificate_digest] = c
        witness = n.motif_witness(f"{self.p}:{self.q}", tr, self.construction,
                                  self.components, registry, enclosure=6)
        self.records.append((tr, c, registry))
        self.motifs.append(witness)
        self.returns.append(tr.indices[-1])
        self.prefix_hashes.append(tr.trace_digest)

    def wave(self):
        return n.wave(self.records, tuple(self.motifs))

    def prefix(self, cut):
        return n.digest(tuple(tr.trace_digest for tr, _, _ in self.records if tr.indices[-1] <= cut))

    def count(self, lo, hi):
        return sum(lo < k <= hi for k in self.returns[1:])

    def phases(self):
        return len(self.returns) - 1


@dataclass
class Channel:
    receiver: str
    sender: str
    contacts: list = field(default_factory=list)
    evidence: list = field(default_factory=list)

    def pressure(self, nodes):
        if len(self.contacts) < 2:
            return 0, None
        latest = self.contacts[-2:]
        source = nodes[self.sender]
        rcd = n.RCD(nodes[self.receiver].identity, source.identity, SCOPE,
                    tuple(c.identity for c in latest), source.rd,
                    tuple(c.reflection[0] for c in latest))
        return rcd.duration(), {"channel": [self.receiver, self.sender],
                                "rcd": asdict(rcd), "rho": rcd.duration()}


class Engine:
    def __init__(self, scenario, intervention, output=None, trace=True):
        self.scenario = scenario
        self.intervention = intervention
        local_q = 3 if scenario == "plus_336" else 4
        self.nodes = {name: Node(name, p, q) for name, p, q in
                      (("P", 3, 2), ("R", 3, 3), ("B0", 3, 4), ("B1", 3, 4),
                       ("L0", 3, local_q), ("L1", 3, 4))}
        self.base = ("P", "R", "B0", "B1")
        self.channels = {}
        self.active = set()
        self.heap = []
        self.serial = 0
        self.pending = {}
        self.returned_packets = []
        self.steps = {name: [] for name in self.nodes}
        self.pressure_changes = []
        self.last_pressure = {}
        self.common_prefix_hash = hashlib.sha256()
        self.observable_hash = hashlib.sha256()
        self.trace_count = 0
        self.trace_path = output
        self.trace = trace
        self.raw_writer = open(output, "wb") if output and trace else None
        self.writer = (io.TextIOWrapper(gzip.GzipFile(filename="", mode="wb", fileobj=self.raw_writer,
                                                     mtime=0), encoding="utf-8") if self.raw_writer else None)
        self.first_operational_local_contact = None
        self.record_count = 0
        self.feedback_disabled = scenario == "feedback_disabled"
        for receiver in self.base:
            for sender in self.base:
                if receiver != sender:
                    self.activate(receiver, sender)
                    for start in (700, 1200):
                        self.seed_contact(receiver, sender, start)
        for node in (self.nodes[name] for name in self.base):
            self.push(node.due, "node", node.name)
        self.push(intervention, "intervention", None)

    def push(self, cut, kind, payload):
        self.serial += 1
        heapq.heappush(self.heap, (cut, self.serial, kind, payload))

    def log(self, row):
        self.trace_count += 1
        if self.writer:
            self.writer.write(json.dumps(row, separators=(",", ":"), default=str) + "\n")

    def activate(self, receiver, sender):
        key = (receiver, sender)
        self.active.add(key)
        self.channels.setdefault(key, Channel(receiver, sender))

    def make_contact(self, receiver, sender, start, reflection, identity):
        a, b = self.nodes[receiver], self.nodes[sender]
        indices = support_indices(start, b.branch, reflection[0])
        tr = trace_with_indices(a.identity + "|" + b.identity, identity, b.vertices,
                                indices, b.branch)
        cut = indices[-1]
        contact = n.Contact(identity, a.identity, b.identity, SCOPE, cut,
                            a.prefix(cut), b.prefix(cut), tuple(reflection), tr, n.certify(tr))
        return contact

    def seed_contact(self, receiver, sender, start):
        contact = self.make_contact(receiver, sender, start, (0, 0), f"seed:{receiver}:{sender}:{start}")
        ch = self.channels[(receiver, sender)]
        ch.contacts.append(contact)
        ch.evidence.append({"id": contact.identity, "seed": True,
                            "start": start, "arrived": contact.committed,
                            "base_RD": self.nodes[sender].rd, "reflection": [0, 0]})

    def pressure(self, receiver):
        own = self.nodes[receiver].rd
        terms = [{"self": receiver, "RD": own, "rho": own}]
        total = own
        for key in sorted(self.active):
            if key[0] != receiver:
                continue
            rho, record = self.channels[key].pressure(self.nodes)
            if record is None:
                continue
            if self.feedback_disabled and "L0" in key:
                continue
            total += rho
            terms.append(record)
        return total, tuple(terms)

    def intervene(self, cut):
        connect = []
        if self.scenario in ("plus_346", "plus_336", "feedback_disabled", "restore_346"):
            connect = ["L0"]
        elif self.scenario == "plus_346_both":
            connect = ["L0"]
        elif self.scenario == "plus_two_346":
            connect = ["L0", "L1"]
        present = connect or (["L0"] if self.scenario == "uncoupled_346" else [])
        for local in present:
            self.nodes[local].due = cut + 1
            self.push(cut+1, "node", local)
        for local in connect:
            self.activate("P", local)
            self.activate(local, "P")
            if self.scenario == "plus_346_both":
                self.activate("R", local)
                self.activate(local, "R")
        self.log([cut, "population_intervention", self.scenario, connect,
                  "background_346_retained", ["B0", "B1"]])

    def node_action(self, cut, name):
        node = self.nodes[name]
        require(cut == node.due, "stale scheduled traversal")
        action = node.action
        if action == -1:
            node.current_indices = [cut]
            node.action = 0
            event = [cut, "start", name, node.occurrence, node.pressure_used]
        elif action == node.branch:
            node.action += 1
            event = [cut, "hinge", name, node.occurrence, node.pressure_used]
        else:
            node.current_indices.append(cut)
            node.action += 1
            index = len(node.current_indices) - 1
            a, b = node.vertices[index-1:index+1]
            require(n.hamming(a, b) == 1, "non-H1 dynamics")
            event = [cut, "edge", name, node.occurrence, index, a, b, node.pressure_used]
        completed = node.action == node.rd
        if completed:
            tr = trace_with_indices(node.lineage, node.occurrence, node.vertices,
                                    node.current_indices, node.branch)
            node.add_return(tr)
            self.log([cut, "certified_reclosure", name, node.occurrence,
                      tr.return_id, node.motifs[-1].witness_digest])
            node.occurrence += 1
            node.action = -1
        self.log(event)
        if name in self.base:
            self.observable_hash.update(canonical(event) + b"\n")
            if cut < self.intervention:
                self.common_prefix_hash.update(canonical(event) + b"\n")
        self.steps[name].append((cut, event[1], node.pressure_used))
        return completed

    def emit(self, cut, sender):
        source = self.nodes[sender]
        for receiver, source_name in sorted(self.active):
            if source_name != sender:
                continue
            target = self.nodes[receiver]
            lag = target.phases() - source.phases()
            reflection = (max(0, lag), max(0, -lag))
            self.record_count += 1
            identity = f"return:{sender}:{receiver}:{self.record_count}"
            packet = {"id": identity, "sender": sender, "receiver": receiver,
                      "emitted": cut, "starts": cut+1, "base_RD": source.rd,
                      "reflection": list(reflection), "lag_at_emission": lag,
                      "source_phase": source.phases(), "receiver_phase": target.phases(),
                      "source_return": source.records[-1][0].return_id,
                      "source_prefix": source.prefix(cut), "receiver_prefix": target.prefix(cut),
                      "arrives": cut+1+source.rd+reflection[0]}
            self.pending[identity] = packet
            self.push(packet["arrives"], "arrival", identity)
            self.log([cut, "return_emitted", packet])

    def arrive(self, cut, identity):
        packet = self.pending.pop(identity)
        require(packet["emitted"] < packet["starts"] < cut, "noncausal returned contact")
        receiver, sender = packet["receiver"], packet["sender"]
        contact = self.make_contact(receiver, sender, packet["starts"], packet["reflection"], identity)
        require(contact.committed == cut, "RCD transport duration mismatch")
        ch = self.channels[(receiver, sender)]
        ch.contacts.append(contact)
        ch.evidence.append(packet)
        self.returned_packets.append(packet)
        if "L0" in (receiver, sender) and len(ch.contacts) >= 2 and self.first_operational_local_contact is None:
            self.first_operational_local_contact = cut
        self.log([cut, "contact_returned", identity, receiver, sender,
                  n.digest(asdict(contact)), len(ch.contacts)])

    def schedule(self, cut, name, completed):
        node = self.nodes[name]
        pressure, terms = self.pressure(name)
        binding = digest(terms)
        if self.last_pressure.get(name) != (pressure, binding):
            change = {"cut": cut, "field": name, "pressure": pressure,
                      "terms": terms, "sha256": binding}
            self.pressure_changes.append(change)
            self.last_pressure[name] = (pressure, binding)
            self.log([cut, "pressure_committed", name, pressure, binding])
        node.pressure_used = pressure
        node.pressure_bindings = terms
        # The next start marker is a distinct later event. Traversals consume
        # the newly committed positive integer pressure response interval.
        node.due = cut + (1 if completed else pressure)
        self.push(node.due, "node", name)

    def run(self, end):
        while self.heap and self.heap[0][0] <= end:
            cut = self.heap[0][0]
            batch = []
            while self.heap and self.heap[0][0] == cut:
                batch.append(heapq.heappop(self.heap))
            done = []
            for _, _, kind, payload in batch:
                if kind == "intervention":
                    self.intervene(cut)
            for _, _, kind, payload in batch:
                if kind == "node":
                    done.append((payload, self.node_action(cut, payload)))
            for _, _, kind, payload in batch:
                if kind == "arrival":
                    self.arrive(cut, payload)
            for name, completed in done:
                if completed:
                    self.emit(cut, name)
            for name, completed in done:
                self.schedule(cut, name, completed)
        if self.writer:
            self.writer.close()
            self.raw_writer.close()
            self.writer = None
        return self

    def validate(self, end):
        waves = {name: node.wave() for name, node in self.nodes.items()}
        for name, wave in waves.items():
            n.validate_wave(wave)
            require(wave.motif == f"{self.nodes[name].p}:{self.nodes[name].q}", "motif lost")
            require(all(m.enclosure == 6 for m in wave.motif_witnesses), "enclosure lost")
        for (receiver, sender), ch in self.channels.items():
            if len(ch.contacts) < 2:
                continue
            a, b = waves[receiver], waves[sender]
            result = n.compare(a, b, tuple(ch.contacts), (0, end))
            require(result["rcd"].support == self.nodes[sender].rd,
                    "contact support differs from enumerated source RD")
            latest = n.compare(a, b, tuple(ch.contacts[-2:]), (0, end))
            require(latest["duration"] == ch.pressure(self.nodes)[0], "operative RCD mismatch")
        for packet in self.returned_packets:
            src, dst = self.nodes[packet["sender"]], self.nodes[packet["receiver"]]
            cut = packet["emitted"]
            require(packet["source_prefix"] == src.prefix(cut) and packet["receiver_prefix"] == dst.prefix(cut),
                    "emission used a substituted prefix")
            require(packet["source_phase"] == src.count(-1, cut) and packet["receiver_phase"] == dst.count(-1, cut),
                    "emission used uncommitted phases")
        return waves

    def summary(self, end):
        counts = {name: node.count(self.intervention, end) for name, node in self.nodes.items()}
        calibration_count = self.nodes["R"].count(START, self.intervention)
        require(calibration_count > 0 and counts["R"] > 0, "reference must recur in calibration and report windows")
        dt = Q(2 * counts["R"], 9192631770)
        return {"scenario": self.scenario, "window": [self.intervention, end],
                "counts": counts, "probe_reference_ratio": str(Q(counts["P"], counts["R"])),
                "conditional_elapsed_seconds": str(dt),
                "conditional_probe_rate_hz": str(Q(counts["P"])/dt),
                "calibration_reference_reclosures": calibration_count,
                "synthetic_calibration_cycles": 2*calibration_count,
                "frozen_gain": "2", "physical_Cs_observation_law": "not supplied",
                "base_prefix_sha256": self.common_prefix_hash.hexdigest(),
                "base_execution_sha256": self.observable_hash.hexdigest(),
                "first_operational_local_contact": self.first_operational_local_contact,
                "pending_return_count": len(self.pending), "returned_contact_count": len(self.returned_packets),
                "trace_rows": self.trace_count,
                "last_pressure": {name: self.pressure(name)[0] for name in self.nodes},
                "next_scheduled": {name: node.due for name, node in self.nodes.items()}}
