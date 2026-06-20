"""
All SQL lives here. app.py never writes raw SQL — it just calls these functions.
Keeps the Streamlit file readable and makes it easy to reuse queries across pages.
"""
from datetime import date
from db import run_query, run_write


def current_month_str():
    return date.today().strftime("%Y-%m-01")


# ---------------------------------------------------------------
# DASHBOARD STATS
# ---------------------------------------------------------------
def get_total_students():
    return run_query("SELECT COUNT(*) AS c FROM students")[0]["c"]


def get_active_students():
    return run_query(
        "SELECT COUNT(*) AS c FROM admissions WHERE status = 'Active'"
    )[0]["c"]


def get_room_capacity():
    row = run_query("SELECT SUM(total_beds) AS c FROM rooms")[0]
    return row["c"] or 0


def get_occupied_beds():
    row = run_query(
        "SELECT COUNT(*) AS c FROM room_allocations WHERE is_current = 1"
    )[0]
    return row["c"] or 0


def get_rent_collected(billing_month=None):
    billing_month = billing_month or current_month_str()
    row = run_query(
        "SELECT COALESCE(SUM(amount_paid),0) AS total "
        "FROM payments WHERE billing_month = %s",
        (billing_month,),
    )[0]
    return float(row["total"])


def get_rent_expected(billing_month=None):
    billing_month = billing_month or current_month_str()
    row = run_query(
        "SELECT COALESCE(SUM(total_amount),0) AS total "
        "FROM payments WHERE billing_month = %s",
        (billing_month,),
    )[0]
    return float(row["total"])


def get_pending_count(billing_month=None):
    billing_month = billing_month or current_month_str()
    row = run_query(
        "SELECT COUNT(*) AS c FROM payments "
        "WHERE billing_month = %s AND payment_status != 'Paid'",
        (billing_month,),
    )[0]
    return row["c"]


def get_pending_amount(billing_month=None):
    billing_month = billing_month or current_month_str()
    row = run_query(
        "SELECT COALESCE(SUM(total_amount - amount_paid),0) AS total "
        "FROM payments WHERE billing_month = %s AND payment_status != 'Paid'",
        (billing_month,),
    )[0]
    return float(row["total"])


# ---------------------------------------------------------------
# ROOMS
# ---------------------------------------------------------------
def get_room_status_grid(billing_month=None):
    """
    One row per occupant (or vacant bed) with their current rent status,
    used to draw the room nameplate grid.
    """
    billing_month = billing_month or current_month_str()
    return run_query(
        """
        SELECT
            r.room_id,
            r.room_number,
            r.total_beds,
            s.student_id,
            s.full_name,
            p.payment_status
        FROM rooms r
        LEFT JOIN room_allocations ra
            ON ra.room_id = r.room_id AND ra.is_current = 1
        LEFT JOIN admissions a
            ON a.admission_id = ra.admission_id
        LEFT JOIN students s
            ON s.student_id = a.student_id
        LEFT JOIN payments p
            ON p.admission_id = a.admission_id AND p.billing_month = %s
        ORDER BY r.room_number
        """,
        (billing_month,),
    )


def get_room_occupancy_summary():
    return run_query("SELECT * FROM v_room_occupancy ORDER BY room_number")


def get_all_rooms():
    return run_query("SELECT * FROM rooms ORDER BY room_number")


def add_room(room_number, total_beds):
    return run_write(
        "INSERT INTO rooms (room_number, total_beds) VALUES (%s, %s)",
        (room_number, total_beds),
    )


def update_room(room_id, room_number, total_beds):
    """
    Updates a room's number/bed-count. Refuses to shrink total_beds below
    beds currently occupied, since that would orphan an existing student.
    """
    occupied = run_query(
        "SELECT COUNT(*) AS c FROM room_allocations WHERE room_id = %s AND is_current = 1",
        (room_id,),
    )[0]["c"]
    if total_beds < occupied:
        raise ValueError(
            f"Total beds {total_beds} se kam nahi kiya ja sakta — abhi {occupied} student(s) is room mein hain."
        )
    run_write(
        "UPDATE rooms SET room_number = %s, total_beds = %s WHERE room_id = %s",
        (room_number, total_beds, room_id),
    )


