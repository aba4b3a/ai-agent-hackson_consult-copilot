from fastapi import FastAPI

from app.api.v1 import approvals, costs, discovery, health, quality_runs, webhooks

app = FastAPI(
    title="Continuous Discovery Agent Backend API",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(discovery.router, prefix="/api", tags=["continuous-discovery"])
app.include_router(quality_runs.router, prefix="/quality-runs", tags=["quality-runs"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(costs.router, prefix="/costs", tags=["costs"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
