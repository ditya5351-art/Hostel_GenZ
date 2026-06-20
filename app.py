import streamlit as st
from datetime import date
import queries as q

st.set_page_config(page_title="Hostel ERP — Owner Dashboard", page_icon="🏠", layout="wide")

# ---------------------------------------------------------------
# THEME (same palette as the design mock)
# ---------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

:root{
    --paper:#F3EEE3; --paper-deep:#EAE2D2; --ink:#232017; --ink-soft:#5B564A;
    --teal:#2C4A52; --teal-deep:#1E363D; --brass:#C08829; --brass-soft:#E8D2A0;
    --green:#4F7A4F; --green-bg:#E4EBDE; --rust:#B14A35; --rust-bg:#F2DFD7;
    --line:#D9CFB8; --card:#FBF8F1;
}
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Force the warm-paper background everywhere, regardless of Streamlit version
   or the visitor's OS dark-mode setting (these selectors cover both old and
   new Streamlit DOM structures). */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stHeader"], .main, body {
    background-color: var(--paper) !important;
    color: var(--ink) !important;
}

section[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    background-color: var(--teal-deep) !important;
}
section[data-testid="stSidebar"] *, [data-testid="stSidebarContent"] * {
    color: #EFE9DA !important;
}

h1, h2, h3, h4, p, span, label, div { color: var(--ink); }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #EFE9DA !important; }
h1, h2, h3 { font-family: 'Fraunces', serif !important; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* Native widgets: buttons, inputs, selects, dataframes — make them match
   the warm palette instead of following the browser's dark/light mode. */
.stButton button, .stDownloadButton button {
    background-color: var(--card) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
}
.stButton button[kind="primary"], .stButton button[data-testid="baseButton-primary"] {
    background-color: var(--teal) !important;
    color: #FBF8F1 !important;
    border-color: var(--teal) !important;
}
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stDateInput input, div[data-baseweb="select"] > div {
    background-color: var(--card) !important;
    color: var(--ink) !important;
    border-color: var(--line) !important;
}
[data-testid="stDataFrame"] { background-color: var(--card) !important; }
.stTabs [data-baseweb="tab-list"] { background-color: transparent; }
.stTabs [data-baseweb="tab"] { color: var(--ink-soft); }
.stTabs [aria-selected="true"] { color: var(--teal) !important; font-weight: 600; }
hr { border-color: var(--line) !important; }

.stat-card{ background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    padding: 16px 18px; box-shadow: 0 1px 2px rgba(35,32,23,0.06), 0 4px 16px rgba(35,32,23,0.05); }
.stat-label{ font-size: 11.5px; text-transform: uppercase; letter-spacing: .06em; color: var(--ink-soft); font-weight: 600; }
.stat-value{ font-family:'Fraunces', serif; font-size: 30px; font-weight: 700; margin-top: 6px; color: var(--ink); }
.stat-sub{ font-size: 12px; margin-top: 6px; color: var(--ink-soft); }
.stat-sub.up{ color: var(--green); } .stat-sub.down{ color: var(--rust); }
.bar-track{ height:6px; border-radius:4px; background: var(--paper-deep); margin-top:8px; overflow:hidden; }
.bar-fill{ height:100%; border-radius:4px; background: var(--brass); }

.tag{ position:relative; background: var(--paper); border: 1px solid var(--line); border-radius: 8px;
    padding: 10px 6px 8px; text-align:center; margin-bottom: 10px; }
.tag.vacant{ background: repeating-linear-gradient(135deg, var(--paper), var(--paper) 6px, var(--paper-deep) 6px, var(--paper-deep) 7px); }
.tag .room-no{ font-family:'JetBrains Mono'; font-size: 14px; font-weight:700; color: var(--ink); }
.tag .room-init{ font-size: 10.5px; color: var(--ink-soft); margin-top:2px; }
.tag .dot{ position:absolute; top:6px; right:7px; width:7px; height:7px; border-radius:50%; }

.chip{ display:inline-flex; align-items:center; gap:5px; font-size:12px; font-weight:600; padding:3px 10px; border-radius:20px; }
.chip.paid{ background: var(--green-bg); color: var(--green); }
.chip.due, .chip.pending{ background: var(--rust-bg); color: var(--rust); }
.chip.partial{ background: var(--brass-soft); color: #7A5A14; }
</style>
""", unsafe_allow_html=True)

DOT = {"Paid": "#4F7A4F", "Partial": "#C08829", "Pending": "#B14A35"}
CHIP_CLASS = {"Paid": "paid", "Partial": "partial", "Pending": "due"}
CHIP_LABEL = {"Paid": "● Paid", "Partial": "◐ Partial", "Pending": "● Due"}

# ---------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏠 Hostel ERP")
    st.caption("Owner Dashboard")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "🛏️ Rooms", "👥 Students", "💰 Rent Collection",
         "🛠️ Complaints", "🍽️ Mess Menu"],
        label_visibility="collapsed",
    )

# =================================================================
# DASHBOARD
# =================================================================
if page == "📊 Dashboard":
    st.title("🏠 Hostel Dashboard")
    st.caption(date.today().strftime("%A, %d %B %Y"))

    capacity = q.get_room_capacity()
    occupied = q.get_occupied_beds()
    vacant = capacity - occupied
    occ_pct = round((occupied / capacity) * 100) if capacity else 0

    collected = q.get_rent_collected()
    expected = q.get_rent_expected()
    pending_amt = q.get_pending_amount()
    pending_n = q.get_pending_count()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
          <div class="stat-label">Occupancy</div>
          <div class="stat-value">{occupied} <span style="font-size:14px;color:var(--ink-soft);">/ {capacity} beds</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:{occ_pct}%"></div></div>
          <div class="stat-sub">{vacant} bed(s) vacant</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        pct = round((collected / expected) * 100) if expected else 0
        st.markdown(f"""
        <div class="stat-card">
          <div class="stat-label">Rent Collected · This Month</div>
          <div class="stat-value">₹{collected:,.0f}</div>
          <div class="stat-sub up">↑ {pct}% of ₹{expected:,.0f} expected</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
          <div class="stat-label">Rent Due · This Month</div>
          <div class="stat-value">₹{pending_amt:,.0f}</div>
          <div class="stat-sub down">{pending_n} student(s) pending</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card">
          <div class="stat-label">Active Students</div>
          <div class="stat-value">{q.get_active_students()}</div>
          <div class="stat-sub">of {q.get_total_students()} total ever admitted</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Room-wise Status")
        st.caption("🟢 Paid  ·  🟡 Partial  ·  🔴 Due  ·  ⚪ Vacant bed")
        grid = q.get_room_status_grid()
        cols = st.columns(6)
        for i, r in enumerate(grid):
            with cols[i % 6]:
                vacant_cls = "vacant" if not r["full_name"] else ""
                if r["full_name"]:
                    color = DOT.get(r["payment_status"] or "Pending", "#BDB6A2")
                    dot_html = f'<div class="dot" style="background:{color}"></div>'
                    name = r["full_name"]
                else:
                    dot_html = ""
                    name = "Vacant bed"
                st.markdown(f"""
                <div class="tag {vacant_cls}">
                  {dot_html}
                  <div class="room-no">{r['room_number']}</div>
                  <div class="room-init">{name}</div>
                </div>""", unsafe_allow_html=True)
        if not grid:
            st.info("Koi room add nahi hua abhi — 'Rooms' tab se room add karo.")

    with right:
        st.subheader("Recent Payments")
        recent = q.get_recent_payments(6)
        if not recent:
            st.caption("Abhi koi payment record nahi hua.")
        for p in recent:
            c_a, c_b = st.columns([3, 1.2])
            with c_a:
                st.markdown(
                    f"**{p['student']}**  \n<span style='font-size:12px;color:var(--ink-soft)'>"
                    f"Room {p['room'] or '—'} · {p['payment_mode']}</span>",
                    unsafe_allow_html=True,
                )
            with c_b:
                st.markdown(
                    f"<div class='mono' style='text-align:right;padding-top:8px;'>₹{p['amount']:,.0f}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("<hr style='margin:2px 0;border-color:var(--line);'>", unsafe_allow_html=True)

    st.write("")
    st.subheader("This Month's Rent Ledger")
    ledger = q.get_rent_ledger()
    if ledger:
        header_cols = st.columns([2, 1, 1, 1, 1.2])
        for c, label in zip(header_cols, ["Student", "Room", "Total Rent", "Paid", "Status"]):
            c.markdown(f"<span style='font-size:11px;text-transform:uppercase;color:var(--ink-soft);font-weight:600;'>{label}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0;border-color:var(--line);'>", unsafe_allow_html=True)
        for row in ledger:
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1.2])
            c1.write(row["student"])
            c2.markdown(f"<span class='mono'>{row['room'] or '—'}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span class='mono'>₹{row['total_amount']:,.0f}</span>", unsafe_allow_html=True)
            c4.markdown(f"<span class='mono'>₹{row['amount_paid']:,.0f}</span>", unsafe_allow_html=True)
            status = row["payment_status"]
            c5.markdown(f"<span class='chip {CHIP_CLASS[status]}'>{CHIP_LABEL[status]}</span>", unsafe_allow_html=True)
    else:
        st.info("Is mahine ka koi bill abhi generate nahi hua.")

    st.write("")
    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("🛠️ Open Complaints")
        open_complaints = q.get_complaints(status="Open")
        if not open_complaints:
            st.caption("Koi open complaint nahi hai 🎉")
        for c in open_complaints[:5]:
            st.markdown(f"🔴 **{c['title']}**  \n<span style='font-size:12px;color:var(--ink-soft)'>{c['student']} · Room {c['room'] or '—'}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0;border-color:var(--line);'>", unsafe_allow_html=True)

    with c_right:
        st.subheader("🍽️ Today's Mess Menu")
        menu = q.get_mess_menu_for_today()
        if menu:
            for m in menu:
                st.markdown(f"**{m['meal_type']}** — {m['items']}")
        else:
            st.caption("Aaj ka menu set nahi hai. 'Mess Menu' tab se add karo.")

# =================================================================
# ROOMS
# =================================================================
elif page == "🛏️ Rooms":
    st.title("🛏️ Rooms")
    tab1, tab2, tab3 = st.tabs(["📋 All Rooms", "➕ Add Room", "✏️ Edit / Delete Room"])

    with tab1:
        rooms = q.get_room_occupancy_summary()
        if rooms:
            st.dataframe(rooms, use_container_width=True, hide_index=True)
        else:
            st.info("Abhi koi room add nahi hua.")

    with tab2:
        room_number = st.text_input("Room Number (e.g. R-19)")
        total_beds = st.number_input("Total Beds in this Room", min_value=1, max_value=10, value=2)
        if st.button("Add Room", type="primary"):
            if not room_number.strip():
                st.error("Room number daalo.")
            else:
                q.add_room(room_number.strip(), total_beds)
                st.success(f"Room {room_number} add ho gaya ✅")
                st.rerun()

    with tab3:
        all_rooms = q.get_all_rooms()
        if not all_rooms:
            st.info("Pehle ek room add karo.")
        else:
            room_map = {r["room_number"]: r for r in all_rooms}
            choice = st.selectbox("Room Select Karo", list(room_map.keys()))
            selected = room_map[choice]

            new_number = st.text_input("Room Number", value=selected["room_number"])
            new_beds = st.number_input(
                "Total Beds", min_value=1, max_value=10, value=selected["total_beds"]
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Save Changes", type="primary"):
                    try:
                        q.update_room(selected["room_id"], new_number.strip(), new_beds)
                        st.success("Room update ho gaya ✅")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            with c2:
                if st.button("🗑️ Delete Room"):
                    try:
                        q.delete_room(selected["room_id"])
                        st.success("Room delete ho gaya ✅")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

# =================================================================
# STUDENTS
# =================================================================
elif page == "👥 Students":
    st.title("👥 Students")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Add Student", "📋 View Students", "✏️ Edit Student",
        "🚪 Checkout Student", "📜 Checkout History"
    ])

    with tab1:
        st.subheader("Naya Student Admit Karo")
        full_name = st.text_input("Full Name *", key="add_full_name")
        father_name = st.text_input("Father's Name", key="add_father_name")
        mobile = st.text_input("Mobile Number *", key="add_mobile")
        course = st.text_input("Course / Branch", key="add_course")

        vacant_rooms = q.get_vacant_rooms()
        room_options = {f"{r['room_number']} ({r['beds_vacant']} bed open)": r["room_id"] for r in vacant_rooms}

        if room_options:
            room_label = st.selectbox("Assign Room *", list(room_options.keys()), key="add_room_select")
        else:
            room_label = None
            st.warning("Koi vacant bed nahi hai. Pehle 'Rooms' tab se naya room add karo, ya kisi student ko checkout karo.")

        monthly_rent = st.number_input("Monthly Rent (₹) *", min_value=0, value=4500, step=100, key="add_monthly_rent")
        security_deposit = st.number_input("Security Deposit (₹) *", min_value=0, value=4500, step=100, key="add_security_deposit")
        joining_date = st.date_input("Joining Date", value=date.today(), key="add_joining_date")

        if st.button("Add Student", type="primary"):
            if not full_name.strip() or not mobile.strip():
                st.error("Naam aur Mobile number required hain.")
            elif not room_label:
                st.error("Room assign karne ke liye pehle vacant bed banao.")
            else:
                q.add_student_with_admission(
                    full_name.strip(), father_name.strip(), mobile.strip(), course.strip(),
                    room_options[room_label], monthly_rent, security_deposit, joining_date,
                )
                st.success(f"{full_name} ko successfully admit kar diya ✅ (Room {room_label.split(' ')[0]})")
                st.rerun()

    with tab2:
        students = q.get_all_students_with_room()
        st.dataframe(students, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("✏️ Student Ki Details Edit Karo")
        search_term = st.text_input("🔍 Naam type karke search karo", placeholder="e.g. Vikram")

        if search_term.strip():
            matches = q.search_students_by_name(search_term.strip())
        else:
            matches = []

        if search_term.strip() and not matches:
            st.warning("Koi student match nahi hua.")
        elif matches:
            match_options = {f"{m['full_name']} — Room {m['room_number'] or '—'}": m["student_id"] for m in matches}
            selected_label = st.selectbox("Matching Students", list(match_options.keys()))
            student_id = match_options[selected_label]

            details = q.get_student_full_details(student_id)
            if details:
                st.markdown("---")
                st.write("**Personal Details**")
                full_name = st.text_input("Full Name", value=details["full_name"] or "")
                father_name = st.text_input("Father's Name", value=details["father_name"] or "")
                mobile = st.text_input("Mobile Number", value=details["mobile_number"] or "")
                course = st.text_input("Course / Branch", value=details["course_branch"] or "")
                email = st.text_input("Email", value=details["email_address"] or "")

                if st.button("💾 Save Personal Details", type="primary"):
                    q.update_student_details(student_id, full_name.strip(), father_name.strip(),
                                              mobile.strip(), course.strip(), email.strip())
                    st.success("Details update ho gayi ✅")
                    st.rerun()

                if details["admission_id"]:
                    st.markdown("---")
                    st.write("**Rent & Deposit** (sirf future bills par effect karega, purane bills change nahi honge)")
                    new_rent = st.number_input("Monthly Rent (₹)", min_value=0,
                                                value=int(details["monthly_rent"] or 0), step=100)
                    new_deposit = st.number_input("Security Deposit (₹)", min_value=0,
                                                   value=int(details["security_deposit"] or 0), step=100)
                    if st.button("💾 Save Rent & Deposit"):
                        q.update_admission_rent(details["admission_id"], new_rent, new_deposit)
                        st.success("Rent/Deposit update ho gaya ✅")
                        st.rerun()

                    st.markdown("---")
                    st.write(f"**Current Room:** {details['room_number'] or '—'}")
                    vacant_rooms = q.get_vacant_rooms()
                    room_choices = {r["room_number"]: r["room_id"] for r in vacant_rooms}
                    if room_choices:
                        new_room_label = st.selectbox("Naye Room mein Shift Karo", list(room_choices.keys()))
                        change_date = st.date_input("Shift Date", value=date.today(), key="shift_date")
                        if st.button("🔁 Shift Room"):
                            try:
                                q.change_student_room(details["admission_id"], details["room_id"],
                                                       room_choices[new_room_label], change_date)
                                st.success(f"Room {new_room_label} mein shift ho gaya ✅")
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))
                    else:
                        st.caption("Koi vacant room nahi hai shift karne ke liye.")
                else:
                    st.caption("Is student ka koi active admission nahi hai (already checked out ho sakta hai).")

                st.markdown("---")
                with st.expander("⚠️ Danger Zone — Student Permanently Delete Karo"):
                    st.error(
                        "Yeh action **permanent** hai. Student ki saari history "
                        "(payments, transactions, complaints, room records) bhi delete ho jayegi. "
                        "Agar student hostel chhod raha hai normally, uske liye 'Checkout Student' "
                        "tab use karo — woh history preserve karta hai aur deposit refund bhi calculate karta hai. "
                        "Yeh delete option sirf galti se add hue student ko hatane ke liye hai."
                    )
                    confirm_name = st.text_input(
                        f"Confirm karne ke liye '{details['full_name']}' type karo:",
                        key="delete_confirm_input",
                    )
                    if st.button("🗑️ Permanently Delete This Student", disabled=(confirm_name.strip() != details["full_name"])):
                        q.delete_student_completely(student_id)
                        st.success(f"{details['full_name']} permanently delete ho gaya.")
                        st.rerun()
        else:
            st.caption("Naam type karo upar search box mein.")

    with tab4:
        st.subheader("🚪 Student ko Checkout Karo")
        active = q.get_active_students_for_checkout()
        if not active:
            st.info("Koi active student nahi hai.")
        else:
            c_options = {f"{s['full_name']} — Room {s['room_number'] or '—'}": s for s in active}
            c_choice = st.selectbox("Student Select Karo", list(c_options.keys()))
            c_selected = c_options[c_choice]

            deposit_collected = float(c_selected["deposit_collected"] or 0)
            st.info(f"💰 Deposit collected so far: ₹{deposit_collected:,.0f}")

            # Show outstanding rent so the owner doesn't forget to deduct it
            outstanding = q.get_outstanding_rent_for_admission(c_selected["admission_id"])
            if outstanding:
                st.warning("⚠️ Is student ka rent pending hai:")
                for o in outstanding:
                    st.write(f"- {str(o['billing_month'])[:7]}: ₹{o['balance']:,.0f} due")

            checkout_date = st.date_input("Checkout Date", value=date.today())
            checkout_reason = st.text_input("Checkout Reason (e.g. Course completed, Personal reasons)")

            st.markdown("**Deposit se koi deduction karni hai?** (room damage, pending dues, etc.)")
            num_deductions = st.number_input("Kitni deductions add karni hain?", min_value=0, max_value=5, value=0)

            deductions = []
            total_deduction = 0.0
            for i in range(int(num_deductions)):
                c1, c2 = st.columns(2)
                with c1:
                    reason = st.text_input(f"Deduction #{i+1} Reason", key=f"deduct_reason_{i}")
                with c2:
                    amt = st.number_input(f"Deduction #{i+1} Amount (₹)", min_value=0, value=0, step=100, key=f"deduct_amt_{i}")
                if reason and amt > 0:
                    deductions.append({"reason": reason, "amount": amt})
                    total_deduction += amt

            refund_amount = deposit_collected - total_deduction
            st.markdown(f"### Refund Amount: ₹{refund_amount:,.0f}")
            if refund_amount < 0:
                st.error("Deductions deposit se zyada hain — refund negative nahi ho sakta. Check karo.")

            remarks = st.text_area("Remarks (optional)")

            if st.button("✅ Confirm Checkout & Settle Deposit", type="primary", disabled=(refund_amount < 0)):
                if not checkout_reason.strip():
                    st.error("Checkout reason daalo.")
                else:
                    q.checkout_student(
                        c_selected["admission_id"], c_selected["room_id"],
                        checkout_date, checkout_reason.strip(),
                        deposit_collected, deductions, remarks.strip(),
                    )
                    st.success(
                        f"{c_selected['full_name']} checkout ho gaya ✅ — "
                        f"Refund: ₹{refund_amount:,.0f}. Room {c_selected['room_number']} ab vacant hai."
                    )
                    st.rerun()

    with tab5:
        st.subheader("📜 Checkout History")
        history = q.get_checked_out_students()
        if history:
            st.dataframe(history, use_container_width=True, hide_index=True)
        else:
            st.info("Abhi koi student checkout nahi hua hai.")

