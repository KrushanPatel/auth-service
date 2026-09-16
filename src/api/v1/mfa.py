from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_current_user
from schemas.mfa import (
    MfaDisableRequest,
    MfaEnrollConfirmRequest,
    MfaEnrollConfirmResponse,
    MfaEnrollResponse,
)
from services.mfa_service import confirm_mfa_enrollment, disable_mfa, enroll_mfa

router = APIRouter()


@router.post("/enroll", response_model=MfaEnrollResponse)
async def enroll(current_user=Depends(get_current_user)):
    return await enroll_mfa(current_user)


@router.post("/enroll/confirm", response_model=MfaEnrollConfirmResponse)
async def enroll_confirm(
    request: MfaEnrollConfirmRequest,
    current_user=Depends(get_current_user),
):
    recovery_codes = await confirm_mfa_enrollment(current_user, request.code)
    return {"recovery_codes": recovery_codes}


@router.post("/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable(request: MfaDisableRequest, current_user=Depends(get_current_user)):
    await disable_mfa(current_user, request.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
