from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.routers import users, tasks

app = FastAPI(
    title="Placement Progress Tracker API",
    description="A modular backend API using FastAPI and Supabase to log and track placement preparation tasks.",
    version="1.0.0"
)

# CORS middleware configuration to allow frontend clients (Web, App, Chrome Extensions) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users.router)
app.include_router(tasks.router)

@app.get("/", include_in_schema=False)
def index_redirect():
    # Redirect base URL to interactive swagger docs
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "Placement Progress Tracker API"}
