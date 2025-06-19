# Task Status

## Epic: Core BCMS Backend Features

### User Story/Functional Requirement: FR 1.1 - Department Management

*   **Description:** Implement backend API endpoints and services for managing departments within an organization.
*   **Status:** **Backend Implemented & Tested (Epic 1 Complete)**
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
    *   Automated Tests (`backend/app/tests/api/test_departments_api.py`): All tests passing, including fixes for `DetachedInstanceError` and validation logic in update operations.
    *   **UI Status:** To Be Implemented
*   **Next Steps (Epic 1):**
    *   Core backend CRUD functionality for departments is complete.
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
*   **Status:** **Core Backend API Implemented & Tested (Epic 1 Complete)**
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
    *   **UI Status:** To Be Implemented
*   **Next Steps (Epic 1):**
    *   Core backend CRUD and role assignment functionality for people is complete.
*   **Key Issues Resolved:**
    *   `AttributeError` in `test_soft_delete_person_as_admin` due to missing `deletedAt`/`deletedBy` fields (corrected test assertions).
*   **Remaining Warnings (Non-critical):**
    *   SQLAlchemy `SAWarning` regarding table drop order for tables with circular dependencies (e.g., `departments`, `people`). Tests are passing.
*   **Next Steps (Post-Epic 1 Enhancements):**
    *   Consider more explicit API endpoints for role assignment/unassignment if needed (e.g., `POST /people/{person_id}/roles`). Current approach handles roles within person create/update.
    *   Further integrate `Location` data in People API responses/requests if more detailed information than `locationId` is required (e.g., embedding location details).

### User Story/Functional Requirement: FR 1.3 - Process Management

*   **Description:** Implement backend API endpoints and services for managing business processes, including their attributes, dependencies, and associated entities like locations and applications.
*   **Status:** **Backend Implemented & Tested (Epic 1 Complete)**
*   **Details:**
    *   API Endpoints (`backend/app/apis/endpoints/processes.py`):
        *   `POST /processes/`: Create Process - **Implemented & Tested**
        *   `GET /processes/{process_id}`: Get Process - **Implemented & Tested**
        *   `GET /processes/`: List Processes - **Implemented & Tested**
        *   `PUT /processes/{process_id}`: Update Process - **Implemented & Tested**
        *   `DELETE /processes/{process_id}`: Delete Process - **Implemented & Tested**
    *   Service Layer (`backend/app/services/process_service.py`): Business logic for CRUD operations, including handling of M2M relationships (locations, applications, dependencies) and validation. - **Implemented & Tested**
    *   Database Model (`backend/app/models/domain/processes.py`): SQLAlchemy model for processes, including M2M tables. - **Implemented**
    *   Pydantic Schemas (`backend/app/models/process.py`): Request/Response models (Create, Update, Response). - **Implemented**
    *   Automated Tests:
        *   `backend/app/tests/api/test_processes_api.py`: Core API functionality tests. - **All tests passing**
        *   `backend/app/tests/api/test_processes_api_rbac.py`: Role-Based Access Control and detailed validation tests, including clearing M2M relationships. - **All tests passing**
    *   **UI Status:** To Be Implemented
*   **Key Issues Resolved (during development):**
    *   `ImportError` for `ApplicationModel` in tests.
    *   `TypeError` in M2M clearing tests due to helper function usage.
    *   `ConflictException` (409) handling for duplicate process names.
*   **Next Steps (Epic 1):**
    *   Core backend CRUD and RBAC functionality for processes is complete.

### User Story/Functional Requirement: FR 1.4 - Application Management

*   **Description:** As an Admin, I want to register and manage applications used by the organization so that I can understand their dependencies on business processes and track their characteristics.
*   **Status:** **Backend Implemented & Tested (Epic 1 Complete)**
*   **Details:**
    *   Database Table (`applications`): **Created via Alembic migration `d9f76c4a13d7`**
    *   Database Model (`backend/app/models/domain/applications.py`): SQLAlchemy model for applications - **Implemented**
    *   Pydantic Schemas (`backend/app/models/application.py`): Request/Response models - **Implemented**
    *   Service Layer (`backend/app/services/application_service.py`): Business logic for CRUD operations - **Implemented & Tested**
    *   API Endpoints (`backend/app/apis/endpoints/applications.py`): CRUD operations - **Implemented & Tested**
    *   Automated Tests (`backend/app/tests/api/test_applications_api.py`): All tests passing (17/17), covering creation, retrieval, update, deletion, and validation scenarios.
    *   **UI Status:** To Be Implemented
