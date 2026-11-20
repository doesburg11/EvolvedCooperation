"""Parameters for ladder steps 0-1 (README pre-registration, commit 4c5fefb). No command-line parameters."""
from __future__ import annotations

from typing import Any

from moran_models.nowak_mechanisms.kin_selection.config.kin_selection_config import config as MORAN_CONFIG

STEPS = 1000
SEEDS = list(range(20))
SUCCESS_FINAL_MEAN_TRAIT = 0.60
RARE = {"initial_trait_mean": 0.05, "initial_trait_stddev": 0.02}
COMMON = {"initial_trait_mean": 0.9, "initial_trait_stddev": 0.05}
UNIFORM = {"kin_weight_same_lineage": 0.5, "kin_weight_other_lineage": 0.5}
BELOW_B = 0.05
LOW_B = 0.6                      # conditional lower-benefit diagnostic
NOBIAS_TRIGGER = 8               # S-nobias successes at B = 1.0 that trigger the B = 0.6 scoring

# arm -> (mechanism kwargs, config updates)
STEP0_ARMS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "A-kin": ({"self_in_routing": True, "kin": "label"}, {**RARE}),
    "A-nobias": ({"self_in_routing": True, "kin": "label"}, {**RARE, **UNIFORM}),
    "A-below": ({"self_in_routing": True, "kin": "label"}, {**COMMON, "B_plus_scale": BELOW_B}),
    "S-kin": ({"self_in_routing": False, "kin": "label"}, {**RARE}),
    "S-nobias": ({"self_in_routing": False, "kin": "label"}, {**RARE, **UNIFORM}),
    "S-below": ({"self_in_routing": False, "kin": "label"}, {**COMMON, "B_plus_scale": BELOW_B}),
}
STEP0_LOW_ARMS = {
    "S-kin-0.6": ({"self_in_routing": False, "kin": "label"}, {**RARE, "B_plus_scale": LOW_B}),
    "S-nobias-0.6": ({"self_in_routing": False, "kin": "label"}, {**RARE, **UNIFORM, "B_plus_scale": LOW_B}),
}

# Step 1 calibration: neutral (h = 0) runs.
CAL_MU = [0.001, 0.003, 0.01, 0.03]
CAL_SEEDS = list(range(5))
CAL_SAMPLE_STEPS = list(range(100, 1001, 50))
CAL_RANDOM_PAIRS = 2000
CAL_PAIR_SEED = 12345
NEUTRAL = {"initial_trait_mean": 0.0, "initial_trait_stddev": 0.0, "mutation_rate": 0.0}  # h stays 0: equal fitness
ATTEMPT2_MU_DIVISOR = 10

WORKERS = 8
DATA_DIR = "ecological_models/nowak_mechanisms/kin_selection_ladder/data"


def run_config(seed: int, updates: dict[str, Any], steps: int = STEPS) -> dict[str, Any]:
    cfg = dict(MORAN_CONFIG)
    cfg.update(updates)
    cfg.update({"random_seed": seed, "simulation_steps": steps, "summary_interval_steps": 10**9, "write_log": False})
    return cfg

# Step 0c (half-step, pre-registered 1252e8f): self at its own routing weight, 3000 steps.
STEPS_0C = 3000
W_SELF_ATTEMPT1 = 0.2
W_SELF_ATTEMPT2 = 0.5
FISHER_ALPHA_ATTEMPT2 = 0.025
STEP0C_ARMS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "H-kin": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT1}, {**RARE}),
    "H-nobias": ({"self_in_routing": True, "kin": "label"}, {**RARE, **UNIFORM}),
    "H-below": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT1},
                {**COMMON, "B_plus_scale": BELOW_B}),
    "A-kin-3k": ({"self_in_routing": True, "kin": "label"}, {**RARE}),
}
STEP0C_ATTEMPT2_ARMS = {
    "H2-kin": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT2}, {**RARE}),
    "H2-below": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT2},
                 {**COMMON, "B_plus_scale": BELOW_B}),
}

