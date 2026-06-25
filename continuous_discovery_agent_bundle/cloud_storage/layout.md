# Cloud Storage Layout

推奨bucket: `gs://cd-agent-knowledge/`

```text
gs://cd-agent-knowledge/
  tenants/
    {company_id}/
      raw/
        onboarding/
          fiscal_year=2026/
            initial_answers/
            followup_answers/
            attachments/
        external/
          fiscal_year=2026/
            competitor/
            news/
            website_snapshots/

      wiki/
        current/
          manifest.json
          company_profile.md
          kpi_definitions.yaml
          focus_metrics.yaml
          research_policy.yaml
          open_questions.yaml
          glossary.md

        versions/
          2026-06-25T100000Z/
            manifest.json
            company_profile.md
            kpi_definitions.yaml
            focus_metrics.yaml
            research_policy.yaml
            open_questions.yaml
            glossary.md

      derived/
        fiscal_year=2026/
          onboarding_summary.json
          kpi_candidates.json
          focus_metric_candidates.json
          followup_questions.json
          company_profile_snapshot.json

      migrations/
        bigquery/
          schema_version.txt
          applied_migrations.json
```

## 運用ルール

- rawは原則不変。上書きせず追記/別ファイル化する
- wiki/current更新前にwiki/versions/{timestamp}へコピーする
- manifest.jsonにsource_files/source_refsを必ず記録する
- Object Versioningを有効化する
- Lifecycle Managementで古い非現行バージョンを削除/Archiveする
