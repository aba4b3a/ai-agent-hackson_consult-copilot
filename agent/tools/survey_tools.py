from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def generate_common_initial_survey(company_id: str) -> dict:
    questions = [
        {
            "question_id": f"{company_id}_q001",
            "company_id": company_id,
            "question_text": "主な商品・サービスは何ですか？売上が大きい順に教えてください。",
            "target_role": "owner",
            "answer_type": "text",
            "frequency": "ad_hoc",
            "qualitative_intent": "事業内容と価値提供の把握",
            "quantitative_intent": "売上構成の把握",
            "related_node_types": ["Product", "Service"],
            "related_edge_types": ["IMPACTS"],
        },
        {
            "question_id": f"{company_id}_q002",
            "company_id": company_id,
            "question_text": "売上が増減する主な要因を最大3つ選び、可能なら影響度を1〜5で付けてください。",
            "target_role": "owner",
            "answer_type": "json",
            "frequency": "ad_hoc",
            "qualitative_intent": "経営者の売上ドライバー仮説を把握",
            "quantitative_intent": "影響度スコアを取得",
            "related_node_types": ["KPI", "Process", "Signal"],
            "related_edge_types": ["IMPACTS"],
        },
        {
            "question_id": f"{company_id}_q003",
            "company_id": company_id,
            "question_text": "社内で『この人に聞かないと分からない』業務は何ですか？該当者と理由も教えてください。",
            "target_role": "manager",
            "answer_type": "text",
            "frequency": "ad_hoc",
            "qualitative_intent": "属人化・暗黙知の所在を把握",
            "quantitative_intent": "属人業務数を把握",
            "related_node_types": ["Person", "Process", "TacitKnowledge"],
            "related_edge_types": ["KNOWS", "PERFORMS", "DEPENDS_ON"],
        },
        {
            "question_id": f"{company_id}_q004",
            "company_id": company_id,
            "question_text": "新人とベテランで判断が分かれる場面はありますか？頻度も教えてください。",
            "target_role": "manager",
            "answer_type": "text",
            "frequency": "ad_hoc",
            "qualitative_intent": "熟練者判断の抽出",
            "quantitative_intent": "発生頻度の把握",
            "related_node_types": ["Skill", "Process", "TacitKnowledge"],
            "related_edge_types": ["DEPENDS_ON", "TRANSFERS_TO"],
        },
        {
            "question_id": f"{company_id}_q005",
            "company_id": company_id,
            "question_text": "顧客が喜ぶ対応にはどのような共通点がありますか？最近の具体例も教えてください。",
            "target_role": "staff",
            "answer_type": "text",
            "frequency": "ad_hoc",
            "qualitative_intent": "顧客満足につながる暗黙知を抽出",
            "quantitative_intent": "事例数や発生頻度を把握",
            "related_node_types": ["CustomerSegment", "TacitKnowledge", "Skill"],
            "related_edge_types": ["INDICATES", "IMPACTS"],
        },
        {
            "question_id": f"{company_id}_q006",
            "company_id": company_id,
            "question_text": "顧客が離れる前、失注する前、クレームになる前に見られる兆候はありますか？",
            "target_role": "staff",
            "answer_type": "text",
            "frequency": "ad_hoc",
            "qualitative_intent": "リスク予兆を把握",
            "quantitative_intent": "兆候の発生頻度を把握",
            "related_node_types": ["Signal", "Risk", "CustomerSegment"],
            "related_edge_types": ["INDICATES"],
        },
        {
            "question_id": f"{company_id}_q007",
            "company_id": company_id,
            "question_text": "最近1か月で、いつもと違う問い合わせ・要望・不満はありましたか？件数感も教えてください。",
            "target_role": "manager",
            "answer_type": "text",
            "frequency": "monthly",
            "qualitative_intent": "顧客変化の兆候を抽出",
            "quantitative_intent": "件数・増減を把握",
            "related_node_types": ["Signal", "CustomerSegment", "Risk"],
            "related_edge_types": ["INDICATES", "RELATED_TO"],
        },
        {
            "question_id": f"{company_id}_q008",
            "company_id": company_id,
            "question_text": "品質・売上・顧客満足に大きく影響するが、現在記録していない情報は何ですか？",
            "target_role": "owner",
            "answer_type": "text",
            "frequency": "ad_hoc",
            "qualitative_intent": "新規管理項目候補を抽出",
            "quantitative_intent": "管理優先度を把握",
            "related_node_types": ["KPI", "TacitKnowledge", "Question"],
            "related_edge_types": ["MEASURES", "RELATED_TO"],
        },
    ]
    return {"company_id": company_id, "survey_type": "common_initial_survey", "questions": questions}


def generate_response_id() -> str:
    return f"resp_{uuid4().hex}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
