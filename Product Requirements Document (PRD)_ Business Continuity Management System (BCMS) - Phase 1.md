\# Product Requirements Document (PRD): Business Continuity Management System (BCMS) \- Phase 1

\*\*Version:\*\* 1.0  
\*\*Date:\*\* May 28, 2025  
\*\*Product Owner:\*\* Bharat S  
\*\*Company:\*\* CyRAACS  
\*\*Platform:\*\* COMPASS

\---

\#\#\# 1\. Introduction

This document outlines the product requirements for Phase 1 of the Business Continuity Management System (BCMS) application, a COMPASS extension. The primary goal of Phase 1 is to establish a foundational data model for organizational information, enable comprehensive Business Impact Analysis (BIA), and derive critical recovery metrics for business processes and their supporting applications. This phase lays the groundwork for subsequent phases that will focus on recovery strategies, plan development, incident management, and advanced integrations. The UI should be clean, uncluttered, refreshing, and minimalist.

\#\#\# 2\. Goals & Objectives

\*\*Overall Business Goal:\*\* To provide organizations with a robust, integrated platform for proactive business continuity planning, incident response, and resilience measurement.

\*\*Phase 1 Specific Goals:\*\*

\* Establish a centralized repository for essential organizational data (departments, people, processes, applications, locations, vendors).  
\* Enable structured Business Impact Analysis (BIA) for all identified business processes.  
\* Automate the calculation of impact scores and Recovery Time Objectives (RTOs) for processes and applications.  
\* Prioritize business processes based on their criticality and RTOs.  
\* Provide a clear, auditable trail for BIA data and decisions.

\*\*Phase 1 Specific Objectives:\*\*

\* Successfully onboard organizational data (departments, people, processes, applications, locations, vendors) with data integrity and relationships.  
\* Complete BIA for at least 80% of critical business processes identified by the organization.  
\* Achieve an accuracy rate of 95% for automatically calculated impact scores and RTOs.  
\* Ensure the system can handle concurrent BIA submissions from multiple users.

\#\#\# 3\. User Personas (Phase 1\)

\*\*3.1. BCM Manager\*\*  
\* \*\*About:\*\* Oversees the entire BCMS program, defines BIA parameters, reviews analysis results, ensures compliance, and manages users.  
\* \*\*Needs (Phase 1):\*\*  
	\* To add, edit and delete categories, parameters, framework for BIA.  
	\* To initiate BIA, Review BIA, send for clarification, submit Impact Score and RTO for approval to Department Head.  
	\* To add, edit and delete users.  
	\* To export BIA.  
	\* To view all sections.  
\* \*\*Pain Points (Phase 1):\*\*  
	\* Manual collection and consolidation of organizational data.  
	\* Inconsistent BIA methodologies across departments.  
	\* Difficulty in tracking BIA progress and chasing stakeholders.  
	\* Lack of a centralized view of all organizational assets and their interdependencies.

\*\*3.2. Process Owner\*\*  
\* \*\*About:\*\* Responsible for specific business processes within their department. They are key contributors to the BIA, providing detailed insights into process dependencies, resource requirements, and impact.  
\* \*\*Needs (Phase 1):\*\*  
	\* To add and edit process information.  
	\* To easily access and update information about their department's processes, applications, and people.  
	\* To complete BIA questionnaires for their processes in an intuitive manner.  
	\* To provide impact ratings for the processes for the timeframes.  
	\* To select and map process dependencies (Upstream and downstream) from a list of processes.  
	\* To submit for Review.  
	\* To understand the impact of disruptions on their processes and the wider organization.  
\* \*\*Pain Points (Phase 1):\*\*  
	\* Time-consuming and manual BIA data entry.  
	\* Lack of clarity on BIA questions and impact definitions.  
	\* Difficulty in mapping processes to supporting applications and infrastructure.  
	\* Lack of visibility into how their process impact contributes to the overall organizational impact.

\*\*3.3. Department Head\*\*  
\* \*\*About:\*\* Responsible for a department and its associated processes. They approve the final impact score and RTO for processes within their department.  
\* \*\*Needs (Phase 1):\*\*  
	\* To approve Impact Score and RTO for processes in the Department.  
	\* To add and edit department and associated process information.  
	\* To provide a note for acceptance.  
\* \*\*Pain Points (Phase 1):\*\*  
	\* Lack of clear visibility into the BIA results for their department.  
	\* Manual approval processes for BIA.

\*\*3.4. Admin\*\*  
\* \*\*About:\*\* Manages user accounts, permissions, and core organizational data.  
\* \*\*Needs (Phase 1):\*\*  
	\* To add, edit and delete users.  
	\* To assign permissions.  
	\* To add, edit and delete departments.  
	\* To add, edit and delete processes.  
	\* To add, edit and delete vendors.  
	\* To add, edit and delete applications.  
	\* To add, edit and delete locations.  
	\* To add, edit and delete people.  
	\* To view all sections.  
\* \*\*Pain Points (Phase 1):\*\*  
	\* Manual and fragmented user and data management.

