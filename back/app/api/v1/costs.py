from fastapi import APIRouter

router = APIRouter()


@router.get("/estimate")
def estimate_cost() -> dict[str, object]:
    return {"currency": "USD", "estimated_cost": 0.42}
