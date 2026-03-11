#!/usr/bin/env python3
"""肿瘤病程时间线总结 - 基于患者目录结构 + LLM 提取病程事件，构建结构化治疗时间线。"""

import argparse
import json
import os
import re
from datetime import datetime, timedelta

import sys as _sys

import requests

_sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------
EVENT_TYPES = {
    "diagnosis": "确诊",
    "surgery": "手术",
    "chemotherapy": "化疗",
    "radiation": "放疗",
    "targeted_therapy": "靶向治疗",
    "immunotherapy": "免疫治疗",
    "imaging": "影像检查",
    "pathology": "病理检查",
    "genetic_testing": "基因检测",
    "lab_result": "实验室检查",
    "hospitalization": "住院",
    "follow_up": "随访",
    "progression": "疾病进展",
    "recurrence": "复发",
    "adverse_event": "不良事件",
    "other": "其他",
}

# Supported file extensions for directory scanning
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md", ".doc", ".rtf"}


# ---------------------------------------------------------------------------
# LLM call helper
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
)
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")


def _llm_call(system_prompt: str, user_prompt: str, max_tokens: int = 8192) -> str:
    """Call LLM via OpenRouter API."""
    if not OPENROUTER_API_KEY:
        return "[错误] 未设置 OPENROUTER_API_KEY 环境变量"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        resp = requests.post(
            OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"[LLM调用失败] {e}"


# ---------------------------------------------------------------------------
# TumorJourneySummary
# ---------------------------------------------------------------------------
class TumorJourneySummary:
    """肿瘤病程时间线总结器。

    支持手动添加事件、扫描患者目录、LLM 提取病程事件、
    生成时间线和叙事性病程总结。
    """

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore(
            "tumor-journey-summary", data_dir=data_dir
        )

    # ----- add_event -----
    def add_event(
        self,
        event_type: str,
        date: str,
        description: str,
        details: dict = None,
        note: str = "",
    ) -> dict:
        """手动添加一个病程事件。

        Args:
            event_type: 事件类型，必须是 EVENT_TYPES 中的 key
            date: 事件日期，YYYY-MM-DD 格式
            description: 事件描述
            details: 可选的结构化详情，如 {"regimen": "FOLFOX", "cycles": 6}
            note: 备注
        Returns:
            存储的记录 dict
        """
        # Validate event type
        if event_type not in EVENT_TYPES:
            valid = ", ".join(EVENT_TYPES.keys())
            print(f"[错误] 不支持的事件类型: {event_type}")
            print(f"  支持的类型: {valid}")
            return {}

        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print(f"[错误] 日期格式不正确: {date}，请使用 YYYY-MM-DD 格式")
            return {}

        data = {
            "event_type": event_type,
            "event_type_cn": EVENT_TYPES[event_type],
            "date": date,
            "description": description,
            "details": details or {},
        }
        rec = self.store.append("event", data, note=note)

        type_cn = EVENT_TYPES[event_type]
        print(f"已记录事件 [{type_cn}] {date}: {description}")
        if details:
            for k, v in details.items():
                print(f"  {k}: {v}")
        if note:
            print(f"  备注: {note}")

        return rec

    # ----- list_events -----
    def list_events(
        self,
        event_type: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> list:
        """列出病程事件，支持按类型和日期范围筛选。

        Args:
            event_type: 筛选特定事件类型
            start_date: 起始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
        Returns:
            事件记录列表
        """
        records = self.store.query(record_type="event")

        if not records:
            print("暂无病程事件记录")
            return []

        # Filter by event type
        if event_type:
            if event_type not in EVENT_TYPES:
                print(f"[错误] 不支持的事件类型: {event_type}")
                return []
            records = [
                r
                for r in records
                if r["data"].get("event_type") == event_type
            ]

        # Filter by date range
        if start_date:
            records = [
                r for r in records if r["data"].get("date", "") >= start_date
            ]
        if end_date:
            records = [
                r for r in records if r["data"].get("date", "") <= end_date
            ]

        # Sort by event date
        records.sort(key=lambda r: r["data"].get("date", ""))

        if not records:
            print("未找到符合条件的事件")
            return []

        # Display
        print(f"\n病程事件列表 (共 {len(records)} 条)")
        print(f"{'日期':<14} {'类型':<12} {'描述'}")
        print("-" * 70)

        for r in records:
            d = r["data"]
            date = d.get("date", "未知日期")
            type_cn = d.get("event_type_cn", d.get("event_type", "未知"))
            desc = d.get("description", "")
            print(f"{date:<14} {type_cn:<12} {desc}")

            # Show details if present
            details = d.get("details", {})
            if details:
                for k, v in details.items():
                    print(f"{'':>14} {'':>12}   {k}: {v}")

            # Show note if present
            if r.get("note"):
                print(f"{'':>14} {'':>12}   备注: {r['note']}")

        return records

    # ----- scan_directory -----
    def scan_directory(self, patient_dir: str) -> list:
        """扫描患者目录，发现医疗文档文件。

        Args:
            patient_dir: 患者文件目录路径
        Returns:
            发现的文件列表 [{path, name, extension, size_kb}]
        """
        if not os.path.isdir(patient_dir):
            print(f"[错误] 目录不存在: {patient_dir}")
            return []

        found_files = []

        for root, _dirs, files in os.walk(patient_dir):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                fpath = os.path.join(root, fname)
                try:
                    size_bytes = os.path.getsize(fpath)
                except OSError:
                    size_bytes = 0

                file_info = {
                    "path": fpath,
                    "name": fname,
                    "extension": ext,
                    "size_kb": round(size_bytes / 1024, 1),
                }
                found_files.append(file_info)

        # Sort by name
        found_files.sort(key=lambda f: f["name"])

        # Store the scan result
        scan_data = {
            "directory": os.path.abspath(patient_dir),
            "scan_time": datetime.now().isoformat(),
            "file_count": len(found_files),
            "files": found_files,
        }
        self.store.append("scan", scan_data, note=f"扫描目录: {patient_dir}")

        # Display
        print(f"\n目录扫描结果: {os.path.abspath(patient_dir)}")
        print(f"发现 {len(found_files)} 个医疗文档文件\n")

        if found_files:
            print(f"{'文件名':<50} {'类型':<8} {'大小'}")
            print("-" * 70)
            for f in found_files:
                print(
                    f"{f['name']:<50} {f['extension']:<8} {f['size_kb']:.1f} KB"
                )

            # Summary by extension
            ext_counts = {}
            for f in found_files:
                ext_counts[f["extension"]] = (
                    ext_counts.get(f["extension"], 0) + 1
                )
            print(f"\n文件类型统计:")
            for ext, cnt in sorted(ext_counts.items()):
                print(f"  {ext}: {cnt} 个")
        else:
            print("未发现支持的医疗文档文件")
            print(
                f"  支持的格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        return found_files

    # ----- extract_events_from_text -----
    def extract_events_from_text(
        self, text: str, source_file: str = ""
    ) -> list:
        """使用 LLM 从自由文本中提取结构化病程事件。

        Args:
            text: 包含病程信息的自由文本
            source_file: 来源文件路径（可选，用于标记来源）
        Returns:
            提取的事件列表
        """
        if not OPENROUTER_API_KEY:
            print("[错误] 未设置 OPENROUTER_API_KEY 环境变量，无法调用 LLM 提取事件")
            print("  请设置环境变量后重试，或使用 add 命令手动添加事件")
            return []

        if not text.strip():
            print("[错误] 输入文本为空")
            return []

        # Build the valid event types for the prompt
        type_list = "\n".join(
            [f'  - "{k}": {v}' for k, v in EVENT_TYPES.items()]
        )

        system_prompt = f"""你是一位专业的医学信息提取助手。你的任务是从患者的医疗文本中提取所有病程事件。

请提取每一个有时间信息的医学事件，包括但不限于：确诊、手术、化疗、放疗、检查、复发等。

对于每个事件，请提取：
- date: 事件日期，格式 YYYY-MM-DD。如果只有年月，用该月1日。如果只有年，用1月1日。如果没有明确日期，根据上下文合理推断。
- event_type: 事件类型，必须是以下之一：
{type_list}
- description: 事件的简要描述（中文，一到两句话）
- details: 结构化详情（JSON对象），如药物名称、方案、剂量、检查结果等

请以严格的 JSON 数组格式返回结果，不要包含其他文字说明。确保 JSON 格式正确可解析。

示例输出：
```json
[
  {{
    "date": "2025-01-15",
    "event_type": "diagnosis",
    "description": "结肠镜检查发现升结肠肿物，活检确认为中分化腺癌",
    "details": {{"location": "升结肠", "pathology": "中分化腺癌", "method": "结肠镜+活检"}}
  }},
  {{
    "date": "2025-02-01",
    "event_type": "surgery",
    "description": "行腹腔镜右半结肠切除术",
    "details": {{"procedure": "腹腔镜右半结肠切除术", "margin": "切缘阴性"}}
  }}
]
```"""

        user_prompt = f"请从以下医疗文本中提取所有病程事件：\n\n{text}"

        print("正在使用 LLM 提取病程事件...")
        raw_response = _llm_call(system_prompt, user_prompt)

        if raw_response.startswith("[错误]") or raw_response.startswith(
            "[LLM调用失败]"
        ):
            print(f"  {raw_response}")
            return []

        # Parse JSON from LLM response
        events = self._parse_events_json(raw_response)

        if not events:
            print("  未能从文本中提取到有效事件")
            return []

        # Add extracted events to store
        added = []
        for evt in events:
            event_type = evt.get("event_type", "other")
            if event_type not in EVENT_TYPES:
                event_type = "other"

            date = evt.get("date", datetime.now().strftime("%Y-%m-%d"))
            description = evt.get("description", "")
            details = evt.get("details", {})

            # Add source file info to details
            if source_file:
                details["source_file"] = source_file

            rec = self.add_event(
                event_type=event_type,
                date=date,
                description=description,
                details=details,
                note=f"LLM自动提取" + (f" (来源: {source_file})" if source_file else ""),
            )
            if rec:
                added.append(rec)

        print(f"\n共提取并记录 {len(added)} 个病程事件")
        return added

    def _parse_events_json(self, response: str) -> list:
        """从 LLM 响应中解析 JSON 事件数组。

        Handles responses that may contain markdown code blocks or
        extra text surrounding the JSON.
        """
        # Try direct parse first
        try:
            result = json.loads(response.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # Try finding a JSON array in the response
        bracket_start = response.find("[")
        bracket_end = response.rfind("]")
        if bracket_start != -1 and bracket_end > bracket_start:
            try:
                result = json.loads(
                    response[bracket_start : bracket_end + 1]
                )
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        return []

    # ----- build_journey -----
    def build_journey(self, text_or_file: str) -> list:
        """从文本或文件构建病程事件。

        如果输入是文件路径且为文本文件，则读取文件内容后提取事件。
        否则视为直接文本输入。

        Args:
            text_or_file: 文本内容或文本文件路径
        Returns:
            提取的事件列表
        """
        # Check if it's a file path
        if os.path.isfile(text_or_file):
            ext = os.path.splitext(text_or_file)[1].lower()
            if ext in {".txt", ".md"}:
                print(f"读取文件: {text_or_file}")
                try:
                    with open(text_or_file, "r", encoding="utf-8") as f:
                        text = f.read()
                except UnicodeDecodeError:
                    # Fallback to gbk for Chinese Windows files
                    try:
                        with open(text_or_file, "r", encoding="gbk") as f:
                            text = f.read()
                    except Exception as e:
                        print(f"[错误] 无法读取文件: {e}")
                        return []
                except Exception as e:
                    print(f"[错误] 无法读取文件: {e}")
                    return []

                if not text.strip():
                    print("[错误] 文件内容为空")
                    return []

                return self.extract_events_from_text(
                    text, source_file=text_or_file
                )
            else:
                print(f"[错误] 暂不支持直接解析 {ext} 格式文件")
                print("  目前支持: .txt, .md")
                print("  PDF/DOCX 文件请先转换为文本，或使用其他工具提取文本后再导入")
                return []
        else:
            # Treat as direct text input
            return self.extract_events_from_text(text_or_file)

    # ----- generate_summary -----
    def generate_summary(self) -> str:
        """使用 LLM 生成叙事性病程总结。

        收集所有事件，按日期排序，发送给 LLM 生成结构化的
        病程叙述，突出关键治疗决策和疾病状态变化。

        Returns:
            病程总结文本
        """
        if not OPENROUTER_API_KEY:
            print("[错误] 未设置 OPENROUTER_API_KEY 环境变量，无法生成总结")
            print("  请设置环境变量后重试")
            return ""

        records = self.store.query(record_type="event")
        if not records:
            print("暂无病程事件记录，无法生成总结")
            print("  请先使用 add 或 extract 命令添加事件")
            return ""

        # Sort by event date
        records.sort(key=lambda r: r["data"].get("date", ""))

        # Build event list text for LLM
        event_lines = []
        for r in records:
            d = r["data"]
            date = d.get("date", "未知日期")
            type_cn = d.get("event_type_cn", EVENT_TYPES.get(d.get("event_type", "other"), "其他"))
            desc = d.get("description", "")
            details = d.get("details", {})

            line = f"- {date} [{type_cn}] {desc}"
            if details:
                # Exclude source_file from details display
                display_details = {
                    k: v for k, v in details.items() if k != "source_file"
                }
                if display_details:
                    detail_str = "；".join(
                        [f"{k}: {v}" for k, v in display_details.items()]
                    )
                    line += f" ({detail_str})"
            event_lines.append(line)

        events_text = "\n".join(event_lines)

        system_prompt = """你是一位资深的肿瘤科医生，擅长撰写病程总结。

请根据提供的病程事件列表，生成一份专业的病程叙事总结。要求：

1. 按时间顺序组织叙述
2. 突出关键治疗决策和治疗方案的转折点
3. 描述疾病状态变化（缓解、稳定、进展、复发等）
4. 注意治疗反应和不良事件
5. 使用专业但易懂的中文医学语言
6. 在结尾处简要评估当前疾病状态和治疗进程

格式要求：
- 使用 Markdown 格式
- 标题使用 "## 病程总结"
- 分段叙述，每个重要阶段一段
- 结尾加 "### 当前评估" 小节"""

        user_prompt = f"以下是该患者的病程事件记录（共 {len(records)} 条）：\n\n{events_text}"

        print("正在使用 LLM 生成病程总结...")
        summary = _llm_call(system_prompt, user_prompt)

        if summary.startswith("[错误]") or summary.startswith("[LLM调用失败]"):
            print(f"  {summary}")
            return ""

        # Store the summary
        self.store.append(
            "summary",
            {
                "content": summary,
                "event_count": len(records),
                "generated_at": datetime.now().isoformat(),
            },
            note="LLM生成的病程总结",
        )

        print("\n" + summary)
        return summary

    # ----- export_timeline -----
    def export_timeline(self) -> str:
        """导出所有事件为格式化的 Markdown 时间线。

        Returns:
            Markdown 格式的时间线文本
        """
        records = self.store.query(record_type="event")
        if not records:
            print("暂无病程事件记录")
            return ""

        # Sort by event date
        records.sort(key=lambda r: r["data"].get("date", ""))

        lines = ["## 肿瘤病程时间线", ""]

        # Group by year-month for visual organization
        current_year_month = ""
        for r in records:
            d = r["data"]
            date = d.get("date", "未知日期")
            type_cn = d.get(
                "event_type_cn",
                EVENT_TYPES.get(d.get("event_type", "other"), "其他"),
            )
            desc = d.get("description", "")
            details = d.get("details", {})

            # Add year-month separator if changed
            ym = date[:7] if len(date) >= 7 else date
            if ym != current_year_month:
                current_year_month = ym
                lines.append("")

            lines.append(f"### {date} {type_cn}")
            lines.append(desc)

            # Show details if present
            display_details = {
                k: v
                for k, v in details.items()
                if k != "source_file"
            }
            if display_details:
                lines.append("")
                for k, v in display_details.items():
                    lines.append(f"- **{k}**: {v}")

            # Show note if present
            if r.get("note"):
                lines.append(f"\n> {r['note']}")

            lines.append("")

        # Add generation timestamp
        lines.append("---")
        lines.append(
            f"*时间线生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        )

        timeline = "\n".join(lines)
        print(timeline)

        # Store the timeline export
        self.store.append(
            "timeline_export",
            {
                "content": timeline,
                "event_count": len(records),
                "generated_at": datetime.now().isoformat(),
            },
            note="导出的Markdown时间线",
        )

        return timeline


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="肿瘤病程时间线总结 - 构建结构化治疗旅程时间线"
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # add
    p_add = sub.add_parser("add", help="添加病程事件")
    p_add.add_argument(
        "--type",
        required=True,
        dest="event_type",
        choices=list(EVENT_TYPES.keys()),
        help="事件类型",
    )
    p_add.add_argument(
        "--date", required=True, help="事件日期 (YYYY-MM-DD)"
    )
    p_add.add_argument("--desc", required=True, help="事件描述")
    p_add.add_argument(
        "--details", default=None, help="结构化详情 (JSON字符串)"
    )
    p_add.add_argument("--note", default="", help="备注")

    # list
    p_list = sub.add_parser("list", help="列出病程事件")
    p_list.add_argument(
        "--type",
        dest="event_type",
        default=None,
        choices=list(EVENT_TYPES.keys()),
        help="筛选事件类型",
    )
    p_list.add_argument("--start", default=None, help="起始日期 (YYYY-MM-DD)")
    p_list.add_argument("--end", default=None, help="结束日期 (YYYY-MM-DD)")

    # scan
    p_scan = sub.add_parser("scan", help="扫描患者文件目录")
    p_scan.add_argument("directory", help="患者文件目录路径")

    # extract
    p_extract = sub.add_parser("extract", help="从文本或文件提取病程事件")
    p_extract_group = p_extract.add_mutually_exclusive_group(required=True)
    p_extract_group.add_argument("--text", help="直接输入文本")
    p_extract_group.add_argument("--file", help="文本文件路径")

    # summary
    sub.add_parser("summary", help="生成病程叙事总结 (需要 LLM)")

    # timeline
    sub.add_parser("timeline", help="导出 Markdown 时间线")

    args = parser.parse_args()
    journey = TumorJourneySummary()

    if args.command == "add":
        details = None
        if args.details:
            try:
                details = json.loads(args.details)
            except json.JSONDecodeError:
                print(f"[错误] details 参数不是有效的 JSON: {args.details}")
                return
        journey.add_event(
            event_type=args.event_type,
            date=args.date,
            description=args.desc,
            details=details,
            note=args.note,
        )

    elif args.command == "list":
        journey.list_events(
            event_type=args.event_type,
            start_date=args.start,
            end_date=args.end,
        )

    elif args.command == "scan":
        journey.scan_directory(args.directory)

    elif args.command == "extract":
        if args.text:
            journey.extract_events_from_text(args.text)
        elif args.file:
            journey.build_journey(args.file)

    elif args.command == "summary":
        journey.generate_summary()

    elif args.command == "timeline":
        journey.export_timeline()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