def delete_room(room_id):
    """Refuses to delete a room that still has students in it."""
    occupied = run_query(
        "SELECT COUNT(*) AS c FROM room_allocations WHERE room_id = %s AND is_current = 1",
        (room_id,),
    )[0]["c"]
    if occupied > 0:
        raise ValueError(f"Pehle is room ke {occupied} student(s) ko dusre room mein shift/checkout karo.")
    run_write("DELETE FROM rooms WHERE room_id = %s", (room_id,))


# ---------------------------------------------------------------
# STUDENTS
# ---------------------------------------------------------------
def get_all_students_with_room():
    return run_query(
        """
        SELECT
            s.student_id, s.full_name, s.mobile_number, s.course_branch,
            r.room_number, a.monthly_rent, a.status
        FROM students s
        LEFT JOIN admissions a ON a.student_id = s.student_id AND a.status = 'Active'
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        ORDER BY s.student_id DESC
        """
    )


def search_students_by_name(name_query):
    """Used for the 'type to search' student picker — matches partial names."""
    return run_query(
        """
        SELECT s.student_id, s.full_name, r.room_number
        FROM students s
        LEFT JOIN admissions a ON a.student_id = s.student_id AND a.status = 'Active'
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        WHERE s.full_name LIKE %s
        ORDER BY s.full_name
        """,
        (f"%{name_query}%",),
    )


def get_student_full_details(student_id):
    """Everything needed to pre-fill the edit form: student info + their
    active admission's rent/deposit + current room."""
    rows = run_query(
        """
        SELECT
            s.student_id, s.full_name, s.father_name, s.mobile_number,
            s.course_branch, s.email_address,
            a.admission_id, a.monthly_rent, a.security_deposit, a.joining_date,
            r.room_id, r.room_number
        FROM students s
        LEFT JOIN admissions a ON a.student_id = s.student_id AND a.status = 'Active'
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        WHERE s.student_id = %s
        """,
        (student_id,),
    )
    return rows[0] if rows else None


def update_student_details(student_id, full_name, father_name, mobile, course, email):
    """Updates the student's personal info (not room/rent — those are handled
    separately since changing room needs a new allocation, not just an edit)."""
    run_write(
        """
        UPDATE students
        SET full_name = %s, father_name = %s, mobile_number = %s,
            course_branch = %s, email_address = %s
        WHERE student_id = %s
        """,
        (full_name, father_name, mobile, course, email, student_id),
    )


def update_admission_rent(admission_id, monthly_rent, security_deposit):
    """Updates rent/deposit on the student's CURRENT admission record.
    Note: this does not retroactively change already-generated bills —
    only affects future months' bills."""
    run_write(
        "UPDATE admissions SET monthly_rent = %s, security_deposit = %s WHERE admission_id = %s",
        (monthly_rent, security_deposit, admission_id),
    )


def change_student_room(admission_id, old_room_id, new_room_id, change_date):
    """Moves a student to a different room: closes the old allocation,
    opens a new one. Refuses if the new room has no vacant bed."""
    vacant = run_query(
        "SELECT beds_vacant FROM v_room_occupancy WHERE room_id = %s", (new_room_id,)
    )
    if not vacant or vacant[0]["beds_vacant"] <= 0:
        raise ValueError("Naye room mein koi vacant bed nahi hai.")

    run_write(
        "UPDATE room_allocations SET is_current = 0, end_date = %s "
        "WHERE admission_id = %s AND room_id = %s AND is_current = 1",
        (change_date, admission_id, old_room_id),
    )
    run_write(
        "INSERT INTO room_allocations (admission_id, room_id, start_date, is_current) "
        "VALUES (%s, %s, %s, 1)",
        (admission_id, new_room_id, change_date),
    )