# Step 0d (pre-registered 697928d): local versus global-competitor replacement, uniform routing, 3000 steps.
SAMPLE_STEPS_0D = list(range(500, 3001, 500))
SUSTAINED_FROM = 2500
STEP0D_ARMS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "V-local": ({"self_in_routing": True, "kin": "label"}, {**RARE, **UNIFORM}),
    "V-global": ({"self_in_routing": True, "kin": "label", "replacement": "global"}, {**RARE, **UNIFORM}),
    "V-below": ({"self_in_routing": True, "kin": "label"}, {**COMMON, **UNIFORM, "B_plus_scale": BELOW_B}),
    "V-null": ({"self_in_routing": True, "kin": "label", "replacement": "global"},
               {**RARE, **UNIFORM, "B_plus_scale": 0.0, "C_scale": 0.0}),
}

# Step 1 (revised ladder, pre-registered ad9c75c): overlapping generations.
STEP1_ATTEMPTS = {1: {"death": 0.5, "steps": 6000}, 2: {"death": 0.8, "steps": 3750}}
STEP1_ALPHA = 0.025
STEP1_MAX_GLOBAL_CORR = 0.10
STEP1_SUSTAINED_LAST = 1000          # descriptive: >= 0.60 at every 50-step sample in the last 1000 steps
UNIFORM_ROUTING = {"self_in_routing": True, "kin": "label"}


def step1_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    d = STEP1_ATTEMPTS[attempt]["death"]
    tag = "O" if attempt == 1 else "O2"
    return {
        f"{tag}-local": ({**UNIFORM_ROUTING, "death": d, "replacement": "local"}, {**RARE, **UNIFORM}),
        f"{tag}-global": ({**UNIFORM_ROUTING, "death": d, "replacement": "global"}, {**RARE, **UNIFORM}),
        f"{tag}-below": ({**UNIFORM_ROUTING, "death": d, "replacement": "local"},
                         {**COMMON, **UNIFORM, "B_plus_scale": BELOW_B}),
        f"{tag}-null": ({**UNIFORM_ROUTING, "death": d, "replacement": "local"},
                        {**RARE, **UNIFORM, "B_plus_scale": 0.0, "C_scale": 0.0}),
    }

# Step 1b (pre-registered a3a180e): selection on survival via a death lottery; lam 1 then 0.5.
STEP1B_LAMBDA = {1: 1.0, 2: 0.5}
STEP1B_STEPS = 6000
STEP1B_DEATH = 0.5


def step1b_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    lam = STEP1B_LAMBDA[attempt]
    tag = "S" if attempt == 1 else "S2"
    base = {**UNIFORM_ROUTING, "death": STEP1B_DEATH, "lam": lam}
    return {
        f"{tag}-local": ({**base, "replacement": "local"}, {**RARE, **UNIFORM}),
        f"{tag}-global": ({**base, "replacement": "global"}, {**RARE, **UNIFORM}),
        f"{tag}-below": ({**base, "replacement": "local"}, {**COMMON, **UNIFORM, "B_plus_scale": BELOW_B}),
        f"{tag}-null": ({**base, "replacement": "local"}, {**RARE, **UNIFORM, "B_plus_scale": 0.0, "C_scale": 0.0}),
    }

# Step 1c (pre-registered 5067eed): as step 1b with the death lottery normalized over the whole grid.
def step1c_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    tag = "L" if attempt == 1 else "L2"
    return {f"{tag}-{k.split('-', 1)[1]}": ({**m, "norm": "global"}, u) for k, (m, u) in step1b_arms(attempt).items()}

# Step 2a (pre-registered 3db3b5e): ages, adult-only helping (attempt 2: juveniles at half strength), on the 1c base.
STEP2A_JUVENILE_STRENGTH = {1: 0.0, 2: 0.5}
STEP2A_JUVENILE_PERIOD = 1


def step2a_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    tag = "A" if attempt == 1 else "A2"
    out = {}
    for k, (m, u) in step1c_arms(2).items():                   # the step-1c attempt-2 base (lam 0.5, global norm)
        out[f"{tag}-{k.split('-', 1)[1]}"] = ({**m, "juvenile_period": STEP2A_JUVENILE_PERIOD,
                                               "juvenile_strength": STEP2A_JUVENILE_STRENGTH[attempt]}, u)
    return out

# Step K0 (pre-registered 9e81fb5): costly-helping base. Step-1 attempt-1 engine, self out of routing (uniform over
# the 4 neighbours), b/c = B/C sweep; attempt 2 excludes the dead site's own occupant (death-birth-like).
K0_STEPS = 6000
K0_DEATH = 0.5
K0_C = 0.2
K0_BC = {3: 0.6, 6: 1.2, 12: 2.4, 24: 4.8}          # b/c -> B at C = 0.2
K0_TEST_BC = 12
K0_ALPHA = 0.025
COSTLY_ROUTING = {"self_in_routing": False, "kin": "label"}   # with UNIFORM weights: uniform over 4 neighbours


