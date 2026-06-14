<!-- Generated from .ai-common. Do not edit directly. -->

# 概要

<!-- 1 段落。何を変更し、なぜ変更したか。 -->

## スコープ

- 対象レイヤ: front / back / agent / infra / docs
- 関連 Issue / チケット:
- フェーズ: [ ] 仕様駆動（Requirements/Design/Task）  [ ] 機能改修（Artifact パイプライン）

## 関連 Artifact（機能改修フェーズの場合）

<!-- 直前 Artifact へのリンクを必ず入れる（トレーサビリティ） -->

- User Feedback:
- Issue / Observation:
- Improvement Plan:
- （この PR が Patch / Diff Artifact になります）

## 品質エビデンス

- テスト:
- UI レビュー（Playwright）:
- AI 品質評価（schema-valid）:
- セキュリティレビュー:
- Cost Guard 判定:

## リリースゲート

- 判定: allow / needs_approval / block
- ロールバック手順:
- 必要な承認者:

## 非交渉ルール確認

- [ ] この diff に secret / token / 公開不可の ID / PII を含めていない
- [ ] 本番 deploy / IAM 更新 / Secret Manager の値読取 / `terraform apply` / 破壊的削除を行っていない
- [ ] Cost Guard を確認し、想定追加コストは USD 300 上限内
- [ ] 意思決定に使う AI 出力は schema-valid
- [ ] diff スコープは依頼された変更に限定（drive-by refactor なし）