def delete_student_completely(student_id):
    """
    PERMANENTLY deletes a student and every record linked to them —
    payments, transactions, complaints, room history, deposit settlements,
    all gone. Unlike checkout (which preserves history), this is for when
    a student was added by mistake and you want a clean slate.

    Deletes in the correct order to satisfy foreign key constraints
    (children before parents).
    """
    admissions = run_query(
        "SELECT admission_id FROM admissions WHERE student_id = %s", (student_id,)
    )
    admission_ids = [a["admission_id"] for a in admissions]

    for admission_id in admission_ids:
        payments = run_query(
            "SELECT payment_id FROM payments WHERE admission_id = %s", (admission_id,)
        )
        for p in payments:
            run_write("DELETE FROM payment_transactions WHERE payment_id = %s", (p["payment_id"],))
        run_write("DELETE FROM payments WHERE admission_id = %s", (admission_id,))

        run_write("DELETE FROM deposit_transactions WHERE admission_id = %s", (admission_id,))

        settlements = run_query(
            "SELECT settlement_id FROM deposit_settlements WHERE admission_id = %s", (admission_id,)
        )
        for s in settlements:
            run_write("DELETE FROM deposit_deductions WHERE settlement_id = %s", (s["settlement_id"],))
        run_write("DELETE FROM deposit_settlements WHERE admission_id = %s", (admission_id,))

        run_write("DELETE FROM student_services WHERE admission_id = %s", (admission_id,))
        run_write("DELETE FROM room_allocations WHERE admission_id = %s", (admission_id,))

    run_write("DELETE FROM admissions WHERE student_id = %s", (student_id,))
    run_write("DELETE FROM complaints WHERE student_id = %s", (student_id,))
    run_write("DELETE FROM mess_attendance WHERE student_id = %s", (student_id,))
    run_write("DELETE FROM students WHERE student_id = %s", (student_id,))


def get_vacant_rooms():
    return run_query(
        "SELECT room_id, room_number, beds_vacant FROM v_room_occupancy "
        "WHERE beds_vacant > 0 ORDER BY room_number"
    )


def add_student_with_admission(full_name, father_name, mobile, course,
                                room_id, monthly_rent, security_deposit, joining_date):
    """
    Creates the student, their admission record, and allocates them to a room
    — all three steps the old app.py was missing (it only inserted into `students`
    with a `room_number` column that doesn't even exist in the schema).
    """
    student_id = run_write(
        """
        INSERT INTO students (full_name, father_name, mobile_number, course_branch)
        VALUES (%s, %s, %s, %s)
        """,
        (full_name, father_name, mobile, course),
    )

    admission_id = run_write(
        """
        INSERT INTO admissions (student_id, joining_date, monthly_rent, security_deposit, status)
        VALUES (%s, %s, %s, %s, 'Active')
        """,
        (student_id, joining_date, monthly_rent, security_deposit),
    )

    run_write(
        """
        INSERT INTO room_allocations (admission_id, room_id, start_date, is_current)
        VALUES (%s, %s, %s, 1)
        """,
        (admission_id, room_id, joining_date),
    )

    # Auto-create this month's pending rent bill so it shows up on the dashboard
    run_write(
        """
        INSERT INTO payments (admission_id, billing_month, rent_amount, total_amount, payment_status)
        VALUES (%s, %s, %s, %s, 'Pending')
        ON DUPLICATE KEY UPDATE rent_amount = rent_amount
        """,
        (admission_id, current_month_str(), monthly_rent, monthly_rent),
    )

    return student_id


# ---------------------------------------------------------------
# PAYMENTS / RENT LEDGER
# ---------------------------------------------------------------
def get_rent_ledger(billing_month=None):
    billing_month = billing_month or current_month_str()
    return run_query(
        """
        SELECT
            s.full_name AS student,
            r.room_number AS room,
            p.payment_id,
            p.total_amount,
            p.amount_paid,
            p.payment_status,
            (SELECT MAX(transaction_date) FROM payment_transactions t
                WHERE t.payment_id = p.payment_id) AS last_paid_on
        FROM payments p
        JOIN admissions a ON a.admission_id = p.admission_id
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        WHERE p.billing_month = %s
        ORDER BY s.full_name
        """,
        (billing_month,),
    )


def get_recent_payments(limit=5):
    return run_query(
        """
        SELECT
            s.full_name AS student,
            r.room_number AS room,
            t.amount,
            t.payment_mode,
            t.transaction_date
        FROM payment_transactions t
        JOIN payments p ON p.payment_id = t.payment_id
        JOIN admissions a ON a.admission_id = p.admission_id
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        ORDER BY t.transaction_date DESC
        LIMIT %s
        """,
        (limit,),
    )


