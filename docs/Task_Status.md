# Task Status

## Epic: Core BCMS Backend Features

### User Story/Functional Requirement: FR 1.1 - Department Management

*   **Description:** Implement backend API endpoints and services for managing departments within an organization.
*   **Status:** **Completed**
*   **Details:**
    *   API Endpoints (`backend/app/apis/endpoints/departments.py`):
        *   `POST /departments/`: Create Department - **Implemented & Tested**
        *   `GET /departments/{department_id}`: Get Department - **Implemented & Tested**
        *   `GET /departments/`: List Departments - **Implemented & Tested**
        *   `PUT /departments/{department_id}`: Update Department - **Implemented & Tested**
        *   `DELETE /departments/{department_id}`: Delete Department - **Implemented & Tested**
    *   Service Layer (`backend/app/services/department_service.py`): Business logic for CRUD operations - **Implemented & Tested**
    *   Database Model (`backend/app/models/domain/departments.py`): SQLAlchemy model for departments - **Implemented**
    *   Pydantic Schemas (`backend/app/models/department.py`): Request/Response models - **Implemented & Updated for Pydantic V2**
    *   Automated Tests (`backend/app/tests/api/test_departments_api.py`): All tests passing.
*   **Key Issues Resolved:**
    *   `AttributeError` for `department_service` instance.
    *   Database connection errors during testing (ensured SQLite usage).
    *   `DetachedInstanceError` in SQLAlchemy during tests.
    *   Pydantic V2 compatibility warnings.
    *   SQLAlchemy `declarative_base` import warning.
    *   Pytest asyncio deprecation warning.
*   **Remaining Warnings (Non-critical):**
    *   SQLAlchemy `SAWarning` regarding table drop order for tables with circular dependencies (e.g., `departments`, `people`). Tests are passing.

### User Story/Functional Requirement: FR 1.2 - People Management

*   **Description:** Implement backend API endpoints and services for managing people (users/employees) within an organization, including role assignments.
*   **Status:** **Core API Implemented & Tested**
*   **Details:**
    *   Database Model (`backend/app/models/domain/people.py`): SQLAlchemy model for people - **Implemented** (including `locationId` and relationship to `Location` model).
    *   Pydantic Schemas (`backend/app/models/person.py`): Request/Response models - **Implemented & Pydantic V2 Compliant**.
    *   Service Layer (`backend/app/services/person_service.py`): Business logic for CRUD operations - **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/people.py`):
        *   `POST /people/`: Create Person - **Implemented & Tested**
        *   `GET /people/`: List People - **Implemented & Tested**
        *   `GET /people/{person_id}`: Get Person - **Implemented & Tested**
        *   `PUT /people/{person_id}`: Update Person - **Implemented & Tested**
        *   `DELETE /people/{person_id}`: Soft Delete Person - **Implemented & Tested**
    *   Automated Tests (`backend/app/tests/api/test_people_api.py`): All 18 tests passing, covering creation, retrieval, update, deletion, role-based access, and validation scenarios.
    *   Role Assignment: People can be assigned roles during creation/update. Models for roles exist and association is defined.
*   **Key Issues Resolved:**
    *   `AttributeError` in `test_soft_delete_person_as_admin` due to missing `deletedAt`/`deletedBy` fields (corrected test assertions).
*   **Remaining Warnings (Non-critical):**
    *   SQLAlchemy `SAWarning` regarding table drop order for tables with circular dependencies (e.g., `departments`, `people`). Tests are passing.
*   **Next Steps (Enhancements/Refinements):**
    *   Consider more explicit API endpoints for role assignment/unassignment if needed (e.g., `POST /people/{person_id}/roles`). Current approach handles roles within person create/update.
    *   Further integrate `Location` data in People API responses/requests if more detailed information than `locationId` is required (e.g., embedding location details).

### User Story/Functional Requirement: FR 1.3 - Role Management

*   **Description:** Implement backend API endpoints and services for managing roles. For Phase 1, roles are predefined, so only read operations are exposed via API.
*   **Status:** **Read API Implemented & Tested (Phase 1 Scope)**
*   **Details:**
    *   Database Model (`backend/app/models/domain/roles.py`): SQLAlchemy model for roles - **Implemented**.
    *   Pydantic Schemas (`backend/app/models/role.py`): Request/Response models - **Implemented & Pydantic V2 Compliant**.
    *   Service Layer (`backend/app/services/role_service.py`): Methods for `get_role_by_id`, `get_role_by_name`, `get_roles` - **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/roles.py`):
        *   `GET /roles/`: List Roles - **Implemented & Tested**
        *   `GET /roles/{role_id}`: Get Role - **Implemented & Tested**
    *   Automated Tests (`backend/app/tests/api/test_roles_api.py`): All tests passing for read operations and authorization.
*   **Next Steps (Phase 1):**
    *   Ensure roles can be easily predefined/seeded for deployment.
    *   CRUD operations for roles (Create, Update, Delete via API) are out of scope for Phase 1.

### User Story/Functional Requirement: FR 1.4 - Application Management

*   **Description:** As an Admin, I want to register and manage applications used by the organization so that I can understand their dependencies on business processes and track their characteristics.
*   **Status:** **To Do**
*   **Details:**
    *   Database Model (`backend/app/models/domain/applications.py`): SQLAlchemy model for applications - **To Be Implemented**
    *   Pydantic Schemas (`backend/app/models/application.py`): Request/Response models - **To Be Implemented**
    *   Service Layer (`backend/app/services/application_service.py`): Business logic for CRUD operations - **To Be Implemented**
    *   API Endpoints (`backend/app/apis/endpoints/applications.py`): CRUD operations - **To Be Implemented**
    *   Automated Tests (`backend/app/tests/api/test_applications_api.py`): **To Be Implemented**
*   **Next Steps (Phase 1):**
    *   Implement core CRUD functionality for applications.

### User Story/Functional Requirement: FR 1.5 - Location Management

*   **Description:** Manage physical locations or sites relevant to business operations.
*   **Status:** **Implemented & Tested**
*   **Details:**
    *   Database Model (`backend/app/models/domain/locations.py`): SQLAlchemy model for locations - **Implemented**.
    *   Pydantic Schemas (`backend/app/models/location.py`): Request/Response models - **Implemented & Pydantic V2 Compliant**.
    *   Relationships with `Organization` and `Person` models established.
    *   Service Layer (`backend/app/services/location_service.py`): CRUD operations - **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/locations.py`): CRUD operations - **Implemented & Tested**.
    *   Automated Tests (`backend/app/tests/api/test_locations_api.py`): All tests passing for CRUD operations and error handling.
*   **Next Steps (Phase 1):**
    *   Core CRUD functionality for locations is complete.
    *   Consider if any specific authorization logic beyond basic user authentication is needed for location management in Phase 1 (currently assumes authenticated user can manage locations within their organization, with some commented-out authorization checks in the API layer for more granular control if needed).

---
*This status is based on the development session up to 2025-05-29 (People Management API core implementation and testing completed).*