*   **Key Issues Resolved:**
    *   `app_owner_id` update and relationship refresh in service layer.
    *   Missing `criticality` field in Pydantic response and update models.
    *   Missing `criticality` attribute in SQLAlchemy model.
*   **Next Steps (Epic 1):**
    *   Core backend CRUD functionality for applications is complete.

### User Story/Functional Requirement: FR 1.5 - Location Management

*   **Description:** Manage physical locations or sites relevant to business operations.
*   **Status:** **Backend Implemented & Tested (Epic 1 Complete)**
*   **Details:**
    *   Database Model (`backend/app/models/domain/locations.py`): SQLAlchemy model for locations - **Implemented**.
    *   Pydantic Schemas (`backend/app/models/location.py`): Request/Response models - **Implemented & Pydantic V2 Compliant**.
    *   Relationships with `Organization` and `Person` models established.
    *   Service Layer (`backend/app/services/location_service.py`): CRUD operations - **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/locations.py`): CRUD operations - **Implemented & Tested**.
    *   Automated Tests (`backend/app/tests/api/test_locations_api.py`): All tests passing for CRUD operations and error handling.
    *   **UI Status:** To Be Implemented
*   **Next Steps (Epic 1):**
    *   Core backend CRUD functionality for locations is complete.
*   **Next Steps (Post-Epic 1 Enhancements):**
    *   Consider if any specific authorization logic beyond basic user authentication is needed for location management (currently assumes authenticated user can manage locations within their organization, with some commented-out authorization checks in the API layer for more granular control if needed).

### User Story/Functional Requirement: FR 1.6 - Role Management (Read API)

*   **Description:** Implement backend API endpoints and services for managing roles. For Phase 1 of Epic 1, roles are predefined, so only read operations are exposed via API.
*   **Status:** **Read API Implemented & Tested (Epic 1 Scope)**
*   **Details:**
    *   Database Model (`backend/app/models/domain/roles.py`): SQLAlchemy model for roles - **Implemented**.
    *   Pydantic Schemas (`backend/app/models/role.py`): Request/Response models - **Implemented & Pydantic V2 Compliant**.
    *   Service Layer (`backend/app/services/role_service.py`): Methods for `get_role_by_id`, `get_role_by_name`, `get_roles` - **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/roles.py`):
        *   `GET /roles/`: List Roles - **Implemented & Tested**
        *   `GET /roles/{role_id}`: Get Role - **Implemented & Tested**
    *   Automated Tests (`backend/app/tests/api/test_roles_api.py`): All tests passing for read operations and authorization.
    *   **UI Status:** To Be Implemented (for viewing roles)
*   **Next Steps (Epic 1):**
    *   Ensure roles can be easily predefined/seeded for deployment. This is the primary remaining task for roles within Epic 1.
*   **Next Steps (Post-Epic 1 Enhancements):**
    *   Full CRUD operations for roles (Create, Update, Delete via API) are out of scope for Epic 1.

---
*This status is based on the development session up to 2025-06-18.*

## Epic 2: Business Impact Analysis (BIA) - Core Framework

### User Story/Functional Requirement: FR 2.1 - BIA Category Management

