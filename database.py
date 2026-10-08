import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campusfix.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create issues table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            department TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium',
            status TEXT NOT NULL DEFAULT 'Submitted',
            reporter_name TEXT NOT NULL,
            reporter_role TEXT NOT NULL DEFAULT 'Student',
            reporter_email TEXT DEFAULT '',
            assigned_to TEXT DEFAULT 'Unassigned',
            resolution_notes TEXT DEFAULT '',
            upvotes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create timeline_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            notes TEXT DEFAULT '',
            updated_by TEXT DEFAULT 'System',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issues (id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM issues")
    count = cursor.fetchone()[0]

    if count == 0:
        seed_data = [
            (
                "CF-1001",
                "Main Library 2nd Floor AC Leaking Water",
                "Water is continuously dripping onto student study desks near bookshelf 14. Creating slippery hazard.",
                "Central Library, 2nd Floor Study Wing",
                "Facilities & Maintenance",
                "High",
                "In Progress",
                "Prof. Sarah Jenkins",
                "Lecturer",
                "sjenkins@campus.edu",
                "Mark Peterson (Facilities)",
                "Maintenance technician arrived. Drain line cleared, verifying compressor condensation.",
                12,
                "2026-10-07 09:30:00",
                "2026-10-08 11:15:00"
            ),
            (
                "CF-1002",
                "CS Lab 3 Projector HDMI Wall Plate Broken",
                "The wall-mounted HDMI connector is loose and pins are bent. Lectures cannot project slides.",
                "Turing Block, Lab 302",
                "IT Support",
                "Medium",
                "Assigned",
                "Aditya Verma",
                "Student",
                "aditya.v@student.campus.edu",
                "Alex Chen (AV Systems)",
                "AV team dispatched with replacement wall faceplate and testing monitor.",
                7,
                "2026-10-07 14:15:00",
                "2026-10-08 09:00:00"
            ),
            (
                "CF-1003",
                "Block B Girls Hostel Water Purifier Dispenser Jammed",
                "The RO water dispenser on the 1st floor common area is showing an error code and not dispensing drinking water.",
                "Hostel Block B, 1st Floor Lounge",
                "Sanitation & Hygiene",
                "Urgent",
                "Submitted",
                "Priya Sharma",
                "Student",
                "priya.s@student.campus.edu",
                "Unassigned",
                "",
                21,
                "2026-10-08 08:20:00",
                "2026-10-08 08:20:00"
            ),
            (
                "CF-1004",
                "Chemistry Annex Emergency Exit Door Stuck",
                "The emergency exit push bar on the rear stairwell is jammed shut. Safety hazard in case of evacuation.",
                "Science Complex, Chemistry Annex Ground Floor",
                "Campus Security",
                "Urgent",
                "Submitted",
                "Dr. Robert Lang",
                "Lecturer",
                "rlang@campus.edu",
                "Unassigned",
                "",
                18,
                "2026-10-08 10:45:00",
                "2026-10-08 10:45:00"
            ),
            (
                "CF-1005",
                "Auditorium Main Quadrangle Streetlights Flickering",
                "Three LED streetlights along the walkway between Auditorium and Cafeteria are strobe flickering at night.",
                "Main Quadrangle, East Walkway",
                "Electrical Services",
                "Low",
                "Resolved",
                "Campus Environmental Club",
                "Student",
                "green.club@student.campus.edu",
                "David Ramos (Chief Electrician)",
                "Replaced faulty surge suppressors and LED drivers. Circuit tested and stable.",
                5,
                "2026-10-06 18:00:00",
                "2026-10-07 16:30:00"
            )
        ]

        for item in seed_data:
            cursor.execute("""
                INSERT INTO issues (
                    ticket_code, title, description, location, department,
                    priority, status, reporter_name, reporter_role, reporter_email,
                    assigned_to, resolution_notes, upvotes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, item)
            issue_id = cursor.lastrowid

            # Add timeline logs according to status
            ticket_code, title, desc, loc, dept, prio, status, rep_name, rep_role, rep_mail, assigned, notes, upvotes, c_at, u_at = item

            # 1. Submitted log
            cursor.execute("""
                INSERT INTO timeline_logs (issue_id, status, notes, updated_by, created_at)
                VALUES (?, 'Submitted', ?, ?, ?)
            """, (issue_id, f"Report logged by {rep_name} ({rep_role})", rep_name, c_at))

            # 2. Assigned log if applicable
            if status in ["Assigned", "In Progress", "Resolved"]:
                cursor.execute("""
                    INSERT INTO timeline_logs (issue_id, status, notes, updated_by, created_at)
                    VALUES (?, 'Assigned', ?, 'Department Admin', ?)
                """, (issue_id, f"Ticket routed to {dept} department. Assigned staff: {assigned}", u_at))

            # 3. In Progress log if applicable
            if status in ["In Progress", "Resolved"]:
                cursor.execute("""
                    INSERT INTO timeline_logs (issue_id, status, notes, updated_by, created_at)
                    VALUES (?, 'In Progress', ?, ?, ?)
                """, (issue_id, notes if status == 'In Progress' else "Work commenced on site.", assigned, u_at))

            # 4. Resolved log if applicable
            if status == "Resolved":
                cursor.execute("""
                    INSERT INTO timeline_logs (issue_id, status, notes, updated_by, created_at)
                    VALUES (?, 'Resolved', ?, ?, ?)
                """, (issue_id, f"Issue resolved: {notes}", assigned, u_at))

        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with sample data!")
