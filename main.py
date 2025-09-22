from fastapi import FastAPI
from db import init_db
from routers.matches import router as matches_router

app = FastAPI(title="Football Match Finder")
@app.get("/health") #
def health():
    return {"status":"ok"}

@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(matches_router)