\*\*3.5. CISO\*\*  
\* \*\*About:\*\* Information Security Officer, often involved in BIA framework definition and review due to the intersection with cybersecurity risks.  
\* \*\*Needs (Phase 1):\*\*  
	\* To add, edit and delete categories, parameters, framework for BIA.  
	\* To initiate BIA, Review BIA, send for clarification, submit Impact Score and RTO for approval to Department Head.  
	\* To add, edit and delete users.  
	\* To view BIA results.  
	\* To export BIA.

\*\*3.6. Internal Auditor\*\*  
\* \*\*About:\*\* Responsible for reviewing the BCMS processes and outputs for compliance and effectiveness.  
\* \*\*Needs (Phase 1):\*\*  
	\* To view all sections.  
	\* To view BIA results.  
	\* To export BIA.

\#\#\# 4\. Requirements

\#\#\#\# 4.1. Functional Requirements

\*\*Epic 1: Organizational Data Management\*\*

\* \*\*FR 1.1: Department Management\*\*  
	\* \*\*User Story:\*\* As a BCM Manager or Admin, I want to add, edit, and delete departments so that I can accurately represent the organizational structure.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for department creation with fields: Department Name (text), Description (text area), Department Head (dropdown, linked to People), Locations (multi-select, linked to Locations), Number of Team Members (numeric).  
        	\* Implement validation for unique Department Name.  
        	\* Enable editing and updating of existing department details.  
        	\* Implement soft delete functionality for departments.  
        	\* Display a hierarchical view of departments (stretch goal for Phase 1).  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 1.1.1:\*\* Verify a new department can be added with all required fields.  
        	\* \*\*Test Case 1.1.2:\*\* Verify department details (e.g., Description, Department Head, Locations, Number of Team Members) can be edited and updated.  
        	\* \*\*Test Case 1.1.3:\*\* Verify a department can be deactivated (soft delete).  
        	\* \*\*Test Case 1.1.4:\*\* Verify an error message is displayed when trying to add a department with a duplicate name.  
        	\* \*\*Test Case 1.1.5:\*\* Verify that multi-select locations are correctly added and displayed for a department.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure department data is correctly linked and displayed across BIA forms and reports. Verify that selecting locations for a department limits process locations to those of the department.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if department creation, update, and deactivation workflows are functioning.  
        	\* Verify data integrity for department relationships (e.g., Department Head, Locations).

\* \*\*FR 1.2: People Management\*\*  
	\* \*\*User Story:\*\* As an Admin, I want to add, edit, and assign roles to people within the organization so that I can identify key stakeholders for BCMS activities and manage user access.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for adding a person with fields: First Name, Last Name, Email (unique, validation), Department (dropdown, linked to FR 1.1), Location (dropdown, linked to FR 1.5).  
        	\* Implement roles for people: BCM Manager, Process Owner, Department Head, CISO, Internal Auditor, Admin.  
        	\* Enable editing and updating of person details and role assignments.  
        	\* Implement soft delete functionality for people.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 1.2.1:\*\* Verify a new person can be added with all required fields.  
        	\* \*\*Test Case 1.2.2:\*\* Verify a person's role can be updated to BCM Manager, Process Owner, Department Head, CISO, Internal Auditor, or Admin.  
        	\* \*\*Test Case 1.2.3:\*\* Verify a person's details can be edited (e.g., Department, Location).  
        	\* \*\*Test Case 1.2.4:\*\* Verify a person can be deactivated.  
        	\* \*\*Test Case 1.2.5:\*\* Verify an error message is displayed for duplicate email.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Verify that users with assigned roles can access relevant sections and perform actions as per their permissions.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if user creation, update, and role assignment are functioning.  
        	\* Verify role-based access control is correctly applied.

\* \*\*FR 1.3: Business Process Management\*\*  
	\* \*\*User Story:\*\* As an Admin or Department Head, I want to define and manage business processes within each department so that I can initiate BIA for them and track their details.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for adding a business process with fields: Process Name (unique per department), Process Owner (dropdown, linked to FR 1.2), Process Description, SLA, TAT, Seasonality, Peak Times, Frequency, Locations (multi-select, limited to the locations of the Department), Number of Team Members (numeric), Applications Used (multi-select choice from list of apps, linked to FR 1.4), Upstream and Downstream Dependency (multi-select choice from list of other processes).  
        	\* Implement validation for unique Process Name within a department.  
        	\* Enable editing and updating of existing process details.  
        	\* Implement soft delete functionality for processes.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 1.3.1:\*\* Verify a new process can be added to a department with all required fields.  
        	\* \*\*Test Case 1.3.2:\*\* Verify a process owner can be assigned to a process.  
        	\* \*\*Test Case 1.3.3:\*\* Verify process details (e.g., SLA, TAT, Seasonality, Peak Times, Frequency, Team Members) can be edited.  
        	\* \*\*Test Case 1.3.4:\*\* Verify applications used can be linked to a process.  
        	\* \*\*Test Case 1.3.5:\*\* Verify upstream and downstream dependencies can be selected and mapped.  
        	\* \*\*Test Case 1.3.6:\*\* Verify process locations are limited to the selected department's locations.  
        	\* \*\*Test Case 1.3.7:\*\* Verify a process can be deactivated.  
        	\* \*\*Test Case 1.3.8:\*\* Verify an error message is displayed for duplicate process name within the same department.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Verify that processes are correctly displayed and accessible for BIA. Ensure application and process dependency linkages are maintained.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if process creation, update, and deactivation workflows are functioning.  
        	\* Verify correct linkage between processes and departments, process owners, applications, and other processes (dependencies).

