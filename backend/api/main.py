import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import overview, heatmap, clusters, trends, resume

app = FastAPI(title="Job Market Intelligence API")

# Allow localhost in dev + the production Vercel frontend URL
_extra = os.environ.get("ALLOWED_ORIGIN", "")
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if _extra:
    origins.append(_extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api")
app.include_router(heatmap.router, prefix="/api")
app.include_router(clusters.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
