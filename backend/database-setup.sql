-- Database Setup Script for Forensic Image Storage System
-- PostgreSQL Version 12+

-- Create Database
CREATE DATABASE forensic_db;

-- Create User
CREATE USER forensic_user WITH PASSWORD 'forensic_password';

-- Grant Privileges
GRANT ALL PRIVILEGES ON DATABASE forensic_db TO forensic_user;

-- Connect to the database
\c forensic_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO forensic_user;

-- Note: Tables will be automatically created by Hibernate DDL
-- based on the Entity classes when the application starts.

-- The following tables will be created:
-- 1. users (user_id, username, password, created_at) - TESTING ONLY! Plain text passwords
-- 2. cases (case_id, case_name, description, created_at)
-- 3. images (image_id, case_id, filename, filepath, iv_base64, hmac_base64, uploaded_at)

-- Tables will be created automatically by Hibernate, but here's the manual SQL if needed:

-- CREATE TABLE IF NOT EXISTS users (
--     user_id BIGSERIAL PRIMARY KEY,
--     username VARCHAR(100) UNIQUE NOT NULL,
--     password VARCHAR(255) NOT NULL,  -- Plain text for testing only!
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS cases (
--     case_id BIGSERIAL PRIMARY KEY,
--     case_name VARCHAR(200) NOT NULL,
--     description TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS images (
--     image_id BIGSERIAL PRIMARY KEY,
--     case_id BIGINT NOT NULL,
--     filename VARCHAR(255) NOT NULL,
--     filepath VARCHAR(500) NOT NULL,
--     iv_base64 VARCHAR(255) NOT NULL,
--     hmac_base64 VARCHAR(255) NOT NULL,
--     uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
-- );

-- Create indexes for better query performance:
-- CREATE INDEX idx_users_username ON users(username);
-- CREATE INDEX idx_images_case_id ON images(case_id);

