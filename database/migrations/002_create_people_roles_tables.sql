-- 002_create_people_roles_tables.sql

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert predefined roles (can be expanded)
-- These names should match what's expected in RBAC logic
INSERT INTO roles (name, description) VALUES
('Admin', 'System Administrator with full access'),
('BCM Manager', 'Business Continuity Management program manager'),
('Department Head', 'Head of a specific department'),
('Process Owner', 'Owner of a specific business process'),
('Employee', 'General employee user'),
('Internal Auditor', 'Auditor with read-only access to relevant data')
ON DUPLICATE KEY UPDATE name = name; -- Do nothing if role already exists

-- Create people table (renaming/enhancing users table)
-- Drop users table if it exists from a previous very basic setup and is being replaced
-- DROP TABLE IF EXISTS users; -- Uncomment if replacing an old 'users' table

CREATE TABLE IF NOT EXISTS people (
    id INT AUTO_INCREMENT PRIMARY KEY,
    organizationId INT NOT NULL,
    firstName VARCHAR(100) NOT NULL,
    lastName VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL, -- To be made unique per organization
    departmentId INT NULL,       -- Foreign key to departments table
    locationId INT NULL,         -- Foreign key to locations table (FR 1.5)
    jobTitle VARCHAR(100) NULL,
    isActive BOOLEAN DEFAULT TRUE,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    createdBy INT NULL,          -- Foreign key to people table (user who created this record)
    updatedBy INT NULL,          -- Foreign key to people table (user who last updated this record)

    FOREIGN KEY (organizationId) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (departmentId) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (locationId) REFERENCES locations(id) ON DELETE SET NULL, -- Assuming locations table exists or will exist
    FOREIGN KEY (createdBy) REFERENCES people(id) ON DELETE SET NULL,
    FOREIGN KEY (updatedBy) REFERENCES people(id) ON DELETE SET NULL,
    UNIQUE (organizationId, email) -- Email must be unique within an organization
);

-- Create people_roles junction table
CREATE TABLE IF NOT EXISTS people_roles (
    personId INT NOT NULL,
    roleId INT NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (personId, roleId),
    FOREIGN KEY (personId) REFERENCES people(id) ON DELETE CASCADE,
    FOREIGN KEY (roleId) REFERENCES roles(id) ON DELETE CASCADE
);

-- Index for faster lookups on people table
CREATE INDEX idx_people_email ON people(email);
CREATE INDEX idx_people_departmentId ON people(departmentId);
CREATE INDEX idx_people_locationId ON people(locationId);