def record_payment(payment_id, amount, payment_mode, remarks=""):
    """Adds a single transaction and updates the payment row's paid amount + status."""
    run_write(
        """
        INSERT INTO payment_transactions (payment_id, amount, payment_mode, remarks)
        VALUES (%s, %s, %s, %s)
        """,
        (payment_id, amount, payment_mode, remarks),
    )

    row = run_query(
        "SELECT total_amount, amount_paid FROM payments WHERE payment_id = %s",
        (payment_id,),
    )[0]
    new_paid = float(row["amount_paid"]) + float(amount)
    total = float(row["total_amount"])
    new_status = "Paid" if new_paid >= total else ("Partial" if new_paid > 0 else "Pending")

    run_write(
        "UPDATE payments SET amount_paid = %s, payment_status = %s WHERE payment_id = %s",
        (new_paid, new_status, payment_id),
    )


def record_split_payment(payment_id, splits):
    """
    Records rent paid across multiple modes in ONE go.
    splits = [{"amount": 2000, "mode": "Cash", "remarks": ""},
              {"amount": 2500, "mode": "UPI", "remarks": ""}]
    Each split becomes its own row in payment_transactions (so the receipt /
    history shows exactly how much came in cash vs UPI), but the student's
    payments row is updated only once at the end.
    """
    total_new = sum(float(s["amount"]) for s in splits)
    for s in splits:
        run_write(
            """
            INSERT INTO payment_transactions (payment_id, amount, payment_mode, remarks)
            VALUES (%s, %s, %s, %s)
            """,
            (payment_id, s["amount"], s["mode"], s.get("remarks", "")),
        )

    row = run_query(
        "SELECT total_amount, amount_paid FROM payments WHERE payment_id = %s",
        (payment_id,),
    )[0]
    new_paid = float(row["amount_paid"]) + total_new
    total = float(row["total_amount"])
    new_status = "Paid" if new_paid >= total else ("Partial" if new_paid > 0 else "Pending")

    run_write(
        "UPDATE payments SET amount_paid = %s, payment_status = %s WHERE payment_id = %s",
        (new_paid, new_status, payment_id),
    )


def get_payment_mode_breakdown(payment_id):
    """Shows exactly how a rent bill was paid — e.g. ₹2000 Cash + ₹2500 UPI."""
    return run_query(
        """
        SELECT payment_mode, SUM(amount) AS total, transaction_date
        FROM payment_transactions
        WHERE payment_id = %s
        GROUP BY payment_mode
        ORDER BY transaction_date
        """,
        (payment_id,),
    )


def get_transactions_for_payment(payment_id):
    """Full list of individual transactions against one rent bill — used to spot
    and fix a wrong entry."""
    return run_query(
        """
        SELECT transaction_id, amount, payment_mode, transaction_date, remarks
        FROM payment_transactions
        WHERE payment_id = %s
        ORDER BY transaction_date DESC
        """,
        (payment_id,),
    )


def delete_payment_transaction(transaction_id, payment_id):
    """
    Deletes one wrong transaction AND recalculates the payment's amount_paid +
    status from scratch (sum of whatever transactions remain). This is safer
    than just subtracting, because subtracting can drift if something else
    changed in between.
    """
    run_write("DELETE FROM payment_transactions WHERE transaction_id = %s", (transaction_id,))
    _recalculate_payment_status(payment_id)


def update_payment_transaction(transaction_id, payment_id, new_amount, new_mode, new_remarks=""):
    """Corrects a wrong amount/mode on an existing transaction instead of delete+re-add."""
    run_write(
        "UPDATE payment_transactions SET amount = %s, payment_mode = %s, remarks = %s "
        "WHERE transaction_id = %s",
        (new_amount, new_mode, new_remarks, transaction_id),
    )
    _recalculate_payment_status(payment_id)


def _recalculate_payment_status(payment_id):
    row = run_query(
        "SELECT total_amount FROM payments WHERE payment_id = %s", (payment_id,)
    )[0]
    total = float(row["total_amount"])

    sum_row = run_query(
        "SELECT COALESCE(SUM(amount),0) AS total_paid FROM payment_transactions WHERE payment_id = %s",
        (payment_id,),
    )[0]
    new_paid = float(sum_row["total_paid"])

    new_status = "Paid" if new_paid >= total else ("Partial" if new_paid > 0 else "Pending")
    run_write(
        "UPDATE payments SET amount_paid = %s, payment_status = %s WHERE payment_id = %s",
        (new_paid, new_status, payment_id),
    )