\* \*\*FR 1.4: Application Management\*\*  
	\* \*\*User Story:\*\* As an Admin, I want to register and manage applications used by the organization so that I can understand their dependencies on business processes and track their characteristics.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for adding an application with fields: Application Name (unique), App Owner (dropdown, linked to FR 1.2), Type (SaaS, Owned \- dropdown/radio button), Hosted on (text/dropdown for location/server if applicable), Workarounds (text area).  
        	\* Dependent Processes (derived from Processes where this application is linked as "Applications Used").  
        	\* RTO (derived from BIA \- will be populated in Epic 4).  
        	\* Implement validation for unique Application Name.  
        	\* Enable editing and updating of existing application details.  
        	\* Implement soft delete functionality for applications.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 1.4.1:\*\* Verify a new application can be added with all required fields.  
        	\* \*\*Test Case 1.4.2:\*\* Verify Application Name, App Owner, Type, Hosted On, and Workarounds can be edited.  
        	\* \*\*Test Case 1.4.3:\*\* Verify an application can be deactivated.  
        	\* \*\*Test Case 1.4.4:\*\* Verify an error message is displayed for duplicate application name.  
        	\* \*\*Test Case 1.4.5:\*\* Verify "Dependent Processes" field correctly displays processes where this application is linked.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Verify that applications are correctly linked to processes and their RTOs are calculated based on process criticality after BIA completion.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if application creation, update, and deactivation workflows are functioning.  
        	\* Verify correct linkage between applications and processes/application owners.

\* \*\*FR 1.5: Location Management\*\*  
	\* \*\*User Story:\*\* As an Admin, I want to define and manage organizational locations so that I can track where departments, people, and applications are physically situated.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for adding a location with fields: Name (unique), City, Address, Country, Time Zone (dropdown, possible to select from a predefined list).  
        	\* Implement validation for unique Location Name.  
        	\* Enable editing and updating of existing location details.  
        	\* Implement soft delete functionality for locations.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 1.5.1:\*\* Verify a new location can be added with all required fields.  
        	\* \*\*Test Case 1.5.2:\*\* Verify a location's details (e.g., City, Address, Country, Time Zone) can be edited.  
        	\* \*\*Test Case 1.5.3:\*\* Verify a location can be deactivated.  
        	\* \*\*Test Case 1.5.4:\*\* Verify an error message is displayed for duplicate location name.  
        	\* \*\*Test Case 1.5.5:\*\* Verify Time Zone can be selected from a dropdown.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure locations are selectable in other relevant forms (e.g., Department, People, Process).  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if location creation, update, and deactivation workflows are functioning.

\* \*\*FR 1.6: Vendor Management\*\*  
	\* \*\*User Story:\*\* As an Admin, I want to register and manage vendors so that I can track their involvement with applications and understand their impact on processes.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for adding a vendor with fields: Name of Vendor (unique), Location, Services (text area describing services/products provided), Time to Impact in case of Unavailability (e.g., 2 hours, 1 day \- dropdown/numeric \+ unit).  
        	\* Implement validation for unique Vendor Name.  
        	\* Enable editing and updating of existing vendor details.  
        	\* Implement soft delete functionality for vendors.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 1.6.1:\*\* Verify a new vendor can be added with all required fields.  
        	\* \*\*Test Case 1.6.2:\*\* Verify vendor details (e.g., Location, Services, Time to Impact) can be edited.  
        	\* \*\*Test Case 1.6.3:\*\* Verify a vendor can be deactivated.  
        	\* \*\*Test Case 1.6.4:\*\* Verify an error message is displayed for duplicate vendor name.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure vendors are selectable in other relevant forms (e.g., Application).  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if vendor creation, update, and deactivation workflows are functioning.

\*\*Epic 2: BIA Framework Configuration\*\*

\* \*\*FR 2.1: BIA Categories Management\*\*  
	\* \*\*User Story:\*\* As a BCM Manager or CISO, I want to create, edit, or delete categories for BIA Impact Parameters so that I can group related impact types.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for Category management with fields: Category Name (unique), Description (text area).  
        	\* Implement validation for unique Category Name.  
        	\* Enable editing and deleting of existing categories.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 2.1.1:\*\* Verify a new category can be created with a unique name and description.  
        	\* \*\*Test Case 2.1.2:\*\* Verify an existing category's name and description can be edited.  
        	\* \*\*Test Case 2.1.3:\*\* Verify a category can be deleted.  
        	\* \*\*Test Case 2.1.4:\*\* Verify an error message is displayed when trying to add a duplicate category name.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure changes to categories are reflected in the Parameter creation form.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if category CRUD operations are functioning.

