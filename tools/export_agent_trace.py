"""Record real runs of agent-consult for the agent room on the portfolio.

    python tools/export_agent_trace.py --agent-consult ../agent-consult

The agent room replays what this script records; it does not simulate anything.
Each run below drives the agent-consult library (github.com/darshan2209/agent-consult)
through one Coordinator and writes every step to assets/agent-room.js:

  case     the operator's grant is narrowed, delegated and refused, then the panel
           deliberates on CR-2291, splits, reconciles and escalates to a person.
  branches the person's two possible calls, each a separate run of the same case:
           overrule protection's objection, or let it stand.
  outage   the same request with the protection agent offline, so the answer
           narrows and says what it no longer covers.

The library's agents are deterministic, so every run reproduces exactly; the script
checks that both branch runs share an identical prefix before writing anything.
Steps are numbered by the library's own ledger. Labels such as "cue" are added here
so the page can attach a caption to each step; they never alter the recorded text.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "agent-room.js")
ENGINEER = "grid duty engineer"


def load_library(path):
    sys.path.insert(0, os.path.abspath(path))
    import agent_consult  # noqa: F401  (import check only)
    from agent_consult.coordinator import Coordinator
    from agent_consult.grants import Grant, GrantError, PolicyDenied
    from agent_consult.scenario import ASPECTS, PROPOSITION, facts, panel
    return Coordinator, Grant, GrantError, PolicyDenied, ASPECTS, PROPOSITION, facts, panel


def commit_of(path):
    try:
        return subprocess.check_output(
            ["git", "-C", path, "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def entry_beat(e, cue, **extra):
    beat = {"t": "entry", "cue": cue, "id": e.id, "kind": e.kind, "actor": e.actor, "text": e.summary}
    if e.refers_to:
        beat["refers"] = e.refers_to
    if e.kind == "verdict":
        beat["pos"] = e.detail["position"]
        beat["ev"] = e.detail["evidence"]
    if e.kind == "unavailable" and "lost" in e.detail:
        beat["lost"] = e.detail["lost"]
    beat.update(extra)
    return beat


def deliberation_beats(lib, co, start, prefix=""):
    """Turn the entries a deliberate() call appended into beats."""
    Coordinator, Grant, GrantError, PolicyDenied, ASPECTS, PROPOSITION, facts, panel = lib
    outcome = co.deliberate(PROPOSITION)
    entries = co.ledger.entries[start:]
    split = outcome.disagreements[0] if outcome.disagreements else None
    beats, positions, splits_seen = [], {}, 0
    for e in entries:
        if e.kind in ("verdict", "scope", "unavailable"):
            if e.kind == "verdict":
                positions[e.actor] = e.detail["position"]
            beats.append(entry_beat(e, "%s:%s" % (e.kind, e.actor)))
        elif e.kind == "disagreement":
            splits_seen += 1
            if splits_seen == 1:
                sup = [a for a, p in positions.items() if p == "supports"]
                opp = [a for a, p in positions.items() if p == "opposes"]
                beats.append(entry_beat(e, prefix + "split", sup=sup, opp=opp))
            else:
                beats.append(entry_beat(e, "restate", sup=list(split.supporting), opp=list(split.opposing)))
        elif e.kind == "reconciled":
            beats.append(entry_beat(e, "reconciled", sup=[a for a, p in positions.items() if p != "abstains"], opp=[]))
        elif e.kind == "escalation":
            beats.append(entry_beat(e, "escalation", q=split.question_for_human))
        elif e.kind == "outcome":
            beats.append(entry_beat(e, prefix + "outcome", status=outcome.status, position=outcome.position,
                                    unsupported=outcome.unsupported))
        else:  # question, reconcile
            beats.append(entry_beat(e, prefix + e.kind if e.kind == "question" else e.kind))
    return beats, outcome


def case_run(lib, branch):
    Coordinator, Grant, GrantError, PolicyDenied, ASPECTS, PROPOSITION, facts, panel = lib
    co = Coordinator(panel(), facts(fault_margin_ka=-0.4), ASPECTS)
    beats = []

    def last(cue, **extra):
        beats.append(entry_beat(co.ledger.entries[-1], cue, **extra))

    # 1. Authority: a grant that names its purpose, narrowed before it is spent.
    grant = Grant(
        issuer="operator",
        audience="regulatory",
        scope=["read:meter_summary", "read:customer_record"],
        purpose="check that this connection request has a complete metering history",
        issued_at=0,
        ttl=50,
    )
    beats.append({"t": "grant", "cue": "grant:operator>regulatory", "from": "operator", "to": "regulatory",
                  "scope": sorted(grant.scope), "chain": list(grant.act_chain), "text": grant.describe()})
    onward = grant.attenuate(audience="regulatory", scope=["read:meter_summary"],
                             purpose="confirm 24 months of meter data with no gaps", step=co.step)
    beats.append({"t": "narrow", "cue": "narrow:regulatory", "holder": "regulatory",
                  "scope": sorted(onward.scope), "dropped": sorted(grant.scope - onward.scope),
                  "chain": list(onward.act_chain), "text": onward.describe()})
    value = co.consult("regulatory", "records", "read:meter_summary", onward)
    last("consult:regulatory>records", to="records", value=value)

    third = onward.attenuate(audience="capacity", scope=["read:meter_summary"],
                             purpose="check the export profile before judging headroom", step=co.step)
    beats.append({"t": "grant", "cue": "grant:regulatory>capacity", "from": "regulatory", "to": "capacity",
                  "scope": sorted(third.scope), "chain": list(third.act_chain), "text": third.describe()})
    co.consult("capacity", "records", "read:meter_summary", third)
    last("consult:capacity>records", to="records")

    try:
        co.consult("regulatory", "records", "read:customer_record", onward)
        raise SystemExit("expected the customer-record request to be refused")
    except PolicyDenied:
        last("denied:regulatory>records", to="records")

    try:
        onward.attenuate(audience="capacity", scope=["read:customer_record"], purpose="curiosity", step=co.step)
        raise SystemExit("expected the widening delegation to be refused")
    except GrantError as err:
        beats.append({"t": "widen", "cue": "widen:regulatory>capacity", "from": "regulatory",
                      "to": "capacity", "text": "refused: %s" % err})

    # 2. The panel deliberates on the same coordinator, so the ledger runs on.
    deliberation, outcome = deliberation_beats(lib, co, len(co.ledger.entries))
    beats.extend(deliberation)
    assert outcome.status == "escalated", outcome.status
    protection = [e for e in co.ledger.entries if e.kind == "verdict" and e.actor == "protection"][0]

    # 3. The person's call, recorded as further entries; nothing is mutated.
    decision_at = len(beats)
    if branch == "overrule":
        co.ledger.contest(co.step + 1, protection.id, ENGINEER,
                          "the switchgear at F-12 was uprated in August and the rating on file is old")
        last("contest")
        co.ledger.overrule(co.step + 2, protection.id, ENGINEER,
                           "fault level is within rating on the uprated switchgear",
                           "uprate certificate SG-4471, signed off 12 August 2026")
        last("override", rationale=co.ledger.entries[-1].detail["rationale"])
    else:
        co.ledger.record(co.step + 1, "decision", ENGINEER,
                         "%s lets step %s stand: the fault-level objection holds, so CR-2291 needs a "
                         "reinforcement study before it can be approved" % (ENGINEER, protection.id),
                         {"decision": "objection stands"}, refers_to=protection.id)
        last("uphold")

    return beats[:decision_at], beats[decision_at:], protection.id, outcome, co.ledger.narrate()


def outage_run(lib):
    Coordinator, Grant, GrantError, PolicyDenied, ASPECTS, PROPOSITION, facts, panel = lib
    co = Coordinator(panel(protection_available=False), facts(), ASPECTS)
    beats, outcome = deliberation_beats(lib, co, 0, prefix="o:")
    assert outcome.degraded and outcome.status == "resolved", outcome
    return beats, outcome, co.ledger.narrate()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent-consult", default=os.environ.get("AGENT_CONSULT_PATH", "../agent-consult"),
                    help="path to a checkout of github.com/darshan2209/agent-consult")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    lib = load_library(args.agent_consult)
    Coordinator, Grant, GrantError, PolicyDenied, ASPECTS, PROPOSITION, facts, panel = lib

    pre_a, overrule, prot_id, outcome, narr_a = case_run(lib, "overrule")
    pre_b, uphold, prot_id_b, _, narr_b = case_run(lib, "uphold")
    if pre_a != pre_b or prot_id != prot_id_b:
        raise SystemExit("the two branch runs diverged before the decision; refusing to write")
    outage, outage_outcome, narr_o = outage_run(lib)

    trace = {
        "source": {"repo": "https://github.com/darshan2209/agent-consult",
                   "commit": commit_of(args.agent_consult),
                   "recorded": datetime.date.today().isoformat()},
        "proposition": PROPOSITION,
        "agents": [{"id": a.id, "role": a.role, "capabilities": sorted(a.capabilities)} for a in panel()],
        "case": {"beats": pre_a, "protection": prot_id,
                 "question": outcome.disagreements[0].question_for_human,
                 "branches": {"overrule": overrule, "uphold": uphold},
                 "record": {"overrule": narr_a, "uphold": narr_b}},
        "outage": {"beats": outage, "headline": outage_outcome.headline(),
                   "unsupported": outage_outcome.unsupported, "record": narr_o},
    }
    body = json.dumps(trace, indent=1, ensure_ascii=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("/* Generated by tools/export_agent_trace.py from %s @ %s on %s.\n"
                 "   Real runs of the agent-consult library, recorded step by step. Do not edit by hand:\n"
                 "   re-run the exporter. */\nwindow.AGENT_ROOM = %s;\n"
                 % (trace["source"]["repo"], trace["source"]["commit"], trace["source"]["recorded"], body))
    steps = len(pre_a) + max(len(overrule), len(uphold))
    print("wrote %s: %d case beats, %d + %d decision beats, %d outage beats (%d steps on the longest path)"
          % (os.path.relpath(args.out), len(pre_a), len(overrule), len(uphold), len(outage), steps))


if __name__ == "__main__":
    main()