def get_payment_id_for_student_room(billing_month=None):
    """All payments this month (paid, partial, pending) — for the 'fix entry' selector,
    unlike get_students_for_payment() which only shows unpaid ones."""
    billing_month = billing_month or current_month_str()
    return run_query(
        """
        SELECT p.payment_id, s.full_name, r.room_number, p.total_amount,
               p.amount_paid, p.payment_status
        FROM payments p
        JOIN admissions a ON a.admission_id = p.admission_id
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        WHERE p.billing_month = %s
        ORDER BY s.full_name
        """,
        (billing_month,),
    )


def get_students_for_payment(billing_month=None):
    """For the 'record payment' dropdown — students with a pending/partial bill."""
    billing_month = billing_month or current_month_str()
    return run_query(
        """
        SELECT p.payment_id, s.full_name, r.room_number,
               p.total_amount, p.amount_paid, p.payment_status
        FROM payments p
        JOIN admissions a ON a.admission_id = p.admission_id
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        WHERE p.billing_month = %s AND p.payment_status != 'Paid'
        ORDER BY s.full_name
        """,
        (billing_month,),
    )


# ---------------------------------------------------------------
# SECURITY DEPOSIT (separate from monthly rent — one-time amount,
# can also be paid in a cash+UPI split, tracked the same way as rent)
# ---------------------------------------------------------------
def get_pending_deposits():
    """Students whose security deposit isn't fully collected yet."""
    return run_query(
        """
        SELECT a.admission_id, s.full_name, r.room_number,
               v.deposit_expected, v.deposit_collected, v.deposit_due
        FROM v_deposit_status v
        JOIN admissions a ON a.admission_id = v.admission_id
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        WHERE v.deposit_due > 0
        ORDER BY s.full_name
        """
    )


def record_split_deposit(admission_id, splits):
    """
    Records security deposit paid across multiple modes in one go —
    same idea as record_split_payment but for the one-time deposit.
    splits = [{"amount": 3000, "mode": "Cash", "remarks": ""},
              {"amount": 1500, "mode": "UPI", "remarks": ""}]
    """
    for s in splits:
        run_write(
            """
            INSERT INTO deposit_transactions (admission_id, amount, payment_mode, remarks)
            VALUES (%s, %s, %s, %s)
            """,
            (admission_id, s["amount"], s["mode"], s.get("remarks", "")),
        )


def get_deposit_breakdown(admission_id):
    """Shows exactly how a deposit was paid — e.g. ₹3000 Cash + ₹1500 UPI."""
    return run_query(
        """
        SELECT payment_mode, SUM(amount) AS total
        FROM deposit_transactions
        WHERE admission_id = %s
        GROUP BY payment_mode
        """,
        (admission_id,),
    )


def get_deposit_transactions(admission_id):
    return run_query(
        """
        SELECT deposit_transaction_id, amount, payment_mode, transaction_date, remarks
        FROM deposit_transactions
        WHERE admission_id = %s
        ORDER BY transaction_date DESC
        """,
        (admission_id,),
    )


def delete_deposit_transaction(deposit_transaction_id):
    """No recalculation needed here since deposit total is read live from
    v_deposit_status (SUM of remaining rows) — deleting is enough."""
    run_write(
        "DELETE FROM deposit_transactions WHERE deposit_transaction_id = %s",
        (deposit_transaction_id,),
    )


def update_deposit_transaction(deposit_transaction_id, new_amount, new_mode, new_remarks=""):
    run_write(
        "UPDATE deposit_transactions SET amount = %s, payment_mode = %s, remarks = %s "
        "WHERE deposit_transaction_id = %s",
        (new_amount, new_mode, new_remarks, deposit_transaction_id),
    )


def get_all_admissions_with_deposit():
    """All students (not just pending) — for the deposit 'fix entry' selector."""
    return run_query(
        """
        SELECT a.admission_id, s.full_name, r.room_number, v.deposit_expected,
               v.deposit_collected, v.deposit_due
        FROM v_deposit_status v
        JOIN admissions a ON a.admission_id = v.admission_id
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        ORDER BY s.full_name
        """
    )


# ---------------------------------------------------------------
# CHECKOUT / REMOVE STUDENT  (ends admission, frees the bed,
# settles + refunds the security deposit)
# ---------------------------------------------------------------
def get_active_students_for_checkout():
    """Active students with their room + how much deposit they've actually
    paid so far (this is the max that can be refunded)."""
    return run_query(
        """
        SELECT a.admission_id, s.student_id, s.full_name, r.room_id, r.room_number,
               a.monthly_rent, v.deposit_collected
        FROM admissions a
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN room_allocations ra ON ra.admission_id = a.admission_id AND ra.is_current = 1
        LEFT JOIN rooms r ON r.room_id = ra.room_id
        LEFT JOIN v_deposit_status v ON v.admission_id = a.admission_id
        WHERE a.status = 'Active'
        ORDER BY s.full_name
        """
    )


