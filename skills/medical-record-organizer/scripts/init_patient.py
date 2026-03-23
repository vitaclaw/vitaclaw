#!/usr/bin/env python3
"""Initialize an anonymized patient directory structure for medical record intake."""

import sys
import json
import hashlib
import re
from pathlib import Path
from datetime import date


def get_patients_base() -> Path:
    return Path.home() / ".openclaw" / "patients"


def get_templates_dir() -> Path:
    return (
        Path.home()
        / ".openclaw"
        / "skills"
        / "medical-record-organizer"
        / "assets"
        / "templates"
    )


def build_patient_id(raw_input: str) -> str:
    """Return an anonymized patient id (never persist real name)."""
    value = re.sub(r"\s+", "", (raw_input or "").strip())
    if not value:
        raise ValueError("patient identifier cannot be empty")

    # If user already provides an anonymized id, reuse it
    if re.fullmatch(r"[A-Za-z0-9_-]{4,40}", value) and not re.search(r"[\u4e00-\u9fff]", value):
        return value.upper()

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10].upper()
    return f"PT-{digest}"


def create_directory_tree(patient_dir: Path) -> None:
    dirs = [
        "01_当前状态/历史快照",
        "02_诊断与分期/病理报告",
        "03_分子病理/基因检测",
        "03_分子病理/免疫组化",
        "04_影像学/CT",
        "04_影像学/MRI",
        "04_影像学/PET-CT",
        "04_影像学/超声",
        "04_影像学/X光DR",
        "05_检验检查/血常规",
        "05_检验检查/生化肝肾功",
        "05_检验检查/肿瘤标志物",
        "06_治疗决策历史",
        "07_合并症与用药",
        "08_出院小结",
        "08_出院小结/入院小结",
        "09_Apple_Health",
        "10_原始文件/未分类",
        "11_诊断证明",
        "10_原始文件/门诊记录",
        "10_原始文件/原始未遮挡",
    ]
    for d in dirs:
        (patient_dir / d).mkdir(parents=True, exist_ok=True)


def create_index(patient_dir: Path, patient_id: str) -> None:
    index_path = patient_dir / "INDEX.md"
    if index_path.exists():
        return
    template_path = get_templates_dir() / "INDEX-template.md"
    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        content = content.replace("{{PATIENT_NAME}}", patient_id)
        content = content.replace("{{PATIENT_ID}}", patient_id)
        content = content.replace("{{UPDATE_DATE}}", date.today().isoformat())
    else:
        content = f"# 病历索引 — {patient_id}\n\n> 最近更新：{date.today().isoformat()}\n"
    index_path.write_text(content, encoding="utf-8")


def create_timeline(patient_dir: Path, patient_id: str) -> None:
    timeline_path = patient_dir / "timeline.md"
    if timeline_path.exists():
        return
    template_path = get_templates_dir() / "timeline-template.md"
    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        content = content.replace("{{PATIENT_NAME}}", patient_id)
        content = content.replace("{{PATIENT_ID}}", patient_id)
    else:
        content = (
            f"# 病历时间线 — {patient_id}\n\n"
            "> 按时间倒序排列。每次录入新文档自动追加。\n\n"
            "| 日期 | 文档类型 | 摘要 | 文件路径 |\n"
            "|------|----------|------|--------|\n"
        )
    timeline_path.write_text(content, encoding="utf-8")


def create_profile(patient_dir: Path, patient_id: str) -> None:
    profile_path = patient_dir / "profile.json"
    if profile_path.exists():
        return
    profile = {
        "patient_id": patient_id,
        "name": "REDACTED",
        "age": None,
        "diagnosis": None,
        "diagnosis_date": None,
        "hospital": None,
        "doctor": None,
        "allergies": [],
        "notes": "",
        "privacy_mode": "ON",
    }
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def create_tumor_marker_trend(patient_dir: Path) -> None:
    trend_path = patient_dir / "05_检验检查" / "肿瘤标志物" / "肿标趋势.md"
    if trend_path.exists():
        return
    content = (
        "# 肿瘤标志物趋势\n"
        "\n"
        "| 日期 | CEA | CA-199 | AFP | CA-125 | 其他 | 趋势 | 备注 |\n"
        "|------|-----|--------|-----|--------|------|------|------|\n"
    )
    trend_path.write_text(content, encoding="utf-8")


def create_treatment_history(patient_dir: Path) -> None:
    history_path = patient_dir / "06_治疗决策历史" / "治疗决策总表.md"
    if history_path.exists():
        return
    content = (
        "# 治疗决策历史总表\n"
        "\n"
        "| 线数 | 时间段 | 方案 | 疗效 | 副反应 | 影像趋势 | 标志物趋势 | 决策思路 |\n"
        "|------|--------|------|------|--------|----------|-----------|--------|\n"
    )
    history_path.write_text(content, encoding="utf-8")


def create_current_status(patient_dir: Path, patient_id: str) -> None:
    status_path = patient_dir / "01_当前状态" / "当前状态.md"
    if status_path.exists():
        return
    content = (
        f"# 当前状态快照 — {patient_id}\n"
        "\n"
        f"> 最近更新：{date.today().isoformat()}\n"
        "\n"
        "## 当前治疗方案\n"
        "- **方案名称**：（待填写）\n"
        "- **开始日期**：—\n"
        "- **周期**：—\n"
        "\n"
        "## 最新影像学评估\n"
        "- **日期**：—\n"
        "- **类型**：—\n"
        "- **主要发现**：（待填写）\n"
        "- **疗效评价**：—\n"
        "\n"
        "## 最新肿瘤标志物\n"
        "| 指标 | 数值 | 日期 | 趋势 |\n"
        "|------|------|------|------|\n"
        "| CEA | — | — | — |\n"
        "| CA-199 | — | — | — |\n"
        "| AFP | — | — | — |\n"
        "| CA-125 | — | — | — |\n"
        "\n"
        "## 主要合并症\n"
        "- （待填写）\n"
        "\n"
        "## ECOG 体能评分\n"
        "- **评分**：—\n"
        "- **评估日期**：—\n"
        "\n"
        "## 累计毒性警告\n"
        "- （待填写）\n"
    )
    status_path.write_text(content, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 init_patient.py [patient_name_or_alias]", file=sys.stderr)
        sys.exit(1)

    raw_identifier = sys.argv[1].strip()
    if not raw_identifier:
        print("Error: patient identifier cannot be empty", file=sys.stderr)
        sys.exit(1)

    try:
        patient_id = build_patient_id(raw_identifier)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    patient_dir = get_patients_base() / patient_id

    # Create directory tree
    create_directory_tree(patient_dir)

    # Create template files (idempotent — skip if already exist)
    create_index(patient_dir, patient_id)
    create_timeline(patient_dir, patient_id)
    create_profile(patient_dir, patient_id)
    create_tumor_marker_trend(patient_dir)
    create_treatment_history(patient_dir)
    create_current_status(patient_dir, patient_id)

    # Print the patient directory path to stdout
    print(str(patient_dir))


if __name__ == "__main__":
    main()
