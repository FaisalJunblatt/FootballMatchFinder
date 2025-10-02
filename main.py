from fastapi import FastAPI
from db import create_db_and_tables
from routers.matches import router as matches_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


app = FastAPI(title="Football Match Finder")
@app.get("/health") 
def health():
    return {"status":"ok"}

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(matches_router)


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")


