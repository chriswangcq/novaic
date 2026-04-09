"""Schema registration API — Gateway calls this at startup."""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..middleware.auth import verify_service_or_user
from ..store.schema_registry import register_entities_from_specs

logger = logging.getLogger(__name__)

router = APIRouter(tags=["schema"])


class RegisterRequest(BaseModel):
    entities: List[dict]


@router.post("/v1/schema/register")
def register_schema(req: RegisterRequest, _user: str = Depends(verify_service_or_user)):
    result = register_entities_from_specs(req.entities)
    return result
