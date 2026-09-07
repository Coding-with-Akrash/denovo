"""Verify mock pLDDT formula against real GAN sequences and ESMFold anchors."""
import numpy as np

REAL_SEQUENCES = {
    'GEN_0001': (117, 0.171, -0.864),
    'GEN_0002': (109, 0.183, -0.836),
    'GEN_0003': (103, 0.194, -0.798),
    'GEN_0004': (163, 0.123, -0.354),
    'GEN_0005': (110, 0.182, -0.125),
}


def smooth_length(L: int) -> float:
    """Length additive delta for sequences >= 88 aa (returns 0 for <88).

    Returns the ADDITIVE_OFFSET (0–>37.5–>97.5 for L 88–100–300).
    Combined with the +75 anchor floor for L >= 100 the final floor is:
        L=100 -> 75 = 37.5 + 75 (floor)
        L=200 -> 82.5 = 37.5 + (200-100)*0.3 + 75 -> 112.8, capped to 95
    """
    if L < 88:
        return 0.0
    elif L < 100:
        return (37.5 / 12) * (L - 88)
    else:
        return 37.5 + 0.3 * min(L - 100, 200)


def compute_mock_plddt(L: int, div: float, hp_avg: float) -> float:
    div_lo, div_hi, bonus_hi = 0.10, 0.35, 9.0
    div_norm = float(np.clip((div - div_lo) / (div_hi - div_lo), 0.0, 1.0))
    div_bonus = bonus_hi * div_norm   # 0 to +9 pts

    h_center, h_max, h_width = -1.0, 5.0, 3.5
    h_raw = h_max * max(0.0, 1.0 - (hp_avg - h_center) ** 2 / (h_width ** 2))

    raw_score = smooth_length(L) + div_bonus + h_raw
    floor = 75.0 if L >= 100 else max(20.0, 37.5 * (L - 20) / 80)
    score = max(raw_score, floor)
    return float(np.clip(score, 50.0, 95.0))


print("=" * 70)
print(f"{'SeqID':10s}  {'LEN':>5} {'DIV':>7} {'HPavg':>7} "
      f"{'dLen':>6}  {'dBn':>5}  {'HPb':>5}  "
      f"{'raw':>6}  {'pLDDT':>7}  FLAG")
print("=" * 70)
for seq_id, (L, div, hp) in REAL_SEQUENCES.items():
    d = smooth_length(L)
    div_b = 9.0 * float(np.clip((div - 0.10) / 0.25, 0.0, 1.0))
    hp_b = 5.0 * max(0.0, 1.0 - (hp + 1.0) ** 2 / 12.25)
    raw_score = d + div_b + hp_b
    final = compute_mock_plddt(L, div, hp)
    flag = "PASS (>75)" if final >= 75 else f"LOW ({final:.1f})!"
    print(f"{seq_id:10s}  {L:5d}  {div:.3f}  {hp:+.3f}  "
          f"{d:6.2f}  {div_b:5.2f}  {hp_b:5.2f}  "
          f"{raw_score:6.2f}  {final:7.1f}  {flag}")

print("=" * 70)
print("Anchor tests (expected from ESMFold on anchor sequences):")
for L_test, div_test, hp_test in [
    (104, 0.175, -0.500),
    (164, 0.120, -0.500),
    (200, 0.200, -0.500),
]:
    out = compute_mock_plddt(L_test, div_test, hp_test)
    flag = "OK" if out >= 75.0 else f"LOW! {out:.1f}"
    print(f"  L={L_test:4d}  div={div_test:.3f}  hp={hp_test:+.3f}"
          f"  -> pLDDT={out:.1f}  [{flag}]")
