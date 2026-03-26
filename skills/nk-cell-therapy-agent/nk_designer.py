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
NK Cell Therapy Design.

Designs CAR-NK constructs, compares NK cell sources, analyzes KIR/HLA matching,
recommends persistence strategies, provides CIML NK protocols, and incorporates
safety features for NK cell-based immunotherapy.
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

# CAR targeting domains
CAR_TARGETS = {
    "CD19": {
        "tumor_types": ["B-ALL", "B-NHL", "CLL", "b_cell_lymphoma"],
        "expression": "B-cell lineage marker",
        "recommended_hinge": "CD8a",
        "recommended_tm": "CD8a",
        "recommended_costim": ["2B4", "CD3z"],
        "clinical_stage": "Phase I/II",
    },
    "CD20": {
        "tumor_types": ["B-NHL", "CLL", "b_cell_lymphoma"],
        "expression": "Mature B-cell marker",
        "recommended_hinge": "IgG1",
        "recommended_tm": "CD28",
        "recommended_costim": ["4-1BB", "CD3z"],
        "clinical_stage": "Phase I",
    },
    "CD22": {
        "tumor_types": ["B-ALL", "B-NHL"],
        "expression": "B-cell restricted",
        "recommended_hinge": "CD8a",
        "recommended_tm": "CD8a",
        "recommended_costim": ["2B4", "CD3z"],
        "clinical_stage": "Phase I",
    },
    "BCMA": {
        "tumor_types": ["multiple_myeloma"],
        "expression": "Plasma cell marker",
        "recommended_hinge": "IgG4",
        "recommended_tm": "CD8a",
        "recommended_costim": ["2B4", "DAP10", "CD3z"],
        "clinical_stage": "Phase I/II",
    },
    "HER2": {
        "tumor_types": ["breast", "gastric", "ovarian"],
        "expression": "Epithelial tumors",
        "recommended_hinge": "IgG1",
        "recommended_tm": "CD28",
        "recommended_costim": ["DAP10", "CD3z"],
        "clinical_stage": "Phase I",
    },
    "GD2": {
        "tumor_types": ["neuroblastoma", "melanoma", "sarcoma"],
        "expression": "Neuroectodermal tumors",
        "recommended_hinge": "CD8a",
        "recommended_tm": "NKG2D",
        "recommended_costim": ["2B4", "DAP12", "CD3z"],
        "clinical_stage": "Phase I",
    },
    "NKG2D-ligands": {
        "tumor_types": ["various_solid", "AML", "multiple_myeloma"],
        "expression": "Stress-induced ligands (MICA/B, ULBPs)",
        "recommended_hinge": "CD8a",
        "recommended_tm": "NKG2D",
        "recommended_costim": ["DAP10", "CD3z"],
        "clinical_stage": "Phase I/II",
    },
    "CD33": {
        "tumor_types": ["AML"],
        "expression": "Myeloid lineage marker",
        "recommended_hinge": "CD8a",
        "recommended_tm": "CD8a",
        "recommended_costim": ["2B4", "CD3z"],
        "clinical_stage": "Phase I",
    },
    "CD123": {
        "tumor_types": ["AML", "BPDCN"],
        "expression": "IL-3 receptor alpha",
        "recommended_hinge": "IgG4",
        "recommended_tm": "CD28",
        "recommended_costim": ["4-1BB", "CD3z"],
        "clinical_stage": "Phase I",
    },
    "EGFR": {
        "tumor_types": ["glioblastoma", "NSCLC", "colorectal"],
        "expression": "Epithelial tumors",
        "recommended_hinge": "IgG1",
        "recommended_tm": "CD28",
        "recommended_costim": ["DAP10", "CD3z"],
        "clinical_stage": "Preclinical/Phase I",
    },
    "Mesothelin": {
        "tumor_types": ["mesothelioma", "pancreatic", "ovarian"],
        "expression": "Mesothelial tumors",
        "recommended_hinge": "IgG4",
        "recommended_tm": "CD8a",
        "recommended_costim": ["2B4", "DAP10", "CD3z"],
        "clinical_stage": "Phase I",
    },
    "CD70": {
        "tumor_types": ["RCC", "AML", "glioblastoma"],
        "expression": "Activated immune and tumor cells",
        "recommended_hinge": "CD8a",
        "recommended_tm": "CD8a",
        "recommended_costim": ["2B4", "CD3z"],
        "clinical_stage": "Phase I",
    },
}

