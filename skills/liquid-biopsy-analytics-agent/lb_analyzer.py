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
Multi-analyte Liquid Biopsy Analysis.

Integrates ctDNA variants, tumor protein markers, methylation patterns, and
CTC data for comprehensive liquid biopsy interpretation with CHIP filtering,
resistance mutation detection, and clinical utility scoring.
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# CHIP genes for filtering
CHIP_GENES = [
    "DNMT3A", "TET2", "ASXL1", "PPM1D", "TP53", "JAK2", "SF3B1",
    "SRSF2", "IDH1", "IDH2", "GNB1", "CBL", "NRAS", "KRAS",
    "GNAS", "MYD88", "U2AF1", "ZRSR2", "BCOR", "STAG2",
]

CHIP_VAF_THRESHOLD = 10.0  # percent

# Known resistance patterns
RESISTANCE_PATTERNS = {
    "EGFR_T790M": {
        "gene": "EGFR", "mutation": "T790M",
        "context": "Acquired resistance to 1st/2nd-gen EGFR TKIs",
        "actionable": "Osimertinib (3rd-gen EGFR TKI)",
    },
    "EGFR_C797S": {
        "gene": "EGFR", "mutation": "C797S",
        "context": "Acquired resistance to osimertinib",
        "actionable": "Combination strategies or clinical trials",
    },
    "ESR1_mutations": {
        "gene": "ESR1", "mutation": "D538G/Y537S/Y537N/Y537C/E380Q",
        "context": "Acquired resistance to aromatase inhibitors in HR+ breast cancer",
        "actionable": "Fulvestrant, elacestrant, or novel SERDs",
    },
    "FGFR_amplification": {
        "gene": "FGFR1/2/3", "mutation": "amplification",
        "context": "Resistance to various targeted therapies",
        "actionable": "FGFR inhibitors (erdafitinib, futibatinib)",
    },
    "MET_amplification": {
        "gene": "MET", "mutation": "amplification",
        "context": "Bypass resistance to EGFR TKIs",
        "actionable": "MET inhibitors (capmatinib, tepotinib)",
    },
    "KRAS_mutations_CRC": {
        "gene": "KRAS", "mutation": "G12/G13/Q61/A146",
        "context": "Acquired resistance to anti-EGFR therapy in CRC",
        "actionable": "Discontinue anti-EGFR; consider rechallenge after ctDNA clearance",
    },
    "PIK3CA_mutations": {
        "gene": "PIK3CA", "mutation": "E545K/H1047R",
        "context": "PI3K pathway activation",
        "actionable": "PI3K inhibitors (alpelisib)",
    },
    "RB1_loss": {
        "gene": "RB1", "mutation": "loss/truncation",
        "context": "Resistance to CDK4/6 inhibitors",
        "actionable": "Alternative therapies",
    },
}

# Tumor protein markers
TUMOR_MARKERS = {
    "CEA": {"normal_max": 5.0, "unit": "ng/mL", "cancers": ["colorectal", "lung", "gastric"]},
    "CA-125": {"normal_max": 35.0, "unit": "U/mL", "cancers": ["ovarian", "endometrial"]},
    "CA19-9": {"normal_max": 37.0, "unit": "U/mL", "cancers": ["pancreatic", "biliary"]},
    "PSA": {"normal_max": 4.0, "unit": "ng/mL", "cancers": ["prostate"]},
    "AFP": {"normal_max": 10.0, "unit": "ng/mL", "cancers": ["liver", "germ_cell"]},
    "HE4": {"normal_max": 150.0, "unit": "pmol/L", "cancers": ["ovarian"]},
}


