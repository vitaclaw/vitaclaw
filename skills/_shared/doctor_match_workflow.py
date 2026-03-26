#!/usr/bin/env python3
"""Productized public-doctor matching workflow for VitaClaw."""

from __future__ import annotations

from datetime import datetime, timedelta

from .doctor_matching import DoctorFitFinder
from .health_scenario_runtime import HealthScenarioRuntime


class DoctorMatchWorkflow:
    """Route departments, rank doctors, and write public doctor-match outputs."""

    def __init__(
        self,
        workspace_root: str | None = None,
        memory_dir: str | None = None,
        now_fn=None,
        fit_finder: DoctorFitFinder | None = None,
    ):
        self._now_fn = now_fn or datetime.now
        self.runtime = HealthScenarioRuntime(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            now_fn=self._now_fn,
        )
        self.writer = self.runtime.writer
        self.fit_finder = fit_finder or DoctorFitFinder()

    def _now(self) -> datetime:
        return self._now_fn()

    def _today(self) -> str:
        return self._now().date().isoformat()

    def _candidate_label(self, ranked: dict) -> str:
        doctor = ranked["doctor"]
        return (
            f"{doctor.get('name', 'Unknown')} | {doctor.get('department', 'Unknown department')} | "
            f"{doctor.get('hospital', 'Unknown hospital')} | score {ranked['score']}"
        )

    def match_doctors(
        self,
        patient_profile: dict,
        doctors: list[dict],
        top_n: int = 5,
        pubmed_mode: str = "auto",
        write: bool = True,
    ) -> dict:
        date_str = self._today()
        result = self.fit_finder.rank(
            patient_profile=patient_profile,
            doctors=doctors,
            top_n=top_n,
            pubmed_mode=pubmed_mode,
        )
        route_result = result["route_result"]
        ranked = result["ranked_doctors"]
        shortlist = ranked[: min(3, len(ranked))]

        preferred_departments = [item["department"] for item in route_result.get("recommendations", [])]
        sources = []
        evidence = []
        for item in route_result.get("recommendations", []):
            evidence.append(
                f"科室路由：{item['department']}（score {item['score']}），"
                f"依据 {', '.join(item.get('matched_terms') or ['综合背景'])}"
            )

        for ranked_item in shortlist:
            doctor = ranked_item["doctor"]
            profile = ranked_item["evidence_profile"]
            url = doctor.get("official_profile_url") or doctor.get("profile_url")
            if url:
                sources.append(str(url))
            for ref in profile.get("source_refs", []):
                sources.append(str(ref))
            breakdown = ranked_item["score_breakdown"]
            evidence.append(
                f"{doctor.get('name', 'Unknown')}：department {breakdown['department']}, "
                f"topic {breakdown['topic']}, location {breakdown['location']}, "
                f"continuity {breakdown['continuity']}, evidence {breakdown['evidence']}."
            )

        sources = sorted(set(sources))

        care_team_path = self.writer.update_care_team(
            date_str=date_str,
            preferred_departments=preferred_departments,
            shortlist=[
                {
                    "doctor": item["doctor"],
                    "score": item["score"],
                    "reasons": item["reasons"],
                    "concerns": item["concerns"],
                    "evidence_signal": item["evidence_profile"].get("evidence_signal"),
                }
                for item in shortlist
            ],
            city=patient_profile.get("city"),
            district=patient_profile.get("district"),
            summary="; ".join(self._candidate_label(item) for item in shortlist) or "pending",
            booking_strategy="先联系 top 1；若号源紧张，平行保留 top 2 / top 3 作为备选。",
        )

        writebacks = [care_team_path]
        next_due = (self._now() + timedelta(days=2)).replace(hour=20, minute=0, second=0, microsecond=0)
        writebacks.append(
            self.writer.upsert_behavior_plan(
                plan_id=f"doctor-match-followup-{date_str}",
                scenario="doctor-fit-finder",
                title="确认首选医生并准备首诊问题单",
                cadence="event",
                due_at=next_due.isoformat(timespec="minutes"),
                topic="care-team",
                risk_policy="focus-closely",
                consequence="如果不尽快确认医生和问题单，体检异常 / 慢病随访会继续拖延。",
                next_step="在 shortlist 中选出首选和备选医生，并准备 3-5 个要问的问题。",
                notes="由 doctor-fit-finder 自动生成。",
            )
        )

        risk_lines = []
        if not shortlist:
            risk_lines.append("当前公开候选医生不足，建议先扩大医院或城市范围。")
        for ranked_item in shortlist:
            if ranked_item["concerns"]:
                risk_lines.append(
                    f"{ranked_item['doctor'].get('name', 'Unknown')}：{'；'.join(ranked_item['concerns'][:2])}"
                )

        recommendation_lines = []
        for index, ranked_item in enumerate(shortlist, start=1):
            doctor = ranked_item["doctor"]
            reasons = "；".join(ranked_item["reasons"][:3]) or "与当前问题较贴合"
            recommendation_lines.append(
                f"Top {index}：{doctor.get('name', 'Unknown')}（{doctor.get('hospital', 'Unknown hospital')} / "
                f"{doctor.get('department', 'Unknown department')}），推荐理由：{reasons}"
            )

        must_seek = route_result.get("must_seek_care") or [
            "当前未触发必须就医级别红旗；若后续出现胸痛、明显呼吸困难或其他急性危险症状，应切换到急症分诊流程。"
        ]

        sections = {
            "## 记录": [
                f"城市 / 区域：{patient_profile.get('city', 'pending')} / {patient_profile.get('district', 'pending')}",
                f"主要问题：{'; '.join(patient_profile.get('conditions', []) or ['pending'])}",
                f"候选医生数：{len(doctors)}",
                f"推荐科室：{'; '.join(preferred_departments) or 'pending'}",
            ],
            "## 解读": [
                "先用公开健康信息把问题路由到合适科室，再对医生做适配度匹配。",
                "PubMed 论文只是加分项，不会压过城市可及性、长期随访适配度和公开简介匹配度。",
                "输出基于公开官网 / 公开论文，不等于对医生能力做绝对排名。",
            ],
            "## 趋势": [
                "如果你希望长期管理高血压、糖前期或体检异常，优先选择可连续随访的医生，而不是只看一次性权威度。",
                "若近两个月内指标持续波动，优先考虑能读懂连续记录并愿意长期跟进的门诊。",
            ],
            "## 风险": risk_lines or ["当前 shortlist 没有额外风险提示。"],
            "## 建议": recommendation_lines
            + [
                "先联系 top 1；若挂号困难，同时保留 top 2 / top 3 作为备选。",
                "预约前准备最近 2-4 周的关键指标、药物清单、最想解决的 3 个问题。",
            ],
            "## 必须就医": must_seek,
        }

        follow_up_tasks = [
            self.runtime.build_task(
                title="确认首选医生与备选医生",
                reason="医生匹配报告已经形成 shortlist，但还没有转成真实就诊动作。",
                next_step="在 48 小时内确认 1 个首选和 1-2 个备选医生。",
                follow_up="若 48 小时后仍未确认，我会继续跟进。",
                priority="medium",
                topic="care-team",
                source_refs=[care_team_path],
                threshold="Doctor shortlist generated but not yet actioned",
                dedupe_key="doctor-match-shortlist-followup",
            )
        ]
        if preferred_departments:
            follow_up_tasks.append(
                self.runtime.build_task(
                    title="准备首诊问题单",
                    reason=(
                        f"推荐科室已经明确为 {' / '.join(preferred_departments[:2])}，"
                        "下一步应该把问题收敛成医生可快速理解的清单。"
                    ),
                    next_step="列出 3-5 个最重要的问题，并带上关键体检或慢病趋势。",
                    follow_up="若 2 天后仍未准备，我会再次提醒。",
                    priority="low",
                    topic="care-team",
                    source_refs=[care_team_path],
                    dedupe_key="doctor-match-question-list",
                )
            )

        return self.runtime.persist_result(
            filename=f"doctor-match-{date_str}.md",
            title="Doctor Fit Finder",
            date_str=date_str,
            sections=sections,
            sources=sources or ["公开医院主页 / 医生简介 / PubMed（如可用）"],
            evidence=evidence or ["当前主要依据用户条件、地点和公开医生资料进行匹配。"],
            scenario="doctor-fit-finder",
            file_type="doctor-match",
            summary=f"{date_str} 医生匹配与就医选择建议",
            alerts=[item["department"] for item in route_result.get("recommendations", [])[:2]],
            follow_up_tasks=follow_up_tasks,
            writebacks=sorted(set(writebacks)),
            audit_reason="公开医生匹配与就医选择写回",
        )