# CAR component options
HINGE_OPTIONS = {
    "CD8a": {"length": "short", "flexibility": "moderate", "note": "Most commonly used for NK CARs"},
    "IgG1": {"length": "long", "flexibility": "high", "note": "Better for membrane-proximal epitopes"},
    "IgG4": {"length": "long", "flexibility": "high", "note": "Reduced Fc-mediated effects vs IgG1"},
}

TM_OPTIONS = {
    "CD8a": {"source": "T/NK cell", "note": "Standard; stable expression"},
    "NKG2D": {"source": "NK cell", "note": "NK-optimized; enhances NK signaling"},
    "CD28": {"source": "T/NK cell", "note": "Provides additional signaling"},
}

COSTIM_OPTIONS = {
    "2B4": {"alias": "CD244", "source": "NK cell", "function": "NK-specific costimulation via SAP/Fyn"},
    "DAP10": {"alias": "HCST", "source": "NK cell", "function": "NKG2D-associated signaling; PI3K activation"},
    "DAP12": {"alias": "TYROBP", "source": "NK cell", "function": "ITAM-based activation; strong cytotoxicity"},
    "CD28": {"alias": "CD28", "source": "T cell", "function": "PI3K/Akt costimulation"},
    "4-1BB": {"alias": "CD137", "source": "T/NK cell", "function": "TRAF-mediated survival; persistence"},
    "OX40": {"alias": "CD134", "source": "T cell", "function": "NF-kB activation; survival"},
    "CD3z": {"alias": "CD247", "source": "T/NK cell", "function": "Primary activation signal (ITAM)"},
}

# NK cell sources
NK_SOURCES = {
    "PB-NK": {
        "full_name": "Peripheral blood NK cells",
        "autologous": True, "allogeneic": True,
        "expansion": "limited (10-50 fold)",
        "maturity": "mature",
        "persistence": "weeks",
        "scalability": "low",
        "safety": "high (autologous) / moderate (allogeneic)",
        "clinical_validation": "extensive",
        "gvhd_risk": "low",
        "advantages": ["Mature phenotype", "Immediate effector function", "Clinical experience"],
        "disadvantages": ["Donor variability", "Limited expansion", "Difficult to gene-modify"],
    },
    "UCB-NK": {
        "full_name": "Umbilical cord blood NK cells",
        "autologous": False, "allogeneic": True,
        "expansion": "good (100-1000 fold)",
        "maturity": "immature to mature",
        "persistence": "weeks to months",
        "scalability": "moderate",
        "safety": "high",
        "clinical_validation": "validated (MD Anderson CAR-NK trials)",
        "gvhd_risk": "very low",
        "advantages": ["Good expansion", "Low GvHD risk", "Clinically validated CAR-NK"],
        "disadvantages": ["Donor-dependent", "Variable potency", "Limited starting material"],
    },
    "iPSC-NK": {
        "full_name": "Induced pluripotent stem cell-derived NK cells",
        "autologous": False, "allogeneic": True,
        "expansion": "unlimited",
        "maturity": "programmed",
        "persistence": "engineered",
        "scalability": "high",
        "safety": "under evaluation",
        "clinical_validation": "early clinical (Fate Therapeutics FT596 etc.)",
        "gvhd_risk": "very low",
        "advantages": ["Unlimited source", "Standardized product", "Multi-engineering possible"],
        "disadvantages": ["Long production time", "Incomplete maturation", "Regulatory complexity"],
    },
    "NK-92": {
        "full_name": "NK-92 cell line",
        "autologous": False, "allogeneic": True,
        "expansion": "easy (unlimited)",
        "maturity": "activated",
        "persistence": "none (irradiated)",
        "scalability": "high",
        "safety": "requires irradiation before infusion",
        "clinical_validation": "limited clinical data",
        "gvhd_risk": "none (irradiated)",
        "advantages": ["Easy expansion", "Consistent product", "Easy to transduce"],
        "disadvantages": ["Requires irradiation", "No persistence", "No ADCC (CD16-)"],
    },
}

# KIR/HLA interactions
KIR_HLA_INTERACTIONS = {
    "KIR2DL1": {"hla_ligand": "HLA-C2 (Lys80)", "type": "inhibitory"},
    "KIR2DL2": {"hla_ligand": "HLA-C1 (Asn80)", "type": "inhibitory"},
    "KIR2DL3": {"hla_ligand": "HLA-C1 (Asn80)", "type": "inhibitory"},
    "KIR3DL1": {"hla_ligand": "HLA-Bw4", "type": "inhibitory"},
    "KIR3DL2": {"hla_ligand": "HLA-A3/A11", "type": "inhibitory"},
    "KIR2DS1": {"hla_ligand": "HLA-C2", "type": "activating"},
    "KIR2DS2": {"hla_ligand": "HLA-C1", "type": "activating"},
    "KIR3DS1": {"hla_ligand": "HLA-Bw4", "type": "activating"},
}

