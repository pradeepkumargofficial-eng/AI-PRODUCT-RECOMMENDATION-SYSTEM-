"""
FastAPI application entry point.

Run locally:
    uvicorn main:app --reload --port 8000

Docs available at:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router

app = FastAPI(
    title="AI Product Recommendation API",
    description="Hybrid (content-based + collaborative filtering) recommendation "
                "engine serving a synthetic e-commerce catalog.",
    version="1.0.0",
)

# In production, replace "*" with the deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "ai-product-recommendation-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}
