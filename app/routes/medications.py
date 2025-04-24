from fastapi import APIRouter, HTTPException, Header, Response, Query, UploadFile, File
from typing import Optional, List
import hashlib
import re
import os

from app.models import Medication, Inventory
from app.utils import serialize_response, generate_etag, IMAGE_DIR
from app.routes.inventory import inventory
from app.metrics import INVENTORY_GAUGE  # Updated import
from app.data import medications, inventory  # Import data and initialization
from fastapi.responses import Response as FastAPIResponse  # Fix import for FastAPIResponse

router = APIRouter()

@router.get("/", response_model=List[Medication], summary="Get all medications", description="Retrieve all medications or search medications by name using a regex pattern. Also supports querying for out-of-stock medications.")
def get_medications(
    regex: Optional[str] = Query(None, description="Regex pattern to search medication names"),
    out_of_stock: Optional[bool] = Query(None, description="Filter for out-of-stock medications"),
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml)")
):
    if out_of_stock:
        matched_medications = [med.dict() for med_id, med in medications.items() if inventory[med_id].quantity == 0]
        if not matched_medications:
            raise HTTPException(status_code=404, detail="No out-of-stock medications found")
        return serialize_response(matched_medications, accept)

    if regex:
        matched_medications = [med.dict() for med in medications.values() if re.search(regex, med.name)]
        if not matched_medications:
            raise HTTPException(status_code=404, detail="No medications found matching the search criteria")
        return serialize_response(matched_medications, accept)

    return serialize_response([med.dict() for med in medications.values()], accept)

@router.get("/{med_id}", response_model=Medication, summary="Get a medication by ID", description="Retrieve a specific medication by its ID.")
def get_medication(
    med_id: int, 
    response: Response, 
    if_none_match: Optional[str] = Header(None, description="ETag value to check against the current ETag"),
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml")
):
    medication = medications.get(med_id)
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    etag = generate_etag(medication)
    if if_none_match == etag:
        response.status_code = 304
        return
    
    response.headers["ETag"] = etag
    re: Response = serialize_response(medication.dict(), accept)
    re.headers["ETag"] = etag
    return re


@router.post("/", response_model=Medication, summary="Create a new medication", description="Create a new medication with the given details.")
def create_medication(
    medication: Medication, 
    response: Response,
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml)")
):
    if medication.id in medications:
        raise HTTPException(status_code=400, detail="Medication with this ID already exists")
    
    # Add medication to the medications dictionary
    medications[medication.id] = medication
    
    # Add a new inventory item for the medication
    inventory[medication.id] = Inventory(
        medication_id=medication.id, 
        quantity=0, 
        shelf_id="", 
        shelf_location=""
    )
    
    # Initialize the Prometheus metric for the new inventory item
    INVENTORY_GAUGE.labels(medication_id=medication.id, shelf_id="", shelf_location="").set(0)
    
    # Set the ETag header
    response.headers["ETag"] = generate_etag(medication)
    
    return serialize_response(medication.dict(), accept)

@router.put("/{med_id}", response_model=Medication, summary="Update a medication", description="Update an existing medication by its ID.")
def update_medication(
    med_id: int, 
    updated_medication: Medication, 
    response: Response, 
    if_match: Optional[str] = Header(None, description="ETag value to check against the current ETag"),
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml)")
):
    medication = medications.get(med_id)
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    current_etag = generate_etag(medication)
    if if_match != current_etag:
        raise HTTPException(status_code=412, detail="Precondition Failed")

    medications[med_id] = updated_medication
    response.headers["ETag"] = generate_etag(updated_medication)
    return serialize_response(updated_medication.dict(), accept)

@router.delete("/{med_id}", response_model=Medication, summary="Delete a medication", description="Delete a medication by its ID.")
def delete_medication(
    med_id: int,
    accept: str = Header("application/json", description="Specify the response format (application/json or application/xml)")
):
    medication = medications.pop(med_id, None)
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    inventory.pop(med_id, None)  # Also remove from inventory
    return serialize_response(medication.dict(), accept)

@router.post("/{med_id}/icon", response_model=dict, summary="Upload an icon for a medication", description="Upload an icon image for a specific medication. Supported file types are: jpg, jpeg, png, tiff.")
async def upload_medication_icon(med_id: int, file: UploadFile = File(...)):
    medication = medications.get(med_id)
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png", "tiff"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Supported types are: jpg, jpeg, png, tiff.")
    
    file_location = f"{IMAGE_DIR}/{med_id}.{file_extension}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    medication.icon_url = f"/medications/{med_id}/icon"
    return {"message": "Icon uploaded successfully", "icon_url": medication.icon_url}

@router.get("/{med_id}/icon", summary="Get the icon for a medication", description="Retrieve the uploaded icon image for a specific medication.")
async def get_image(med_id: int):
    for extension in ["jpg", "jpeg", "png", "tiff"]:
        file_location = f"{IMAGE_DIR}/{med_id}.{extension}"
        if os.path.exists(file_location):
            return FastAPIResponse(content=open(file_location, "rb").read(), media_type=f"image/{extension}")
    raise HTTPException(status_code=404, detail="Image not found")

@router.delete("/{med_id}/icon", summary="Delete the icon for a medication", description="Delete the uploaded icon image for a specific medication.")
async def delete_medication_icon(med_id: int):
    medication = medications.get(med_id)
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    # Check and delete the icon file
    for extension in ["jpg", "jpeg", "png", "tiff"]:
        file_location = f"{IMAGE_DIR}/{med_id}.{extension}"
        if os.path.exists(file_location):
            os.remove(file_location)
            return {"message": "Icon deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Icon not found")