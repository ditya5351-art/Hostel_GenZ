-- ==========================================================
-- HOSTEL MANAGEMENT DATABASE — V2
-- Builds on Hostel_DB_V1.sql, adds:
--   - complaints table (was missing, needed for dashboard)
--   - mess_menu table (was missing, needed for dashboard)
--   - indexes on foreign keys (V1 had none -> slow joins as data grows)
--   - a couple of VIEWs so Streamlit queries stay simple
-- Safe to run on a FRESH database. If you already ran V1 and have
-- real data in it, scroll to the "MIGRATION FOR EXISTING DB" block
-- at the bottom instead and run only that part.
-- ==========================================================

CREATE DATABASE IF NOT EXISTS hostel_management;
USE hostel_management;

-- ==========================================
-- STUDENTS
-- ==========================================
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,
    father_name VARCHAR(100),
    mother_name VARCHAR(100),

    guardian_name VARCHAR(100),
    guardian_mobile VARCHAR(15),

    date_of_birth DATE,

    mobile_number VARCHAR(15) NOT NULL,
    email_address VARCHAR(100),

    college_institution VARCHAR(150),
    course_branch VARCHAR(100),

    aadhaar_number VARCHAR(20) UNIQUE,

    permanent_address TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- ROOMS
-- ==========================================
CREATE TABLE IF NOT EXISTS rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(20) NOT NULL UNIQUE,
    total_beds INT NOT NULL,
    CHECK (total_beds > 0)
);

-- ==========================================
-- ADMISSIONS  (one row per student's stay)
-- ==========================================
CREATE TABLE IF NOT EXISTS admissions (
    admission_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,

    joining_date DATE NOT NULL,
    checkout_date DATE DEFAULT NULL,

    monthly_rent DECIMAL(10,2) NOT NULL,
    security_deposit DECIMAL(10,2) DEFAULT 0,

    status ENUM('Active','Checked Out') DEFAULT 'Active',
    checkout_reason VARCHAR(255),
    remarks TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
CREATE INDEX idx_admissions_student ON admissions(student_id);
CREATE INDEX idx_admissions_status ON admissions(status);

-- ==========================================
-- ROOM ALLOCATIONS  (which room an admission currently/previously occupies)
-- ==========================================
CREATE TABLE IF NOT EXISTS room_allocations (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id INT NOT NULL,
    room_id INT NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE DEFAULT NULL,
    is_current BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
CREATE INDEX idx_alloc_admission ON room_allocations(admission_id);
CREATE INDEX idx_alloc_room ON room_allocations(room_id);
CREATE INDEX idx_alloc_current ON room_allocations(is_current);

-- ==========================================
-- SERVICES (mess, laundry, etc — optional add-ons)
-- ==========================================
CREATE TABLE IF NOT EXISTS services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL UNIQUE,
    monthly_charge DECIMAL(10,2) NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS student_services (
    student_service_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id INT NOT NULL,
    service_id INT NOT NULL,
    start_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id),
    UNIQUE(admission_id, service_id)
);
CREATE INDEX idx_studentservices_admission ON student_services(admission_id);

-- ==========================================
-- MONTHLY PAYMENTS (one row per student per billing month)
-- ==========================================
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id INT NOT NULL,

    billing_month DATE NOT NULL,   -- store as YYYY-MM-01

    rent_amount DECIMAL(10,2) DEFAULT 0,
    service_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    amount_paid DECIMAL(10,2) DEFAULT 0,

    payment_status ENUM('Pending','Partial','Paid') DEFAULT 'Pending',
    due_date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id),
    UNIQUE(admission_id, billing_month)
);
CREATE INDEX idx_payments_admission ON payments(admission_id);
CREATE INDEX idx_payments_month ON payments(billing_month);
CREATE INDEX idx_payments_status ON payments(payment_status);

-- ==========================================
-- PAYMENT TRANSACTIONS (actual cash/UPI entries against a payment row)
-- ==========================================
CREATE TABLE IF NOT EXISTS payment_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_mode ENUM('Cash','UPI','Bank Transfer') NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    remarks VARCHAR(255),
    FOREIGN KEY (payment_id) REFERENCES payments(payment_id)
);
CREATE INDEX idx_transactions_payment ON payment_transactions(payment_id);

