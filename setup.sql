-- Create and switch to the database
CREATE DATABASE IF NOT EXISTS test;
USE test;

-- Drop existing tables to avoid conflicts
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS quizzes;
DROP TABLE IF EXISTS users;

-- Users table (with optional OTP)
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  role ENUM('student','teacher') NOT NULL,
  otp VARCHAR(6) NULL
);

-- Quizzes table
CREATE TABLE quizzes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  teacher_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Questions table
CREATE TABLE questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  quiz_id INT,
  question_text TEXT NOT NULL,
  option_a VARCHAR(255),
  option_b VARCHAR(255),
  option_c VARCHAR(255),
  option_d VARCHAR(255),
  correct_answer CHAR(1),
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Scores table
CREATE TABLE scores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  quiz_id INT,
  score INT,
  taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Demo teacher & student accounts
INSERT IGNORE INTO users (name, email, password, role) VALUES
('Demo Teacher', 'demo@karunya.edu', 'teacher123', 'teacher'),
('Demo Student', 'demo@karunya.edu.in', 'student123', 'student');
