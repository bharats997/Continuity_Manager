# backend/app/main.py
import asyncio
import uuid  # For custom json_encoder
import typer
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# Import routers
from .apis.endpoints import (
    departments as departments_router,
    users as users_router,
    roles as roles_router,
    locations as locations_router,
    applications as applications_router,
    processes as processes_router,
    vendors as vendors_router,
    bia_categories as bia_categories_router,
    bia_parameters as bia_parameters_router, # Added for BIA Parameters
    bia_impact_criteria as bia_impact_criteria_router, # Added for BIA Impact Criteria
    bia_frameworks as bia_frameworks_router,
)
# Import database session and models
from .db.session import get_main_app_engine, Base
from .models.domain import (
    organizations, departments, users, roles, locations, applications, processes, vendors
)
from .core.seed_data import init_db as seed_init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for the FastAPI application."""
    # On startup
    print("Starting up and initializing engine...")
    engine = get_main_app_engine() # Use the main app's singleton engine
    yield
    # On shutdown
    print("Shutting down and disposing engine...")
    await engine.dispose()

app = FastAPI(
    title="Business Continuity Management System (BCMS) API",
    description="API for the BCMS platform, extending COMPASS.",
    version="0.1.0",
    lifespan=lifespan,
    json_encoders={
        uuid.UUID: lambda o: str(o)  # Ensure UUIDs are serialized as strings
    }
)

# CORS (Cross-Origin Resource Sharing) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify ["http://localhost:3000"] for React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(departments_router.router, prefix="/api/v1/departments", tags=["Departments"])
app.include_router(users_router.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(roles_router.router, prefix="/api/v1/roles", tags=["Roles"])
app.include_router(locations_router.router, prefix="/api/v1/locations", tags=["Locations"])
app.include_router(applications_router.router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(processes_router.router, prefix="/api/v1/processes", tags=["Processes"])
app.include_router(vendors_router.router, prefix="/api/v1/vendors", tags=["Vendors"])
app.include_router(bia_categories_router.router, prefix="/api/v1/bia-categories", tags=["BIA Categories"])
app.include_router(bia_parameters_router.router, prefix="/api/v1/bia-parameters", tags=["BIA Parameters"])
app.include_router(bia_impact_criteria_router.router, prefix="/api/v1/bia-impact-criteria", tags=["BIA Impact Criteria"]) # Added for BIA Impact Criteria
app.include_router(bia_frameworks_router.router, prefix="/api/v1/bia-frameworks", tags=["BIA Frameworks"])

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# Typer CLI app for management commands
cli_app = typer.Typer()

@cli_app.command()
def seed_db():
    """Initialize the database with predefined roles, default organization, and admin user."""
    typer.echo("Starting database seeding process...")
    asyncio.run(seed_init_db())
    typer.echo("Database seeding process finished.")

if __name__ == "__main__":
    # If main.py is run directly, execute the Typer CLI app.
    # This allows commands like `python -m app.main seed-db`
    # The FastAPI app itself should be run with Uvicorn (e.g., `uvicorn app.main:app --reload`)
    cli_app()
