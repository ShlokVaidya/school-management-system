CREATE DATABASE IF NOT EXISTS student_tracker;
USE student_tracker;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(50),
    role ENUM('admin', 'teacher', 'student', 'vice_principal', 'coordinator'),
    full_name VARCHAR(100),
    section_id INT DEFAULT NULL
);

INSERT INTO users (username, password, role, full_name) VALUES
('admin', 'adminpass', 'admin', 'Administrator')