def k0_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    sfx = "-local" if attempt == 1 else "-DB"
    base = {**COSTLY_ROUTING, "death": K0_DEATH, "exclude_focal": attempt == 2}
    arms = {f"K{bc}{sfx}": ({**base, "replacement": "local"}, {**RARE, **UNIFORM, "B_plus_scale": b, "C_scale": K0_C})
            for bc, b in K0_BC.items()}
    gname = f"K{K0_TEST_BC}-global" if attempt == 1 else f"K{K0_TEST_BC}-DB-global"
    arms[gname] = ({**base, "replacement": "global"},
                   {**RARE, **UNIFORM, "B_plus_scale": K0_BC[K0_TEST_BC], "C_scale": K0_C})
    tail = "" if attempt == 1 else "-DB"
    arms[f"K-below{tail}"] = ({**base, "replacement": "local"},
                              {**COMMON, **UNIFORM, "B_plus_scale": BELOW_B, "C_scale": K0_C})
    arms[f"K-null{tail}"] = ({**base, "replacement": "local"},
                             {**RARE, **UNIFORM, "B_plus_scale": 0.0, "C_scale": 0.0})
    return arms


def k0_roles(attempt: int) -> tuple[str, str, str]:
    """(test arm, global control, below control) names."""
    if attempt == 1:
        return f"K{K0_TEST_BC}-local", f"K{K0_TEST_BC}-global", "K-below"
    return f"K{K0_TEST_BC}-DB", f"K{K0_TEST_BC}-DB-global", "K-below-DB"

# Step K1 (pre-registered 3615065): parental care on the K0 base. Attempt 1 offspring-only (lost if none);
# attempt 2 hybrid (no offspring -> uniform to neighbours).
K1_TEST_BC = 6
K1_LOCAL_BC = {1.5: 0.3, 3: 0.6, 6: 1.2, 12: 2.4}
K1_GLOBAL_BC = {3: 0.6, 6: 1.2, 12: 2.4}
K1_MIN_TEST = 15
K1_DIAG_FROM = 1000


def _bc(x) -> str:
    return f"{x:g}"


def k1_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag, care = ("P", "offspring") if attempt == 1 else ("H", "hybrid")
    base = {**COSTLY_ROUTING, "death": K0_DEATH, "care": care}
    upd = lambda b, start=RARE: {**start, **UNIFORM, "B_plus_scale": b, "C_scale": K0_C}
    arms = {}
    for bc in (6, 1.5, 3, 12):
        arms[f"{tag}{_bc(bc)}-local"] = ({**base, "replacement": "local"}, upd(K1_LOCAL_BC[bc]))
    if attempt == 1:
        arms["N6-local"] = k0_arms(1)["K6-local"]                    # exact K6-local rerun
    arms[f"{tag}-below"] = ({**base, "replacement": "local"}, upd(BELOW_B, COMMON))
    for bc, b in K1_GLOBAL_BC.items():
        arms[f"{tag}{_bc(bc)}-global"] = ({**base, "replacement": "global"}, upd(b))
    return arms


def k1_roles(attempt: int) -> tuple[str, str, str]:
    """(test arm, below control, secondary global arm)."""
    tag = "P" if attempt == 1 else "H"
    return f"{tag}6-local", f"{tag}-below", f"{tag}6-global"

# Step R1 (pre-registered 0231603): care lowers the recipient's death, d = 0.5 exp(-lam R / T); attempt 1 lam 1,
# attempt 2 lam 0.5. Base: K1 attempt 1.
R1_LAM = {1: 1.0, 2: 0.5}
R1_LOCAL_BC = {6: 1.2, 3: 0.6, 12: 2.4, 24: 4.8}
R1_GLOBAL_BC = {6: 1.2, 12: 2.4}


