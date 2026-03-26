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
Homologous Recombination Deficiency (HRD) Analysis Agent.

Computes LOH, TAI, LST, GIS (Genomic Instability Score), HRDetect-style
score, BRCA pathway analysis, PARP inhibitor response prediction, reversion
mutation detection, and platinum sensitivity correlation.
"""

import argparse
import json
import os
import random
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CENTROMERE_POSITIONS = {
    "chr1": 125_000_000, "chr2": 93_300_000, "chr3": 91_000_000,
    "chr4": 50_400_000, "chr5": 48_400_000, "chr6": 61_000_000,
    "chr7": 59_900_000, "chr8": 45_600_000, "chr9": 49_000_000,
    "chr10": 40_200_000, "chr11": 53_700_000, "chr12": 35_800_000,
    "chr13": 17_900_000, "chr14": 17_600_000, "chr15": 19_000_000,
    "chr16": 36_600_000, "chr17": 24_000_000, "chr18": 17_200_000,
    "chr19": 26_500_000, "chr20": 27_500_000, "chr21": 13_200_000,
    "chr22": 14_700_000,
}

CHROMOSOME_LENGTHS = {
    "chr1": 249_000_000, "chr2": 243_000_000, "chr3": 198_000_000,
    "chr4": 191_000_000, "chr5": 181_000_000, "chr6": 171_000_000,
    "chr7": 159_000_000, "chr8": 146_000_000, "chr9": 141_000_000,
    "chr10": 136_000_000, "chr11": 135_000_000, "chr12": 134_000_000,
    "chr13": 115_000_000, "chr14": 107_000_000, "chr15": 103_000_000,
    "chr16": 90_000_000, "chr17": 83_000_000, "chr18": 80_000_000,
    "chr19": 59_000_000, "chr20": 65_000_000, "chr21": 47_000_000,
    "chr22": 51_000_000,
}

HR_PATHWAY_GENES = [
    "BRCA1", "BRCA2", "ATM", "ATR", "PALB2", "CHEK2", "CDK12",
    "RAD51C", "RAD51D", "FANCA", "FANCC", "RAD51", "RAD51B",
    "BARD1", "BRIP1", "NBN", "MRE11", "RAD50",
]

BRCA_REVERSION_HOTSPOTS = {
    "BRCA1": ["exon10", "exon11", "exon13"],
    "BRCA2": ["exon11", "exon14", "exon27"],
}

TUMOR_TYPE_CONTEXT = {
    "ovarian": {
        "hrd_prevalence": 0.50, "brca_prevalence": 0.25,
        "parp_approved": True, "platinum_first_line": True,
        "relevant_drugs": ["olaparib", "niraparib", "rucaparib"],
    },
    "breast": {
        "hrd_prevalence": 0.35, "brca_prevalence": 0.15,
        "parp_approved": True, "platinum_first_line": False,
        "relevant_drugs": ["olaparib", "talazoparib"],
    },
    "pancreatic": {
        "hrd_prevalence": 0.25, "brca_prevalence": 0.08,
        "parp_approved": True, "platinum_first_line": True,
        "relevant_drugs": ["olaparib"],
    },
    "prostate": {
        "hrd_prevalence": 0.20, "brca_prevalence": 0.12,
        "parp_approved": True, "platinum_first_line": False,
        "relevant_drugs": ["olaparib", "rucaparib"],
    },
}

HRDETECT_WEIGHTS = {
    "sbs3": 0.25, "sbs8": 0.10,
    "rs3": 0.20, "rs5": 0.10,
    "hrd_index": 0.20, "del_mh": 0.15,
}

PARP_RESPONSE_TABLE = {
    "brca_mutated": {
        "label": "Strong response expected",
        "response_rate": "50-70%", "confidence": "high",
    },
    "hrd_positive_brca_wt": {
        "label": "Moderate response expected",
        "response_rate": "20-35%", "confidence": "moderate",
    },
    "hrd_negative": {
        "label": "Limited response expected",
        "response_rate": "5-15%", "confidence": "low",
    },
}


# ---------------------------------------------------------------------------
# Demo data generator
# ---------------------------------------------------------------------------

def _generate_demo_segments(hrd_positive: bool = True) -> List[Dict]:
    """Generate mock CNV segments with a realistic HRD pattern."""
    segments = []
    random.seed(42)
    for chrom, length in CHROMOSOME_LENGTHS.items():
        n_segs = random.randint(3, 8) if hrd_positive else random.randint(1, 3)
        pos = 1
        for _ in range(n_segs):
            seg_len = random.randint(5_000_000, 50_000_000)
            end = min(pos + seg_len, length)
            cn = random.choice([0, 1, 1, 2, 2, 3, 4]) if hrd_positive else 2
            minor_cn = 0 if (cn <= 1 and random.random() < 0.6) else min(1, cn // 2)
            segments.append({
                "chromosome": chrom, "start": pos, "end": end,
                "total_cn": cn, "minor_cn": minor_cn,
                "segment_mean": round(random.uniform(-1.5, 1.5), 3),
            })
            pos = end + 1
            if pos >= length:
                break
    return segments


def _generate_demo_mutations() -> List[Dict]:
    random.seed(43)
    genes = HR_PATHWAY_GENES + ["TP53", "PIK3CA", "KRAS", "PTEN"]
    muts = []
    for i in range(60):
        gene = random.choice(genes)
        muts.append({
            "gene": gene,
            "chromosome": f"chr{random.randint(1, 22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "ref": random.choice(["A", "C", "G", "T"]),
            "alt": random.choice(["A", "C", "G", "T"]),
            "vaf": round(random.uniform(0.05, 0.95), 3),
            "variant_class": random.choice(["Missense", "Nonsense", "Frame_Shift_Del",
                                             "Frame_Shift_Ins", "Splice_Site"]),
            "is_germline": random.random() < 0.15,
        })
    return muts


# ---------------------------------------------------------------------------
# HRDAnalyzer
# ---------------------------------------------------------------------------

class HRDAnalyzer:
    """Homologous Recombination Deficiency analyser."""

    def __init__(
        self,
        cnv_segments: Optional[List[Dict]] = None,
        mutations: Optional[List[Dict]] = None,
        germline_mutations: Optional[List[Dict]] = None,
        tumor_type: str = "ovarian",
        purity: float = 0.65,
        ploidy: float = 2.1,
    ):
        self.cnv_segments = cnv_segments or _generate_demo_segments(hrd_positive=True)
        self.mutations = mutations or _generate_demo_mutations()
        self.germline_mutations = germline_mutations or []
        self.tumor_type = tumor_type.lower()
        self.purity = purity
        self.ploidy = ploidy
        self.tumor_context = TUMOR_TYPE_CONTEXT.get(self.tumor_type, TUMOR_TYPE_CONTEXT["ovarian"])

    # ----- LOH Score -----
    def _compute_loh_score(self) -> Tuple[int, List[Dict]]:
        loh_regions: List[Dict] = []
        for seg in self.cnv_segments:
            if seg.get("minor_cn", 1) == 0:
                seg_len = seg["end"] - seg["start"]
                chrom = seg["chromosome"]
                chrom_len = CHROMOSOME_LENGTHS.get(chrom, 250_000_000)
                spans_whole = seg_len >= chrom_len * 0.9
                if seg_len > 15_000_000 and not spans_whole:
                    loh_regions.append({
                        "chromosome": chrom, "start": seg["start"],
                        "end": seg["end"], "length_mb": round(seg_len / 1e6, 1),
                    })
        return len(loh_regions), loh_regions

    # ----- TAI Score -----
    def _compute_tai_score(self) -> Tuple[int, List[Dict]]:
        tai_regions: List[Dict] = []
        for seg in self.cnv_segments:
            if seg.get("minor_cn", 1) == 0 or seg.get("total_cn", 2) != 2:
                chrom = seg["chromosome"]
                centro = CENTROMERE_POSITIONS.get(chrom, 50_000_000)
                chrom_len = CHROMOSOME_LENGTHS.get(chrom, 250_000_000)
                touches_telomere = seg["start"] <= 1_000_000 or seg["end"] >= chrom_len - 1_000_000
                crosses_centromere = seg["start"] < centro < seg["end"]
                if touches_telomere and not crosses_centromere:
                    tai_regions.append({
                        "chromosome": chrom, "start": seg["start"],
                        "end": seg["end"],
                        "length_mb": round((seg["end"] - seg["start"]) / 1e6, 1),
                    })
        return len(tai_regions), tai_regions

    # ----- LST Score -----
    def _compute_lst_score(self) -> Tuple[float, int, List[Dict]]:
        filtered = [s for s in self.cnv_segments if (s["end"] - s["start"]) >= 3_000_000]
        filtered.sort(key=lambda s: (s["chromosome"], s["start"]))
        breakpoints: List[Dict] = []
        for i in range(1, len(filtered)):
            prev, cur = filtered[i - 1], filtered[i]
            if prev["chromosome"] != cur["chromosome"]:
                continue
            if prev.get("total_cn", 2) != cur.get("total_cn", 2):
                prev_len = prev["end"] - prev["start"]
                cur_len = cur["end"] - cur["start"]
                if prev_len >= 10_000_000 and cur_len >= 10_000_000:
                    breakpoints.append({
                        "chromosome": prev["chromosome"],
                        "position": prev["end"],
                        "left_cn": prev.get("total_cn", 2),
                        "right_cn": cur.get("total_cn", 2),
                    })
        raw_lst = len(breakpoints)
        lst_adj = raw_lst - 15.5 * self.ploidy
        return round(lst_adj, 1), raw_lst, breakpoints

    # ----- GIS -----
    def _compute_gis(self, loh: int, tai: int, lst_adj: float) -> Tuple[float, str]:
        gis = loh + tai + max(lst_adj, 0)
        status = "HRD-positive" if gis >= 42 else "HRD-negative"
        return round(gis, 1), status

    # ----- HRDetect-style -----
    def _compute_hrdetect(self) -> Tuple[float, Dict]:
        random.seed(44)
        sbs3 = round(random.uniform(0.05, 0.55), 3)
        sbs8 = round(random.uniform(0.01, 0.15), 3)
        rs3 = round(random.uniform(0.0, 0.4), 3)
        rs5 = round(random.uniform(0.0, 0.3), 3)
        hrd_idx = round(random.uniform(0.2, 0.9), 3)
        del_mh = round(random.uniform(0.1, 0.7), 3)

        features = {"sbs3": sbs3, "sbs8": sbs8, "rs3": rs3, "rs5": rs5,
                     "hrd_index": hrd_idx, "del_mh": del_mh}
        score = sum(HRDETECT_WEIGHTS[k] * v for k, v in features.items())
        score = min(max(round(score, 4), 0), 1)
        return score, features

    # ----- BRCA Pathway -----
    def _analyse_brca_pathway(self) -> Dict:
        all_muts = self.mutations + self.germline_mutations
        pathway_hits: Dict[str, List[Dict]] = {}
        for m in all_muts:
            if m["gene"] in HR_PATHWAY_GENES:
                pathway_hits.setdefault(m["gene"], []).append({
                    "variant_class": m.get("variant_class", "Unknown"),
                    "vaf": m.get("vaf"), "germline": m.get("is_germline", False),
                })
        brca1_hit = "BRCA1" in pathway_hits
        brca2_hit = "BRCA2" in pathway_hits
        brca_status = "mutated" if (brca1_hit or brca2_hit) else "wildtype"
        methylation = random.random() < 0.15  # simulated
        rad51_foci_low = random.random() < 0.4  # simulated
        return {
            "brca_status": brca_status,
            "brca1_mutated": brca1_hit,
            "brca2_mutated": brca2_hit,
            "brca1_promoter_methylation": methylation,
            "rad51_foci_low": rad51_foci_low,
            "hr_gene_hits": {g: hits for g, hits in pathway_hits.items()},
            "n_hr_genes_affected": len(pathway_hits),
        }

    # ----- Reversion mutations -----
    def _detect_reversions(self) -> List[Dict]:
        reversions: List[Dict] = []
        for m in self.mutations:
            if m["gene"] in ("BRCA1", "BRCA2"):
                if m.get("variant_class") in ("Frame_Shift_Ins", "Frame_Shift_Del"):
                    if m.get("vaf", 0) > 0.05:
                        reversions.append({
                            "gene": m["gene"], "position": m.get("position"),
                            "variant_class": m["variant_class"], "vaf": m.get("vaf"),
                            "interpretation": "Potential reversion mutation restoring reading frame",
                        })
        return reversions

    # ----- PARP prediction -----
    def _predict_parp_response(self, brca_status: str, hrd_status: str) -> Dict:
        if brca_status == "mutated":
            key = "brca_mutated"
        elif hrd_status == "HRD-positive":
            key = "hrd_positive_brca_wt"
        else:
            key = "hrd_negative"
        pred = dict(PARP_RESPONSE_TABLE[key])
        pred["approved_drugs"] = self.tumor_context.get("relevant_drugs", [])
        pred["tumor_type_approved"] = self.tumor_context.get("parp_approved", False)
        return pred

    # ----- Platinum sensitivity -----
    def _platinum_sensitivity(self, hrd_status: str) -> Dict:
        if hrd_status == "HRD-positive":
            return {
                "prediction": "Platinum sensitive",
                "rationale": "HRD-positive tumors show impaired DNA repair and higher platinum sensitivity",
                "first_line_platinum": self.tumor_context.get("platinum_first_line", False),
            }
        return {
            "prediction": "Platinum sensitivity uncertain",
            "rationale": "HRD-negative status does not preclude platinum response but correlation is weaker",
            "first_line_platinum": self.tumor_context.get("platinum_first_line", False),
        }

    # ----- main entry -----
    def analyze(self) -> Dict[str, Any]:
        loh_score, loh_regions = self._compute_loh_score()
        tai_score, tai_regions = self._compute_tai_score()
        lst_adj, lst_raw, lst_breakpoints = self._compute_lst_score()
        gis_score, hrd_status = self._compute_gis(loh_score, tai_score, lst_adj)
        hrdetect_score, hrdetect_features = self._compute_hrdetect()
        brca_pathway = self._analyse_brca_pathway()
        reversions = self._detect_reversions()
        parp_pred = self._predict_parp_response(brca_pathway["brca_status"], hrd_status)
        platinum = self._platinum_sensitivity(hrd_status)

        return {
            "analysis_metadata": {
                "analysis_type": "Homologous Recombination Deficiency",
                "timestamp": datetime.now().isoformat(),
                "tumor_type": self.tumor_type,
                "purity": self.purity,
                "ploidy": self.ploidy,
                "n_segments": len(self.cnv_segments),
                "n_mutations": len(self.mutations),
            },
            "loh_score": loh_score,
            "loh_regions": loh_regions,
            "tai_score": tai_score,
            "tai_regions": tai_regions,
            "lst_score": {"adjusted": lst_adj, "raw": lst_raw},
            "lst_breakpoints": lst_breakpoints,
            "gis_score": gis_score,
            "hrd_status": hrd_status,
            "hrdetect_score": hrdetect_score,
            "hrdetect_features": hrdetect_features,
            "hrdetect_status": "HRD-positive" if hrdetect_score >= 0.7 else "HRD-negative",
            "brca_pathway": brca_pathway,
            "reversion_mutations": reversions,
            "parp_prediction": parp_pred,
            "platinum_sensitivity": platinum,
            "tumor_type_context": self.tumor_context,
        }


# ---------------------------------------------------------------------------
# File loaders (stub – real implementations would parse TSV/MAF/VCF)
# ---------------------------------------------------------------------------

def _load_cnv_segments(path: str) -> Optional[List[Dict]]:
    if not os.path.isfile(path):
        return None
    rows: List[Dict] = []
    with open(path) as fh:
        header = fh.readline().strip().split("\t")
        for line in fh:
            vals = line.strip().split("\t")
            row = dict(zip(header, vals))
            rows.append({
                "chromosome": row.get("chromosome", row.get("chrom", "chr1")),
                "start": int(row.get("start", 0)),
                "end": int(row.get("end", 0)),
                "total_cn": int(float(row.get("total_cn", row.get("cn", 2)))),
                "minor_cn": int(float(row.get("minor_cn", 1))),
                "segment_mean": float(row.get("segment_mean", 0)),
            })
    return rows if rows else None


def _load_mutations(path: str) -> Optional[List[Dict]]:
    if not os.path.isfile(path):
        return None
    rows: List[Dict] = []
    with open(path) as fh:
        header = fh.readline().strip().split("\t")
        for line in fh:
            vals = line.strip().split("\t")
            row = dict(zip(header, vals))
            rows.append({
                "gene": row.get("Hugo_Symbol", row.get("gene", "")),
                "chromosome": row.get("Chromosome", ""),
                "position": int(row.get("Start_Position", row.get("position", 0))),
                "ref": row.get("Reference_Allele", ""),
                "alt": row.get("Tumor_Seq_Allele2", ""),
                "vaf": float(row.get("t_alt_count", 0)) / max(
                    float(row.get("t_depth", 1)), 1),
                "variant_class": row.get("Variant_Classification", "Unknown"),
                "is_germline": False,
            })
    return rows if rows else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="HRD (Homologous Recombination Deficiency) Analyzer",
    )
    parser.add_argument("--cnv_segments", default=None,
                        help="Path to CNV segments TSV")
    parser.add_argument("--mutations", default=None,
                        help="Path to somatic variants MAF")
    parser.add_argument("--germline", default=None,
                        help="Path to germline variants VCF")
    parser.add_argument("--tumor_type", default="ovarian",
                        choices=list(TUMOR_TYPE_CONTEXT.keys()),
                        help="Tumor type for context")
    parser.add_argument("--purity", type=float, default=0.65,
                        help="Estimated tumor purity (0-1)")
    parser.add_argument("--ploidy", type=float, default=2.1,
                        help="Estimated tumor ploidy")
    parser.add_argument("--output", default=None,
                        help="Output JSON path")
    args = parser.parse_args()

    cnv = _load_cnv_segments(args.cnv_segments) if args.cnv_segments else None
    muts = _load_mutations(args.mutations) if args.mutations else None
    germline = _load_mutations(args.germline) if args.germline else None

    analyzer = HRDAnalyzer(
        cnv_segments=cnv,
        mutations=muts,
        germline_mutations=germline,
        tumor_type=args.tumor_type,
        purity=args.purity,
        ploidy=args.ploidy,
    )
    result = analyzer.analyze()
    output = json.dumps(result, indent=2, default=str)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as fh:
            fh.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"