\* \*\*FR 2.2: BIA Parameters Management\*\*  
	\* \*\*User Story:\*\* As a BCM Manager or CISO, I want to create, edit, or delete parameters under categories for BIA so that I can define specific impact criteria.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for Parameter management with fields: Parameter Name (unique per category), Description (text area), Select Category from mandatory dropdown (linked to FR 2.1).  
        	\* Implement Rating Type selection: Qualitative or Quantitative.  
        	\* For \*\*Qualitative\*\* type: Define how many ratings (e.g., Nil, Low, Medium, High, Very High) and corresponding scores (e.g., 0, 1, 2, 3, 4). User can choose how many ratings and corresponding scores.  
        	\* For \*\*Quantitative\*\* type: Define how many ratings, allow use of numerical ranges (e.g., 1 to 10, 11 to 25, 26 to 50, 51 to 100 and above 100\) and corresponding scores (e.g., 0, 1, 2, 3, 4). User can choose how many ratings, corresponding ranges and scores. The last range can be a singular value (e.g., "Above 100").  
        	\* Implement validation for unique Parameter Name within a category.  
        	\* Enable editing and deleting of existing parameters.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 2.2.1:\*\* Verify a new qualitative parameter can be created with custom ratings and scores.  
        	\* \*\*Test Case 2.2.2:\*\* Verify a new quantitative parameter can be created with custom ranges and scores, including an "Above X" range.  
        	\* \*\*Test Case 2.2.3:\*\* Verify an existing parameter's details (Name, Description, Category, Rating Type, ratings/ranges/scores) can be edited.  
        	\* \*\*Test Case 2.2.4:\*\* Verify a parameter can be deleted.  
        	\* \*\*Test Case 2.2.5:\*\* Verify error message for duplicate parameter name within the same category.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure changes to parameters are correctly reflected in the BIA framework builder.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if parameter CRUD operations are functioning, including dynamic rating/range configurations.

\* \*\*FR 2.3: BIA Framework Builder\*\*  
	\* \*\*User Story:\*\* As a BCM Manager or CISO, I want to build a BIA framework by selecting parameters and assigning weightages so that I can define the BIA methodology.  
    	\* \*\*Tasks:\*\*  
        	\* Create UI for building a BIA framework: Select Parameters from the defined Parameters (FR 2.2).  
        	\* Assign weightages to each selected parameter.  
        	\* Implement validation to ensure the sum of all parameter weightages is 100\.  
        	\* Allow selecting a formula from pre-defined formulas (e.g., weighted average).  
        	\* Show a sample calculation for the selected formula based on parameter weightages and parameter definitions (ratings and corresponding scores).  
        	\* Provide a threshold value.  
        	\* Allow defining default RTO options: 1 hour, 2 hours, 4 hours, 8 hours, 24 hours, 48 hours, 3 days, 5 days, 7 days, 10 days, 15 days, 30 days, 90 days, 180 days.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 2.3.1:\*\* Verify a new framework can be created by selecting parameters.  
        	\* \*\*Test Case 2.3.2:\*\* Verify weightages can be assigned to parameters, and the sum of weightages equals 100\.  
        	\* \*\*Test Case 2.3.3:\*\* Verify a predefined formula can be selected.  
        	\* \*\*Test Case 2.3.4:\*\* Verify the sample calculation accurately reflects the formula, weightages, and parameter definitions.  
        	\* \*\*Test Case 2.3.5:\*\* Verify a threshold value can be set.  
        	\* \*\*Test Case 2.3.6:\*\* Verify default RTO options are available for selection.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure changes to the BIA framework (parameters, weightages, formula) are correctly applied to new BIA calculations.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if the BIA framework builder UI is functional and all inputs are validated.  
        	\* Verify that saved frameworks persist and can be retrieved.

\*\*Epic 3: BIA Execution and Workflow\*\*

\* \*\*FR 3.1: BIA Initiation\*\*  
	\* \*\*User Story:\*\* As a BCM Manager or CISO, I want to initiate a BIA for a department and its related processes based on a defined frequency.  
    	\* \*\*Tasks:\*\*  
        	\* Provide an option to initiate BIA for a selected Department. This should automatically initiate BIA for all processes within that department.  
        	\* Allow defining the frequency of BIA initiation (annually, bi-annually, biennially).  
        	\* Automate notification (in-app and email) to the Process Owner(s) about pending BIA assignments.  
        	\* Track the status of BIA: Initiated, Submitted for Review, Review in Progress, Approved.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 3.1.1:\*\* Verify a BIA can be initiated for a specific department.  
        	\* \*\*Test Case 3.1.2:\*\* Verify that all processes within the selected department are included in the initiated BIA.  
        	\* \*\*Test Case 3.1.3:\*\* Verify the BIA status is "Initiated" upon creation.  
        	\* \*\*Test Case 3.1.4:\*\* Verify process owners receive notifications for new BIA assignments.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure BIA initiation correctly links to departments and processes, and status updates are accurate.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if BIA initiation process is functional.  
        	\* Verify that new BIA records are created with the correct initial status.

