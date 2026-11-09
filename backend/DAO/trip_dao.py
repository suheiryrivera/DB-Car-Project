import json
from backend.API.DB import pooled_connection
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from psycopg2.extras import DictCursor

class TripCreate(BaseModel):
    vehicle_id: int
    start_ts: str
    end_ts: str
    start_geom: Optional[Dict[str, Any]] = None
    end_geom: Optional[Dict[str, Any]] = None
    distance_km: Optional[float] = None

class TripUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    start_geom: Optional[Dict[str, Any]] = None
    end_geom: Optional[Dict[str, Any]] = None
    distance_km: Optional[float] = None

class TripDAO:
    def _format_timestamp(self, dt): #dt = date time
        if not dt:
            return None
        ts_str = dt.isoformat()
        return ts_str if ('+' in ts_str or ts_str.endswith('Z')) else ts_str + 'Z'

    def vehicle_exists(self, vehicle_id: int) -> bool:
        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM public.vehicle WHERE vehicle_id = %s", (vehicle_id,))
                return cursor.fetchone() is not None

    def get_all_trips(
        self,
        vehicle_id: Optional[int] = None,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT trip_id, vehicle_id, start_ts, end_ts, 
                       ST_AsGeoJSON(start_geom)::json AS start_geom,
                       ST_AsGeoJSON(end_geom)::json AS end_geom,
                       distance_km
                FROM public.trip
                WHERE 1=1
                """
                params = []

                if vehicle_id is not None:
                    query += " AND vehicle_id = %s"
                    params.append(vehicle_id)
                if from_ts is not None:
                    query += " AND start_ts >= %s"
                    params.append(from_ts)
                if to_ts is not None:
                    query += " AND end_ts <= %s"
                    params.append(to_ts)

                query += " ORDER BY start_ts DESC LIMIT %s OFFSET %s;"
                params.extend([limit, offset])

                cursor.execute(query, tuple(params))
                result = []
                for row in cursor:
                    d = dict(row)
                    d["start_ts"] = self._format_timestamp(d["start_ts"])
                    d["end_ts"] = self._format_timestamp(d["end_ts"])
                    result.append(d)
                return result

    def get_trip_by_id(self, trip_id: int) -> Optional[dict]:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                SELECT trip_id, vehicle_id, start_ts, end_ts, 
                       ST_AsGeoJSON(start_geom)::json AS start_geom,
                       ST_AsGeoJSON(end_geom)::json AS end_geom,
                       distance_km
                FROM public.trip
                WHERE trip_id = %s
                """
                cursor.execute(query, (trip_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                d = dict(row)
                d["start_ts"] = self._format_timestamp(d["start_ts"])
                d["end_ts"] = self._format_timestamp(d["end_ts"])
                return d

    def create_trip(self, data: TripCreate) -> int:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Dynamically get the next available ID
                cursor.execute("SELECT COALESCE(MAX(trip_id), 0) + 1 FROM public.trip;")
                new_id = cursor.fetchone()[0]

                query = """
                INSERT INTO public.trip
                    (trip_id, vehicle_id, start_ts, end_ts, start_geom, end_geom, distance_km)
                VALUES (
                    %s, %s, %s, %s,
                    CASE WHEN %s::text IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) END,
                    CASE WHEN %s::text IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) END,
                    %s
                )
                RETURNING trip_id;
                """
                sg_json = json.dumps(data.start_geom) if data.start_geom else None
                eg_json = json.dumps(data.end_geom) if data.end_geom else None

                cursor.execute(query, (
                    new_id,
                    data.vehicle_id,
                    data.start_ts,
                    data.end_ts,
                    sg_json, sg_json,
                    eg_json, eg_json,
                    data.distance_km
                ))
                conn.commit()
                return new_id

    def update_trip(self, trip_id: int, data: TripUpdate) -> dict:
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                fields = data.model_dump(exclude_unset=True)
                set_clauses = []
                params = []

                if "vehicle_id" in fields:
                    set_clauses.append("vehicle_id = %s")
                    params.append(fields["vehicle_id"])
                if "start_ts" in fields:
                    set_clauses.append("start_ts = %s")
                    params.append(fields["start_ts"])
                if "end_ts" in fields:
                    set_clauses.append("end_ts = %s")
                    params.append(fields["end_ts"])
                if "start_geom" in fields:
                    if fields["start_geom"] is None:
                        set_clauses.append("start_geom = NULL")
                    else:
                        set_clauses.append("start_geom = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)")
                        params.append(json.dumps(fields["start_geom"]))
                if "end_geom" in fields:
                    if fields["end_geom"] is None:
                        set_clauses.append("end_geom = NULL")
                    else:
                        set_clauses.append("end_geom = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)")
                        params.append(json.dumps(fields["end_geom"]))
                if "distance_km" in fields:
                    set_clauses.append("distance_km = %s")
                    params.append(fields["distance_km"])

                params.append(trip_id)
                query = f"""
                UPDATE public.trip
                SET {", ".join(set_clauses)}
                WHERE trip_id = %s
                RETURNING trip_id, vehicle_id, start_ts, end_ts, 
                          ST_AsGeoJSON(start_geom)::json AS start_geom,
                          ST_AsGeoJSON(end_geom)::json AS end_geom,
                          distance_km;
                """
                cursor.execute(query, tuple(params))
                row = cursor.fetchone()
                conn.commit()
                d = dict(row)
                d["start_ts"] = self._format_timestamp(d["start_ts"])
                d["end_ts"] = self._format_timestamp(d["end_ts"])
                return d

    def delete_trip(self, trip_id: int) -> bool:
        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM public.trip WHERE trip_id = %s", (trip_id,))
                rows = cursor.rowcount
                conn.commit()
                return rows == 1