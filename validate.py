#!/usr/bin/env python3
"""Validate PC Builder data.json.

PC is for gaming, so we use **PassMark Single Thread** as the ordering
metric (gaming is largely single-thread-bound). GPU compatibility ceilings
must grow monotonically with ST.

Checks:
1. JSON validity + count.
2. Every CPU has stScore and gpuRange; every GPU is reachable.
3. No inverted or negative ranges.
4. Sanity: i3-12100 + RTX 2060 should match (recommended pairing).
5. Monotonicity: for any two CPUs A and B with stScore_A <= stScore_B,
   gpuRange_B[1] >= gpuRange_A[1] AND gpuRange_B[0] >= gpuRange_A[0].

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

    # Basic checks
    for cpu in cpus:
        if "gpuRange" not in cpu:
            errors.append(f"CPU {cpu['id']}: missing gpuRange")
            continue
        if "stScore" not in cpu:
            errors.append(f"CPU {cpu['id']}: missing stScore (PassMark Single Thread)")
        lo, hi = cpu["gpuRange"]
        if lo > hi:
            errors.append(f"CPU {cpu['id']}: gpuRange inverted ({lo} > {hi})")
        if lo < 0:
            errors.append(f"CPU {cpu['id']}: gpuRange negative min")
    for gpu in gpus:
        if "cpuRange" in gpu:
            errors.append(f"GPU {gpu['id']}: legacy 'cpuRange' field present, should be removed")

    # Reachable GPUs
    for gpu in gpus:
        if not any(
            cpu["gpuRange"][0] <= gpu["score"] <= cpu["gpuRange"][1]
            for cpu in cpus
        ):
            errors.append(
                f"GPU {gpu['id']} (G3D={gpu['score']}) is NOT in any CPU's gpuRange"
            )

    # Non-empty gpuRange
    for cpu in cpus:
        if not any(
            cpu["gpuRange"][0] <= gpu["score"] <= cpu["gpuRange"][1]
            for gpu in gpus
        ):
            errors.append(
                f"CPU {cpu['id']} gpuRange={cpu['gpuRange']} matches no GPU at all"
            )

    # Sanity: i3-12100 + RTX 2060
    i3 = next((c for c in cpus if c["id"] == "i3-12100"), None)
    rtx2060 = next((g for g in gpus if g["id"] == "rtx-2060"), None)
    if i3 and rtx2060:
        match = i3["gpuRange"][0] <= rtx2060["score"] <= i3["gpuRange"][1]
        print("=== i3-12100 vs RTX 2060 ===")
        print(f"  i3-12100: ST={i3.get('stScore', '?')}, gpuRange={i3['gpuRange']}")
        print(f"  RTX 2060: G3D={rtx2060['score']}")
        print(f"  Match? {match}  (expected: True)")
        print()
        if not match:
            errors.append("i3-12100 + RTX 2060 SHOULD match")

    # Per-CPU match count
    print("=== Per-CPU match count ===")
    counts = []
    for cpu in cpus:
        n = sum(1 for g in gpus if cpu["gpuRange"][0] <= g["score"] <= cpu["gpuRange"][1])
        counts.append((cpu['name'], n, cpu.get('stScore', 0)))
    counts.sort(key=lambda x: x[1])
    print("  Least matches:")
    for name, n, st in counts[:5]:
        print(f"    {n:3d}  ST={st:5}  {name}")
    print("  Most matches:")
    for name, n, st in counts[-5:]:
        print(f"    {n:3d}  ST={st:5}  {name}")
    print()

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

    # Monotonicity check vs ST score
    print("=== Monotonicity check: gpuRange bounds vs ST score ===")
    sorted_cpus = sorted(cpus, key=lambda c: c.get("stScore", 0))
    monotonic_errors = []
    for i, cpu_a in enumerate(sorted_cpus):
        for cpu_b in sorted_cpus[i + 1:]:
            a_st = cpu_a.get("stScore", 0)
            b_st = cpu_b.get("stScore", 0)
            if a_st == 0 or b_st == 0:
                continue
            # Only flag when meaningfully apart (>= 100 ST points)
            if b_st - a_st < 100:
                continue
            a_min, a_max = cpu_a["gpuRange"]
            b_min, b_max = cpu_b["gpuRange"]
            if b_max < a_max:
                monotonic_errors.append(
                    f"  {cpu_b['id']:15} (ST={b_st}, max={b_max}) "
                    f"< {cpu_a['id']:15} (ST={a_st}, max={a_max})"
                )
            if b_min < a_min:
                monotonic_errors.append(
                    f"  {cpu_b['id']:15} (ST={b_st}, min={b_min}) "
                    f"< {cpu_a['id']:15} (ST={a_st}, min={a_min})"
                )
    if monotonic_errors:
        print(f"  Found {len(monotonic_errors)} anomalies:")
        for e in monotonic_errors:
            print(e)
    else:
        print("  OK: no anomalies")
    errors.extend(monotonic_errors)
    print()

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
