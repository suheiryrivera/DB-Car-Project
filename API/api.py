from fastapi import FastAPI
from fastapi import HTTPException
from API.DB import get_connection
app = FastAPI()

@app.get("/api/v1/test-db")
def test_database():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_database(), version();")
                result = cursor.fetchone()

        return {
            "status": "connected",
            "database": result[0],
            "postgresql_version": result[1]
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )