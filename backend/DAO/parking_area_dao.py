
import json
from psycopg2.extras import DictCursor
from backend.API.DB import pooled_connection
from pydantic import BaseModel


class ParkingAreaCreate(BaseModel):
    name: str
    capacity: int | None = None
    geom: dict


class ParkingAreaUpdate(BaseModel):
    name: str | None = None
    capacity: int | None = None
    geom: dict | None = None


class ParkingAreaDAO:

    def get_parking_area_by_id(self, parking_area_id: int):
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = """
                    SELECT parking_area_id, name, capacity,
                           ST_AsGeoJSON(geom) AS geom,
                           created_at
                    FROM public.parking_area
                    WHERE parking_area_id = %s;
                """

                cursor.execute(query, (parking_area_id,))
                row = cursor.fetchone()

                if row is None:
                    return None

                result = dict(row)

                if result["geom"] is not None:
                    result["geom"] = json.loads(result["geom"])

                if result["created_at"] is not None:
                    result["created_at"] = (
                        result["created_at"].isoformat()
                    )

                return result


    def get_all_parking_areas(
        self,
        limit: int = 20,
        offset: int = 0,
        name: str | None = None,
        bbox: tuple | None = None
    ):
        with pooled_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = """
                    SELECT parking_area_id, name, capacity,
                           created_at
                    FROM public.parking_area
                    WHERE 1=1
                """

                params = []

                if name is not None:
                    query += " AND name ILIKE %s"
                    params.append(f"%{name}%")

                if bbox is not None:
                    query += """
                        AND ST_Intersects(
                            geom,
                            ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                        )
                    """
                    params.extend(bbox)

                query += " ORDER BY parking_area_id LIMIT %s OFFSET %s"
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


    def get_parking_areas_count(
        self,
        name: str | None = None,
        bbox: tuple | None = None
    ):
        with pooled_connection() as conn:
            with conn.cursor() as cursor:

                query = """
                    SELECT COUNT(*)
                    FROM public.parking_area
                    WHERE 1=1
                """

                params = []

                if name is not None:
                    query += " AND name ILIKE %s"
                    params.append(f"%{name}%")

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

    def create_parking_area(self, new_area: ParkingAreaCreate):
        with pooled_connection() as conn:
            with conn.cursor() as cursor:

                query = """
                    INSERT INTO public.parking_area
                    (parking_area_id, name, capacity, geom, created_at)
                    VALUES (
                        nextval('public.parking_area_id_seq'),
                        %s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                        CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
                    )
                    RETURNING parking_area_id;
                """

                cursor.execute(query, (
                    new_area.name.strip(),
                    new_area.capacity,
                    json.dumps(new_area.geom)
                ))

                new_id = cursor.fetchone()[0]
                return new_id


    def update_parking_area(
        self, parking_area_id: int, area_data: ParkingAreaUpdate
    ):
        data = area_data.model_dump(exclude_unset=True)

        fields = {
            "name": "name",
            "capacity": "capacity"
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

        params.append(parking_area_id)

        query = f"""
            UPDATE public.parking_area
            SET {", ".join(assignments)}
            WHERE parking_area_id = %s
            RETURNING parking_area_id;
        """

        with pooled_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                row = cursor.fetchone()

                return row[0] if row else None


    def delete_parking_area(self, parking_area_id: int):
        with pooled_connection() as conn:
            with conn.cursor() as cursor:

                query = """
                    DELETE FROM public.parking_area
                    WHERE parking_area_id = %s
                    RETURNING parking_area_id;
                """

                cursor.execute(query, (parking_area_id,))
                deleted = cursor.fetchone()

                return deleted is not None





