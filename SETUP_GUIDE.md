# Outlook Email Module - Complete Setup & Testing Guide

This guide walks you through setting up, running, and testing the Email Module backend.

---

## Prerequisites

- **Python 3.10+** - Required for FastAPI and async features
- **Docker & Docker Compose** - For running PostgreSQL, Redis, Elasticsearch
- **Azure AD Application** - For Microsoft OAuth (can skip for mock testing)

---

## Step 1: Start Docker Services

First, start the required services (PostgreSQL, Redis, Elasticsearch):

```bash
cd /Users/kabeer/Downloads/TCO-email-module

# Start all services in background
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                    STATUS
email-postgres          running (0.0.0.0:5432)
email-redis             running (0.0.0.0:6379)
email-elasticsearch     running (0.0.0.0:9200)
```

---

## Step 2: Set Up Python Environment

```bash
cd /Users/kabeer/Downloads/TCO-email-module/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate   # On macOS/Linux
# OR: venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

This installs:
- FastAPI, Uvicorn (API server)
- SQLAlchemy, Alembic (database)
- Redis, Elasticsearch (caching & search)
- Celery (background tasks)
- Streamlit (test UI)

---

## Step 3: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit the .env file
nano .env   # or use any editor
```

### Minimum Required Configuration:

```env
# Database (uses Docker defaults)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/email_module

# Redis
REDIS_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Generate a new encryption key:
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=<paste-generated-key-here>

# Platform URL (for OAuth callback)
PLATFORM_URL=http://localhost:8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000

# Webhook secret (any random string)
WEBHOOK_SECRET=my-webhook-secret-123
```

### Generate Encryption Key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and paste it as `ENCRYPTION_KEY` in your `.env` file.

---

## Step 4: Azure AD Configuration (Optional - for real OAuth)

If you want to test real Microsoft OAuth:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure:
   - Name: `Tax Email Module`
   - Redirect URI: `http://localhost:8000/auth/callback`
5. Go to **API permissions** and add:
   - Microsoft Graph → Delegated:
     - `Mail.Read`, `Mail.ReadWrite`, `Mail.Send`
     - `MailboxSettings.ReadWrite`
     - `User.Read`
6. Create a **Client secret** under **Certificates & secrets**
7. Copy these values to your `.env`:

```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

---

## Step 5: Start the FastAPI Server

```bash
# Make sure you're in the backend directory with venv activated
cd /Users/kabeer/Downloads/TCO-email-module/backend
source venv/bin/activate

# Start the server
uvicorn app.main:app --reload --port 8000
```

Expected output:
```
🚀 Starting Outlook Email Module...
✅ Database tables created
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Verify the Server:

Open in browser: http://localhost:8000

You should see:
```json
{
  "service": "Outlook Email Module",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### API Documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Step 6: Run the Streamlit Test UI

In a **new terminal**:

```bash
cd /Users/kabeer/Downloads/TCO-email-module/backend
source venv/bin/activate

# Start Streamlit
streamlit run streamlit_app.py --server.port 8501
```

Expected output:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

Open http://localhost:8501 to see the test UI.

---

## Step 7: Start Celery Workers (Optional - for background tasks)

In a **new terminal**:

```bash
cd /Users/kabeer/Downloads/TCO-email-module/backend
source venv/bin/activate

# Start Celery worker
celery -A tasks.celery_app worker --loglevel=info
```

For periodic tasks (in another terminal):
```bash
celery -A tasks.celery_app beat --loglevel=info
```

---

## Step 8: Run Tests

```bash
cd /Users/kabeer/Downloads/TCO-email-module/backend
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_threading.py -v
pytest tests/test_classification.py -v
```

---

## Testing the API

### Using Streamlit UI:

1. Open http://localhost:8501
2. Go to the **"🧪 API Testing"** tab
3. Click **"Check API Health"** to verify connection
4. Test individual endpoints

### Using cURL:

```bash
# Health check
curl http://localhost:8000/health

# Get login URL
curl http://localhost:8000/auth/login

# List emails (requires auth token)
curl -H "Authorization: Bearer test-user-id" http://localhost:8000/emails

# Search emails
curl "http://localhost:8000/search?q=NIL+filing" -H "Authorization: Bearer test-user-id"

# Get templates
curl http://localhost:8000/templates -H "Authorization: Bearer test-user-id"
```

### Using Python:

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Get login URL
response = requests.get(f"{BASE_URL}/auth/login")
print(response.json())
```

---

## Quick Reference: All Terminals Needed

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `docker-compose up -d` | Database, Redis, Elasticsearch |
| 2 | `uvicorn app.main:app --reload --port 8000` | FastAPI server |
| 3 | `streamlit run streamlit_app.py --server.port 8501` | Test UI |
| 4 | `celery -A tasks.celery_app worker --loglevel=info` | Background worker |
| 5 | `celery -A tasks.celery_app beat --loglevel=info` | Periodic tasks |

---

## Troubleshooting

### Docker Services Not Starting
```bash
# Check logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs elasticsearch

# Restart services
docker-compose down
docker-compose up -d
```

### Database Connection Error
- Ensure PostgreSQL is running: `docker-compose ps`
- Verify DATABASE_URL in `.env`
- Check port 5432 is not in use

### Elasticsearch Connection Error
- Elasticsearch takes ~30-60 seconds to start
- Check: `curl http://localhost:9200`

### Import Errors
- Ensure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### OAuth Errors
- For testing without Azure AD, use mock data in Streamlit UI
- Verify Azure AD app configuration and redirect URIs

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/login` | GET | Get OAuth login URL |
| `/auth/callback` | GET | OAuth callback |
| `/emails` | GET | List emails |
| `/emails` | POST | Send email |
| `/emails/{id}` | GET | Get email |
| `/emails/sync` | GET | Sync from Outlook |
| `/threads` | GET | List threads |
| `/threads/{id}` | GET | Get thread |
| `/search?q=query` | GET | Search emails |
| `/templates` | GET | List templates |
| `/signatures` | GET | List signatures |
| `/clients` | GET | List clients |
| `/webhooks/subscribe` | POST | Create subscription |
| `/webhooks/status` | GET | Subscription status |

---

## Next Steps

1. ✅ Test all API endpoints via Streamlit UI
2. ✅ Configure Azure AD for real OAuth
3. ✅ Set up webhook endpoint on public URL (ngrok)
4. ✅ Connect to your frontend application
5. ✅ Deploy to production
