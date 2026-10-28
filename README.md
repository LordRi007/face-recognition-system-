---
title: Face Recognition Management System
emoji: 👤
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Face Recognition Management System (FRMS)

A modern, secure, responsive, and production-ready **Web-Based Face Recognition and Identity Management System** built with Python, Flask, DeepFace (FaceNet512), OpenCV, and Bootstrap 5.

Designed for enterprise identity verification, voluntary attendance tracking, role-based access control (RBAC), and administrative auditing.

---

## 1. System Architecture & Features

```
+-----------------------------------------------------------------------------------+
|                            Client Browser (HTML5 / JS)                            |
|  - getUserMedia() Live Video Preview       - Guided Face Oval & Quality Meters    |
|  - Voluntary Informed Consent Modal        - Alternative PIN Fallback             |
|  - Responsive Light / Dark SaaS Theme      - Dynamic Chart.js Visualizations      |
+-----------------------------------------------------------------------------------+
                                         │ (HTTPS / REST JSON)
                                         ▼
+-----------------------------------------------------------------------------------+
|                             Nginx Reverse Proxy & SSL                             |
|  - SSL Termination (TLS 1.2 / 1.3)         - 16MB Image Upload Capacity           |
|  - Rate Limiting & Proxy Headers           - Static Asset Caching                 |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        Flask Application (Python 3.12)                            |
|  ├── Security & Auth: Flask-Login, Scrypt Password Hashing, Lockout Protection     |
|  ├── Biometrics: DeepFace (FaceNet512), OpenCV Quality Checks (Blur & Illumination)|
|  ├── Cryptography: AES-256 (Fernet) Biometric Template Encryption at Rest         |
|  ├── Attendance: Automated Check-In/Out, Late Cutoff, Admin Correction Auditing  |
|  └── Audit Logs: Immutable Event Tracking for Every Admin & Security Action       |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                    Database (PostgreSQL / SQLite Development)                      |
|  - Users (with alternative hashed PIN)     - Encrypted Face Enrollments (Vectors) |
|  - Daily Attendance Logs                   - Verification Attempt History         |
|  - Immutable Audit Trails                  - Organizational Departments           |
+-----------------------------------------------------------------------------------+
```

### Core Modules:
1. **Authentication & Authorization**: Role-based access (Admin, Staff, User), session expiration, rate-limiting lockout (5 failed attempts = 15-minute lockout), audit logs for all security actions.
2. **Executive Dashboard**: Real-time stats on total users, enrolled faces, attendance rates, absent rosters, and Chart.js trend graphs.
3. **User Management**: Add, view, edit, and deactivate users, department assignments, profile images, and alternative PIN setup.
4. **Consent-Based Face Enrollment**: Mandatory informed consent checkbox, live camera preview, blur detection (Laplacian variance), illumination validation (grayscale mean), and single-face verification.
5. **1-to-1 Facial Verification**: Cosine distance comparison against claimed identity using FaceNet512 ($\le 0.30$ match threshold), spoof detection heuristics, instant check-in/out buttons, and alternative PIN fallback.
6. **Attendance Tracking**: Automated morning arrival cutoff (e.g. 09:15:00 UTC), late duration calculation, admin manual correction with mandatory audit reason, and CSV export.
7. **Privacy & Security Hardening**: Raw face photos are **NEVER stored on disk or in the database**. Facial templates are stored as AES-256 Fernet encrypted float vectors. Voluntary consent withdrawal immediately purges biometric vectors.

---

## 2. Technology Stack

- **Backend**: Python 3.12, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF, Gunicorn
- **AI & Vision**: DeepFace, OpenCV, NumPy, Pretrained FaceNet512 model
- **Security & Crypto**: `cryptography` (Fernet AES-256), Werkzeug Scrypt password & PIN hashing
- **Frontend**: HTML5, CSS3 (Vanilla custom design system with dark/light themes), JavaScript, Bootstrap 5.3, Lucide Icons, Chart.js
- **Database**: SQLite (Local Dev) / PostgreSQL 16 (Production)

---

## 3. Local Development Setup (Windows / macOS / Linux)

### Step 1: Clone or Open Project
```powershell
cd "c:\face scan"
```

### Step 2: Create Python Virtual Environment (Python 3.12 recommended)
```powershell
# Windows
py -3.12 -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3.12 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(The default `.env` includes development secrets and a pre-generated Fernet 32-byte key).*

### Step 5: Seed Demo Database
Populate demo departments, administrators, staff accounts, sample attendance, and encrypted test biometrics:
```powershell
python scripts/seed_data.py
```

### Step 6: Start Flask Server
```powershell
python run.py
```
Open your browser to: **http://127.0.0.1:5000**

#### Default Demo Accounts:
| Role | Email | Password | Alternative PIN |
|---|---|---|---|
| **Administrator** | `admin@frms.local` | `AdminPass123!` | `1234` |
| **Staff / Security** | `staff@frms.local` | `StaffPass123!` | `4321` |
| **Demo User** | `alex.chen@frms.local` | `UserPass123!` | `9876` |

---

## 4. Production Deployment on Ubuntu 22.04 / 24.04 VPS

### Step 1: Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql postgresql-contrib \
    nginx git curl libgl1 libglib2.0-0 libgomp1 build-essential ufw
```

