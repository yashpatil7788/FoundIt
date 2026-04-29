# FoundIt

FoundIt is a modern, production-grade web application for campus communities, built with Flask, SQLAlchemy ORM, and Supabase (PostgreSQL for data, Supabase Storage for images). It is designed with best practices for security, scalability, and maintainability, and is fully cloud-native and container-ready. The app is deployed on Render with automated CI/CD, secret management, and robust error handling.

## Key Platforms
- **Lost & Found:** Report, search, and manage lost or found items.
- **Marketplace:** Post, browse, and manage items for sale or rent.

## Live Link : https://found-it-mu.vercel.app/auth/login
  

## Industry-Grade Features
- **Authentication & Authorization:**
  - Secure registration and login with hashed passwords (Werkzeug)
  - Email verification via Flask-Mail
  - Role-based access control (admin, student, guest)
  - Persistent sessions with Flask-Session
- **Cloud-Native Storage:**
  - PostgreSQL (Supabase) for all data
  - Supabase Storage for all images (no local storage)
- **Image Handling:**
  - Direct upload to Supabase Storage
  - Strict validation (PNG, JPG, JPEG, WEBP)
  - Public URLs for images
- **Feedback & Comments:**
  - Users can comment and rate items on both platforms
- **Admin Utilities:**
  - Category management
  - Default admin account (admin/admin123)
  - User and item moderation
- **Security:**
  - Password hashing (Werkzeug)
  - CSRF protection (Flask-WTF)
  - Session security (Flask-Session, secret key)
  - Email credentials and secrets managed via environment variables or Render Secret Files
  - No sensitive data in codebase
- **Error Handling:**
  - Custom 404 and 500 error pages
  - Logging for startup, DB connection, and errors
- **Deployment:**
  - Dockerized for local and cloud deployment
  - Infrastructure-as-code with `render.yaml`
  - Automated deployment to Render on every push
  - Secret management and environment variables via Render dashboard
- **Extensibility:**
  - Modular Flask blueprints
  - Easily add new features (e.g., events, forums, notifications)
- **Documentation:**
  - Well-structured, developer-friendly codebase
  - Clear setup, configuration, and extension instructions

---

