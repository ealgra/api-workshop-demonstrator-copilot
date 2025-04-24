from prometheus_client import Gauge, Counter

# Define Prometheus metrics
INVENTORY_GAUGE = Gauge(
    "inventory_quantity",
    "Quantity of medications in inventory",
    ["medication_id", "shelf_id", "shelf_location"]
)

REQUEST_COUNT = Counter(
    "request_count",
    "Total number of requests",
    ["method", "endpoint"]
)
