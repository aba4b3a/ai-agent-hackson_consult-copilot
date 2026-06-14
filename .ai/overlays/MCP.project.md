# Project MCP Overlay（プロジェクト用 MCP 上書き）

`.ai-common/standards/MCP_POLICY.base.md` の **後ろに** 適用されます。ドキュメント化されているが base では非アクティブな MCP サーバーを、**承認者** と **監査先** を明記したうえで有効化します。ベースの禁止事項を **緩めることはできません**。

## このプロジェクトで有効化するサーバー

<!-- 例:
- gcs-artifacts:
    buckets: ["my-project-playwright-artifacts"]
    approver: release-manager
    audit: cloud-logging://my-project/mcp-audit
-->

## スコープの絞り込み

<!-- 例:
- playwright:
    approved-preview-hosts:
      - "localhost:3000"
      - "*.web.app プレビュースラッグのみ"
-->

## 常時禁止（base と同じ。緩めない）

- secret 値の読取（あらゆる経路で）
- IAM 変更
- 本番 deploy
- `terraform apply`
- 破壊的削除
