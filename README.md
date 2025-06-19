# Continuity Manager by CyRAACS - BCMS

Business Continuity Management System.

## Development Setup

### Placeholder User for Testing

For development and testing purposes, a default placeholder user and organization are seeded into the database. You can use these credentials to interact with the API when running the application locally.

*   **Default Organization ID**: `00000000-0000-0000-0000-000000000001`
*   **Default User (Admin) ID**: `00000000-0000-0000-0000-000000000002`
    *   **Email (for login if UI supports it/identification)**: `admin@default.com` (or similar, as defined in `backend/app/core/config.py` or seed script)
    *   **Role**: "Default Admin" (or equivalent superuser/admin role)
    *   **Permissions**: This user typically has broad permissions, including but not limited to:
        *   `department:create`
        *   `department:read`
        *   `department:update`
        *   `department:delete`
        *   `department:list`
        *   (Similar permissions for other modules like roles, people, locations, applications etc.)

When making API calls from tools like Postman or directly via `curl`, or when interacting through the frontend, ensure your requests are authenticated as this user (e.g., by obtaining a JWT token associated with this user ID) and that the `organizationId` (`00000000-0000-0000-0000-000000000001`) is correctly included in payloads where required (like department creation).

Refer to `backend/app/core/config.py` and any database seeding scripts (e.g., in `backend/app/db/init_db.py` or initial data loading mechanisms) for the precise details of the default user and organization setup.
