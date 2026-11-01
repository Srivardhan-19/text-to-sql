-- Sample Seed Data for College Management Database

-- Departments
INSERT INTO departments (dept_id, dept_name, building, budget) VALUES
(1, 'Computer Science', 'Alan Turing Block', 1200000.00),
(2, 'Information Technology', 'Ada Lovelace Hall', 950000.00),
(3, 'Electronics', 'Nikola Tesla Building', 800000.00),
(4, 'Mechanical', 'James Watt Hall', 750000.00),
(5, 'Mathematics', 'Ramanujan Block', 500000.00);

-- Instructors
INSERT INTO instructors (instructor_id, name, email, dept_id, salary, hire_year) VALUES
(1, 'Dr. Rajesh Sharma', 'rajesh.sharma@college.edu', 1, 95000.00, 2015),
(2, 'Prof. Priya Nair', 'priya.nair@college.edu', 1, 88000.00, 2018),
(3, 'Dr. Amit Verma', 'amit.verma@college.edu', 2, 91000.00, 2016),
(4, 'Prof. Sneha Kulkarni', 'sneha.k@college.edu', 3, 82000.00, 2019),
(5, 'Dr. Vikram Rathore', 'vikram.r@college.edu', 4, 87000.00, 2014),
(6, 'Dr. Sunita Rao', 'sunita.rao@college.edu', 5, 89000.00, 2017);

-- Students
INSERT INTO students (student_id, student_name, gender, dept_id, admission_year, cgpa) VALUES
(1, 'Aarav Patel', 'Male', 1, 2021, 8.85),
(2, 'Diya Sen', 'Female', 1, 2021, 9.20),
(3, 'Rohan Gupta', 'Male', 1, 2022, 7.60),
(4, 'Ananya Iyer', 'Female', 2, 2021, 8.90),
(5, 'Kabir Mehta', 'Male', 2, 2022, 6.95),
(6, 'Isha Deshmukh', 'Female', 3, 2020, 8.40),
(7, 'Aditya Joshi', 'Male', 3, 2021, 7.80),
(8, 'Tanvi Bansal', 'Female', 4, 2020, 8.10),
(9, 'Rahul Verma', 'Male', 4, 2022, 6.70),
(10, 'Meera Nambiar', 'Female', 5, 2021, 9.50);

-- Courses
INSERT INTO courses (course_id, course_title, dept_id, credits, instructor_id) VALUES
(1, 'Database Management Systems', 1, 4, 1),
(2, 'Operating Systems', 1, 4, 2),
(3, 'Web Technologies', 2, 3, 3),
(4, 'Digital Signal Processing', 3, 4, 4),
(5, 'Thermodynamics', 4, 4, 5),
(6, 'Linear Algebra', 5, 3, 6);

-- Enrollments
INSERT INTO enrollments (enrollment_id, student_id, course_id, semester, year, grade) VALUES
(1, 1, 1, 'Fall', 2023, 'A'),
(2, 1, 2, 'Fall', 2023, 'A-'),
(3, 2, 1, 'Fall', 2023, 'A+'),
(4, 2, 2, 'Fall', 2023, 'A'),
(5, 3, 1, 'Fall', 2023, 'B'),
(6, 4, 1, 'Fall', 2023, 'A'),
(7, 4, 3, 'Fall', 2023, 'A'),
(8, 5, 3, 'Fall', 2023, 'C+'),
(9, 6, 4, 'Fall', 2023, 'B+'),
(10, 7, 4, 'Fall', 2023, 'B'),
(11, 8, 5, 'Fall', 2023, 'A-'),
(12, 10, 6, 'Fall', 2023, 'A+');

-- Marks
INSERT INTO marks (mark_id, student_id, course_id, subject, marks, exam_type) VALUES
(1, 1, 1, 'DBMS', 85, 'Final'),
(2, 1, 2, 'OS', 78, 'Final'),
(3, 2, 1, 'DBMS', 94, 'Final'),
(4, 2, 2, 'OS', 88, 'Final'),
(5, 3, 1, 'DBMS', 68, 'Final'),
(6, 4, 1, 'DBMS', 82, 'Final'),
(7, 4, 3, 'WebTech', 90, 'Final'),
(8, 5, 3, 'WebTech', 58, 'Final'),
(9, 6, 4, 'DSP', 76, 'Final'),
(10, 7, 4, 'DSP', 72, 'Final'),
(11, 8, 5, 'Thermo', 81, 'Final'),
(12, 10, 6, 'Algebra', 98, 'Final');

-- Classrooms
INSERT INTO classrooms (classroom_id, building, room_number, capacity) VALUES
(1, 'Alan Turing Block', 'T-101', 60),
(2, 'Alan Turing Block', 'T-102', 45),
(3, 'Ada Lovelace Hall', 'L-201', 50),
(4, 'Nikola Tesla Building', 'E-301', 40),
(5, 'James Watt Hall', 'M-105', 70);

