from backend.DAO.trip_dao import TripDAO, TripCreate, TripUpdate
from fastapi import HTTPException
from datetime import datetime

class TripHandler:
    def _validate_rfc3339(self, ts_str: str):
        if not ts_str or not isinstance(ts_str, str):
            raise HTTPException(status_code=422, detail="Timestamp must be a string.")
        try:
            return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid RFC 3339 timestamp format.")

    def get_all_trips(self, vehicle_id: int | None, from_ts: str | None, to_ts: str | None, limit: int, offset: int):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="Limit and offset must be non-negative integers.")
        if vehicle_id is not None and vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        if from_ts:
            self._validate_rfc3339(from_ts)
        if to_ts:
            self._validate_rfc3339(to_ts)

        dao = TripDAO()
        items = dao.get_all_trips(vehicle_id=vehicle_id, from_ts=from_ts, to_ts=to_ts, limit=limit, offset=offset)
        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": len(items)
        }

    def get_trip_by_id(self, trip_id: int):
        if trip_id <= 0:
            raise HTTPException(status_code=400, detail="trip_id must be a positive integer.")
        dao = TripDAO()
        trip = dao.get_trip_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found.")
        return trip

    def create_trip(self, data: TripCreate):
        dao = TripDAO()
        if not dao.vehicle_exists(data.vehicle_id):
            raise HTTPException(status_code=404, detail="vehicle_id does not exist.")
        
        dt_start = self._validate_rfc3339(data.start_ts)
        dt_end = self._validate_rfc3339(data.end_ts)
        if dt_end <= dt_start:
            raise HTTPException(status_code=400, detail="end_ts must be later than start_ts.")

        if data.start_geom and data.start_geom.get("type") != "Point":
            raise HTTPException(status_code=400, detail="start_geom must be a valid Point.")
        if data.end_geom and data.end_geom.get("type") != "Point":
            raise HTTPException(status_code=400, detail="end_geom must be a valid Point.")
        if data.distance_km is not None and data.distance_km < 0:
            raise HTTPException(status_code=400, detail="distance_km must be >= 0.")

        new_id = dao.create_trip(data)
        return dao.get_trip_by_id(new_id)

    def update_trip(self, trip_id: int, data: TripUpdate):
        if trip_id <= 0:
            raise HTTPException(status_code=400, detail="trip_id must be a positive integer.")
        dao = TripDAO()
        current = dao.get_trip_by_id(trip_id)
        if not current:
            raise HTTPException(status_code=404, detail="trip_id does not exist.")

        fields = data.model_dump(exclude_unset=True)
        if not fields:
            raise HTTPException(status_code=400, detail="Empty patch payload.")

        if "vehicle_id" in fields:
            if not dao.vehicle_exists(fields["vehicle_id"]):
                raise HTTPException(status_code=404, detail="Referenced vehicle_id does not exist.")

        start_str = fields.get("start_ts", current["start_ts"])
        end_str = fields.get("end_ts", current["end_ts"])
        if "start_ts" in fields or "end_ts" in fields:
            dt_start = self._validate_rfc3339(start_str)
            dt_end = self._validate_rfc3339(end_str)
            if dt_end <= dt_start:
                raise HTTPException(status_code=422, detail="end_ts must be later than start_ts.")

        if "distance_km" in fields and fields["distance_km"] is not None and fields["distance_km"] < 0:
            raise HTTPException(status_code=400, detail="distance_km must be >= 0.")

        return dao.update_trip(trip_id, data)

    def delete_trip(self, trip_id: int):
        if trip_id <= 0:
            raise HTTPException(status_code=400, detail="trip_id must be a positive integer.")
        dao = TripDAO()
        if not dao.get_trip_by_id(trip_id):
            raise HTTPException(status_code=404, detail="trip_id does not exist.")
        dao.delete_trip(trip_id)
        return {"message": "Trip deleted successfully.", "trip_id": trip_id}

    def get_vehicle_trips(self, vehicle_id: int, limit: int, offset: int, from_ts: str | None, to_ts: str | None):
        if vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        dao = TripDAO()
        if not dao.vehicle_exists(vehicle_id):
            raise HTTPException(status_code=404, detail="vehicle_id does not exist.")
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative integers.")
        if from_ts:
            self._validate_rfc3339(from_ts)
        if to_ts:
            self._validate_rfc3339(to_ts)

        items = dao.get_all_trips(vehicle_id=vehicle_id, from_ts=from_ts, to_ts=to_ts, limit=limit, offset=offset)
        return {
            "vehicle_id": vehicle_id,
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": len(items)
        }