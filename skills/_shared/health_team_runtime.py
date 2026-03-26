#!/usr/bin/env python3
"""Chief-led multi-agent team orchestration for VitaClaw Iteration 3."""

from __future__ import annotations

from datetime import datetime

from .doctor_match_workflow import DoctorMatchWorkflow
from .health_flagship_scenarios import (
    AnnualCheckupAdvisorWorkflow,
    DiabetesControlHub,
    HypertensionDailyCopilot,
)
from .health_memory import HealthMemoryWriter
from .health_operations import HealthOperationsRunner

ROLE_DEFINITIONS = {
    "health-chief-of-staff": {
        "label": "健康总管",
        "package": "core",
        "tool_policy": "local-files-and-internal-scripts",
        "sandbox": "local-no-web",
        "can_write": [],
        "long_term_memory": True,
        "raw_archive": False,
        "tone": "clear-steady-continuous",
    },
    "health-main": {
        "label": "主健康中枢",
        "package": "core",
        "tool_policy": "local-files-write",
        "sandbox": "local-write",
        "can_write": ["memory.md", "items", "appointments", "behavior-plans", "digests"],
        "long_term_memory": True,
        "raw_archive": False,
        "tone": "quiet-execution",
    },
    "health-records": {
        "label": "病历秘书",
        "package": "core",
        "tool_policy": "local-records-plus-controlled-web",
        "sandbox": "local-controlled-public-web",
        "can_write": ["archive-summary", "timeline", "role-brief"],
        "long_term_memory": False,
        "raw_archive": True,
        "tone": "structured-documentary",
    },
    "health-metrics": {
        "label": "指标分析师",
        "package": "core",
        "tool_policy": "local-analysis-only",
        "sandbox": "local-no-web",
        "can_write": ["role-brief"],
        "long_term_memory": True,
        "raw_archive": False,
        "tone": "quantitative-calm",
    },
    "health-lifestyle": {
        "label": "生活方式教练",
        "package": "core",
        "tool_policy": "local-planning-only",
        "sandbox": "local-no-web",
        "can_write": ["role-brief"],
        "long_term_memory": True,
        "raw_archive": False,
        "tone": "supportive-low-pressure",
    },
    "health-safety": {
        "label": "风险雷达",
        "package": "core",
        "tool_policy": "local-audit-only",
        "sandbox": "local-no-web",
        "can_write": ["alert", "task", "role-brief"],
        "long_term_memory": True,
        "raw_archive": False,
        "tone": "high-reliability",
    },
    "health-research": {
        "label": "医疗研究助理",
        "package": "core",
        "tool_policy": "official-evidence-only",
        "sandbox": "research-no-long-term-memory",
        "can_write": ["role-brief"],
        "long_term_memory": False,
        "raw_archive": False,
        "tone": "evidence-first",
    },
    "health-mental": {
        "label": "心理健康守门员",
        "package": "core",
        "tool_policy": "local-support-only",
        "sandbox": "local-no-web",
        "can_write": ["role-brief"],
        "long_term_memory": False,
        "raw_archive": False,
        "tone": "gentle-supportive",
    },
    "health-family": {
        "label": "家庭照护协调者",
        "package": "family-care",
        "tool_policy": "local-family-care",
        "sandbox": "default-read-mostly",
        "can_write": ["family-brief", "family-task"],
        "long_term_memory": False,
        "raw_archive": False,
        "tone": "caregiver-reliable",
    },
    "health-oncology": {
        "label": "肿瘤专科参谋",
        "package": "oncology",
        "tool_policy": "local-oncology-restricted",
        "sandbox": "restricted-labs",
        "can_write": ["oncology-brief"],
        "long_term_memory": False,
        "raw_archive": True,
        "tone": "specialist-cautious",
    },
}

