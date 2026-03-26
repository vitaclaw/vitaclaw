#!/usr/bin/env python3
# COPYRIGHT NOTICE
# This file is part of the "Universal Biomedical Skills" project.
# Copyright (c) 2026 MD BABU MIA, PhD <md.babu.mia@mssm.edu>
# All Rights Reserved.
#
# This code is proprietary and confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Provenance: Authenticated by MD BABU MIA

"""
Myeloma MRD Analyzer – Multiple myeloma minimal residual disease assessment.

Usage:
    python3 myeloma_mrd.py \
        --flow_fcs bone_marrow_ngf.fcs \
        --ngs_clonotype clonoseq_results.json \
        --ms_mprotein maldi_spectrum.csv \
        --baseline_clone diagnosis_clone.json \
        --treatment_phase post_consolidation \
        --output mrd_report.json
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    pd = None

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

NGF_MARKERS = {
    "aberrant_plasma_cell": {
        "positive": ["CD38++", "CD138+", "CD56+", "CD117+"],
        "negative_dim": ["CD19-", "CD45-/dim", "CD81-/dim", "CD27-/dim"],
    },
    "normal_plasma_cell": {
        "positive": ["CD38++", "CD138+", "CD19+", "CD45+", "CD27+"],
        "negative": ["CD56-", "CD117-"],
    },
    "sensitivity": "10^-5 to 10^-6",
}

NGS_SPECS = {
    "method": "ClonoSEQ-style IGH/IGK/IGL VDJ rearrangement tracking",
    "sensitivity": "10^-6",
    "quantification": "clone frequency among total nucleated cells",
}

MS_SPECS = {
    "method": "MALDI-TOF mass spectrometry",
    "sensitivity_mg_L": 50,
    "application": "M-protein isotype detection and quantification",
}

IMWG_RESPONSE = {
    "sCR": {
        "label": "Stringent Complete Response",
        "criteria": [
            "Negative immunofixation on serum and urine",
            "Normal free light chain ratio",
            "No clonal plasma cells by immunohistochemistry or flow",
        ],
    },
    "CR": {
        "label": "Complete Response",
        "criteria": [
            "Negative immunofixation on serum and urine",
            "< 5% plasma cells in bone marrow",
        ],
    },
    "VGPR": {
        "label": "Very Good Partial Response",
        "criteria": [
            "M-protein detectable by immunofixation but not electrophoresis",
            "OR >= 90% reduction in serum M-protein",
        ],
    },
    "PR": {
        "label": "Partial Response",
        "criteria": [
            ">= 50% reduction in serum M-protein",
            "AND >= 90% reduction in 24h urine M-protein or < 200 mg/24h",
        ],
    },
    "MR": {
        "label": "Minimal Response",
        "criteria": ["25-49% reduction in serum M-protein"],
    },
    "SD": {
        "label": "Stable Disease",
        "criteria": ["Not meeting criteria for CR, VGPR, PR, MR, or PD"],
    },
    "PD": {
        "label": "Progressive Disease",
        "criteria": [
            ">= 25% increase from lowest response value in serum M-protein (absolute >= 0.5 g/dL)",
            "OR bone marrow plasma cell increase >= 10%",
        ],
    },
}

TREATMENT_PHASES = ["induction", "consolidation", "post_consolidation", "maintenance"]

M_PROTEIN_ISOTYPES = {
    "IgG_kappa": "Most common (~35%)",
    "IgG_lambda": "~20%",
    "IgA_kappa": "~12%",
    "IgA_lambda": "~8%",
    "IgM_kappa": "Rare in myeloma; consider Waldenstrom's",
    "IgD_lambda": "Rare, aggressive",
    "kappa_light_chain": "Light chain myeloma (~15%)",
    "lambda_light_chain": "Light chain myeloma (~7%)",
    "biclonal": "Biclonal gammopathy",
    "non_secretory": "Non-secretory myeloma (~3%)",
}

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_FLOW = {
    "total_events": 5000000,
    "total_plasma_cells": 450,
    "aberrant_plasma_cells": 3,
    "normal_plasma_cells": 447,
    "aberrant_markers": ["CD38++", "CD138+", "CD56+", "CD19-", "CD45-/dim"],
    "sensitivity_achieved": "2e-6",
}

DEMO_NGS = {
    "baseline_clonotype": "IGHV3-23*01_IGHD6-19*01_IGHJ4*02",
    "baseline_clone_frequency": 0.35,
    "current_clone_frequency": 0.000004,
    "total_sequences": 1200000,
    "clone_sequences": 5,
    "sensitivity_achieved": "8.3e-7",
    "mrd_status": "POSITIVE",
}

DEMO_MS = {
    "isotype": "IgG_kappa",
    "m_protein_detected": False,
    "m_protein_level_mg_L": 0,
    "baseline_m_protein_g_dL": 3.8,
    "polyclonal_background": "present (immune reconstitution)",
}

DEMO_BASELINE = {
    "diagnosis_date": "2023-06-15",
    "isotype": "IgG_kappa",
    "baseline_m_protein_g_dL": 3.8,
    "baseline_bm_plasma_cell_pct": 55,
    "baseline_clonotype": "IGHV3-23*01_IGHD6-19*01_IGHJ4*02",
    "baseline_clone_frequency": 0.35,
    "cytogenetics": {
        "del17p": False,
        "t_4_14": True,
        "t_14_16": False,
        "gain_1q": True,
        "del_13q": True,
    },
    "iss_stage": "II",
    "r_iss_stage": "II",
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class MyelomaMRDAnalyzer:
    """Multiple myeloma MRD assessment across multiple modalities."""

    def __init__(
        self,
        flow_path=None,
        ngs_path=None,
        ms_path=None,
        baseline_path=None,
        treatment_phase="post_consolidation",
    ):
        self.flow = self._load_json(flow_path, DEMO_FLOW)
        self.ngs = self._load_json(ngs_path, DEMO_NGS)
        self.ms = self._load_ms(ms_path)
        self.baseline = self._load_json(baseline_path, DEMO_BASELINE)
        self.treatment_phase = treatment_phase
        self.timestamp = datetime.now().isoformat()

    # --- loaders --------------------------------------------------------

    @staticmethod
    def _load_json(path, default):
        if path and os.path.isfile(path):
            with open(path) as fh:
                return json.load(fh)
        return default

    def _load_ms(self, path):
        if path and os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext == ".json":
                with open(path) as fh:
                    return json.load(fh)
            if ext == ".csv" and pd is not None:
                df = pd.read_csv(path)
                return df.to_dict(orient="records")[0] if len(df) else DEMO_MS
        return DEMO_MS

    # --- NGF analysis ---------------------------------------------------

    def _analyze_ngf(self):
        total = self.flow.get("total_events", 0)
        aberrant = self.flow.get("aberrant_plasma_cells", 0)
        normal = self.flow.get("normal_plasma_cells", 0)

        if total > 0:
            aberrant_freq = aberrant / total
        else:
            aberrant_freq = 0

        mrd_negative = aberrant_freq < 1e-5
        mrd_status = "NEGATIVE" if mrd_negative else "POSITIVE"
        mrd_level = f"{aberrant_freq:.2e}" if not mrd_negative else f"< 10^-5 ({aberrant_freq:.2e})"

        return {
            "method": "Next-Generation Flow (NGF)",
            "total_events_acquired": total,
            "aberrant_plasma_cells": aberrant,
            "normal_plasma_cells": normal,
            "aberrant_frequency": float(f"{aberrant_freq:.2e}"),
            "aberrant_markers": self.flow.get("aberrant_markers", NGF_MARKERS["aberrant_plasma_cell"]["positive"]),
            "sensitivity_achieved": self.flow.get("sensitivity_achieved", NGF_MARKERS["sensitivity"]),
            "mrd_status": mrd_status,
            "mrd_level": mrd_level,
        }

    # --- NGS analysis ---------------------------------------------------

    def _analyze_ngs(self):
        baseline_freq = self.ngs.get("baseline_clone_frequency", 0)
        current_freq = self.ngs.get("current_clone_frequency", 0)
        total_seq = self.ngs.get("total_sequences", 0)
        clone_seq = self.ngs.get("clone_sequences", 0)

        mrd_negative = current_freq < 1e-6
        mrd_status = "NEGATIVE" if mrd_negative else "POSITIVE"

        log_reduction = None
        if baseline_freq > 0 and current_freq > 0:
            log_reduction = round(math.log10(baseline_freq / current_freq), 2)

        return {
            "method": "NGS (ClonoSEQ-style VDJ tracking)",
            "baseline_clonotype": self.ngs.get("baseline_clonotype", "N/A"),
            "baseline_clone_frequency": baseline_freq,
            "current_clone_frequency": current_freq,
            "clone_sequences": clone_seq,
            "total_sequences": total_seq,
            "log_reduction": log_reduction,
            "sensitivity_achieved": self.ngs.get("sensitivity_achieved", NGS_SPECS["sensitivity"]),
            "mrd_status": mrd_status,
        }

    # --- Mass spectrometry analysis -------------------------------------

    def _analyze_ms(self):
        detected = self.ms.get("m_protein_detected", False)
        level = self.ms.get("m_protein_level_mg_L", 0)
        isotype = self.ms.get("isotype", "unknown")
        baseline = self.ms.get("baseline_m_protein_g_dL", 0)

        reduction_pct = None
        if baseline > 0:
            current_g_dL = level / 10000.0  # mg/L to g/dL approximation
            reduction_pct = round((1 - current_g_dL / baseline) * 100, 1)

        return {
            "method": "MALDI-TOF Mass Spectrometry",
            "isotype": isotype,
            "isotype_description": M_PROTEIN_ISOTYPES.get(isotype, "Unknown isotype"),
            "m_protein_detected": detected,
            "m_protein_level_mg_L": level,
            "baseline_m_protein_g_dL": baseline,
            "reduction_pct": reduction_pct,
            "sensitivity_mg_L": MS_SPECS["sensitivity_mg_L"],
            "polyclonal_background": self.ms.get("polyclonal_background", "not assessed"),
            "mrd_status": "POSITIVE" if detected else "NEGATIVE",
        }

    # --- multi-modal integration ----------------------------------------

    def _integrate_mrd(self, ngf, ngs, ms):
        statuses = {
            "ngf": ngf["mrd_status"],
            "ngs": ngs["mrd_status"],
            "ms": ms["mrd_status"],
        }
        concordance = len(set(statuses.values())) == 1
        positive_count = sum(1 for s in statuses.values() if s == "POSITIVE")

        if positive_count == 0:
            integrated = "MRD NEGATIVE (all modalities concordant)"
        elif positive_count == len(statuses):
            integrated = "MRD POSITIVE (all modalities concordant)"
        else:
            integrated = f"MRD DISCORDANT ({positive_count}/{len(statuses)} positive)"

        return {
            "modality_statuses": statuses,
            "concordance": concordance,
            "integrated_mrd_status": integrated,
            "most_sensitive_result": ngs["mrd_status"],
            "note": "NGS typically offers highest sensitivity (10^-6); use as primary MRD marker.",
        }

    # --- IMWG response category -----------------------------------------

    def _determine_response(self, ngf, ngs, ms):
        ms_detected = ms["m_protein_detected"]
        reduction = ms.get("reduction_pct", 0)
        aberrant_pc = ngf.get("aberrant_frequency", 1)

        # Simplified response determination
        if not ms_detected and aberrant_pc < 1e-5 and ngs["mrd_status"] == "NEGATIVE":
            category = "sCR"
        elif not ms_detected and aberrant_pc < 0.05:
            category = "CR"
        elif reduction and reduction >= 90:
            category = "VGPR"
        elif reduction and reduction >= 50:
            category = "PR"
        elif reduction and reduction >= 25:
            category = "MR"
        elif reduction and reduction < 0:
            category = "PD"
        else:
            category = "SD"

        resp = IMWG_RESPONSE.get(category, IMWG_RESPONSE["SD"])
        return {
            "category": category,
            "label": resp["label"],
            "criteria": resp["criteria"],
            "treatment_phase": self.treatment_phase,
        }

    # --- IMWG sustained MRD negativity ----------------------------------

    def _sustained_mrd(self, ngs):
        # In real implementation, would compare serial MRD tests >= 1 year apart
        return {
            "sustained_mrd_negativity": False,
            "definition": "MRD negative on two assessments >= 1 year apart",
            "note": "Requires longitudinal data – single timepoint assessed here.",
            "current_mrd_status": ngs["mrd_status"],
        }

    # --- kinetic modelling ----------------------------------------------

    def _kinetic_model(self, ngs):
        baseline_freq = ngs.get("baseline_clone_frequency", 0)
        current_freq = ngs.get("current_clone_frequency", 0)

        if baseline_freq > 0 and current_freq > 0 and current_freq < baseline_freq:
            log_reduction = math.log10(baseline_freq / current_freq)
            estimated_trajectory = "declining"
        elif current_freq >= baseline_freq and baseline_freq > 0:
            log_reduction = 0
            estimated_trajectory = "stable_or_rising"
        else:
            log_reduction = None
            estimated_trajectory = "insufficient data"

        # Doubling time estimation (mock – would need serial data)
        doubling_time_days = None
        if current_freq > 0 and current_freq < 0.01:
            # Rough estimate assuming exponential kinetics
            doubling_time_days = round(180 / max(math.log2(max(current_freq, 1e-8) / 1e-8), 1), 0)

        return {
            "tumor_burden_trajectory": estimated_trajectory,
            "log_reduction_from_baseline": log_reduction,
            "estimated_doubling_time_days": doubling_time_days,
            "model_type": "exponential_decay_approximation",
            "note": "Accurate kinetic modelling requires >= 3 serial MRD measurements.",
        }

    # --- prognostic implications ----------------------------------------

    def _prognostic_implications(self, integrated, response):
        implications = []
        cytogenetics = self.baseline.get("cytogenetics", {})

        if "NEGATIVE" in integrated["integrated_mrd_status"]:
            implications.append("MRD negativity is associated with improved PFS and OS across risk groups.")
            implications.append("Consider maintenance therapy to sustain MRD-negative status.")
        else:
            implications.append("MRD positivity may indicate need for treatment intensification or change.")

        if cytogenetics.get("del17p"):
            implications.append("High-risk: del(17p) present – closer monitoring recommended.")
        if cytogenetics.get("t_4_14"):
            implications.append("High-risk: t(4;14) present – consider proteasome inhibitor-based maintenance.")
        if cytogenetics.get("gain_1q"):
            implications.append("Adverse: gain(1q) present – associated with poorer outcomes.")

        r_iss = self.baseline.get("r_iss_stage", "unknown")
        if r_iss == "III":
            implications.append("R-ISS Stage III – high-risk disease; aggressive monitoring advised.")

        return {
            "prognostic_implications": implications,
            "r_iss_stage": r_iss,
            "cytogenetics": cytogenetics,
            "current_response": response["category"],
        }

    # --- main -----------------------------------------------------------

    def analyze(self) -> dict:
        ngf = self._analyze_ngf()
        ngs = self._analyze_ngs()
        ms = self._analyze_ms()
        integrated = self._integrate_mrd(ngf, ngs, ms)
        response = self._determine_response(ngf, ngs, ms)

        return {
            "analysis": "Multiple Myeloma MRD Assessment",
            "timestamp": self.timestamp,
            "treatment_phase": self.treatment_phase,
            "baseline_summary": {
                "diagnosis_date": self.baseline.get("diagnosis_date"),
                "isotype": self.baseline.get("isotype"),
                "iss_stage": self.baseline.get("iss_stage"),
                "r_iss_stage": self.baseline.get("r_iss_stage"),
                "baseline_bm_plasma_cell_pct": self.baseline.get("baseline_bm_plasma_cell_pct"),
            },
            "ngf_result": ngf,
            "ngs_result": ngs,
            "ms_result": ms,
            "integrated_mrd_status": integrated,
            "imwg_response": response,
            "sustained_mrd": self._sustained_mrd(ngs),
            "kinetic_model": self._kinetic_model(ngs),
            "prognostic_implications": self._prognostic_implications(integrated, response),
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Myeloma MRD Analyzer – Multi-modal MRD assessment")
    parser.add_argument("--flow_fcs", type=str, default=None, help="NGF flow cytometry data (FCS/JSON)")
    parser.add_argument("--ngs_clonotype", type=str, default=None, help="ClonoSEQ NGS results JSON")
    parser.add_argument("--ms_mprotein", type=str, default=None, help="MALDI-TOF M-protein CSV/JSON")
    parser.add_argument("--baseline_clone", type=str, default=None, help="Baseline diagnosis clone JSON")
    parser.add_argument("--treatment_phase", type=str, default="post_consolidation",
                        choices=TREATMENT_PHASES, help="Treatment phase")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    analyzer = MyelomaMRDAnalyzer(
        flow_path=args.flow_fcs,
        ngs_path=args.ngs_clonotype,
        ms_path=args.ms_mprotein,
        baseline_path=args.baseline_clone,
        treatment_phase=args.treatment_phase,
    )
    result = analyzer.analyze()
    output_json = json.dumps(result, indent=2, default=str)

    if args.output:
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
        with open(args.output, "w") as fh:
            fh.write(output_json)
        print(f"[INFO] Report written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"
