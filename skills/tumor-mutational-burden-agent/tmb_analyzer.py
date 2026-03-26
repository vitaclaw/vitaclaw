#!/usr/bin/env python3
"""Tumor Mutational Burden (TMB) Analyzer.

Calculates TMB from mutation data (MAF/VCF), applies panel-specific
normalization, harmonization across panels, and integrates PD-L1/MSI
biomarkers for immunotherapy response prediction.
"""
# COPYRIGHT NOTICE
# This file is part of the "Universal Biomedical Skills" project.
# Copyright (c) 2026 MD BABU MIA, PhD <md.babu.mia@mssm.edu>
# All Rights Reserved.
#
# This code is proprietary and confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Provenance: Authenticated by MD BABU MIA

import argparse
import json
import os
import random
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Add shared utilities to path
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "../.."))
sys.path.insert(0, _PROJECT_ROOT)

from skills._shared.biomedical_utils import build_result, write_output

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Panel sizes in megabases (Mb)
PANEL_SIZES: dict[str, float] = {
    "foundation_one": 0.8,
    "msk_impact": 1.14,
    "tso500": 1.94,
    "tempus_xt": 3.15,
    "wes": 30.0,
    "wgs": 3000.0,
}

# TMB classification thresholds (mutations / Mb)
TMB_THRESHOLDS: dict[str, float] = {
    "fda": 10.0,
    "conservative": 16.0,
    "strict": 20.0,
}

# Tumor-type specific TMB-High thresholds (mutations / Mb)
TUMOR_TYPE_THRESHOLDS: dict[str, float] = {
    "melanoma": 13.8,
    "nsclc": 10.0,
    "colorectal": 40.0,
    "bladder": 15.0,
    "head_and_neck": 10.0,
    "cervical": 10.0,
    "endometrial": 15.0,
    "gastric": 12.0,
    "renal": 8.0,
    "breast": 10.0,
    "pancreatic": 6.0,
    "glioblastoma": 12.0,
    "unknown": 10.0,
}

# Harmonization correction factors: from_panel -> to_panel -> factor
# TMB_harmonized = TMB_raw * factor
HARMONIZATION_FACTORS: dict[str, dict[str, float]] = {
    "foundation_one": {
        "wes": 1.10,
        "msk_impact": 0.96,
        "tso500": 1.02,
        "tempus_xt": 1.05,
    },
    "msk_impact": {
        "wes": 1.15,
        "foundation_one": 1.04,
        "tso500": 1.06,
        "tempus_xt": 1.09,
    },
    "tso500": {
        "wes": 1.05,
        "foundation_one": 0.98,
        "msk_impact": 0.94,
        "tempus_xt": 1.03,
    },
    "tempus_xt": {
        "wes": 1.02,
        "foundation_one": 0.95,
        "msk_impact": 0.92,
        "tso500": 0.97,
    },
    "wes": {
        "foundation_one": 0.91,
        "msk_impact": 0.87,
        "tso500": 0.95,
        "tempus_xt": 0.98,
    },
}

# Variant classifications considered coding & nonsynonymous
NONSYNONYMOUS_CLASSES = {
    "Missense_Mutation",
    "Nonsense_Mutation",
    "Frame_Shift_Del",
    "Frame_Shift_Ins",
    "In_Frame_Del",
    "In_Frame_Ins",
    "Splice_Site",
    "Nonstop_Mutation",
    "Translation_Start_Site",
}


# ---------------------------------------------------------------------------
# Demo data generation
# ---------------------------------------------------------------------------

