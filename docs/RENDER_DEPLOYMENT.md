# CareerMate AI — Render Deployment Guide (Native Python & PostgreSQL)

This guide provides complete, step-by-step instructions for deploying **CareerMate AI** on **[Render](https://render.com)** using Render's **native Python runtime** and **Render Managed PostgreSQL** (no Docker or containers required).

---

## 1. Architecture Overview on Render

```
                                  +-----------------------+
                                  |   Client / Browser    |
                                  +-----------+-----------+
                                              |
                                              | HTTPS (Auto SSL)
                                              v
                              +-------------------------------+
                              |    Render Load Balancer       |
                              +---------------+---------------+
                                              |
                        +---------------------+---------------------+
                        |                                           |
                        v                                           v
     +-------------------------------------+     +-------------------------------------+
     |        Static Files (/static/)      |     |         Application Requests        |
     | WhiteNoise (Compressed / Manifest)  |     |   Gunicorn WSGI (3 Workers)         |
     +-------------------------------------+     +------------------+------------------+
                                                                    |
                                        +---------------------------+---------------------------+
                                        |                                                       |
                                        v                                                       v
                         +-----------------------------+                         +-----------------------------+
                         |      Render PostgreSQL      |                         |      Google Gemini API      |
                         |  (via DATABASE_URL & Psycopg)|                         |    (gemini-3.8-flash)       |
                         +-----------------------------+                         +-----------------------------+
```

---

## 2. Prerequisites

1. A **Render account** ([render.com](https://render.com)).
2. A **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).
3. A **GitHub / GitLab repository** containing the CareerMate AI codebase.

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Create the Render Managed PostgreSQL Database

1. Log in to the [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation and select **PostgreSQL**.
3. Fill in the database settings:
   - **Name:** `careermate-db`
   - **Database Name:** `careermate_ai` (or leave default)
   - **User:** `careermate_user` (or leave default)
   - **Region:** Choose the region closest to your users (e.g., *Singapore*, *Frankfurt*, *Oregon*).
   - **PostgreSQL Version:** `16` (Default)
   - **Instance Type:** Free or Starter.
4. Click **Create Database**.
5. Once provisioned, locate the **Internal Database URL** under the database **Connections** section. You will connect your web service using this URL.

---

### Step 2: Create the Render Web Service (Native Python)

1. In the Render Dashboard, click **New +** and select **Web Service**.
2. Select **Build and deploy from a Git repository** and connect your repository (`careermate-ai`).
3. Fill in the service configuration:
   - **Name:** `careermate-ai`
   - **Region:** Same region as your PostgreSQL database.
   - **Branch:** `main` (or your production deployment branch).
   - **Root Directory:** *(Leave empty)*
   - **Runtime:** **Python** (Native Python 3.12).
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn careermate_core.wsgi:application --chdir backend --bind 0.0.0.0:$PORT`
   - **Instance Type:** Free or Starter.

---

### Step 3: Configure Environment Variables

Navigate to the **Environment** tab of your new Web Service and add the following required variables:

| Key | Value / Source | Description |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.12.8` | Pins the native Python runtime on Render. |
| `DEBUG` | `False` | Disables debug mode for production security. |
| `SECRET_KEY` | *(Generate a 50+ character random string)* | Production Django cryptographic secret key. |
| `DATABASE_URL` | *Paste your Render Internal Database URL* | Provided automatically by linking database or pasting URL. |
| `ALLOWED_HOSTS` | `careermate-ai.onrender.com` | Your Render domain (automatically includes `RENDER_EXTERNAL_HOSTNAME`). |
| `CSRF_TRUSTED_ORIGINS` | `https://careermate-ai.onrender.com` | Required for secure CSRF verification on forms. |
| `GEMINI_API_KEY` | *(Your actual Google Gemini API key)* | Powers AI recommendations, resumes, roadmaps, and chat. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | The validated enterprise Gemini model. |
| `SECURE_SSL_REDIRECT` | `True` | Enforces HTTPS on all web requests. |

> [!TIP]
> You can generate a secure 64-character `SECRET_KEY` locally by running:
> ```bash
> python -c 'import secrets; print(secrets.token_urlsafe(50))'
> ```

---

### Step 4: Deploy and Verify

1. Click **Create Web Service** (or **Manual Deploy > Deploy latest commit**).
2. Render will automatically execute `build.sh`:
   - Installs dependencies from `requirements.txt`.
   - Runs `python backend/manage.py migrate --noinput` to create all tables in PostgreSQL.
   - Compresses and hashes static assets via `python backend/manage.py collectstatic --no-input`.
3. Once the build finishes, Gunicorn starts serving traffic.
4. Verify deployment health by visiting your health check endpoint:
   ```text
   https://<your-service-name>.onrender.com/api/health/
   ```
   **Expected JSON Response:**
   ```json
   {
     "status": "healthy",
     "timestamp": "2026-11-07T07:00:00.000000+00:00",
     "environment": "production",
     "version": "1.0.0",
     "checks": {
       "database": {
         "engine": "postgresql",
         "status": "healthy",
         "latency_ms": 3.45
       },
       "api": {
         "status": "healthy"
       }
     }
   }
   ```

---

### Step 5: Create a Django Superuser (Admin Access)

To access the Django Admin portal at `https://<your-service-name>.onrender.com/admin/`:

1. In the Render Dashboard, go to your Web Service.
2. Click on the **Shell** tab on the left navigation bar.
3. Run the following command in the web terminal:
   ```bash
   python backend/manage.py createsuperuser
   ```
4. Follow the interactive prompts to enter an administrative username, email, and password.

---

## 4. Alternative: Render Blueprint (`render.yaml`)

You can also deploy both the Web Service and PostgreSQL database in a single click using Render Blueprints. 

The repository includes a ready-to-use `render.yaml` specification:

1. In the Render Dashboard, navigate to **Blueprints**.
2. Click **New Blueprint Instance**.
3. Select your repository.
4. Render will detect `render.yaml`, configure the managed PostgreSQL database, link `DATABASE_URL` automatically, and prompt only for `GEMINI_API_KEY` and `SECRET_KEY`.

---

## 5. Build and Start Commands Reference

- **Build Command:**
  ```bash
  ./build.sh
  ```
  *(Equivalently in the dashboard: `pip install -r requirements.txt && python backend/manage.py migrate --noinput && python backend/manage.py collectstatic --no-input`)*

- **Start Command:**
  ```bash
  gunicorn careermate_core.wsgi:application --chdir backend --bind 0.0.0.0:$PORT
  ```

---

## 6. Local Development vs. Render Production

CareerMate AI dynamically switches database engines based on the presence of `DATABASE_URL`:

- **Local Development:** When `DATABASE_URL` is omitted, Django automatically connects to your local **MySQL** database (`careermate_ai`) via `PyMySQL` using the credentials in your local `.env`.
- **Render Production:** When `DATABASE_URL` is set, Django connects to **Render PostgreSQL** via `dj-database-url` and modern `psycopg 3` with connection health checks and connection pooling (`CONN_MAX_AGE=600`).

---

## 7. Troubleshooting & FAQ

### Issue: CSRF verification failed (403 Forbidden)
- **Cause:** Request origin is not listed in `CSRF_TRUSTED_ORIGINS`.
- **Fix:** In Render environment variables, ensure `CSRF_TRUSTED_ORIGINS` is set to `https://<your-app-name>.onrender.com`.

### Issue: Static files returning 404
- **Cause:** `collectstatic` was not run or WhiteNoise is not loaded.
- **Fix:** The provided `build.sh` automatically runs `collectstatic`. Verify that `WhiteNoiseMiddleware` is enabled in `settings.py` (already configured).

### Issue: Gemini API Error: 404 NOT_FOUND
- **Cause:** Deprecated Gemini model name.
- **Fix:** Ensure `GEMINI_MODEL=gemini-3.8-flash` in the Render environment variables.
