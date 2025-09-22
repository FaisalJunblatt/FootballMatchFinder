from fastapi import FastAPI
from db import init_db

app = FastAPI(title="Football Match Finder")
@app.get("/health") #
def health():
    return {"status":"ok"}

@app.on_event("startup")
def on_startup():
    init_db()