def _generate_demo_mutations(n: int = 150) -> list[dict]:
    """Generate *n* synthetic mutations for demo / testing."""
    genes = [
        "TP53", "KRAS", "BRAF", "PIK3CA", "EGFR", "PTEN", "APC", "ATM",
        "BRCA1", "BRCA2", "CDKN2A", "RB1", "SMAD4", "STK11", "NF1", "ARID1A",
        "KMT2D", "NOTCH1", "FAT1", "TERT", "IDH1", "FGFR3", "ERBB2", "MET",
    ]
    chroms = [f"chr{i}" for i in range(1, 23)] + ["chrX"]
    classifications = list(NONSYNONYMOUS_CLASSES) + ["Silent", "Intron", "3'UTR", "5'UTR"]
    mutations = []
    for _ in range(n):
        vaf = round(random.uniform(0.01, 0.85), 4)
        depth = random.randint(20, 800)
        gnomad_af = round(random.uniform(0.0, 0.05), 5)
        mutations.append({
            "Hugo_Symbol": random.choice(genes),
            "Chromosome": random.choice(chroms),
            "Start_Position": random.randint(1_000_000, 200_000_000),
            "Variant_Classification": random.choice(classifications),
            "Variant_Type": random.choice(["SNP", "DEL", "INS"]),
            "t_alt_count": int(depth * vaf),
            "t_ref_count": int(depth * (1 - vaf)),
            "t_depth": depth,
            "VAF": vaf,
            "gnomAD_AF": gnomad_af,
        })
    return mutations


# ---------------------------------------------------------------------------
# TMBAnalyzer
# ---------------------------------------------------------------------------

