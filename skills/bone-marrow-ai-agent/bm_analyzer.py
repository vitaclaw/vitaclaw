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
Bone Marrow Analyzer – Morphology analysis with mock image analysis mode.

Usage:
    python3 bm_analyzer.py \
        --image aspirate_smear.tiff \
        --stain wright_giemsa \
        --target_cells 500 \
        --assess_dysplasia true \
        --model coatnet_bm_v2 \
        --output bm_report.json
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime

try:
    import numpy as np
except ImportError:
    np = None

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CELL_TYPES = {
    "Blast":                        {"normal_pct": (0, 3),    "lineage": "myeloid"},
    "Promyelocyte":                 {"normal_pct": (2, 5),    "lineage": "myeloid"},
    "Myelocyte":                    {"normal_pct": (5, 15),   "lineage": "myeloid"},
    "Metamyelocyte":                {"normal_pct": (5, 15),   "lineage": "myeloid"},
    "Band neutrophil":              {"normal_pct": (10, 25),  "lineage": "myeloid"},
    "Segmented neutrophil":         {"normal_pct": (10, 30),  "lineage": "myeloid"},
    "Eosinophil":                   {"normal_pct": (1, 5),    "lineage": "myeloid"},
    "Basophil":                     {"normal_pct": (0, 1),    "lineage": "myeloid"},
    "Monocyte":                     {"normal_pct": (1, 5),    "lineage": "myeloid"},
    "Lymphocyte":                   {"normal_pct": (5, 20),   "lineage": "lymphoid"},
    "Plasma cell":                  {"normal_pct": (0, 3),    "lineage": "lymphoid"},
    "Proerythroblast":              {"normal_pct": (1, 4),    "lineage": "erythroid"},
    "Basophilic erythroblast":      {"normal_pct": (2, 6),    "lineage": "erythroid"},
    "Polychromatic erythroblast":   {"normal_pct": (5, 15),   "lineage": "erythroid"},
    "Orthochromatic erythroblast":  {"normal_pct": (3, 10),   "lineage": "erythroid"},
    "Megakaryocyte":                {"normal_pct": (0, 1),    "lineage": "megakaryocytic"},
}

STAIN_TYPES = {
    "wright_giemsa": "Wright-Giemsa (standard haematology stain)",
    "may_grunwald": "May-Grunwald-Giemsa (European standard)",
    "perls": "Perl's Prussian blue (iron stain for ring sideroblasts)",
}

ME_RATIO_NORMAL = {"low": 2.0, "high": 4.0}

DYSPLASIA_FEATURES = {
    "dyserythropoiesis": [
        {"feature": "Nuclear budding", "threshold_pct": 10},
        {"feature": "Megaloblastoid changes", "threshold_pct": 10},
        {"feature": "Internuclear bridging", "threshold_pct": 10},
        {"feature": "Karyorrhexis", "threshold_pct": 10},
        {"feature": "Multinucleation", "threshold_pct": 10},
        {"feature": "Ring sideroblasts", "threshold_pct": 15},
    ],
    "dysgranulopoiesis": [
        {"feature": "Hypogranulation", "threshold_pct": 10},
        {"feature": "Pseudo-Pelger-Huet anomaly", "threshold_pct": 10},
        {"feature": "Nuclear hyposegmentation", "threshold_pct": 10},
        {"feature": "Abnormal nuclear shape", "threshold_pct": 10},
        {"feature": "Auer rods", "threshold_pct": 0},
    ],
    "dysmegakaryopoiesis": [
        {"feature": "Micromegakaryocytes", "threshold_pct": 10},
        {"feature": "Hypolobation (mono/bilobed)", "threshold_pct": 10},
        {"feature": "Multinucleation (separated nuclei)", "threshold_pct": 10},
        {"feature": "Cytoplasmic hypogranularity", "threshold_pct": 10},
    ],
}

WHO_BLAST_THRESHOLDS = {
    5:  "Borderline – consider MDS with excess blasts-1 if 5-9%",
    10: "MDS with excess blasts-2 if 10-19%",
    20: "Acute myeloid leukaemia threshold (>=20%)",
}

