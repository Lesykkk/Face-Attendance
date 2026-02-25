from fastapi import FastAPI

from api.router import router as api_router

app = FastAPI(
    title="Face-Attendance Central Server",
    version="1.0.0",
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
