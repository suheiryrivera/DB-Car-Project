from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from backend.API.DB import get_connection
from backend.DAO.vehicle_dao import VehicleCreate, VehicleUpdate
from backend.HANDLER.vehicle_handler import VehicleHandler
from backend.DAO.driver_dao import DriverCreate, DriverUpdate
from backend.HANDLER.driver_handler import DriverHandler

app = FastAPI()
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    status_code = 400

    if request.url.path.startswith("/api/v1/drivers"):
        for error in errors:
            error_type = error.get("type", "")
            location = error.get("loc", ())

            if error_type == "json_invalid":
                status_code = 400
                break

            if location and location[0] == "body":
                if error_type not in (
                    "model_attributes_type",
                    "model_type",
                    "dict_type"
                ):
                    status_code = 422

    return JSONResponse(
        status_code=status_code,
        content={"detail": jsonable_encoder(errors)}
    )

@app.get("/api/v1/test-db")
def test_database():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_database(), version();")
                result = cursor.fetchone()

        return {
            "status": "connected",
            "database": result[0],
            "postgresql_version": result[1]
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

#vehicle stuff -----

@app.get("/api/v1/vehicles")
async def get_all_vehicles(
    limit: int = 20, 
    offset: int = 0, 
    status: str | int | None = None, 
    plate_number: str | None = None
):
    return VehicleHandler().get_all_vehicles(
        limit=limit, 
        offset=offset, 
        status=status, 
        plate_number=plate_number
    )

@app.post("/api/v1/vehicles", status_code=201)
async def create_vehicle(new_vehicle: VehicleCreate):
    return VehicleHandler().create_vehicle(new_vehicle)

@app.get("/api/v1/vehicles/{vehicle_id}")
async def get_vehicle_by_id(vehicle_id: int):
    return VehicleHandler().get_vehicle_by_id(vehicle_id)

@app.put("/api/v1/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: int, vehicle_data: VehicleUpdate):
    return VehicleHandler().update_vehicle(vehicle_id, vehicle_data)

@app.delete("/api/v1/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int):
    return VehicleHandler().delete_vehicle(vehicle_id)

@app.get("/api/v1/vehicles/{vehicle_id}/current-location")
async def get_vehicle_current_location(vehicle_id: int):
    return VehicleHandler().get_vehicle_current_location(vehicle_id)

#driver stuff -----

@app.get("/api/v1/drivers")
async def get_all_drivers(
    limit: int = 20, 
    offset: int = 0, 
    name: str | None = None, 
    license_number: str | None = None
):
    return DriverHandler().get_all_drivers(
        limit=limit, 
        offset=offset, 
        name=name, 
        license_number=license_number
    )

@app.post("/api/v1/drivers", status_code=201)
async def create_driver(new_driver: DriverCreate):
    return DriverHandler().create_driver(new_driver)

@app.get("/api/v1/drivers/{driver_id}")
async def get_driver_by_id(driver_id: int):
    return DriverHandler().get_driver_by_id(driver_id)

@app.put("/api/v1/drivers/{driver_id}")
async def update_driver(driver_id: int, driver_data: DriverUpdate):
    return DriverHandler().update_driver(driver_id, driver_data)

@app.delete("/api/v1/drivers/{driver_id}")
async def delete_driver(driver_id: int):
    return DriverHandler().delete_driver(driver_id)