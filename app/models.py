from pydantic import BaseModel
from typing import Optional

class Medication(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Aspirin",
                "description": "Pain reliever",
                "icon_url": "/medications/1/icon"
            }
        }

class Inventory(BaseModel):
    medication_id: int
    quantity: int
    shelf_id: str
    shelf_location: str

    class Config:
        schema_extra = {
            "example": {
                "medication_id": 1,
                "quantity": 100,
                "shelf_id": "A1",
                "shelf_location": "Shelf 1"
            }
        }