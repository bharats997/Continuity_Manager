## **Product Requirements Document (PRD): Business Continuity Management System (BCMS) \- Phase 1**

**Version:** 1.0 **Date:** May 28, 2025 **Product Owner:** Bharat S **Company:** CyRAACS **Platform:** COMPASS

---

### **1\. Introduction**

This document outlines the product requirements for Phase 1 of the Business Continuity Management System (BCMS) application, a COMPASS extension. The primary goal of Phase 1 is to establish a foundational data model for organizational information, enable comprehensive Business Impact Analysis (BIA), and derive critical recovery metrics for business processes and their supporting applications. This phase lays the groundwork for subsequent phases that will focus on recovery strategies, plan development, incident management, and advanced integrations. The UI should be clean, uncluttered, refreshing, and minimalist.

### **2\. Goals & Objectives**

**Overall Business Goal:** To provide organizations with a robust, integrated platform for proactive business continuity planning, incident response, and resilience measurement.

**Phase 1 Specific Goals:**

* Establish a centralized repository for essential organizational data (departments, people, processes, applications, locations, vendors).  
* Enable structured Business Impact Analysis (BIA) for all identified business processes.  
* Automate the calculation of impact scores and Recovery Time Objectives (RTOs) for processes and applications.  
* Prioritize business processes based on their criticality and RTOs.  
* Provide a clear, auditable trail for BIA data and decisions.

**Phase 1 Specific Objectives:**

* Successfully onboard organizational data (departments, people, processes, applications, locations, vendors) with data integrity and relationships.  
* Complete BIA for at least 80% of critical business processes identified by the organization.  
* Achieve an accuracy rate of 95% for automatically calculated impact scores and RTOs.  
* Ensure the system can handle concurrent BIA submissions from multiple users.

### **3\. User Personas (Phase 1\)**

**3.1. BCM Manager**

* **About:** Oversees the entire BCMS program, defines BIA parameters, reviews analysis results, ensures compliance, and manages users.  
* **Needs (Phase 1):**  
  * To add, edit and delete categories, parameters, framework for BIA.  
  * To initiate BIA, Review BIA, send for clarification, submit Impact Score and RTO for approval to Department Head.  
  * To add, edit and delete users.  
  * To export BIA.  
  * To view all sections.  
* **Pain Points (Phase 1):**  
  * Manual collection and consolidation of organizational data.  
  * Inconsistent BIA methodologies across departments.  
  * Difficulty in tracking BIA progress and chasing stakeholders.  
  * Lack of a centralized view of all organizational assets and their interdependencies.

**3.2. Process Owner**

* **About:** Responsible for specific business processes within their department. They are key contributors to the BIA, providing detailed insights into process dependencies, resource requirements, and impact.  
* **Needs (Phase 1):**  
  * To add and edit process information.  
  * To easily access and update information about their department's processes, applications, and people.  
  * To complete BIA questionnaires for their processes in an intuitive manner.  
  * To provide impact ratings for the processes for the timeframes.  
  * To select and map process dependencies (Upstream and downstream) from a list of processes.  
  * To submit for Review.  
  * To understand the impact of disruptions on their processes and the wider organization.  
* **Pain Points (Phase 1):**  
  * Time-consuming and manual BIA data entry.  
  * Lack of clarity on BIA questions and impact definitions.  
  * Difficulty in mapping processes to supporting applications and infrastructure.  
  * Lack of visibility into how their process impact contributes to the overall organizational impact.

**3.3. Department Head**

* **About:** Responsible for a department and its associated processes. They approve the final impact score and RTO for processes within their department.  
* **Needs (Phase 1):**  
  * To approve Impact Score and RTO for processes in the Department.  
  * To add and edit department and associated process information.  
  * To provide a note for acceptance.  
* **Pain Points (Phase 1):**  
  * Lack of clear visibility into the BIA results for their department.  
  * Manual approval processes for BIA.

**3.4. Admin**

* **About:** Manages user accounts, permissions, and core organizational data.  
* **Needs (Phase 1):**  
  * To add, edit and delete users.  
  * To assign permissions.  
  * To add, edit and delete departments.  
  * To add, edit and delete processes.  
  * To add, edit and delete vendors.  
  * To add, edit and delete applications.  
  * To add, edit and delete locations.  
  * To add, edit and delete people.  
  * To view all sections.  
* **Pain Points (Phase 1):**  
  * Manual and fragmented user and data management.

**3.5. CISO**

* **About:** Information Security Officer, often involved in BIA framework definition and review due to the intersection with cybersecurity risks.  
* **Needs (Phase 1):**  
  * To add, edit and delete categories, parameters, framework for BIA.  
  * To initiate BIA, Review BIA, send for clarification, submit Impact Score and RTO for approval to Department Head.  
  * To add, edit and delete users.  
  * To view BIA results.  
  * To export BIA.

**3.6. Internal Auditor**

* **About:** Responsible for reviewing the BCMS processes and outputs for compliance and effectiveness.  
* **Needs (Phase 1):**  
  * To view all sections.  
  * To view BIA results.  
  * To export BIA.

### **4\. Requirements**

#### **4.1. Functional Requirements**

**Epic 1: Organizational Data Management**

### **FR 1.1: Department Management**

#### **User Story: As a BCM Manager or Admin, I want to add, edit, and delete departments so that I can accurately represent the organizational structure.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `departments` table in the MySQL database with columns: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per organization), `description` (TEXT), `departmentHeadId` (FK to `users.id`, nullable), `numTeamMembers` (INT, nullable), `isActive` (BOOLEAN, default TRUE).  
   * Create a `department_locations` junction table: `departmentId` (FK), `locationId` (FK), composite PK.  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for Department (Create, Read, Update).  
   * Create API endpoints:  
     * `POST /departments`: To create a new department.  
       * Input validation: `name` is unique within the `organizationId`. `departmentHeadId` and `locationIds` must exist in respective tables.  
       * Assign `organizationId` based on authenticated user's organization.  
     * `GET /departments`: To retrieve a list of departments (filter by `organizationId`, sort by `name`).  
     * `GET /departments/{id}`: To retrieve a single department by ID.  
     * `PUT /departments/{id}`: To update an existing department.  
       * Input validation: `name` uniqueness check during update. `departmentHeadId` and `locationIds` must exist.  
     * `DELETE /departments/{id}`: To soft delete (mark `isActive=FALSE`) a department.  
   * Implement business logic for linking/unlinking multiple locations to a department.  
   * Ensure all API endpoints respect the user's `organizationId` for data isolation (multi-tenancy).  
   * Implement basic RBAC: Only users with 'BCM Manager' or 'Admin' roles can access these endpoints.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'Department Management'.  
   * Build a UI for department creation:  
     * Text input for 'Department Name'.  
     * Text area for 'Description'.  
     * Dropdown for 'Department Head' (populates from People data, linked to FR 1.2).  
     * Multi-select dropdown/checkboxes for 'Locations' (populates from Location data, linked to FR 1.5). Selected locations should appear as tags.  
     * Numeric input for 'Number of Team Members'.  
     * 'Submit' button.  
   * Build a UI to display departments in a list/table, showing Name, Head, Locations, Team Members.  
   * Implement 'Edit' button for each department:  
     * Opens a form pre-populated with existing data.  
     * Allows updating all fields.  
     * 'Update' button to save changes.  
   * Implement 'Delete' button for each department:  
     * Confirms deletion (soft delete).  
   * Implement client-side validation for form inputs (e.g., required fields, numeric for team members, unique name locally before API call).  
   * Integrate with backend API endpoints for CRUD operations.  
   * Apply UI/UX design guidelines: Primary Colors (Blue), Heading Font (Outfit), Body Font (DM Sans), minimalist, clean.

**Windsurf, implement the above granular tasks for FR 1.1: Department Management.**

---

**Test Cases for FR 1.1: Department Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 1.1. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 1.1.1 (Create Department \- Success):**  
     * Action: Send POST request to `/departments` with valid data: `name='Finance'`, `description='Manages org finances'`, `departmentHeadId=<valid_user_id>`, `locationIds=[<loc1_id>, <loc2_id>]`, `numTeamMembers=25`.  
     * Expected Result: HTTP 201 Created. Department record created in `departments` table with `isActive=TRUE`. `department_locations` table has correct entries.  
   * **Test Case 1.1.2 (Retrieve Departments):**  
     * Action: Send GET request to `/departments`.  
     * Expected Result: HTTP 200 OK. List includes the newly created 'Finance' department.  
   * **Test Case 1.1.3 (Update Department \- Success):**  
     * Action: Send PUT request to `/departments/<finance_department_id>` with updated `name='Financial Operations'`, `numTeamMembers=30`, `locationIds=[<loc1_id>]`.  
     * Expected Result: HTTP 200 OK. Department record updated in `departments` table. `department_locations` updated to reflect single location.  
   * **Test Case 1.1.4 (Delete Department \- Soft Delete):**  
     * Action: Send DELETE request to `/departments/<financial_operations_department_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` column for the department record in `departments` table is set to `FALSE`.  
   * **Test Case 1.1.5 (Verify Deleted Department Not in Default List):**  
     * Action: Send GET request to `/departments`.  
     * Expected Result: HTTP 200 OK. The "soft-deleted" department is NOT included in the default list (assuming default GET filters for `isActive=TRUE`).  
2. **Edge Case Tests:**

   * **Test Case 1.1.6 (Create Department \- Duplicate Name):**  
     * Action: Send POST request to `/departments` with `name='Finance'` (already exists in active state for the organization).  
     * Expected Result: HTTP 400 Bad Request or 409 Conflict. Error message indicating duplicate department name.  
   * **Test Case 1.1.7 (Create Department \- Missing Mandatory Fields):**  
     * Action: Send POST request to `/departments` with missing `name`.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating missing required field.  
   * **Test Case 1.1.8 (Update Department \- Non-existent ID):**  
     * Action: Send PUT request to `/departments/99999` (non-existent ID).  
     * Expected Result: HTTP 404 Not Found.  
   * **Test Case 1.1.9 (Update Department \- Invalid Department Head ID):**  
     * Action: Send PUT request to `/departments/<department_id>` with `departmentHeadId=<non_existent_user_id>`.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating invalid foreign key.  
   * **Test Case 1.1.10 (Update Department \- Invalid Location ID):**  
     * Action: Send PUT request to `/departments/<department_id>` with `locationIds=[<non_existent_loc_id>]`.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating invalid foreign key.  
   * **Test Case 1.1.11 (Create Department \- Max Length Values):**  
     * Action: Send POST request with department name/description at max allowed length.  
     * Expected Result: HTTP 201 Created. Data saved successfully without truncation.  
   * **Test Case 1.1.12 (RBAC \- Unauthorized User):**  
     * Action: Authenticate as 'Process Owner' and attempt POST /departments.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 1.1.13 (Integrity after Person Update):**  
     * Pre-requisite: Department created with a Department Head (linked to FR 1.2).  
     * Action: Update the `name` of the Department Head via People Management (FR 1.2).  
     * Expected Result: Department display (FR 1.1 UI) correctly reflects the updated Department Head name without breaking the link.  
   * **Test Case 1.1.14 (Integrity after Location Update):**  
     * Pre-requisite: Department created with linked Locations (linked to FR 1.5).  
     * Action: Update the `name` of a linked Location via Location Management (FR 1.5).  
     * Expected Result: Department display (FR 1.1 UI) correctly reflects the updated Location name without breaking the link.

---

### **FR 1.2: People Management**

#### **User Story: As an Admin, I want to add, edit, and assign roles to people within the organization so that I can identify key stakeholders for BCMS activities and manage user access.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `users` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `firstName` (VARCHAR), `lastName` (VARCHAR), `email` (VARCHAR, UNIQUE per organization), `passwordHash` (VARCHAR), `departmentId` (FK to `departments.id`, nullable), `locationId` (FK to `locations.id`, nullable), `role` (ENUM: 'BCM Manager', 'Process Owner', 'Department Head', 'CISO', 'Internal Auditor', 'Admin'), `isActive` (BOOLEAN, default TRUE).  
   * Ensure password hashing is implemented (e.g., bcrypt) and not plain text.  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for User (Create, Read, Update).  
   * Create API endpoints:  
     * `POST /users`: To create a new user.  
       * Input validation: `email` is unique per `organizationId`. `departmentId` and `locationId` must exist if provided. `role` must be one of the predefined ENUM values. Password policy enforcement (e.g., min length).  
       * Assign `organizationId`.  
       * Hash password before saving.  
     * `GET /users`: To retrieve a list of users (filter by `organizationId`, sort by `lastName`, `firstName`).  
     * `GET /users/{id}`: To retrieve a single user by ID.  
     * `PUT /users/{id}`: To update an existing user (including role changes).  
       * Input validation: `email` uniqueness check during update.  
     * `DELETE /users/{id}`: To soft delete (mark `isActive=FALSE`) a user.  
   * Implement RBAC: Only 'Admin' can create/edit/delete users. Only 'Admin' can assign permissions (roles).  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'People Management'.  
   * Build a UI for adding a person:  
     * Text inputs for 'First Name', 'Last Name', 'Email'.  
     * Dropdown for 'Department' (populates from Department data, linked to FR 1.1).  
     * Dropdown for 'Location' (populates from Location data, linked to FR 1.5).  
     * Dropdown for 'Role' (populates from predefined roles: BCM Manager, Process Owner, Department Head, CISO, Internal Auditor, Admin).  
     * Password input (for initial setup of user).  
     * 'Add User' button.  
   * Build a UI to display users in a list/table, showing Name, Email, Department, Location, Role.  
   * Implement 'Edit' button for each user:  
     * Opens a form pre-populated with existing data.  
     * Allows updating all fields, including role reassignment.  
     * 'Update' button to save changes.  
   * Implement 'Delete' button for each user:  
     * Confirms deletion (soft delete).  
   * Implement client-side validation for form inputs (e.g., valid email format, required fields).  
   * Integrate with backend API endpoints for CRUD operations.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 1.2: People Management.**

---

**Test Cases for FR 1.2: People Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 1.2. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 1.2.1 (Create User \- Success):**  
     * Action: Authenticate as Admin. Send POST request to `/users` with valid data: `firstName='John'`, `lastName='Doe'`, `email='john.doe@org.com'`, `departmentId=<valid_dept_id>`, `locationId=<valid_loc_id>`, `role='Process Owner'`, `password='Password123!'`.  
     * Expected Result: HTTP 201 Created. User record created in `users` table with hashed password, `isActive=TRUE`.  
   * **Test Case 1.2.2 (Retrieve Users):**  
     * Action: Authenticate as Admin. Send GET request to `/users`.  
     * Expected Result: HTTP 200 OK. List includes the newly created 'John Doe'.  
   * **Test Case 1.2.3 (Update User Role \- Success):**  
     * Action: Authenticate as Admin. Send PUT request to `/users/<john_doe_id>` with `role='BCM Manager'`.  
     * Expected Result: HTTP 200 OK. User's role updated to 'BCM Manager' in the database.  
   * **Test Case 1.2.4 (Update User Details \- Success):**  
     * Action: Authenticate as Admin. Send PUT request to `/users/<john_doe_id>` with updated `email='john.a.doe@org.com'`, `departmentId=<another_valid_dept_id>`.  
     * Expected Result: HTTP 200 OK. User's email and department updated.  
   * **Test Case 1.2.5 (Delete User \- Soft Delete):**  
     * Action: Authenticate as Admin. Send DELETE request to `/users/<john_doe_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` column for the user record in `users` table is set to `FALSE`.  
