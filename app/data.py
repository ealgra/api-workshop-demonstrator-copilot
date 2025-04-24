from app.models import Medication, Inventory

# In-memory storage for medications
medications = {}

# In-memory storage for inventory
inventory = {}

# Demo data initialization
def initialize_demo_data():
    demo_medications = [
        Medication(id=1, name="Aspirin", description="Pain reliever"),
        Medication(id=2, name="Ibuprofen", description="Anti-inflammatory"),
        Medication(id=3, name="Paracetamol", description="Fever reducer"),
    ]

    demo_inventory = [
        Inventory(medication_id=1, quantity=100, shelf_id="A1", shelf_location="Shelf 1"),
        Inventory(medication_id=2, quantity=0, shelf_id="A2", shelf_location="Shelf 2"),
        Inventory(medication_id=3, quantity=50, shelf_id="A3", shelf_location="Shelf 3"),
    ]

    for med in demo_medications:
        medications[med.id] = med

    for inv in demo_inventory:
        inventory[inv.medication_id] = inv


initialize_demo_data()