\* \*\*FR 3.2: BIA Questionnaire Completion (Process Owner)\*\*  
	\* \*\*User Story:\*\* As a Process Owner, I want to provide detailed impact ratings and process dependencies for my assigned BIA questionnaires.  
    	\* \*\*Tasks:\*\*  
        	\* Provide an intuitive BIA questionnaire for each assigned process.  
        	\* For each impact parameter defined in the BIA framework (FR 2.3), allow the process owner to select the appropriate impact rating (qualitative or quantitative based on parameter type).  
        	\* Enable process owners to provide qualitative descriptions for each impact.  
        	\* Allow selection and mapping of Upstream and Downstream Process Dependencies from a list of all processes.  
        	\* Allow the process owner to provide a recommended RTO from the predefined RTO options (FR 2.3).  
        	\* Provide a text field for justification for the recommended RTO.  
        	\* Display the current calculated impact score dynamically as the questionnaire is filled (using the selected framework and parameters).  
        	\* Enable saving the BIA as a draft and submitting it for review.  
        	\* All Process Owners should be able to provide the information related to impact and submit.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 3.2.1:\*\* Verify a process owner can access their assigned BIA questionnaires.  
        	\* \*\*Test Case 3.2.2:\*\* Verify a process owner can select impact ratings for all parameters based on their type (qualitative/quantitative).  
        	\* \*\*Test Case 3.2.3:\*\* Verify upstream and downstream process dependencies can be selected and mapped.  
        	\* \*\*Test Case 3.2.4:\*\* Verify a recommended RTO can be selected and justification provided.  
        	\* \*\*Test Case 3.2.5:\*\* Verify the BIA can be saved as a draft.  
        	\* \*\*Test Case 3.2.6:\*\* Verify the BIA can be submitted for review.  
        	\* \*\*Test Case 3.2.7:\*\* Verify the dynamic calculation of impact score is displayed during completion.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure BIA questionnaire submissions correctly update process data and trigger BCM review.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if BIA questionnaire is accessible and submittable by process owners.  
        	\* Verify that saved drafts and submitted BIAs are retrievable.

\* \*\*FR 3.3: BIA Review & Approval (BCM Manager / Department Head)\*\*  
	\* \*\*User Story:\*\* As a BCM Manager, I want to review submitted BIAs, send for clarification, and submit Impact Score and RTO for approval to the Department Head. As a Department Head, I want to approve the Impact Score and RTO for processes in my department.  
    	\* \*\*Tasks:\*\*  
        	\* Provide a dashboard view of all submitted BIAs, categorized by status (Submitted for Review, Review in Progress, Approved).  
        	\* Enable BCM Manager to view the completed questionnaire, including selected impact ratings, proposed RTO, justification, and process dependencies.  
        	\* Allow BCM Manager to add comments/feedback and send for clarification (rejection). This should update the BIA status and notify the Process Owner.  
        	\* Implement review cycles (configurable for future phases, fixed for Phase 1 as one review cycle).  
        	\* Allow BCM Manager to submit the calculated impact score and recommended RTO for approval to the Department Head.  
        	\* Department Head receives notification for pending approval.  
        	\* Department Head can view the proposed Impact Score and RTO.  
        	\* Department Head can provide a note for acceptance when approving.  
        	\* Department Head approves the Impact Score and RTO. Upon approval, the final values are recorded, and the BIA status changes to "Approved".  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 3.3.1:\*\* Verify BCM Manager can view submitted BIAs.  
        	\* \*\*Test Case 3.3.2:\*\* Verify BCM Manager can review all submitted BIA details.  
        	\* \*\*Test Case 3.3.3:\*\* Verify BCM Manager can send a BIA back for clarification with comments.  
        	\* \*\*Test Case 3.3.4:\*\* Verify Process Owner receives notification for BIA sent for clarification.  
        	\* \*\*Test Case 3.3.5:\*\* Verify BCM Manager can submit BIA for Department Head approval.  
        	\* \*\*Test Case 3.3.6:\*\* Verify Department Head receives notification for pending approval.  
        	\* \*\*Test Case 3.3.7:\*\* Verify Department Head can view the Impact Score and RTO.  
        	\* \*\*Test Case 3.3.8:\*\* Verify Department Head can provide a note for acceptance and approve the BIA.  
        	\* \*\*Test Case 3.3.9:\*\* Verify BIA status changes to "Approved" after Department Head approval.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure BIA review and approval workflow correctly updates BIA status and process data.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if BCM Manager review dashboard is functional.  
        	\* Verify approval/rejection workflows are working as expected, with correct notifications.

\#\#\#\# 4.3. Impact Calculation & Prioritization

\*\*Epic 4: Impact Calculation and Prioritization\*\*

\* \*\*FR 4.1: Automated Impact Score Calculation\*\*  
	\* \*\*User Story:\*\* As a BCM Manager, I want the system to automatically calculate the impact score for each business process based on the configured BIA framework.  
    	\* \*\*Tasks:\*\*  
        	\* Implement algorithms to calculate the overall impact score based on selected impact ratings, their assigned scores, and category weighting factors (defined in FR 2.3).  
        	\* Display the calculated impact score on the BIA questionnaire (dynamically, FR 3.2), BIA review screen, and in BIA reports.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 4.1.1:\*\* Verify impact score is calculated correctly based on a sample BIA and framework settings (qualitative parameters).  
        	\* \*\*Test Case 4.1.2:\*\* Verify impact score is calculated correctly based on a sample BIA and framework settings (quantitative parameters).  
        	\* \*\*Test Case 4.1.3:\*\* Verify impact score updates dynamically when impact levels are changed in the questionnaire.  
        	\* \*\*Test Case 4.1.4:\*\* Verify weighting factors are applied correctly in the calculation.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure BIA calculations are robust and accurate after any data model or framework changes.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Verify that impact scores are calculated and displayed correctly for all approved BIAs.

