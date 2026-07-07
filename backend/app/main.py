from fastapi import FastAPI

from app.api.discover import router as discover_router

app = FastAPI(title="AI Product Research Platform")
app.include_router(discover_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
