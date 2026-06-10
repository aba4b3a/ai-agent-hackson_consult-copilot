from fastapi import APIRouter

router = APIRouter()


@router.post("/github")
def receive_github_webhook() -> dict[str, str]:
    return {"status": "accepted"}