\* \*\*FR 4.2: Recovery Time Objective (RTO) Derivation (Process)\*\*  
	\* \*\*User Story:\*\* As a BCM Manager, I want the system to derive the final RTO for each business process based on the Process Owner's input and Department Head's approval.  
    	\* \*\*Tasks:\*\*  
        	\* Store the Process Owner's recommended RTO.  
        	\* The final RTO for the process will be the one approved by the Department Head.  
        	\* Display the final RTO for each process in reports and process details.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 4.2.1:\*\* Verify the proposed RTO is stored when the BIA is saved/submitted.  
        	\* \*\*Test Case 4.2.2:\*\* Verify the Department Head's approved RTO is stored as the final RTO.  
        	\* \*\*Test Case 4.2.3:\*\* Verify the final RTO is displayed correctly in process details.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure RTO derivation logic is sound and correctly applied.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Verify that RTOs are derived and displayed correctly for all approved BIAs.

\* \*\*FR 4.3: Recovery Time Objective (RTO) Derivation (Application)\*\*  
	\* \*\*User Story:\*\* As a BCM Manager, I want the system to automatically derive the RTO for applications based on the RTOs of the business processes they support.  
    	\* \*\*Tasks:\*\*  
        	\* For each application, identify all supporting business processes (linked in FR 1.4).  
        	\* The application's RTO should be the \*shortest\* (most stringent) RTO of all critical business processes it supports.  
        	\* Display the derived application RTO in application details and reports.  
        	\* Recalculate application RTO if a supported process's RTO changes.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 4.3.1:\*\* Verify an application supporting a single process inherits that process's RTO.  
        	\* \*\*Test Case 4.3.2:\*\* Verify an application supporting multiple processes inherits the shortest RTO among them.  
        	\* \*\*Test Case 4.3.3:\*\* Verify the application's RTO updates automatically if a supported process's RTO changes.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure application RTO calculations are accurate and dynamically update based on process changes.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Verify that application RTOs are correctly derived and displayed.

\* \*\*FR 4.4: Process Prioritization\*\*  
	\* \*\*User Story:\*\* As a BCM Manager, I want to view a prioritized list of business processes based on their impact scores and RTOs so that I can focus on critical processes first.  
    	\* \*\*Tasks:\*\*  
        	\* Provide a dashboard/report to display business processes, sortable by:  
            	\* Descending Impact Score (highest impact first).  
            	\* Ascending RTO (shortest recovery time first).  
        	\* Allow filtering by department, process category (from process details), or BIA status.  
        	\* Visually highlight processes with high impact scores and short RTOs (e.g., using color coding or icons).  
        	\* View critical processes, impact score, and RTO on the dashboard.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 4.4.1:\*\* Verify processes can be sorted by impact score in descending order.  
        	\* \*\*Test Case 4.4.2:\*\* Verify processes can be sorted by RTO in ascending order.  
        	\* \*\*Test Case 4.4.3:\*\* Verify processes can be filtered by department.  
        	\* \*\*Test Case 4.4.4:\*\* Verify processes can be filtered by BIA status.  
        	\* \*\*Test Case 4.4.5:\*\* Verify visual highlighting for critical processes is applied.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure prioritization logic remains consistent and accurate after data updates or framework changes.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Verify that process prioritization dashboard/report is functional and displays accurate data.

\*\*Epic 5: Dashboard and Monitoring\*\*

\* \*\*FR 5.1: BIA Status Dashboard\*\*  
	\* \*\*User Story:\*\* As a BCM Manager, CISO, or Internal Auditor, I want to view the status of BIA for individual departments and overall progress.  
    	\* \*\*Tasks:\*\*  
        	\* Create a dashboard section that displays BIA status for individual departments as a listing and cards.  
        	\* Display KPI cards for "Critical Processes," "Impact Score," "RTO," and "Open BIAs".  
        	\* Provide a table view of BIAs with filters for department and status.  
        	\* Apply semantic color codes and severity icons to status tags (e.g., green for approved, red for rejected, yellow for in progress).  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 5.1.1:\*\* Verify the dashboard loads with KPI cards and BIA status display.  
        	\* \*\*Test Case 5.1.2:\*\* Verify "Critical Processes," "Impact Score," "RTO," and "Open BIAs" KPI cards show accurate counts/averages.  
        	\* \*\*Test Case 5.1.3:\*\* Verify the BIA table can be filtered by Department.  
        	\* \*\*Test Case 5.1.4:\*\* Verify the BIA table displays correct status tags with semantic color codes.  
        	\* \*\*Test Case 5.1.5:\*\* Verify icons are meaningful and consistent.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure dashboard data remains consistent and up-to-date with BIA workflow changes.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if the dashboard is accessible and all data points are refreshing correctly.