2. **Edge Case Tests:**

   * **Test Case 1.2.6 (Create User \- Duplicate Email for Organization):**  
     * Action: Authenticate as Admin. Send POST request to `/users` with `email='john.doe@org.com'` (already exists in active state for the organization).  
     * Expected Result: HTTP 400 Bad Request or 409 Conflict. Error message indicating duplicate email.  
   * **Test Case 1.2.7 (Create User \- Invalid Role):**  
     * Action: Authenticate as Admin. Send POST request to `/users` with `role='InvalidRole'`.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating invalid role.  
   * **Test Case 1.2.8 (Update User \- Invalid Department ID):**  
     * Action: Authenticate as Admin. Send PUT request to `/users/<user_id>` with `departmentId=<non_existent_dept_id>`.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating invalid foreign key.  
   * **Test Case 1.2.9 (RBAC \- Non-Admin User):**  
     * Action: Authenticate as 'BCM Manager'. Attempt POST /users.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 1.2.10 (Department Head Linkage):**  
     * Pre-requisite: Create a department (FR 1.1) and assign a user as its Department Head (FR 1.2).  
     * Action: Update the email address of the user who is a Department Head via People Management.  
     * Expected Result: The Department display (FR 1.1) continues to correctly show the linked Department Head, with the updated email (if displayed), and the link is not broken.  
   * **Test Case 1.2.11 (Process Owner Linkage):**  
     * Pre-requisite: Create a process (FR 1.3 \- *when implemented*) and assign a user as its Process Owner.  
     * Action: Update the first name of the user who is a Process Owner via People Management.  
     * Expected Result: The Process display (FR 1.3 \- *when implemented*) continues to correctly show the linked Process Owner with the updated name, and the link is not broken.

---

### **FR 1.3: Business Process Management**

