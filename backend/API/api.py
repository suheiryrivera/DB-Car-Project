from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from backend.API.DB import get_connection
from backend.DAO.vehicle_dao import VehicleCreate, VehicleUpdate
from backend.HANDLER.vehicle_handler import VehicleHandler

app = FastAPI()
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": jsonable_encoder(exc.errors())}
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