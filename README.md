# 🏫 CampusFix - Smart Campus Issue Tracker
> **Built for Hackathon Demo & Rapid Campus Community Issue Resolution**

CampusFix is a web application that enables students, lecturers, and staff to report infrastructure and campus issues, automatically route them to the appropriate department, and track their resolution in real time through an interactive 4-step status pipeline:

$$\text{Submitted} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved}$$

---

## 🌟 Key Features

1. **✨ AI-Powered Smart Issue Classification (New!)**:
   - **Real-Time Natural Language Understanding**: As the student types their description, an offline AI engine analyzes semantics, urgency, and campus context.
   - **Auto-Suggestions Before Submission**: Suggests the matching **Department**, **Priority**, and **Location** (e.g. *Central Library 2nd Floor*, *CS Lab 3*, *Hostel Block B*).
   - **Student Confirmation & Override**: Suggestions are displayed as preview cards with confidence scores and reasoning. The student can click **"Apply Suggestions"** or edit any field before submitting.
   - **Zero External API Keys Needed**: 100% self-contained, offline-compatible, and lightning fast (<15ms response).

2. **Student & Lecturer Campus Board (`/`)**:
   - **One-Click Issue Reporting**: Submit problems with title, location/room, department, priority, and reporter role.
   - **Visual 4-Stage Progress Stepper**: Easily see whether an issue is Submitted, Assigned, In Progress, or Resolved.
   - **Community Upvotes ("Me Too")**: Students can upvote active issues to signal high campus impact to administrators.
   - **Interactive Search & Filter**: Real-time filtering by department, status, or search term (e.g. room number, keywords).
   - **Full Audit Timeline**: View chronological timestamps and technician notes for any ticket.

3. **Department Response Console (`/department`)**:
   - **Department Filter Tabs**: Switch between Facilities, IT Support, Electrical, Sanitation, Campus Security, and Hostel.
   - **Live Ticket Management**: Update ticket status directly (`Submitted` → `Assigned` → `In Progress` → `Resolved`).
   - **Staff Assignment & Work Log**: Assign maintenance technicians and append resolution notes.

4. **Hackathon Pre-Seeded Sample Data**:
   - Comes pre-populated with realistic campus issues (e.g., *Library AC leak*, *CS Lab projector damaged*, *Hostel water dispenser malfunction*).

---

## 🚀 How to Run the Application

### 1. Open Terminal in the project directory:
```bash
cd "C:\Users\Raksha T\.gemini\antigravity\scratch\campusfix"
```

### 2. Start the Flask server:
```bash
python app.py
```

### 3. Open in your browser:
- **Campus Issue Board (Student/Faculty view)**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Department Portal (Maintenance/Staff view)**: [http://127.0.0.1:5000/department](http://127.0.0.1:5000/department)

---

## 🎤 Hackathon 2-Minute Presentation Script

1. **The Problem**: Students and faculty encounter broken projectors, water leaks, or security hazards daily, but reporting usually happens through slow emails or physical complaint books where tickets get lost.
2. **The Solution (CampusFix)**: A centralized, transparent tracker with immediate department routing and community upvoting.
3. **Live Demo Flow**:
   - Open [http://127.0.0.1:5000](http://127.0.0.1:5000) and show the statistics overview and existing tickets.
   - Click **"Report Issue"**.
   - Type in Description: *"The ceiling projector in CS Lab 3 has a loose HDMI cable and flickering display."*
   - Watch the **AI Suggestions Box** automatically appear with:
     - Suggested Department: **IT Support** (98% Match)
     - Suggested Priority: **Medium**
     - Detected Location: **CS Lab 3**
   - Click **"Apply Suggestions"** to show how it auto-fills the form fields while letting the student confirm or edit before submitting!
   - Submit the issue and show the live ticket `#CF-XXXX` with status `Submitted`.
   - Click **"Department Portal"**, switch to **IT Support**, and advance the ticket to `In Progress` / `Resolved`.
   - Return to Campus Board to show the live updated status and timeline history!

---

## 🛠 Tech Stack
- **Backend**: Python 3.14 + Flask
- **Database**: SQLite3 (zero-configuration, built into Python)
- **Frontend**: HTML5, Tailwind CSS (via CDN), FontAwesome icons, Vanilla JS (Fetch API)