#### **User Story: As an Admin or Department Head, I want to define and manage business processes within each department so that I can initiate BIA for them and track their details.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `processes` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per department), `description` (TEXT), `processOwnerId` (FK to `users.id`), `departmentId` (FK to `departments.id`), `sla` (VARCHAR), `tat` (VARCHAR), `seasonality` (VARCHAR), `peakTimes` (VARCHAR), `frequency` (VARCHAR), `numTeamMembers` (INT), `finalImpactScore` (FLOAT, nullable), `finalRTO` (VARCHAR, nullable), `isActive` (BOOLEAN, default TRUE).  
   * Create `process_locations` junction table: `processId` (FK), `locationId` (FK), composite PK.  
   * Create `process_applications` junction table: `processId` (FK), `applicationId` (FK), composite PK.  
   * Create `process_dependencies` table: `id` (PK, AUTO\_INCREMENT), `processId` (FK to `processes.id`), `dependentProcessId` (FK to `processes.id`), `dependencyType` (ENUM: 'Upstream', 'Downstream').  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for Process (Create, Read, Update).  
   * Create API endpoints:  
     * `POST /processes`: To create a new business process.  
       * Input validation: `name` is unique within `departmentId`. FKs (`processOwnerId`, `departmentId`) must exist. `locationIds` must be a subset of the selected `departmentId`'s locations. `applicationIds` and `dependentProcessIds` must exist.  
       * Assign `organizationId`.  
     * `GET /processes`: To retrieve a list of processes (filter by `organizationId`, `departmentId`, sort by `name`).  
     * `GET /processes/{id}`: To retrieve a single process by ID.  
     * `PUT /processes/{id}`: To update an existing process.  
       * Input validation: `name` uniqueness check during update. Location subset check.  
     * `DELETE /processes/{id}`: To soft delete (mark `isActive=FALSE`) a process.  
   * Implement logic for linking/unlinking multiple applications, locations, and upstream/downstream dependencies.  
   * Ensure all API endpoints respect `organizationId`.  
   * Implement RBAC: Only 'Admin' or 'Department Head' (for their department's processes) can create/edit/delete processes.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'Process Management'.  
   * Build a UI for adding a business process:  
     * Text inputs for 'Process Name', 'Process Description', 'SLA', 'TAT', 'Seasonality', 'Peak Times', 'Frequency'.  
     * Dropdown for 'Process Owner' (from People data).  
     * Dropdown for 'Department' (from Department data).  
     * Numeric input for 'Number of Team Members'.  
     * Multi-select dropdown for 'Applications Used' (populates from Application data, linked to FR 1.4).  
     * Multi-select dropdown for 'Locations' (filters based on selected Department's locations).  
     * Multi-select dropdowns for 'Upstream Dependency' and 'Downstream Dependency' (populates from other Process data).  
     * 'Submit' button.  
   * Build a UI to display processes in a list/table, showing Name, Department, Owner, etc.  
   * Implement 'Edit' button for each process: allows full updates.  
   * Implement 'Delete' button (soft delete).  
   * Implement client-side validation.  
   * Integrate with backend API.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 1.3: Business Process Management.**

---

**Test Cases for FR 1.3: Business Process Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 1.3. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 1.3.1 (Create Process \- Success):**  
     * Pre-requisite: Valid Department, Process Owner, Locations, Applications.  
     * Action: Authenticate as Admin. Send POST request to `/processes` with valid data: `name='Order Fulfillment'`, `departmentId=<dept_id>`, `processOwnerId=<owner_id>`, `locations=[<loc_id1>]`, `applicationsUsed=[<app_id1>]`, `upstreamDependencies=[<proc_id_A>]`, `downstreamDependencies=[<proc_id_B>]`.  
     * Expected Result: HTTP 201 Created. Process, `process_locations`, `process_applications`, `process_dependencies` records created.  
   * **Test Case 1.3.2 (Retrieve Processes):**  
     * Action: Authenticate as Admin. Send GET request to `/processes`.  
     * Expected Result: HTTP 200 OK. List includes 'Order Fulfillment'.  
   * **Test Case 1.3.3 (Update Process \- Success):**  
     * Action: Authenticate as Admin. Send PUT request to `/processes/<order_fulfillment_id>` with updated `sla='4 Hours'`, `locations=[<loc_id1>, <loc_id2>]`.  
     * Expected Result: HTTP 200 OK. Process and associated junction table records updated.  
   * **Test Case 1.3.4 (Delete Process \- Soft Delete):**  
     * Action: Authenticate as Admin. Send DELETE request to `/processes/<order_fulfillment_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` set to `FALSE`.  
2. **Edge Case Tests:**

   * **Test Case 1.3.5 (Create Process \- Duplicate Name in Department):**  
     * Action: Send POST request to `/processes` with `name='Order Fulfillment'` and same `departmentId`.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating duplicate process name for department.  
   * **Test Case 1.3.6 (Create Process \- Location not in Department's Locations):**  
     * Action: Send POST request to `/processes` with `departmentId=<dept_id>` and `locations=[<loc_id_not_in_dept>]`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid location for department.  
   * **Test Case 1.3.7 (Create Process \- Invalid Process Owner/Department/Application/Dependency FK):**  
     * Action: Send POST request with a non-existent FK.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid FK.  
   * **Test Case 1.3.8 (RBAC \- Department Head for Other Department):**  
     * Pre-requisite: Create a process in Department A. Authenticate as Department Head of Department B.  
     * Action: Attempt POST/PUT/DELETE /processes for a process in Department A.  
     * Expected Result: HTTP 403 Forbidden.  
   * **Test Case 1.3.9 (RBAC \- Process Owner):**  
     * Pre-requisite: Authenticate as Process Owner.  
     * Action: Attempt POST/PUT/DELETE /processes.  
     * Expected Result: HTTP 403 Forbidden (Process Owners can only modify their own assigned process info, not create/delete processes).  
3. **Regression Test Cases:**

   * **Test Case 1.3.10 (Department Head Linkage):**  
     * Pre-requisite: Process created with a Process Owner linked to a Department.  
     * Action: Update `description` of the linked Department (FR 1.1).  
     * Expected Result: Process display (FR 1.3 UI) accurately shows the correct Department information.  
   * **Test Case 1.3.11 (Process Owner Details Update):**  
     * Pre-requisite: Process created with a Process Owner.  
     * Action: Update the `firstName` of the Process Owner via People Management (FR 1.2).  
     * Expected Result: Process display (FR 1.3 UI) accurately shows the updated Process Owner name.  
   * **Test Case 1.3.12 (Application Linkage):**  
     * Pre-requisite: Process created, linked to an Application.  
     * Action: Update `description` of the linked Application (FR 1.4 \- *when implemented*).  
     * Expected Result: Process display (FR 1.3 UI) accurately shows the correct Application information.

---

### **FR 1.4: Application Management**

#### **User Story: As an Admin, I want to register and manage applications used by the organization so that I can understand their dependencies on business processes and track their characteristics.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create an `applications` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per organization), `appOwnerId` (FK to `users.id`, nullable), `type` (ENUM: 'SaaS', 'Owned'), `hostedOn` (VARCHAR), `workarounds` (TEXT), `derivedRTO` (VARCHAR, nullable), `isActive` (BOOLEAN, default TRUE).  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for Application (Create, Read, Update).  
   * Create API endpoints:  
     * `POST /applications`: To create a new application.  
       * Input validation: `name` is unique per `organizationId`. `appOwnerId` must exist if provided. `type` must be 'SaaS' or 'Owned'.  
       * Assign `organizationId`.  
     * `GET /applications`: To retrieve a list of applications (filter by `organizationId`, sort by `name`).  
     * `GET /applications/{id}`: To retrieve a single application by ID.  
       * Include derived `dependentProcesses` (processes that link to this application via `process_applications` table) and `derivedRTO` (will be populated in Epic 4).  
     * `PUT /applications/{id}`: To update an existing application.  
     * `DELETE /applications/{id}`: To soft delete (mark `isActive=FALSE`) an application.  
   * Ensure all API endpoints respect `organizationId`.  
   * Implement RBAC: Only 'Admin' can create/edit/delete applications.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'Application Management'.  
   * Build a UI for adding an application:  
     * Text inputs for 'Application Name', 'Hosted On', 'Workarounds'.  
     * Dropdown for 'App Owner' (from People data).  
     * Radio buttons/dropdown for 'Type' (SaaS, Owned).  
     * 'Submit' button.  
   * Build a UI to display applications in a list/table, showing Name, Type, Owner, etc.  
   * Implement 'Edit' button for each application: allows full updates.  
   * Implement 'Delete' button (soft delete).  
   * Implement client-side validation.  
   * Integrate with backend API.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 1.4: Application Management.**

---

**Test Cases for FR 1.4: Application Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 1.4. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 1.4.1 (Create Application \- Success):**  
     * Pre-requisite: Valid Application Owner.  
     * Action: Authenticate as Admin. Send POST request to `/applications` with valid data: `name='CRM System'`, `appOwnerId=<owner_id>`, `type='SaaS'`, `hostedOn='Cloud Provider'`, `workarounds='Manual data entry'`.  
     * Expected Result: HTTP 201 Created. Application record created.  
   * **Test Case 1.4.2 (Retrieve Applications):**  
     * Action: Authenticate as Admin. Send GET request to `/applications`.  
     * Expected Result: HTTP 200 OK. List includes 'CRM System'.  
   * **Test Case 1.4.3 (Update Application \- Success):**  
     * Action: Authenticate as Admin. Send PUT request to `/applications/<crm_system_id>` with updated `type='Owned'`, `hostedOn='On-Premise Server A'`.  
     * Expected Result: HTTP 200 OK. Application record updated.  
   * **Test Case 1.4.4 (Delete Application \- Soft Delete):**  
     * Action: Authenticate as Admin. Send DELETE request to `/applications/<crm_system_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` set to `FALSE`.  
   * **Test Case 1.4.5 (Dependent Processes Derivation):**  
     * Pre-requisite: Create a process (FR 1.3) and link 'CRM System' as an application used by it.  
     * Action: Send GET request to `/applications/<crm_system_id>`.  
     * Expected Result: HTTP 200 OK. The response includes the linked process in `dependentProcesses`.  
2. **Edge Case Tests:**

   * **Test Case 1.4.6 (Create Application \- Duplicate Name):**  
     * Action: Send POST request to `/applications` with `name='CRM System'` (already exists in active state for the organization).  
     * Expected Result: HTTP 400 Bad Request. Error message indicating duplicate application name.  
   * **Test Case 1.4.7 (Create Application \- Invalid Type):**  
     * Action: Send POST request with `type='InvalidType'`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid enum value.  
   * **Test Case 1.4.8 (Create Application \- Invalid App Owner FK):**  
     * Action: Send POST request with a non-existent `appOwnerId`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid foreign key.  
   * **Test Case 1.4.9 (RBAC \- Non-Admin User):**  
     * Action: Authenticate as 'Process Owner'. Attempt POST /applications.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 1.4.10 (App Owner Details Update):**  
     * Pre-requisite: Application created with an App Owner.  
     * Action: Update the `lastName` of the App Owner via People Management (FR 1.2).  
     * Expected Result: Application display (FR 1.4 UI) accurately shows the updated App Owner name.  
   * **Test Case 1.4.11 (Process-Application Linkage):**  
     * Pre-requisite: Application created and linked to a process (FR 1.3).  
     * Action: Update the `description` of the linked process (FR 1.3).  
     * Expected Result: The link between the application and process remains intact and visible in the application's details, even if the process data changes.

---

### **FR 1.5: Location Management**

#### **User Story: As an Admin, I want to define and manage organizational locations so that I can track where departments, people, and applications are physically situated.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `locations` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per organization), `address` (TEXT), `city` (VARCHAR), `country` (VARCHAR), `timeZone` (VARCHAR), `isActive` (BOOLEAN, default TRUE).  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for Location (Create, Read, Update).  
   * Create API endpoints:  
     * `POST /locations`: To create a new location.  
       * Input validation: `name` is unique per `organizationId`. `timeZone` should be selected from a predefined list (e.g., IANA Time Zone Database names, can be simplified for Phase 1 to a fixed list).  
       * Assign `organizationId`.  
     * `GET /locations`: To retrieve a list of locations (filter by `organizationId`, sort by `name`).  
     * `GET /locations/{id}`: To retrieve a single location by ID.  
     * `PUT /locations/{id}`: To update an existing location.  
     * `DELETE /locations/{id}`: To soft delete (mark `isActive=FALSE`) a location.  
   * Ensure all API endpoints respect `organizationId`.  
   * Implement RBAC: Only 'Admin' can create/edit/delete locations.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'Location Management'.  
   * Build a UI for adding a location:  
     * Text inputs for 'Name', 'Address', 'City', 'Country'.  
     * Dropdown for 'Time Zone' (populates from a predefined list).  
     * 'Submit' button.  
   * Build a UI to display locations in a list/table.  
   * Implement 'Edit' and 'Delete' buttons.  
   * Implement client-side validation.  
   * Integrate with backend API.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 1.5: Location Management.**

---

**Test Cases for FR 1.5: Location Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 1.5. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 1.5.1 (Create Location \- Success):**  
     * Action: Authenticate as Admin. Send POST request to `/locations` with valid data: `name='Head Office'`, `address='123 Main St'`, `city='Bengaluru'`, `country='India'`, `timeZone='Asia/Kolkata'`.  
     * Expected Result: HTTP 201 Created. Location record created.  
   * **Test Case 1.5.2 (Retrieve Locations):**  
     * Action: Authenticate as Admin. Send GET request to `/locations`.  
     * Expected Result: HTTP 200 OK. List includes 'Head Office'.  
   * **Test Case 1.5.3 (Update Location \- Success):**  
     * Action: Authenticate as Admin. Send PUT request to `/locations/<head_office_id>` with updated `address='456 New Rd'`, `timeZone='Europe/London'`.  
     * Expected Result: HTTP 200 OK. Location record updated.  
   * **Test Case 1.5.4 (Delete Location \- Soft Delete):**  
     * Action: Authenticate as Admin. Send DELETE request to `/locations/<head_office_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` set to `FALSE`.  
2. **Edge Case Tests:**

   * **Test Case 1.5.5 (Create Location \- Duplicate Name):**  
     * Action: Send POST request to `/locations` with `name='Head Office'` (already exists).  
     * Expected Result: HTTP 400 Bad Request. Error message indicating duplicate location name.  
   * **Test Case 1.5.6 (Create Location \- Invalid Time Zone):**  
     * Action: Send POST request with `timeZone='InvalidTimeZone'`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid time zone.  
   * **Test Case 1.5.7 (RBAC \- Non-Admin User):**  
     * Action: Authenticate as 'BCM Manager'. Attempt POST /locations.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 1.5.8 (Department Location Linkage):**  
     * Pre-requisite: Create a Department (FR 1.1) and link a Location to it.  
     * Action: Update the `city` of the linked Location via Location Management.  
     * Expected Result: The Department display (FR 1.1 UI) accurately shows the correct Location information.  
   * **Test Case 1.5.9 (Person Location Linkage):**  
     * Pre-requisite: Create a Person (FR 1.2) and link a Location to them.  
     * Action: Update the `address` of the linked Location via Location Management.  
     * Expected Result: The Person display (FR 1.2 UI) accurately shows the correct Location information.  
   * **Test Case 1.5.10 (Process Location Linkage):**  
     * Pre-requisite: Create a Process (FR 1.3) and link a Location to it.  
     * Action: Update the `name` of the linked Location via Location Management.  
     * Expected Result: The Process display (FR 1.3 UI) accurately shows the correct Location information.

---

### **FR 1.6: Vendor Management**

#### **User Story: As an Admin, I want to register and manage vendors so that I can track their involvement with applications and understand their impact on processes.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `vendors` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per organization), `location` (VARCHAR), `services` (TEXT), `timeToImpact` (VARCHAR, e.g., '2 hours', '1 day'), `isActive` (BOOLEAN, default TRUE).  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for Vendor (Create, Read, Update).  
   * Create API endpoints:  
     * `POST /vendors`: To create a new vendor.  
       * Input validation: `name` is unique per `organizationId`. `timeToImpact` can be structured (e.g., numeric value \+ unit: 'hours', 'days').  
       * Assign `organizationId`.  
     * `GET /vendors`: To retrieve a list of vendors (filter by `organizationId`, sort by `name`).  
     * `GET /vendors/{id}`: To retrieve a single vendor by ID.  
     * `PUT /vendors/{id}`: To update an existing vendor.  
     * `DELETE /vendors/{id}`: To soft delete (mark `isActive=FALSE`) a vendor.  
   * Ensure all API endpoints respect `organizationId`.  
   * Implement RBAC: Only 'Admin' can create/edit/delete vendors.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'Vendor Management'.  
   * Build a UI for adding a vendor:  
     * Text inputs for 'Name of Vendor', 'Location', 'Services'.  
     * Dropdown/text input for 'Time to Impact in case of Unavailability'.  
     * 'Submit' button.  
   * Build a UI to display vendors in a list/table.  
   * Implement 'Edit' and 'Delete' buttons.  
   * Implement client-side validation.  
   * Integrate with backend API.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 1.6: Vendor Management.**

---

**Test Cases for FR 1.6: Vendor Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 1.6. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 1.6.1 (Create Vendor \- Success):**  
     * Action: Authenticate as Admin. Send POST request to `/vendors` with valid data: `name='CloudServ Inc.'`, `location='USA'`, `services='Cloud Hosting'`, `timeToImpact='8 hours'`.  
     * Expected Result: HTTP 201 Created. Vendor record created.  
   * **Test Case 1.6.2 (Retrieve Vendors):**  
     * Action: Authenticate as Admin. Send GET request to `/vendors`.  
     * Expected Result: HTTP 200 OK. List includes 'CloudServ Inc.'.  
   * **Test Case 1.6.3 (Update Vendor \- Success):**  
     * Action: Authenticate as Admin. Send PUT request to `/vendors/<cloudserv_id>` with updated `services='Managed IT Services'`, `timeToImpact='24 hours'`.  
     * Expected Result: HTTP 200 OK. Vendor record updated.  
   * **Test Case 1.6.4 (Delete Vendor \- Soft Delete):**  
     * Action: Authenticate as Admin. Send DELETE request to `/vendors/<cloudserv_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` set to `FALSE`.  
2. **Edge Case Tests:**

   * **Test Case 1.6.5 (Create Vendor \- Duplicate Name):**  
     * Action: Send POST request to `/vendors` with `name='CloudServ Inc.'` (already exists).  
     * Expected Result: HTTP 400 Bad Request. Error message indicating duplicate vendor name.  
   * **Test Case 1.6.6 (RBAC \- Non-Admin User):**  
     * Action: Authenticate as 'BCM Manager'. Attempt POST /vendors.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 1.6.7 (Application Vendor Linkage):**  
     * Pre-requisite: Create an Application (FR 1.4) and link a Vendor to it.  
     * Action: Update the `location` of the linked Vendor via Vendor Management.  
     * Expected Result: The Application display (FR 1.4 UI) accurately shows the correct Vendor information.

---

**Epic 1 Completion \- Final Checks**

**Prompt to Windsurf:** All User Stories within Epic 1 (FR 1.1 to FR 1.6) are now implemented, and their individual tests have passed. Now, execute the following Epic-level Regression Test Cases and Health Checks. Report the PASS/FAIL status for each. **DO NOT proceed to Epic 2 until ALL these tests pass.**

1. **Epic-Level Regression Test Cases:**

   * **Test Case E1.R.1 (Cross-Module Data Consistency):**  
     * Pre-requisite: At least one Department, Person, Process, Application, Location, and Vendor have been created and linked across modules.  
     * Action: Perform a series of updates across different modules (e.g., rename a Department, change a Person's location, update a Process's description).  
     * Expected Result: All linked records in other modules correctly reflect the updated information without breaking relationships or causing errors.  
   * **Test Case E1.R.2 (Soft Delete Propagation):**  
     * Pre-requisite: Create a complex data structure (e.g., Department \-\> People \-\> Process \-\> Application \-\> Vendor).  
     * Action: Soft delete a parent entity (e.g., a Department).  
     * Expected Result: The soft-deleted parent entity is not shown in default lists. Its linked children (people, processes) are still marked as belonging to that department but are handled gracefully (e.g., either also marked inactive or remain active but show inactive department, depending on future phase requirements for data visibility). Crucially, no hard deletes occurred.  
   * **Test Case E1.R.3 (Multi-Tenancy Isolation):**  
     * Pre-requisite: Create two separate organizations (`Org A`, `Org B`) and populate data (Departments, People, Processes, etc.) for both.  
     * Action: Authenticate as a user from `Org A`. Attempt to view/modify data belonging to `Org B` by directly querying or manipulating IDs.  
     * Expected Result: HTTP 403 Forbidden or 404 Not Found for any attempts to access `Org B`'s data from `Org A`'s context. Data from `Org B` should not be visible in `Org A`'s UI/API responses.  
2. **Epic-Level Health Checks:**

   * **Health Check E1.H.1 (Database Connection & Schema):**  
     * Action: Verify that the application can connect to the MySQL database and that all tables and relationships defined for Epic 1 are correctly present and indexed.  
     * Expected Result: Successful connection and schema validation.  
   * **Health Check E1.H.2 (API Endpoint Availability):**  
     * Action: Ping all Epic 1 API endpoints (`/departments`, `/users`, `/processes`, `/applications`, `/locations`, `/vendors`).  
     * Expected Result: All endpoints return a 200 OK (or appropriate 4xx for auth/validation issues, but not 5xx).  
   * **Health Check E1.H.3 (Basic UI Load):**  
     * Action: Attempt to load the main UI pages for Department, People, Process, Application, Location, and Vendor management.  
     * Expected Result: Pages load without critical errors or broken components.  
   * **Health Check E1.H.4 (Audit Log for CRUD operations \- Future):**  
     * *Note: This is a reference for future, more robust health checks. Not implemented in Phase 1 tasks.*  
     * Action: Verify that audit logs are correctly recording creation, update, and deletion events for Epic 1 entities.  
     * Expected Result: Audit trail is accurate and complete.

---

## **Epic 2: BIA Framework Configuration**

### **FR 2.1: BIA Categories Management**

#### **User Story: As a BCM Manager or CISO, I want to create, edit, or delete categories for BIA Impact Parameters so that I can group related impact types.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `bia_categories` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per organization), `description` (TEXT), `isActive` (BOOLEAN, default TRUE).  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for BIACategory (Create, Read, Update).  
   * Create API endpoints:  
     * `POST /bia_categories`: To create a new BIA category.  
       * Input validation: `name` is unique within the `organizationId`.  
       * Assign `organizationId`.  
     * `GET /bia_categories`: To retrieve a list of BIA categories (filter by `organizationId`, sort by `name`).  
     * `GET /bia_categories/{id}`: To retrieve a single BIA category by ID.  
     * `PUT /bia_categories/{id}`: To update an existing BIA category.  
       * Input validation: `name` uniqueness check during update.  
     * `DELETE /bia_categories/{id}`: To soft delete (mark `isActive=FALSE`) a BIA category.  
   * Ensure all API endpoints respect the user's `organizationId`.  
   * Implement RBAC: Only 'BCM Manager' or 'CISO' can create/edit/delete BIA categories.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'BIA Category Management'.  
   * Build a UI for category creation:  
     * Text input for 'Category Name'.  
     * Text area for 'Description'.  
     * 'Submit' button.  
   * Build a UI to display categories in a list/table.  
   * Implement 'Edit' and 'Delete' buttons for each category.  
   * Implement client-side validation for form inputs (e.g., required fields, unique name locally).  
   * Integrate with backend API endpoints for CRUD operations.  
   * Apply UI/UX design guidelines: Primary Colors (Blue), Heading Font (Outfit), Body Font (DM Sans), minimalist, clean.

**Windsurf, implement the above granular tasks for FR 2.1: BIA Categories Management.**

---

**Test Cases for FR 2.1: BIA Categories Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 2.1. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 2.1.1 (Create Category \- Success):**  
     * Action: Authenticate as BCM Manager. Send POST request to `/bia_categories` with valid data: `name='Financial'`, `description='Impact on financial stability'`.  
     * Expected Result: HTTP 201 Created. Category record created in `bia_categories` table with `isActive=TRUE`.  
   * **Test Case 2.1.2 (Retrieve Categories):**  
     * Action: Authenticate as BCM Manager. Send GET request to `/bia_categories`.  
     * Expected Result: HTTP 200 OK. List includes the newly created 'Financial' category.  
   * **Test Case 2.1.3 (Update Category \- Success):**  
     * Action: Authenticate as BCM Manager. Send PUT request to `/bia_categories/<financial_category_id>` with updated `name='Monetary Impact'`, `description='Direct and indirect financial losses'`.  
     * Expected Result: HTTP 200 OK. Category record updated in `bia_categories` table.  
   * **Test Case 2.1.4 (Delete Category \- Soft Delete):**  
     * Action: Authenticate as BCM Manager. Send DELETE request to `/bia_categories/<monetary_impact_category_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` column for the category record is set to `FALSE`.  
2. **Edge Case Tests:**

   * **Test Case 2.1.5 (Create Category \- Duplicate Name):**  
     * Action: Send POST request to `/bia_categories` with `name='Financial'` (already exists in active state for the organization).  
     * Expected Result: HTTP 400 Bad Request or 409 Conflict. Error message indicating duplicate category name.  
   * **Test Case 2.1.6 (Create Category \- Missing Mandatory Fields):**  
     * Action: Send POST request to `/bia_categories` with missing `name`.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating missing required field.  
   * **Test Case 2.1.7 (RBAC \- Unauthorized User):**  
     * Action: Authenticate as 'Process Owner' and attempt POST /bia\_categories.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 2.1.8 (Parameter Linkage):**  
     * Pre-requisite: Create a BIA Category (FR 2.1) and then create a BIA Parameter under it (FR 2.2 \- *when implemented*).  
     * Action: Update the `description` of the linked BIA Category via Category Management.  
     * Expected Result: The BIA Parameter display (FR 2.2 UI \- *when implemented*) accurately shows the correct Category information without breaking the link.

---

### **FR 2.2: BIA Parameters Management**

#### **User Story: As a BCM Manager or CISO, I want to create, edit, or delete parameters under categories for BIA so that I can define specific impact criteria.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `bia_parameters` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per category), `description` (TEXT), `categoryId` (FK to `bia_categories.id`), `ratingType` (ENUM: 'Qualitative', 'Quantitative'), `isActive` (BOOLEAN, default TRUE).  
   * Create a `bia_rating_definitions` table: `id` (PK, AUTO\_INCREMENT), `parameterId` (FK to `bia_parameters.id`), `ratingLabel` (VARCHAR, e.g., 'Low', '1-10'), `minRange` (FLOAT, nullable), `maxRange` (FLOAT, nullable), `score` (FLOAT), `order` (INT for sequence), `organizationId` (FK to `organizations.id`).  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for BIAParameter (Create, Read, Update) and BIARatingDefinition.  
   * Create API endpoints:  
     * `POST /bia_parameters`: To create a new BIA parameter.  
       * Input validation: `name` is unique within the `categoryId`. `categoryId` must exist. `ratingType` must be 'Qualitative' or 'Quantitative'. Ratings must be provided correctly (e.g., `minRange`/`maxRange` for quantitative, `ratingLabel`/`score` for both).  
       * Assign `organizationId`.  
     * `GET /bia_parameters`: To retrieve a list of BIA parameters (filter by `organizationId`, `categoryId`, sort by `name`).  
     * `GET /bia_parameters/{id}`: To retrieve a single BIA parameter by ID, including its associated `bia_rating_definitions`.  
     * `PUT /bia_parameters/{id}`: To update an existing BIA parameter and its associated rating definitions.  
       * Input validation: `name` uniqueness check during update. Handle updates to rating definitions (add, modify, delete).  
     * `DELETE /bia_parameters/{id}`: To soft delete (mark `isActive=FALSE`) a BIA parameter and its associated rating definitions.  
   * Ensure all API endpoints respect `organizationId`.  
   * Implement RBAC: Only 'BCM Manager' or 'CISO' can create/edit/delete BIA parameters.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'BIA Parameter Management'.  
   * Build a UI for parameter creation:  
     * Text input for 'Parameter Name', 'Description'.  
     * Dropdown for 'Category' (populates from FR 2.1).  
     * Radio buttons/dropdown for 'Rating Type' (Qualitative, Quantitative).  
     * **Conditional UI based on Rating Type:**  
       * For Qualitative: Dynamic fields to add 'Rating Label' (e.g., Nil, Low) and 'Score' (numeric). Allow adding/removing multiple ratings.  
       * For Quantitative: Dynamic fields to add 'Min Range' (numeric), 'Max Range' (numeric), 'Score' (numeric). Handle "Above X" for the last range (e.g., input '100+' implies min=100, max=null). Allow adding/removing multiple ranges.  
     * 'Submit' button.  
   * Build a UI to display parameters in a list/table, showing Name, Category, Type, and a summary of ratings/ranges.  
   * Implement 'Edit' and 'Delete' buttons for each parameter.  
   * Implement client-side validation (e.g., score validation, range overlap prevention for quantitative).  
   * Integrate with backend API endpoints for CRUD operations.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 2.2: BIA Parameters Management.**

---

**Test Cases for FR 2.2: BIA Parameters Management**

**Prompt to Windsurf:** Execute the following automated test cases for FR 2.2. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 2.2.1 (Create Qualitative Parameter \- Success):**  
     * Pre-requisite: Valid BIA Category.  
     * Action: Authenticate as BCM Manager. Send POST request to `/bia_parameters` with valid data: `name='Reputational Impact'`, `categoryId=<category_id>`, `ratingType='Qualitative'`, `ratings=[{'label':'Low', 'score':1}, {'label':'High', 'score':3}]`.  
     * Expected Result: HTTP 201 Created. Parameter and associated rating definitions created.  
   * **Test Case 2.2.2 (Create Quantitative Parameter \- Success):**  
     * Pre-requisite: Valid BIA Category.  
     * Action: Authenticate as BCM Manager. Send POST request to `/bia_parameters` with valid data: `name='Revenue Loss ($)'`, `categoryId=<category_id>`, `ratingType='Quantitative'`, `ratings=[{'minRange':0, 'maxRange':1000, 'score':1}, {'minRange':1001, 'maxRange':null, 'score':5, 'label':'Above 1000'}]`.  
     * Expected Result: HTTP 201 Created. Parameter and associated rating definitions created.  
   * **Test Case 2.2.3 (Retrieve Parameter with Ratings):**  
     * Action: Authenticate as BCM Manager. Send GET request to `/bia_parameters/<parameter_id>`.  
     * Expected Result: HTTP 200 OK. Response includes the parameter details and its `bia_rating_definitions`.  
   * **Test Case 2.2.4 (Update Parameter \- Change Ratings):**  
     * Action: Authenticate as BCM Manager. Send PUT request to update 'Reputational Impact' parameter, adding a new rating: `{'label':'Very High', 'score':4}`.  
     * Expected Result: HTTP 200 OK. Parameter updated, new rating definition added.  
   * \*\*Test Case 2.2.5 (Delete Parameter \- Soft Delete):  
     * Action: Authenticate as BCM Manager. Send DELETE request to `/bia_parameters/<parameter_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` set to `FALSE` for parameter and its rating definitions.  
2. **Edge Case Tests:**

   * **Test Case 2.2.6 (Create Parameter \- Duplicate Name in Category):**  
     * Action: Send POST request to `/bia_parameters` with `name='Reputational Impact'` and same `categoryId`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating duplicate parameter name for category.  
   * **Test Case 2.2.7 (Create Quantitative Parameter \- Overlapping Ranges):**  
     * Action: Send POST request for quantitative parameter with ranges like `[0-10, 5-20]`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating overlapping ranges.  
   * **Test Case 2.2.8 (Create Quantitative Parameter \- Gaps in Ranges):**  
     * Action: Send POST request for quantitative parameter with ranges like `[0-10, 12-20]`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating gaps in ranges (or handle as warning, depending on business logic \- for now, treat as error).  
   * **Test Case 2.2.9 (Create Parameter \- Invalid Category FK):**  
     * Action: Send POST request with a non-existent `categoryId`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid foreign key.  
   * **Test Case 2.2.10 (RBAC \- Unauthorized User):**  
     * Action: Authenticate as 'Process Owner'. Attempt POST /bia\_parameters.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 2.2.11 (Category Linkage after Category Update):**  
     * Pre-requisite: Create a BIA Category (FR 2.1) and a Parameter under it (FR 2.2).  
     * Action: Update the `name` of the linked BIA Category (FR 2.1).  
     * Expected Result: The BIA Parameter display (FR 2.2 UI) accurately shows the updated Category name.

---

### **FR 2.3: BIA Framework Builder**

#### **User Story: As a BCM Manager or CISO, I want to build a BIA framework by selecting parameters and assigning weightages so that I can define the BIA methodology.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `bia_frameworks` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `name` (VARCHAR, UNIQUE per organization), `formula` (VARCHAR, e.g., 'Weighted Average'), `thresholdValue` (FLOAT), `isActive` (BOOLEAN, default TRUE).  
   * Create a `bia_framework_parameters` junction table: `frameworkId` (FK to `bia_frameworks.id`), `parameterId` (FK to `bia_parameters.id`), `weightage` (FLOAT), composite PK.  
   * Create an `rto_options` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `label` (VARCHAR, e.g., '4 hours'), `valueInMinutes` (INT), `isActive` (BOOLEAN, default TRUE). Populate with default options: 1 hour, 2 hours, 4 hours, ..., 180 days.  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for BIAFramework (Create, Read, Update) and BIAFrameworkParameter.  
   * Create API endpoints:  
     * `POST /bia_frameworks`: To create a new BIA framework.  
       * Input validation: `name` is unique within `organizationId`. `parameterIds` must exist and correspond to active parameters. `weightages` for selected parameters must sum to 100\. `formula` must be from a predefined list (e.g., 'Weighted Average').  
       * Assign `organizationId`.  
     * `GET /bia_frameworks`: To retrieve a list of frameworks.  
     * `GET /bia_frameworks/{id}`: To retrieve a single framework by ID, including its parameters and weightages.  
     * `PUT /bia_frameworks/{id}`: To update an existing framework.  
     * `DELETE /bia_frameworks/{id}`: To soft delete a framework.  
   * Implement an API to retrieve RTO options.  
   * Implement logic to calculate and return a "sample calculation" for the selected formula based on given parameters, weightages, and their rating definitions. This will be an endpoint or a utility function used internally.  
   * Ensure all API endpoints respect `organizationId`.  
   * Implement RBAC: Only 'BCM Manager' or 'CISO' can create/edit/delete BIA frameworks.  
3. **Frontend (React/Tailwind):**  
   * Create a dedicated React component for 'BIA Framework Builder'.  
   * Build a multi-step UI for creating/editing a framework:  
     * Step 1: Input 'Framework Name', 'Threshold Value'.  
     * Step 2: Select 'Parameters' from a list (populates from FR 2.2).  
     * Step 3: For each selected parameter, allow assigning a 'Weightage' (numeric input). Display a running sum of weightages and validate that it equals 100% upon submission.  
     * Step 4: Select 'Formula' from a dropdown (e.g., 'Weighted Average').  
     * Dynamically display a 'Sample Calculation' preview based on selected parameters, weightages, and formula. This should show how a hypothetical set of ratings would result in an impact score.  
     * Display predefined RTO options (1 hour, 2 hours, etc.) for reference (read-only for now, direct editing not in scope for this FR but options should be visible for future BIA use).  
     * 'Save Framework' button.  
   * Build a UI to display configured frameworks.  
   * Implement 'Edit' and 'Delete' buttons.  
   * Implement client-side validation.  
   * Integrate with backend API.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 2.3: BIA Framework Builder.**

---

**Test Cases for FR 2.3: BIA Framework Builder**

**Prompt to Windsurf:** Execute the following automated test cases for FR 2.3. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next Epic until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 2.3.1 (Create Framework \- Success):**  
     * Pre-requisite: At least two BIA Parameters (FR 2.2).  
     * Action: Authenticate as BCM Manager. Send POST request to `/bia_frameworks` with valid data: `name='Standard BIA'`, `formula='Weighted Average'`, `thresholdValue=2.5`, `parameters=[{'parameterId':<param1_id>, 'weightage':60}, {'parameterId':<param2_id>, 'weightage':40}]`.  
     * Expected Result: HTTP 201 Created. Framework and `bia_framework_parameters` records created.  
   * **Test Case 2.3.2 (Retrieve Framework with Parameters):**  
     * Action: Authenticate as BCM Manager. Send GET request to `/bia_frameworks/<standard_bia_framework_id>`.  
     * Expected Result: HTTP 200 OK. Response includes framework details and its associated parameters with weightages.  
   * **Test Case 2.3.3 (Update Framework \- Change Parameters/Weightages):**  
     * Action: Authenticate as BCM Manager. Send PUT request to update 'Standard BIA' framework, modifying weightages or adding/removing parameters, ensuring sum is 100\.  
     * Expected Result: HTTP 200 OK. Framework and `bia_framework_parameters` updated.  
   * **Test Case 2.3.4 (Delete Framework \- Soft Delete):**  
     * Action: Authenticate as BCM Manager. Send DELETE request to `/bia_frameworks/<framework_id>`.  
     * Expected Result: HTTP 200 OK. `isActive` set to `FALSE` for framework and its associated parameters.  
   * **Test Case 2.3.5 (Sample Calculation Display):**  
     * Action: Select a framework in the UI.  
     * Expected Result: A "Sample Calculation" preview is displayed, accurately demonstrating how scores would be derived based on the selected formula, parameters, and weightages.  
   * **Test Case 2.3.6 (RTO Options Display):**  
     * Action: Access the BIA Framework Builder UI.  
     * Expected Result: Predefined RTO options (1 hour, 2 hours, etc.) are clearly displayed.  
2. **Edge Case Tests:**

   * **Test Case 2.3.7 (Create Framework \- Weightages Not Summing to 100):**  
     * Action: Send POST request to `/bia_frameworks` with `parameters` whose `weightage` sum is not 100\.  
     * Expected Result: HTTP 400 Bad Request. Error message indicating weightage sum validation failure.  
   * **Test Case 2.3.8 (Create Framework \- Duplicate Name):**  
     * Action: Send POST request to `/bia_frameworks` with `name='Standard BIA'` (already exists).  
     * Expected Result: HTTP 400 Bad Request. Error message indicating duplicate framework name.  
   * **Test Case 2.3.9 (Create Framework \- Invalid Parameter FK):**  
     * Action: Send POST request with a non-existent `parameterId`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid foreign key.  
   * **Test Case 2.3.10 (RBAC \- Unauthorized User):**  
     * Action: Authenticate as 'Process Owner'. Attempt POST /bia\_frameworks.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 2.3.11 (Parameter Details Update Impact):**  
     * Pre-requisite: Create a Framework (FR 2.3) that includes a specific Parameter (FR 2.2).  
     * Action: Update the `score` for one of the `rating_definitions` of that Parameter (FR 2.2).  
     * Expected Result: The 'Sample Calculation' in the Framework UI (FR 2.3) automatically reflects the updated scores of the underlying parameter.  
   * **Test Case 2.3.12 (Category Update Impact):**  
     * Pre-requisite: Create a Framework with Parameters, which belong to Categories (FR 2.1).  
     * Action: Update the `name` of a BIA Category (FR 2.1).  
     * Expected Result: The Framework UI (FR 2.3) still correctly displays or links to the parameters, and there are no broken references due to the category name change.

---

**Epic 2 Completion \- Final Checks**

**Prompt to Windsurf:** All User Stories within Epic 2 (FR 2.1 to FR 2.3) are now implemented, and their individual tests have passed. Now, execute the following Epic-level Regression Test Cases and Health Checks. Report the PASS/FAIL status for each. **DO NOT proceed to Epic 3 until ALL these tests pass.**

1. **Epic-Level Regression Test Cases:**

   * **Test Case E2.R.1 (Framework Integrity after Parameter Deactivation):**  
     * Pre-requisite: Create a BIA Framework that includes a parameter.  
     * Action: Soft delete the parameter that is part of the framework (via FR 2.2).  
     * Expected Result: The framework should still exist, but the deleted parameter should either be marked as inactive within the framework's definition or automatically removed from the framework's active parameters, without causing errors. The 'Sample Calculation' should adapt or indicate a missing parameter.  
   * **Test Case E2.R.2 (Multi-Tenancy Isolation):**  
     * Pre-requisite: Two organizations (`Org A`, `Org B`) with their own BIA categories, parameters, and frameworks.  
     * Action: Authenticate as a user from `Org A`. Attempt to view/modify BIA framework data belonging to `Org B`.  
     * Expected Result: HTTP 403 Forbidden or 404 Not Found for any attempts to access `Org B`'s data from `Org A`'s context. `Org B`'s BIA data should not be visible in `Org A`'s UI/API responses.  
2. **Epic-Level Health Checks:**

   * **Health Check E2.H.1 (Database Connection & Schema):**  
     * Action: Verify that the application can connect to the MySQL database and that all tables (`bia_categories`, `bia_parameters`, `bia_rating_definitions`, `bia_frameworks`, `bia_framework_parameters`, `rto_options`) and relationships defined for Epic 2 are correctly present and indexed.  
     * Expected Result: Successful connection and schema validation.  
   * **Health Check E2.H.2 (API Endpoint Availability):**  
     * Action: Ping all Epic 2 API endpoints (`/bia_categories`, `/bia_parameters`, `/bia_frameworks`).  
     * Expected Result: All endpoints return a 200 OK (or appropriate 4xx for auth/validation issues, but not 5xx).  
   * **Health Check E2.H.3 (Basic UI Load):**  
     * Action: Attempt to load the main UI pages for BIA Category, Parameter, and Framework management.  
     * Expected Result: Pages load without critical errors or broken components.

---

## **Epic 3: BIA Execution and Workflow**

### **FR 3.1: BIA Initiation**

#### **User Story: As a BCM Manager or CISO, I want to initiate a BIA for a department and its related processes based on a defined frequency.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `bia_instances` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `departmentId` (FK to `departments.id`), `frameworkId` (FK to `bia_frameworks.id`), `initiationDate` (DATETIME), `frequency` (ENUM: 'Annually', 'Bi-annually', 'Biennially'), `status` (ENUM: 'Initiated', 'Submitted for Review', 'Review in Progress', 'Approved'), `isActive` (BOOLEAN, default TRUE).  
   * Create a `bia_process_inputs` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `biaInstanceId` (FK to `bia_instances.id`), `processId` (FK to `processes.id`), `processOwnerId` (FK to `users.id`), `recommendedRTOId` (FK to `rto_options.id`, nullable), `rtoJustification` (TEXT, nullable), `submittedDate` (DATETIME, nullable), `reviewerComments` (TEXT, nullable), `departmentHeadApprovalNote` (TEXT, nullable), `finalApprovedRTOId` (FK to `rto_options.id`, nullable), `finalImpactScore` (FLOAT, nullable), `status` (ENUM: 'Initiated', 'Submitted for Review', 'Review in Progress', 'Approved'). This status mirrors the overall BIA instance status for that specific process.  
   * Note: `bia_process_parameter_ratings` table will be created in FR 3.2.  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for BIAInstance (Create, Read, Update) and BIAProcessInput.  
   * Create API endpoint:  
     * `POST /bia_instances/initiate`: To initiate a new BIA.  
       * Input: `departmentId` (mandatory), `frameworkId` (mandatory), `frequency` (mandatory).  
       * Logic:  
         * Create a `bia_instances` record.  
         * Retrieve all active processes associated with the `departmentId`.  
         * For each process, create a `bia_process_inputs` record, setting `status` to 'Initiated', linking `processId`, `processOwnerId`, and `biaInstanceId`.  
         * Send automated in-app and email notifications to the assigned `processOwnerId` for each new `bia_process_inputs` record.  
       * Assign `organizationId` to all new records.  
   * `GET /bia_instances`: To retrieve a list of BIA instances (filter by `organizationId`, status, department).  
   * `GET /bia_process_inputs`: To retrieve individual process BIA inputs (filter by `organizationId`, `biaInstanceId`, `processId`, `status`).  
   * Implement RBAC: Only 'BCM Manager' or 'CISO' can initiate a BIA.  
3. **Frontend (React/Tailwind):**  
   * Create a UI for BIA Initiation:  
     * Dropdown to select a 'Department' (from FR 1.1).  
     * Dropdown to select a 'BIA Framework' (from FR 2.3).  
     * Dropdown to select 'Frequency' (Annually, Bi-annually, Biennially).  
     * 'Initiate BIA' button.  
   * Display a dashboard/list of initiated BIA instances, showing: Department, Framework, Initiation Date, Frequency, Overall Status.  
   * Implement a mechanism to track BIA status: Initiated, Submitted for Review, Review in Progress, Approved.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 3.1: BIA Initiation.**

---

**Test Cases for FR 3.1: BIA Initiation**

**Prompt to Windsurf:** Execute the following automated test cases for FR 3.1. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 3.1.1 (Initiate BIA for Department \- Success):**  
     * Pre-requisite: A valid Department (FR 1.1) with at least 2 active Processes (FR 1.3), a valid BIA Framework (FR 2.3), and a valid Process Owner for each process.  
     * Action: Authenticate as BCM Manager. Send POST request to `/bia_instances/initiate` with `departmentId=<valid_dept_id>`, `frameworkId=<valid_framework_id>`, `frequency='Annually'`.  
     * Expected Result: HTTP 201 Created. A new `bia_instances` record is created. Two `bia_process_inputs` records are created, one for each process, linked to the `bia_instance_id`, with `status='Initiated'` and correct `processOwnerId`. Automated notifications (simulate or log receipt) are sent to process owners.  
   * **Test Case 3.1.2 (Retrieve BIA Instances and Process Inputs):**  
     * Action: Authenticate as BCM Manager. Send GET requests to `/bia_instances` and `/bia_process_inputs` filtered by the newly created instance.  
     * Expected Result: HTTP 200 OK. Records are retrieved, reflecting the 'Initiated' status.  
   * **Test Case 3.1.3 (Notification Trigger):**  
     * Action: Initiate a BIA.  
     * Expected Result: System logs indicate an attempt to send notifications to the relevant Process Owners (mock or actual email client integration is out of scope for automated testing, but logging should confirm).  
2. **Edge Case Tests:**

   * **Test Case 3.1.4 (Initiate BIA \- Invalid Department/Framework ID):**  
     * Action: Send POST request to `/bia_instances/initiate` with a non-existent `departmentId` or `frameworkId`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid foreign key.  
   * **Test Case 3.1.5 (Initiate BIA \- Department with No Processes):**  
     * Pre-requisite: A valid Department with no active Processes.  
     * Action: Send POST request to `/bia_instances/initiate` for this department.  
     * Expected Result: HTTP 201 Created. `bia_instances` record is created, but no `bia_process_inputs` records are created. (Or, if business logic requires at least one process, return 400 with an appropriate message). Assume it creates instance but no process inputs.  
   * **Test Case 3.1.6 (RBAC \- Unauthorized User):**  
     * Action: Authenticate as 'Process Owner'. Attempt POST /bia\_instances/initiate.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 3.1.7 (Department Deactivation Impact on BIA Initiation):**  
     * Pre-requisite: Soft delete a Department (FR 1.1).  
     * Action: Attempt to initiate a BIA for the soft-deleted Department.  
     * Expected Result: HTTP 400 Bad Request or UI prevents selection. No new BIA instance can be created for an inactive department.  
   * **Test Case 3.1.8 (Process Deactivation Impact on BIA Initiation):**  
     * Pre-requisite: Soft delete a Process (FR 1.3) that belongs to a Department.  
     * Action: Initiate a BIA for that Department.  
     * Expected Result: The soft-deleted process is *not* included in the `bia_process_inputs` for the new BIA instance.  
   * **Test Case 3.1.9 (Framework Deactivation Impact on BIA Initiation):**  
     * Pre-requisite: Soft delete a BIA Framework (FR 2.3).  
     * Action: Attempt to initiate a BIA using the soft-deleted Framework.  
     * Expected Result: HTTP 400 Bad Request or UI prevents selection.

---

### **FR 3.2: BIA Questionnaire Completion (Process Owner)**

#### **User Story: As a Process Owner, I want to provide detailed impact ratings and process dependencies for my assigned BIA questionnaires.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * Create a `bia_process_parameter_ratings` table: `id` (PK, AUTO\_INCREMENT), `organizationId` (FK to `organizations.id`), `biaProcessInputId` (FK to `bia_process_inputs.id`), `parameterId` (FK to `bia_parameters.id`), `selectedRatingValue` (VARCHAR, stores chosen label/range text), `qualitativeDescription` (TEXT, nullable), `scoreGivenForRating` (FLOAT).  
   * Update `processes` table to include columns for `upstream_dependencies` (TEXT/JSON) and `downstream_dependencies` (TEXT/JSON) or ensure `process_dependencies` table (from FR 1.3) is used and updated. (Given the requirement for selection from a list, using `process_dependencies` is preferred).  
2. **Backend (FastAPI):**  
   * Implement Pydantic models for BIAProcessParameterRating.  
   * Create API endpoints:  
     * `GET /bia_process_inputs/{id}`: To retrieve a specific BIA questionnaire for a process.  
       * Include details of the associated Process, the Framework's Parameters and their Rating Definitions, and any previously saved ratings.  
       * Ensure only the assigned Process Owner or BCM/CISO/Admin/Department Head can access.  
     * `PUT /bia_process_inputs/{id}/save_draft`: To save BIA input as a draft.  
       * Input: `parameterRatings` (list of `bia_process_parameter_ratings`), `recommendedRTOId`, `rtoJustification`, `upstreamDependencies`, `downstreamDependencies`.  
       * Logic: Save provided data, update `bia_process_inputs` status to 'In Progress' if not already. Do not change overall `bia_instance` status.  
     * `PUT /bia_process_inputs/{id}/submit_for_review`: To submit BIA for review.  
       * Input: All data from `save_draft` (ensure completeness).  
       * Logic: Update `bia_process_inputs` status to 'Submitted for Review'. Set `submittedDate`. Send automated notification to BCM Manager.  
       * **Crucially, implement the impact score calculation here**:  
         * Retrieve the BIA Framework (from `bia_instance.frameworkId`).  
         * For each submitted `parameterRating`, retrieve its `scoreGivenForRating`.  
         * Apply the framework's `formula` (e.g., Weighted Average) using the parameter `weightages` to calculate the `finalImpactScore`.  
         * Store this `finalImpactScore` in `bia_process_inputs.finalImpactScore`.  
     * `GET /rto_options`: To retrieve the list of predefined RTO options (from FR 2.3).  
   * Implement RBAC: Only the assigned 'Process Owner' can save/submit their own BIA. 'BCM Manager', 'CISO', 'Admin', 'Department Head' can read.  
3. **Frontend (React/Tailwind):**  
   * Create a UI for Process Owners to access their assigned BIAs (e.g., a dashboard showing pending BIAs).  
   * Build an intuitive BIA questionnaire form for a specific process:  
     * Display process details (Name, Department, Description).  
     * Dynamically generate input fields for each BIA Parameter from the selected Framework:  
       * For Qualitative parameters: Radio buttons or dropdowns for `ratingLabel`s with corresponding scores.  
       * For Quantitative parameters: Input fields for value with a hint about ranges, and display the corresponding score.  
       * Text area for `qualitativeDescription` for each parameter.  
     * Multi-select dropdowns for 'Upstream Process Dependencies' and 'Downstream Process Dependencies' (populate from all active processes \- FR 1.3).  
     * Dropdown to select a 'Recommended RTO' (from FR 2.3).  
     * Text area for 'Justification' for the recommended RTO.  
     * Display the `calculated impact score` dynamically (update as ratings are selected/entered).  
     * 'Save Draft' button.  
     * 'Submit for Review' button (with client-side validation for completeness).  
   * Apply UI/UX design guidelines, including semantic colors for status updates (e.g., 'In Progress').

**Windsurf, implement the above granular tasks for FR 3.2: BIA Questionnaire Completion.**

---

**Test Cases for FR 3.2: BIA Questionnaire Completion**

**Prompt to Windsurf:** Execute the following automated test cases for FR 3.2. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 3.2.1 (Access BIA Questionnaire \- Success):**  
     * Pre-requisite: BIA initiated (FR 3.1), user is the assigned Process Owner.  
     * Action: Authenticate as Process Owner. Send GET request to `/bia_process_inputs/<process_input_id>`.  
     * Expected Result: HTTP 200 OK. Response contains process details, framework parameters, and RTO options.  
   * **Test Case 3.2.2 (Save BIA as Draft \- Success):**  
     * Action: Authenticate as Process Owner. Send PUT request to `/bia_process_inputs/<process_input_id>/save_draft` with partial ratings, selected recommended RTO, justification, and some dependencies.  
     * Expected Result: HTTP 200 OK. `bia_process_inputs` record status updated to 'In Progress' (if it was 'Initiated'). `bia_process_parameter_ratings` records are created/updated. `recommendedRTOId` and `rtoJustification` are saved. Process dependencies are updated.  
   * **Test Case 3.2.3 (Dynamic Impact Score Calculation \- UI/Backend Interaction):**  
     * Action: Simulate UI interaction where Process Owner selects/enters rating for a parameter.  
     * Expected Result: The displayed `calculated impact score` updates dynamically in the UI. (Backend: Verify the API endpoint for `save_draft` or `submit_for_review` correctly calculates and stores the score based on the framework).  
   * **Test Case 3.2.4 (Submit BIA for Review \- Success):**  
     * Action: Authenticate as Process Owner. Send PUT request to `/bia_process_inputs/<process_input_id>/submit_for_review` with complete data (all required ratings provided).  
     * Expected Result: HTTP 200 OK. `bia_process_inputs` record status updated to 'Submitted for Review'. `submittedDate` is set. `finalImpactScore` is calculated and stored. Automated notification sent to BCM Manager.  
   * **Test Case 3.2.5 (Process Dependencies Mapping):**  
     * Action: During `save_draft` or `submit_for_review`, link valid upstream/downstream processes.  
     * Expected Result: `process_dependencies` table is updated correctly for the associated process.  
2. **Edge Case Tests:**

   * **Test Case 3.2.6 (Submit Incomplete BIA):**  
     * Action: Authenticate as Process Owner. Send PUT request to `/bia_process_inputs/<process_input_id>/submit_for_review` with missing required ratings (e.g., not all parameters addressed).  
     * Expected Result: HTTP 400 Bad Request. Error message indicating incomplete BIA.  
   * **Test Case 3.2.7 (Invalid RTO Option):**  
     * Action: Submit BIA with a non-existent `recommendedRTOId`.  
     * Expected Result: HTTP 400 Bad Request.  
   * **Test Case 3.2.8 (Submit BIA \- Non-assigned Process Owner):**  
     * Action: Authenticate as a different Process Owner. Attempt to submit BIA for a process not assigned to them.  
     * Expected Result: HTTP 403 Forbidden.  
   * **Test Case 3.2.9 (Submit BIA \- Non-Process Owner Role):**  
     * Action: Authenticate as 'Admin'. Attempt to submit BIA (they should only review/approve).  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 3.2.10 (BIA Framework Changes Impact on Questionnaire):**  
     * Pre-requisite: BIA initiated. Update a BIA Parameter's rating definitions (FR 2.2) or a Framework's weightages (FR 2.3).  
     * Action: Access the BIA questionnaire (FR 3.2 UI) for the initiated BIA.  
     * Expected Result: The questionnaire displays the *framework and parameter definitions as they were at the time of BIA initiation* (snapshot for consistency). Dynamic calculation should still work based on that snapshot. (If real-time reflection of changes is desired, this requires explicit clarification). **Assuming snapshot for consistency.**  
   * **Test Case 3.2.11 (Process Owner Role Change Impact):**  
     * Pre-requisite: BIA assigned to a Process Owner. Change that user's role to 'Viewer' (FR 1.2).  
     * Action: Attempt to access and submit the BIA questionnaire as the now 'Viewer' user.  
     * Expected Result: HTTP 403 Forbidden. The user should lose submission privileges.

---

### **FR 3.3: BIA Review & Approval (BCM Manager / Department Head)**

#### **User Story: As a BCM Manager, I want to review submitted BIAs, send for clarification, and submit Impact Score and RTO for approval to the Department Head. As a Department Head, I want to approve the Impact Score and RTO for processes in my department.**

**Granular Development Tasks:**

1. **Database (MySQL):**  
   * No new tables required. Updates to `bia_process_inputs` table.  
2. **Backend (FastAPI):**  
   * Create API endpoints:  
     * `GET /bia_process_inputs/for_review`: To retrieve a list of BIAs awaiting review for BCM Manager or Department Head (filtered by `organizationId`, `status='Submitted for Review'` or 'Review in Progress').  
     * `GET /bia_process_inputs/{id}/details`: To retrieve full details of a submitted BIA, including process info, framework parameters, and all submitted ratings.  
     * `PUT /bia_process_inputs/{id}/send_for_clarification`:  
       * Input: `reviewerComments` (mandatory).  
       * Logic: Update `bia_process_inputs` status to 'Initiated' (or 'Clarification Required'). Clear `submittedDate`. Send automated notification to Process Owner with comments.  
     * `PUT /bia_process_inputs/{id}/submit_for_department_head_approval`:  
       * Input: (Optional: override `finalImpactScore`, `finalApprovedRTOId`).  
       * Logic: Update `bia_process_inputs` status to 'Review in Progress'. Send automated notification to the Department Head of the process's department.  
     * `PUT /bia_process_inputs/{id}/department_head_approve`:  
       * Input: `departmentHeadApprovalNote` (mandatory).  
       * Logic: Update `bia_process_inputs` status to 'Approved'. Store `departmentHeadApprovalNote`. Set `finalApprovedRTOId` (if not already set by BCM).  
     * `PUT /bia_process_inputs/{id}/department_head_reject`:  
       * Input: `departmentHeadApprovalNote` (mandatory).  
       * Logic: Update `bia_process_inputs` status to 'Initiated'. Send automated notification to Process Owner and BCM Manager.  
   * RBAC:  
     * 'BCM Manager' / 'CISO': Can access `for_review` list, `send_for_clarification`, `submit_for_department_head_approval` for all BIAs in their organization.  
     * 'Department Head': Can access `for_review` list and `department_head_approve`/`reject` *only* for processes within their assigned department.  
     * 'Admin': Can perform all review/approval actions.  
     * 'Process Owner' / 'Internal Auditor': Read-only access to their own submitted BIA.  
3. **Frontend (React/Tailwind):**  
   * Create a 'BIA Review Dashboard' for BCM Managers, CISO, and Department Heads:  
     * List of submitted BIAs with status (Submitted for Review, Review in Progress).  
     * Filters by Department, Process, Status.  
   * Detail view for a specific BIA:  
     * Display all submitted information: Process details, all parameter ratings and descriptions, recommended RTO and justification, derived Impact Score.  
     * For BCM Manager / CISO:  
       * Text area for 'Reviewer Comments'.  
       * Button 'Send for Clarification' (sends back to Process Owner).  
       * Button 'Submit for Department Head Approval'.  
       * Option to override calculated Impact Score and RTO (with justification field for override).  
     * For Department Head:  
       * View proposed Impact Score and RTO.  
       * Text area for 'Note for Acceptance'.  
       * Buttons: 'Approve', 'Reject'.  
     * Display current status of the BIA process (e.g., "Awaiting BCM Review", "Awaiting Department Head Approval").  
   * Notifications (in-app): For Process Owner (BIA sent for clarification), BCM Manager (BIA submitted), Department Head (BIA submitted for approval).  
   * Apply UI/UX design guidelines, including semantic colors for status (e.g., red for rejected, green for approved).

**Windsurf, implement the above granular tasks for FR 3.3: BIA Review & Approval.**

---

**Test Cases for FR 3.3: BIA Review & Approval**

**Prompt to Windsurf:** Execute the following automated test cases for FR 3.3. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next Epic until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 3.3.1 (BCM Review \- Access Submitted BIA):**  
     * Pre-requisite: A BIA is `Submitted for Review` (FR 3.2).  
     * Action: Authenticate as BCM Manager. Send GET request to `/bia_process_inputs/for_review` or direct GET to `/bia_process_inputs/<process_input_id>/details`.  
     * Expected Result: HTTP 200 OK. All submitted details are accessible.  
   * **Test Case 3.3.2 (BCM Review \- Send for Clarification):**  
     * Action: Authenticate as BCM Manager. Send PUT request to `/bia_process_inputs/<process_input_id>/send_for_clarification` with `reviewerComments='Missing details on dependencies'`.  
     * Expected Result: HTTP 200 OK. `bia_process_inputs` status changes to 'Initiated'. `reviewerComments` are stored. Process Owner receives notification.  
   * **Test Case 3.3.3 (Process Owner Revises after Clarification):**  
     * Pre-requisite: BIA sent for clarification.  
     * Action: Authenticate as Process Owner. Re-submit the BIA (FR 3.2) after making revisions.  
     * Expected Result: HTTP 200 OK. Status becomes 'Submitted for Review' again.  
   * **Test Case 3.3.4 (BCM Review \- Submit for Department Head Approval):**  
     * Action: Authenticate as BCM Manager. Send PUT request to `/bia_process_inputs/<process_input_id>/submit_for_department_head_approval`. (Optional: include `overrideImpactScore` and `overrideRTOId`).  
     * Expected Result: HTTP 200 OK. `bia_process_inputs` status changes to 'Review in Progress'. Department Head receives notification.  
   * **Test Case 3.3.5 (Department Head Approval \- Success):**  
     * Action: Authenticate as Department Head. Send PUT request to `/bia_process_inputs/<process_input_id>/department_head_approve` with `departmentHeadApprovalNote='Approved as critical process'`.  
     * Expected Result: HTTP 200 OK. `bia_process_inputs` status changes to 'Approved'. `departmentHeadApprovalNote` is stored. `finalApprovedRTOId` is set to the proposed RTO (or BCM override).  
   * **Test Case 3.3.6 (Department Head Reject \- Success):**  
     * Pre-requisite: BIA submitted for Department Head approval.  
     * Action: Authenticate as Department Head. Send PUT request to `/bia_process_inputs/<process_input_id>/department_head_reject` with `departmentHeadApprovalNote='Requires lower RTO'`.  
     * Expected Result: HTTP 200 OK. `bia_process_inputs` status changes to 'Initiated'. Process Owner and BCM Manager receive notifications.  
2. **Edge Case Tests:**

   * **Test Case 3.3.7 (BCM Override without Justification \- if applicable):**  
     * Action: BCM Manager attempts to override Impact Score/RTO without providing justification (if justification is made mandatory for override).  
     * Expected Result: HTTP 400 Bad Request.  
   * **Test Case 3.3.8 (Dept Head Approves for another Dept):**  
     * Action: Authenticate as Department Head of Department A. Attempt to approve a BIA belonging to Department B.  
     * Expected Result: HTTP 403 Forbidden.  
   * **Test Case 3.3.9 (Submit for Approval \- BIA not 'Submitted for Review'):**  
     * Action: BCM Manager attempts to submit a BIA that is still 'Initiated' or 'In Progress' for approval.  
     * Expected Result: HTTP 400 Bad Request or state validation error.  
   * **Test Case 3.3.10 (RBAC \- Process Owner attempts Review/Approval):**  
     * Action: Authenticate as Process Owner. Attempt to access review endpoints or send approval/rejection.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 3.3.11 (Impact Score Consistency after Approval):**  
     * Pre-requisite: A BIA is approved.  
     * Action: Check the `finalImpactScore` in the `bia_process_inputs` table.  
     * Expected Result: The `finalImpactScore` matches the value calculated and stored (either from Process Owner submission or BCM override).  
   * **Test Case 3.3.12 (RTO Consistency after Approval):**  
     * Pre-requisite: A BIA is approved.  
     * Action: Check the `finalApprovedRTOId` in the `bia_process_inputs` table.  
     * Expected Result: The `finalApprovedRTOId` matches the RTO approved by the Department Head (or BCM override).  
   * **Test Case 3.3.13 (Notifications are triggered):**  
     * Action: Perform BIA submission, send for clarification, and approval/rejection actions.  
     * Expected Result: System logs show corresponding notification attempts for each action.

---

**Epic 3 Completion \- Final Checks**

**Prompt to Windsurf:** All User Stories within Epic 3 (FR 3.1 to FR 3.3) are now implemented, and their individual tests have passed. Now, execute the following Epic-level Regression Test Cases and Health Checks. Report the PASS/FAIL status for each. **DO NOT proceed to Epic 4 until ALL these tests pass.**

1. **Epic-Level Regression Test Cases:**

   * **Test Case E3.R.1 (End-to-End BIA Workflow):**  
     * Action: Execute a full BIA workflow: Initiate BIA for a department \-\> Process Owner submits \-\> BCM sends for clarification \-\> Process Owner resubmits \-\> BCM submits for DH approval \-\> Department Head approves.  
     * Expected Result: All status transitions occur correctly, all data is stored at each stage, and final `finalImpactScore` and `finalApprovedRTOId` are correctly populated. Notifications are triggered at each stage.  
   * **Test Case E3.R.2 (BIA Workflow with Rejection):**  
     * Action: Execute a BIA workflow: Initiate BIA \-\> Process Owner submits \-\> BCM submits for DH approval \-\> Department Head rejects.  
     * Expected Result: Status correctly reverts to 'Initiated', Process Owner and BCM receive notifications, and `departmentHeadApprovalNote` is stored.  
   * **Test Case E3.R.3 (Multi-Tenancy Isolation):**  
     * Pre-requisite: Two organizations (`Org A`, `Org B`) with initiated BIAs.  
     * Action: Authenticate as a user from `Org A`. Attempt to access/modify BIA instances or process inputs belonging to `Org B`.  
     * Expected Result: HTTP 403 Forbidden or 404 Not Found for any attempts to access `Org B`'s BIA data.  
2. **Epic-Level Health Checks:**

   * **Health Check E3.H.1 (Database Connection & Schema):**  
     * Action: Verify that the application can connect to the MySQL database and that all tables (`bia_instances`, `bia_process_inputs`, `bia_process_parameter_ratings`) and relationships defined for Epic 3 are correctly present and indexed.  
     * Expected Result: Successful connection and schema validation.  
   * **Health Check E3.H.2 (API Endpoint Availability):**  
     * Action: Ping all Epic 3 API endpoints (`/bia_instances/initiate`, `/bia_process_inputs/{id}/save_draft`, `/bia_process_inputs/{id}/submit_for_review`, etc.).  
     * Expected Result: All endpoints return a 200 OK (or appropriate 4xx for auth/validation issues, but not 5xx).  
   * **Health Check E3.H.3 (BIA Workflow Statuses):**  
     * Action: Create several dummy BIAs and move them through different statuses. Check database for correct status values.  
     * Expected Result: Status values in `bia_instances` and `bia_process_inputs` tables are consistent and transition correctly.

---

## **Epic 4: Impact Calculation and Prioritization**

### **FR 4.1: Automated Impact Score Calculation**

#### **User Story: As a BCM Manager, I want the system to automatically calculate the impact score for each business process based on the configured BIA framework.**

**Granular Development Tasks:**

1. **Backend (FastAPI):**  
   * **Refine `calculate_impact_score` logic:** This logic was initially included in FR 3.2's `submit_for_review` endpoint. Ensure it is a robust, reusable function that:  
     * Takes `bia_process_parameter_ratings` and `frameworkId` as input.  
     * Retrieves `bia_parameters` and `bia_rating_definitions` associated with the framework's parameters.  
     * Retrieves `bia_framework_parameters` to get `weightage` for each parameter.  
     * Applies the `formula` (e.g., 'Weighted Average') defined in the `bia_frameworks` table.  
     * Calculates the `finalImpactScore` using the `scoreGivenForRating` from `bia_process_parameter_ratings` and the `weightages` from the framework.  
     * Handles cases where not all parameters have ratings (e.g., skip, or use a default score of 0, as per business rule).  
     * Ensures calculation is accurate for both Qualitative and Quantitative parameters.  
   * **Integration Check:** Confirm that this calculation function is correctly invoked and its result stored in `bia_process_inputs.finalImpactScore` when a BIA is submitted for review (FR 3.2).  
   * **Display on Review Screen:** Ensure the calculated `finalImpactScore` is included in the response of `GET /bia_process_inputs/{id}/details` for review by BCM/Department Head (FR 3.3).  
   * **Display in Reports:** Ensure the calculated `finalImpactScore` is available for future reporting endpoints (Epic 5).  
2. **Frontend (React/Tailwind):**  
   * **Dynamic Display in Questionnaire:** Verify that the `calculated impact score` updates dynamically in the UI as the Process Owner selects/enters ratings in the BIA questionnaire (as implemented in FR 3.2).  
   * **Display in Review UI:** Ensure the BCM Manager and Department Head review UIs (FR 3.3) clearly display the calculated `finalImpactScore` alongside submitted ratings.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 4.1: Automated Impact Score Calculation.**

---

**Test Cases for FR 4.1: Automated Impact Score Calculation**

**Prompt to Windsurf:** Execute the following automated test cases for FR 4.1. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 4.1.1 (Weighted Average Calculation \- Qualitative):**  
     * Pre-requisite: A BIA framework configured with 2 qualitative parameters (e.g., P1: {Low=1, High=5} @ 60%; P2: {Low=1, High=3} @ 40%). A BIA is initiated and submitted.  
     * Action: Process Owner submits BIA with P1='High' (score 5\) and P2='Low' (score 1).  
     * Expected Result: `finalImpactScore` in `bia_process_inputs` is calculated as `(5 * 0.60) + (1 * 0.40) = 3.0 + 0.4 = 3.4`.  
   * **Test Case 4.1.2 (Weighted Average Calculation \- Quantitative):**  
     * Pre-requisite: A BIA framework with 2 quantitative parameters (e.g., P3: {0-10=1, 11-50=3} @ 50%; P4: {0-5=1, 6-10=5} @ 50%). A BIA is initiated and submitted.  
     * Action: Process Owner submits BIA with P3 value=20 (score 3\) and P4 value=7 (score 5).  
     * Expected Result: `finalImpactScore` is calculated as `(3 * 0.50) + (5 * 0.50) = 1.5 + 2.5 = 4.0`.  
   * **Test Case 4.1.3 (Dynamic UI Update):**  
     * Action: Simulate UI interaction where Process Owner fills out BIA questionnaire and changes a rating.  
     * Expected Result: The displayed `calculated impact score` on the UI updates in real-time, matching the backend calculation logic.  
2. **Edge Case Tests:**

   * **Test Case 4.1.4 (Calculation \- Zero Weightage Parameter):**  
     * Pre-requisite: Framework has a parameter with 0% weightage.  
     * Action: Submit BIA using this framework.  
     * Expected Result: The parameter with 0% weightage has no impact on the final score.  
   * **Test Case 4.1.5 (Calculation \- All Parameters Missed):**  
     * Pre-requisite: BIA submitted with no ratings provided for any parameter.  
     * Action: Verify the `finalImpactScore`.  
     * Expected Result: `finalImpactScore` is 0 or indicates a default 'no impact' score, as per defined business rule (assume 0 for now).  
   * **Test Case 4.1.6 (BCM Override of Score):**  
     * Pre-requisite: A BIA is submitted.  
     * Action: BCM Manager sets an `overrideImpactScore` during `submit_for_department_head_approval` (FR 3.3).  
     * Expected Result: The overridden score is stored in `finalImpactScore` and takes precedence over the calculated score.  
3. **Regression Test Cases:**

   * **Test Case 4.1.7 (Framework Weightage Change):**  
     * Pre-requisite: A BIA framework is established.  
     * Action: Update the weightages of parameters in the BIA framework (FR 2.3).  
     * Expected Result: Existing `Approved` BIAs retain their original `finalImpactScore`. New BIAs initiated with the *updated* framework correctly reflect the new weightages in their `finalImpactScore` calculation.  
   * **Test Case 4.1.8 (Parameter Rating Definition Change):**  
     * Pre-requisite: A BIA parameter is defined.  
     * Action: Update the score of a rating definition for a parameter (FR 2.2).  
     * Expected Result: Existing `Approved` BIAs retain their original `finalImpactScore`. New BIAs initiated with the *updated* parameter definition correctly reflect the new scores in their `finalImpactScore` calculation.

---

### **FR 4.2: Recovery Time Objective (RTO) Derivation (Process)**

#### **User Story: As a BCM Manager, I want the system to derive the final RTO for each business process based on the Process Owner's input and Department Head's approval.**

**Granular Development Tasks:**

1. **Backend (FastAPI):**  
   * **RTO Selection Logic:**  
     * Ensure `bia_process_inputs.recommendedRTOId` stores the Process Owner's selection (from FR 3.2).  
     * Ensure `bia_process_inputs.finalApprovedRTOId` is updated:  
       * When BCM submits for Department Head approval (FR 3.3), `finalApprovedRTOId` is initially set to `recommendedRTOId` (or BCM override if provided).  
       * When Department Head approves (FR 3.3), `finalApprovedRTOId` is confirmed and stored. If Department Head rejects, it should revert or be cleared.  
   * **Display Final RTO:** Ensure the `finalApprovedRTOId` (and its corresponding label from `rto_options`) is included in the response of `GET /bia_process_inputs/{id}/details` and for any process listing/reporting endpoints.  
   * Update the `processes` table to store the final RTO value (e.g., `processes.finalRTO` VARCHAR) once the BIA for that process is approved. This will be the label of the RTO option.  
2. **Frontend (React/Tailwind):**  
   * **Questionnaire Display:** Process Owner's questionnaire (FR 3.2) displays the dropdown for 'Recommended RTO' populated from `rto_options`.  
   * **Review UI Display:** BCM Manager and Department Head review UIs (FR 3.3) clearly display:  
     * Process Owner's 'Recommended RTO' and 'Justification'.  
     * The 'Final Approved RTO' (after Department Head approval).  
   * **Process Details Page:** The main Process details page (FR 1.3) should display the `finalRTO` for that process, sourced from the latest Approved BIA.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 4.2: Recovery Time Objective (RTO) Derivation (Process).**

---

**Test Cases for FR 4.2: Recovery Time Objective (RTO) Derivation (Process)**

**Prompt to Windsurf:** Execute the following automated test cases for FR 4.2. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 4.2.1 (Process Owner Recommended RTO):**  
     * Pre-requisite: BIA initiated.  
     * Action: Process Owner submits BIA (FR 3.2) with `recommendedRTOId=<valid_rto_option_id>` and `rtoJustification`.  
     * Expected Result: `recommendedRTOId` and `rtoJustification` are correctly stored in `bia_process_inputs`.  
   * **Test Case 4.2.2 (Department Head Approval of RTO):**  
     * Pre-requisite: BIA submitted and sent for Department Head approval (FR 3.3).  
     * Action: Department Head approves BIA (FR 3.3).  
     * Expected Result: `finalApprovedRTOId` in `bia_process_inputs` is set to the `recommendedRTOId` (or BCM override). The `processes.finalRTO` for the associated process is updated to the label of this approved RTO option.  
   * **Test Case 4.2.3 (BCM Override of RTO):**  
     * Pre-requisite: BIA submitted.  
     * Action: BCM Manager submits for Department Head approval (FR 3.3), explicitly setting an `overrideRTOId` different from the Process Owner's recommendation.  
     * Expected Result: `finalApprovedRTOId` in `bia_process_inputs` is set to the BCM's overridden RTO. If Department Head approves, `processes.finalRTO` reflects this override.  
2. **Edge Case Tests:**

   * **Test Case 4.2.4 (RTO not Recommended by Process Owner):**  
     * Action: Process Owner submits BIA without selecting a `recommendedRTOId`.  
     * Expected Result: System allows submission (if RTO is not mandatory at this stage), and `recommendedRTOId` is null. BCM/DH should still be able to approve/set an RTO.  
   * **Test Case 4.2.5 (Department Head Rejection Impact on RTO):**  
     * Pre-requisite: BIA submitted for Department Head approval.  
     * Action: Department Head rejects the BIA (FR 3.3).  
     * Expected Result: `finalApprovedRTOId` is cleared/set to null in `bia_process_inputs`, and `processes.finalRTO` for that process is reset or indicates no approved RTO.  
3. **Regression Test Cases:**

   * **Test Case 4.2.6 (RTO Option Deactivation Impact):**  
     * Pre-requisite: A process has an approved RTO. Deactivate the corresponding `rto_option` (FR 2.3).  
     * Action: View the process details (FR 1.3 UI) and its approved RTO.  
     * Expected Result: The RTO is still correctly displayed, indicating that the value is stored and not dependent on the active status of the RTO option. (Soft deleting an RTO option should not affect already approved RTOs).

---

### **FR 4.3: Recovery Time Objective (RTO) Derivation (Application)**

#### **User Story: As a BCM Manager, I want the system to automatically derive the RTO for applications based on the RTOs of the business processes they support.**

**Granular Development Tasks:**

1. **Backend (FastAPI):**  
   * **Update `applications` table:** Ensure `applications.derivedRTO` (VARCHAR) column exists as per data model.  
   * **Application RTO Derivation Logic:**  
     * Create a background task or trigger that recalculates `applications.derivedRTO` whenever a `processes.finalRTO` is updated for any process.  
     * For a given application:  
       * Identify all active processes (`processes.isActive=TRUE`) that use this application (`process_applications` table).  
       * Retrieve the `finalRTO` (label) for each of these processes.  
       * Convert these RTO labels (e.g., '4 hours', '1 day') to their corresponding `valueInMinutes` (from `rto_options`).  
       * The `derivedRTO` for the application should be the *shortest* (most stringent) `valueInMinutes` among all its supporting processes.  
       * Store the label of this shortest RTO in `applications.derivedRTO`.  
     * This logic should be triggered upon:  
       * Approval of a BIA for a process (FR 3.3).  
       * Linkage of a process to an application (FR 1.3, on process creation/update).  
       * Linkage of an application to a process (FR 1.4, on application creation/update).  
2. **Frontend (React/Tailwind):**  
   * **Application Details Page:** The Application details page (FR 1.4) should display the `derivedRTO` for that application.  
   * **Reports/Dashboards:** Ensure `derivedRTO` is available for future reporting and prioritization.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 4.3: Recovery Time Objective (RTO) Derivation (Application).**

---

**Test Cases for FR 4.3: Recovery Time Objective (RTO) Derivation (Application)**

**Prompt to Windsurf:** Execute the following automated test cases for FR 4.3. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 4.3.1 (Application RTO \- Single Process Support):**  
     * Pre-requisite: Create an Application (A1) and a Process (P1) with an approved `finalRTO` of '4 hours'. Link P1 to A1.  
     * Action: Trigger application RTO calculation (e.g., by approving P1's BIA).  
     * Expected Result: `A1.derivedRTO` is correctly updated to '4 hours'.  
   * **Test Case 4.3.2 (Application RTO \- Multiple Process Support, Shortest RTO):**  
     * Pre-requisite: Create Application (A2), Process (P2) with `finalRTO` '24 hours', Process (P3) with `finalRTO` '8 hours'. Link both P2 and P3 to A2.  
     * Action: Trigger application RTO calculation (e.g., by approving P2 and P3's BIAs).  
     * Expected Result: `A2.derivedRTO` is correctly updated to '8 hours' (shortest).  
   * **Test Case 4.3.3 (Application RTO \- Update Process RTO):**  
     * Pre-requisite: Application (A3) linked to Process (P4) with `finalRTO` '7 days'. `A3.derivedRTO` is '7 days'.  
     * Action: Update P4's approved RTO to '3 days' (e.g., via new BIA approval cycle for P4).  
     * Expected Result: `A3.derivedRTO` automatically updates to '3 days'.  
2. **Edge Case Tests:**

   * **Test Case 4.3.4 (Application RTO \- No Supporting Processes):**  
     * Pre-requisite: Create an Application with no linked processes.  
     * Action: Trigger application RTO calculation.  
     * Expected Result: `derivedRTO` is null/empty or indicates 'Not Applicable'.  
   * **Test Case 4.3.5 (Application RTO \- All Supporting Processes Inactive):**  
     * Pre-requisite: Application linked to processes, all of which are soft deleted (FR 1.3).  
     * Action: Trigger application RTO calculation.  
     * Expected Result: `derivedRTO` is null/empty or indicates 'Not Applicable'.  
   * **Test Case 4.3.6 (Application RTO \- Only Inactive Processes Linked):**  
     * Pre-requisite: Application linked only to processes that are not in 'Approved' BIA status or have no final RTO.  
     * Action: Trigger application RTO calculation.  
     * Expected Result: `derivedRTO` is null/empty as no valid RTO can be derived.  
3. **Regression Test Cases:**

   * **Test Case 4.3.7 (Process Linkage Change Impact):**  
     * Pre-requisite: Application (A4) linked to processes P5 and P6. `A4.derivedRTO` is derived from shortest of P5/P6.  
     * Action: Unlink P5 from A4 (via Process Management FR 1.3 or Application Management FR 1.4).  
     * Expected Result: `A4.derivedRTO` automatically recalculates based *only* on P6's RTO.  
   * **Test Case 4.3.8 (Application Soft Delete Impact):**  
     * Pre-requisite: An application (A5) with a derived RTO.  
     * Action: Soft delete A5 (FR 1.4).  
     * Expected Result: A5 is marked inactive and should no longer appear in active lists. Its `derivedRTO` value should persist in the database but be associated with an inactive record.

---

### **FR 4.4: Process Prioritization**

#### **User Story: As a BCM Manager, I want to view a prioritized list of business processes based on their impact scores and RTOs so that I can focus on critical processes first.**

**Granular Development Tasks:**

1. **Backend (FastAPI):**  
   * Create API endpoint:  
     * `GET /processes/prioritized`: To retrieve a list of processes with their `finalImpactScore` and `finalRTO`.  
       * Parameters: `sortBy` (e.g., 'impact\_desc', 'rto\_asc'), `filterByDepartmentId`, `filterByProcessCategory` (if implemented), `filterByBIAStatus` (e.g., 'Approved').  
       * Logic: Retrieve data from `processes` and `bia_process_inputs` tables. Join with `rto_options` to get RTO labels and values.  
       * Implement sorting logic based on `finalImpactScore` (descending) and `finalApprovedRTOId` (ascending based on `valueInMinutes`).  
       * Ensure results are filtered by `organizationId`.  
   * Implement RBAC: Only 'BCM Manager', 'CISO', 'Internal Auditor' can view this prioritized list. Department Heads can only see processes in their own department.  
2. **Frontend (React/Tailwind):**  
   * Create a 'Process Prioritization Dashboard/Report' component.  
   * Display processes in a table/list format.  
   * Implement sortable columns for 'Process Name', 'Department', 'Process Owner', 'Impact Score', 'RTO'.  
   * Implement filters for:  
     * 'Department' (dropdown, from FR 1.1).  
     * 'BIA Status' (dropdown: Approved, etc.).  
     * 'Process Category' (dropdown, from FR 1.3 \- if implemented as a separate entity).  
   * Visually highlight processes that are deemed 'critical' (e.g., Impact Score above `framework.thresholdValue` and/or RTO below a configurable critical threshold) using semantic colors (e.g., red for high criticality, yellow for medium).  
   * Display KPI cards for 'Critical Processes', 'Impact Score', 'RTO' on a dashboard summary.  
   * Apply UI/UX design guidelines: Semantic colors (Red for critical, Green for healthy), KPI numbers font (Urbanist), meaningful icons.

**Windsurf, implement the above granular tasks for FR 4.4: Process Prioritization.**

---

**Test Cases for FR 4.4: Process Prioritization**

**Prompt to Windsurf:** Execute the following automated test cases for FR 4.4. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next Epic until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 4.4.1 (Sort by Impact Score \- Descending):**  
     * Pre-requisite: Multiple processes with varying `finalImpactScore` values.  
     * Action: Authenticate as BCM Manager. Send GET request to `/processes/prioritized?sortBy=impact_desc`.  
     * Expected Result: HTTP 200 OK. The list of processes is returned, sorted by `finalImpactScore` in descending order.  
   * **Test Case 4.4.2 (Sort by RTO \- Ascending):**  
     * Pre-requisite: Multiple processes with varying `finalRTO` values.  
     * Action: Authenticate as BCM Manager. Send GET request to `/processes/prioritized?sortBy=rto_asc`.  
     * Expected Result: HTTP 200 OK. The list of processes is returned, sorted by `finalRTO` (converted to minutes for comparison) in ascending order.  
   * **Test Case 4.4.3 (Filter by Department):**  
     * Pre-requisite: Processes associated with multiple departments.  
     * Action: Authenticate as BCM Manager. Send GET request to `/processes/prioritized?filterByDepartmentId=<department_id>`.  
     * Expected Result: HTTP 200 OK. Only processes belonging to the specified department are returned.  
   * **Test Case 4.4.4 (Filter by BIA Status):**  
     * Pre-requisite: Processes with different BIA statuses (e.g., Approved, Initiated).  
     * Action: Authenticate as BCM Manager. Send GET request to `/processes/prioritized?filterByBIAStatus=Approved`.  
     * Expected Result: HTTP 200 OK. Only processes with 'Approved' BIA status are returned.  
   * **Test Case 4.4.5 (Visual Highlighting \- UI Check):**  
     * Pre-requisite: Access to the Process Prioritization UI. Processes with high impact scores and short RTOs exist.  
     * Action: Observe the UI.  
     * Expected Result: Processes deemed critical (e.g., impact \> threshold, RTO \< critical\_threshold) are visually highlighted (e.g., red background, bold text).  
2. **Edge Case Tests:**

   * **Test Case 4.4.6 (Empty Process List):**  
     * Action: Send GET request to `/processes/prioritized` when no processes exist or none have approved BIAs.  
     * Expected Result: HTTP 200 OK. An empty list is returned.  
   * **Test Case 4.4.7 (Invalid SortBy Parameter):**  
     * Action: Send GET request to `/processes/prioritized?sortBy=invalid_sort`.  
     * Expected Result: HTTP 400 Bad Request. Error indicating invalid sort parameter.  
   * **Test Case 4.4.8 (RBAC \- Department Head Scope):**  
     * Action: Authenticate as Department Head. Send GET request to `/processes/prioritized`.  
     * Expected Result: HTTP 200 OK. Only processes belonging to their department are returned, even if no explicit filter is applied.  
   * **Test Case 4.4.9 (RBAC \- Process Owner):**  
     * Action: Authenticate as Process Owner. Send GET request to `/processes/prioritized`.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 4.4.10 (Impact Score Change Reflection):**  
     * Pre-requisite: A process appears in the prioritized list. Re-approve its BIA with a significantly different `finalImpactScore` (via FR 3.3).  
     * Action: View the prioritized list again.  
     * Expected Result: The process's position in the sorted list updates correctly based on its new impact score.  
   * **Test Case 4.4.11 (RTO Change Reflection):**  
     * Pre-requisite: A process appears in the prioritized list. Re-approve its BIA with a significantly different `finalRTO` (via FR 3.3).  
     * Action: View the prioritized list again.  
     * Expected Result: The process's position in the sorted list updates correctly based on its new RTO.

---

**Epic 4 Completion \- Final Checks**

**Prompt to Windsurf:** All User Stories within Epic 4 (FR 4.1 to FR 4.4) are now implemented, and their individual tests have passed. Now, execute the following Epic-level Regression Test Cases and Health Checks. Report the PASS/FAIL status for each. **DO NOT proceed to Epic 5 until ALL these tests pass.**

1. **Epic-Level Regression Test Cases:**

   * **Test Case E4.R.1 (End-to-End BIA Cycle with Impact/RTO Update):**  
     * Action: Initiate a new BIA, have Process Owner submit, BCM approve, Department Head approve. Then, initiate a new BIA for the *same process*, and submit with different ratings resulting in different Impact Score/RTO, and get it approved.  
     * Expected Result: The process's `finalImpactScore` and `finalRTO` update correctly, and the `applications.derivedRTO` updates if affected. The prioritization dashboard reflects the latest values.  
   * **Test Case E4.R.2 (Soft Delete Impact on Prioritization):**  
     * Pre-requisite: A process is listed on the prioritization dashboard.  
     * Action: Soft delete that process (FR 1.3).  
     * Expected Result: The soft-deleted process is immediately removed from the active prioritization dashboard.  
2. **Epic-Level Health Checks:**

   * **Health Check E4.H.1 (Database Connection & Schema):**  
     * Action: Verify that the application can connect to the MySQL database and that all columns and relationships required for impact/RTO calculations are correctly present and indexed.  
     * Expected Result: Successful connection and schema validation.  
   * **Health Check E4.H.2 (Core Calculation Logic):**  
     * Action: Run a series of predefined test cases for impact score and RTO derivation directly against the backend calculation functions (without full API calls).  
     * Expected Result: Calculations are consistently accurate.  
   * **Health Check E4.H.3 (Prioritization Endpoint Performance):**  
     * Action: Stress test the `/processes/prioritized` endpoint with a large number of processes (e.g., 500-1000 processes) and various filter/sort combinations.  
     * Expected Result: Response times remain within acceptable limits (e.g., \< 5 seconds).

---

## **Epic 5: Dashboard and Monitoring**

### **FR 5.1: BIA Status Dashboard**

#### **User Story: As a BCM Manager, CISO, or Internal Auditor, I want to view the status of BIA for individual departments and overall progress.**

**Granular Development Tasks:**

1. **Backend (FastAPI):**  
   * Create API endpoint:  
     * `GET /dashboard/bia_status`: To retrieve summarized BIA status data.  
       * Parameters: `filterByDepartmentId`, `filterByBIAFrameworkId`, `groupByDepartment` (boolean, for cards/listing).  
       * Logic:  
         * Query `bia_instances` and `bia_process_inputs` tables.  
         * For overall KPIs:  
           * Count `processes` with `finalImpactScore` exceeding `framework.thresholdValue` (from `bia_frameworks`) for 'Critical Processes'.  
           * Calculate average `finalImpactScore` for 'Impact Score'.  
           * Calculate average `finalApprovedRTOId` (converted to minutes) for 'RTO'.  
           * Count `bia_process_inputs` records with status 'Initiated', 'Submitted for Review', 'Review in Progress' for 'Open BIAs'.  
         * For departmental/listing view: Group `bia_process_inputs` by department, showing counts for each status.  
         * Ensure data is filtered by `organizationId`.  
   * Implement RBAC: Only 'BCM Manager', 'CISO', and 'Internal Auditor' can view the full dashboard. 'Department Heads' can view dashboard data pertaining to their own department.  
2. **Frontend (React/Tailwind):**  
   * Create a dedicated 'Dashboard' React component.  
   * Display KPI cards at the top: 'Critical Processes', 'Impact Score (Avg.)', 'RTO (Avg.)', 'Open BIAs'.  
     * Use Urbanist font for KPI numbers.  
     * Apply semantic colors: Green for 'Approved', Red for 'Critical/Rejected', Yellow for 'In Progress'.  
   * Display 'BIA Status by Department' section:  
     * Can be a listing or card view per department.  
     * Show counts of processes in each status (Initiated, Submitted, In Review, Approved).  
     * Use semantic colors for status tags (e.g., green for approved, red for rejected, yellow for in progress).  
   * Implement a 'BIA Table' below, listing individual `bia_process_inputs` records.  
     * Columns: Process Name, Department, Process Owner, Current Status, Impact Score, RTO.  
     * Implement filters for 'Department' and 'Status'.  
     * Allow sorting by Impact Score and RTO (linking to FR 4.4 logic).  
     * Use semantic icons for status (e.g., checkmark for Approved, warning for In Review).  
   * Ensure the UI is clean, uncluttered, refreshing, and minimalist.  
   * Apply UI/UX design guidelines (colors, fonts, icons).

**Windsurf, implement the above granular tasks for FR 5.1: BIA Status Dashboard.**

---

**Test Cases for FR 5.1: BIA Status Dashboard**

**Prompt to Windsurf:** Execute the following automated test cases for FR 5.1. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next User Story until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 5.1.1 (Dashboard Load \- Success):**  
     * Pre-requisite: Multiple BIAs in various statuses (Initiated, Submitted, Approved) across different departments.  
     * Action: Authenticate as BCM Manager. Send GET request to `/dashboard/bia_status`.  
     * Expected Result: HTTP 200 OK. Dashboard data (KPIs, departmental breakdown, table data) is returned. UI loads correctly displaying header and KPI cards.  
   * **Test Case 5.1.2 (KPI Card Accuracy):**  
     * Action: Verify the calculated values for 'Critical Processes', 'Impact Score (Avg.)', 'RTO (Avg.)', and 'Open BIAs' KPI cards.  
     * Expected Result: KPI values accurately reflect the underlying data and calculations.  
   * **Test Case 5.1.3 (Filter by Department \- UI/API):**  
     * Action: Apply a filter for a specific department on the dashboard UI.  
     * Expected Result: The displayed BIA table and departmental cards update to show only data relevant to the selected department. The backend API request includes the `filterByDepartmentId` parameter.  
   * **Test Case 5.1.4 (Status Tag Colors \- UI):**  
     * Action: Observe the BIA table/listing.  
     * Expected Result: Status tags (e.g., 'Approved', 'Submitted for Review') are displayed with their correct semantic colors (Green for Approved, Yellow for Submitted for Review, etc.).  
   * **Test Case 5.1.5 (Icon Relevance \- UI):**  
     * Action: Observe icons used on the dashboard.  
     * Expected Result: Icons are meaningful and consistent with business continuity concepts and general UI practices.  
   * **Test Case 5.1.6 (Sort Functionality):**  
     * Action: Click on the Impact Score or RTO column headers to sort the BIA table.  
     * Expected Result: The table data sorts correctly by the selected column (descending for Impact Score, ascending for RTO).  
2. **Edge Case Tests:**

   * **Test Case 5.1.7 (Empty Dashboard):**  
     * Pre-requisite: No BIAs have been initiated.  
     * Action: Access the dashboard.  
     * Expected Result: KPIs show 0/NA, and tables/listings are empty with an appropriate "No BIAs found" message.  
   * **Test Case 5.1.8 (RBAC \- Department Head View):**  
     * Action: Authenticate as a Department Head. Access the dashboard.  
     * Expected Result: Only data pertaining to processes within their assigned department is visible in KPIs and listings/tables, even if no explicit filter is applied. Other departments' data is not shown.  
   * **Test Case 5.1.9 (RBAC \- Process Owner View):**  
     * Action: Authenticate as a Process Owner. Access the dashboard.  
     * Expected Result: HTTP 403 Forbidden, as Process Owners are not intended to view the full dashboard.  
3. **Regression Test Cases:**

   * **Test Case 5.1.10 (BIA Status Change Reflection):**  
     * Pre-requisite: A BIA is `Initiated` and visible on the dashboard.  
     * Action: Complete the BIA workflow for that process, changing its status to `Approved` (via FR 3.3).  
     * Expected Result: The dashboard automatically updates. The process moves from 'Open BIAs' to `Approved` status, and relevant KPIs like 'Impact Score' and 'RTO' reflect its final values.  
   * **Test Case 5.1.11 (Process Deactivation Impact):**  
     * Pre-requisite: A process with an `Approved` BIA is visible on the dashboard.  
     * Action: Soft delete the process (FR 1.3).  
     * Expected Result: The process is removed from the dashboard listings/tables, and relevant KPIs are updated to exclude its data.  
   * **Test Case 5.1.12 (Framework Threshold Change Impact):**  
     * Pre-requisite: Several processes exist, some are `Approved` and some are `Critical` based on current framework threshold.  
     * Action: Change the `thresholdValue` in the BIA framework (FR 2.3).  
     * Expected Result: The 'Critical Processes' KPI and visual highlighting on the prioritization dashboard update to reflect the new threshold, re-categorizing processes as needed.

---

### **FR 5.2: BIA Export**

#### **User Story: As a BCM Manager, CISO, or Internal Auditor, I want to export BIA results for reporting and auditing purposes.**

**Granular Development Tasks:**

1. **Backend (FastAPI):**  
   * Create API endpoint:  
     * `GET /export/bia_results`: To generate and provide BIA results in a downloadable format.  
       * Parameters: `format` (e.g., 'csv', 'pdf'), `filterByDepartmentId`, `filterByBIAStatus`.  
       * Logic:  
         * Query `bia_process_inputs` and relevant joined tables (`processes`, `departments`, `users`, `rto_options`, `bia_frameworks`, `bia_parameters`, `bia_process_parameter_ratings`).  
         * Collect all comprehensive data for approved BIAs.  
         * Implement data serialization to CSV format. (PDF generation is complex, consider as stretch goal or future phase, but outline basic structure for CSV).  
         * Return the file as a response with appropriate content-type headers.  
         * Ensure data is filtered by `organizationId`.  
   * Implement RBAC: Only 'BCM Manager', 'CISO', and 'Internal Auditor' can trigger BIA exports.  
2. **Frontend (React/Tailwind):**  
   * Add an 'Export' button on the BIA Status Dashboard or a dedicated 'Reports' section.  
   * Provide options for export format (CSV initially).  
   * When the button is clicked, trigger the backend `/export/bia_results` endpoint.  
   * The browser should initiate a file download.  
   * Apply UI/UX design guidelines.

**Windsurf, implement the above granular tasks for FR 5.2: BIA Export.**

---

**Test Cases for FR 5.2: BIA Export**

**Prompt to Windsurf:** Execute the following automated test cases for FR 5.2. Report the PASS/FAIL status for each individual test case. **DO NOT proceed to the next Epic until ALL these tests pass.**

1. **Functional Tests:**

   * **Test Case 5.2.1 (Export CSV \- Success):**  
     * Pre-requisite: At least one approved BIA exists.  
     * Action: Authenticate as BCM Manager. Send GET request to `/export/bia_results?format=csv`.  
     * Expected Result: HTTP 200 OK. Response headers indicate `Content-Type: text/csv` and a downloadable filename. The downloaded CSV file contains all relevant BIA data, including process details, impact ratings, calculated score, and RTO, for the approved BIAs.  
   * **Test Case 5.2.2 (Export with Filters):**  
     * Action: Authenticate as BCM Manager. Send GET request to `/export/bia_results?format=csv&filterByDepartmentId=<valid_dept_id>&filterByBIAStatus=Approved`.  
     * Expected Result: HTTP 200 OK. The downloaded CSV contains only the BIA data matching the applied filters.  
   * **Test Case 5.2.3 (UI Export Trigger):**  
     * Action: As BCM Manager, click the 'Export' button on the dashboard UI.  
     * Expected Result: The browser initiates a file download for the CSV.  
2. **Edge Case Tests:**

   * **Test Case 5.2.4 (Export \- No BIA Data):**  
     * Pre-requisite: No approved BIAs exist in the system.  
     * Action: Send GET request to `/export/bia_results?format=csv`.  
     * Expected Result: HTTP 200 OK. The downloaded CSV file contains only headers or an empty dataset, without error.  
   * **Test Case 5.2.5 (Export \- Invalid Format):**  
     * Action: Send GET request to `/export/bia_results?format=xml` (assuming only CSV is supported for now).  
     * Expected Result: HTTP 400 Bad Request. Error indicating unsupported format.  
   * **Test Case 5.2.6 (RBAC \- Unauthorized User):**  
     * Action: Authenticate as 'Process Owner'. Attempt GET `/export/bia_results`.  
     * Expected Result: HTTP 403 Forbidden.  
3. **Regression Test Cases:**

   * **Test Case 5.2.7 (Data Consistency After BIA Update):**  
     * Pre-requisite: A BIA is approved and exported. Then, the BIA is re-evaluated and re-approved with updated impact scores/RTOs (via FR 3.3).  
     * Action: Export BIA results again.  
     * Expected Result: The new export correctly reflects the latest approved impact scores and RTOs, demonstrating that the export pulls live data.  
   * **Test Case 5.2.8 (Schema Change Impact on Export):**  
     * Pre-requisite: Assume a minor schema change (e.g., adding a new field to `processes` table, not yet displayed in UI).  
     * Action: Export BIA results.  
     * Expected Result: The export still functions, ideally including the new field (if relevant to BIA data), or at least not breaking.

---

**Epic 5 Completion \- Final Checks**

**Prompt to Windsurf:** All User Stories within Epic 5 (FR 5.1 to FR 5.2) are now implemented, and their individual tests have passed. Now, execute the following Epic-level Regression Test Cases and Health Checks. Report the PASS/FAIL status for each. **DO NOT request user testing until ALL these tests pass.**

1. **Epic-Level Regression Test Cases:**

   * **Test Case E5.R.1 (End-to-End Data Flow to Dashboard/Export):**  
     * Action: Perform a complete BIA workflow (initiate \-\> submit \-\> review \-\> approve) for a new process. Then, immediately check the dashboard and perform an export.  
     * Expected Result: The newly approved BIA is accurately reflected in all dashboard KPIs and listings, and correctly included in the export file with its final scores and RTOs.  
   * **Test Case E5.R.2 (Multi-Tenancy Isolation):**  
     * Pre-requisite: Data exists for two organizations (`Org A`, `Org B`).  
     * Action: Authenticate as a user from `Org A`. Access the dashboard and trigger an export.  
     * Expected Result: Dashboard only shows `Org A`'s data. Export file only contains `Org A`'s data. Attempts to query/export `Org B`'s data directly via API result in 403/404.  
2. **Epic-Level Health Checks:**

   * **Health Check E5.H.1 (Database Connection & Schema):**  
     * Action: Verify that the application can connect to the MySQL database and that all tables and relationships required for dashboarding and export are correctly present and indexed.  
     * Expected Result: Successful connection and schema validation.  
   * **Health Check E5.H.2 (API Endpoint Availability):**  
     * Action: Ping all Epic 5 API endpoints (`/dashboard/bia_status`, `/export/bia_results`).  
     * Expected Result: All endpoints return a 200 OK (or appropriate 4xx for auth/validation issues, but not 5xx).  
   * **Health Check E5.H.3 (Dashboard Performance):**  
     * Action: Load the dashboard with a large dataset (e.g., 50 departments, 1000 processes, all with approved BIAs).  
     * Expected Result: Dashboard loads within the specified performance threshold (e.g., \< 5 seconds).  
   * **Health Check E5.H.4 (Export Integrity):**  
     * Action: Perform a large export.  
     * Expected Result: Export completes without timeouts or errors, and the integrity of the generated file is maintained.

---

**Phase 1 Completion \- Final Review and Handover**

**Prompt to Windsurf:** You have now completed all Epics for Phase 1 of the Business Continuity Platform. All individual User Story tests and Epic-level regression/health checks have been executed and passed.

**Final Steps for Phase 1 Completion:**

1. **Comprehensive Code Review:** Perform a final self-review of the entire codebase for adherence to coding standards, best practices, and security guidelines.  
2. **Documentation Update:** Ensure all API endpoints are well-documented (e.g., OpenAPI/Swagger). Update any internal design documents or architectural diagrams as needed.  
3. **Deployment Readiness:** Verify that the application is ready for deployment to the specified AWS environment (SaaS on AWS model), including proper configuration for multi-tenancy.  
4. **Final Test Run:** Execute all regression tests and health checks across *all Epics (E1.R.1 to E5.R.2, E1.H.1 to E5.H.4)* one last time to confirm end-to-end stability.

**Report back with confirmation that all final steps are completed and all tests pass. You may then request user testing.**