class TMBAnalyzer:
    """Analyse tumour mutational burden from MAF / VCF mutation data."""

    def __init__(
        self,
        mutations: list[dict],
        panel: str = "foundation_one",
        tumor_type: str = "unknown",
        pdl1_tps: float | None = None,
        msi_status: str | None = None,
        harmonize_to: str | None = None,
    ):
        self.raw_mutations = mutations
        self.panel = panel.lower().replace("-", "_")
        self.tumor_type = tumor_type.lower().replace("-", "_").replace(" ", "_")
        self.pdl1_tps = pdl1_tps
        self.msi_status = msi_status.upper() if msi_status else None
        self.harmonize_to = harmonize_to.lower().replace("-", "_") if harmonize_to else None

        if self.panel not in PANEL_SIZES:
            raise ValueError(f"Unknown panel '{self.panel}'. Choose from {list(PANEL_SIZES)}")
        self.panel_size = PANEL_SIZES[self.panel]

    # ----- filtering -----

    def _filter_mutations(self) -> list[dict]:
        """Apply quality and functional filters to mutations."""
        passed = []
        for m in self.raw_mutations:
            # Must be coding nonsynonymous
            if m.get("Variant_Classification") not in NONSYNONYMOUS_CLASSES:
                continue
            # VAF >= 5 %
            vaf = float(m.get("VAF", 0))
            if vaf < 0.05:
                continue
            # Depth >= 100
            depth = int(m.get("t_depth", 0))
            if depth < 100:
                continue
            # gnomAD AF <= 1 % (filter common germline)
            gnomad = float(m.get("gnomAD_AF", 0))
            if gnomad > 0.01:
                continue
            passed.append(m)
        return passed

    # ----- classification -----

    def _classify_tmb(self, tmb_value: float) -> dict:
        """Classify TMB against multiple threshold schemes."""
        classification = {}
        for scheme, threshold in TMB_THRESHOLDS.items():
            classification[scheme] = "TMB-High" if tmb_value >= threshold else "TMB-Low"

        # Tumor-type specific
        tt_threshold = TUMOR_TYPE_THRESHOLDS.get(self.tumor_type, TMB_THRESHOLDS["fda"])
        classification["tumor_type_specific"] = "TMB-High" if tmb_value >= tt_threshold else "TMB-Low"
        classification["tumor_type_threshold"] = tt_threshold
        return classification

    # ----- harmonization -----

    def _harmonize(self, tmb_value: float) -> dict | None:
        """Harmonize TMB to a different panel if requested."""
        if not self.harmonize_to or self.harmonize_to == self.panel:
            return None
        factors = HARMONIZATION_FACTORS.get(self.panel, {})
        factor = factors.get(self.harmonize_to)
        if factor is None:
            return {"error": f"No harmonization factor from {self.panel} to {self.harmonize_to}"}
        harmonized = round(tmb_value * factor, 2)
        return {
            "from_panel": self.panel,
            "to_panel": self.harmonize_to,
            "correction_factor": factor,
            "harmonized_tmb": harmonized,
            "harmonized_classification": self._classify_tmb(harmonized),
        }

    # ----- biomarker integration -----

    def _predict_immunotherapy(self, tmb_value: float, classification: dict) -> dict:
        """Predict immunotherapy response integrating TMB, PD-L1, and MSI."""
        scores: list[str] = []
        evidence: list[str] = []
        positive_signals = 0

        # TMB
        if classification.get("fda") == "TMB-High":
            positive_signals += 1
            scores.append("TMB-High (FDA >=10)")
            evidence.append("Pembrolizumab FDA-approved for TMB-H (>=10 mut/Mb) solid tumors")

        # PD-L1
        if self.pdl1_tps is not None:
            if self.pdl1_tps >= 50:
                positive_signals += 1
                scores.append(f"PD-L1 TPS {self.pdl1_tps}% (high)")
                evidence.append("PD-L1 TPS >=50% associated with improved ICI response")
            elif self.pdl1_tps >= 1:
                positive_signals += 0.5
                scores.append(f"PD-L1 TPS {self.pdl1_tps}% (low positive)")
            else:
                scores.append(f"PD-L1 TPS {self.pdl1_tps}% (negative)")

        # MSI
        if self.msi_status:
            if self.msi_status in ("MSI-H", "MSI_H", "HIGH"):
                positive_signals += 1
                scores.append("MSI-High")
                evidence.append("MSI-H/dMMR tumors respond to checkpoint inhibitors (KEYNOTE-158)")
            elif self.msi_status in ("MSS", "MSI-L", "MSI_L", "LOW", "STABLE"):
                scores.append("MSS / MSI-Low")

        # Overall prediction
        if positive_signals >= 2:
            prediction = "likely_responder"
            confidence = "high"
        elif positive_signals >= 1:
            prediction = "possible_responder"
            confidence = "moderate"
        else:
            prediction = "unlikely_responder"
            confidence = "low"

        return {
            "prediction": prediction,
            "confidence": confidence,
            "positive_signals": positive_signals,
            "biomarker_details": scores,
            "supporting_evidence": evidence,
        }

    # ----- main analysis -----

    def analyze(self) -> dict:
        """Run the full TMB analysis pipeline and return structured results."""
        filtered = self._filter_mutations()
        mutations_counted = len(filtered)
        tmb_value = round(mutations_counted / self.panel_size, 2)

        classification = self._classify_tmb(tmb_value)
        harmonized = self._harmonize(tmb_value)
        immunotherapy = self._predict_immunotherapy(tmb_value, classification)

        # Build gene-level summary of counted mutations
        gene_counts: dict[str, int] = {}
        for m in filtered:
            g = m.get("Hugo_Symbol", "UNKNOWN")
            gene_counts[g] = gene_counts.get(g, 0) + 1
        top_genes = sorted(gene_counts.items(), key=lambda x: x[1], reverse=True)[:15]

        result = {
            "tmb_value": tmb_value,
            "tmb_unit": "mutations/Mb",
            "tmb_classification": classification,
            "mutations_counted": mutations_counted,
            "total_mutations_input": len(self.raw_mutations),
            "panel_used": self.panel,
            "panel_size_mb": self.panel_size,
            "tumor_type": self.tumor_type,
            "top_mutated_genes": dict(top_genes),
        }

        if harmonized:
            result["harmonized_tmb"] = harmonized

        result["immunotherapy_prediction"] = immunotherapy

        biomarker_integration = {}
        if self.pdl1_tps is not None:
            biomarker_integration["pdl1_tps"] = self.pdl1_tps
        if self.msi_status:
            biomarker_integration["msi_status"] = self.msi_status
        if biomarker_integration:
            result["biomarker_integration"] = biomarker_integration

        # Evidence list
        evidence = [
            "Friends of Cancer Research TMB Harmonization Project (Nat Med 2019)",
            "Marabelle et al. KEYNOTE-158 (Ann Oncol 2020)",
            "Samstein et al. Nat Genet 2019 – pan-cancer TMB & survival",
        ]
        if self.tumor_type in TUMOR_TYPE_THRESHOLDS:
            evidence.append(
                f"Tumor-type threshold for {self.tumor_type}: "
                f"{TUMOR_TYPE_THRESHOLDS[self.tumor_type]} mut/Mb"
            )

        # Markdown summary
        md_lines = [
            f"## TMB Analysis Report",
            f"- **TMB**: {tmb_value} mutations/Mb",
            f"- **Panel**: {self.panel} ({self.panel_size} Mb)",
            f"- **Mutations counted**: {mutations_counted} / {len(self.raw_mutations)} total",
            f"- **FDA classification**: {classification.get('fda', 'N/A')}",
            f"- **Tumor type**: {self.tumor_type} (threshold {classification.get('tumor_type_threshold', 'N/A')})",
        ]
        if harmonized and "harmonized_tmb" in harmonized:
            md_lines.append(
                f"- **Harmonized TMB** ({harmonized['to_panel']}): "
                f"{harmonized['harmonized_tmb']} mut/Mb"
            )
        md_lines.append(
            f"- **Immunotherapy prediction**: {immunotherapy['prediction']} "
            f"(confidence: {immunotherapy['confidence']})"
        )

        return build_result(
            status="success",
            result=result,
            evidence=evidence,
            metadata={"panel": self.panel, "tumor_type": self.tumor_type},
            markdown="\n".join(md_lines),
        )


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_maf(filepath: str) -> list[dict]:
    """Load mutations from a MAF file (tab-separated with header)."""
    import csv
    mutations = []
    with open(filepath, "r") as fh:
        # Skip comment lines
        lines = (line for line in fh if not line.startswith("#"))
        reader = csv.DictReader(lines, delimiter="\t")
        for row in reader:
            # Compute VAF if not present
            if "VAF" not in row or not row["VAF"]:
                try:
                    alt = int(row.get("t_alt_count", 0))
                    depth = int(row.get("t_depth", alt + int(row.get("t_ref_count", 0))))
                    row["VAF"] = alt / depth if depth else 0
                    row["t_depth"] = depth
                except (ValueError, ZeroDivisionError):
                    row["VAF"] = 0
                    row["t_depth"] = 0
            mutations.append(dict(row))
    return mutations


