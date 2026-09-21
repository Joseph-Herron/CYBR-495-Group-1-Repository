CREATE TABLE [dbo].[access_logs]
(
  [Id] INT NOT NULL PRIMARY KEY
)
SELECT * FROM access_logs;

CREATE TABLE access_logs (
	log_id INTEGER PRIMARY KEY,
	user_id VARCHAR(100),
	iamge_id INTEGER REFERENCES satellite_images(image_id),
	action VARCHAR(50),
	success BOOLEAN,
	timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);