# =================================================================
# RENT COLLECTION
# =================================================================
elif page == "💰 Rent Collection":
    st.title("💰 Rent Collection")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Record Payment", "📋 This Month's Ledger",
        "🔒 Security Deposit", "✏️ Fix Wrong Entry", "📅 Monthly Billing"
    ])

    with tab1:
        pending = q.get_students_for_payment()
        if not pending:
            st.success("Sabka rent paid hai is mahine ke liye 🎉")
        else:
            options = {
                f"{p['full_name']} — Room {p['room_number'] or '—'} (₹{p['total_amount']-p['amount_paid']:,.0f} due)": p
                for p in pending
            }
            choice = st.selectbox("Select Student", list(options.keys()))
            selected = options[choice]
            balance = float(selected["total_amount"]) - float(selected["amount_paid"])
            st.caption(f"Balance due: ₹{balance:,.0f}")

            split_payment = st.checkbox(
                "💡 Payment cash + online mix mein aaya hai (split payment)"
            )

            if not split_payment:
                amount = st.number_input("Amount Received (₹)", min_value=1, max_value=int(balance), value=int(balance), step=100)
                mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Bank Transfer"])
                remarks = st.text_input("Remarks (optional)")
                if st.button("Record Payment", type="primary"):
                    q.record_payment(selected["payment_id"], amount, mode, remarks)
                    st.success(f"₹{amount:,.0f} received from {selected['full_name']} ✅")
                    st.rerun()
            else:
                st.write("Kitne mode mein paisa aaya hai? Har mode ka amount alag daalo:")
                num_splits = st.number_input("Kitne tareeke se paisa aaya (Cash/UPI/Bank)?", min_value=2, max_value=4, value=2)

                splits = []
                running_total = 0.0
                cols_per_row = st.columns(2)
                for i in range(int(num_splits)):
                    c1, c2 = st.columns(2)
                    with c1:
                        amt = st.number_input(f"Amount #{i+1} (₹)", min_value=0, value=0, step=100, key=f"split_amt_{i}")
                    with c2:
                        mode_i = st.selectbox(f"Mode #{i+1}", ["Cash", "UPI", "Bank Transfer"], key=f"split_mode_{i}")
                    if amt > 0:
                        splits.append({"amount": amt, "mode": mode_i})
                        running_total += amt

                st.markdown(f"**Total entered: ₹{running_total:,.0f}** / Balance due: ₹{balance:,.0f}")

                if running_total > balance:
                    st.error("Total entered amount balance due se zyada hai — check karo.")
                elif st.button("Record Split Payment", type="primary", disabled=(running_total == 0)):
                    q.record_split_payment(selected["payment_id"], splits)
                    breakdown = ", ".join(f"₹{s['amount']:,.0f} {s['mode']}" for s in splits)
                    st.success(f"{selected['full_name']} se {breakdown} record ho gaya ✅")
                    st.rerun()

    with tab2:
        ledger = q.get_rent_ledger()
        st.dataframe(ledger, use_container_width=True, hide_index=True)
        st.caption("Tip: kisi student ka paid amount cash+UPI mix mein tha toh woh breakdown 'Record Payment' tab ke through dikh sakta hai (aage add kar sakte hain receipt view mein).")

    with tab3:
        st.subheader("Security Deposit Collection")
        pending_deposits = q.get_pending_deposits()
        if not pending_deposits:
            st.success("Sabka security deposit fully collected hai 🎉")
        else:
            dep_options = {
                f"{d['full_name']} — Room {d['room_number'] or '—'} (₹{d['deposit_due']:,.0f} due)": d
                for d in pending_deposits
            }
            dep_choice = st.selectbox("Select Student for Deposit", list(dep_options.keys()))
            dep_selected = dep_options[dep_choice]
            dep_balance = float(dep_selected["deposit_due"])
            st.caption(f"Deposit due: ₹{dep_balance:,.0f}")

            dep_split = st.checkbox("💡 Deposit cash + online mix mein aaya hai", key="dep_split_chk")

            if not dep_split:
                dep_amount = st.number_input("Deposit Amount Received (₹)", min_value=1, max_value=int(dep_balance), value=int(dep_balance), step=100)
                dep_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Bank Transfer"], key="dep_mode")
                if st.button("Record Deposit", type="primary"):
                    q.record_split_deposit(dep_selected["admission_id"], [{"amount": dep_amount, "mode": dep_mode}])
                    st.success(f"₹{dep_amount:,.0f} deposit received ✅")
                    st.rerun()
            else:
                num_dep_splits = st.number_input("Kitne tareeke se deposit aaya?", min_value=2, max_value=4, value=2, key="dep_num_splits")
                dep_splits = []
                dep_running_total = 0.0
                for i in range(int(num_dep_splits)):
                    c1, c2 = st.columns(2)
                    with c1:
                        amt = st.number_input(f"Deposit Amount #{i+1} (₹)", min_value=0, value=0, step=100, key=f"dep_split_amt_{i}")
                    with c2:
                        mode_i = st.selectbox(f"Mode #{i+1}", ["Cash", "UPI", "Bank Transfer"], key=f"dep_split_mode_{i}")
                    if amt > 0:
                        dep_splits.append({"amount": amt, "mode": mode_i})
                        dep_running_total += amt

                st.markdown(f"**Total entered: ₹{dep_running_total:,.0f}** / Due: ₹{dep_balance:,.0f}")
                if dep_running_total > dep_balance:
                    st.error("Total entered deposit due se zyada hai — check karo.")
                elif st.button("Record Split Deposit", type="primary", disabled=(dep_running_total == 0)):
                    q.record_split_deposit(dep_selected["admission_id"], dep_splits)
                    breakdown = ", ".join(f"₹{s['amount']:,.0f} {s['mode']}" for s in dep_splits)
                    st.success(f"Deposit record ho gaya: {breakdown} ✅")
                    st.rerun()

    with tab4:
        st.subheader("✏️ Galat Entry Theek Karo")
        fix_type = st.radio("Kis type ki entry fix karni hai?", ["Rent Payment", "Security Deposit"], horizontal=True)

        if fix_type == "Rent Payment":
            all_payments = q.get_payment_id_for_student_room()
            if not all_payments:
                st.info("Is mahine ka koi bill nahi hai.")
            else:
                p_options = {
                    f"{p['full_name']} — Room {p['room_number'] or '—'} (₹{p['amount_paid']:,.0f} / ₹{p['total_amount']:,.0f} paid)": p
                    for p in all_payments
                }
                p_choice = st.selectbox("Student Select Karo", list(p_options.keys()))
                p_selected = p_options[p_choice]

                txns = q.get_transactions_for_payment(p_selected["payment_id"])
                if not txns:
                    st.caption("Is student ka koi transaction record nahi hai abhi.")
                else:
                    st.write("**Transaction History:**")
                    for t in txns:
                        c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5])
                        c1.write(f"₹{t['amount']:,.0f}")
                        c2.write(t["payment_mode"])
                        c3.write(str(t["transaction_date"])[:16])
                        with c4:
                            if st.button("🗑️ Delete", key=f"del_txn_{t['transaction_id']}"):
                                q.delete_payment_transaction(t["transaction_id"], p_selected["payment_id"])
                                st.success("Entry delete ho gayi aur total recalculate ho gaya ✅")
                                st.rerun()

                    st.markdown("---")
                    st.write("**Ya kisi entry ko edit karo (delete + naya add karne se behtar):**")
                    edit_options = {f"₹{t['amount']:,.0f} · {t['payment_mode']} · {str(t['transaction_date'])[:16]}": t for t in txns}
                    edit_choice = st.selectbox("Edit karne wali entry choose karo", list(edit_options.keys()))
                    edit_selected = edit_options[edit_choice]

                    new_amt = st.number_input("Correct Amount (₹)", min_value=1, value=int(edit_selected["amount"]), step=100)
                    new_mode = st.selectbox("Correct Mode", ["Cash", "UPI", "Bank Transfer"],
                                             index=["Cash", "UPI", "Bank Transfer"].index(edit_selected["payment_mode"]))
                    if st.button("Save Correction", type="primary"):
                        q.update_payment_transaction(edit_selected["transaction_id"], p_selected["payment_id"], new_amt, new_mode)
                        st.success("Entry correct ho gayi aur total recalculate ho gaya ✅")
                        st.rerun()

        else:  # Security Deposit
            all_deposits = q.get_all_admissions_with_deposit()
            if not all_deposits:
                st.info("Koi deposit record nahi hai.")
            else:
                d_options = {
                    f"{d['full_name']} — Room {d['room_number'] or '—'} (₹{d['deposit_collected']:,.0f} / ₹{d['deposit_expected']:,.0f} collected)": d
                    for d in all_deposits
                }
                d_choice = st.selectbox("Student Select Karo", list(d_options.keys()), key="fix_dep_student")
                d_selected = d_options[d_choice]

                d_txns = q.get_deposit_transactions(d_selected["admission_id"])
                if not d_txns:
                    st.caption("Is student ka koi deposit transaction nahi hai abhi.")
                else:
                    st.write("**Deposit Transaction History:**")
                    for t in d_txns:
                        c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5])
                        c1.write(f"₹{t['amount']:,.0f}")
                        c2.write(t["payment_mode"])
                        c3.write(str(t["transaction_date"])[:16])
                        with c4:
                            if st.button("🗑️ Delete", key=f"del_dep_txn_{t['deposit_transaction_id']}"):
                                q.delete_deposit_transaction(t["deposit_transaction_id"])
                                st.success("Deposit entry delete ho gayi ✅")
                                st.rerun()

                    st.markdown("---")
                    edit_d_options = {f"₹{t['amount']:,.0f} · {t['payment_mode']}": t for t in d_txns}
                    edit_d_choice = st.selectbox("Edit karne wali entry choose karo", list(edit_d_options.keys()), key="edit_dep_select")
                    edit_d_selected = edit_d_options[edit_d_choice]

                    new_d_amt = st.number_input("Correct Amount (₹)", min_value=1, value=int(edit_d_selected["amount"]), step=100, key="new_dep_amt")
                    new_d_mode = st.selectbox("Correct Mode", ["Cash", "UPI", "Bank Transfer"],
                                               index=["Cash", "UPI", "Bank Transfer"].index(edit_d_selected["payment_mode"]),
                                               key="new_dep_mode")
                    if st.button("Save Correction", type="primary", key="save_dep_correction"):
                        q.update_deposit_transaction(edit_d_selected["deposit_transaction_id"], new_d_amt, new_d_mode)
                        st.success("Deposit entry correct ho gayi ✅")
                        st.rerun()

    with tab5:
        st.subheader("📅 Monthly Bill Generation")
        st.caption(
            "Streamlit mein koi automatic scheduler nahi hai — naye mahine ka rent bill "
            "khud-ba-khud nahi banta. Har mahine ki shuruaat mein yeh button ek baar click karo."
        )

        if st.button(f"🧾 Generate {date.today().strftime('%B %Y')} ka Bill — Sab Active Students Ke Liye", type="primary"):
            count = q.generate_bills_for_month()
            if count > 0:
                st.success(f"{count} naye bills bana diye gaye ✅")
            else:
                st.info("Sabka is mahine ka bill already ban chuka hai — koi naya bill banane ki zarurat nahi thi.")
            st.rerun()

        st.markdown("---")
        st.subheader("🔁 Backfill Missing Past Bills (kisi specific student ke liye)")
        st.caption(
            "Agar koi student mahino pehle admit hua tha lekin sirf pehle mahine ka bill bana, "
            "yahan se uske saare missing mahino ke bills ek saath bana sakte ho."
        )
        all_active = q.get_active_students_for_checkout()
        if all_active:
            b_options = {f"{s['full_name']} — Room {s['room_number'] or '—'}": s for s in all_active}
            b_choice = st.selectbox("Student Select Karo", list(b_options.keys()), key="backfill_select")
            b_selected = b_options[b_choice]

            missing = q.get_missing_bill_months(b_selected["admission_id"])
            if not missing:
                st.success("Is student ke koi missing bills nahi hain — sab up-to-date hai ✅")
            else:
                month_names = ", ".join(m.strftime("%B %Y") for m in missing)
                st.warning(f"Missing bills: {month_names}")
                if st.button(f"🧾 Generate {len(missing)} Missing Bill(s)", type="primary"):
                    n = q.backfill_bills_for_admission(b_selected["admission_id"], b_selected["monthly_rent"])
                    st.success(f"{n} bill(s) generate ho gaye ✅")
                    st.rerun()
        else:
            st.info("Koi active student nahi hai.")


