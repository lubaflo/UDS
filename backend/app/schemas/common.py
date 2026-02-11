from __future__ import annotations

from pydantic import BaseModel


class Paginated(BaseModel):
    page: int
    page_size: int
    total: int
