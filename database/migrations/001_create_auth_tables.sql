-- NovaMS Authentication Tables Migration
-- Run this SQL script once to initialize the authentication system
-- Supports PostgreSQL 12+

-- Drop tables if they exist (for development/reset)
-- DROP TABLE IF EXISTS activity_log CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create activity_log table for audit trail
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_verified ON users(is_verified);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_user_id ON activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_action ON activity_log(action);

-- Create comments for documentation
COMMENT ON TABLE users IS 'User accounts for NovaMS authentication';
COMMENT ON TABLE activity_log IS 'Audit trail of user activities';

COMMENT ON COLUMN users.email IS 'Unique email address used for login';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password (never plain text)';
COMMENT ON COLUMN users.role IS 'User role: user (default), admin, or moderator';
COMMENT ON COLUMN users.is_verified IS 'Email verification status';
COMMENT ON COLUMN users.is_active IS 'Account active status';
COMMENT ON COLUMN users.last_login IS 'Timestamp of last successful login';

-- Insert sample data (optional - for development only)
-- Uncomment to use. Default admin password: Admin@123456
-- INSERT INTO users (email, password_hash, name, role, is_verified, is_active)
-- VALUES (
--     'admin@novams.com',
--     '$2b$12$...', -- Use: python -c "from auth.hashing import hash_password; print(hash_password('Admin@123456'))"
--     'Admin User',
--     'admin',
--     TRUE,
--     TRUE
-- ) ON CONFLICT (email) DO NOTHING;

-- Verify tables
SELECT 
    tablename,
    ARRAY_AGG(columnname) as columns
FROM pg_tables
JOIN pg_class ON relname = tablename
LEFT JOIN information_schema.columns ON table_name = tablename
WHERE schemaname = 'public' AND tablename IN ('users', 'activity_log')
GROUP BY tablename;
