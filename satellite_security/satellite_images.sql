CREATE TABLE [dbo].[satellite_images]
(
  [Id] INT NOT NULL PRIMARY KEY
)
SELECT * FROM satellite_images;

CREATE TABLE satellite_images(
    image_id INTEGER PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    satellite VARCHAR(50),
    processing_level VARCHAR(20),
    tile_id VARCHAR(20),
    cloud_cover REAL,
    encrypted_image BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
