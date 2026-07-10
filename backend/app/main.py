from fastapi import FastAPI

from app.api.discover import router as discover_router
from app.api.pipeline_stage1 import router as pipeline_stage1_router
from app.api.validate import router as validate_router

app = FastAPI(title="AI Product Research Platform")
app.include_router(discover_router)
app.include_router(pipeline_stage1_router)
app.include_router(validate_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