def _load_vcf(filepath: str) -> list[dict]:
    """Minimal VCF loader – extracts key fields into MAF-like dicts."""
    mutations = []
    with open(filepath, "r") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 8:
                continue
            chrom, pos, _, ref, alt, qual, filt, info = parts[:8]
            info_dict = {}
            for entry in info.split(";"):
                if "=" in entry:
                    k, v = entry.split("=", 1)
                    info_dict[k] = v
            mutations.append({
                "Chromosome": chrom,
                "Start_Position": int(pos),
                "Reference_Allele": ref,
                "Tumor_Seq_Allele2": alt,
                "Hugo_Symbol": info_dict.get("GENE", "UNKNOWN"),
                "Variant_Classification": info_dict.get("VC", "Missense_Mutation"),
                "VAF": float(info_dict.get("VAF", 0)),
                "t_depth": int(info_dict.get("DP", 0)),
                "gnomAD_AF": float(info_dict.get("gnomAD_AF", 0)),
            })
    return mutations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Tumor Mutational Burden Analyzer")
    parser.add_argument("--mutations", required=True, help="Path to MAF or VCF mutation file")
    parser.add_argument("--panel", default="foundation_one", choices=list(PANEL_SIZES), help="Sequencing panel used")
    parser.add_argument("--tumor_type", default="unknown", help="Tumor type (e.g. nsclc, melanoma)")
    parser.add_argument("--pdl1_tps", type=float, default=None, help="PD-L1 TPS percentage (0-100)")
    parser.add_argument("--msi_status", default=None, help="MSI status (MSI-H, MSS, MSI-L)")
    parser.add_argument("--harmonize_to", default=None, choices=list(PANEL_SIZES), help="Harmonize TMB to this panel")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    # Load or generate mutations
    if os.path.isfile(args.mutations):
        ext = os.path.splitext(args.mutations)[1].lower()
        if ext in (".vcf", ".gz"):
            mutations = _load_vcf(args.mutations)
        else:
            mutations = _load_maf(args.mutations)
    else:
        print(f"[DEMO MODE] File '{args.mutations}' not found – generating 150 synthetic mutations.", file=sys.stderr)
        mutations = _generate_demo_mutations(150)

    analyzer = TMBAnalyzer(
        mutations=mutations,
        panel=args.panel,
        tumor_type=args.tumor_type,
        pdl1_tps=args.pdl1_tps,
        msi_status=args.msi_status,
        harmonize_to=args.harmonize_to,
    )
    result = analyzer.analyze()
    write_output(result, args.output)


if __name__ == "__main__":
    main()


__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"
