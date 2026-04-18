from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.compression_routes import router as compression_router
from app.api.routes.ocr_routes import router as ocr_router

app = FastAPI(title="Strike3 Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compression_router)
app.include_router(ocr_router)

@app.get("/")
def root():
    return {"message": "Strike3 running"}

@app.get("/health")
def health():
    return {"status": "ok"}