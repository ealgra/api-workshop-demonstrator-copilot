from fastapi import APIRouter, HTTPException, Header, Response, Query, Body
from typing import Optional, List

from app.models import Inventory
from app.utils import serialize_response, generate_etag
from app.metrics import INVENTORY_GAUGE  # Updated import
from app.data import medications, inventory  # Import data and initialization

router = APIRouter()

@router.get("/", response_model=List[Inventory], summary="Get all inventory items", description="Retrieve all inventory items or filter for empty inventory items.")
def get_inventory(
    empty: Optional[bool] = Query(None, description="Filter for empty inventory items"),
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml)")
):
    if empty:
        empty_inventory = [inv.dict() for inv in inventory.values() if inv.quantity == 0]
        if not empty_inventory:
            raise HTTPException(status_code=404, detail="No empty inventory found")
        return serialize_response(empty_inventory, accept)
    return serialize_response([inv.dict() for inv in inventory.values()], accept)

@router.get("/{med_id}", response_model=Inventory, summary="Get an inventory item", description="Retrieve a specific inventory item by medication ID.")
def get_inventory_item(
    med_id: int, 
    if_none_match: Optional[str] = Header(None, description="ETag value to check against the current ETag"),
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml)")
):
    inv = inventory.get(med_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Inventory for this medication not found")
    
    etag = generate_etag(inv)
    if if_none_match == etag:
        return Response(status_code=304)
    
    response = serialize_response(inv.dict(), accept)
    response.headers["ETag"] = etag
    return response

@router.put("/{med_id}", response_model=Inventory, summary="Update an inventory item", description="Update the inventory details for a specific medication.")
def update_inventory(
    med_id: int, 
    updated_inventory: Inventory = Body(..., description="Updated inventory details"),  # Accept JSON payload
    if_match: Optional[str] = Header(None, description="ETag value to check against the current ETag"),
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml)")
):
    if med_id not in medications:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    inv = inventory.get(med_id)
    if inv:
        current_etag = generate_etag(inv)
        if if_match != current_etag:
            raise HTTPException(status_code=412, detail="Precondition Failed")
        # Update inventory details
        inv.quantity = updated_inventory.quantity
        inv.shelf_id = updated_inventory.shelf_id
        inv.shelf_location = updated_inventory.shelf_location
    else:
        # Create a new inventory item if it doesn't exist
        inventory[med_id] = updated_inventory
        inv = updated_inventory

    # Update Prometheus metric
    INVENTORY_GAUGE.labels(
        medication_id=med_id, 
        shelf_id=inv.shelf_id, 
        shelf_location=inv.shelf_location
    ).set(inv.quantity)
    
    # Generate new ETag and prepare response
    etag = generate_etag(inv)
    response = serialize_response(inv.dict(), accept)
    response.headers["ETag"] = etag
    return response