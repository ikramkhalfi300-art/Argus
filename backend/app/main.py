from fastapi import FastAPI

app = FastAPI(title="AI Product Research Platform")


@app.get("/health")
async def health():
    return {"status": "ok"}
