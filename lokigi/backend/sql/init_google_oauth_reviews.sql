CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS google_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    google_account_name VARCHAR(255) NOT NULL,
    location_id VARCHAR(128) NOT NULL,
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT NOT NULL,
    token_expiry TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_google_connections_user_id UNIQUE (user_id),
    CONSTRAINT uq_google_connections_location_id UNIQUE (location_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL REFERENCES google_connections(id) ON DELETE CASCADE,
    review_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(128) NOT NULL,
    rating INT,
    comment TEXT,
    create_time TIMESTAMPTZ,
    update_time TIMESTAMPTZ,
    author_display_name VARCHAR(255),
    author_profile_photo_url TEXT,
    author_is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
    author_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    author_metadata_hash CHAR(64) NOT NULL,
    raw_payload JSONB NOT NULL,
    raw_payload_hash CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reviews_review_id UNIQUE (review_id)
);

CREATE INDEX IF NOT EXISTS ix_reviews_location_id ON reviews(location_id);