-- ==========================================
-- DEPOSIT SETTLEMENTS / DEDUCTIONS
-- ==========================================
CREATE TABLE IF NOT EXISTS deposit_settlements (
    settlement_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id INT NOT NULL UNIQUE,
    deposit_amount DECIMAL(10,2) NOT NULL,
    total_deduction DECIMAL(10,2) DEFAULT 0,
    refund_amount DECIMAL(10,2) NOT NULL,
    settlement_date DATE,
    remarks TEXT,
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE TABLE IF NOT EXISTS deposit_deductions (
    deduction_id INT AUTO_INCREMENT PRIMARY KEY,
    settlement_id INT NOT NULL,
    deduction_reason VARCHAR(255) NOT NULL,
    deduction_amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (settlement_id) REFERENCES deposit_settlements(settlement_id)
);

-- ==========================================
-- COMPLAINTS  (NEW — needed for dashboard, wasn't in V1)
-- ==========================================
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,
    room_id INT DEFAULT NULL,

    title VARCHAR(150) NOT NULL,
    description TEXT,

    status ENUM('Open','In Progress','Resolved') DEFAULT 'Open',

    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL DEFAULT NULL,

    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_student ON complaints(student_id);

-- ==========================================
-- MESS MENU  (NEW — needed for dashboard, wasn't in V1)
-- ==========================================
CREATE TABLE IF NOT EXISTS mess_menu (
    menu_id INT AUTO_INCREMENT PRIMARY KEY,

    day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
    meal_type ENUM('Breakfast','Lunch','Dinner') NOT NULL,
    items VARCHAR(255) NOT NULL,

    UNIQUE(day_of_week, meal_type)
);

-- ==========================================
-- MESS ATTENDANCE  (NEW — optional, for "30/32 had dinner" type stats)
-- ==========================================
CREATE TABLE IF NOT EXISTS mess_attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    meal_type ENUM('Breakfast','Lunch','Dinner') NOT NULL,
    present BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    UNIQUE(student_id, attendance_date, meal_type)
);

-- ==========================================
-- VIEWS — keep Streamlit's queries.py simple & fast
-- ==========================================

-- Current room occupancy: one row per room with beds filled / vacant
CREATE OR REPLACE VIEW v_room_occupancy AS
SELECT
    r.room_id,
    r.room_number,
    r.total_beds,
    COUNT(ra.allocation_id) AS beds_occupied,
    (r.total_beds - COUNT(ra.allocation_id)) AS beds_vacant
FROM rooms r
LEFT JOIN room_allocations ra
    ON ra.room_id = r.room_id AND ra.is_current = 1
GROUP BY r.room_id, r.room_number, r.total_beds;

-- Current occupants with their student + admission + room info
CREATE OR REPLACE VIEW v_current_occupants AS
SELECT
    s.student_id,
    s.full_name,
    s.mobile_number,
    a.admission_id,
    a.monthly_rent,
    r.room_id,
    r.room_number
FROM admissions a
JOIN students s ON s.student_id = a.student_id
JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
JOIN rooms r ON r.room_id = ra.room_id
WHERE a.status = 'Active';

-- Default mess menu (you can edit later from the app)
INSERT INTO mess_menu (day_of_week, meal_type, items) VALUES
('Monday','Breakfast','Poha, Tea'),
('Monday','Lunch','Dal, Rice, Aloo Sabzi, Roti'),
('Monday','Dinner','Rajma, Rice, Salad')
ON DUPLICATE KEY UPDATE items = VALUES(items);

-- Default services
INSERT INTO services (service_name, monthly_charge, description) VALUES
('Mess', 3000, 'Monthly mess facility'),
('Tiffin', 500, 'Daily tiffin service'),
('Laundry', 500, 'Laundry facility'),
('Pick & Drop', 1000, 'Transportation service')
ON DUPLICATE KEY UPDATE monthly_charge = VALUES(monthly_charge);


-- ==========================================================
-- MIGRATION FOR EXISTING DB (you already ran V1 and have data)
-- Run ONLY the block below in that case, skip everything above.
-- ==========================================================
/*
USE hostel_management;

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    room_id INT DEFAULT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    status ENUM('Open','In Progress','Resolved') DEFAULT 'Open',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_student ON complaints(student_id);

CREATE TABLE IF NOT EXISTS mess_menu (
    menu_id INT AUTO_INCREMENT PRIMARY KEY,
    day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
    meal_type ENUM('Breakfast','Lunch','Dinner') NOT NULL,
    items VARCHAR(255) NOT NULL,
    UNIQUE(day_of_week, meal_type)
);

CREATE TABLE IF NOT EXISTS mess_attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    meal_type ENUM('Breakfast','Lunch','Dinner') NOT NULL,
    present BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    UNIQUE(student_id, attendance_date, meal_type)
);

CREATE INDEX idx_admissions_student ON admissions(student_id);
CREATE INDEX idx_admissions_status ON admissions(status);
CREATE INDEX idx_alloc_admission ON room_allocations(admission_id);
CREATE INDEX idx_alloc_room ON room_allocations(room_id);
CREATE INDEX idx_alloc_current ON room_allocations(is_current);
CREATE INDEX idx_payments_admission ON payments(admission_id);
CREATE INDEX idx_payments_month ON payments(billing_month);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_transactions_payment ON payment_transactions(payment_id);

CREATE OR REPLACE VIEW v_room_occupancy AS
SELECT r.room_id, r.room_number, r.total_beds,
       COUNT(ra.allocation_id) AS beds_occupied,
       (r.total_beds - COUNT(ra.allocation_id)) AS beds_vacant
FROM rooms r
LEFT JOIN room_allocations ra ON ra.room_id = r.room_id AND ra.is_current = 1
GROUP BY r.room_id, r.room_number, r.total_beds;

CREATE OR REPLACE VIEW v_current_occupants AS
SELECT s.student_id, s.full_name, s.mobile_number, a.admission_id, a.monthly_rent,
       r.room_id, r.room_number
FROM admissions a
JOIN students s ON s.student_id = a.student_id
JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
JOIN rooms r ON r.room_id = ra.room_id
WHERE a.status = 'Active';
*/