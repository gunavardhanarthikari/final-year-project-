# TrueFace AI

**AI-Powered Face Identification Under Partial Occlusion**

A professional academic-grade web application for robust face detection and identification, capable of recognizing faces even when 40-50% occluded by masks, scarves, glasses, or other obstructions.

## Features

- **Robust Face Detection**: Optmized for heavy occlusion using RetinaFace.
- **Role-Based Access Control**: Multi-user system with Admin, Manager, and Viewer roles.
- **Global Synchronization**: PostgreSQL support for cross-device data consistency.
- **Automated Alerts**: Dual-channel email notifications for face matches.
- **Advanced Dashboard**: Real-time analytics for system activity and detection accuracy.

## System Architecture

```
TrueFace AI/
├── backend/                 # Flask API server
│   ├── app.py              # Main application
│   ├── models/             # AI models & face processing
│   ├── database/           # Database models & operations (PostgreSQL/SQLite)
│   ├── utils/              # Utility functions (ID Gen, Notifier)
│   └── uploads/            # Temporary file storage
├── frontend/               # Web interface
├── face_database/          # Stored face embeddings & images
├── .env                    # Environment configuration (Private)
└── requirements.txt        # Python dependencies
```

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **AI/ML**: DeepFace, RetinaFace, FaceNet, OpenCV
- **Database**: PostgreSQL (Cloud/Global) or SQLite (Local)
- **Email**: SMTP handles matching alerts

## Installation

### 1. Clone & Set Up
```bash
git clone <repository-url>
cd trueface-ai
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install psycopg2-binary
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your details:
- **`DATABASE_URL`**: Your PostgreSQL URI (e.g., from Supabase).
- **`MAIL_USERNAME/PASSWORD`**: Your SMTP credentials for alerts.

### 4. Run the Application
```bash
python backend/app.py
```

## Authentication & Roles

The system uses a sequential ID system for security and auditing:

| ID Pattern | Role | Permissions |
| :--- | :--- | :--- |
| **`AD###`** | Administrator | Full control, User Management, Dashboard Stats. |
| **`MG###`** | Manager | Upload files, add NEW faces to the database. |
| **`VW###`** | Viewer | Upload files and see match results only. |

**Default Admin**: On first run, a default account is created:
- **Identifier**: `AD001` (or `admin@trueface.ai`)
- **Password**: `admin123`

## Usage

### Face Enrollment (Managers/Admins)
1. Enroll faces via the Admin panel.
2. The system assigns a unique **`FC###`** ID to every enrolled person.

### Alerts & Notifications
When a successful match is detected:
1. An email is sent to the **Global Admin**.
2. An email is sent to the **Uploader's** address.
3. The email includes detection confidence and a face crop attachment.

## Performance

- **Occlusion Handling**: Handles up to 50% coverage (masks/helmets).
- **Match Accuracy**: uses FaceNet512 for high-precision verification.
- **Concurrency**: PostgreSQL ensures stable data access across multiple devices.

## Academic Use
This system is designed for academic demonstrations and research. 

## License
Academic Project - 2026
