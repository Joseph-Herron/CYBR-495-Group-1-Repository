CREATE TABLE [dbo].[satellite_metadata]
(
  [Id] INT NOT NULL PRIMARY KEY
)
SELECT * FROM satellite_metadata;

CREATE TABLE satellite_metadata(
metadata_id INTEGER PRIMARY KEY,
image_id INTEGER REFERENCES satellite_images(image_id),
latitude REAL,
longitude REAL,
sensing_time TIMESTAMP,
tile_id VARCHAR(20),
orbit_number INTEGER
);