# Persistence strategies
PERSISTENCE_STRATEGIES = {
    "il15_secretion": {
        "name": "IL-15 autocrine secretion",
        "description": "Membrane-bound or secreted IL-15/IL-15Ra fusion",
        "mechanism": "Sustained IL-15 signaling for NK survival and proliferation",
        "clinical_data": "Validated in MD Anderson CAR-NK trials (Rezvani et al.)",
        "safety": "Monitor for uncontrolled proliferation",
    },
    "il21_priming": {
        "name": "IL-21 priming (CIML)",
        "description": "Pre-activation with IL-12/15/18 to induce memory-like phenotype",
        "mechanism": "Epigenetic reprogramming for enhanced recall response",
        "clinical_data": "CIML NK trials at Washington University",
        "safety": "Good safety profile",
    },
    "tgfb_dnr": {
        "name": "TGF-beta dominant negative receptor",
        "description": "Expression of truncated TGF-beta receptor to block suppression",
        "mechanism": "Resistance to TME immunosuppression",
        "clinical_data": "Preclinical; some clinical trials",
        "safety": "Under evaluation",
    },
    "nkg2d_overexpression": {
        "name": "NKG2D overexpression",
        "description": "Forced expression of NKG2D for enhanced tumor recognition",
        "mechanism": "Increased recognition of stress-ligand expressing tumors",
        "clinical_data": "Preclinical",
        "safety": "Monitor for on-target off-tumor effects",
    },
    "cish_knockout": {
        "name": "CISH knockout",
        "description": "Deletion of CIS (CISH) — negative regulator of IL-15 signaling",
        "mechanism": "Enhanced IL-15 responsiveness and metabolic fitness",
        "clinical_data": "Fate Therapeutics iPSC-NK trials",
        "safety": "Good (redundant regulation)",
    },
    "nkg2a_knockout": {
        "name": "NKG2A knockout",
        "description": "Deletion of inhibitory receptor NKG2A (CD94/NKG2A)",
        "mechanism": "Prevent HLA-E mediated inhibition in TME",
        "clinical_data": "Early clinical",
        "safety": "Under evaluation",
    },
}

# Suicide switch options
SUICIDE_SWITCHES = {
    "iCasp9": {
        "activator": "AP1903 (rimiducid)",
        "mechanism": "Dimerizable caspase-9 → apoptosis",
        "speed": "Minutes to hours",
        "efficacy": ">90% elimination",
    },
    "CD20_rituximab": {
        "activator": "Rituximab",
        "mechanism": "Truncated CD20 surface expression → ADCC/CDC by rituximab",
        "speed": "Hours to days",
        "efficacy": "Variable",
    },
    "tEGFR_cetuximab": {
        "activator": "Cetuximab",
        "mechanism": "Truncated EGFR surface expression → ADCC by cetuximab",
        "speed": "Hours to days",
        "efficacy": "Variable; also serves as selection marker",
    },
}