### Step 2: Set Up PostgreSQL Database
```bash
sudo -u postgres psql
```
In PostgreSQL prompt:
```sql
CREATE DATABASE frms_db;
CREATE USER frms_user WITH ENCRYPTED PASSWORD 'StrongProductionPasswordHere!';
GRANT ALL PRIVILEGES ON DATABASE frms_db TO frms_user;
\q
```

### Step 3: Clone Code & Configure Virtualenv
```bash
sudo mkdir -p /var/www/frms
sudo chown -R $USER:$USER /var/www/frms
git clone <your-repo-url> /var/www/frms
cd /var/www/frms

python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Production `.env`
```bash
cp .env.example .env
nano .env
```
Update production settings:
```ini
FLASK_ENV=production
SECRET_KEY=generate-a-strong-random-key-with-openssl-rand-hex-32
SESSION_COOKIE_SECURE=True
DATABASE_URL=postgresql://frms_user:StrongProductionPasswordHere!@localhost:5432/frms_db
BIOMETRIC_ENCRYPTION_KEY=generate-with-python-cryptography-fernet
```

Generate new encryption keys:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 5: Seed Database & Run Migrations
```bash
python scripts/seed_data.py
```

### Step 6: Configure Systemd Service
Copy `systemd.service` into systemd directory:
```bash
sudo cp systemd.service /etc/systemd/system/frms.service
sudo systemctl daemon-reload
sudo systemctl enable frms
sudo systemctl start frms
sudo systemctl status frms
```

### Step 7: Configure Nginx & SSL
```bash
sudo cp nginx.conf /etc/nginx/sites-available/frms
sudo ln -s /etc/nginx/sites-available/frms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Obtain free Let's Encrypt SSL certificate:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d frms.yourdomain.com
```

### Step 8: Configure Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 5. Docker & Docker Compose Deployment

Run the complete multi-container stack (PostgreSQL 16 + FRMS App) with a single command:

```bash
docker compose up -d --build
```
Access the application at: **http://localhost:5000**

To populate initial demo accounts in Docker:
```bash
docker compose exec web python scripts/seed_data.py
```

---

## 6. REST API Reference

All programmatic API endpoints accept and return `application/json`.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/login` | Authenticate user, return session cookie & profile | None |
| `POST` | `/api/auth/logout` | Invalidate active session | Required |
| `GET` | `/api/users` | List all users (searchable, filterable) | Staff / Admin |
| `POST` | `/api/users` | Register new user | Admin |
| `GET` | `/api/users/<id>` | Retrieve user profile & biometric status | Self / Staff |
| `PUT` | `/api/users/<id>` | Update user profile, department, or role | Admin |
| `DELETE` | `/api/users/<id>` | Delete user & purge biometric vectors | Admin |
| `POST` | `/api/face/detect` | Analyze frame quality (blur, lighting, face count) | Required |
| `POST` | `/api/face/enroll` | Enroll face with informed consent | Self / Staff |
| `POST` | `/api/face/verify` | 1-to-1 facial verification or alternative PIN | Self / Staff |
| `DELETE` | `/api/face/enrollment` | Voluntarily revoke & purge biometric vector | Self / Admin |
| `GET` | `/api/attendance` | Retrieve daily attendance records | Required |
| `POST` | `/api/attendance/check-in` | Record morning check-in (facial or PIN) | Self / Staff |
| `POST` | `/api/attendance/check-out` | Record evening check-out | Self / Staff |
| `GET` | `/api/reports/attendance` | Aggregate attendance & verification statistics | Staff / Admin |
| `GET` | `/api/dashboard/statistics` | Headline executive dashboard counts | Required |

---

## 7. Running the Automated Test Suite

Run unit and integration tests covering authentication, rate limiting, biometric encryption, cosine mathematics, quality gates, and attendance logic:

```bash
pytest -v
```

---

## 8. Biometric Ethics, Privacy & Known Limitations

1. **Zero-Raw-Photo Storage**: FRMS processes webcam frames in volatile memory, extracts the normalized mathematical vector, and discards pixel data immediately.
2. **AES-256 Encryption**: Biometric vectors are encrypted at rest with Fernet ciphers using keys stored outside the database.
3. **Consent & Revocation**: Biometrics are enrolled only after explicit consent confirmation and can be deleted at any time with a single click.
4. **Non-Biometric Alternative**: Users who cannot or prefer not to use facial recognition are provided an Alternative PIN check-in option.
5. **Presentation Attack Detection**: Integrated heuristics evaluate high-frequency texture variance to protect against printed paper or phone screen spoofing.
6. **VPS Hardware Sizing**: DeepFace model inference on CPU requires at least 2 vCPUs and 2GB RAM. On low-tier VPS (1 vCPU / 1GB RAM), configure swap memory and keep Gunicorn workers at 2.

---

## 9. License

Developed for enterprise identity management, educational research, and secure organizational attendance tracking.
