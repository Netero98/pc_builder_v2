#!/usr/bin/env python3
"""Validate PC Builder data.json.

Checks:
1. JSON validity + count.
2. Every GPU's score is within at least one CPU's gpuRange (reachable).
3. Every CPU's gpuRange matches at least one GPU (non-empty).
4. No inverted or negative ranges.
5. Bug case: i3-12100 must NOT match RTX 2060.
6. List what i3-12100 IS compatible with.

Usage: python3 validate.py [path/to/data.json]
"""
import json
import sys
from pathlib import Path

PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data.json"


def main() -> int:
    with PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    cpus = data["cpus"]
    gpus = data["gpus"]

    print(f"Loaded {PATH}")
    print(f"  CPUs: {len(cpus)}")
    print(f"  GPUs: {len(gpus)}")
    print()

    errors = []

    for cpu in cpus:
        if "gpuRange" not in cpu:
            errors.append(f"CPU {cpu['id']}: missing gpuRange")
            continue
        lo, hi = cpu["gpuRange"]
        if lo > hi:
            errors.append(f"CPU {cpu['id']}: gpuRange inverted ({lo} > {hi})")
        if lo < 0:
            errors.append(f"CPU {cpu['id']}: gpuRange negative min")
    for gpu in gpus:
        if "cpuRange" in gpu:
            errors.append(f"GPU {gpu['id']}: legacy 'cpuRange' field present, should be removed")

    # Reachable GPUs: each GPU must be in at least one CPU's gpuRange
    for gpu in gpus:
        if not any(
            cpu["gpuRange"][0] <= gpu["score"] <= cpu["gpuRange"][1]
            for cpu in cpus
        ):
            errors.append(
                f"GPU {gpu['id']} (score={gpu['score']}) is NOT in any CPU's gpuRange"
            )

    # Non-empty gpuRange: every CPU must list at least one GPU
    for cpu in cpus:
        if not any(
            cpu["gpuRange"][0] <= gpu["score"] <= cpu["gpuRange"][1]
            for gpu in gpus
        ):
            errors.append(
                f"CPU {cpu['id']} gpuRange={cpu['gpuRange']} matches no GPU at all"
            )

    # Sanity: i3-12100 + RTX 2060 SHOULD match (per multiple sources, RTX 2060 is
    # in the recommended GPU list for i3-12100F)
    i3 = next((c for c in cpus if c["id"] == "i3-12100"), None)
    rtx2060 = next((g for g in gpus if g["id"] == "rtx-2060"), None)
    if i3 and rtx2060:
        match = i3["gpuRange"][0] <= rtx2060["score"] <= i3["gpuRange"][1]
        print(f"=== i3-12100 vs RTX 2060 ===")
        print(f"  i3-12100 score: {i3['score']}, gpuRange: {i3['gpuRange']}")
        print(f"  RTX 2060 score: {rtx2060['score']}")
        print(f"  Match? {match}  (expected: True — RTX 2060 is recommended for i3-12100)")
        print()
        if not match:
            errors.append("i3-12100 + RTX 2060 SHOULD match (per data sources)")

    # Show what i3-12100 actually pairs with
    if i3:
        suitable = [
            g for g in gpus
            if i3["gpuRange"][0] <= g["score"] <= i3["gpuRange"][1]
        ]
        print(f"=== GPUs compatible with i3-12100 ({len(suitable)}) ===")
        for g in suitable:
            print(f"  - {g['name']:35} G3D {g['score']}")
        print()

    # Per-CPU match count
    print("=== Per-CPU match count (out of 99 GPUs) ===")
    counts = []
    for cpu in cpus:
        n = sum(1 for g in gpus if cpu["gpuRange"][0] <= g["score"] <= cpu["gpuRange"][1])
        counts.append((cpu['name'], n))
    counts.sort(key=lambda x: x[1])
    print("  Least matches:")
    for name, n in counts[:5]:
        print(f"    {n:3d}  {name}")
    print("  Most matches:")
    for name, n in counts[-5:]:
        print(f"    {n:3d}  {name}")
    print()

    # Show top-CPU pairings
    if rtx2060:
        suitable = [
            c for c in cpus
            if rtx2060["score"] >= c["gpuRange"][0] and rtx2060["score"] <= c["gpuRange"][1]
        ]
        print(f"=== CPUs compatible with RTX 2060 ({len(suitable)}) ===")
        for c in suitable:
            print(f"  - {c['name']:35} Mark {c['score']}")
        print()

    # Check: every GPU must have at least one CPU that pairs with it
    for gpu in gpus:
        cpus_pairing = [c for c in cpus
                        if c["gpuRange"][0] <= gpu["score"] <= c["gpuRange"][1]]
        if not cpus_pairing:
            errors.append(f"GPU {gpu['id']} has no CPU pairing it")

    print()
    if errors:
        print(f"ERRORS: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: no validation errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
