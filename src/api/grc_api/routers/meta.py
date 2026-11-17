from fastapi import APIRouter

from grc_api.auth.deps import secured
from grc_api.domain.catalogs import all_catalogs
from grc_api.domain.iso import ISO_CATALOG
from grc_api.schemas.auth import Catalogs, IsoClause

router = APIRouter(prefix="/api/v1/meta", tags=["meta"])


@router.get("/catalogs", operation_id="meta_catalogs", **secured("people:read"))
async def catalogs() -> Catalogs:
    return Catalogs(
        lists=all_catalogs(),
        iso=[IsoClause(id=i, standard=s, clause=c, title=t) for i, s, c, t in ISO_CATALOG],
    )
