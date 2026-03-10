-- Create all microservice databases
-- Runs automatically when PostgreSQL container first starts

CREATE DATABASE stockpilot_auth;
CREATE DATABASE stockpilot_inventory;
CREATE DATABASE stockpilot_billing;
CREATE DATABASE stockpilot_crm;
CREATE DATABASE stockpilot_notifications;

-- Grant all permissions to the stockpilot user
GRANT ALL PRIVILEGES ON DATABASE stockpilot_auth TO stockpilot;
GRANT ALL PRIVILEGES ON DATABASE stockpilot_inventory TO stockpilot;
GRANT ALL PRIVILEGES ON DATABASE stockpilot_billing TO stockpilot;
GRANT ALL PRIVILEGES ON DATABASE stockpilot_crm TO stockpilot;
GRANT ALL PRIVILEGES ON DATABASE stockpilot_notifications TO stockpilot;
