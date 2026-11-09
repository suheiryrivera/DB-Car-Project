import json
from backend.API.DB import pooled_connection
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from psycopg2.extras import DictCursor

class LocationPingCreate(BaseModel):
    vehicle_id: int
    ts: str
    geom: Dict[str, Any]
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None

class LocationPingUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    ts: Optional[str] = None
    geom: Optional[Dict[str, Any]] = None
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None

class LocationPingDAO:
    def _format_timestamp(self, dt): # date time
        if not dt:
            return None
        ts_str = dt.isoformat()
        return ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'

    def vehicle_exists(self, vehicle_id: int) -> bool:
        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM public.vehicle WHERE vehicle_id = %s", (vehicle_id,))
                return cursor.fetchone() is not None

    def get_all_pings(
        self,
        vehicle_id: Optional[int] = None,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
        bbox: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT ping_id, vehicle_id, ts, 
                       ST_AsGeoJSON(geom)::json AS geom, 
                       speed_kph, heading_deg
                FROM public.location_ping
                WHERE 1=1
                """
                params = []

                if vehicle_id is not None:
                    query += " AND vehicle_id = %s"
                    params.append(vehicle_id)
                if from_ts is not None:
                    query += " AND ts >= %s"
                    params.append(from_ts)
                if to_ts is not None:
                    query += " AND ts <= %s"
                    params.append(to_ts)
                if bbox is not None:
                    min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
                    query += """ AND ST_Intersects(
                        geom, 
                        ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                    )"""
                    params.extend([min_lon, min_lat, max_lon, max_lat])

                query += " ORDER BY ts DESC LIMIT %s OFFSET %s;"
                params.extend([limit, offset])

                cursor.execute(query, tuple(params))
                result = []
                for row in cursor:
                    d = dict(row)
                    d["ts"] = self._format_timestamp(d["ts"])
                    result.append(d)
                return result

    def get_ping_by_id(self, ping_id: int) -> Optional[dict]:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT ping_id, vehicle_id, ts, 
                       ST_AsGeoJSON(geom)::json AS geom, 
                       speed_kph, heading_deg
                FROM public.location_ping
                WHERE ping_id = %s
                """
                cursor.execute(query, (ping_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                d = dict(row)
                d["ts"] = self._format_timestamp(d["ts"])
                return d

    def create_ping(self, data: LocationPingCreate) -> int:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Dynamically get the next available ID
                cursor.execute("SELECT COALESCE(MAX(ping_id), 0) + 1 FROM public.location_ping;")
                new_id = cursor.fetchone()[0]

                query = """
                INSERT INTO public.location_ping
                    (ping_id, vehicle_id, ts, geom, speed_kph, heading_deg)
                VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), %s, %s)
                RETURNING ping_id;
                """
                cursor.execute(query, (
                    new_id,
                    data.vehicle_id,
                    data.ts,
                    json.dumps(data.geom),
                    data.speed_kph,
                    data.heading_deg
                ))
                conn.commit()
                return new_id

    def update_ping(self, ping_id: int, data: LocationPingUpdate) -> dict:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                fields = data.model_dump(exclude_unset=True)
                set_clauses = []
                params = []

                if "vehicle_id" in fields:
                    set_clauses.append("vehicle_id = %s")
                    params.append(fields["vehicle_id"])
                if "ts" in fields:
                    set_clauses.append("ts = %s")
                    params.append(fields["ts"])
                if "geom" in fields:
                    set_clauses.append("geom = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)")
                    params.append(json.dumps(fields["geom"]))
                if "speed_kph" in fields:
                    set_clauses.append("speed_kph = %s")
                    params.append(fields["speed_kph"])
                if "heading_deg" in fields:
                    set_clauses.append("heading_deg = %s")
                    params.append(fields["heading_deg"])

                params.append(ping_id)
                query = f"""
                UPDATE public.location_ping
                SET {", ".join(set_clauses)}
                WHERE ping_id = %s
                RETURNING ping_id, vehicle_id, ts, ST_AsGeoJSON(geom)::json AS geom, speed_kph, heading_deg;
                """
                cursor.execute(query, tuple(params))
                row = cursor.fetchone()
                conn.commit()
                d = dict(row)
                d["ts"] = self._format_timestamp(d["ts"])
                return d

    def delete_ping(self, ping_id: int) -> bool:
        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM public.location_ping WHERE ping_id = %s", (ping_id,))
                rows = cursor.rowcount
                conn.commit()
                return rows == 1