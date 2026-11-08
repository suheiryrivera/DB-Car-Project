
import json
from psycopg2.extras import DictCursor
from backend.API.DB import pooled_connection
from pydantic import BaseModel


class RoadSegmentCreate(BaseModel):
    name: str
    speed_limit_kph: int | None = None
    is_oneway: bool | None = None
    direction: str | None = None
    geom: dict

class RoadSegmentUpdate(BaseModel):
    name: str | None = None
    speed_limit_kph: int | None = None
    is_oneway: bool | None = None
    direction: str | None = None
    geom: dict | None = None

class RoadSegmentDAO:

    def get_road_segment_by_id(self, road_id: int):
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = """
                    SELECT road_id, name, speed_limit_kph,is_oneway,direction,
                           ST_AsGeoJSON(geom) AS geom,
                           created_at
                    FROM public.road_segment
                    WHERE road_id = %s;
                """

                cursor.execute(query, (road_id,))
                row = cursor.fetchone()

                if row is None:
                    return None

                result = dict(row)

                if result["geom"] is not None:
                    result["geom"] = json.loads(result["geom"])

                if result["created_at"] is not None:
                    result["created_at"] = result["created_at"].isoformat()

                return result

    def get_all_road_segments(
            self,
            limit: int = 20,
            offset: int = 0,
            name: str | None = None,
            min_speed_kph: int | None = None,
            max_speed_kph: int | None = None,
            bbox: tuple | None = None
    ):
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = """
                    SELECT road_id, name, speed_limit_kph,
                           created_at
                    FROM public.road_segment
                    WHERE 1=1
                """

                params = []

                if name is not None:
                    query += " AND name ILIKE %s"
                    params.append(f"%{name}%")

                if min_speed_kph is not None:
                    query += " AND speed_limit_kph >= %s"
                    params.append(min_speed_kph)

                if max_speed_kph is not None:
                    query += " AND speed_limit_kph <= %s"
                    params.append(max_speed_kph)

                if bbox is not None:
                    query += """
                        AND ST_Intersects(
                            geom,
                            ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                        )
                    """
                    params.extend(bbox)

                query += " ORDER BY road_id LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cursor.execute(query, tuple(params))

                result = []

                for row in cursor.fetchall():
                    row_dict = dict(row)

                    if row_dict["created_at"] is not None:
                        row_dict["created_at"] = (
                                row_dict["created_at"].isoformat() + "Z"
                        )

                    result.append(row_dict)

                return result

    def get_road_segments_count(
            self,
            name: str | None = None,
            min_speed_kph: int | None = None,
            max_speed_kph: int | None = None,
            bbox: tuple | None = None
    ):
        with pooled_connection() as conn:
            with conn.cursor() as cursor:

                query = """
                    SELECT COUNT(*)
                    FROM public.road_segment
                    WHERE 1=1
                """

                params = []

                if name is not None:
                    query += " AND name ILIKE %s"
                    params.append(f"%{name}%")

                if min_speed_kph is not None:
                    query += " AND speed_limit_kph >= %s"
                    params.append(min_speed_kph)

                if max_speed_kph is not None:
                    query += " AND speed_limit_kph <= %s"
                    params.append(max_speed_kph)

                if bbox is not None:
                    query += """
                        AND ST_Intersects(
                            geom,
                            ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                        )
                    """
                    params.extend(bbox)

                cursor.execute(query, tuple(params))

                return cursor.fetchone()[0]

    def create_road_segment(self, new_road: RoadSegmentCreate):
        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO public.road_segment
                    (road_id, name, speed_limit_kph,
                     is_oneway, direction, geom, created_at)
                    VALUES (
                        nextval('public.road_segment_id_seq'),
                        %s, %s, %s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                        CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
                    )
                    RETURNING road_id;
                """

                cursor.execute(query, (
                    new_road.name.strip(),
                    new_road.speed_limit_kph,
                    new_road.is_oneway,
                    new_road.direction,
                    json.dumps(new_road.geom)
                ))

                new_id = cursor.fetchone()[0]
                return new_id


    def update_road_segment(
        self, road_id: int, road_data: RoadSegmentUpdate
    ):
        data = road_data.model_dump(exclude_unset=True)

        fields = {
            "name": "name",
            "speed_limit_kph": "speed_limit_kph",
            "is_oneway": "is_oneway",
            "direction": "direction"
        }

        assignments = []
        params = []

        for field, value in data.items():
            if field == "geom":
                assignments.append(
                    "geom = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)"
                )
                params.append(json.dumps(value))

            elif field in fields:
                assignments.append(f"{fields[field]} = %s")

                if field == "name" and isinstance(value, str):
                    value = value.strip()

                params.append(value)

        if not assignments:
            raise ValueError("No fields to update")

        params.append(road_id)

        query = f"""
            UPDATE public.road_segment
            SET {", ".join(assignments)}
            WHERE road_id = %s
            RETURNING road_id;
        """

        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                row = cursor.fetchone()

                return row[0] if row else None


    def delete_road_segment(self, road_id: int):
        with pooled_connection() as conn:
            with conn.cursor() as cursor:

                query = """
                    DELETE FROM public.road_segment
                    WHERE road_id = %s
                    RETURNING road_id;
                """

                cursor.execute(query, (road_id,))
                deleted = cursor.fetchone()

                return deleted is not None


    def get_road_segments_geojson(
        self,
        limit: int = 15000,
        offset: int = 0,
        name: str | None = None,
        min_speed_kph: int | None = None,
        max_speed_kph: int | None = None
    ):
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = """
                    SELECT road_id, name, speed_limit_kph,
                           is_oneway, direction,
                           ST_AsGeoJSON(geom) AS geom,
                           created_at
                    FROM public.road_segment 
                    WHERE 1=1
                """

                params = []

                if name is not None:
                    query += " AND name ILIKE %s"
                    params.append(f"%{name}%")

                if min_speed_kph is not None:
                    query += " AND speed_limit_kph >= %s"
                    params.append(min_speed_kph)

                if max_speed_kph is not None:
                    query += " AND speed_limit_kph <= %s"
                    params.append(max_speed_kph)

                query += " ORDER BY road_id LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cursor.execute(query, tuple(params))

                result = []

                for row in cursor.fetchall():
                    road = dict(row)

                    if road["geom"] is not None:
                        road["geom"] = json.loads(road["geom"])

                    if road["created_at"] is not None:
                        road["created_at"] = (
                            road["created_at"].isoformat() + "Z"
                        )

                    result.append(road)

                return result