\* \*\*FR 5.2: BIA Export\*\*  
	\* \*\*User Story:\*\* As a BCM Manager, CISO, or Internal Auditor, I want to export BIA results for reporting and auditing purposes.  
    	\* \*\*Tasks:\*\*  
        	\* Provide an export function for BIA results (e.g., CSV, PDF) from the BIA dashboard/reports.  
        	\* The export should include all relevant BIA data, including process details, impact ratings, calculated score, and RTO.  
    	\* \*\*Test Script:\*\*  
        	\* \*\*Test Case 5.2.1:\*\* Verify BCM Manager can export BIA data.  
        	\* \*\*Test Case 5.2.2:\*\* Verify the exported file contains accurate and complete BIA information.  
    	\* \*\*Regression Test Case (Post-Epic):\*\* Ensure export functionality continues to work correctly after any data model changes.  
    	\* \*\*Health Check (Post-Epic):\*\*  
        	\* Check if BIA export functionality is available and produces valid files.

\#\#\#\# 4.4. Non-Functional Requirements

\* \*\*NFR 4.4.1: Performance:\*\*  
	\* The application should load BIA questionnaires within 3 seconds.  
	\* Impact score and RTO calculations should be near real-time (under 1 second).  
	\* Dashboard data should load within 5 seconds for up to 1000 processes.  
\* \*\*NFR 4.4.2: Security:\*\*  
	\* Role-based access control (RBAC) must be strictly enforced as per persona permissions.  
	\* All sensitive data (e.g., impact scores, RTOs) must be encrypted at rest and in transit.  
	\* Input validation should prevent common web vulnerabilities (e.g., XSS, SQL injection).  
	\* Multi-tenancy: Every organization should have its own tenant and related database, accessible only to its added users. A Platform Admin will create an organization, its users and assign permissions. \[cite: 25, 26\]  
\* \*\*NFR 4.4.3: Scalability:\*\*  
	\* The application should be able to support up to 500 organizations, each with up to 1000 processes, in Phase 1\.  
	\* The architecture should support horizontal scaling for both frontend and backend.  
\* \*\*NFR 4.4.4: Usability:\*\*  
	\* The user interface (UI) should be clean, uncluttered, and refreshing. \[cite: 28\]  
	\* The design should be minimalist. \[cite: 29\]  
	\* Icons must have a meaning and relation to business continuity and generally used common icons. \[cite: 27\]  
	\* The UI should be intuitive and require minimal training for core BIA workflows.  
	\* Consistent navigation and layout across all modules.  
\* \*\*NFR 4.4.5: Accessibility:\*\*  
	\* Adhere to WCAG 2.1 AA guidelines where feasible in Phase 1 (focus on contrast, keyboard navigation).  
\* \*\*NFR 4.4.6: Maintainability:\*\*  
	\* Codebase should be modular, well-documented, and follow best practices.  
	\* Automated tests (unit, integration) should cover critical functionalities.  
\* \*\*NFR 4.4.7: Reliability:\*\*  
	\* High availability (target 99.9% uptime).  
	\* Robust error handling and logging mechanisms.  
