from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class RefreshToken(BaseModel):
    
    id:UUID
    user_id:UUID
    token_hash:str
    jti:UUID
    expire_at:datetime
    created_at:datetime
    last_used_at:datetime | None
    revoked:bool
    
    
        