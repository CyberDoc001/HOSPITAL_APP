-- nuam_database schema and table creation script for PostgreSQL
-- Run this script with: psql -f database/nuam_database_schema.sql

CREATE DATABASE nuam_database;

\connect nuam_database;

CREATE USER IF NOT EXISTS nuam_user WITH PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE nuam_database TO nuam_user;

CREATE TABLE IF NOT EXISTS patients_doctor (
    id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(128) NOT NULL,
    last_name VARCHAR(128) NOT NULL,
    specialty VARCHAR(128) NOT NULL,
    email VARCHAR(254),
    phone VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS patients_patient (
    id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(128) NOT NULL,
    last_name VARCHAR(128) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(16) NOT NULL,
    email VARCHAR(254),
    phone VARCHAR(32),
    address TEXT,
    emergency_contact VARCHAR(256),
    primary_physician_id BIGINT REFERENCES patients_doctor(id) ON DELETE SET NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patients_appointment (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients_patient(id) ON DELETE CASCADE,
    doctor_id BIGINT REFERENCES patients_doctor(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'scheduled',
    reason VARCHAR(256),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patients_medicalrecord (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients_patient(id) ON DELETE CASCADE,
    record_type VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patients_admission (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients_patient(id) ON DELETE CASCADE,
    admission_date DATE NOT NULL,
    discharge_date DATE,
    ward VARCHAR(128) NOT NULL,
    bed_number VARCHAR(16) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'admitted',
    notes TEXT
);
