from config.dbconfig import PG_DB_CONFIG, POOL_CONFIG
from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional
from datetime import datetime, timezone
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool

class VehicleAssignment(BaseModel):
    assignment_id: Optional[int] = None
    vehicle_id: int
    driver_id: int
    assigned_from: datetime
    assigned_to: Optional[datetime] = None

    @field_validator("assigned_from", "assigned_to", mode="before")
    @classmethod
    def validate_timestamp(cls, value):
        if isinstance(value, str):
            if "T" not in value or not (value.endswith("Z") or value[10:].count("+") or value[10:].count("-")):
                raise ValueError("Timestamp must be RFC 3339 with a timezone.")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("Invalid RFC 3339 timestamp.")
            if parsed.tzinfo is None:
                raise ValueError("Timestamp must include a timezone.")
            return parsed
        return value

    @field_serializer("assigned_from", "assigned_to")
    def serialize_timestamp(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class VehicleAssignmentUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    assigned_from: Optional[datetime] = None
    assigned_to: Optional[datetime] = None

    @field_validator("assigned_from", "assigned_to", mode="before")
    @classmethod
    def validate_timestamp(cls, value):
        if isinstance(value, str):
            if "T" not in value or not (value.endswith("Z") or value[10:].count("+") or value[10:].count("-")):
                raise ValueError("Timestamp must be RFC 3339 with a timezone.")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("Invalid RFC 3339 timestamp.")
            if parsed.tzinfo is None:
                raise ValueError("Timestamp must include a timezone.")
            return parsed
        return value

    @field_serializer("assigned_from", "assigned_to")
    def serialize_timestamp(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class VehicleAssignmentDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG
        )

    def vehicle_exists(self, vehicle_id: int) -> bool:
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute("select 1 from vehicle where vehicle_id = %s", (vehicle_id,))
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        finally:
            self.pool.putconn(conn)

    def driver_exists(self, driver_id: int) -> bool:
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute("select 1 from driver where driver_id = %s", (driver_id,))
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        finally:
            self.pool.putconn(conn)

    def get_all_assignments(self, vehicle_id: Optional[int] = None, driver_id: Optional[int] = None, active: Optional[bool] = None, limit: int = 20, offset: int = 0) -> dict:
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            
            base_query = "from vehicle_assignment where 1=1"
            params = []

            if vehicle_id is not None:
                base_query += " and vehicle_id = %s"
                params.append(vehicle_id)
            if driver_id is not None:
                base_query += " and driver_id = %s"
                params.append(driver_id)
            if active is not None:
                if active:
                    base_query += " and assigned_to is null"
                else:
                    base_query += " and assigned_to is not null"

            # Count total matching records before pagination
            cursor.execute(f"select count(*) {base_query}", tuple(params))
            count = cursor.fetchone()[0]

            # Fetch paginated items
            query = f"select assignment_id, vehicle_id, driver_id, assigned_from, assigned_to {base_query} order by assignment_id limit %s offset %s"
            cursor.execute(query, tuple(params) + (limit, offset))
            
            items = []
            for row in cursor:
                items.append(VehicleAssignment(**row))
            
            cursor.close()
            return {"items": items, "limit": limit, "offset": offset, "count": count}
        finally:
            self.pool.putconn(conn)

    def get_assignment_by_id(self, assignment_id: int) -> Optional[VehicleAssignment]:
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            query = """
            select assignment_id, vehicle_id, driver_id, assigned_from, assigned_to
            from vehicle_assignment
            where assignment_id = %s
            """
            cursor.execute(query, (assignment_id,))
            row = cursor.fetchone()
            cursor.close()
            if row is None:
                return None
            return VehicleAssignment(**row)
        finally:
            self.pool.putconn(conn)

    def create_assignment(self, new_assignment: VehicleAssignment) -> int:
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            query = """
            insert into vehicle_assignment (vehicle_id, driver_id, assigned_from, assigned_to)
            values (%(vehicle_id)s, %(driver_id)s, %(assigned_from)s, %(assigned_to)s)
            returning assignment_id;
            """
            cursor.execute(query, new_assignment.model_dump(exclude_none=False))
            assignment_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            return assignment_id
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def update_assignment(self, assignment_id: int, assignment: VehicleAssignment) -> VehicleAssignment:
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            query = """
            update vehicle_assignment
            set vehicle_id = %(vehicle_id)s, driver_id = %(driver_id)s, assigned_from = %(assigned_from)s, assigned_to = %(assigned_to)s
            where assignment_id = %(assignment_id)s
            returning assignment_id, vehicle_id, driver_id, assigned_from, assigned_to
            """
            data = assignment.model_dump()
            data["assignment_id"] = assignment_id
            cursor.execute(query, data)
            row = cursor.fetchone()
            conn.commit()
            cursor.close()
            return VehicleAssignment(**row) if row else None
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def delete_assignment(self, assignment_id: int) -> bool:
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            query = "delete from vehicle_assignment where assignment_id = %s"
            cursor.execute(query, (assignment_id,))
            rows = cursor.rowcount
            conn.commit()
            cursor.close()
            return rows == 1
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)