import psycopg2
from backend.API.DB import get_connection
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import DictCursor
from datetime import datetime, timezone

class DriverCreate(BaseModel):
    first_name: str
    last_name: str
    license_number: str
    hired_at: str

class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    license_number: Optional[str] = None
    hired_at: Optional[str] = None

class DriverDAO:
    def _utc_hired_at(self, value):
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)

    def get_all_drivers(self, limit: int = 20, offset: int = 0, name: Optional[str] = None, license_number: Optional[str] = None) -> list[dict]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT driver_id, first_name, last_name, license_number, hired_at
                FROM public.driver
                WHERE 1=1
                """
                params = []

                if name is not None:
                    query += " AND (first_name ILIKE %s OR last_name ILIKE %s)"
                    params.extend([f"%{name}%", f"%{name}%"])

                if license_number is not None:
                    query += " AND license_number ILIKE %s"
                    params.append(f"%{license_number}%")

                query += " LIMIT %s OFFSET %s;"
                params.extend([limit, offset])

                cursor.execute(query, tuple(params))
                result = []
                for row in cursor:
                    row_dict = dict(row)
                    if row_dict.get("hired_at"):
                        ts_str = row_dict["hired_at"].isoformat()
                        row_dict["hired_at"] = ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'
                    result.append(row_dict)
                return result

    def get_drivers_count(self, name: Optional[str] = None, license_number: Optional[str] = None) -> int:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                query = "SELECT COUNT(*) FROM public.driver WHERE 1=1"
                params = []
                if name is not None:
                    query += " AND (first_name ILIKE %s OR last_name ILIKE %s)"
                    params.extend([f"%{name}%", f"%{name}%"])
                if license_number is not None:
                    query += " AND license_number ILIKE %s"
                    params.append(f"%{license_number}%")
                cursor.execute(query, tuple(params))
                return cursor.fetchone()[0]

    def get_driver_by_id(self, driver_id: int) -> Optional[dict]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT driver_id, first_name, last_name, license_number, hired_at
                FROM public.driver
                WHERE driver_id = %s
                """
                cursor.execute(query, (driver_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                row_dict = dict(row)
                if row_dict.get("hired_at"):
                    ts_str = row_dict["hired_at"].isoformat()
                    row_dict["hired_at"] = ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'
                return row_dict

    def license_exists(self, license_number: str, exclude_id: Optional[int] = None) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                if exclude_id:
                    cursor.execute("SELECT 1 FROM public.driver WHERE license_number = %s AND driver_id != %s", (license_number, exclude_id))
                else:
                    cursor.execute("SELECT 1 FROM public.driver WHERE license_number = %s", (license_number,))
                return cursor.fetchone() is not None

    def create_driver(self, new_driver: DriverCreate) -> int:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO public.driver
                    (driver_id, first_name, last_name, license_number, hired_at)
                VALUES (
                    nextval('public.driver_id_seq'),
                    %s, %s, %s, %s
                )
                RETURNING driver_id;
                """
                cursor.execute(query, (
                    new_driver.first_name.strip(),
                    new_driver.last_name.strip(),
                    new_driver.license_number.strip(),
                    self._utc_hired_at(new_driver.hired_at)
                ))

                new_id = cursor.fetchone()[0]
                conn.commit()
                return new_id

    def update_driver(self, driver_id: int, driver: DriverUpdate) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                data = driver.model_dump(exclude_unset=True)
                query = """
                UPDATE public.driver
                SET first_name = COALESCE(%s, first_name),
                    last_name = COALESCE(%s, last_name),
                    license_number = COALESCE(%s, license_number),
                    hired_at = COALESCE(%s, hired_at)
                WHERE driver_id = %s
                RETURNING driver_id, first_name, last_name, license_number, hired_at;
                """
                try:
                    cursor.execute(query, (
                        data.get("first_name").strip() if data.get("first_name") else None,
                        data.get("last_name").strip() if data.get("last_name") else None,
                        data.get("license_number").strip() if data.get("license_number") else None,
                        self._utc_hired_at(data.get("hired_at")),
                        driver_id
                    ))
                    row = cursor.fetchone()
                    conn.commit()
                    row_dict = dict(row)
                    if row_dict.get("hired_at"):
                        ts_str = row_dict["hired_at"].isoformat()
                        row_dict["hired_at"] = ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'
                    return row_dict
                except psycopg2.IntegrityError as e:
                    conn.rollback()
                    raise e

    def delete_driver(self, driver_id: int) -> bool:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = "DELETE FROM public.driver WHERE driver_id = %s"
                try:
                    cursor.execute(query, (driver_id,))
                    rows = cursor.rowcount
                    conn.commit()
                except Exception:
                    conn.rollback()
                    rows = 0
                return rows == 1