from backend.API.DB import pooled_connection
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import DictCursor
import json

class VehicleCreate(BaseModel):
    vehicle_type_id: int
    vehicle_status_id: int
    plate_number: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None

class VehicleUpdate(BaseModel):
    vehicle_type_id: Optional[int] = None
    vehicle_status_id: Optional[int] = None
    plate_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None

class VehicleDAO:
    def get_all_vehicles(self, limit: int = 20, offset: int = 0, status: Optional[str | int] = None, plate_number: Optional[str] = None) -> list[dict]:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT v.vehicle_id, v.vehicle_type_id, v.vehicle_status_id, 
                       v.plate_number, v.make, v.model, v.year, v.created_at
                FROM public.vehicle v
                LEFT JOIN public.vehicle_status s ON v.vehicle_status_id = s.vehicle_status_id
                WHERE 1=1
                """
                params = []

                if status is not None:
                    if str(status).isdigit():
                        query += " AND v.vehicle_status_id = %s"
                        params.append(int(status))
                    else:
                        query += " AND s.name ILIKE %s"
                        params.append(f"%{status}%")

                if plate_number is not None:
                    query += " AND v.plate_number ILIKE %s"
                    params.append(f"%{plate_number}%")

                query += " LIMIT %s OFFSET %s;"
                params.extend([limit, offset])

                cursor.execute(query, tuple(params))
                result = []
                for row in cursor:
                    row_dict = dict(row)
                    if row_dict.get("created_at"):
                        ts_str = row_dict["created_at"].isoformat()
                        row_dict["created_at"] = ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'
                    result.append(row_dict)
                return result

    def get_vehicles_count(self, status: Optional[str | int] = None, plate_number: Optional[str] = None) -> int:
        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                SELECT COUNT(*) 
                FROM public.vehicle v
                LEFT JOIN public.vehicle_status s ON v.vehicle_status_id = s.vehicle_status_id
                WHERE 1=1
                """
                params = []
                if status is not None:
                    if str(status).isdigit():
                        query += " AND v.vehicle_status_id = %s"
                        params.append(int(status))
                    else:
                        query += " AND s.name ILIKE %s"
                        params.append(f"%{status}%")
                if plate_number is not None:
                    query += " AND v.plate_number ILIKE %s"
                    params.append(f"%{plate_number}%")

                cursor.execute(query, tuple(params))
                return cursor.fetchone()[0]

    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[dict]:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT vehicle_id, vehicle_type_id, vehicle_status_id, 
                       plate_number, make, model, year, created_at
                FROM public.vehicle
                WHERE vehicle_id = %s
                """
                cursor.execute(query, (vehicle_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                row_dict = dict(row)
                if row_dict.get("created_at"):
                    ts_str = row_dict["created_at"].isoformat()
                    row_dict["created_at"] = ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'
                return row_dict

    def plate_exists(self, plate_number: str, exclude_id: Optional[int] = None) -> bool:
        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                if exclude_id:
                    cursor.execute("SELECT 1 FROM public.vehicle WHERE plate_number = %s AND vehicle_id != %s", (plate_number, exclude_id))
                else:
                    cursor.execute("SELECT 1 FROM public.vehicle WHERE plate_number = %s", (plate_number,))
                return cursor.fetchone() is not None

    def get_vehicle_current_location(self, vehicle_id: int) -> dict | None:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                check_query = "SELECT vehicle_id FROM public.vehicle WHERE vehicle_id = %s"
                cursor.execute(check_query, (vehicle_id,))
                if not cursor.fetchone():
                    return {"exists": False}

                query = """
                SELECT v.vehicle_id, v.plate_number, 
                       s.name AS status, 
                       vk.name AS vehicle_kind, 
                       ft.name AS fuel_type, vt.emissions_rating,
                       p.ts AS last_ts, 
                       ST_AsGeoJSON(p.geom) AS last_geom,
                       p.speed_kph, p.heading_deg
                FROM public.vehicle v
                LEFT JOIN public.vehicle_status s ON v.vehicle_status_id = s.vehicle_status_id
                LEFT JOIN public.vehicle_type vt ON v.vehicle_type_id = vt.vehicle_type_id
                LEFT JOIN public.vehicle_kind vk ON vt.vehicle_kind_id = vk.vehicle_kind_id
                LEFT JOIN public.fuel_type ft ON vt.fuel_type_id = ft.fuel_type_id
                JOIN public.location_ping p ON v.vehicle_id = p.vehicle_id
                WHERE v.vehicle_id = %s
                ORDER BY p.ts DESC
                LIMIT 1;
                """
                cursor.execute(query, (vehicle_id,))
                row = cursor.fetchone()

                if not row:
                    return {"exists": True, "ping": None}
                
                row_dict = dict(row)
                if row_dict.get("last_ts"):
                    ts_str = row_dict["last_ts"].isoformat()
                    row_dict["last_ts"] = ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'
                if row_dict.get("last_geom"):
                    row_dict["last_geom"] = json.loads(row_dict["last_geom"])
                    
                return {"exists": True, "ping": row_dict}

    def create_vehicle(self, new_vehicle: VehicleCreate) -> int:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT nextval('public.vehicle_id_seq')")
                new_id = cursor.fetchone()[0]
                query = """
                INSERT INTO public.vehicle (vehicle_id, vehicle_type_id, vehicle_status_id, plate_number, make, model, year, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
                RETURNING vehicle_id;
                """
                cursor.execute(query, (
                    new_id,
                    new_vehicle.vehicle_type_id,
                    new_vehicle.vehicle_status_id,
                    new_vehicle.plate_number.strip(),
                    new_vehicle.make.strip() if new_vehicle.make else None,
                    new_vehicle.model.strip() if new_vehicle.model else None,
                    new_vehicle.year
                ))
                conn.commit()
                return new_id

    def update_vehicle(self, vehicle_id: int, vehicle: VehicleUpdate) -> dict:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                data = vehicle.model_dump(exclude_unset=True)
                
                query = """
                UPDATE public.vehicle
                SET vehicle_type_id = COALESCE(%s, vehicle_type_id),
                    vehicle_status_id = COALESCE(%s, vehicle_status_id),
                    plate_number = COALESCE(%s, plate_number),
                    make = COALESCE(%s, make),
                    model = COALESCE(%s, model),
                    year = COALESCE(%s, year)
                WHERE vehicle_id = %s
                RETURNING vehicle_id, vehicle_type_id, vehicle_status_id, plate_number, make, model, year, created_at;
                """
                cursor.execute(query, (
                    data.get("vehicle_type_id"),
                    data.get("vehicle_status_id"),
                    data.get("plate_number").strip() if data.get("plate_number") else None,
                    data.get("make").strip() if data.get("make") else None,
                    data.get("model").strip() if data.get("model") else None,
                    data.get("year"),
                    vehicle_id
                ))
                row = cursor.fetchone()
                conn.commit()
                
                row_dict = dict(row)
                if row_dict.get("created_at"):
                    ts_str = row_dict["created_at"].isoformat()
                    row_dict["created_at"] = ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'
                    
                return row_dict

    def delete_vehicle(self, vehicle_id: int) -> bool:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = "DELETE FROM public.vehicle WHERE vehicle_id = %s"
                try:
                    cursor.execute(query, (vehicle_id,))
                    rows = cursor.rowcount
                    conn.commit()
                except Exception:
                    conn.rollback()
                    rows = 0
                return rows == 1