def get_outstanding_rent_for_admission(admission_id):
    """Any unpaid rent bills for this student — owner should see this before
    refunding the deposit, in case they want to deduct it."""
    return run_query(
        """
        SELECT billing_month, total_amount, amount_paid,
               (total_amount - amount_paid) AS balance, payment_status
        FROM payments
        WHERE admission_id = %s AND payment_status != 'Paid'
        ORDER BY billing_month
        """,
        (admission_id,),
    )


# ---------------------------------------------------------------
# MONTHLY BILL GENERATION
# (there is no cron/scheduler here — Streamlit only runs code when
#  someone opens the app, so the owner has to trigger this once at the
#  start of each month. This is what creates next month's rent bill for
#  every active student — without it, payments simply never appear.)
# ---------------------------------------------------------------
def generate_bills_for_month(billing_month=None):
    """
    Creates a 'Pending' payments row for every ACTIVE admission for the
    given month, skipping any admission that already has a bill for that
    month (so it's safe to click multiple times — no duplicates).
    Returns how many new bills were created.
    """
    billing_month = billing_month or current_month_str()
    active_admissions = run_query(
        "SELECT admission_id, monthly_rent FROM admissions WHERE status = 'Active'"
    )

    created = 0
    for a in active_admissions:
        existing = run_query(
            "SELECT payment_id FROM payments WHERE admission_id = %s AND billing_month = %s",
            (a["admission_id"], billing_month),
        )
        if not existing:
            run_write(
                """
                INSERT INTO payments (admission_id, billing_month, rent_amount, total_amount, payment_status)
                VALUES (%s, %s, %s, %s, 'Pending')
                """,
                (a["admission_id"], billing_month, a["monthly_rent"], a["monthly_rent"]),
            )
            created += 1
    return created


def get_missing_bill_months(admission_id):
    """
    For a specific student: lists every month between their joining_date
    and today that DOESN'T have a bill yet — used to backfill history for
    students who joined months ago but only ever got their first bill.
    """
    row = run_query(
        "SELECT joining_date FROM admissions WHERE admission_id = %s", (admission_id,)
    )[0]
    joining = row["joining_date"]

    existing = run_query(
        "SELECT billing_month FROM payments WHERE admission_id = %s", (admission_id,)
    )
    existing_months = {str(e["billing_month"])[:7] for e in existing}

    months = []
    cursor_date = date(joining.year, joining.month, 1)
    today_month = date(date.today().year, date.today().month, 1)
    while cursor_date <= today_month:
        key = cursor_date.strftime("%Y-%m")
        if key not in existing_months:
            months.append(cursor_date)
        if cursor_date.month == 12:
            cursor_date = date(cursor_date.year + 1, 1, 1)
        else:
            cursor_date = date(cursor_date.year, cursor_date.month + 1, 1)
    return months


def backfill_bills_for_admission(admission_id, monthly_rent):
    """Creates 'Pending' bills for every missing past month for one student."""
    missing = get_missing_bill_months(admission_id)
    for m in missing:
        run_write(
            """
            INSERT INTO payments (admission_id, billing_month, rent_amount, total_amount, payment_status)
            VALUES (%s, %s, %s, %s, 'Pending')
            """,
            (admission_id, m, monthly_rent, monthly_rent),
        )
    return len(missing)


