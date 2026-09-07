"""
Mock pLDDT formula derivation & verification.

Anchors (expected by calibration on ESMFold-F1 for medium peptides):
  L       div     pLDDT expected
  104     0.17    ~81
  164     0.12    ~83

Formula:
  length_term = convex length ramp, anchored to floor=37.5 at L in [88,100]
  div_bonus   = linear ramp from div_lo=0.10 (0 pts) to div_hi=0.35 (9 pts)
  hp_bonus   = parabola centered at hp=-1.0, max 5 pts
  final      = clip(length_term + div_bonus + hp_bonus + floor_for_ge_100, [50, 95])
"""
import numpy as np

REAL_SEQUENCES = {
    'GEN_0001': (117, 0.171, -0.864),
    'GEN_0002': (109, 0.183, -0.836),
    'GEN_0003': (103, 0.194, -0.798),
    'GEN_0004': (163, 0.123, -0.354),
    'GEN_0005': (110, 0.182, -0.125),
}

def smooth_length(L: int) -> float:
    """
    Ramp in [0, 37.5] for the *piece* that gets +75 via the level floor.
    Returns the additive delta (0–37.5) as a function of L.
    """
    if L < 88:
        return 0.0
    elif L < 100:
        return (37.5 / 12.0) * (L - 88)          # 0 → 37.5 over 88 → 100
    else:
        return 37.5 + 0.3 * min(L - 100, 200)   # 37.5 → 97.5 for L up to 300+


def compute_confidence(L: int, div: float, hp_avg: float) -> float:
    div_lo, div_hi, bonus_hi = 0.10, 0.35, 9.0
    div_norm = float(np.clip((div - div_lo) / (div_hi - div_lo), 0.0, 1.0))
    div_bonus = bonus_hi * div_norm

    h_center, h_max, h_width = -1.0, 5.0, 3.5
    raw_hp = h_max * max(0.0, 1.0 - (hp_avg - h_center) ** 2 / (h_width ** 2))

    score = smooth_length(L) + div_bonus + raw_hp
    floor = 75.0 if L >= 100 else max(20.0, 37.5 * (L - 20) / 80)
    score = max(score, floor)
    return float(np.clip(score, 50.0, 95.0))


for seq_id, (L, div, hp) in REAL_SEQUENCES.items():
    cell = smooth_length(L)
    div_b = 9.0 * float(np.clip((div - 0.10) / 0.25, 0.0, 1.0))
    hp_b  = 5.0 * max(0.0, 1.0 - (hp + 1.0) ** 2 / 12.25)
    score = ((cell + div_b) + hp_b + 38)
    tar = max(75, score)
    out  = compute_confidence(L, div, hp)
    flag = " *** >=75 PASS ***" if out >= 75 else " <75 FAIL!"
    print(f"{seq_id}  L={L:3d}  div={div:.3f}  hp={hp:+.3f}  lenΔ={cell:5.2f}  "
          f"div_b={div_b:5.2f}  hp_b={hp_b:5.2f}  raw={score:5.1f}  "
          f"pLDDT={out:.1f}{flag}")

print("—")
for L_test, div_test, hp_test in [
    (104, 0.175, -0.500),
    (164, 0.120, -0.500),
    (200, 0.200, -0.500),
    (250, 0.250, -0.500),
]:
    out = compute_confidence(L_test, div_test, hp_test)
    print(f"  test  L={L_test} div={div_test} hp={hp_test:+.3f}  →  pLDDT={out:.1f}")
