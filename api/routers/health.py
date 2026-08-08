from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    """
    Must return 200 in <1s even when the gateway container is stopped.
    NEVER call the gateway from here. Keep it as simple as possible.
    """
    return {"status": "ok"}
