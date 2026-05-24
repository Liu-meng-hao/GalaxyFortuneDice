from pydantic import BaseModel
from typing import Any, Optional


class ApiResponse(BaseModel):
    code: int = 0
    msg: str = "success"
    data: Optional[Any] = None