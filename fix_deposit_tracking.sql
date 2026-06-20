-- Run this against your EXISTING hostel_management database.
-- It only adds the deposit_transactions table + v_deposit_status view
-- that were missing — nothing else is touched, your current data is safe.

USE hostel_management;

CREATE TABLE IF NOT EXISTS deposit_transactions (
    deposit_transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_mode ENUM('Cash','UPI','Bank Transfer') NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    remarks VARCHAR(255),
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE INDEX idx_deposit_txn_admission ON deposit_transactions(admission_id);

CREATE OR REPLACE VIEW v_deposit_status AS
SELECT
    a.admission_id,
    a.security_deposit AS deposit_expected,
    COALESCE(SUM(dt.amount), 0) AS deposit_collected,
    (a.security_deposit - COALESCE(SUM(dt.amount), 0)) AS deposit_due
FROM admissions a
LEFT JOIN deposit_transactions dt ON dt.admission_id = a.admission_id
GROUP BY a.admission_id, a.security_deposit;

