
CREATE TABLE IF NOT EXISTS access_logs (
    log_id INTEGER PRIMARY KEY,
    user_id VARCHAR(100),
    image_id INTEGER REFERENCES satellite_images(image_id),
    action VARCHAR(50),
    success BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
