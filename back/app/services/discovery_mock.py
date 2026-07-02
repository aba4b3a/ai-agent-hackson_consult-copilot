from __future__ import annotations

from datetime import UTC, datetime
from itertools import count

from app.schemas.discovery import (
    CopilotAnswer,
    DiscoverySignal,
    EvidenceResult,
    GraphEdge,
    GraphNode,
    GraphSlice,
    Hypothesis,
    Observation,
    ReportForm,
    ReportFormCreate,
    ReportSubmissionCreate,
    Source,
    VoiceIntakeCreate,
    WeeklyReport,
    Workspace,
    WorkspaceCreate,
)
from app.schemas.extraction import ExtractedEntity, ExtractedRelationship, ExtractionResult
from app.services import agent_client


class DiscoveryMockRepository:
    def __init__(self) -> None:
        self._ids = count(1)
        self.workspaces: dict[str, Workspace] = {}
        self.forms: dict[str, ReportForm] = {}
        self.sources: dict[str, Source] = {}
        self.observations: dict[str, Observation] = {}
        self.hypotheses: dict[str, Hypothesis] = {}
        self.signals: dict[str, DiscoverySignal] = {}
        # Entities and relationships are persisted from extraction output but not
        # yet wired into graph_slice (kept derived from observations for now).
        self.entities: dict[str, dict[str, ExtractedEntity]] = {}
        self.relationships: dict[str, list[ExtractedRelationship]] = {}
        self._seed()

    def _next_id(self, prefix: str) -> str:
        return f"{prefix}_{next(self._ids):03d}"

    def _seed(self) -> None:
        workspace = self.create_workspace(
            WorkspaceCreate(
                workspace_name="みどり薬局チェーン",
                business_description="地域密着型の調剤薬局。処方箋受付、在宅訪問、健康相談を提供。",
                products=["処方箋受付", "在宅訪問", "健康相談"],
                customer_segments=["高齢者", "子育て世帯", "慢性疾患患者"],
                competitors=["駅前ドラッグ", "オンライン服薬指導サービス"],
                known_issues=["待ち時間", "価格不安", "在庫切れ"],
                kpis=["再来店率", "待ち時間", "処方箋受付数"],
                observation_topics=["価格比較", "待ち時間", "オンライン服薬指導への反応"],
            )
        )
        form = self.create_report_form(
            ReportFormCreate(
                workspace_id=workspace.workspace_id,
                focus_topics=["価格比較", "待ち時間"],
            )
        )
        self.submit_report(
            ReportSubmissionCreate(
                form_id=form.form_id,
                submitted_by_role="店舗スタッフ",
                free_text="高齢のお客様から、駅前ドラッグのほうが待ち時間が短いと言われた。薬の在庫確認も早いらしい。",
                customer_type="高齢者",
                product="処方箋受付",
                issue_category="待ち時間",
                competitor="駅前ドラッグ",
                kpi_note="夕方の待ち時間が伸びた",
            )
        )
        self.submit_voice(
            VoiceIntakeCreate(
                workspace_id=workspace.workspace_id,
                submitted_by_role="薬剤師",
                transcript="今日は子育て世帯からオンライン服薬指導についての質問が増えました。通院後に店舗へ寄る時間が取りづらいそうです。",
            )
        )

    def create_workspace(self, payload: WorkspaceCreate) -> Workspace:
        workspace = Workspace(workspace_id=self._next_id("ws"), **payload.model_dump())
        self.workspaces[workspace.workspace_id] = workspace
        self._create_initial_signal(workspace)
        return workspace

    def _create_initial_signal(self, workspace: Workspace) -> None:
        signal = DiscoverySignal(
            signal_id=self._next_id("sig"),
            workspace_id=workspace.workspace_id,
            signal_type="weekly_increase",
            metric_name="competitor_wait_time_mentions",
            current_value=11,
            baseline_value=5,
            change_rate=1.2,
            related_entities=["待ち時間", "駅前ドラッグ"],
            evidence_count=4,
            severity="warning",
        )
        self.signals[signal.signal_id] = signal

    def create_report_form(self, payload: ReportFormCreate) -> ReportForm:
        form_id = self._next_id("form")
        topics = payload.focus_topics or ["顧客の変化", "競合名", "業務影響"]
        questions = [
            "今日、顧客から普段と違う反応や相談はありましたか。",
            f"{'、'.join(topics)}に関係する具体的な発言はありましたか。",
            "競合名、商品、顧客層、KPIへの影響が分かれば記録してください。",
        ]
        form = ReportForm(
            form_id=form_id,
            workspace_id=payload.workspace_id,
            url=f"/intake/{form_id}",
            target_role=payload.target_role,
            focus_topics=topics,
            due_date=payload.due_date,
            questions=questions,
        )
        self.forms[form_id] = form
        return form

    def get_report_form(self, form_id: str) -> ReportForm | None:
        return self.forms.get(form_id)

    def submit_report(self, payload: ReportSubmissionCreate) -> Source:
        form = self.forms[payload.form_id]
        body = "\n".join(
            [
                payload.free_text,
                f"customer_type={payload.customer_type}",
                f"product={payload.product}",
                f"issue_category={payload.issue_category}",
                f"competitor={payload.competitor or 'unknown'}",
                f"kpi_note={payload.kpi_note or 'unknown'}",
            ]
        )
        return self._create_source(
            workspace_id=form.workspace_id,
            source_type="daily_report",
            title=f"Daily report {datetime.now(UTC).date().isoformat()}",
            body=body,
        )

    def generate_followups(self, workspace_id: str, answers: list[str]) -> list[str]:
        workspace = self.workspaces[workspace_id]
        return agent_client.generate_followups(workspace, answers)

    def submit_voice(self, payload: VoiceIntakeCreate) -> Source:
        return self._create_source(
            workspace_id=payload.workspace_id,
            source_type="voice_transcript",
            title=f"Voice transcript {datetime.now(UTC).date().isoformat()}",
            body=payload.transcript,
        )

    def _create_source(self, workspace_id: str, source_type: str, title: str, body: str) -> Source:
        source_id = self._next_id("src")
        source = Source(
            source_id=source_id,
            workspace_id=workspace_id,
            source_type=source_type,
            title=title,
            body=body,
            processing_status="extracted",
            source_uri=f"gs://continuous-discovery-local/raw/{workspace_id}/{source_id}.txt",
        )
        self.sources[source_id] = source
        self._extract_knowledge(source)
        return source

    def _extract_knowledge(self, source: Source) -> None:
        workspace = self.workspaces[source.workspace_id]
        result = agent_client.extract_knowledge(source.source_type, source.body, workspace)

        created_observation_ids: list[str] = []
        for extracted in result.observations:
            observation = Observation(
                observation_id=self._next_id("obs"),
                workspace_id=source.workspace_id,
                source_id=source.source_id,
                source_type=source.source_type,
                summary=extracted.summary,
                quote=extracted.quote,
                fact_or_hypothesis=extracted.fact_or_hypothesis,
                confidence=extracted.confidence,
                related_entities=extracted.related_entities,
                evidence_uri=source.source_uri,
            )
            self.observations[observation.observation_id] = observation
            created_observation_ids.append(observation.observation_id)

        for extracted_hypothesis in result.hypotheses:
            hypothesis = Hypothesis(
                hypothesis_id=self._next_id("hyp"),
                workspace_id=source.workspace_id,
                statement=extracted_hypothesis.statement,
                status="observing",
                confidence=extracted_hypothesis.confidence,
                supporting_observation_ids=list(created_observation_ids),
                recommended_observations=extracted_hypothesis.recommended_observations,
            )
            self.hypotheses[hypothesis.hypothesis_id] = hypothesis

        self._store_graph_knowledge(source.workspace_id, result)

    def _store_graph_knowledge(self, workspace_id: str, result: ExtractionResult) -> None:
        # Persist entities/relationships for later graph use. Deduped by name.
        entity_store = self.entities.setdefault(workspace_id, {})
        for entity in result.entities:
            existing = entity_store.get(entity.name)
            if existing is None:
                entity_store[entity.name] = entity
                continue
            for alias in entity.aliases:
                if alias not in existing.aliases:
                    existing.aliases.append(alias)
        self.relationships.setdefault(workspace_id, []).extend(result.relationships)

    def list_workspaces(self) -> list[Workspace]:
        return list(self.workspaces.values())

    def dashboard(self, workspace_id: str) -> dict[str, object]:
        observations = [o for o in self.observations.values() if o.workspace_id == workspace_id]
        hypotheses = [h for h in self.hypotheses.values() if h.workspace_id == workspace_id]
        signals = [s for s in self.signals.values() if s.workspace_id == workspace_id]
        sources = [s for s in self.sources.values() if s.workspace_id == workspace_id]
        return {
            "workspace": self.workspaces[workspace_id],
            "metrics": {
                "sources_ingested": len(sources),
                "observations_extracted": len(observations),
                "entities_formed": len({e for o in observations for e in o.related_entities}),
                "hypotheses_under_observation": len(hypotheses),
                "evidence_coverage": 0.86,
            },
            "signals": signals,
            "observations": observations[-5:],
            "hypotheses": hypotheses[-5:],
        }

    def search_evidence(self, workspace_id: str, query: str = "") -> list[EvidenceResult]:
        query_lower = query.lower()
        results: list[EvidenceResult] = []
        for observation in self.observations.values():
            if observation.workspace_id != workspace_id:
                continue
            text = f"{observation.summary} {observation.quote} {' '.join(observation.related_entities)}"
            if query_lower and query_lower not in text.lower():
                continue
            source = self.sources[observation.source_id]
            results.append(
                EvidenceResult(
                    source_id=source.source_id,
                    observation_id=observation.observation_id,
                    title=source.title,
                    source_type=source.source_type,
                    snippet=observation.quote,
                    tags=observation.related_entities,
                    confidence=observation.confidence,
                    evidence_uri=observation.evidence_uri,
                )
            )
        return results

    def graph_slice(self, workspace_id: str) -> GraphSlice:
        observations = [o for o in self.observations.values() if o.workspace_id == workspace_id]
        nodes = {
            "workspace": GraphNode(
                id="workspace",
                type="Workspace",
                label=self.workspaces[workspace_id].workspace_name,
                summary="初期設定と観察データの中心ノード",
            )
        }
        edges: list[GraphEdge] = []
        for observation in observations:
            obs_id = observation.observation_id
            nodes[obs_id] = GraphNode(
                id=obs_id,
                type="Observation",
                label=observation.summary,
                summary=observation.quote,
            )
            edges.append(
                GraphEdge(
                    source="workspace",
                    target=obs_id,
                    type="MENTIONS",
                    evidence_count=1,
                    fact_or_hypothesis="fact",
                )
            )
            for entity in observation.related_entities:
                entity_id = f"ent_{entity}"
                nodes[entity_id] = GraphNode(
                    id=entity_id,
                    type="Entity",
                    label=entity,
                    summary="観察から形成された軽量エンティティ",
                )
                edges.append(
                    GraphEdge(
                        source=obs_id,
                        target=entity_id,
                        type="RELATES_TO",
                        evidence_count=1,
                        fact_or_hypothesis="fact",
                    )
                )
        for hypothesis in self.hypotheses.values():
            if hypothesis.workspace_id != workspace_id:
                continue
            nodes[hypothesis.hypothesis_id] = GraphNode(
                id=hypothesis.hypothesis_id,
                type="Hypothesis",
                label=hypothesis.statement,
                summary="観察中の仮説",
            )
            for obs_id in hypothesis.supporting_observation_ids:
                edges.append(
                    GraphEdge(
                        source=obs_id,
                        target=hypothesis.hypothesis_id,
                        type="SUPPORTS",
                        evidence_count=1,
                        fact_or_hypothesis="hypothesis",
                    )
                )
        return GraphSlice(
            nodes=list(nodes.values()),
            edges=edges[:50],
            summary="観察事実を中心に、関連エンティティと観察中の仮説を分離して表示しています。",
        )

    def weekly_report(self, workspace_id: str) -> WeeklyReport:
        evidence = self.search_evidence(workspace_id)
        observations = [o.summary for o in self.observations.values() if o.workspace_id == workspace_id]
        hypotheses = [h.statement for h in self.hypotheses.values() if h.workspace_id == workspace_id]
        return WeeklyReport(
            report_id="rep_latest",
            workspace_id=workspace_id,
            period="latest_week",
            summary="待ち時間と競合利便性に関する言及が増えています。因果は未確定のため、次週も比較理由を重点観察します。",
            observed_facts=observations,
            hypotheses=hypotheses,
            evidence=evidence[:3],
            recommended_observations=[
                "競合名が出た発話で、価格・待ち時間・在庫のどれが理由か確認する",
                "子育て世帯のオンライン服薬指導ニーズを日報で分けて記録する",
            ],
            limitations=[
                "デモ用 mock mode のため、BigQuery Graph と Elasticsearch はローカルデータで代替しています。",
                "仮説は観察中であり、確定した事業原因として扱いません。",
            ],
        )

    def ask_copilot(self, workspace_id: str, question: str) -> CopilotAnswer:
        workspace = self.workspaces[workspace_id]
        evidence = self.search_evidence(workspace_id, "")
        facts = [o.summary for o in self.observations.values() if o.workspace_id == workspace_id]
        hypotheses = [
            h.statement for h in self.hypotheses.values() if h.workspace_id == workspace_id
        ]

        # Retrieval (in-memory) + agent-generated grounded answer. Evidence
        # references are attached here, not fabricated by the model (R16).
        payload = agent_client.answer_copilot(
            question=question,
            facts=facts,
            hypotheses=hypotheses,
            evidence=[e.snippet for e in evidence[:5]],
            workspace=workspace,
        )
        if payload is not None:
            return CopilotAnswer(
                answer=payload.answer,
                observed_facts=payload.observed_facts,
                hypotheses=payload.hypotheses,
                evidence=evidence[:3],
                recommended_observations=payload.recommended_observations,
            )

        # Fallback: templated answer when agent extraction is off/unreachable.
        report = self.weekly_report(workspace_id)
        return CopilotAnswer(
            answer=(
                f"質問「{question}」に対して、現時点の観察事実では待ち時間と競合比較の言及が確認できます。"
                "原因は未確定なので、競合利便性が影響している可能性を仮説として扱い、追加観察で検証してください。"
            ),
            observed_facts=report.observed_facts,
            hypotheses=report.hypotheses,
            evidence=evidence[:3],
            recommended_observations=report.recommended_observations,
        )


discovery_repository = DiscoveryMockRepository()
