from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_approvals() -> dict[str, list[object]]:
    return {"approvals": []}
