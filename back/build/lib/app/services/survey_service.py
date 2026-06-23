from app.schemas.survey import SurveyQuestion


class SurveyService:
    def generate_common_initial_survey(self, company_id: str) -> dict:
        raw_questions = [
            ('q001', '主な商品・サービスは何ですか？売上が大きい順に教えてください。可能なら割合も教えてください。', 'owner', 'text', 'ad_hoc', 'Product,Service,KPI', 'IMPACTS,MEASURES'),
            ('q002', '売上が増減する主な要因を最大3つ挙げ、それぞれ影響度を1〜5で付けてください。', 'owner', 'json', 'ad_hoc', 'KPI,Signal,Process', 'IMPACTS'),
            ('q003', '社内で「この人に聞かないと分からない」業務は何ですか？該当者、業務、理由、発生頻度を教えてください。', 'manager', 'text', 'ad_hoc', 'Person,Process,TacitKnowledge', 'KNOWS,PERFORMS,DEPENDS_ON'),
            ('q004', '新人とベテランで判断が分かれる場面はありますか？具体例と月あたりの頻度を教えてください。', 'manager', 'text', 'ad_hoc', 'Skill,Process,TacitKnowledge', 'DEPENDS_ON,TRANSFERS_TO'),
            ('q005', '顧客が喜ぶ対応にはどのような共通点がありますか？最近の具体例と、おおよその発生件数も教えてください。', 'staff', 'text', 'weekly', 'CustomerSegment,TacitKnowledge,Skill', 'INDICATES,IMPACTS'),
            ('q006', '顧客が離れる前、失注する前、クレームになる前に見られる兆候はありますか？件数感も教えてください。', 'staff', 'text', 'weekly', 'Signal,Risk,CustomerSegment', 'INDICATES'),
            ('q007', '最近1か月で、いつもと違う問い合わせ・要望・不満はありましたか？種類と件数感を教えてください。', 'manager', 'text', 'monthly', 'Signal,CustomerSegment,Risk', 'INDICATES,RELATED_TO'),
            ('q008', '品質・売上・顧客満足に大きく影響するが、現在記録していない情報は何ですか？重要度を1〜5で付けてください。', 'owner', 'text', 'ad_hoc', 'KPI,TacitKnowledge,Question', 'MEASURES,RELATED_TO'),
        ]
        questions = []
        for suffix, text, role, answer_type, freq, node_types, edge_types in raw_questions:
            questions.append(SurveyQuestion(
                question_id=f'{company_id}_{suffix}', company_id=company_id, question_text=text,
                target_role=role, answer_type=answer_type, frequency=freq,
                qualitative_intent='暗黙知・業務文脈の把握', quantitative_intent='件数・頻度・影響度の把握',
                related_node_types=node_types.split(','), related_edge_types=edge_types.split(','),
            ).model_dump())
        return {'company_id': company_id, 'survey_type': 'common_initial_survey', 'questions': questions}


survey_service = SurveyService()
