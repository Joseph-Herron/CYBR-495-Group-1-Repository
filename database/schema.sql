CREATE TABLE satellite_images (
    image_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    satellite VARCHAR(50),
    processing_level VARCHAR(20),
    tile_id VARCHAR(20),
    cloud_cover REAL,
    encrypted_image BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE satellite_metadata (
    metadata_id INTEGER PRIMARY KEY,
    image_id INTEGER REFERENCES satellite_images(image_id),
    latitude REAL,
    longitude REAL,
    sensing_time TIMESTAMP,
    tile_id VARCHAR(20),
    orbit_number INTEGER
);

CREATE TABLE access_logs (
    log_id INTEGER PRIMARY KEY,
    user_id VARCHAR(100),
    image_id INTEGER REFERENCES satellite_images(image_id),
    action VARCHAR(50),
    success BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
