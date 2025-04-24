from fastapi import FastAPI
from prometheus_client import start_http_server, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response as FastAPIResponse

from app.routes.medications import router as medications_router
from app.routes.inventory import router as inventory_router
from app.metrics import INVENTORY_GAUGE, REQUEST_COUNT  # Updated import

app = FastAPI()

# Middleware to track requests
@app.middleware("http")
async def prometheus_middleware(request, call_next):
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    return response

# Include routers
app.include_router(medications_router, prefix="/medications", tags=["Medications"])
app.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])

@app.get("/metrics", summary="Get metrics", description="Retrieve Prometheus metrics.")
def get_metrics():
    return FastAPIResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    start_http_server(8001)  # Start Prometheus metrics server on port 8001
    uvicorn.run(app, host="0.0.0.0", port=8000)