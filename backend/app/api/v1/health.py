from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import SecurityError, verify_telegram_init_data
from app.schemas.auth import VerifyInitDataRequest, VerifyInitDataResponse
from app.services.auth_service import login_with_telegram

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram/verify", response_model=VerifyInitDataResponse)
def verify(req: VerifyInitDataRequest, db: Session = Depends(get_db)) -> VerifyInitDataResponse:
    try:
        tg_user = verify_telegram_init_data(req.init_data)
    except SecurityError as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = login_with_telegram(db, tg_user)
    return VerifyInitDataResponse(access_token=token)