*   **Description:** As a BCM Manager or Admin, I want to define and manage BIA categories (e.g., Financial, Reputational, Operational, Legal/Regulatory) so that I can structure the impact assessment consistently across the organization.
*   **Status:** **Backend Implemented & Tested**
*   **Details:**
    *   Database Model (`backend/app/models/domain/bia_categories.py`): SQLAlchemy model - **Implemented**.
    *   Pydantic Schemas (`backend/app/schemas/bia_categories.py`): Request/Response models - **Implemented & Pydantic V2 Compliant**.
    *   Service Layer (`backend/app/services/bia_category_service.py`): Business logic for CRUD - **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/bia_categories.py`): CRUD operations - **Implemented & Tested**.
    *   Automated Tests (`backend/app/tests/api/test_bia_categories.py`): All tests passing, including RBAC and validation. Test environment stabilized (async, Pydantic warnings fixed).
    *   **UI Status:** To Be Implemented
*   **Key Issues Resolved (during development of FR 2.1 backend):**
    *   Persistent asynchronous test failures due to database initialization.
    *   `ImportError` in test fixtures.
    *   `PytestDeprecationWarning` for asyncio event loop scope.
    *   Pydantic v2 deprecation warnings in schemas.
    *   Fixed a critical `TypeError` during model instantiation (`'created_by_id' is an invalid keyword argument for BIACategory`) by adding missing audit fields (`created_by_id`, `updated_by_id`) and relationships to the `BIACategory` model and its corresponding Pydantic schemas.
*   **Next Steps for FR 2.1:** Frontend implementation.

### User Story/Functional Requirement: FR 2.2 - BIA Configuration Elements Management

*   **Overall Description:** As a BCM Manager or Admin/CISO, I want to define and manage various elements that configure the BIA, so that I can customize the BIA process to the organization's specific needs. This FR is broken into two main parts:
    1.  Management of BIA Impact Scales and Timeframes (foundational elements).
    2.  Management of BIA Impact Criteria Parameters (detailed criteria linked to BIA Categories, used in framework building).

#### FR 2.2.1 - BIA Impact Scales & Timeframes Management

*   **Description (Derived from initial interpretation):** Manage BIA Impact Scales (with levels) and BIA Timeframes.
*   **Status:** **Backend Implemented & Tested**
*   **Details:**
    *   Database Models (`bia_impact_scales`, `bia_impact_scale_levels`, `bia_timeframes`): **Implemented**.
    *   Pydantic Schemas (`backend/app/schemas/bia_parameters.py`): CRUD models for Impact Scales (with levels) and Timeframes - **Implemented**.
    *   Service Layer (`backend/app/services/bia_parameter_service.py`): CRUD logic for Impact Scales and Timeframes - **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/bia_parameters.py`): CRUD operations for Impact Scales and Timeframes - **Implemented & Tested**.
    *   Automated Tests (`backend/app/tests/api/test_bia_parameters.py`): All tests passing for Impact Scales and Timeframes, covering CRUD, RBAC, and validation.
    *   **UI Status:** To Be Implemented (for Impact Scales & Timeframes)
*   **Key Issues Resolved (during development of FR 2.2.1):**
    *   Fixed complex `403 Forbidden` errors in tests caused by a combination of incorrect test fixture logic (`conftest.py`), faulty data seeding, and transaction isolation issues.
    *   Corrected multiple bugs in `user_service.py` related to incorrect database column names (camelCase vs. snake_case).
    *   Ensured user roles and permissions are eagerly loaded to provide correct authorization context to the application.
*   **Next Steps for FR 2.2.1:**
    *   Frontend implementation for BIA Impact Scales and Timeframes.

#### FR 2.2.2 - BIA Impact Criteria Parameter Management (as per PRD FR 2.2)

*   **Description (as per PRD FR 2.2):** As a BCM Manager or CISO, I want to create, edit, or delete parameters under BIA categories so that I can define specific impact criteria. These parameters will have a rating type (Qualitative/Quantitative) with configurable levels/ranges and scores, and will be used in the BIA Framework Builder (FR 2.3).
*   **Status:** **Backend Implemented & Tested**
*   **Details:**
    *   Database Models (`backend/app/models/domain/bia_impact_criteria.py`): `BIAImpactCriterion` and `BIAImpactCriterionLevel` models are **Implemented**.
    *   Pydantic Schemas (`backend/app/schemas/bia_impact_criteria.py`): CRUD schemas for criteria and their levels are **Implemented**.
    *   Service Layer (`backend/app/services/bia_impact_criteria_service.py`): Business logic for managing criteria and their levels is **Implemented & Tested**.
    *   API Endpoints (`backend/app/apis/endpoints/bia_impact_criteria.py`): CRUD operations are **Implemented & Tested**.
    *   Automated Tests (`backend/app/tests/api/test_bia_impact_criteria_api.py`): All tests passing, covering CRUD, RBAC, and validation.
    *   **UI Status:** To Be Implemented
*   **Key Issues Resolved (during development of FR 2.2.2):**
    *   Resolved a `TypeError` originating from the `BIACategory` model which was blocking tests for this feature.
    *   Fixed a Pydantic `ValidationError` in tests due to a missing `sequence_order` field in `BIAImpactCriterionLevelCreate` schema.
*   **Next Steps for FR 2.2.2:**
    *   Frontend implementation.
