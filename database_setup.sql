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

CREATE TABLE sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    section_name VARCHAR(10) NOT NULL
);

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    roll_no VARCHAR(10),
    section_id INT,
    user_id INT,
    email VARCHAR(100) DEFAULT NULL,
    phone VARCHAR(15) DEFAULT NULL,
    dob DATE DEFAULT NULL,
    gender VARCHAR(10) DEFAULT NULL,
    parent_name VARCHAR(100) DEFAULT NULL,
    parent_phone VARCHAR(15) DEFAULT NULL,
    address VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (section_id) REFERENCES sections(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_roll_in_section (roll_no, section_id)
);

CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(50)
);

CREATE TABLE assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    description TEXT,
    subject VARCHAR(50),
    due_date DATE,
    section_id INT,
    teacher_id INT,
    FOREIGN KEY (section_id) REFERENCES sections(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

CREATE TABLE student_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    assignment_id INT,
    status VARCHAR(20) DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id)
);

CREATE TABLE marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject VARCHAR(50),
    exam_name VARCHAR(50),
    marks_obtained INT,
    total_marks INT,
    exam_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    date DATE,
    status VARCHAR(10) DEFAULT 'Present',   -- Present, Absent, Late
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE teacher_sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    section_id INT,
    UNIQUE KEY unique_teacher_section (teacher_id, section_id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (section_id) REFERENCES sections(id)
);

CREATE TABLE teacher_subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    subject_name VARCHAR(50),
    UNIQUE KEY unique_teacher_subject (teacher_id, subject_name),
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

CREATE TABLE announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,
    posted_by INT,    -- user id of who posted it
    target_role VARCHAR(20) DEFAULT 'all',   -- 'all', 'student', 'teacher'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by) REFERENCES users(id)
);

INSERT INTO users (username, password, role, full_name) VALUES
('admin', 'admin123', 'admin', 'Administrator');

INSERT INTO users (username, password, role, full_name) VALUES
('vp1',    'vp123',    'vice_principal', 'Mrs. Anita Desai (Vice Principal)'),
('coord1', 'coord123', 'coordinator',    'Mr. Vikram Mehta (Coordinator)');