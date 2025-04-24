import hashlib
import xmltodict
from fastapi.responses import JSONResponse, Response as FastAPIResponse

IMAGE_DIR = "/tmp/images"

def generate_etag(obj) -> str:
    obj_data = f"{obj.dict()}"
    return hashlib.md5(obj_data.encode()).hexdigest()

def serialize_response(data, accept: str):
    if accept == "application/xml":
        return FastAPIResponse(content=xmltodict.unparse({"response": data}, pretty=True), media_type="application/xml")
    else:
        return JSONResponse(content=data)