from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .pipelines import run_comparison
from .tickets import TICKETS

app = FastAPI(title="TokenLean", description="Token-minimal support automation demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "demo", "tickets": len(TICKETS)}


@app.get("/tickets")
def tickets():
    return {"tickets": TICKETS}


@app.get("/compare")
def compare():
    return run_comparison()
