# backend/app/main.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# Assuming your routers are in apis.endpoints
from .apis.endpoints import departments as departments_router
from .apis.endpoints import people as people_router
from .apis.endpoints import roles as roles_router
from .apis.endpoints import locations as locations_router # Added locations_router
# Import other necessary modules like database session, base for table creation etc.
from .database.session import engine, Base
from .models.domain import organizations, departments, people, roles, locations # Added locations, Ensure all domain models are imported for Base.metadata

# Create database tables if they don't exist
# In a production app, you'd likely use Alembic for migrations.
# This is okay for development.
# try:
#     Base.metadata.create_all(bind=engine) # Commented out: Handled by migrations in prod, and by conftest.py for tests
#     print("Database tables checked/created successfully.")
# except Exception as e:
#     print(f"Error creating database tables: {e}")


app = FastAPI(
    title="Business Continuity Management System (BCMS) API",
    description="API for the BCMS platform, extending COMPASS.",
    version="0.1.0"
)

# CORS (Cross-Origin Resource Sharing) middleware
# Adjust origins as necessary for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify ["http://localhost:3000"] for React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(departments_router.router, prefix="/api/v1/departments", tags=["Departments"])
app.include_router(people_router.router, prefix="/api/v1/people", tags=["People"])
app.include_router(roles_router.router, prefix="/api/v1/roles", tags=["Roles"])
app.include_router(locations_router.router, prefix="/api/v1/locations", tags=["Locations"]) # Added locations_router

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# Placeholder for organizations router if it exists or will be added
# from .apis.endpoints import organizations as organizations_router
# app.include_router(organizations_router.router, prefix="/api/v1/organizations", tags=["Organizations"])