PACKAGE_MATRIX = {
    "core": [
        "health-chief-of-staff",
        "health-main",
        "health-records",
        "health-metrics",
        "health-lifestyle",
        "health-safety",
        "health-research",
        "health-mental",
    ],
    "family-care": ["health-family"],
    "oncology": ["health-oncology"],
    "labs": [],
}

ROLE_CADENCE = {
    "health-chief-of-staff": "30m",
    "health-main": "2h",
    "health-records": "6h",
    "health-metrics": "2h",
    "health-lifestyle": "12h",
    "health-safety": "30m",
    "health-research": "0m",
    "health-mental": "8h",
    "health-family": "6h",
    "health-oncology": "0m",
}

ROUTE_TABLE = {
    "hypertension-daily-copilot": ["health-metrics", "health-lifestyle"],
    "diabetes-control-hub": ["health-metrics", "health-lifestyle"],
    "annual-checkup-advisor": ["health-records", "health-metrics"],
    "doctor-profile-harvester": ["health-records"],
    "doctor-fit-finder": ["health-records", "health-research", "health-metrics"],
    "mental-support": ["health-mental"],
    "research-brief": ["health-research"],
    "family-care": ["health-family"],
    "oncology-review": ["health-oncology", "health-research", "health-safety"],
}

STANDARD_DISCLAIMER = "仅供长期追踪、准备就医和风险分层使用，不替代医生诊断、处方调整或急救系统。"


