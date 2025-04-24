import pytest
from httpx import AsyncClient
from app.main import app

BASE_URL = "http://127.0.0.1:8000"  # Single variable for base_url

@pytest.mark.asyncio
async def test_get_inventory():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.get("/inventory/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_update_inventory_with_correct_etag():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        # Step 1: Get the current inventory item to retrieve the ETag
        response = await client.get("/inventory/1")
        assert response.status_code == 200
        etag = response.headers.get("ETag")
        assert etag is not None

        # Step 2: Update the inventory item using the retrieved ETag
        updated_inventory = {
            "medication_id": 1,  # Add medication_id to the updated inventory item
            "quantity": 200,
            "shelf_id": "B1",
            "shelf_location": "Shelf 2"
        }
        response = await client.put(
            "/inventory/1",
            json=updated_inventory,
            headers={"If-Match": etag}
        )
        assert response.status_code == 200
        assert response.json()["quantity"] == 200
        assert response.json()["shelf_id"] == "B1"
        assert response.json()["shelf_location"] == "Shelf 2"

@pytest.mark.asyncio
async def test_update_inventory_with_incorrect_etag():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        # Step 1: Use an incorrect ETag value
        incorrect_etag = "incorrect-etag"

        # Step 2: Attempt to update the inventory item with the incorrect ETag
        updated_inventory = {
            "medication_id": 1,  # Add medication_id to the updated inventory item
            "quantity": 300,
            "shelf_id": "C1",
            "shelf_location": "Shelf 3"
        }
        response = await client.put(
            "/inventory/1",
            json=updated_inventory,
            headers={"If-Match": incorrect_etag}
        )
        assert response.status_code == 412  # Precondition Failed
        assert response.json()["detail"] == "Precondition Failed"

@pytest.mark.asyncio
async def test_delete_inventory_not_allowed():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        # Attempt to delete an inventory item
        response = await client.delete("/inventory/1")
        assert response.status_code == 405  # Method Not Allowed
        assert response.json()["detail"] == "Method Not Allowed"