def r1_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "R" if attempt == 1 else "R2-"
    base = {**COSTLY_ROUTING, "death": K0_DEATH, "care_lam": R1_LAM[attempt]}
    upd = lambda b, start=RARE: {**start, **UNIFORM, "B_plus_scale": b, "C_scale": K0_C}
    arms = {}
    for bc, b in R1_LOCAL_BC.items():
        arms[f"{tag}{bc}-local"] = ({**base, "care": "offspring", "replacement": "local"}, upd(b))
    arms[f"{tag}N6-local"] = ({**base, "care": "neighbours", "replacement": "local"}, upd(1.2))
    arms[f"{tag}below" if attempt == 2 else "R-below"] = ({**base, "care": "offspring", "replacement": "local"},
                                                         upd(BELOW_B, COMMON))
    for bc, b in R1_GLOBAL_BC.items():
        arms[f"{tag}{bc}-global"] = ({**base, "care": "offspring", "replacement": "global"}, upd(b))
    return arms


def r1_roles(attempt: int) -> tuple[str, str, str, str]:
    """(test, control, below, secondary global)."""
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "R6-local", "RN6-local", "R-below", "R6-global"
    return "R2-6-local", "R2-N6-local", "R2-below", "R2-6-global"

# Diagnostic DR1 (pre-registered 8317f48): survival-care plateau (lam = 1), high starts, b/c 48, drift references.
DR1_RARE_REF = {                                     # R1 attempt-1 mean final h, frozen at full precision
    "R12-local": 0.11892638472644475, "R24-local": 0.10033534869417678,
    "R6-global": 0.2430629944190848, "R12-global": 0.2259714860586167,
}
DR1_PAIRS = {"D12-local-high": "R12-local", "D24-local-high": "R24-local",
             "D6-global-high": "R6-global", "D12-global-high": "R12-global"}
DR1_NULL_FOR = {"D12-local-high": "D-null-local-high", "D24-local-high": "D-null-local-high",
                "D6-global-high": "D-null-global-high", "D12-global-high": "D-null-global-high"}
DR1_TOL = 0.03
DR1_SETTLED_RANGE = 0.02
DR1_SETTLED_FROM = 5000
DR1_NULL_MIN = 0.50


def dr1_arms() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    base = {**COSTLY_ROUTING, "death": K0_DEATH, "care_lam": 1.0, "care": "offspring"}
    upd = lambda b, start, c=K0_C: {**start, **UNIFORM, "B_plus_scale": b, "C_scale": c}
    return {
        "D12-local-high": ({**base, "replacement": "local"}, upd(2.4, COMMON)),
        "D24-local-high": ({**base, "replacement": "local"}, upd(4.8, COMMON)),
        "D48-local-high": ({**base, "replacement": "local"}, upd(9.6, COMMON)),
        "D6-global-high": ({**base, "replacement": "global"}, upd(1.2, COMMON)),
        "D12-global-high": ({**base, "replacement": "global"}, upd(2.4, COMMON)),
        "D48-local": ({**base, "replacement": "local"}, upd(9.6, RARE)),
        "D-null-local-high": ({**base, "replacement": "local"}, upd(0.0, COMMON, 0.0)),
        "D-null-global-high": ({**base, "replacement": "global"}, upd(0.0, COMMON, 0.0)),
    }

# Step R2 (pre-registered aa957de): care only for juvenile offspring (age < J); J = 2, attempt 2 J = 5; R1 lam 0.5 base.
R2_J = {1: 2, 2: 5}
R2_LAM = 0.5


def r2_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "Y" if attempt == 1 else "Y2-"
    base = {**COSTLY_ROUTING, "death": K0_DEATH, "care_lam": R2_LAM, "care_juvenile": R2_J[attempt]}
    upd = lambda b, start=RARE: {**start, **UNIFORM, "B_plus_scale": b, "C_scale": K0_C}
    arms = {}
    for bc, b in R1_LOCAL_BC.items():
        arms[f"{tag}{bc}-local"] = ({**base, "care": "offspring", "replacement": "local"}, upd(b))
    arms[f"{tag}N6-local"] = ({**base, "care": "young_neighbours", "replacement": "local"}, upd(1.2))
    arms["Y-below" if attempt == 1 else "Y2-below"] = ({**base, "care": "offspring", "replacement": "local"},
                                                       upd(BELOW_B, COMMON))
    for bc, b in R1_GLOBAL_BC.items():
        arms[f"{tag}{bc}-global"] = ({**base, "care": "offspring", "replacement": "global"}, upd(b))
    return arms


def r2_roles(attempt: int) -> tuple[str, str, str, str]:
    """(test, control, below, secondary global)."""
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "Y6-local", "YN6-local", "Y-below", "Y6-global"
    return "Y2-6-local", "Y2-N6-local", "Y2-below", "Y2-6-global"