class HealthTeamOrchestrator:
    """Chief-led orchestration layer that turns flagship scenarios into team outputs."""

    def __init__(
        self,
        data_dir: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        patients_root: str | None = None,
        patient_id: str | None = None,
        packages: list[str] | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.packages = self._normalize_packages(packages)
        self.writer = HealthMemoryWriter(
            memory_root=memory_dir,
            workspace_root=workspace_root,
            now_fn=self._now_fn,
        )
        self.hypertension = HypertensionDailyCopilot(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.diabetes = DiabetesControlHub(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.checkup = AnnualCheckupAdvisorWorkflow(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.doctor_match = DoctorMatchWorkflow(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            now_fn=self._now_fn,
        )
        self.operations = HealthOperationsRunner(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )

    def _now(self) -> datetime:
        return self._now_fn()

    def _normalize_packages(self, packages: list[str] | None) -> list[str]:
        ordered = ["core"]
        for package in packages or []:
            if package and package not in ordered:
                ordered.append(package)
        return ordered

    def enabled_roles(self) -> list[str]:
        roles: list[str] = []
        for package in self.packages:
            for role in PACKAGE_MATRIX.get(package, []):
                if role not in roles:
                    roles.append(role)
        return roles

    def context_policy(self, context: str = "direct") -> dict[str, bool | str]:
        return {
            "context": context,
            "load_long_term_memory": context == "direct",
            "load_memory_in_group": False,
            "load_memory_in_public": False,
        }

    def role_policies(self, context: str = "direct") -> dict[str, dict[str, object]]:
        direct_memory = context == "direct"
        policies: dict[str, dict[str, object]] = {}
        for role in self.enabled_roles():
            base = ROLE_DEFINITIONS[role]
            policies[role] = {
                "tool_policy": base["tool_policy"],
                "sandbox": base["sandbox"],
                "can_write": list(base["can_write"]),
                "long_term_memory_allowed": bool(base["long_term_memory"]) and direct_memory,
                "raw_archive_allowed": bool(base["raw_archive"]),
                "tone": base["tone"],
            }
        return policies

    def route_scenario(self, scenario: str, crisis: bool = False) -> list[str]:
        roles = list(ROUTE_TABLE.get(scenario, []))
        enabled = set(self.enabled_roles())
        roles = [role for role in roles if role in enabled]
        if crisis and "health-safety" in enabled and "health-safety" not in roles:
            roles.append("health-safety")
        return roles

    def _base_task_id(self, scenario: str) -> str:
        slug = scenario.replace("_", "-")
        return f"{slug}-{self._now().strftime('%Y%m%d%H%M%S')}"

    def _severity_is_must_seek(self, sections: dict[str, list[str]]) -> bool:
        urgent_keywords = ("立即", "急救", "尽快就医", "危急", "自伤", "他伤", "高血压危象")
        negative_markers = ("当前没有触发", "未触发", "暂无", "没有新的")
        for value in sections.get("## 必须就医", []):
            line = value.strip()
            if not line:
                continue
            if any(marker in line for marker in negative_markers):
                continue
            if any(keyword in line for keyword in urgent_keywords):
                return True
        return False

    def _run_flagship_workflow(self, scenario: str, payload: dict, write: bool) -> dict:
        if scenario == "hypertension-daily-copilot":
            return self.hypertension.daily_entry(write=write, **payload)
        if scenario == "diabetes-control-hub":
            return self.diabetes.daily_log(write=write, **payload)
        if scenario == "annual-checkup-advisor":
            return self.checkup.import_report(**payload)
        if scenario == "doctor-fit-finder":
            return self.doctor_match.match_doctors(write=write, **payload)
        raise ValueError(f"Unsupported flagship scenario: {scenario}")

    def _role_summary_lines(self, role: str, scenario: str, result: dict, payload: dict) -> list[str]:
        if role == "health-records":
            return [
                f"聚焦：{scenario} 的报告、病历摘要、统一时间线与原始证据关联。",
                f"来源文件数：{len(result.get('sources_used', []))}",
                "长期画像不在本角色直接修改范围内。",
            ]
        if role == "health-metrics":
            return [
                f"聚焦：{scenario} 的阈值、趋势、连续性和停滞识别。",
                f"风险条目数：{len(result.get('sections', {}).get('## 风险', []))}",
                "输出只给 brief 与建议写回，不直接修改长期事实。",
            ]
        if role == "health-lifestyle":
            return [
                f"聚焦：{scenario} 的饮食、运动、作息、依从性与执行障碍。",
                f"重点 follow-up 数：{len(result.get('follow_up_tasks', []))}",
                "输出只给 brief 与行为计划建议。",
            ]
        if role == "health-safety":
            return [
                f"聚焦：{scenario} 的危急值、升级路径与必须就医条件。",
                "只允许生成 alert / task / brief。",
            ]
        if role == "health-research":
            return [
                "本轮只允许处理去标识化问题和证据口径校准。",
                "不读取长期健康画像，也不读取 raw patient archive。",
            ]
        if role == "health-mental":
            return [
                "本轮以支持型心理健康守门为主，关注情绪、睡眠、功能和危机分流。",
                "不提供治疗化建议。",
            ]
        if role == "health-family":
            return [
                "本轮面向照护协同和家庭执行闭环。",
                "默认不直接接触主用户长期健康记忆，除非显式授权。",
            ]
        if role == "health-oncology":
            return [
                "本轮为肿瘤专科辅助视角，只在对应包启用时使用。",
                "不得在无明确证据和医生上下文时给出处置性结论。",
            ]
        return [f"聚焦：{scenario}"]

    def _role_sections(self, role: str, result: dict, payload: dict) -> dict[str, list[str]]:
        base_sections = result.get("sections", {})
        if role == "health-records":
            return {
                "## 记录": [
                    *(base_sections.get("## 记录", [])[:3] or ["- 当前没有新的病历类记录。"]),
                    f"- 写回目标：{', '.join(result.get('writebacks', [])[:3]) or 'pending'}",
                ],
                "## 解读": [
                    "- 重点是把报告、时间线和病历归档转成后续可复用摘要。",
                    "- 不直接改长期画像。",
                ],
                "## 趋势": base_sections.get("## 趋势", [])[:3] or ["- 等待更多历史比较。"],
                "## 风险": base_sections.get("## 风险", [])[:3] or ["- 暂无记录层新风险。"],
                "## 建议": [
                    "- 若本轮有新报告，优先同步 patient archive summary 和 health timeline。",
                    "- 把待复查项写进 appointments 和 follow-up。",
                ],
                "## 必须就医": base_sections.get("## 必须就医", [])[:2] or ["- 暂无。"],
            }
        if role == "health-lifestyle":
            lifestyle_lines = []
            for key in ("diet_summary", "exercise_summary", "meals_summary", "symptoms"):
                value = payload.get(key)
                if value:
                    lifestyle_lines.append(f"- {key}: {value}")
            return {
                "## 记录": lifestyle_lines or ["- 当前 lifestyle 线索有限，需依赖后续 daily 补录。"],
                "## 解读": [
                    "- lifestyle 角色主要判断执行连续性、诱因和依从性，而不是诊断。",
                    "- 优先把缺失记录转成下一步行为计划。",
                ],
                "## 趋势": ["- 行为计划和执行障碍将决定是否需要更强提醒。"]
                + result.get("sections", {}).get("## 趋势", [])[:2],
                "## 风险": result.get("sections", {}).get("## 风险", [])[:2] or ["- 暂无。"],
                "## 建议": [
                    "- 把执行断点沉淀为 execution barriers。",
                    "- 优先维持低成本、可持续的生活方式动作。",
                ],
                "## 必须就医": result.get("sections", {}).get("## 必须就医", [])[:1]
                or ["- lifestyle 线未新增必须就医信号。"],
            }
        if role == "health-safety":
            must_seek = result.get("sections", {}).get("## 必须就医", [])
            risk = result.get("sections", {}).get("## 风险", [])
            return {
                "## 记录": ["- 本角色只处理升级与边界，不接管普通随访。"] + (risk[:2] or ["- 当前未见新增高危风险。"]),
                "## 解读": [
                    "- 风险层优先于免责声明呈现。",
                    "- 出现危急值或心理危机时，直接打断普通建议流程。",
                ],
                "## 趋势": ["- 观察是否存在连续高风险、连续失访或持续恶化。"],
                "## 风险": risk[:3] or ["- 暂无。"],
                "## 建议": [
                    "- 仅保留升级、求助和立即处理建议。",
                    "- 不提供诊断或处方调整结论。",
                ],
                "## 必须就医": must_seek or ["- 当前未触发必须就医。"],
            }
        if role == "health-mental":
            return {
                "## 记录": [
                    "- 本角色默认只读取 mood/sleep/PHQ/GAD 与相关 daily。",
                    "- 当前若无心理量表和睡眠记录，则只输出支持性 follow-up。",
                ],
                "## 解读": [
                    "- 以支持、陪伴、危机识别和求助引导为边界。",
                ],
                "## 趋势": ["- 睡眠和情绪若持续恶化，应与 safety 联动。"],
                "## 风险": ["- 若出现自伤/他伤风险、极端绝望感或快速恶化，立即升级。"],
                "## 建议": [
                    "- 维持低压提醒，先支持记录连续性和稳定作息。",
                    "- 严重情况优先专业帮助而不是继续普通跟进。",
                ],
                "## 必须就医": ["- 出现明确自伤/他伤风险或严重功能崩溃时，应立即求助急救/精神专科。"],
            }
        return {
            "## 记录": result.get("sections", {}).get("## 记录", [])[:3] or ["- 暂无。"],
            "## 解读": result.get("sections", {}).get("## 解读", [])[:2] or ["- 暂无。"],
            "## 趋势": result.get("sections", {}).get("## 趋势", [])[:3] or ["- 暂无。"],
            "## 风险": result.get("sections", {}).get("## 风险", [])[:3] or ["- 暂无。"],
            "## 建议": result.get("sections", {}).get("## 建议", [])[:3] or ["- 暂无。"],
            "## 必须就医": result.get("sections", {}).get("## 必须就医", [])[:2] or ["- 暂无。"],
        }

    def _chief_sections(
        self,
        scenario: str,
        routed_roles: list[str],
        result: dict,
        context: str,
    ) -> dict[str, list[str]]:
        sections = result.get("sections", {})
        return {
            "## 记录": [
                "- 单入口：health-chief-of-staff",
                f"- 本轮场景：{scenario}",
                f"- 后台角色：{', '.join(routed_roles)}",
                f"- 会话上下文：{context}",
            ],
            "## 解读": [
                "- chief 负责接单、路由、汇总、升级与持续跟进。",
                "- specialist 只产出 brief，长期事实写回统一收敛到 health-main。",
            ],
            "## 趋势": sections.get("## 趋势", [])[:3] or ["- 暂无。"],
            "## 风险": sections.get("## 风险", [])[:3] or ["- 暂无。"],
            "## 建议": sections.get("## 建议", [])[:3] or ["- 暂无。"],
            "## 必须就医": sections.get("## 必须就医", [])[:2] or ["- 暂无。"],
        }

    def dispatch_flagship_scenario(
        self,
        scenario: str,
        payload: dict | None = None,
        context: str = "direct",
        write: bool = True,
    ) -> dict:
        payload = payload or {}
        result = self._run_flagship_workflow(scenario, payload, write=write)
        routed_roles = self.route_scenario(
            scenario,
            crisis=self._severity_is_must_seek(result.get("sections", {})),
        )
        task_id = self._base_task_id(scenario)
        policies = self.role_policies(context=context)
        chief_sources = result.get("sources_used", [])
        chief_evidence = result.get("evidence", [])
        role_brief_paths: dict[str, str] = {}
        team_task_paths: dict[str, str] = {}

        for role in routed_roles:
            role_task_id = f"{task_id}-{role}"
            task_path = self.writer.write_team_task(
                task_id=role_task_id,
                role=role,
                scenario=scenario,
                priority="high" if role == "health-safety" else "medium",
                status="completed",
                due_at=self._now().isoformat(timespec="minutes"),
                execution_mode="isolated-session" if role in {"health-safety", "health-records"} else "heartbeat",
                privacy_tier="restricted" if role in {"health-records", "health-oncology"} else "internal",
                source_refs=chief_sources,
                summary_lines=self._role_summary_lines(role, scenario, result, payload),
                next_steps=result.get("sections", {}).get("## 建议", [])[:3] or ["- 查看 brief 并按需升级。"],
            )
            brief_path = self.writer.write_role_brief(
                task_id=task_id,
                role=role,
                scenario=scenario,
                sections=self._role_sections(role, result, payload),
                sources=chief_sources,
                evidence=chief_evidence,
                recommended_writebacks=result.get("writebacks", []),
                follow_up=[task.get("title", "pending") for task in result.get("follow_up_tasks", [])],
                disclaimer=STANDARD_DISCLAIMER,
            )
            self.writer.append_dispatch_log(
                task_id=task_id,
                scenario=scenario,
                role=role,
                event="task-created",
                target=task_path,
                reason="Chief dispatched specialist task.",
                source_refs=chief_sources,
            )
            self.writer.append_dispatch_log(
                task_id=task_id,
                scenario=scenario,
                role=role,
                event="brief-generated",
                target=brief_path,
                reason="Specialist brief generated.",
                source_refs=chief_sources,
            )
            team_task_paths[role] = task_path
            role_brief_paths[role] = brief_path

        main_task_path = self.writer.write_team_task(
            task_id=f"{task_id}-health-main",
            role="health-main",
            scenario=scenario,
            priority="medium",
            status="completed",
            due_at=self._now().isoformat(timespec="minutes"),
            execution_mode="heartbeat",
            privacy_tier="internal",
            source_refs=result.get("writebacks", []),
            summary_lines=[
                "- health-main 统一承接允许的长期事实写回。",
                f"- 本轮写回数：{len(result.get('writebacks', []))}",
            ],
            next_steps=result.get("writebacks", []) or ["- 无额外写回。"],
        )
        self.writer.append_dispatch_log(
            task_id=task_id,
            scenario=scenario,
            role="health-main",
            event="writebacks-applied",
            target=main_task_path,
            reason="Main workspace writebacks completed.",
            source_refs=result.get("writebacks", []),
        )
        chief_summary_path = self.writer.write_role_brief(
            task_id=task_id,
            role="health-chief-of-staff",
            scenario=scenario,
            sections=self._chief_sections(scenario, routed_roles, result, context),
            sources=chief_sources,
            evidence=chief_evidence,
            recommended_writebacks=result.get("writebacks", []),
            follow_up=[
                f"{task.get('title', 'pending')} -> {task.get('next_step', 'pending')}"
                for task in result.get("follow_up_tasks", [])
            ],
            disclaimer=STANDARD_DISCLAIMER,
        )
        self.writer.append_dispatch_log(
            task_id=task_id,
            scenario=scenario,
            role="health-chief-of-staff",
            event="summary-generated",
            target=chief_summary_path,
            reason="Chief consolidated specialist briefs and main writebacks.",
            source_refs=chief_sources,
        )

        open_tasks = [
            f"{task.get('title', 'pending')} ({task.get('priority', 'medium')})"
            for task in result.get("follow_up_tasks", [])
        ] or ["- 当前没有新增待办。"]
        active_roles = [
            f"health-chief-of-staff ({ROLE_CADENCE['health-chief-of-staff']})",
            *[f"{role} ({ROLE_CADENCE.get(role, '0m')})" for role in routed_roles],
            f"health-main ({ROLE_CADENCE['health-main']})",
        ]
        latest_outputs = [
            f"chief-summary: {chief_summary_path}",
            f"scenario-output: {result.get('output_path')}",
            *[f"{role}: {path}" for role, path in role_brief_paths.items()],
        ]
        team_board_path = self.writer.update_team_board(
            open_tasks=open_tasks,
            active_roles=active_roles,
            latest_outputs=latest_outputs,
            generated_at=self._now().isoformat(timespec="minutes"),
        )
        self.writer.append_dispatch_log(
            task_id=task_id,
            scenario=scenario,
            role="health-chief-of-staff",
            event="team-board-updated",
            target=team_board_path,
            reason="Chief refreshed team board after scenario dispatch.",
            source_refs=chief_sources,
        )

        return {
            "task_id": task_id,
            "scenario": scenario,
            "context_policy": self.context_policy(context),
            "policies": policies,
            "packages": self.packages,
            "routed_roles": routed_roles,
            "output_path": result.get("output_path"),
            "task_board_path": result.get("task_board_path"),
            "team_board_path": team_board_path,
            "dispatch_log_path": str(self.writer.dispatch_log_path),
            "chief_summary_path": chief_summary_path,
            "role_brief_paths": role_brief_paths,
            "team_task_paths": team_task_paths,
            "main_task_path": main_task_path,
            "writebacks": result.get("writebacks", []),
            "follow_up_tasks": result.get("follow_up_tasks", []),
            "result": result,
        }

    def run_team_heartbeat(self, write: bool = True) -> dict:
        result = self.operations.run(write=write)
        team_board_path = self.writer.update_team_board(
            open_tasks=result.get("actions", []) or ["- 当前没有新增后台动作。"],
            active_roles=[
                f"health-chief-of-staff ({ROLE_CADENCE['health-chief-of-staff']})",
                f"health-main ({ROLE_CADENCE['health-main']})",
                f"health-safety ({ROLE_CADENCE['health-safety']})",
            ],
            latest_outputs=[
                f"heartbeat-report: {result.get('heartbeat_report_path') or 'pending'}",
                f"task-board: {result.get('task_board_path') or 'pending'}",
            ],
            generated_at=self._now().isoformat(timespec="minutes"),
        )
        return {
            **result,
            "team_board_path": team_board_path,
        }
