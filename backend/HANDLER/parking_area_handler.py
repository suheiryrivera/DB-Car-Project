
import math
from fastapi import HTTPException
from backend.DAO.parking_area_dao import (
    ParkingAreaDAO,
    ParkingAreaCreate,
    ParkingAreaUpdate
)


class ParkingAreaHandler:

    def validate_bbox(self, bbox: str | None):
        if bbox is None:
            return None

        try:
            values = tuple(float(x) for x in bbox.split(","))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox format."
            )

        if len(values) != 4:
            raise HTTPException(
                status_code=400,
                detail="bbox must contain four values."
            )

        min_lon, min_lat, max_lon, max_lat = values

        if (
            not all(math.isfinite(x) for x in values)
            or not -180 <= min_lon < max_lon <= 180
            or not -90 <= min_lat < max_lat <= 90
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox coordinates."
            )

        return values

    def validate_polygon(self, geom: dict):
        if not isinstance(geom, dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid geometry."
            )

        if geom.get("type") != "Polygon":
            raise HTTPException(
                status_code=400,
                detail="Geometry must be a Polygon."
            )

        rings = geom.get("coordinates")

        if not isinstance(rings, list) or not rings:
            raise HTTPException(
                status_code=400,
                detail="Polygon coordinates are required."
            )

        for ring in rings:
            if not isinstance(ring, list) or len(ring) < 4:
                raise HTTPException(
                    status_code=400,
                    detail="Polygon ring requires at least four points."
                )

            for point in ring:
                if (
                    not isinstance(point, list)
                    or len(point) != 2
                    or any(
                        not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or not math.isfinite(value)
                        for value in point
                    )
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid polygon coordinates."
                    )

                lon, lat = point

                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    raise HTTPException(
                        status_code=400,
                        detail="Coordinates outside valid range."
                    )

            if ring[0] != ring[-1]:
                raise HTTPException(
                    status_code=400,
                    detail="Polygon ring must be closed."
                )

            if len({tuple(point) for point in ring[:-1]}) < 3:
                raise HTTPException(
                    status_code=400,
                    detail="Polygon requires three distinct vertices."
                )

    def get_all_parking_areas(
        self,
        limit: int = 20,
        offset: int = 0,
        name: str | None = None,
        bbox: str | None = None
    ):
        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Limit and offset must be non-negative."
            )

        bbox_values = self.validate_bbox(bbox)

        dao = ParkingAreaDAO()

        items = dao.get_all_parking_areas(
            limit=limit,
            offset=offset,
            name=name,
            bbox=bbox_values
        )

        count = dao.get_parking_areas_count(
            name=name,
            bbox=bbox_values
        )

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_parking_area_by_id(self, parking_area_id: int):
        if parking_area_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="parking_area_id must be positive."
            )

        dao = ParkingAreaDAO()
        result = dao.get_parking_area_by_id(parking_area_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Parking area not found."
            )

        return result

    def create_parking_area(self, new_area: ParkingAreaCreate):
        if not new_area.name.strip():
            raise HTTPException(
                status_code=400,
                detail="name cannot be empty."
            )

        if new_area.capacity is not None and new_area.capacity < 0:
            raise HTTPException(
                status_code=400,
                detail="capacity must be non-negative."
            )

        self.validate_polygon(new_area.geom)

        dao = ParkingAreaDAO()

        parking_area_id = dao.create_parking_area(new_area)

        return dao.get_parking_area_by_id(parking_area_id)

    def update_parking_area(
        self,
        parking_area_id: int,
        area_data: ParkingAreaUpdate
    ):
        if parking_area_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="parking_area_id must be positive."
            )

        data = area_data.model_dump(exclude_unset=True)

        if not data:
            raise HTTPException(
                status_code=400,
                detail="Request body cannot be empty."
            )

        if "name" in data:
            if not isinstance(data["name"], str) or not data["name"].strip():
                raise HTTPException(
                    status_code=400,
                    detail="name cannot be empty."
                )

        if "capacity" in data:
            capacity = data["capacity"]

            if capacity is not None and capacity < 0:
                raise HTTPException(
                    status_code=400,
                    detail="capacity must be non-negative."
                )

        if "geom" in data:
            self.validate_polygon(data["geom"])

        dao = ParkingAreaDAO()

        existing = dao.get_parking_area_by_id(parking_area_id)

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Parking area not found."
            )

        dao.update_parking_area(parking_area_id, area_data)

        return dao.get_parking_area_by_id(parking_area_id)

    def delete_parking_area(self, parking_area_id: int):
        if parking_area_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="parking_area_id must be positive."
            )

        dao = ParkingAreaDAO()

        existing = dao.get_parking_area_by_id(parking_area_id)

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Parking area not found."
            )

        deleted = dao.delete_parking_area(parking_area_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Parking area not found."
            )

        return {
            "message": "Parking area deleted successfully.",
            "parking_area_id": parking_area_id
        }
