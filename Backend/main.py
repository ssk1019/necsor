from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect_db()
    yield
    await db.close_db()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    # Simple check to ensure DB connections are active
    try:
        await db.db.command("ping")
        await db.redis.ping()
        return {"status": "ok", "database": "connected", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "details": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)