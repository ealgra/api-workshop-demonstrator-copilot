from fastapi.testclient import TestClient
from app.main import app  # Assuming the main FastAPI app is defined in app/main.py

client = TestClient(app)

def test_metrics_endpoint():
    """
    Test the Prometheus metrics endpoint to ensure it is accessible and returns valid metrics data.
    """
    response = client.get("/metrics")
    assert response.status_code == 200

    # Check for specific metrics and their structure
    metrics_text = response.text
    assert "# HELP request_count_total Total number of requests" in metrics_text
    assert "# TYPE request_count_total counter" in metrics_text
    assert 'request_count_total' in metrics_text
    assert "# HELP inventory_quantity Quantity of medications in inventory" in metrics_text
    assert "# TYPE inventory_quantity gauge" in metrics_text
