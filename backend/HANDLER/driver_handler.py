from backend.DAO.driver_dao import DriverDAO
from backend.DAO.driver_dao import DriverCreate
from backend.DAO.driver_dao import DriverUpdate
from fastapi import HTTPException
from datetime import datetime
from psycopg2.errors import UniqueViolation

class DriverHandler:
    def _validate_rfc3339(self, ts_str: str):
        if not ts_str or not isinstance(ts_str, str):
            raise HTTPException(status_code=422, detail="Timestamp must be a string.")
        if not ('Z' in ts_str or '+' in ts_str or '-' in ts_str[10:]):
            raise HTTPException(status_code=422, detail="Timestamp must include a valid RFC 3339.")
        try:
            datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid RFC 3339 timestamp format.")

    def get_all_drivers(self, limit: int = 20, offset: int = 0, name: str | None = None, license_number: str | None = None):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="Limit and offset must be a positive integer.")
        dao = DriverDAO()
        items = dao.get_all_drivers(limit=limit, offset=offset, name=name, license_number=license_number)
        count = dao.get_drivers_count(name=name, license_number=license_number)
        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_driver_by_id(self, driver_id: int):
        if driver_id <= 0:
            raise HTTPException(status_code=400, detail="driver_id must be a positive integer.")
        dao = DriverDAO()
        result = dao.get_driver_by_id(driver_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Driver not found")
        return result

    def create_driver(self, new_driver: DriverCreate):
        if not new_driver.first_name or not new_driver.first_name.strip():
            raise HTTPException(status_code=422, detail="first_name cannot be empty.")
        if not new_driver.last_name or not new_driver.last_name.strip():
            raise HTTPException(status_code=422, detail="last_name cannot be empty.")
        if not new_driver.license_number or not new_driver.license_number.strip():
            raise HTTPException(status_code=422, detail="license_number cannot be empty.")
        self._validate_rfc3339(new_driver.hired_at)

        dao = DriverDAO()
        if dao.license_exists(new_driver.license_number.strip()):
            raise HTTPException(status_code=409, detail="license_number already exists.")
        try:
            driver_id = dao.create_driver(new_driver)
            return dao.get_driver_by_id(driver_id)
        except UniqueViolation:
            raise HTTPException(
                status_code=409,
                detail="license_number already exists."
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_driver(self, driver_id: int, driver_data: DriverUpdate):
        if driver_id <= 0:
            raise HTTPException(status_code=400, detail="driver_id must be a positive integer.")
        
        update_dict = driver_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="Request body cannot be empty.")

        for key in ["first_name", "last_name", "license_number"]:
            if key in update_dict:
                val = update_dict[key]
                if val is None or not str(val).strip():
                    raise HTTPException(status_code=422, detail=f"{key} cannot be null or empty.")

        if "hired_at" in update_dict:
            if update_dict["hired_at"] is None:
                raise HTTPException(status_code=422, detail="hired_at cannot be null.")
            self._validate_rfc3339(update_dict["hired_at"])

        dao = DriverDAO()
        temp = dao.get_driver_by_id(driver_id)
        if temp is None:
            raise HTTPException(status_code=404, detail="Driver not found")

        if "license_number" in update_dict:
            lic = update_dict["license_number"]
            if dao.license_exists(lic.strip(), exclude_id=driver_id):
                raise HTTPException(status_code=409, detail="Updated license_number conflicts with another driver.")

        try:
            return dao.update_driver(driver_id, driver_data)
        except UniqueViolation:
            raise HTTPException(
                status_code=409,
                detail="Updated license_number conflicts with another driver."
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def delete_driver(self, driver_id: int):
        if driver_id <= 0:
            raise HTTPException(status_code=400, detail="driver_id must be a positive integer.")
        dao = DriverDAO()
        temp = dao.get_driver_by_id(driver_id)
        if temp is None:
            raise HTTPException(status_code=404, detail="Driver not found")
        result = dao.delete_driver(driver_id)
        if not result:
            raise HTTPException(status_code=409, detail="Deletion is blocked by vehicle assignment foreign key constraints.")
        return {"message": "Driver deleted successfully.", "driver_id": driver_id}