\* \*\*NFR 4.4.8: User Interface Design:\*\*  
	\* \*\*Primary Colours:\*\* Blue (\#196BDE, \#64A5FF, \#B2D2FF, \#E1EDFF). \[cite: 27\]  
	\* \*\*Secondary Colours:\*\* Yellow (\#FDB812, \#FFCF5A, \#FFE29D, \#FFEEC5, \#FFF7E2). \[cite: 27\]  
	\* \*\*Green:\*\* \#5EB485, \#7EC39D, \#B2DBC4, \#D8EDE2, \#EFF7F3 (for success/positive indicators). \[cite: 27\]  
	\* \*\*Red:\*\* \#EC4654, \#F49098, \#F9C4C8, \#FCDEE0, \#FDF0F1 (for error/critical indicators). \[cite: 27\]  
	\* \*\*Heading Fonts:\*\* Outfit. \[cite: 29\]  
	\* \*\*Body Font:\*\* DM Sans. \[cite: 29\]  
	\* \*\*KPI Numbers:\*\* Urbanist. \[cite: 29\]  
	\* Icons must have a meaning and relation to business continuity and generally used common icons. \[cite: 27\]

\#\#\# 5\. Tech Stack

\* \*\*Frontend:\*\* React, Tailwind CSS, Heroicons/Lucide for icons.  
\* \*\*Backend:\*\* FastAPI (Python), Node.js (for potential microservices or specific integrations if needed, but primary backend is Python).  
\* \*\*Database:\*\* MySQL\[cite: 25\].  
	\* \*\*Model:\*\* SaaS on AWS\[cite: 25\].  
\* \*\*Deployment Environment:\*\* AWS (EC2, RDS, S3 for static assets, etc.).

\#\#\# 6\. Data Model (High-Level for Phase 1\)

\*\*Key Entities and Relationships:\*\*

\* \*\*Organization:\*\* \`id\`, \`name\` (for multi-tenancy)  
\* \*\*User:\*\* \`id\`, \`firstName\`, \`lastName\`, \`email\`, \`departmentId (FK)\`, \`locationId (FK)\`, \`role (Enum: BCM Manager, Process Owner, Department Head, CISO, Internal Auditor, Admin)\`, \`passwordHash\`, \`isActive\`  
\* \*\*Department:\*\* \`id\`, \`name\`, \`description\`, \`departmentHeadId (FK to User)\`, \`organizationId (FK)\`  
\* \*\*DepartmentLocation (Junction Table):\*\* \`departmentId (FK)\`, \`locationId (FK)\`  
\* \*\*Process:\*\* \`id\`, \`name\`, \`description\`, \`processOwnerId (FK to User)\`, \`departmentId (FK)\`, \`sla\`, \`tat\`, \`seasonality\`, \`peakTimes\`, \`frequency\`, \`numTeamMembers\`, \`finalImpactScore\`, \`finalRTO\`, \`organizationId (FK)\`  
\* \*\*ProcessLocation (Junction Table):\*\* \`processId (FK)\`, \`locationId (FK)\`  
\* \*\*ProcessApplication (Junction Table):\*\* \`processId (FK)\`, \`applicationId (FK)\`  
\* \*\*ProcessDependency (Self-referencing table):\*\* \`processId (FK)\`, \`dependentProcessId (FK)\`, \`dependencyType (Upstream, Downstream)\`  
\* \*\*Application:\*\* \`id\`, \`name\`, \`appOwnerId (FK to User)\`, \`type (SaaS, Owned)\`, \`hostedOn\`, \`workarounds\`, \`derivedRTO\`, \`organizationId (FK)\`  
\* \*\*ApplicationVendor (Junction Table):\*\* \`applicationId (FK)\`, \`vendorId (FK)\`  
\* \*\*Location:\*\* \`id\`, \`name\`, \`address\`, \`city\`, \`country\`, \`timeZone\`, \`organizationId (FK)\`  
\* \*\*Vendor:\*\* \`id\`, \`name\`, \`location\`, \`services\`, \`timeToImpact\`, \`organizationId (FK)\`  
\* \*\*BIACategory:\*\* \`id\`, \`name\`, \`description\`, \`organizationId (FK)\`  
\* \*\*BIAParameter:\*\* \`id\`, \`name\`, \`description\`, \`categoryId (FK)\`, \`ratingType (Qualitative, Quantitative)\`, \`organizationId (FK)\`  
\* \*\*BIARatingDefinition (child of BIAParameter):\*\* \`id\`, \`parameterId (FK)\`, \`ratingLabel (e.g., Low, 1-10)\`, \`minRange (nullable)\`, \`maxRange (nullable)\`, \`score\`, \`order\`  
\* \*\*BIAFramework:\*\* \`id\`, \`name\`, \`formula (e.g., Weighted Average)\`, \`thresholdValue\`, \`organizationId (FK)\`  
\* \*\*BIAFrameworkParameter (Junction Table):\*\* \`frameworkId (FK)\`, \`parameterId (FK)\`, \`weightage\`  
\* \*\*RTOOption:\*\* \`id\`, \`label (e.g., 4 hours)\`, \`valueInMinutes\`, \`organizationId (FK)\` (Predefined system-level options, organization can choose to use/edit)  
\* \*\*BIAInstance:\*\* \`id\`, \`departmentId (FK)\`, \`frameworkId (FK)\`, \`initiationDate\`, \`status (Initiated, Submitted for Review, Review in Progress, Approved)\`, \`frequency (Annually, Bi-annually, Biennially)\`, \`organizationId (FK)\`  
\* \*\*BIAProcessInput (child of BIAInstance, one per process):\*\* \`id\`, \`biaInstanceId (FK)\`, \`processId (FK)\`, \`processOwnerId (FK)\`, \`recommendedRTOId (FK to RTOOption)\`, \`rtoJustification\`, \`submittedDate\`, \`reviewerComments\`, \`departmentHeadApprovalNote\`, \`finalApprovedRTOId (FK to RTOOption)\`, \`finalImpactScore\`, \`status (matches BIAInstance status for that process)\`, \`organizationId (FK)\`  
\* \*\*BIAProcessParameterRating (child of BIAProcessInput):\*\* \`id\`, \`biaProcessInputId (FK)\`, \`parameterId (FK)\`, \`selectedRatingValue (e.g., "High" or "50-100")\`, \`qualitativeDescription\`, \`scoreGivenForRating\`

\#\#\# 7\. References for Future Phases and Features

\*\*Phase 2: Recovery Strategies & Plan Development\*\* \[cite: 30\]

\* Build and map recovery strategies to critical processes and applications. \[cite: 30\]  
\* Define recovery teams, roles, and responsibilities.  
\* Develop comprehensive Business Continuity Plans (BCPs) with step-by-step procedures. \[cite: 30\]  
\* Version control for BCPs.

\*\*Phase 3: Threat Assessment & Incident Management\*\* \[cite: 30\]

\* Conduct threat assessments, linking identified threats to potential impacts on processes. \[cite: 30\]  
\* Track business continuity incidents and responses. \[cite: 30\]  
\* Provide the ability to assess actual impact of incidents in business terms. \[cite: 30\]  
\* Integrate with threat intelligence feeds to assess potential business disruptions. \[cite: 30\]

\*\*Phase 4: Integrations & Advanced Reporting\*\* \[cite: 30\]

\* Integrate with other apps like HRMS (for employee contact info, roles), IT asset management systems (for application/infrastructure details), and threat intelligence feeds. \[cite: 30\]  
\* Advanced reporting and analytics dashboard for BCMS metrics, trends, and compliance.  
\* Simulation and testing functionalities for BCPs.