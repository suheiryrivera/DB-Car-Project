

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from backend.DAO.road_segment_dao import (
    RoadSegmentDAO,
    RoadSegmentCreate,
    RoadSegmentUpdate
)
import math


class RoadSegmentHandler:


    def get_road_segment_by_id(self, road_id: int):
        if road_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="road_id must be a positive integer."
            )

        dao = RoadSegmentDAO()
        result = dao.get_road_segment_by_id(road_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Road segment not found."
            )

        return result


    def get_all_road_segments(
        self,
        limit: int = 20,
        offset: int = 0,
        name: str | None = None,
        min_speed_kph: int | None = None,
        max_speed_kph: int | None = None,
        bbox: str | None = None
    ):
        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid pagination parameters."
            )

        if min_speed_kph is not None and min_speed_kph < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid minimum speed."
            )

        if max_speed_kph is not None and max_speed_kph < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid maximum speed."
            )

        if (
            min_speed_kph is not None
            and max_speed_kph is not None
            and min_speed_kph > max_speed_kph
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid speed range."
            )

        bbox_values = None

        if bbox is not None:
            try:
                bbox_values = tuple(float(x) for x in bbox.split(","))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid bbox format."
                )

            if len(bbox_values) != 4:
                raise HTTPException(
                    status_code=400,
                    detail="bbox must contain four values."
                )

            min_lon, min_lat, max_lon, max_lat = bbox_values

            if (
                not all(math.isfinite(x) for x in bbox_values)
                or not -180 <= min_lon < max_lon <= 180
                or not -90 <= min_lat < max_lat <= 90
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid bbox coordinates."
                )

        dao = RoadSegmentDAO()

        items = dao.get_all_road_segments(
            limit=limit,
            offset=offset,
            name=name,
            min_speed_kph=min_speed_kph,
            max_speed_kph=max_speed_kph,
            bbox=bbox_values
        )

        count = dao.get_road_segments_count(
            name=name,
            min_speed_kph=min_speed_kph,
            max_speed_kph=max_speed_kph,
            bbox=bbox_values
        )

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def create_road_segment(self, new_road: RoadSegmentCreate):
        if not new_road.name.strip():
            raise HTTPException(
                status_code=400,
                detail="name cannot be empty."
            )

        if (
            new_road.speed_limit_kph is not None
            and new_road.speed_limit_kph < 0
        ):
            raise HTTPException(
                status_code=400,
                detail="speed_limit_kph must be non-negative."
            )

        if new_road.direction not in (None, "both", "forward"):
            raise HTTPException(
                status_code=400,
                detail="direction must be both or forward."
            )

        geom = new_road.geom

        if geom.get("type") != "LineString":
            raise HTTPException(
                status_code=400,
                detail="Geometry must be a LineString."
            )

        coordinates = geom.get("coordinates")

        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise HTTPException(
                status_code=400,
                detail="LineString requires at least two points."
            )

        for point in coordinates:
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
                    detail="Invalid geometry coordinates."
                )

            lon, lat = point

            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise HTTPException(
                    status_code=400,
                    detail="Coordinates outside valid range."
                )

        if all(point == coordinates[0] for point in coordinates):
            raise HTTPException(
                status_code=400,
                detail="LineString must contain distinct points."
            )

        dao = RoadSegmentDAO()
        road_id = dao.create_road_segment(new_road)

        return dao.get_road_segment_by_id(road_id)



    def update_road_segment(
        self, road_id: int, road_data: RoadSegmentUpdate
    ):
        if road_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="road_id must be a positive integer."
            )

        data = road_data.model_dump(exclude_unset=True)

        if not data:
            raise HTTPException(
                status_code=400,
                detail="Request body cannot be empty."
            )

        if "name" in data:
            name = data["name"]

            if not isinstance(name, str) or not name.strip():
                raise HTTPException(
                    status_code=400,
                    detail="name cannot be empty."
                )

        if "speed_limit_kph" in data:
            speed = data["speed_limit_kph"]

            if speed is not None and speed < 0:
                raise HTTPException(
                    status_code=400,
                    detail="speed_limit_kph must be non-negative."
                )

        if "direction" in data:
            if data["direction"] not in ("both", "forward"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid direction."
                )

        if "geom" in data:
            geom = data["geom"]

            if not isinstance(geom, dict):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid geometry."
                )

            if geom.get("type") != "LineString":
                raise HTTPException(
                    status_code=400,
                    detail="Geometry must be a LineString."
                )

            coordinates = geom.get("coordinates")

            if not isinstance(coordinates, list) or len(coordinates) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="LineString requires at least two points."
                )

            for point in coordinates:
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
                        detail="Invalid coordinates."
                    )

                lon, lat = point

                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    raise HTTPException(
                        status_code=400,
                        detail="Coordinates outside valid range."
                    )

            if all(point == coordinates[0] for point in coordinates):
                raise HTTPException(
                    status_code=400,
                    detail="LineString must contain distinct points."
                )

        dao = RoadSegmentDAO()

        existing = dao.get_road_segment_by_id(road_id)

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Road segment not found."
            )

        dao.update_road_segment(road_id, road_data)

        return dao.get_road_segment_by_id(road_id)

    def delete_road_segment(self, road_id: int):
        if road_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="road_id must be a positive integer."
            )

        dao = RoadSegmentDAO()

        existing = dao.get_road_segment_by_id(road_id)

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Road segment not found."
            )

        deleted = dao.delete_road_segment(road_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Road segment not found."
            )

        return {
            "message": "Road segment deleted successfully.",
            "road_id": road_id
        }


    def get_road_segments_geojson(
        self,
        limit: int = 15000,
        offset: int = 0,
        name: str | None = None,
        min_speed_kph: int | None = None,
        max_speed_kph: int | None = None
    ):
        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=422,
                detail="Invalid pagination parameters."
            )

        if min_speed_kph is not None and min_speed_kph < 0:
            raise HTTPException(
                status_code=422,
                detail="Invalid minimum speed."
            )

        if max_speed_kph is not None and max_speed_kph < 0:
            raise HTTPException(
                status_code=422,
                detail="Invalid maximum speed."
            )

        if (
            min_speed_kph is not None
            and max_speed_kph is not None
            and min_speed_kph > max_speed_kph
        ):
            raise HTTPException(
                status_code=400,
                detail="Minimum speed cannot exceed maximum speed."
            )

        dao = RoadSegmentDAO()

        roads = dao.get_road_segments_geojson(
            limit=limit,
            offset=offset,
            name=name,
            min_speed_kph=min_speed_kph,
            max_speed_kph=max_speed_kph
        )

        count = dao.get_road_segments_count(
            name=name,
            min_speed_kph=min_speed_kph,
            max_speed_kph=max_speed_kph
        )

        features = []

        for road in roads:
            geometry = road.pop("geom")

            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": road
            }

            features.append(feature)

        response = {
            "type": "FeatureCollection",
            "count": count,
            "limit": limit,
            "offset": offset,
            "features": features
        }

        return JSONResponse(
            content=response,
            media_type="application/geo+json"
        )

