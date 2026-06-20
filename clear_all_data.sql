-- Clears ALL DATA from every table but keeps the table structure (schema) intact.
-- AUTO_INCREMENT counters also reset to 1 (TRUNCATE does this automatically).
-- Run this when you want a clean slate for testing without rebuilding the
-- whole database from Hostel_DB_V2.sql.

USE hostel_management;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE payment_transactions;
TRUNCATE TABLE deposit_transactions;
TRUNCATE TABLE deposit_deductions;
TRUNCATE TABLE deposit_settlements;
TRUNCATE TABLE payments;
TRUNCATE TABLE student_services;
TRUNCATE TABLE complaints;
TRUNCATE TABLE mess_attendance;
TRUNCATE TABLE room_allocations;
TRUNCATE TABLE admissions;
TRUNCATE TABLE students;
TRUNCATE TABLE rooms;

-- Keeping these as-is since they're reference/lookup data, not transactional
-- data — uncomment the next two lines only if you also want to wipe them:
-- TRUNCATE TABLE mess_menu;
-- TRUNCATE TABLE services;

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'All data cleared. Tables are empty, schema is intact.' AS status;

