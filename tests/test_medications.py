import pytest
from httpx import AsyncClient
from app.main import app
import base64
from fastapi.testclient import TestClient

BASE_URL = "http://127.0.0.1:8000"  # Single variable for base_url

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_medications():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.get("/medications/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_medication_by_id():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.get("/medications/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_create_medication():
    new_medication = {
        "id": 4,
        "name": "Amoxicillin",
        "description": "Antibiotic"
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post("/medications/", json=new_medication)
    assert response.status_code == 200
    assert response.json()["id"] == 4

@pytest.mark.asyncio
async def test_update_medication_with_correct_etag():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        # Step 1: Get the current medication to retrieve the ETag
        response = await client.get("/medications/1")
        assert response.status_code == 200
        etag = response.headers.get("ETag")
        assert etag is not None

        # Step 2: Update the medication using the correct ETag
        updated_medication = {
            "id": 1,
            "name": "Aspirin Updated",
            "description": "Updated description"
        }
        response = await client.put(
            "/medications/1",
            json=updated_medication,
            headers={"If-Match": etag}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Aspirin Updated"
        assert response.json()["description"] == "Updated description"

@pytest.mark.asyncio
async def test_update_medication_with_incorrect_etag():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        # Use an incorrect ETag value
        incorrect_etag = "incorrect-etag"

        # Attempt to update the medication with the incorrect ETag
        updated_medication = {
            "id": 1,
            "name": "Aspirin Updated",
            "description": "Updated description"
        }
        response = await client.put(
            "/medications/1",
            json=updated_medication,
            headers={"If-Match": incorrect_etag}
        )
        assert response.status_code == 412  # Precondition Failed
        assert response.json()["detail"] == "Precondition Failed"

@pytest.mark.asyncio
async def test_delete_medication():
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        # Step 1: Create a new medication to delete
        new_medication = {
            "id": 5,
            "name": "Test Medication",
            "description": "Test Description"
        }
        create_response = await client.post("/medications/", json=new_medication)
        assert create_response.status_code == 200
        assert create_response.json()["id"] == 5

        # Step 2: Delete the newly created medication
        delete_response = await client.delete("/medications/5")
        assert delete_response.status_code == 200
        assert delete_response.json()["id"] == 5

        # Step 3: Attempt to delete the medication again to ensure idempotency
        second_delete_response = await client.delete("/medications/5")
        assert second_delete_response.status_code == 404  # Medication no longer exists
        assert second_delete_response.json()["detail"] == "Medication not found"

def test_upload_medication_icon():
    # Create a sample base64-encoded image
    image_data = base64.b64encode(b"fake_image_data").decode("utf-8")
    image_bytes = base64.b64decode(image_data)
    files = {"file": ("test_image.png", image_bytes, "image/png")}
    
    # Upload the icon
    response = client.post("/medications/1/icon", files=files)
    assert response.status_code == 200
    assert response.json()["message"] == "Icon uploaded successfully"
    assert "icon_url" in response.json()

def test_get_medication_icon():
    # Retrieve the uploaded icon
    response = client.get("/medications/1/icon")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/")

def test_delete_medication_icon():
    # Create a sample base64-encoded image
    image_data = base64.b64encode(b"fake_image_data").decode("utf-8")
    image_bytes = base64.b64decode(image_data)
    files = {"file": ("test_image.png", image_bytes, "image/png")}
    
    # Step 1: Upload the icon
    upload_response = client.post("/medications/1/icon", files=files)
    assert upload_response.status_code == 200
    assert upload_response.json()["message"] == "Icon uploaded successfully"

    # Step 2: Delete the icon
    delete_response = client.delete("/medications/1/icon")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Icon deleted successfully"

    # Step 3: Attempt to retrieve the deleted icon
    get_response = client.get("/medications/1/icon")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Image not found"
