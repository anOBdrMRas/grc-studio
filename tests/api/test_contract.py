"""Contract rules: every operation declares its permission; the migrations match the models."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from grc_api.auth.deps import PUBLIC_PATHS
from grc_api.db import Base, get_engine
from grc_api.main import create_app

METHODS = {"get", "post", "put", "patch", "delete"}


def _operations() -> list[tuple[str, str, dict[str, object]]]:
    spec = create_app(run_lifespan=False).openapi()
    return [
        (m.upper(), path, op)
        for path, ops in spec["paths"].items()
        for m, op in ops.items()
        if m in METHODS
    ]


def test_every_operation_declares_a_permission() -> None:
    ops = _operations()
    assert len(ops) > 30, "the API surface was not found – the test would prove nothing"
    missing = [
        f"{m} {p}" for m, p, op in ops if p not in PUBLIC_PATHS and not op.get("x-permission")
    ]
    assert missing == [], f"operations without permission: {missing}"


def test_public_paths_are_known() -> None:
    paths = {p for _, p, _ in _operations()}
    assert {"/health/live", "/health/ready", "/api/v1/auth/demo-login"} <= paths
    # a public path must not carry a permission (it would never be checked)
    assert not [p for _, p, op in _operations() if p in PUBLIC_PATHS and op.get("x-permission")]


async def test_migrations_match_models(migrated: None) -> None:
    def diff(conn):  # type: ignore[no-untyped-def]
        return compare_metadata(
            MigrationContext.configure(conn, opts={"compare_type": True}), Base.metadata
        )

    async with get_engine().connect() as conn:
        changes = await conn.run_sync(diff)
    assert changes == []
