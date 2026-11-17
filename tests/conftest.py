"""Shared test setup.

API tests run against a real PostgreSQL 16 (TEST_DATABASE_URL); they are skipped without it.
The database is rebuilt by the migrations once per run and refilled with the demo data per test.
"""

import os

TEST_DB = os.environ.get("TEST_DATABASE_URL", "")
if TEST_DB:
    # before any grc_api import: the settings are read once
    os.environ["DATABASE_URL"] = TEST_DB
    os.environ["DEMO_LOGIN"] = "true"