class NKDesigner:
    """NK cell therapy CAR construct designer."""

    def __init__(self, target="CD19", tumor_type="b_cell_lymphoma",
                 nk_source="ucb", persistence_strategy="il15_secretion",
                 costimulatory="2B4_DAP10", donors_path=None):
        self.target = target.upper()
        self.tumor_type = tumor_type.lower()
        self.nk_source = nk_source.upper().replace("-", "_").replace(" ", "_")
        self.persistence_strategy = persistence_strategy.lower()
        self.costimulatory_input = costimulatory
        self.donors_path = donors_path
        self.donor_data = {}

    def _load_donor_data(self):
        """Load donor HLA/KIR data or generate demo."""
        if self.donors_path and os.path.isfile(self.donors_path):
            with open(self.donors_path, "r") as fh:
                return json.load(fh)
        return {
            "donor_1": {
                "id": "D001",
                "kir_genes": ["KIR2DL1", "KIR2DL2", "KIR3DL1", "KIR2DS1", "KIR2DS2"],
                "hla": {"HLA-A": ["A*02:01", "A*03:01"], "HLA-B": ["B*07:02", "B*44:02"],
                        "HLA-C": ["C*07:02", "C*05:01"]},
            },
            "patient": {
                "id": "P001",
                "hla": {"HLA-A": ["A*01:01", "A*24:02"], "HLA-B": ["B*08:01", "B*35:01"],
                        "HLA-C": ["C*04:01", "C*07:01"]},
            },
        }

    def _design_car_construct(self):
        """Design the CAR construct for the given target."""
        target_info = CAR_TARGETS.get(self.target, CAR_TARGETS.get("CD19"))

        # Parse costimulatory input
        costim_domains = [c.strip() for c in self.costimulatory_input.split("_") if c.strip()]
        costim_details = []
        for c in costim_domains:
            info = COSTIM_OPTIONS.get(c, COSTIM_OPTIONS.get("CD3z"))
            costim_details.append({
                "domain": c,
                "alias": info.get("alias", c),
                "source": info.get("source", "unknown"),
                "function": info.get("function", ""),
            })

        hinge = target_info.get("recommended_hinge", "CD8a")
        tm = target_info.get("recommended_tm", "CD8a")

        construct = {
            "target_antigen": self.target,
            "tumor_types": target_info.get("tumor_types", []),
            "scFv_or_binding": f"anti-{self.target} scFv or NKG2D ectodomain",
            "hinge_spacer": {
                "selected": hinge,
                "properties": HINGE_OPTIONS.get(hinge, {}),
            },
            "transmembrane_domain": {
                "selected": tm,
                "properties": TM_OPTIONS.get(tm, {}),
            },
            "costimulatory_domains": costim_details,
            "signaling_domain": "CD3z (ITAM-based primary activation)",
            "construct_architecture": (
                f"scFv(anti-{self.target}) → {hinge} hinge → "
                f"{tm} TM → {'→'.join(costim_domains)} → CD3z"
            ),
            "clinical_stage": target_info.get("clinical_stage", "Preclinical"),
        }
        return construct

    def _compare_nk_sources(self):
        """Compare NK cell sources and recommend."""
        source_key = self.nk_source.replace("_", "-")
        if source_key not in NK_SOURCES:
            # Try without hyphen
            for k in NK_SOURCES:
                if k.replace("-", "").lower() == source_key.replace("-", "").lower():
                    source_key = k
                    break
            else:
                source_key = "UCB-NK"

        selected = NK_SOURCES[source_key]
        comparison = {}
        for name, info in NK_SOURCES.items():
            comparison[name] = {
                "expansion": info["expansion"],
                "persistence": info["persistence"],
                "scalability": info["scalability"],
                "safety": info["safety"],
                "clinical_validation": info["clinical_validation"],
                "gvhd_risk": info["gvhd_risk"],
            }

        return {
            "selected_source": source_key,
            "selected_details": selected,
            "comparison": comparison,
            "recommendation_rationale": (
                f"{source_key} selected for {self.tumor_type}: "
                f"{', '.join(selected.get('advantages', []))}"
            ),
        }

    def _analyze_kir_hla(self, donor_data):
        """Analyze KIR/HLA matching for alloreactivity prediction."""
        donor = donor_data.get("donor_1", {})
        patient = donor_data.get("patient", {})

        donor_kir = donor.get("kir_genes", [])
        patient_hla = patient.get("hla", {})

        # Determine HLA-C group for patient
        patient_c_alleles = patient_hla.get("HLA-C", [])
        # Simplified: C*04, C*05 = C2 group; C*07 = C1 group
        c1_alleles = [a for a in patient_c_alleles if any(
            x in a for x in ["C*01", "C*03", "C*07", "C*08", "C*12", "C*14", "C*16"])]
        c2_alleles = [a for a in patient_c_alleles if any(
            x in a for x in ["C*02", "C*04", "C*05", "C*06", "C*15", "C*17", "C*18"])]

        # Check Bw4
        patient_b_alleles = patient_hla.get("HLA-B", [])
        bw4_alleles = [a for a in patient_b_alleles if any(
            x in a for x in ["B*44", "B*13", "B*27", "B*38", "B*49", "B*51", "B*52", "B*57", "B*58"])]

        # Check A3/A11
        patient_a_alleles = patient_hla.get("HLA-A", [])
        a3_a11 = [a for a in patient_a_alleles if "A*03" in a or "A*11" in a]

        # Missing self analysis
        missing_self = []
        if "KIR2DL1" in donor_kir and not c2_alleles:
            missing_self.append({
                "kir": "KIR2DL1",
                "missing_ligand": "HLA-C2",
                "effect": "NK activation (missing self) → enhanced GVL",
            })
        if ("KIR2DL2" in donor_kir or "KIR2DL3" in donor_kir) and not c1_alleles:
            missing_self.append({
                "kir": "KIR2DL2/3",
                "missing_ligand": "HLA-C1",
                "effect": "NK activation (missing self) → enhanced GVL",
            })
        if "KIR3DL1" in donor_kir and not bw4_alleles:
            missing_self.append({
                "kir": "KIR3DL1",
                "missing_ligand": "HLA-Bw4",
                "effect": "NK activation (missing self) → enhanced GVL",
            })
        if "KIR3DL2" in donor_kir and not a3_a11:
            missing_self.append({
                "kir": "KIR3DL2",
                "missing_ligand": "HLA-A3/A11",
                "effect": "NK activation (missing self) → enhanced GVL",
            })

        kir_mismatch = len(missing_self) > 0
        return {
            "donor_kir_genes": donor_kir,
            "patient_hla_c1": c1_alleles,
            "patient_hla_c2": c2_alleles,
            "patient_hla_bw4": bw4_alleles,
            "patient_hla_a3_a11": a3_a11,
            "missing_self_interactions": missing_self,
            "kir_ligand_mismatch": kir_mismatch,
            "predicted_alloreactivity": "enhanced" if kir_mismatch else "standard",
            "interpretation": (
                f"{len(missing_self)} missing-self interaction(s) detected → "
                f"{'favorable for GVL effect' if kir_mismatch else 'standard NK reactivity'}"
            ),
            "kir_hla_reference": KIR_HLA_INTERACTIONS,
        }

    def _design_persistence(self):
        """Design persistence strategy."""
        strategy = PERSISTENCE_STRATEGIES.get(
            self.persistence_strategy,
            PERSISTENCE_STRATEGIES["il15_secretion"]
        )
        all_strategies = {}
        for name, info in PERSISTENCE_STRATEGIES.items():
            all_strategies[name] = {
                "name": info["name"],
                "description": info["description"],
                "clinical_data": info["clinical_data"],
            }
        return {
            "selected_strategy": self.persistence_strategy,
            "details": strategy,
            "all_available_strategies": all_strategies,
        }

    def _ciml_protocol(self):
        """Generate CIML (Cytokine-Induced Memory-Like) NK protocol."""
        return {
            "name": "Cytokine-Induced Memory-Like (CIML) NK Cell Protocol",
            "priming_cytokines": {
                "IL-12": {"concentration": "10 ng/mL", "duration": "12-16 hours"},
                "IL-15": {"concentration": "50 ng/mL", "duration": "12-16 hours"},
                "IL-18": {"concentration": "50 ng/mL", "duration": "12-16 hours"},
            },
            "mechanism": (
                "Brief cytokine preactivation induces epigenetic reprogramming in NK cells, "
                "resulting in enhanced IFN-gamma production, cytotoxicity, and anti-tumor "
                "responses upon restimulation weeks to months later."
            ),
            "expected_outcomes": [
                "Enhanced IFN-gamma production upon restimulation",
                "Improved tumor cytotoxicity",
                "Longer persistence vs conventional NK cells",
                "Epigenetic memory (H3K4me3 at IFNG locus)",
            ],
            "clinical_evidence": "Phase I/II trials at Washington University (Berrien-Elliott et al.)",
            "post_priming": {
                "rest_period": "12-24 hours in low-dose IL-15 (1 ng/mL)",
                "expansion": "Optional feeder-based expansion post-priming",
                "infusion": "Fresh or after brief expansion",
            },
        }

    def _design_safety_features(self):
        """Design safety features including suicide switches and logic gating."""
        return {
            "suicide_switches": SUICIDE_SWITCHES,
            "recommended_switch": "iCasp9" if self.nk_source in ("UCB_NK", "UCB-NK", "IPSC_NK", "IPSC-NK") else "tEGFR_cetuximab",
            "logic_gating": {
                "description": "Dual antigen targeting for enhanced tumor specificity",
                "options": [
                    {
                        "type": "AND gate",
                        "mechanism": "Split CAR: activation only when both antigens present",
                        "example": f"CAR({self.target}) + synNotch(secondary antigen) → full activation",
                    },
                    {
                        "type": "NOT gate (iCAR)",
                        "mechanism": "Inhibitory CAR against normal tissue antigen",
                        "example": "Activating CAR + inhibitory CAR against normal marker",
                    },
                ],
            },
            "additional_safety": [
                "Low GvHD risk inherent to NK cells (no TCR-mediated alloreactivity)",
                "Limited in vivo persistence reduces long-term toxicity risk",
                "No CRS/ICANS observed at rates seen with CAR-T cells",
            ],
        }

    def _manufacturing_considerations(self):
        """Provide manufacturing considerations."""
        source = self.nk_source.replace("_", "-")
        considerations = {
            "nk_source": source,
            "transduction_method": "Retroviral vector (for UCB-NK) or non-viral (for iPSC-NK)",
            "expansion_protocol": {
                "feeder_cells": "K562-mb21-41BBL (irradiated) or equivalent",
                "cytokines": "IL-2 (200 IU/mL) + IL-15 (10 ng/mL)",
                "duration": "14-21 days",
                "expected_fold_expansion": "100-1000x (source-dependent)",
            },
            "quality_control": [
                "CAR expression by flow cytometry (>70% target)",
                "NK purity (CD56+CD3- >90%)",
                "Viability >70%",
                "Sterility testing",
                "Mycoplasma testing",
                "Endotoxin testing",
                "Cytotoxicity assay against target+ cell line",
            ],
            "cryopreservation": "Possible but may reduce viability/function by 10-20%",
            "dose_range": "1e7 to 1e9 NK cells per infusion (dose-escalation)",
            "lymphodepletion": "Fludarabine 25mg/m2 x3 + Cyclophosphamide 300mg/m2 x3",
        }
        return considerations

    def analyze(self):
        """Run NK cell therapy design analysis."""
        self.donor_data = self._load_donor_data()
        car_design = self._design_car_construct()
        nk_source_rec = self._compare_nk_sources()
        kir_hla = self._analyze_kir_hla(self.donor_data)
        persistence = self._design_persistence()
        ciml = self._ciml_protocol()
        safety = self._design_safety_features()
        manufacturing = self._manufacturing_considerations()

        results = {
            "analysis": "NK_cell_therapy_design",
            "analysis_date": datetime.now().isoformat(),
            "target_antigen": self.target,
            "tumor_type": self.tumor_type,
            "car_design": car_design,
            "nk_source_recommendation": nk_source_rec,
            "kir_hla_analysis": kir_hla,
            "persistence_strategy": persistence,
            "ciml_protocol": ciml,
            "safety_features": safety,
            "manufacturing_considerations": manufacturing,
        }
        return results


