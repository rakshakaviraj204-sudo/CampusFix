from flask import Flask, render_template, request, jsonify
from database import get_db_connection, init_db
from ai_classifier import classify_issue
import datetime

app = Flask(__name__)

DEPARTMENTS = [
    "Facilities & Maintenance",
    "IT Support",
    "Electrical Services",
    "Sanitation & Hygiene",
    "Campus Security",
    "Hostel Administration"
]

STATUS_ORDER = ["Submitted", "Assigned", "In Progress", "Resolved"]

@app.route("/")
def index():
    return render_template("index.html", departments=DEPARTMENTS)

@app.route("/department")
def department_portal():
    dept = request.args.get("dept", DEPARTMENTS[0])
    return render_template("department.html", departments=DEPARTMENTS, selected_dept=dept)

# --- API ENDPOINTS ---

@app.route("/api/classify", methods=["POST"])
def classify():
    data = request.json or {}
    description = data.get("description", "").strip()
    title = data.get("title", "").strip()

    if not description and not title:
        return jsonify({"error": "Please provide a description or title to analyze"}), 400

    result = classify_issue(description, title)
    return jsonify({"success": True, **result})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM issues")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM issues WHERE status = 'Resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM issues WHERE status IN ('Submitted', 'Assigned', 'In Progress')")
    in_progress = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM issues WHERE priority = 'Urgent' AND status != 'Resolved'")
    urgent = cursor.fetchone()[0]

    # Department breakdown
    cursor.execute("SELECT department, COUNT(*) as count FROM issues GROUP BY department")
    dept_counts = {row["department"]: row["count"] for row in cursor.fetchall()}

    conn.close()
    return jsonify({
        "total": total,
        "resolved": resolved,
        "active": in_progress,
        "urgent": urgent,
        "department_counts": dept_counts
    })

@app.route("/api/issues", methods=["GET"])
def list_issues():
    department = request.args.get("department")
    status = request.args.get("status")
    search = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM issues WHERE 1=1"
    params = []

    if department and department != "All":
        query += " AND department = ?"
        params.append(department)

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ? OR ticket_code LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    query += " ORDER BY CASE priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, created_at DESC"

    cursor.execute(query, params)
    issues = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(issues)

@app.route("/api/issues/<int:issue_id>", methods=["GET"])
def get_issue(issue_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
    issue = cursor.fetchone()

    if not issue:
        conn.close()
        return jsonify({"error": "Issue not found"}), 404

    cursor.execute("SELECT * FROM timeline_logs WHERE issue_id = ? ORDER BY created_at ASC", (issue_id,))
    logs = [dict(row) for row in cursor.fetchall()]

    issue_data = dict(issue)
    issue_data["timeline"] = logs
    conn.close()

    return jsonify(issue_data)

@app.route("/api/issues", methods=["POST"])
def create_issue():
    data = request.json or request.form
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    location = data.get("location", "").strip()
    department = data.get("department", "").strip()
    priority = data.get("priority", "Medium").strip()
    reporter_name = data.get("reporter_name", "Anonymous").strip()
    reporter_role = data.get("reporter_role", "Student").strip()
    reporter_email = data.get("reporter_email", "").strip()

    if not title or not description or not location or not department:
        return jsonify({"error": "Please provide title, description, location, and department"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(id) FROM issues")
    max_id = cursor.fetchone()[0] or 1000
    ticket_code = f"CF-{max_id + 1}"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO issues (
            ticket_code, title, description, location, department,
            priority, status, reporter_name, reporter_role, reporter_email,
            assigned_to, resolution_notes, upvotes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'Submitted', ?, ?, ?, 'Unassigned', '', 1, ?, ?)
    """, (ticket_code, title, description, location, department, priority, reporter_name, reporter_role, reporter_email, now, now))

    issue_id = cursor.lastrowid

    # Create initial timeline log
    cursor.execute("""
        INSERT INTO timeline_logs (issue_id, status, notes, updated_by, created_at)
        VALUES (?, 'Submitted', ?, ?, ?)
    """, (issue_id, f"Report filed by {reporter_name} ({reporter_role})", reporter_name, now))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": issue_id, "ticket_code": ticket_code}), 201

@app.route("/api/issues/<int:issue_id>/status", methods=["POST"])
def update_status(issue_id):
    data = request.json or {}
    new_status = data.get("status")
    assigned_to = data.get("assigned_to")
    notes = data.get("notes", "").strip()
    updated_by = data.get("updated_by", "Department Staff")

    if new_status not in STATUS_ORDER:
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        return jsonify({"error": "Issue not found"}), 404

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    current_assigned = assigned_to if assigned_to is not None else issue["assigned_to"]
    current_notes = notes if notes else issue["resolution_notes"]

    cursor.execute("""
        UPDATE issues
        SET status = ?, assigned_to = ?, resolution_notes = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, current_assigned, current_notes, now, issue_id))

    # Add log entry
    log_note = notes if notes else f"Status transitioned to '{new_status}'"
    cursor.execute("""
        INSERT INTO timeline_logs (issue_id, status, notes, updated_by, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (issue_id, new_status, log_note, updated_by, now))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "status": new_status, "assigned_to": current_assigned})

@app.route("/api/issues/<int:issue_id>/upvote", methods=["POST"])
def upvote_issue(issue_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE issues SET upvotes = upvotes + 1 WHERE id = ?", (issue_id,))
    cursor.execute("SELECT upvotes FROM issues WHERE id = ?", (issue_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Issue not found"}), 404

    upvotes = row[0]
    conn.commit()
    conn.close()

    return jsonify({"success": True, "upvotes": upvotes})

if __name__ == "__main__":
    init_db()
    print("[INFO] CampusFix Server starting on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
