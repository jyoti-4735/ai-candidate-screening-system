from fastapi import APIRouter
from app.services.interview_service import ROLE_LABELS

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("")
def list_roles():
    return [{"key": k, "label": v} for k, v in ROLE_LABELS.items()]
