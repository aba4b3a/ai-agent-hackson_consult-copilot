<!-- Generated from .ai-common. Do not edit directly. -->

# Budget Policy

Default Google Cloud budget target: USD 300 maximum project spend.

Project overlays may override thresholds in `.ai/overlays/COST_GUARD.project.md`.

Watch for:

- Cloud Run min instances and CPU allocation
- Cloud Build frequency and machine type
- Logging volume
- GCS retention and artifact growth
- Firestore reads and writes
- Model calls, retries, and context size
- Scheduled jobs and background loops
