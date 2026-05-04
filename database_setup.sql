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
    status VARCHAR(10) DEFAULT 'Present', -- Present, Absent, Late
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
    subject_id varchar(50),
    UNIQUE KEY unique_teacher_subject (teacher_id, subject_id),
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

CREATE TABLE announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,
    posted_by INT,
    target_role VARCHAR(20) DEFAULT 'all', -- 'all', 'students', 'teachers'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by) REFERENCES users(id)
);


INSERT INTO users (username, password, role, full_name) VALUES
('admin', 'admin123', 'admin', 'Administrator');

INSERT INTO sections (section_name) VALUES ('12-A'), ('12-B');

INSERT INTO users (username, password, role, full_name, section_id) VALUES
('teacher1', 'teacher123', 'teacher', 'John Doe', 1),
('teacher2', 'teacher123', 'teacher', 'Jane Doe', 2);

INSERT INTO teacher_sections (teacher_id, section_id) VALUES
(1, 1), -- teacher1 assigned to section 12-A
(2, 2); -- teacher2 assigned to section 12-B

INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES
(1, 'Mathematics'), -- teacher1 teaches Mathematics
(2, 'Computer Science'); -- teacher2 teaches Computer Science

INSERT INTO users (username, password, role, full_name) VALUES
('student1', 'student123', 'student', 'Alice Smith'),
('student2', 'student123', 'student', 'Diana Prince');

INSERT INTO students (name, roll_no, section_id, user_id) VALUES
('Alice Smith', '001', 1, 3), -- student1 in section 12-A
('Diana Prince', '002', 2, 4); -- student2 in section 12-B

INSERT INTO subjects (subject_name) VALUES 
('Mathematics'),
('English'),
('Chemistry'),
('Physics'),
('Biology'),
('Computer Science');

INSERT INTO marks (student_id, subject, exam_name, marks_obtained, total_marks, exam_date) VALUES
(1, 'Mathematics', 'Midterm', 85, 100, '2024-05-01'),
(1, 'English', 'Midterm', 78, 100, '2024-05-02'),
(2, 'Computer Science', 'Midterm', 92, 100, '2024-05-01'),
(2, 'Mathematics', 'Midterm', 88, 100, '2024-05-02');



