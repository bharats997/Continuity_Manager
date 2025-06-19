# backend/app/db/base.py
# This file ensures that all models are imported before Base.metadata.create_all
# is called by Alembic or by test setup routines.

# Import Base from the session module where it's defined
from app.db.session import Base  # noqa: F401 imported but unused - Base is used by SQLAlchemy metadata

# Import all models here to register them with Base.metadata
from app.models.domain.organizations import Organization  # noqa: F401
from app.models.domain.users import User, user_roles_association  # noqa: F401
from app.models.domain.roles import Role  # noqa: F401
from app.models.domain.permissions import Permission, role_permissions_association  # noqa: F401
from app.models.domain.departments import Department, department_locations_association  # noqa: F401 # Depends on Organization
from app.models.domain.bia_categories import BIACategory  # noqa: F401
from app.models.domain.applications import Application  # noqa: F401
from app.models.domain.locations import Location  # noqa: F401
from app.models.domain.processes import Process, process_locations_association, process_applications_association, process_dependencies_association  # noqa: F401
from app.models.domain.vendors import Vendor  # noqa
from app.models.domain.bia_impact_scales import BIAImpactScale  # noqa: F401
from app.models.domain.bia_impact_scale_levels import BIAImpactScaleLevel  # noqa: F401
from app.models.domain.bia_timeframes import BIATimeframe  # noqa: F401
from app.models.domain.bia_impact_criteria import BIAImpactCriterion, BIAImpactCriterionLevel  # noqa: F401
from sqlalchemy.orm import relationship

# All relationships are now defined declaratively in their respective model files.

# Explicitly configure mappers after all models are imported
# This can help resolve complex dependencies or ordering issues.

Base.registry.configure()

print(f"--- app.db.base DIAGNOSTICS ---")
print(f"Base class in app.db.base: {Base}")
print(f"ID of Base class in app.db.base: {id(Base)}")
print(f"-----------------------------")

# print(f"INFO [app.db.base.py]: All models imported and mappers configured. Base.metadata.tables: {list(Base.metadata.tables.keys())}")