def main():
    parser = argparse.ArgumentParser(
        description="NK cell therapy design and CAR-NK construct optimization"
    )
    parser.add_argument("--target", default="CD19",
                        help="Target antigen (CD19, BCMA, HER2, etc.)")
    parser.add_argument("--tumor_type", default="b_cell_lymphoma",
                        help="Tumor type")
    parser.add_argument("--nk_source", default="ucb",
                        help="NK cell source (PB, UCB, iPSC, NK-92)")
    parser.add_argument("--persistence_strategy", default="il15_secretion",
                        help="Persistence strategy")
    parser.add_argument("--costimulatory", default="2B4_DAP10",
                        help="Costimulatory domains (underscore-separated)")
    parser.add_argument("--donors", default=None,
                        help="Path to donor HLA/KIR data (JSON)")
    parser.add_argument("--output", default="carnk_design/",
                        help="Output directory or JSON file")
    args = parser.parse_args()

    designer = NKDesigner(
        target=args.target,
        tumor_type=args.tumor_type,
        nk_source=args.nk_source,
        persistence_strategy=args.persistence_strategy,
        costimulatory=args.costimulatory,
        donors_path=args.donors,
    )

    results = designer.analyze()

    output_path = args.output
    if output_path.endswith("/"):
        os.makedirs(output_path, exist_ok=True)
        output_path = os.path.join(output_path, "nk_design_results.json")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"NK cell therapy design complete. Results: {output_path}")
    print(f"  Target: {results['target_antigen']}")
    print(f"  CAR architecture: {results['car_design']['construct_architecture']}")
    print(f"  NK source: {results['nk_source_recommendation']['selected_source']}")
    print(f"  KIR mismatch: {'Yes' if results['kir_hla_analysis']['kir_ligand_mismatch'] else 'No'}")
    print(f"  Persistence: {results['persistence_strategy']['selected_strategy']}")
    ms = results['kir_hla_analysis']['missing_self_interactions']
    print(f"  Missing-self interactions: {len(ms)}")


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"
