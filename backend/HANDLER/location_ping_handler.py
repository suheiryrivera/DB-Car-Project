from backend.DAO.location_ping_dao import LocationPingDAO, LocationPingCreate, LocationPingUpdate
from fastapi import HTTPException
from datetime import datetime

class LocationPingHandler:
    def _validate_rfc3339(self, ts_str: str):
        if not ts_str or not isinstance(ts_str, str):
            raise HTTPException(status_code=422, detail="Timestamp must be a string.")
        try:
            datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid RFC 3339 timestamp format.")

    def _validate_bbox(self, bbox: str):
        try:
            parts = [float(x) for x in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError()
            min_lon, min_lat, max_lon, max_lat = parts
            if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180 and -90 <= min_lat <= 90 and -90 <= max_lat <= 90):
                raise ValueError()
            if min_lon >= max_lon or min_lat >= max_lat:
                raise ValueError()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid bounding box parameters.")

    def get_all_pings(self, vehicle_id: int | None, from_ts: str | None, to_ts: str | None, bbox: str | None, limit: int, offset: int):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="Limit and offset must be non-negative integers.")
        if vehicle_id is not None and vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        if from_ts:
            self._validate_rfc3339(from_ts)
        if to_ts:
            self._validate_rfc3339(to_ts)
        if bbox:
            self._validate_bbox(bbox)

        dao = LocationPingDAO()
        items = dao.get_all_pings(vehicle_id=vehicle_id, from_ts=from_ts, to_ts=to_ts, bbox=bbox, limit=limit, offset=offset)
        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": len(items)
        }

    def get_ping_by_id(self, ping_id: int):
        if ping_id <= 0:
            raise HTTPException(status_code=400, detail="ping_id must be a positive integer.")
        dao = LocationPingDAO()
        ping = dao.get_ping_by_id(ping_id)
        if not ping:
            raise HTTPException(status_code=404, detail="Location ping not found.")
        return ping

    def create_ping(self, data: LocationPingCreate):
        dao = LocationPingDAO()
        if not dao.vehicle_exists(data.vehicle_id):
            raise HTTPException(status_code=404, detail="vehicle_id does not exist.")
        self._validate_rfc3339(data.ts)
        
        if data.geom.get("type") != "Point":
            raise HTTPException(status_code=400, detail="Geometry must be a valid Point.")
        if data.speed_kph is not None and data.speed_kph < 0:
            raise HTTPException(status_code=400, detail="speed_kph must be >= 0.")
        if data.heading_deg is not None and not (0 <= data.heading_deg < 360):
            raise HTTPException(status_code=400, detail="heading_deg must be within [0, 360).")

        new_id = dao.create_ping(data)
        return dao.get_ping_by_id(new_id)

    def update_ping(self, ping_id: int, data: LocationPingUpdate):
        if ping_id <= 0:
            raise HTTPException(status_code=400, detail="ping_id must be a positive integer.")
        dao = LocationPingDAO()
        if not dao.get_ping_by_id(ping_id):
            raise HTTPException(status_code=404, detail="ping_id does not exist.")

        fields = data.model_dump(exclude_unset=True)
        if not fields:
            raise HTTPException(status_code=400, detail="Empty patch payload.")

        if "vehicle_id" in fields:
            if not dao.vehicle_exists(fields["vehicle_id"]):
                raise HTTPException(status_code=404, detail="Referenced vehicle_id does not exist.")
        if "ts" in fields and fields["ts"]:
            self._validate_rfc3339(fields["ts"])
        if "geom" in fields and fields["geom"] and fields["geom"].get("type") != "Point":
            raise HTTPException(status_code=400, detail="Geometry must be a valid Point.")
        if "speed_kph" in fields and fields["speed_kph"] is not None and fields["speed_kph"] < 0:
            raise HTTPException(status_code=400, detail="speed_kph must be >= 0.")
        if "heading_deg" in fields and fields["heading_deg"] is not None and not (0 <= fields["heading_deg"] < 360):
            raise HTTPException(status_code=400, detail="heading_deg must be within [0, 360).")

        return dao.update_ping(ping_id, data)

    def delete_ping(self, ping_id: int):
        if ping_id <= 0:
            raise HTTPException(status_code=400, detail="ping_id must be a positive integer.")
        dao = LocationPingDAO()
        if not dao.get_ping_by_id(ping_id):
            raise HTTPException(status_code=404, detail="ping_id does not exist.")
        dao.delete_ping(ping_id)
        return {"message": "Location ping deleted successfully.", "ping_id": ping_id}

    def get_vehicle_pings(self, vehicle_id: int, limit: int, offset: int, from_ts: str | None, to_ts: str | None):
        if vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        dao = LocationPingDAO()
        if not dao.vehicle_exists(vehicle_id):
            raise HTTPException(status_code=404, detail="vehicle_id does not exist.")
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative integers.")
        if from_ts:
            self._validate_rfc3339(from_ts)
        if to_ts:
            self._validate_rfc3339(to_ts)

        items = dao.get_all_pings(vehicle_id=vehicle_id, from_ts=from_ts, to_ts=to_ts, limit=limit, offset=offset)
        return {
            "vehicle_id": vehicle_id,
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": len(items)
        }