# Step R3a (pre-registered 415b90c): condition stores with carry-over rho (0.8, attempt 2 0.4) on the R2 base.
R3A_RHO = {1: 0.8, 2: 0.4}


def r3a_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "E" if attempt == 1 else "E2-"
    out = {}
    for name, (m, u) in r2_arms(1).items():
        rest = "below" if name == "Y-below" else name[1:]
        new = ("E-below" if attempt == 1 else "E2-below") if rest == "below" else f"{tag}{rest}"
        out[new] = ({**m, "care_rho": R3A_RHO[attempt]}, u)
    return out


def r3a_roles(attempt: int) -> tuple[str, str, str, str]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "E6-local", "EN6-local", "E-below", "E6-global"
    return "E2-6-local", "E2-N6-local", "E2-below", "E2-6-global"

# Step R3b (pre-registered 4b81e7f): a realized birth costs the surviving parent c_b in D (0.5, attempt 2 0.2),
# on the R3a attempt-1 base (rho 0.8).
R3B_CB = {1: 0.5, 2: 0.2}


def r3b_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "Q" if attempt == 1 else "Q2-"
    out = {}
    for name, (m, u) in r3a_arms(1).items():
        new = ("Q-below" if attempt == 1 else "Q2-below") if name == "E-below" else f"{tag}{name[1:]}"
        out[new] = ({**m, "care_birth_cost": R3B_CB[attempt]}, u)
    return out


def r3b_roles(attempt: int) -> tuple[str, str, str, str]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "Q6-local", "QN6-local", "Q-below", "Q6-global"
    return "Q2-6-local", "Q2-N6-local", "Q2-below", "Q2-6-global"

# Step R3c (pre-registered da353fd): breeding threshold theta on W (0.25, attempt 2 0); sites can stay empty;
# joint endpoint: final mean h over occupied sites >= 0.60 and final occupancy >= 0.5. R3b attempt-1 base.
R3C_THETA = {1: 0.25, 2: 0.0}
R3C_MIN_OCCUPANCY = 0.5


def r3c_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "V" if attempt == 1 else "V2-"
    out = {}
    for name, (m, u) in r3b_arms(1).items():
        new = ("V-below" if attempt == 1 else "V2-below") if name == "Q-below" else f"{tag}{name[1:]}"
        out[new] = ({**m, "care_theta": R3C_THETA[attempt]}, u)
    return out


def r3c_roles(attempt: int) -> tuple[str, str, str, str]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "V6-local", "VN6-local", "V-below", "V6-global"
    return "V2-6-local", "V2-N6-local", "V2-below", "V2-6-global"

# Step R3d (pre-registered 1a5830a): starvation, occupants with W < sigma die (0, attempt 2 -0.1); R3c attempt-1 base.
# Activation: added starvation deaths >= 1% of all deaths in the test arm (diagnostic window), else "inactive".
R3D_SIGMA = {1: 0.0, 2: -0.1}
R3D_MIN_ACTIVATION = 0.01


def r3d_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "F" if attempt == 1 else "F2-"
    out = {}
    for name, (m, u) in r3c_arms(1).items():
        new = ("F-below" if attempt == 1 else "F2-below") if name == "V-below" else f"{tag}{name[1:]}"
        out[new] = ({**m, "care_sigma": R3D_SIGMA[attempt]}, u)
    return out


def r3d_roles(attempt: int) -> tuple[str, str, str, str]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "F6-local", "FN6-local", "F-below", "F6-global"
    return "F2-6-local", "F2-N6-local", "F2-below", "F2-6-global"

# Step R4 (pre-registered b0104c2): the free baseline 1 in W is replaced by an income store G fed by a renewable
# site resource (harvest min(r, 0.2), regrowth r <- r + gamma (1 - r)); gamma 0.15, attempt 2 0.18; lean descriptive
# arms at 0.08 (attempt 1 only). R3d attempt-1 base. Activation: pooled harvest per occupant-step in the test arm
# <= 0.19 (exposure to limitation, not an effect), else "income limitation inactive".
R4_GAMMA = {1: 0.15, 2: 0.18}
R4_LEAN_GAMMA = 0.08
R4_MAX_HARVEST = 0.19


