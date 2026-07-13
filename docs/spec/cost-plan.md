# コスト計画

このプロジェクトは Cost Guard を前提に、開発・検証時のクラウド利用を最小化します。

- ローカル開発では BigQuery Emulator、filesystem storage fallback、Ollama を優先します。
- Cloud Run は原則 `min_instances=0` とし、常時起動コストを避けます。
- AI モデル呼び出しは明示的な検証時に限定し、評価・リリース判定はスキーマ検証済み出力を使います。
- 本番相当のデプロイ、Terraform apply、共有インフラの変更は人間の承認後に実施します。

詳細な上限や運用ルールは `.ai/overlays/COST_GUARD.project.md` を参照してください。