class LiquidBiopsyAnalyzer:
    """Multi-analyte liquid biopsy analysis with CHIP filtering and resistance detection."""

    def __init__(self, ctdna_variants_path=None, timepoints=None,
                 tumor_markers_path=None, baseline_tissue_path=None,
                 analysis_mode="response_resistance", chip_filter=True):
        self.ctdna_variants_path = ctdna_variants_path
        self.timepoints = timepoints or ["week0", "week4", "week8", "week12"]
        self.tumor_markers_path = tumor_markers_path
        self.baseline_tissue_path = baseline_tissue_path
        self.analysis_mode = analysis_mode
        self.chip_filter = chip_filter
        self.variants = []
        self.baseline_variants = set()
        self.marker_data = []

    def _load_ctdna_variants(self):
        """Load ctDNA variants from VCF or generate demo data."""
        if self.ctdna_variants_path and os.path.isfile(self.ctdna_variants_path):
            variants = []
            with open(self.ctdna_variants_path, "r") as fh:
                for line in fh:
                    if line.startswith("#"):
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 5:
                        info = parts[7] if len(parts) > 7 else ""
                        variants.append({
                            "chrom": parts[0], "pos": parts[1], "id": parts[2],
                            "ref": parts[3], "alt": parts[4],
                            "info": info,
                        })
            return variants
        return self._generate_demo_variants()

    def _generate_demo_variants(self):
        """Generate demo longitudinal ctDNA variant data."""
        demo_mutations = [
            {"gene": "KRAS", "aa_change": "G12D", "vafs": [4.5, 2.1, 0.3, 0.0]},
            {"gene": "TP53", "aa_change": "R175H", "vafs": [3.2, 1.5, 0.2, 0.0]},
            {"gene": "APC", "aa_change": "R876*", "vafs": [5.1, 2.8, 0.4, 0.0]},
            {"gene": "PIK3CA", "aa_change": "E545K", "vafs": [2.0, 0.9, 0.1, 0.0]},
            {"gene": "DNMT3A", "aa_change": "R882H", "vafs": [1.2, 1.3, 1.1, 1.2]},  # CHIP
            {"gene": "TET2", "aa_change": "Q1034*", "vafs": [0.8, 0.9, 0.7, 0.8]},  # CHIP
            {"gene": "EGFR", "aa_change": "T790M", "vafs": [0.0, 0.0, 0.1, 0.5]},  # Emerging resistance
        ]
        variants = []
        for mut in demo_mutations:
            for i, tp in enumerate(self.timepoints):
                vaf = mut["vafs"][i] if i < len(mut["vafs"]) else 0.0
                variants.append({
                    "gene": mut["gene"],
                    "aa_change": mut["aa_change"],
                    "timepoint": tp,
                    "vaf_percent": vaf,
                    "depth": 15000,
                    "alt_reads": int(vaf / 100.0 * 15000),
                    "in_baseline_tissue": mut["gene"] not in ["DNMT3A", "TET2"],
                })
        return variants

    def _load_baseline_tissue(self):
        """Load baseline tissue variants (MAF format) or return demo set."""
        if self.baseline_tissue_path and os.path.isfile(self.baseline_tissue_path):
            genes = set()
            with open(self.baseline_tissue_path, "r") as fh:
                header = fh.readline()
                for line in fh:
                    parts = line.strip().split("\t")
                    if parts:
                        genes.add(parts[0])
            return genes
        return {"KRAS", "TP53", "APC", "PIK3CA", "SMAD4"}

    def _load_tumor_markers(self):
        """Load tumor marker values or generate demo data."""
        if self.tumor_markers_path and os.path.isfile(self.tumor_markers_path):
            markers = []
            with open(self.tumor_markers_path, "r") as fh:
                header = fh.readline().strip().split(",")
                for line in fh:
                    fields = line.strip().split(",")
                    markers.append(dict(zip(header, fields)))
            return markers
        return [
            {"timepoint": "week0", "CEA": "45.2", "CA19-9": "120.0"},
            {"timepoint": "week4", "CEA": "22.1", "CA19-9": "65.0"},
            {"timepoint": "week8", "CEA": "8.5", "CA19-9": "30.0"},
            {"timepoint": "week12", "CEA": "3.2", "CA19-9": "18.0"},
        ]

    def _filter_chip(self, variants):
        """Filter CHIP variants: exclude CHIP gene variants with VAF < threshold unless in baseline tissue."""
        if not self.chip_filter:
            return variants, []
        filtered = []
        chip_removed = []
        for v in variants:
            gene = v.get("gene", "")
            vaf = float(v.get("vaf_percent", 0))
            in_tissue = v.get("in_baseline_tissue", False)
            if gene in CHIP_GENES and vaf < CHIP_VAF_THRESHOLD and not in_tissue:
                chip_removed.append({
                    "gene": gene,
                    "aa_change": v.get("aa_change", ""),
                    "vaf_percent": vaf,
                    "reason": f"CHIP gene with VAF {vaf}% < {CHIP_VAF_THRESHOLD}% and not in baseline tissue",
                })
            else:
                filtered.append(v)
        return filtered, chip_removed

    def _analyze_ctdna_trend(self, variants):
        """Analyze ctDNA VAF trends across timepoints."""
        gene_trends = {}
        for v in variants:
            gene = v.get("gene", "UNKNOWN")
            aa = v.get("aa_change", "")
            key = f"{gene}_{aa}"
            if key not in gene_trends:
                gene_trends[key] = {"gene": gene, "aa_change": aa, "timepoints": []}
            gene_trends[key]["timepoints"].append({
                "timepoint": v.get("timepoint", ""),
                "vaf_percent": float(v.get("vaf_percent", 0)),
            })
        trends = []
        for key, data in gene_trends.items():
            vafs = [tp["vaf_percent"] for tp in data["timepoints"]]
            if len(vafs) >= 2:
                if vafs[-1] > vafs[0]:
                    direction = "rising"
                elif vafs[-1] < vafs[0] * 0.1:
                    direction = "cleared"
                elif vafs[-1] < vafs[0]:
                    direction = "declining"
                else:
                    direction = "stable"
            else:
                direction = "single_timepoint"
            trends.append({
                "mutation": key,
                "gene": data["gene"],
                "aa_change": data["aa_change"],
                "direction": direction,
                "vaf_values": vafs,
                "timepoints": data["timepoints"],
            })
        return trends

    def _analyze_tumor_markers(self, marker_data):
        """Analyze tumor protein marker trends."""
        marker_trends = {}
        for row in marker_data:
            tp = row.get("timepoint", "")
            for marker_name, marker_info in TUMOR_MARKERS.items():
                if marker_name in row:
                    val = float(row[marker_name])
                    if marker_name not in marker_trends:
                        marker_trends[marker_name] = {
                            "normal_max": marker_info["normal_max"],
                            "unit": marker_info["unit"],
                            "values": [],
                        }
                    marker_trends[marker_name]["values"].append({
                        "timepoint": tp,
                        "value": val,
                        "elevated": val > marker_info["normal_max"],
                    })
        results = {}
        for name, data in marker_trends.items():
            vals = [v["value"] for v in data["values"]]
            if len(vals) >= 2:
                direction = "declining" if vals[-1] < vals[0] else "rising"
            else:
                direction = "single_timepoint"
            results[name] = {
                "normal_max": data["normal_max"],
                "unit": data["unit"],
                "direction": direction,
                "values": data["values"],
            }
        return results

    def _compute_concordance(self, ctdna_trends, marker_trends):
        """Compute multi-modal concordance between ctDNA and protein markers."""
        ctdna_overall = "declining"
        if ctdna_trends:
            directions = [t["direction"] for t in ctdna_trends]
            if any(d == "rising" for d in directions):
                ctdna_overall = "rising"
            elif all(d in ("cleared", "declining") for d in directions):
                ctdna_overall = "declining"
        marker_overall = "declining"
        for name, data in marker_trends.items():
            if data["direction"] == "rising":
                marker_overall = "rising"
                break
        concordant = ctdna_overall == marker_overall
        return {
            "ctdna_overall_direction": ctdna_overall,
            "marker_overall_direction": marker_overall,
            "concordant": concordant,
            "interpretation": (
                "ctDNA and protein markers are concordant"
                if concordant else
                "Discordance between ctDNA and protein markers — further investigation recommended"
            ),
        }

    def _detect_resistance_mutations(self, ctdna_trends):
        """Detect emerging resistance mutations."""
        emerging = []
        for trend in ctdna_trends:
            if trend["direction"] == "rising":
                gene = trend["gene"]
                aa = trend["aa_change"]
                for pattern_key, pattern in RESISTANCE_PATTERNS.items():
                    if gene == pattern["gene"] or gene in pattern["gene"]:
                        if aa in pattern["mutation"] or pattern["mutation"] in aa:
                            emerging.append({
                                "mutation": trend["mutation"],
                                "pattern": pattern_key,
                                "context": pattern["context"],
                                "actionable": pattern["actionable"],
                                "vaf_trend": trend["vaf_values"],
                            })
                            break
                else:
                    if trend["vaf_values"] and trend["vaf_values"][-1] > 0.1:
                        emerging.append({
                            "mutation": trend["mutation"],
                            "pattern": "novel_emerging",
                            "context": "New or rising mutation during treatment",
                            "actionable": "Assess for resistance mechanism",
                            "vaf_trend": trend["vaf_values"],
                        })
        return emerging

    def _conceptual_methylation_analysis(self):
        """Conceptual cfDNA methylation analysis (placeholder)."""
        return {
            "status": "conceptual",
            "description": "cfDNA methylation-based tissue-of-origin deconvolution",
            "methods": [
                "CpG island methylation profiling",
                "Tissue-of-origin classification from methylation patterns",
                "Early detection scores from multi-cancer methylation panels",
            ],
            "note": "Requires bisulfite sequencing or enzymatic methylation sequencing data",
        }

    def _conceptual_ctc_analysis(self):
        """Conceptual CTC enumeration analysis (placeholder)."""
        return {
            "status": "conceptual",
            "description": "Circulating tumor cell enumeration and characterization",
            "thresholds": {
                "metastatic_breast": ">=5 CTCs per 7.5mL = poor prognosis",
                "metastatic_prostate": ">=5 CTCs per 7.5mL = poor prognosis",
                "metastatic_colorectal": ">=3 CTCs per 7.5mL = poor prognosis",
            },
            "note": "Requires CellSearch or equivalent CTC enumeration platform",
        }

    def _score_clinical_utility(self, ctdna_trends, resistance, concordance):
        """Score clinical utility of the liquid biopsy results."""
        score = 0
        reasons = []
        if ctdna_trends:
            score += 2
            reasons.append("ctDNA mutation tracking available")
        if resistance:
            score += 3
            reasons.append(f"{len(resistance)} resistance mutation(s) detected — actionable")
        if concordance.get("concordant"):
            score += 1
            reasons.append("Multi-modal concordance confirmed")
        else:
            score += 2
            reasons.append("Discordance detected — clinically informative")
        level = "high" if score >= 5 else "moderate" if score >= 3 else "low"
        return {
            "utility_score": score,
            "utility_level": level,
            "reasons": reasons,
        }

    def analyze(self):
        """Run multi-analyte liquid biopsy analysis."""
        raw_variants = self._load_ctdna_variants()
        self.baseline_variants = self._load_baseline_tissue()
        marker_data = self._load_tumor_markers()

        # Mark baseline tissue presence
        for v in raw_variants:
            if "in_baseline_tissue" not in v:
                v["in_baseline_tissue"] = v.get("gene", "") in self.baseline_variants

        filtered_variants, chip_removed = self._filter_chip(raw_variants)
        ctdna_trends = self._analyze_ctdna_trend(filtered_variants)
        marker_trends = self._analyze_tumor_markers(marker_data)
        concordance = self._compute_concordance(ctdna_trends, marker_trends)
        resistance = self._detect_resistance_mutations(ctdna_trends)
        methylation = self._conceptual_methylation_analysis()
        ctc = self._conceptual_ctc_analysis()
        utility = self._score_clinical_utility(ctdna_trends, resistance, concordance)

        actionable = []
        for r in resistance:
            if r.get("actionable"):
                actionable.append({
                    "mutation": r["mutation"],
                    "recommendation": r["actionable"],
                })

        results = {
            "analysis": "multi_analyte_liquid_biopsy",
            "analysis_date": datetime.now().isoformat(),
            "analysis_mode": self.analysis_mode,
            "ctdna_trend": ctdna_trends,
            "chip_filtered_variants": chip_removed,
            "chip_filter_applied": self.chip_filter,
            "tumor_marker_trend": marker_trends,
            "multi_modal_concordance": concordance,
            "resistance_mutations": resistance,
            "actionable_findings": actionable,
            "clinical_utility": utility,
            "methylation_analysis": methylation,
            "ctc_analysis": ctc,
        }
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Multi-analyte liquid biopsy analysis"
    )
    parser.add_argument("--ctdna_variants", default=None,
                        help="Path to longitudinal ctDNA variants (VCF)")
    parser.add_argument("--timepoints", default="week0,week4,week8,week12",
                        help="Comma-separated timepoint labels")
    parser.add_argument("--tumor_markers", default=None,
                        help="Path to tumor marker values (CSV)")
    parser.add_argument("--baseline_tissue", default=None,
                        help="Path to baseline tissue mutations (MAF)")
    parser.add_argument("--analysis", default="response_resistance",
                        help="Analysis mode (response_resistance, monitoring)")
    parser.add_argument("--chip_filter", default="true",
                        help="Apply CHIP filtering (true/false)")
    parser.add_argument("--output", default="lb_report/",
                        help="Output directory or JSON file")
    args = parser.parse_args()

    timepoints = args.timepoints.split(",")
    chip_filter = args.chip_filter.lower() in ("true", "1", "yes")

    analyzer = LiquidBiopsyAnalyzer(
        ctdna_variants_path=args.ctdna_variants,
        timepoints=timepoints,
        tumor_markers_path=args.tumor_markers,
        baseline_tissue_path=args.baseline_tissue,
        analysis_mode=args.analysis,
        chip_filter=chip_filter,
    )

    results = analyzer.analyze()

    output_path = args.output
    if output_path.endswith("/"):
        os.makedirs(output_path, exist_ok=True)
        output_path = os.path.join(output_path, "lb_analysis_results.json")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"Liquid biopsy analysis complete. Results: {output_path}")
    print(f"  CHIP variants filtered: {len(results['chip_filtered_variants'])}")
    print(f"  ctDNA trends tracked: {len(results['ctdna_trend'])}")
    print(f"  Resistance mutations: {len(results['resistance_mutations'])}")
    print(f"  Actionable findings: {len(results['actionable_findings'])}")
    print(f"  Clinical utility: {results['clinical_utility']['utility_level']}")


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"
