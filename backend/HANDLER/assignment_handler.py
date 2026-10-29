from backend.DAO.assignment_dao import VehicleAssignmentDAO
from backend.DAO.assignment_dao import VehicleAssignment
from backend.DAO.assignment_dao import VehicleAssignmentUpdate
from fastapi import HTTPException
from typing import Optional
from datetime import timezone

class VehicleAssignmentHandler:
    def get_all_assignments(self, vehicle_id: Optional[int] = None, driver_id: Optional[int] = None, active: Optional[bool] = None, limit: int = 20, offset: int = 0):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="Limit and offset must be non-negative integers.")
        if vehicle_id is not None and vehicle_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id must be a positive integer.")
        if driver_id is not None and driver_id <= 0:
            raise HTTPException(status_code=400, detail="driver_id must be a positive integer.")

        dao = VehicleAssignmentDAO()
        return dao.get_all_assignments(vehicle_id=vehicle_id, driver_id=driver_id, active=active, limit=limit, offset=offset)

    def get_assignment_by_id(self, assignment_id: int):
        if assignment_id <= 0:
            raise HTTPException(status_code=400, detail="assignment_id must be a positive integer.")
        dao = VehicleAssignmentDAO()
        result = dao.get_assignment_by_id(assignment_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Vehicle assignment not found.")
        return result

    def create_assignment(self, new_assignment: VehicleAssignment):
        if new_assignment.vehicle_id <= 0 or new_assignment.driver_id <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id and driver_id must be positive integers.")

        dao = VehicleAssignmentDAO()
        
        if not dao.vehicle_exists(new_assignment.vehicle_id):
            raise HTTPException(status_code=404, detail="Referenced vehicle_id does not exist.")
        if not dao.driver_exists(new_assignment.driver_id):
            raise HTTPException(status_code=404, detail="Referenced driver_id does not exist.")
            
        # Normalize to UTC for PostgreSQL TIMESTAMP columns.
        new_assignment.assigned_from = new_assignment.assigned_from.astimezone(timezone.utc).replace(tzinfo=None)
        if new_assignment.assigned_to is not None:
            new_assignment.assigned_to = new_assignment.assigned_to.astimezone(timezone.utc).replace(tzinfo=None)
            if new_assignment.assigned_to <= new_assignment.assigned_from:
                raise HTTPException(status_code=422, detail="assigned_to must be later than assigned_from.")

        assignment_id = dao.create_assignment(new_assignment)
        new_assignment.assignment_id = assignment_id
        return new_assignment

    def update_assignment(self, assignment_id: int, assignment_data: VehicleAssignmentUpdate):
        if assignment_id <= 0:
            raise HTTPException(status_code=400, detail="assignment_id must be a positive integer.")

        update_dict = assignment_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(status_code=400, detail="Request body cannot be empty.")

        for field in ["vehicle_id", "driver_id", "assigned_from"]:
            if field in update_dict and update_dict[field] is None:
                raise HTTPException(status_code=422, detail=f"{field} cannot be null.")
        dao = VehicleAssignmentDAO()
        existing = dao.get_assignment_by_id(assignment_id)

        if existing is None:
            raise HTTPException(status_code=404, detail="Vehicle assignment not found.")
        updated_data = existing.model_dump()
        updated_data.update(update_dict)

        # Only convert newly provided timestamps; existing DB values are already UTC.
        for field in ["assigned_from", "assigned_to"]:
            if field in update_dict and updated_data[field] is not None:
                updated_data[field] = updated_data[field].astimezone(timezone.utc).replace(tzinfo=None)

        if updated_data["vehicle_id"] <= 0 or updated_data["driver_id"] <= 0:
            raise HTTPException(status_code=400, detail="vehicle_id and driver_id must be positive integers.")

        if not dao.vehicle_exists(updated_data["vehicle_id"]):
            raise HTTPException(status_code=404, detail="Referenced vehicle_id does not exist.")

        if not dao.driver_exists(updated_data["driver_id"]):
            raise HTTPException(status_code=404, detail="Referenced driver_id does not exist.")

        if (updated_data["assigned_to"] is not None and
                updated_data["assigned_to"] <= updated_data["assigned_from"]):
            raise HTTPException(status_code=422, detail="The resulting assignment interval is invalid.")

        return dao.update_assignment(assignment_id, VehicleAssignment(**updated_data)
        )

    def delete_assignment(self, assignment_id: int):
        if assignment_id <= 0:
            raise HTTPException(status_code=400, detail="assignment_id must be a positive integer.")
        dao = VehicleAssignmentDAO()
        existing = dao.get_assignment_by_id(assignment_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="assignment_id does not exist.")
        
        result = dao.delete_assignment(assignment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Vehicle assignment not found.")
        return {"message": "Vehicle assignment deleted successfully.", "assignment_id": assignment_id}