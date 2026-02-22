from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sweetwalk.config import settings
from sweetwalk.routing.router import router as routing_router

app = FastAPI(title="Sweet Walk API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing_router)


@app.get("/health")
def health():
    return {"status": "ok"}
