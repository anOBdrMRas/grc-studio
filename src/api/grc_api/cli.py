"""Command line: migrate, seed-demo, create-admin, serve, openapi."""

import argparse
import asyncio
import json
import sys

from grc_api.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="grc-api")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="apply the database migrations")
    sub.add_parser("seed-demo", help="load the demo data into an empty database")
    admin = sub.add_parser("create-admin", help="create a local administrator account")
    admin.add_argument("username")
    admin.add_argument(
        "password", nargs="?", help="omit to be asked (keeps it out of the shell history)"
    )
    serve = sub.add_parser("serve", help="run the API server")
    serve.add_argument("--host", default="0.0.0.0")  # noqa: S104 - runs inside the container
    serve.add_argument("--port", type=int, default=8000)
    sub.add_parser("openapi", help="print the OpenAPI document")
    args = parser.parse_args()

    if args.cmd == "migrate":
        from grc_api.migrate import upgrade

        upgrade()
    elif args.cmd == "seed-demo":
        asyncio.run(_seed())
    elif args.cmd == "create-admin":
        import getpass

        password = args.password or getpass.getpass("Password: ")
        if len(password) < 12:
            raise SystemExit("The password needs at least 12 characters")
        asyncio.run(_admin(args.username, password))
    elif args.cmd == "serve":
        import uvicorn

        uvicorn.run(
            "grc_api.main:app",
            host=args.host,
            port=args.port,
            workers=1,
            log_level=get_settings().log_level.lower(),
        )
    elif args.cmd == "openapi":
        from grc_api.main import create_app

        json.dump(
            create_app(run_lifespan=False).openapi(),
            sys.stdout,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        sys.stdout.write("\n")


async def _seed() -> None:
    from grc_api.db import get_sessionmaker
    from grc_api.seed.loader import is_empty, load_demo

    async with get_sessionmaker()() as db:
        if not await is_empty(db):
            print("database is not empty – demo data not loaded")
            return
        print("loaded:", await load_demo(db))


async def _admin(username: str, password: str) -> None:
    from grc_api.auth.passwords import hash_password
    from grc_api.db import get_sessionmaker
    from grc_api.models import User

    async with get_sessionmaker()() as db:
        db.add(
            User(
                id=f"U-{username.upper()}"[:40],
                code=f"U-{username.upper()}"[:40],
                last_name=username,
                display_name=username,
                username=username,
                password_hash=hash_password(password),
                system_roles=["admin"],
            )
        )
        await db.commit()
    print("created", username)


if __name__ == "__main__":
    main()