def r4_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "G" if attempt == 1 else "G2-"
    base = r3d_arms(1)
    out = {}
    for name, (m, u) in base.items():
        new = ("G-below" if attempt == 1 else "G2-below") if name == "F-below" else f"{tag}{name[1:]}"
        out[new] = ({**m, "care_gamma": R4_GAMMA[attempt]}, u)
    if attempt == 1:
        for s in ("local", "global"):
            m, u = base[f"F6-{s}"]
            out[f"G6-{s}-lean"] = ({**m, "care_gamma": R4_LEAN_GAMMA}, u)
    return out


def r4_roles(attempt: int) -> tuple[str, str, str, str]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "G6-local", "GN6-local", "G-below", "G6-global"
    return "G2-6-local", "G2-N6-local", "G2-below", "G2-6-global"

# Diagnostic DR4 (pre-registered 51821a1, labels 1010b9d): which part of R4 accounts for the higher helping.
# Seven arms at b/c 6, local settlement, seeds 0-19, 6000 steps; references rerun in the same batch.
DR4_BASELINES = {"D-U85": 0.85, "D-U75": 0.75}
DR4_G_START = 0.75
DR4_MIN_RISE = 0.10
DR4_BOOT = 10_000
DR4_BOOT_SEED = 0


def dr4_arms() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    mf, uf = r3d_arms(1)["F6-local"]
    mg, ug = r4_arms(1)["G6-local"]
    out = {"D-F": (dict(mf), dict(uf)), "D-G": (dict(mg), dict(ug))}
    for a, b in DR4_BASELINES.items():
        out[a] = (dict(mf), {**uf, "base_fitness": b})
    out["D-E"] = ({**mg, "care_g_start": DR4_G_START}, dict(ug))
    out["D-Fcb0"] = ({**mf, "care_birth_cost": 0.0}, dict(uf))
    out["D-Gcb0"] = ({**mg, "care_birth_cost": 0.0}, dict(ug))
    return out


# Step R5a (pre-registered 51821a1): foraging over the von Neumann neighbourhood, on R4 attempt 1 (gamma 0.15).
# Attempt 1: w = 1/5 per site; attempt 2: 1/2 own, 1/8 per neighbour (no lean arms). Exposure pilot first: seeds 0-1
# of A6-local and A6-local-lean; main run only if exposure >= 2% in at least one pilot arm.
R5A_W_OWN = {1: 0.2, 2: 0.5}
R5A_PILOT_ARMS = ("A6-local", "A6-local-lean")
R5A_PILOT_SEEDS = [0, 1]
R5A_MIN_EXPOSURE = 0.02


def r5a_arms(attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "A" if attempt == 1 else "A2-"
    out = {}
    for name, (m, u) in r4_arms(1).items():
        if attempt == 2 and name.endswith("-lean"):
            continue
        new = ("A-below" if attempt == 1 else "A2-below") if name == "G-below" else f"{tag}{name[1:]}"
        out[new] = ({**m, "care_forage_own": R5A_W_OWN[attempt]}, u)
    return out


def r5a_roles(attempt: int) -> tuple[str, str, str, str]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    if attempt == 1:
        return "A6-local", "AN6-local", "A-below", "A6-global"
    return "A2-6-local", "A2-N6-local", "A2-below", "A2-6-global"


# Step R6 (pre-registered 8e056ea): the newborn's endowment E = 0.75 (D-E base) is paid by its parent, fraction q.
# Pilot: seeds 0-1 of the test arm at q = 1 and q = 0.5; main run at the highest level that is viable with vacant
# space; attempt 2 halves q (gamma stays 0.15, no lean arms).
R6_E = 0.75
R6_Q_LEVELS = (1.0, 0.5)
R6_PILOT_SEEDS = [0, 1]
R6_MIN_FILL_FAILURE = 0.05
R6_MAX_OCCUPANCY = 0.97
R6_MIN_FINAL_OCCUPANCY = 0.5


def r6_arms(q: float, attempt: int) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if attempt not in (1, 2):
        raise ValueError("attempt must be 1 or 2")
    tag = "T" if attempt == 1 else "T2-"
    out = {}
    for name, (m, u) in r4_arms(1).items():
        if attempt == 2 and name.endswith("-lean"):
            continue
        new = ("T-below" if attempt == 1 else "T2-below") if name == "G-below" else f"{tag}{name[1:]}"
        out[new] = ({**m, "care_g_start": R6_E, "care_parent_pay": float(q)}, u)
    return out


def r6_pilot_arms() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    return {f"T6-local-q{q:g}": r6_arms(q, 1)["T6-local"] for q in R6_Q_LEVELS}
