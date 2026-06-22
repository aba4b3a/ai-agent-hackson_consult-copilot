import json
import logging
from config import AppConfig
from repository import KPIRepository

# Google ADK / LiteLLM imports
from google.adk.agents import Agent
from google.adk.tools import function_tool
from google.adk.models import LiteLLMAdapter

logger = logging.getLogger(__name__)

class KPIConsultantAgentService:
    """KPI策定およびDB設計を行うエージェントサービス"""

    def __init__(self, config: AppConfig, repository: KPIRepository):
        self.config = config
        self.repository = repository
        self.agent = self._build_agent()

    def _build_agent(self) -> Agent:
        """エージェントとツールを初期化して返す"""
        
        # モデルの初期化 (LiteLLMを利用して環境ごとに切り替え)
        llm_model = LiteLLMAdapter(
            model=self.config.current_model_id,
            api_base=self.config.current_api_base
        )

        # ツールの定義 (インスタンス変数 repository を利用するためクロージャとして定義)
        @function_tool
        def setup_kpi_database(company_id: str, kpis: list, data_schema: dict) -> str:
            """
            決定したKPIと、計測用のデータスキーマ（JSON）をデータベースに登録するツール。
            """
            success = self.repository.save_kpi_and_schema(company_id, kpis, data_schema)
            if success:
                return f"企業 {company_id} のデータベース設定（スキーマ登録）が正常に完了しました。"
            else:
                return f"企業 {company_id} のデータベース設定に失敗しました。"

        # ADKエージェントの構成
        return Agent(
            name="SME_KPI_Consultant_Agent",
            model=llm_model,
            instruction="""
            あなたは優秀な中小企業向けコンサルティングエージェントです。
            与えられた初期情報（業種、売上、課題など）を分析し、自律的に業務を遂行してください。
            
            1. この企業が追うべき「KPI」と「重要管理項目」を3つ設定する。
            2. それらを毎月計測するために収集すべき「データ項目名と型」のJSONスキーマを設計する。
            3. 設計が完了したら、`setup_kpi_database` ツールを必ず呼び出してシステムに登録する。
            """,
            tools=[setup_kpi_database]
        )

    def execute_consulting(self, company_id: str, industry: str, sales: int, issues: str) -> str:
        """外部から呼び出される実行メソッド"""
        prompt = f"初期情報 -> 企業ID:{company_id}, 業種:{industry}, 年商:{sales}万円, 課題:{issues}"
        
        logger.info(f"[{self.config.env}環境] モデル {self.config.current_model_id} で推論を開始します。")
        
        # ADKによるエージェント実行
        response = self.agent.run(prompt)
        return response.text