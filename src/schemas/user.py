from uuid import UUID
from pydantic import BaseModel, ConfigDict,EmailStr

class UserResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str