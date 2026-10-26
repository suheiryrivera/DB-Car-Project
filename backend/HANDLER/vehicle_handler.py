from backend.DAO.vehicle_dao import VehicleDAO
from backend.DAO.vehicle_dao import VehicleCreate
from backend.DAO.vehicle_dao import VehicleUpdate
from fastapi import HTTPException
from fastapi import Response
from psycopg2.errors import UniqueViolation

class VehicleHandler:
    def get_all_vehicles(self, limit: int = 20, offset: int = 0, status: str | int | None = None, plate_number: str | None = None):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="Limit and offset must be non-negative integers.")
        dao = VehicleDAO()
        items = dao.get_all_vehicles(limit=limit, offset=offset, status=status, plate_number=plate_number)
        count = dao.get_vehicles_count(status=status, plate_number=plate_number)
        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_vehicle_by_id(self, vehicle_id: int):
        if vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        dao = VehicleDAO()
        result = dao.get_vehicle_by_id(vehicle_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return result

    def get_vehicle_current_location(self, vehicle_id: int):
        if vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        dao = VehicleDAO()
        res = dao.get_vehicle_current_location(vehicle_id)
        
        if not res["exists"]:
            raise HTTPException(status_code=404, detail="vehicle_id does not exist.")
        if res["ping"] is None:
            return Response(status_code=204)
        return res["ping"]

    def create_vehicle(self, new_vehicle: VehicleCreate):
        if not new_vehicle.plate_number or not new_vehicle.plate_number.strip():
            raise HTTPException(status_code=400, detail="plate_number cannot be empty.")
        if new_vehicle.year is not None and not (1950 <= new_vehicle.year <= 2100):
            raise HTTPException(status_code=400, detail="Year must be between 1950 and 2100.")
        
        dao = VehicleDAO()
        if dao.plate_exists(new_vehicle.plate_number.strip()):
            raise HTTPException(status_code=409, detail="plate_number already exists.")
        try:
            vehicle_id = dao.create_vehicle(new_vehicle)
            return dao.get_vehicle_by_id(vehicle_id)
        except UniqueViolation:
            raise HTTPException(
        status_code=409,
        detail="plate_number already exists."
    )
        except Exception as e:
            err_msg = str(e).lower()
            if "violates foreign key constraint" in err_msg:
                raise HTTPException(status_code=404, detail="Referenced vehicle_type_id or vehicle_status_id does not exist.")
            raise HTTPException(status_code=400, detail=str(e))

    def update_vehicle(self, vehicle_id: int, vehicle_data: VehicleUpdate):
        if vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        update_dict = vehicle_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="Request body cannot be empty.")

        if "vehicle_type_id" in update_dict and update_dict["vehicle_type_id"] is None:
            raise HTTPException(status_code=400, detail="vehicle_type_id cannot be null.")
        if "vehicle_status_id" in update_dict and update_dict["vehicle_status_id"] is None:
            raise HTTPException(status_code=400, detail="vehicle_status_id cannot be null.")

        dao = VehicleDAO()
        temp = dao.get_vehicle_by_id(vehicle_id)
        if temp is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        if "plate_number" in update_dict:
            plate = update_dict["plate_number"]
            if not plate or not plate.strip():
                raise HTTPException(status_code=400, detail="plate_number cannot be empty.")
            if dao.plate_exists(plate.strip(), exclude_id=vehicle_id):
                raise HTTPException(status_code=409, detail="Updated plate_number conflicts with another vehicle.")

        if vehicle_data.year is not None and not (1950 <= vehicle_data.year <= 2100):
            raise HTTPException(status_code=400, detail="Year must be between 1950 and 2100.")

        try:
            result = dao.update_vehicle(vehicle_id, vehicle_data)
            return result
        except UniqueViolation:
            raise HTTPException(
        status_code=409,
        detail="plate_number already exists."
    )
        except Exception as e:
            err_msg = str(e).lower()
            if "violates foreign key constraint" in err_msg:
                raise HTTPException(status_code=404, detail="Referenced foreign key does not exist.")
            raise HTTPException(status_code=400, detail=str(e))

    def delete_vehicle(self, vehicle_id: int):
        if vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        dao = VehicleDAO()
        temp = dao.get_vehicle_by_id(vehicle_id)
        if temp is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        result = dao.delete_vehicle(vehicle_id)
        if not result:
            raise HTTPException(status_code=409, detail="Deletion is blocked by foreign key constraints.")
        else:
            return {"message": "Vehicle deleted successfully.", "vehicle_id": vehicle_id}