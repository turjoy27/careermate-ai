# CareerMate AI — Technical Architecture & System Design

## 1. System Overview

**CareerMate AI** is a production-oriented SaaS platform engineered for university students, fresh graduates, and career transitioners in Bangladesh. It unifies AI-driven career guidance, algorithmic job matching, ATS-optimized resume building with PDF generation, real-time mock interviews, and personalized 3-stage learning roadmaps.

```
                           +----------------------------------------+
                           |           Frontend Layer               |
                           |   (Bootstrap 5.3 + Vanilla JS + HTML5) |
                           +-------------------+--------------------+
                                               |
                                     HTTP / REST API (JSON)
                                               |
                           +-------------------v--------------------+
                           |        Django Web & API Layer          |
                           |       (Django 6.1 + DRF 3.18)          |
                           +-------------------+--------------------+
                                               |
               +-------------------------------+-------------------------------+
               |                               |                               |
    +----------v----------+         +----------v----------+         +----------v----------+
    |   MySQL 9.5 Storage |         |   AI Services Hub   |         | ReportLab PDF Engine|
    |  (PyMySQL + ORM)    |         | (Google Gen AI SDK) |         |  (Flowables + Canvas|
    |                     |         |  gemini-3.8-flash   |         |                     |
    +---------------------+         +---------------------+         +---------------------+
```

---

## 2. Django Modular Applications Structure

The application follows strict separation of business responsibilities:

| Application | Responsibilities | Key Models & Services |
| :--- | :--- | :--- |
| **`apps.accounts`** | Custom email-based user model, profile management, educational history, skills portfolio, onboarding wizard. | `User`, `UserProfile`, `Education`, `Experience`, `UserSkill`. |
| **`apps.ai_services`** | Centralized client service wrapping the official `google-genai` Python SDK, Pydantic schemas, prompt engineering, and exception mapping. | `GeminiService`, `exceptions.py`, `schemas.py`, `prompts.py`. |
| **`apps.careers`** | Profile serialization, Gemini-assisted career recommendations, market demand diagnosis, and historical sessions. | `CareerRecommendationSession`, `CareerRecommendation`, `SkillGapReport`, `CareerRecommendationService`. |
| **`apps.resumes`** | Multi-section CV builder, live preview, Gemini bullet polisher & summary generation, ReportLab PDF rendering. | `Resume`, `ResumeEducation`, `ResumeExperience`, `ResumeProject`, `ResumeService`, `ResumePDFGenerator`. |
| **`apps.chat`** | Context-injected career counselor chatbot, 10-turn conversation window, MySQL persistence, rate limiting (15 msg/min). | `ChatConversation`, `ChatMessage`, `ChatService`. |
| **`apps.jobs`** | Curated job listings, bookmarking, and **deterministic mathematical match scoring engine** (zero hallucination). | `JobListing`, `SavedJob`, `JobMatchEngine`. |
| **`apps.interviews`** | AI mock interview question generator, response capture, objective 1-10 rubric evaluation, scoring history. | `InterviewSession`, `InterviewQuestion`, `InterviewService`. |
| **`apps.roadmaps`** | 3-stage progressive curriculum (Beginner, Intermediate, Advanced), interactive milestone progress checklist, curated platform library. | `LearningRoadmap`, `RoadmapStage`, `RoadmapMilestone`, `RoadmapResource`, `LearningResource`, `ReportedContent`, `RoadmapService`. |
| **`apps.dashboard`** | Unified user dashboard, profile strength tracker, and dedicated Platform Administration Telemetry (`/admin-analytics/`). | `DashboardHomeView`, `AdminAnalyticsDashboardView`. |

---

## 3. Deterministic Job Matching vs. Generative AI

A core architectural principle of CareerMate AI is **Algorithmic Separation**:
- **Generative AI (Gemini):** Used for qualitative synthesis, phrasing enhancement, question generation, and constructive critique.
- **Deterministic Math Engine ([`JobMatchEngine`](file:///Users/turjoy/Documents/Software%20dev%20%233/CareerMate%20AI/careermate-ai/backend/apps/jobs/matching.py)):** Used for match percentages.
  $$\text{Final Score} = \min\left(100, \left[\frac{|\text{Matched Core}|}{|\text{Total Core}|} \times 80\right] + \left[\frac{|\text{Matched Pref}|}{|\text{Total Pref}|} \times 15\right] + \text{Role Bonus (5)}\right)$$
  - Fuzzy normalization handles common tech aliases (`react.js` $\to$ `react`, `k8s` $\to$ `kubernetes`, `postgresql` $\to$ `postgres`).
  - Completely eliminates non-deterministic LLM scoring and false eligibility claims.

---

## 4. Security & Privacy Architecture

1. **API Key Isolation:** `GEMINI_API_KEY` is loaded exclusively from `.env` in the backend service layer and is never exposed in client HTML, templates, or JS.
2. **Object-Level Permissions (IDOR Defense):** Queries across all user resources (CVs, mock interviews, chat history, roadmaps) enforce `profile=request.user.profile`. Unauthorized requests result in `404 Not Found`.
3. **Role-Based Access Control (RBAC):** Platform Administration Telemetry (`/admin-analytics/`) is guarded by `request.user.is_staff or request.user.role == 'admin'`, returning `403 Forbidden` (`PermissionDenied`) to students.
4. **CSRF & XSS Protection:** Django CSRF tokens are enforced on all POST endpoints. DOM outputs are sanitized through client-side `escapeHTML()` utilities.
