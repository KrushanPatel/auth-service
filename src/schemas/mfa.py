from pydantic import BaseModel, Field


class MfaEnrollResponse(BaseModel):
    secret: str
    otpauth_url: str


class MfaEnrollConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=10, examples=["123456"])


class MfaEnrollConfirmResponse(BaseModel):
    recovery_codes: list[str]


class MfaDisableRequest(BaseModel):
    password: str