## Table of Contents
- [Features](#industry-grade-features)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [Core Functionality](#core-functionality)
- [Usage Guide](#usage-guide)
- [Security & Best Practices](#security--best-practices)
- [Extending the App](#extending-the-app)
- [Deployment](#deployment)
- [License](#license)

---

## Project Structure

```
FoundIt/
├── Main.py                # Main Flask application entry point
├── config.py              # Configuration settings (Supabase, mail, sessions, etc.)
├── models.py              # SQLAlchemy ORM models and core logic
├── extensions.py          # Flask extensions (e.g., mail)
├── blueprints/            # Flask blueprints for modular routes
│   ├── auth/
│   ├── lost_and_found/
│   └── marketplace/
├── static/
│   └── images/            # (Legacy, not used; images now in Supabase)
├── templates/             # HTML templates (Jinja2)
│   ├── base.html
│   ├── 404.html, 500.html
│   ├── auth/
│   ├── lost_and_found/
│   └── marketplace/
├── flask_session/         # Session files (auto-generated)
├── lostnfound.db          # (Legacy, not used)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (Supabase, DB, mail, secret)
└── init_categories.py     # Script to initialize default categories
```

---

## Setup Instructions

### 1. Clone the Repository
```sh
git clone https://github.com/yashpatil7788/FoundIt
cd FoundIt
```

### 2. Create & Activate a Virtual Environment (Recommended)
```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Configuration
- Copy `.env.example` to `.env` and fill in your Supabase/PostgreSQL, Supabase Storage, and mail credentials.
- Edit `config.py` if you need to override any settings.

### 5. Initialize Categories (Optional, recommended for first run)
```sh
python init_categories.py
```

### 6. Run the Application
```sh
python Main.py
```
- Open your browser and navigate to: http://127.0.0.1:5000/

---

## Configuration
All configuration values are managed in `.env` and `config.py`. Key settings include:

| Key                      | Description                                      |
|--------------------------|--------------------------------------------------|
| POSTGRES_URI             | PostgreSQL connection string (Supabase)          |
| SUPABASE_URL             | Supabase project URL                             |
| SUPABASE_KEY             | Supabase service key                             |
| SUPABASE_LOSTFOUND_BUCKET| Supabase Storage bucket for lost/found images    |
| SUPABASE_MARKETPLACE_BUCKET| Supabase Storage bucket for marketplace images |
| MAIL_SERVER, MAIL_PORT   | SMTP server and port                             |
| MAIL_USERNAME, MAIL_PASSWORD | Email credentials for Flask-Mail           |
| SECRET_KEY               | Flask secret key (change for production)         |
| SESSION_TYPE, SESSION_FILE_DIR, SESSION_PERMANENT | Flask-Session settings |

---

## Database Schema (PostgreSQL via SQLAlchemy ORM)

### Tables & Fields

#### 1. user
| Column      | Type      | Description                        |
|-------------|-----------|------------------------------------|
| id          | INTEGER   | Primary key                        |
| username    | TEXT      | Unique username                    |
| password    | TEXT      | Hashed password                    |
| email       | TEXT      | Unique user email                  |
| role        | TEXT      | User role (admin, student, guest)  |
| created_at  | DATETIME  | Timestamp of registration          |
| is_admin    | BOOLEAN   | True if user is an admin           |
| is_confirmed| BOOLEAN   | True if email is verified          |

#### 2. lost_found_item
| Column      | Type      | Description                        |
|-------------|-----------|------------------------------------|
| id          | INTEGER   | Primary key                        |
| name        | TEXT      | Name/title of the item             |
| description | TEXT      | Detailed description               |
| category    | TEXT      | Category name                      |
| status      | TEXT      | "lost" or "found"                  |
| priority    | INTEGER   | Priority level                     |
| date        | DATE      | Date when reported                 |
| location    | TEXT      | Location details                   |
| contact_info| TEXT      | Contact details                    |
| latitude    | REAL      | Latitude coordinate (optional)     |
| longitude   | REAL      | Longitude coordinate (optional)    |
| user_id     | INTEGER   | Foreign key to user.id             |
| found_by    | INTEGER   | User ID who found the item         |
| claimed_by  | INTEGER   | User ID who claimed the item       |
| is_deleted  | BOOLEAN   | Soft delete flag                   |

#### 3. marketplace_item
| Column      | Type      | Description                        |
|-------------|-----------|------------------------------------|
| id          | INTEGER   | Primary key                        |
| name        | TEXT      | Name/title of the item             |
| description | TEXT      | Detailed description               |
| price       | NUMERIC   | Price of the item                  |
| category    | TEXT      | Category name                      |
| condition   | TEXT      | Condition (e.g., "New", "Used")    |
| status      | TEXT      | "available", "sold", or "rented"    |
| date        | DATE      | Date when posted                   |
| location    | TEXT      | Location details                   |
| contact_info| TEXT      | Contact details of seller          |
| user_id     | INTEGER   | Foreign key to user.id             |
| is_deleted  | BOOLEAN   | Soft delete flag                   |

#### 4. category
| Column      | Type      | Description                        |
|-------------|-----------|------------------------------------|
| id          | INTEGER   | Primary key                        |
| name        | TEXT      | Category name                      |
| type        | TEXT      | Either lost_found or marketplace   |
| description | TEXT      | Category description (optional)    |

#### 5. item_image
| Column      | Type      | Description                        |
|-------------|-----------|------------------------------------|
| id          | INTEGER   | Primary key                        |
| item_type   | TEXT      | 'lost_found' or 'marketplace'      |
| item_id     | INTEGER   | ID of the associated item          |
| image_url   | TEXT      | Public URL in Supabase Storage     |
| uploaded_at | DATETIME  | Timestamp of upload                |

#### 6. feedback
| Column      | Type      | Description                        |
|-------------|-----------|------------------------------------|
| id          | INTEGER   | Primary key                        |
| user_id     | INTEGER   | Foreign key to user.id             |
| item_type   | TEXT      | Either lost_found or marketplace   |
| item_id     | INTEGER   | ID of the associated item          |
| comment     | TEXT      | User’s feedback or comment         |
| rating      | INTEGER   | Optional rating                    |
| date        | DATETIME  | Timestamp when comment was posted  |

---

## Core Functionality
All database operations and core logic are implemented in `models.py` using SQLAlchemy ORM. All image uploads are handled via Supabase Storage. The app is structured for maintainability and extensibility, following best practices for separation of concerns and modularity.

---

## Usage Guide

### 1. User Registration & Login
- Register a new account or use the default admin:
  - Username: admin
  - Password: admin123
- Email verification is required — check your inbox for the confirmation link.
- Log in to access both Lost & Found and Marketplace platforms.

### 2. Lost & Found Platform
- **Add Item:** Click “Add Lost/Found Item”, fill in details (name, description, category, status, location), and upload an image.
- **Browse/Search:** Use filters (category, status) and sorting to find items.
- **Comment:** Click on an item to view details and add feedback/comments.

### 3. Marketplace Platform
- **Add Item:** Navigate to “Add Marketplace Item”, fill in details (name, description, price, category, condition), and upload an image.
- **Browse/Search:** Filter by category, price range, or condition to find listings.
- **Comment:** Click on a listing to view details and leave feedback or inquiries.

### 4. Admin Dashboard
- Log in as admin to access special utilities:
  - Manage categories and users.
  - Edit or delete any user, lost/found item, or marketplace item.

---

## Security & Best Practices
- **Password Hashing:** Passwords are securely hashed using Werkzeug.
- **Session Security:** Sessions are stored on the filesystem (Flask-Session) with a secret key.
- **CSRF Protection:** Enabled via Flask-WTF for all forms.
- **Image Uploads:**
  - Restricted to allowed extensions (png, jpg, jpeg, webp).
  - Images are uploaded directly to Supabase Storage.
- **Email Verification:** SMTP credentials are kept in environment variables or `.env` (never committed).
- **Configuration Management:** All sensitive data is managed via environment variables or Render Secret Files.
- **Error Handling:** Custom error pages and logging for all critical operations.
- **Cloud-Native Deployment:** Fully containerized, with automated deployment and secret management on Render.

---

## Extending the App
- **Add New Blueprints:** Create additional Flask blueprints for new features (e.g., Events, Forums).
- **Extend Models & Templates:**
  - Add new fields or tables in `models.py` and update related templates.
  - Customize HTML/CSS in `templates/` and `static/`.
- **Advanced Search & Analytics:** Integrate full-text search or analytics tools.
- **Notifications:** Add real-time notifications using WebSockets (Flask-SocketIO).
- **REST API Endpoints:** Expose CRUD operations via a RESTful API (Flask-RESTful or Flask-API).

---

## Deployment

### Render (Recommended)
- **Cloud-native deployment** using [Render](https://render.com/), with infrastructure-as-code via `render.yaml`.
- **Automated builds and deploys** on every push to the main branch.
- **Secret management** via Render dashboard or Secret Files.
- **Health checks** and logging via Render dashboard.
- **Scalable and production-ready** out of the box.

#### Steps:
1. Commit and push your code (including `render.yaml`) to GitHub.
2. Create a new Web Service on Render and connect your repo.
3. Set environment variables and/or upload your `.env` as a Secret File.
4. Deploy and monitor via the Render dashboard.

## License
MIT License

