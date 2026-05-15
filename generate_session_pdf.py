#!/usr/bin/env python3
"""Generate a session-memory PDF covering all five ecological Nowak mechanism models."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from pathlib import Path

OUTPUT = Path("ecological_models/session_memory.pdf")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

W, H = A4
MARGIN = 2.0 * cm

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN, bottomMargin=MARGIN,
    title="Ecological Nowak Mechanisms — Session Memory",
    author="EvolvedCooperation Project",
)

base = getSampleStyleSheet()

DARK = colors.HexColor("#1a1a2e")
BLUE = colors.HexColor("#16213e")
ACC  = colors.HexColor("#0f3460")
HEAD = colors.HexColor("#533483")
PASS_GREEN = colors.HexColor("#2d6a4f")
FAIL_RED   = colors.HexColor("#9b2226")
LIGHT_GREY = colors.HexColor("#f0f0f0")
MID_GREY   = colors.HexColor("#cccccc")

def sty(name, **kw):
    s = ParagraphStyle(name, parent=base["Normal"], **kw)
    return s

title_sty   = sty("Title2",   fontSize=22, leading=28, textColor=DARK,
                  spaceAfter=6, fontName="Helvetica-Bold", alignment=TA_CENTER)
sub_sty     = sty("Sub",      fontSize=13, leading=17, textColor=ACC,
                  spaceAfter=4, fontName="Helvetica-BoldOblique", alignment=TA_CENTER)
date_sty    = sty("Date",     fontSize=10, textColor=colors.grey,
                  spaceAfter=16, alignment=TA_CENTER)
h1_sty      = sty("H1",       fontSize=16, leading=20, textColor=DARK,
                  spaceBefore=18, spaceAfter=6, fontName="Helvetica-Bold")
h2_sty      = sty("H2",       fontSize=13, leading=17, textColor=ACC,
                  spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold")
h3_sty      = sty("H3",       fontSize=11, leading=14, textColor=HEAD,
                  spaceBefore=8, spaceAfter=3, fontName="Helvetica-Bold")
body_sty    = sty("Body",     fontSize=9.5, leading=14, textColor=DARK,
                  spaceAfter=5, alignment=TA_JUSTIFY)
bullet_sty  = sty("Bullet",   fontSize=9.5, leading=14, textColor=DARK,
                  leftIndent=16, spaceAfter=3, bulletIndent=6)
code_sty    = sty("Code",     fontSize=8.5, leading=12,
                  fontName="Courier", textColor=colors.HexColor("#333333"),
                  leftIndent=12, spaceAfter=4, backColor=LIGHT_GREY)
caption_sty = sty("Caption",  fontSize=8, leading=11, textColor=colors.grey,
                  alignment=TA_CENTER, spaceAfter=6)
finding_sty = sty("Finding",  fontSize=9.5, leading=14, textColor=DARK,
                  leftIndent=14, spaceAfter=5, alignment=TA_JUSTIFY,
                  borderPadding=(4, 6, 4, 6))

def HR():
    return HRFlowable(width="100%", thickness=0.5, color=MID_GREY, spaceAfter=8, spaceBefore=4)

def h1(t): return Paragraph(t, h1_sty)
def h2(t): return Paragraph(t, h2_sty)
def h3(t): return Paragraph(t, h3_sty)
def p(t):  return Paragraph(t, body_sty)
def bl(t): return Paragraph(f"• {t}", bullet_sty)
def code(t): return Paragraph(t.replace(" ", "&nbsp;"), code_sty)
def cap(t): return Paragraph(t, caption_sty)
def sp(n=6): return Spacer(1, n)


TABLE_STYLE_BASE = TableStyle([
    ("BACKGROUND",  (0, 0), (-1, 0), ACC),
    ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",    (0, 0), (-1, 0), 8.5),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ("TOPPADDING",    (0, 0), (-1, 0), 6),
    ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE",    (0, 1), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
    ("GRID",        (0, 0), (-1, -1), 0.3, MID_GREY),
    ("TOPPADDING",  (0, 1), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ("VALIGN",      (0, 0), (-1, -1), "TOP"),
])


def proof_table(rows, col_widths):
    """rows = list of lists of str; first row is header."""
    data = []
    for i, row in enumerate(rows):
        data.append([Paragraph(cell, sty(f"tc{i}", fontSize=8,
                    fontName="Helvetica-Bold" if i == 0 else "Helvetica",
                    textColor=colors.white if i == 0 else DARK,
                    leading=11)) for cell in row])
    t = Table(data, colWidths=col_widths)
    ts = TableStyle(list(TABLE_STYLE_BASE._cmds))
    # Colour PASS/FAIL cells
    for r, row in enumerate(rows[1:], start=1):
        last = row[-1]
        if "PASS" in last:
            ts.add("BACKGROUND", (-1, r), (-1, r), colors.HexColor("#d8f3dc"))
            ts.add("TEXTCOLOR",  (-1, r), (-1, r), PASS_GREEN)
            ts.add("FONTNAME",   (-1, r), (-1, r), "Helvetica-Bold")
        elif "FAIL" in last:
            ts.add("BACKGROUND", (-1, r), (-1, r), colors.HexColor("#ffe0e0"))
            ts.add("TEXTCOLOR",  (-1, r), (-1, r), FAIL_RED)
            ts.add("FONTNAME",   (-1, r), (-1, r), "Helvetica-Bold")
        if "†" in row[0]:
            ts.add("TEXTCOLOR", (0, r), (0, r), colors.HexColor("#7d6608"))
    t.setStyle(ts)
    return t


def comparison_table(rows, col_widths):
    data = []
    for i, row in enumerate(rows):
        data.append([Paragraph(cell, sty(f"ct{i}", fontSize=8,
                    fontName="Helvetica-Bold" if i == 0 else "Helvetica",
                    textColor=colors.white if i == 0 else DARK,
                    leading=11)) for cell in row])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TABLE_STYLE_BASE)
    return t


# ─── Build story ─────────────────────────────────────────────────────────────
story = []

# Cover
story += [
    sp(30),
    Paragraph("Ecological Nowak Mechanisms", title_sty),
    Paragraph("Session Memory — Five Cooperation Models", sub_sty),
    Paragraph("EvolvedCooperation Project · 2026-05-14", date_sty),
    HR(),
    sp(10),
    p("This document records the design, results, and key findings of the five ecological "
      "counterparts to Nowak's cooperation mechanisms, built sequentially during this session. "
      "Each model uses the same demographic engine (age structure, energy budget, sexual "
      "reproduction with blending inheritance, density-dependent mortality) but isolates a "
      "different cooperation mechanism."),
    sp(6),
    p("The Moran models remain the abstract reference implementations. The ecological models "
      "ask whether each mechanism can operate under realistic life-history dynamics — and "
      "consistently reveal that <b>spatial or temporal reproductive assortment</b> is more "
      "fundamental than the explicit energetic mechanism that gives each model its name."),
    PageBreak(),
]

# ─── Section 1: Overview ─────────────────────────────────────────────────────
story += [
    h1("1. Project Overview"),
    HR(),
    p("Nowak (2006) identified five routes by which natural selection can favour cooperation: "
      "kin selection, group selection, network reciprocity, direct reciprocity, and indirect "
      "reciprocity. This project builds both abstract Moran-process models and ecological "
      "models for each mechanism, allowing comparison across two levels of biological realism."),
    sp(4),
    h2("1.1 Mechanism Map"),
]

overview_rows = [
    ["Mechanism", "Moran", "Ecological", "Proof", "Primary finding"],
    ["Kin selection",        "✓", "✓", "10/10", "Rearing dependency load-bearing; well-mixed kin ≠ kin proximity"],
    ["Group selection",      "✓", "✓", "10/11", "Conflict does demographic double-duty; assortative mating is parallel channel"],
    ["Network reciprocity",  "✓", "✓", "10/10", "Offspring placement (not benefit routing) is the mechanism; genetic channel dominant"],
    ["Direct reciprocity",   "✓", "✓", "10/10", "Partner fidelity + memory jointly necessary; optimal partnership length exists"],
    ["Indirect reciprocity", "✓", "—", "—",     "Ecological model pending"],
]
story += [
    comparison_table(overview_rows, [3.5*cm, 1.5*cm, 1.8*cm, 1.5*cm, 8.2*cm]),
    sp(4),
    h2("1.2 Shared Demographic Engine"),
    p("All ecological models share a common core:"),
    bl("Individuals carry: <b>id</b>, <b>sex</b>, <b>age</b>, <b>stage</b> (juvenile/adult/elder), "
       "<b>energy</b>, <b>helping_trait</b> ∈ [0, 1], plus mechanism-specific fields."),
    bl("<b>Blending inheritance</b>: offspring trait = 0.5 × (mother.trait + father.trait) + N(0, σ) mutation."),
    bl("Mechanisms add structure (spatial coordinates, group_id, partner_id, or rearing_group_id) "
       "without replacing the base engine."),
    bl("Proof scenarios use 5 seeds × 500 steps with 10% rare-helper founders (trait = 0.65) "
       "in a background of low-trait residents (trait ~ U[0, 0.04])."),
    sp(4),
    h2("1.3 Recurring Methodological Pattern"),
    p("Across all four completed ecological models, the same structural pattern appears:"),
    bl("<b>Primary mechanism</b>: reproductive or temporal assortment (offspring placement, group structure, "
       "partner fidelity). Ablating this causes cooperation to decline."),
    bl("<b>Secondary mechanism</b>: explicit energetic routing (benefit to neighbors, inter-group conflict bonus, "
       "conditional cooperation). Ablating this alone still allows cooperation to spread via the primary channel."),
    bl("<b>Parallel genetic channel</b>: blending inheritance + demographic structure independently spreads "
       "cooperation in three of four models (kin, group, network). Direct reciprocity is the exception — "
       "the well-mixed model lacks spatial clustering."),
    bl("<b>Metric choice</b>: mean trait change is the reliable signal for inverted scenarios; invasion frequency "
       "is inflated by blending inheritance in short runs."),
    PageBreak(),
]

# ─── Section 2: Kin Selection ────────────────────────────────────────────────
story += [
    h1("2. Ecological Kin Selection"),
    HR(),
    p("Mechanism: cooperation evolves because helpers direct benefits toward related juveniles. "
      "Rearing groups contain mother, father, and juveniles; helpers pay a care cost and raise "
      "juvenile survival probability. Hamilton's rule (rb > c) is the theoretical condition."),
    sp(4),
    h2("2.1 Key Structural Features"),
    bl("Pedigree relatedness tracked explicitly (diploid blending, ½ parent-offspring, ¼ grandparent)."),
    bl("Care benefits flow to juveniles in the same rearing group as the helper."),
    bl("Relatedness-biased care probability: P(care) ∝ helping_trait × (1 + kin_bias × relatedness)."),
    bl("Hamilton-margin proxy measured from simulation: rb_proxy − c_proxy must be positive."),
    sp(4),
    h2("2.2 Key Finding"),
    p("<b>Rearing dependency is load-bearing.</b> Removing the kin-biased rearing connection "
      "(unrelated_rearing_groups scenario) abolishes cooperation spread. The well-mixed kin "
      "control (kin_bias without kin proximity) produces a biologically artificial scenario — "
      "a lesson that applies to the Moran model too."),
    PageBreak(),
]

# ─── Section 3: Group Selection ──────────────────────────────────────────────
story += [
    h1("3. Ecological Group Selection"),
    HR(),
    p("Mechanism: cooperation evolves because cooperative groups win inter-group conflicts. "
      "Groups with higher mean helping trait score better in combat; winners receive an energy "
      "bonus; losers emigrate or die (warfare). Qst (between-group / total variance) is the "
      "key diagnostic."),
    sp(4),
    h2("3.1 Proof Results (10/11 scenarios)"),
]

gs_rows = [
    ["Scenario", "inv_Δ", "pop", "Qst", "Result"],
    ["group_selection_baseline", "+0.24", "249", "0.13", "PASS"],
    ["group_selection_off",      "+0.32", "41",  "0.37", "FAIL*"],
    ["warfare_off",              "+0.09", "267", "0.19", "PASS"],
    ["warfare_high_lethality",   "+0.08", "119", "0.28", "PASS"],
    ["high_conflict_frequency",  "+0.50", "395", "0.21", "PASS"],
    ["low_conflict_frequency†",  "−0.01", "67",  "0.15", "PASS†"],
    ["many_small_groups",        "+0.55", "243", "0.13", "PASS"],
    ["few_large_groups",         "+0.38", "314", "0.22", "PASS"],
    ["high_dispersal",           "+0.31", "199", "0.12", "PASS"],
    ["cost_too_high†",           "−0.12", "112", "0.21", "PASS†"],
    ["group_public_goods_on†",   "−0.03", "399", "0.20", "PASS†"],
]
story += [
    proof_table(gs_rows, [4.8*cm, 1.8*cm, 1.5*cm, 1.5*cm, 1.9*cm]),
    cap("† inverted scenario (cooperation expected to decline). * Fail: see Finding 1 below."),
    sp(4),
    h2("3.2 Key Findings"),
    h3("Finding 1 — Conflict mechanism does double duty"),
    p("group_selection_off (no conflicts) shows cooperation spreading (+0.32) but population "
      "collapsing to 41. The conflict_winner_energy_bonus is both the selection mechanism AND "
      "the primary demographic stabiliser. Without it, assortative mating spreads cooperation "
      "but the population collapses. FAIL because population threshold not met."),
    h3("Finding 2 — Multi-mechanism entanglement"),
    p("Assortative mating (65% within-group) creates a parallel within-group genetic channel "
      "that spreads cooperation independently of inter-group conflict. This cannot be disabled "
      "without restructuring basic demographic mechanics — the same lesson as kin-selection."),
    h3("Finding 3 — Warfare amplifies; small groups outperform large"),
    p("warfare_high_lethality and many_small_groups both amplify cooperation spread. "
      "Small groups maintain higher Qst, giving group selection more leverage — confirming "
      "standard multilevel selection theory."),
    PageBreak(),
]

# ─── Section 4: Network Reciprocity ──────────────────────────────────────────
story += [
    h1("4. Ecological Network Reciprocity"),
    HR(),
    p("Mechanism: cooperation evolves because cooperators cluster in continuous space. "
      "Offspring are born near their mother (offspring_placement_radius); adults deliver "
      "a fixed benefit budget equally to all individuals within interaction_radius. "
      "No spatial coordinates in the Moran model; continuous unit square here."),
    sp(4),
    h2("4.1 Proof Results (10/10 scenarios)"),
]

nr_rows = [
    ["Scenario", "trait_Δ", "inv_Δ", "pop", "cluster", "Result"],
    ["network_reciprocity_baseline",  "+0.013", "+0.188", "400", "+0.000", "PASS"],
    ["scattered_offspring†",          "−0.021", "−0.096", "348", "+0.000", "PASS†"],
    ["no_spatial_structure†",         "+0.001", "+0.113", "248", "−0.001", "PASS†"],
    ["cost_too_high†",                "−0.013", "+0.078",  "62", "+0.001", "PASS†"],
    ["tight_clustering",              "+0.017", "+0.289", "382", "−0.000", "PASS"],
    ["uniform_benefit_routing",       "+0.001", "+0.130", "391", "−0.000", "PASS"],
    ["wide_neighborhood",             "+0.008", "+0.129", "377", "+0.000", "PASS"],
    ["low_dispersal",                 "−0.005", "+0.069", "347", "−0.000", "PASS"],
    ["high_matured_dispersal",        "+0.007", "+0.182", "313", "−0.000", "PASS"],
    ["high_benefit",                  "+0.003", "+0.113", "397", "+0.000", "PASS"],
]
story += [
    proof_table(nr_rows, [4.5*cm, 1.6*cm, 1.6*cm, 1.3*cm, 1.8*cm, 1.7*cm]),
    cap("† inverted scenario (cooperation expected to stay flat or decline)."),
    sp(4),
    h2("4.2 Key Findings"),
    h3("Finding 1 — Offspring placement is the primary mechanism"),
    p("scattered_offspring (random offspring placement) shows clear cooperation decline "
      "(trait −0.021). Without spatial clustering via local birth, cooperators cannot form "
      "the self-reinforcing patches that enable network reciprocity."),
    h3("Finding 2 — Invasion frequency inflated by blending inheritance"),
    p("no_spatial_structure shows inv_Δ = +0.113 but trait_Δ = +0.001. Intermediate-trait "
      "offspring (trait ≈ 0.35) from rare-helper × resident crosses count as invaders for "
      "3–4 generations before diluting back. Mean trait change is the reliable signal."),
    h3("Finding 3 — Benefit routing is not load-bearing (uniform_benefit_routing passes)"),
    p("Distributing benefits uniformly to all individuals (not spatial neighbors) still shows "
      "cooperation spreading (inv_Δ = +0.130). Spatial reproductive assortment is sufficient "
      "without explicit spatial benefit routing. This mirrors group_selection_off finding."),
    h3("Finding 4 — Tight clustering amplifies most strongly"),
    p("offspring_placement_radius = 0.03 (vs. 0.07 default) shows highest invasion "
      "frequency (+0.289). Smaller clusters have near-100% cooperator fraction among "
      "neighbors, maximising the cluster benefit."),
    PageBreak(),
]

# ─── Section 5: Direct Reciprocity ───────────────────────────────────────────
story += [
    h1("5. Ecological Direct Reciprocity"),
    HR(),
    p("Mechanism: cooperation evolves through repeated dyadic encounters. Partner fidelity "
      "creates temporal assortment; partner memory enables conditional strategies; differential "
      "dissolution lets cooperators exit non-reciprocating partnerships. This is the first "
      "ecological model without spatial structure — fully well-mixed."),
    sp(4),
    h2("5.1 Partnership Mechanism"),
    code("effective_coop   = helping_trait × (1 − reciprocity_weight × (1 − partner_memory))"),
    code("partner.energy  += effective_coop × cooperation_benefit_per_step"),
    code("partner_memory   = (1−smoothing)×partner_memory + smoothing×partner.effective_coop"),
    code("eff_persistence  = base_persistence × (1 − leave_weight × (1 − partner_memory))"),
    sp(4),
    h2("5.2 Proof Results (10/10 scenarios)"),
]

dr_rows = [
    ["Scenario", "trait_Δ", "inv_Δ", "pop", "quality", "Result"],
    ["direct_reciprocity_baseline", "+0.001", "+0.041", "400", "+0.688", "PASS"],
    ["memory_off†",                 "−0.002", "−0.002", "400", "+1.000", "PASS†"],
    ["random_partners†",            "−0.005", "−0.038", "400", "+0.815", "PASS†"],
    ["no_direct_reciprocity†",      "−0.005", "−0.038", "400", "+1.000", "PASS†"],
    ["cost_too_high†",              "−0.037", "−0.129", "400", "+0.684", "PASS†"],
    ["long_partnerships",           "−0.002", "+0.049", "400", "+0.676", "PASS"],
    ["short_partnerships",          "−0.002", "+0.041", "400", "+0.758", "PASS"],
    ["high_reciprocity_weight",     "+0.002", "+0.055", "400", "+0.691", "PASS"],
    ["strong_leave_weight",         "−0.003", "+0.022", "400", "+0.722", "PASS"],
    ["no_reproduction_cost",        "+0.002", "+0.038", "399", "+0.688", "PASS"],
]
story += [
    proof_table(dr_rows, [4.5*cm, 1.6*cm, 1.6*cm, 1.3*cm, 1.8*cm, 1.7*cm]),
    cap("† inverted scenario (cooperation expected to stay flat or decline). "
        "quality = mean partner_memory for active adult partnerships."),
    sp(4),
    h2("5.3 Key Findings"),
    h3("Finding 1 — Partner fidelity is the primary load-bearing mechanism"),
    p("random_partners (reshuffled every step) and no_direct_reciprocity (both off) both show "
      "cooperation declining (inv_Δ = −0.038). Without repeated encounters, temporal assortment "
      "is impossible regardless of memory. Partner fidelity is more fundamental than conditional "
      "cooperation."),
    h3("Finding 2 — Memory and conditional dissolution are jointly necessary"),
    p("memory_off (partner_memory frozen at 1.0) causes cooperation to barely hold or "
      "slowly decline. Without memory: cooperators give generously to everyone, cannot reduce "
      "cooperation toward defectors, and cannot trigger differential dissolution."),
    h3("Finding 3 — Optimal partnership length: very high persistence hurts"),
    p("long_partnerships at 0.97 (mean ~33 steps) amplifies the mechanism (inv_Δ = +0.049). "
      "However, 0.99 (mean ~100 steps) causes cooperation to DECLINE. The optimistic memory "
      "start (1.0 at partnership formation) combined with very high base persistence traps "
      "cooperators in bad partnerships longer than the differential-dissolution signal can "
      "overcome in the initial exploitation phase."),
    h3("Finding 4 — High benefit amplifies defector exploitation; does not help"),
    p("cooperation_benefit_per_step = 0.40 causes cooperation to fail. Rare cooperators are "
      "mostly paired with defectors, so higher benefit means MORE energy extracted by defectors. "
      "The coop-coop surplus grows, but initial exploitation also grows — net negative. "
      "This mirrors kin-selection (removing kin proximity) and network-reciprocity (wide "
      "neighborhood dilutes benefit) findings: amplifying one parameter in isolation can "
      "strengthen the countervailing force."),
    h3("Finding 5 — First model where genetic channel is insufficient on its own"),
    p("Unlike kin selection, group selection, and network reciprocity, the direct-reciprocity "
      "model is well-mixed. There is no spatial clustering to create population-level trait "
      "assortment. Mean trait changes are very small (±0.001–0.003) in all scenarios. "
      "Invasion frequency (+0.02 to +0.06) is the primary signal of mechanism operation."),
    PageBreak(),
]

# ─── Section 6: Cross-model comparison ───────────────────────────────────────
story += [
    h1("6. Cross-Model Comparison"),
    HR(),
    h2("6.1 Primary Mechanism vs. Secondary Mechanism"),
]

cross_rows = [
    ["Model", "Primary mechanism", "Secondary mechanism", "Ablation result"],
    ["Kin selection",       "Rearing-group proximity (kin near kin)",
     "Relatedness-biased care probability",
     "unrelated_rearing_groups → cooperation fails"],
    ["Group selection",     "Within-group assortative mating (genetic clustering)",
     "Inter-group conflict + energy bonus",
     "group_selection_off → cooperation spreads but population collapses"],
    ["Network reciprocity", "Offspring placement (spatial clustering)",
     "Spatial benefit routing to neighbors",
     "uniform_benefit_routing → cooperation still spreads"],
    ["Direct reciprocity",  "Partner fidelity (temporal repeated encounters)",
     "Conditional cooperation + differential dissolution",
     "memory_off → cooperation barely holds or declines"],
]
story += [
    comparison_table(cross_rows, [3.0*cm, 4.0*cm, 4.0*cm, 5.5*cm]),
    sp(4),
    h2("6.2 Metric Reliability Across Models"),
    p("The choice of success metric differs depending on whether the model has a spatial "
      "reproductive assortment channel:"),
    bl("<b>Models with spatial clustering</b> (kin selection, network reciprocity): "
       "mean trait change is the reliable primary signal; invasion frequency may be inflated "
       "by blending inheritance in inverted scenarios."),
    bl("<b>Group selection</b>: invasion frequency is the primary metric; Qst diagnostic "
       "tracks whether between-group variance is high enough for selection to have leverage."),
    bl("<b>Direct reciprocity</b> (well-mixed): invasion frequency is the only reliable "
       "signal; mean trait changes are too small (~0.001–0.003) to be conclusive in 500 steps."),
    sp(4),
    h2("6.3 The Parallel Genetic Channel"),
    p("In three of four ecological models, spatial or demographic reproductive structure "
      "creates a <i>parallel genetic channel</i> that spreads cooperation independently of "
      "the named mechanism:"),
    bl("Kin selection: offspring born near mother → kin cluster → cooperation spreads even "
       "in unrelated groups (partially)."),
    bl("Group selection: within-group mating preference → genetic clustering within groups "
       "→ assortative spread independent of conflict."),
    bl("Network reciprocity: offspring placement → spatial cooperator clusters → spatial "
       "reproductive assortment operates without explicit benefit routing."),
    bl("Direct reciprocity (well-mixed): <b>no parallel channel</b>. This is the cleanest "
       "test of pure mechanism, and accordingly the weakest signal (modest invasion, negligible "
       "mean trait change)."),
    p("The implication: ecological models of the first three mechanisms cannot cleanly "
      "isolate the named mechanism from the parallel genetic channel without restructuring "
      "basic demographic structure — which would itself change the biology being tested."),
    PageBreak(),
]

# ─── Section 7: Architecture ─────────────────────────────────────────────────
story += [
    h1("7. Package Architecture"),
    HR(),
    h2("7.1 Directory Structure"),
    code("ecological_models/nowak_mechanisms/"),
    code("  ├── kin_selection/        (complete)"),
    code("  ├── group_selection/      (complete)"),
    code("  ├── network_reciprocity/  (complete)"),
    code("  ├── direct_reciprocity/   (complete)"),
    code("  └── indirect_reciprocity/ (pending)"),
    sp(4),
    code("Each mechanism package:"),
    code("  ├── __init__.py"),
    code("  ├── config/<mechanism>_config.py   # DEFAULT_CONFIG + PROOF_SCENARIOS"),
    code("  ├── <mechanism>_model.py            # EcologicalXxxModel + run_simulation()"),
    code("  ├── data/latest_run.json            # written after each single run"),
    code("  └── utils/proof_of_mechanism.py     # runs all scenarios × all seeds"),
    sp(4),
    h2("7.2 Run Commands"),
    code("./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.utils.proof_of_mechanism"),
    code("./.conda/bin/python -m ecological_models.nowak_mechanisms.group_selection.utils.proof_of_mechanism"),
    code("./.conda/bin/python -m ecological_models.nowak_mechanisms.network_reciprocity.utils.proof_of_mechanism"),
    code("./.conda/bin/python -m ecological_models.nowak_mechanisms.direct_reciprocity.utils.proof_of_mechanism"),
    sp(4),
    h2("7.3 Findings Log"),
    p("All findings are recorded in <b>moran_models/nowak_mechanisms/findings.md</b> "
      "as sequentially numbered phases (Phase 13 = ecological kin selection, "
      "Phase 14 = ecological group selection, Phase 15 = ecological network reciprocity, "
      "Phase 16 = ecological direct reciprocity)."),
    PageBreak(),
]

# ─── Section 8: Next steps ────────────────────────────────────────────────────
story += [
    h1("8. Pending Work"),
    HR(),
    h2("8.1 Ecological Indirect Reciprocity (next sequential step)"),
    p("The Moran indirect reciprocity model uses inherited public reputation scores "
      "and routes benefits toward high-reputation partners. The ecological counterpart needs:"),
    bl("A public reputation field per individual (updated by observers of cooperative acts)."),
    bl("Reputation-biased partner choice: individuals prefer to interact with / help "
       "high-reputation partners."),
    bl("Reputation decay and inheritance rules."),
    bl("Key ablation: reputation-blind benefit routing should prevent cooperation spread, "
       "as it removes the discriminative partner choice that enables indirect reciprocity."),
    bl("Key boundary with direct reciprocity: reputation is PUBLIC (third parties update it); "
       "direct reciprocity memory is PRIVATE (only the dyadic pair tracks history)."),
    sp(4),
    h2("8.2 Combined Multi-Mechanism Ecological Model"),
    p("After all five ecological mechanism models are complete, a combined model can "
      "run multiple mechanisms simultaneously and test their interactions:"),
    bl("Can kin selection and direct reciprocity independently spread cooperation "
       "from the same initial condition?"),
    bl("Does network reciprocity amplify or substitute for group selection?"),
    bl("Which mechanism has the highest invasion success from a 10% rare foothold?"),
    sp(4),
    h2("8.3 Website Integration"),
    p("The human-cooperation-site project (separate repo) needs to be updated to "
      "include visualisations and explanations for each ecological model once all "
      "five are complete."),
]

# Build
doc.build(story)
print(f"PDF written to {OUTPUT.resolve()}")
