from fastapi import FastAPI

from app.api.v1 import approvals, costs, health, quality_runs, webhooks

app = FastAPI(
    title="AI QualityOps Backend API",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(quality_runs.router, prefix="/quality-runs", tags=["quality-runs"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(costs.router, prefix="/costs", tags=["costs"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