# =================================================================
# COMPLAINTS
# =================================================================
elif page == "🛠️ Complaints":
    st.title("🛠️ Complaints & Maintenance")
    tab1, tab2 = st.tabs(["📋 All Complaints", "➕ Log Complaint"])

    with tab1:
        status_filter = st.radio("Filter", ["All", "Open", "In Progress", "Resolved"], horizontal=True)
        complaints = q.get_complaints(status=None if status_filter == "All" else status_filter)
        for c in complaints:
            icon = "🟢" if c["status"] == "Resolved" else "🔴"
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"{icon} **{c['title']}**  \n<span style='font-size:12px;color:var(--ink-soft)'>{c['student']} · Room {c['room'] or '—'} · {c['status']}</span>", unsafe_allow_html=True)
            with col2:
                if c["status"] != "Resolved":
                    if st.button("Mark Resolved", key=f"resolve_{c['complaint_id']}"):
                        q.resolve_complaint(c["complaint_id"])
                        st.rerun()
            st.markdown("<hr style='margin:4px 0;border-color:var(--line);'>", unsafe_allow_html=True)

    with tab2:
        students = q.get_all_students_with_room()
        student_options = {f"{s['full_name']} (Room {s['room_number'] or '—'})": s for s in students}
        if student_options:
            choice = st.selectbox("Student", list(student_options.keys()))
            title = st.text_input("Complaint Title (e.g. Geyser not working)")
            desc = st.text_area("Details (optional)")
            if st.button("Submit Complaint", type="primary"):
                if not title.strip():
                    st.error("Complaint ka title daalo.")
                else:
                    s = student_options[choice]
                    room_id = None
                    rooms = q.get_all_rooms()
                    for r in rooms:
                        if r["room_number"] == s["room_number"]:
                            room_id = r["room_id"]
                            break
                    q.add_complaint(s["student_id"], room_id, title.strip(), desc.strip())
                    st.success("Complaint log ho gayi ✅")
                    st.rerun()
        else:
            st.info("Pehle student add karo.")

# =================================================================
# MESS MENU
# =================================================================
elif page == "🍽️ Mess Menu":
    st.title("🍽️ Mess Menu")
    tab1, tab2 = st.tabs(["📅 Full Week", "✏️ Edit Menu"])

    with tab1:
        menu = q.get_full_week_menu()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            st.markdown(f"**{day}**")
            day_items = [m for m in menu if m["day_of_week"] == day]
            if day_items:
                for m in day_items:
                    st.markdown(f"&nbsp;&nbsp;• {m['meal_type']}: {m['items']}")
            else:
                st.caption("&nbsp;&nbsp;Not set")
            st.write("")

    with tab2:
        day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        meal = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner"])
        items = st.text_input("Items (comma separated)")
        if st.button("Save Menu", type="primary"):
            if items.strip():
                q.upsert_menu_item(day, meal, items.strip())
                st.success(f"{day} {meal} menu update ho gaya ✅")
                st.rerun()
            else:
                st.error("Items daalo.")