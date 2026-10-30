import os
from contextlib import contextmanager
from functools import lru_cache
import psycopg2
from psycopg2.pool import ThreadedConnectionPool


@lru_cache(maxsize=1)
def get_db_pool():
    # One shared pool, not a new pool for every DAO call.
    return ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=os.environ["DATABASE_URL"]
    )


def get_connection():
    # Preserve the original function for /api/v1/test-db.
    return psycopg2.connect(os.environ["DATABASE_URL"])


def release_connection(conn):
    get_db_pool().putconn(conn)


@contextmanager
def pooled_connection():
    pool = get_db_pool()
    conn = pool.getconn()

    try:
        # Commit on success, rollback on exception.
        with conn:
            yield conn
    finally:
        # Return connection to pool.
        pool.putconn(conn)