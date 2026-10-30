"""GET /health: is the process alive and can it reach the database?"""

import logging

from fastapi import APIRouter, Request, Response
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request, response: Response) -> dict[str, str]:
    """Report liveness and database connectivity.

    Declared with `def` (not `async def`) on purpose: the SQLAlchemy call is
    synchronous, and FastAPI runs sync endpoints in a worker thread pool so the
    event loop is never blocked.
    """
    database = request.app.state.database
    try:
        database.ping()
    except SQLAlchemyError:
        # The exception (and the database URL) goes to the log, not the client.
        logger.exception("Health check failed: database unreachable")
        response.status_code = 503
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}