def checkout_student(admission_id, room_id, checkout_date, checkout_reason,
                      deposit_collected, deductions, remarks=""):
    """
    Full checkout flow:
      1. Mark the admission as 'Checked Out'
      2. Free up the bed (room_allocations.is_current = 0, end_date set)
      3. Create a deposit_settlement row with refund_amount =
         deposit_collected - sum(deductions)
      4. Log each deduction reason separately (mess due, damage, etc.)

    deductions = [{"reason": "Room damage", "amount": 500}, ...]
    """
    total_deduction = sum(float(d["amount"]) for d in deductions)
    refund_amount = float(deposit_collected) - total_deduction

    # 1. Close the admission
    run_write(
        """
        UPDATE admissions
        SET status = 'Checked Out', checkout_date = %s, checkout_reason = %s, remarks = %s
        WHERE admission_id = %s
        """,
        (checkout_date, checkout_reason, remarks, admission_id),
    )

    # 2. Free the bed
    run_write(
        """
        UPDATE room_allocations
        SET is_current = 0, end_date = %s
        WHERE admission_id = %s AND room_id = %s AND is_current = 1
        """,
        (checkout_date, admission_id, room_id),
    )

    # 3. Settle the deposit
    settlement_id = run_write(
        """
        INSERT INTO deposit_settlements
            (admission_id, deposit_amount, total_deduction, refund_amount, settlement_date, remarks)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (admission_id, deposit_collected, total_deduction, refund_amount, checkout_date, remarks),
    )

    # 4. Log each deduction line item
    for d in deductions:
        run_write(
            """
            INSERT INTO deposit_deductions (settlement_id, deduction_reason, deduction_amount)
            VALUES (%s, %s, %s)
            """,
            (settlement_id, d["reason"], d["amount"]),
        )

    return refund_amount


def get_checked_out_students():
    """History of everyone who has left — with their final settlement."""
    return run_query(
        """
        SELECT s.full_name, a.admission_id, a.joining_date, a.checkout_date,
               a.checkout_reason, ds.deposit_amount, ds.total_deduction, ds.refund_amount
        FROM admissions a
        JOIN students s ON s.student_id = a.student_id
        LEFT JOIN deposit_settlements ds ON ds.admission_id = a.admission_id
        WHERE a.status = 'Checked Out'
        ORDER BY a.checkout_date DESC
        """
    )


def get_deductions_for_settlement(admission_id):
    return run_query(
        """
        SELECT dd.deduction_reason, dd.deduction_amount
        FROM deposit_deductions dd
        JOIN deposit_settlements ds ON ds.settlement_id = dd.settlement_id
        WHERE ds.admission_id = %s
        """,
        (admission_id,),
    )


# ---------------------------------------------------------------
# COMPLAINTS
# ---------------------------------------------------------------
def get_complaints(status=None):
    if status:
        return run_query(
            """
            SELECT c.complaint_id, c.title, c.status, c.reported_at,
                   s.full_name AS student, r.room_number AS room
            FROM complaints c
            JOIN students s ON s.student_id = c.student_id
            LEFT JOIN rooms r ON r.room_id = c.room_id
            WHERE c.status = %s
            ORDER BY c.reported_at DESC
            """,
            (status,),
        )
    return run_query(
        """
        SELECT c.complaint_id, c.title, c.status, c.reported_at,
               s.full_name AS student, r.room_number AS room
        FROM complaints c
        JOIN students s ON s.student_id = c.student_id
        LEFT JOIN rooms r ON r.room_id = c.room_id
        ORDER BY c.reported_at DESC
        """
    )


def add_complaint(student_id, room_id, title, description=""):
    return run_write(
        """
        INSERT INTO complaints (student_id, room_id, title, description)
        VALUES (%s, %s, %s, %s)
        """,
        (student_id, room_id, title, description),
    )


def resolve_complaint(complaint_id):
    run_write(
        "UPDATE complaints SET status = 'Resolved', resolved_at = NOW() "
        "WHERE complaint_id = %s",
        (complaint_id,),
    )


# ---------------------------------------------------------------
# MESS MENU
# ---------------------------------------------------------------
def get_mess_menu_for_today():
    day_name = date.today().strftime("%A")
    return run_query(
        "SELECT meal_type, items FROM mess_menu WHERE day_of_week = %s "
        "ORDER BY FIELD(meal_type,'Breakfast','Lunch','Dinner')",
        (day_name,),
    )


def get_full_week_menu():
    return run_query(
        """
        SELECT day_of_week, meal_type, items FROM mess_menu
        ORDER BY FIELD(day_of_week,'Monday','Tuesday','Wednesday','Thursday',
                        'Friday','Saturday','Sunday'),
                 FIELD(meal_type,'Breakfast','Lunch','Dinner')
        """
    )


def upsert_menu_item(day_of_week, meal_type, items):
    run_write(
        """
        INSERT INTO mess_menu (day_of_week, meal_type, items)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE items = %s
        """,
        (day_of_week, meal_type, items, items),
    )
