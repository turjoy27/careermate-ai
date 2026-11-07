# CareerMate AI — Smart AI Career Assistant

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-9.5-orange.svg)](https://www.mysql.com/)
[![Google Gen AI](https://img.shields.io/badge/Google%20Gen%20AI-gemini--3.8--flash-purple.svg)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-107%20Passed-brightgreen.svg)](#running-tests)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**CareerMate AI** is a production-oriented, AI-powered career acceleration SaaS web application designed primarily for university students, fresh graduates, and career transitioners in Bangladesh.

The platform combines the official **Google Gen AI Python SDK** (`google-genai`) with **deterministic backend algorithmic scoring** to deliver personalized career recommendations, ATS-compliant CV generation with ReportLab PDF export, real-time mock interviews with objective rubric evaluation, intelligent career counseling, and 3-stage progressive learning roadmaps.

---

## 1. Problem Statement & Objectives

### The Problem
University graduates in Bangladesh often face significant hurdles entering the modern software and corporate sectors:
- **Academic vs. Industry Gap:** University curricula rarely track fast-moving industry tech stacks in Dhaka, Chittagong, and remote global employers.
- **Unstructured CVs:** Inadequate formatting and weak bullet points result in immediate ATS rejection.
- **Interview Anxiety:** Lack of accessible, rigorous technical and behavioral interview practice with structured feedback.

### Main Objectives
1. **Diagnose & Bridge Skill Gaps:** Provide grounded, realistic career trajectory recommendations mapped to the Bangladesh job market.
2. **Empower Job Applications:** Generate professional resumes with AI-polished accomplishments exported into valid ReportLab PDFs without inventing qualifications.
3. **Calibrate Interview Readiness:** Conduct automated mock technical and HR interviews scored out of 10 against objective rubrics.
4. **Transparent Job Matching:** Compute profile-to-job match percentages using a deterministic, transparent formula rather than non-deterministic LLM scoring.

---

## 2. Core Modules & Features

```
+-------------------------------------------------------------------------------+
|                                CAREERMATE AI                                  |
+-------------------+-------------------+-------------------+-------------------+
|  1. Career Match  |   2. CV Studio    |  3. Mock Arena    |  4. Roadmaps      |
|  - Skill Gap Rpt  |  - AI Summaries   |  - Tech & HR Qs   |  - 3-Stage Paths  |
|  - BD Market Fit  |  - ReportLab PDF  |  - Rubric Scoring |  - Milestones     |
+-------------------+-------------------+-------------------+-------------------+
|  5. Job Matching  |   6. AI Chatbot   |  7. Admin Telemetry                   |
|  - 80/15/5% Math  |  - Profile Context|  - Moderation Queue                   |
|  - Bookmarks      |  - Rate-Limited   |  - Real-time KPIs                     |
+-------------------+-------------------+---------------------------------------+
```

### A. AI Career Recommendations (`apps.careers`)
- Synthesizes user skills, education, and preferences with Google Gemini (`gemini-3.8-flash`).
- Produces structured Pydantic-validated career recommendations and skill-gap diagnostics.

### B. AI Resume Builder & PDF Studio (`apps.resumes`)
- Real-time interactive CV builder.
- Generates professional summaries and polishes bullet points while strictly preserving factual honesty.
- Exports clean, ATS-compliant multi-page PDFs using ReportLab.

### C. AI Career Advisor Chatbot (`apps.chat`)
- Multi-turn career guidance retaining the last 10 messages of context.
- Injects candidate profile facts to answer questions about tech stacks, hiring processes, and salary benchmarks.
- Hardened with sliding-window rate limiting (max 15 messages/minute).

### D. Algorithmic Job Matching (`apps.jobs`)
- Curated job board featuring remote, hybrid, and onsite roles in Bangladesh.
- **Deterministic Match Engine:** Core required skills (80%), preferred bonus (15%), role alignment bonus (5%).
- Zero LLM scoring hallucination.

### E. Mock Interview Arena (`apps.interviews`)
- Generates calibrated technical and behavioral interview questions based on target role and seniority.
- Evaluates candidate answers on an objective 1-10 scale, detailing strengths, improvement areas, and ideal answer points.

### F. Personalized Learning Roadmaps (`apps.roadmaps`)
- 3-stage progressive curriculum: Beginner (Foundations), Intermediate (Core Mastery), Advanced (Production Ready).
- Actionable milestones with practical mini-projects and curated learning links.
- Interactive checkboxes with live visual progress recalculation.

### G. Platform Administration & Telemetry (`apps.dashboard`)
- Dedicated `/admin-analytics/` telemetry dashboard showing total candidates, resumes, interviews, roadmaps, and jobs.
- Role-based permissions denying non-staff access with HTTP 403 Forbidden.
- User feedback and content moderation reporting pipeline (`ReportedContent`).

---

## 3. Technology Stack

- **Backend:** Python 3.14.7, Django 6.1.3, Django REST Framework 3.18.3
- **Database:** MySQL 9.5 (via PyMySQL)
- **AI Framework:** Official Google Gen AI Python SDK (`google-genai==2.34.0`)
- **Default AI Model:** `gemini-3.8-flash`
- **PDF Generation:** ReportLab 5.1.0
- **Frontend:** Bootstrap 5.3.3, Bootstrap Icons, Vanilla JavaScript, HTML5/CSS3
- **Production Server:** Gunicorn, WhiteNoise

---

## 4. System Requirements

- Python 3.12+ (Python 3.14 recommended)
- MySQL Server 8.0+ or 9.0+
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))
- Git

---

## 5. Local Setup & Installation

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/your-username/careermate-ai.git
cd careermate-ai

python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure your credentials:
```env
SECRET_KEY=your-secure-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL Database
DB_NAME=careermate_ai
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Google Gemini API
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
```

### Step 4: Prepare MySQL Database & Run Migrations
Create the MySQL database if it does not exist:
```sql
CREATE DATABASE careermate_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run Django database migrations:
```bash
cd backend
python manage.py migrate
```

### Step 5: Seed Curated Resources & Create Superuser
```bash
python manage.py seed_resources
python manage.py createsuperuser
```

### Step 6: Test Gemini API Connectivity
Verify your Gemini API key and live model connectivity:
```bash
python manage.py verify_gemini
```

### Step 7: Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 6. Running Tests

The application features a comprehensive test suite of **107 unit, integration, and security tests**:

```bash
cd backend
python manage.py test
```

### Test Scope:
- **Accounts:** Registration, login, logout, profile updates, password hashing, onboarding.
- **AI Services:** Gemini client, timeout handling, retry logic, missing key error mapping.
- **Careers:** Career recommendations, profile compilation, skill-gap reports.
- **Resumes:** CV builder, AI summaries, bullet point polisher, ReportLab PDF rendering.
- **Chat:** Multi-turn history, context injection, rate limiting.
- **Jobs:** Deterministic 80/15/5% scoring, fuzzy skill normalization, bookmarking.
- **Interviews:** Question generation, response validation, rubric scoring out of 10.
- **Roadmaps:** 3-stage curriculum, milestone checkboxes, curated library.
- **Security & QA:** IDOR privacy isolation, admin RBAC guards, PDF special character escaping.

---

## 7. Production Deployment Guide

CareerMate AI is production-ready and includes containerization and PaaS configurations:

### Deployment via Docker Compose
```bash
docker compose up -d --build
```
This launches:
- `careermate_db`: MySQL 9 container with persistent volume.
- `careermate_web`: Gunicorn WSGI server on port 8000 with automatic migration and resource seeding.

### Deployment via PaaS (Railway / Render / Fly.io)
1. Configure environment variables in the provider dashboard (`SECRET_KEY`, `DEBUG=False`, `GEMINI_API_KEY`, MySQL credentials).
2. The included `Procfile` executes:
   ```
   web: gunicorn careermate_core.wsgi:application --chdir backend --bind 0.0.0.0:$PORT --workers 3
   ```
3. Static files are collected and served automatically via **WhiteNoise**.

---

## 8. Project Structure

```
careermate-ai/
├── .env.example                   # Sample environment configuration
├── .gitignore                      # Git exclusion rules (secrets, venv, staticfiles)
├── Dockerfile                      # Production Docker container configuration
├── docker-compose.yml              # Local multi-container Docker compose
├── Procfile                        # PaaS process file for Gunicorn
├── runtime.txt                     # Target Python version definition
├── requirements.txt                # Fixed application dependencies
├── docs/                           # Technical & user documentation
│   ├── ARCHITECTURE.md             # System design and architecture document
│   ├── USER_GUIDE.md               # User guide and module manual
│   └── FINAL_PROJECT_REPORT.md     # Comprehensive academic & technical report
└── backend/
    ├── manage.py                   # Django management script
    ├── careermate_core/            # Root project settings, URLs, WSGI, QA tests
    ├── apps/
    │   ├── accounts/               # Authentication, profiles, onboarding, skills
    │   ├── ai_services/            # Centralized Google Gen AI client, prompts, schemas
    │   ├── careers/                # Career recommendations & skill-gap reports
    │   ├── chat/                   # Career counselor chatbot & multi-turn history
    │   ├── dashboard/              # User dashboard & platform admin analytics
    │   ├── interviews/             # Mock interview arena & answer evaluation
    │   ├── jobs/                   # Job listings & deterministic match engine
    │   ├── resumes/                # CV builder & ReportLab PDF generator
    │   └── roadmaps/               # 3-stage roadmaps & platform resource library
    ├── static/                     # CSS, JS, and image assets
    └── templates/                  # Bootstrap 5.3 Django HTML templates
```

---

## 9. Known Limitations

1. **Third-Party AI Service Availability:** AI features require external network connectivity to Google Gemini. If Google's API experiences downtime, features gracefully report an error without crashing.
2. **Deterministic Matching Scope:** The match engine strictly evaluates technical and tool proficiencies. It does not attempt to evaluate subjective qualities like cultural fit.

---

## 10. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