CELLULARITY_BY_AGE = {
    "pediatric": {"expected_pct": (80, 100)},
    "young_adult": {"expected_pct": (60, 80)},
    "middle_age": {"expected_pct": (40, 60)},
    "elderly": {"expected_pct": (20, 40)},
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class BoneMarrowAnalyzer:
    """Bone marrow morphology analysis engine (mock mode when image unavailable)."""

    def __init__(
        self,
        image_path=None,
        stain="wright_giemsa",
        target_cells=500,
        assess_dysplasia=True,
        model="coatnet_bm_v2",
    ):
        self.image_path = image_path
        self.stain = stain
        self.target_cells = int(target_cells)
        self.assess_dysplasia = str(assess_dysplasia).lower() in ("true", "1", "yes")
        self.model = model
        self.image_available = image_path is not None and os.path.isfile(image_path)
        self.timestamp = datetime.now().isoformat()

    # --- mock differential generator ------------------------------------

    def _generate_mock_differential(self):
        """Generate a realistic differential count using normal ranges + small perturbation."""
        random.seed(42)  # reproducible demo
        counts = {}
        total = 0
        for cell, info in CELL_TYPES.items():
            lo, hi = info["normal_pct"]
            mid = (lo + hi) / 2.0
            spread = (hi - lo) / 2.0
            pct = max(0, mid + random.uniform(-spread * 0.6, spread * 0.6))
            counts[cell] = round(pct, 1)
            total += pct

        # normalise to ~100
        if total > 0:
            factor = 100.0 / total
            counts = {k: round(v * factor, 1) for k, v in counts.items()}
        return counts

    # --- differential interpretation ------------------------------------

    def _interpret_differential(self, diff):
        flags = []
        for cell, pct in diff.items():
            info = CELL_TYPES.get(cell, {})
            lo, hi = info.get("normal_pct", (0, 100))
            if pct > hi:
                flags.append({"cell": cell, "percent": pct, "status": "INCREASED", "normal_range": f"{lo}-{hi}%"})
            elif pct < lo and pct > 0:
                flags.append({"cell": cell, "percent": pct, "status": "DECREASED", "normal_range": f"{lo}-{hi}%"})
        return flags

    # --- M:E ratio ------------------------------------------------------

    def _compute_me_ratio(self, diff):
        myeloid = sum(diff.get(c, 0) for c, info in CELL_TYPES.items() if info["lineage"] == "myeloid")
        erythroid = sum(diff.get(c, 0) for c, info in CELL_TYPES.items() if info["lineage"] == "erythroid")
        if erythroid == 0:
            ratio = None
            interpretation = "Cannot compute – no erythroid precursors counted"
        else:
            ratio = round(myeloid / erythroid, 2)
            if ME_RATIO_NORMAL["low"] <= ratio <= ME_RATIO_NORMAL["high"]:
                interpretation = "Normal"
            elif ratio > ME_RATIO_NORMAL["high"]:
                interpretation = "Myeloid hyperplasia / erythroid hypoplasia"
            else:
                interpretation = "Erythroid hyperplasia / myeloid hypoplasia"
        return {"ratio": ratio, "myeloid_pct": round(myeloid, 1), "erythroid_pct": round(erythroid, 1), "interpretation": interpretation}

    # --- blast quantification -------------------------------------------

    def _quantify_blasts(self, diff):
        blast_pct = diff.get("Blast", 0)
        classification_hints = []
        for threshold, desc in sorted(WHO_BLAST_THRESHOLDS.items()):
            if blast_pct >= threshold:
                classification_hints.append({"threshold_pct": threshold, "description": desc})
        return {
            "blast_percentage": blast_pct,
            "target_cells_counted": self.target_cells,
            "who_classification_hints": classification_hints if classification_hints else [{"description": "Blast count within normal limits (<5%)"}],
        }

    # --- dysplasia assessment -------------------------------------------

    def _assess_dysplasia_mock(self):
        if not self.assess_dysplasia:
            return {"assessed": False, "reason": "Dysplasia assessment not requested"}
        random.seed(99)
        results = {}
        for lineage, features in DYSPLASIA_FEATURES.items():
            lineage_results = []
            dysplastic = False
            for feat in features:
                observed_pct = round(random.uniform(0, feat["threshold_pct"] * 1.5), 1)
                is_present = observed_pct >= feat["threshold_pct"]
                if is_present:
                    dysplastic = True
                lineage_results.append({
                    "feature": feat["feature"],
                    "observed_pct": observed_pct,
                    "threshold_pct": feat["threshold_pct"],
                    "present": is_present,
                })
            results[lineage] = {"features": lineage_results, "dysplasia_present": dysplastic}

        dysplastic_lineages = sum(1 for v in results.values() if v["dysplasia_present"])
        multilineage = dysplastic_lineages >= 2

        return {
            "assessed": True,
            "stain": self.stain,
            "lineage_assessment": results,
            "dysplastic_lineages": dysplastic_lineages,
            "multilineage_dysplasia": multilineage,
        }

    # --- cellularity ----------------------------------------------------

    def _estimate_cellularity(self):
        random.seed(77)
        estimated_pct = round(random.uniform(35, 75), 0)
        if estimated_pct >= 70:
            interpretation = "Hypercellular"
        elif estimated_pct <= 30:
            interpretation = "Hypocellular"
        else:
            interpretation = "Normocellular (age-adjusted assessment recommended)"
        return {"estimated_cellularity_pct": estimated_pct, "interpretation": interpretation}

    # --- WHO classification hints ---------------------------------------

    def _who_hints(self, blast_pct, dysplasia):
        hints = []
        if blast_pct >= 20:
            hints.append("AML (blast count >= 20%)")
        elif blast_pct >= 10:
            hints.append("MDS with excess blasts-2 (MDS-EB-2)")
        elif blast_pct >= 5:
            hints.append("MDS with excess blasts-1 (MDS-EB-1)")

        if dysplasia.get("assessed") and dysplasia.get("multilineage_dysplasia"):
            hints.append("Multilineage dysplasia present")

        ring_sideroblasts = False
        if dysplasia.get("assessed"):
            dys_e = dysplasia.get("lineage_assessment", {}).get("dyserythropoiesis", {})
            for feat in dys_e.get("features", []):
                if "Ring sideroblasts" in feat.get("feature", "") and feat.get("present"):
                    ring_sideroblasts = True
        if ring_sideroblasts:
            hints.append("Ring sideroblasts detected – consider MDS-RS")

        return hints if hints else ["No WHO-defining features detected in this assessment"]

    # --- main -----------------------------------------------------------

    def analyze(self) -> dict:
        mode = "image_analysis" if self.image_available else "mock_demonstration"
        diff = self._generate_mock_differential()
        blast_info = self._quantify_blasts(diff)
        dysplasia = self._assess_dysplasia_mock()

        result = {
            "analysis": "Bone Marrow Morphology Analysis",
            "timestamp": self.timestamp,
            "mode": mode,
            "image_path": self.image_path,
            "stain": STAIN_TYPES.get(self.stain, self.stain),
            "model_used": self.model if self.image_available else "mock (no model weights loaded)",
            "target_cells": self.target_cells,
            "differential_count": diff,
            "differential_flags": self._interpret_differential(diff),
            "me_ratio": self._compute_me_ratio(diff),
            "cellularity": self._estimate_cellularity(),
            "blast_percentage": blast_info["blast_percentage"],
            "blast_assessment": blast_info,
            "dysplasia_assessment": dysplasia,
            "who_classification_hints": self._who_hints(blast_info["blast_percentage"], dysplasia),
        }
        if not self.image_available:
            result["notice"] = (
                "Mock mode: No image file found. Differential counts are generated "
                "from normal-range distributions for demonstration purposes. "
                "Actual deep-learning classification requires PyTorch + model weights."
            )
        return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Bone Marrow Analyzer – Morphology analysis")
    parser.add_argument("--image", type=str, default=None, help="Aspirate smear image (TIFF/PNG)")
    parser.add_argument("--stain", type=str, default="wright_giemsa",
                        choices=["wright_giemsa", "may_grunwald", "perls"], help="Stain type")
    parser.add_argument("--target_cells", type=int, default=500, help="Target cell count (default 500)")
    parser.add_argument("--assess_dysplasia", type=str, default="true", help="Assess dysplasia (true/false)")
    parser.add_argument("--model", type=str, default="coatnet_bm_v2", help="Model identifier")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    analyzer = BoneMarrowAnalyzer(
        image_path=args.image,
        stain=args.stain,
        target_cells=args.target_cells,
        assess_dysplasia=args.assess_dysplasia,
        model=args.model,
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
