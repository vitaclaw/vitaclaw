#!/usr/bin/env python3
"""Shared utilities for biomedical agent skills."""
# COPYRIGHT NOTICE
# This file is part of the "Universal Biomedical Skills" project.
# Copyright (c) 2026 MD BABU MIA, PhD <md.babu.mia@mssm.edu>
# All Rights Reserved.
#
# This code is proprietary and confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Provenance: Authenticated by MD BABU MIA

import json
import os
from datetime import datetime


def get_project_root():
    """Return the vitaclaw project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def build_result(status, result, evidence=None, metadata=None, markdown=None):
    """Build a standardized result dictionary for agent skill outputs.

    Args:
        status: 'success', 'warning', or 'error'
        result: Main result dictionary
        evidence: List of evidence items supporting the result
        metadata: Dict of analysis metadata (tool version, timestamps, etc.)
        markdown: Human-readable markdown summary

    Returns:
        Standardized output dictionary
    """
    output = {
        "status": status,
        "result": result,
        "evidence": evidence or [],
        "metadata": {"timestamp": datetime.now().isoformat(), "tool_version": "1.0.0", **(metadata or {})},
    }
    if markdown:
        output["markdown"] = markdown
    return output


def safe_import(module_name, package_name=None):
    """Try to import a module, returning None if unavailable."""
    try:
        return __import__(module_name)
    except ImportError:
        return None


def write_output(result, output_path=None):
    """Write result dict as JSON to stdout and optionally to a file."""
    output = json.dumps(result, indent=2, default=str)
    print(output)
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output)


def parse_csv_file(filepath, delimiter=","):
    """Parse a CSV file into a list of dicts (header row as keys)."""
    import csv

    rows = []
    with open(filepath) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(dict(row))
    return rows


def parse_json_file(filepath):
    """Parse a JSON file and return the data."""
    with open(filepath) as f:
        return json.load(f)


__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"
