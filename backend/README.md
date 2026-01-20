# Outlook Email Module Backend

A production-ready email module for the tax automation platform, integrating with Microsoft Outlook via Graph API.

## Features

- 🔐 **OAuth 2.0 Authentication** - Secure Microsoft authentication
- 📧 **Email CRUD Operations** - Full email management capabilities
- 🧵 **Multi-layer Threading** - Sophisticated 6-layer threading algorithm
- ⚡ **Real-time Webhooks** - < 5 second email sync
- 🔍 **Full-text Search** - Elasticsearch integration
- 📝 **Templates & Signatures** - Reusable email components
- 📊 **Audit Logging** - RTI compliance trail
- 🏷️ **Auto-classification** - Email type detection

## Technology Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Search**: Elasticsearch
- **Tasks**: Celery
- **API**: Microsoft Graph API

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Azure AD application (for OAuth)

### 1. Start Development Services

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, and Elasticsearch.

### 2. Set Up Python Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Azure AD credentials:

```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### 4. Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the output to your `.env` as `ENCRYPTION_KEY`.

### 5. Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for API documentation.

### 6. Start Celery Workers (Optional)

```bash
# In a new terminal
celery -A tasks.celery_app worker --loglevel=info

# For periodic tasks (in another terminal)
celery -A tasks.celery_app beat --loglevel=info
```

## Azure AD Setup

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. App registrations → New registration
3. Configure:
   - Name: "Tax Email Module"
   - Redirect URI: `http://localhost:8000/auth/callback`
4. Add API Permissions:
   - Microsoft Graph → Delegated:
     - `Mail.Read`
     - `Mail.ReadWrite`
     - `Mail.Send`
     - `MailboxSettings.ReadWrite`
     - `User.Read`
5. Create a client secret
6. Copy Tenant ID, Client ID, and Client Secret to `.env`

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/login` | Start OAuth flow |
| GET | `/auth/callback` | OAuth callback |
| POST | `/auth/logout` | Logout |
| POST | `/auth/refresh-token` | Refresh token |
| GET | `/auth/me` | Current user |

### Emails
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/emails` | List emails |
| GET | `/emails/{id}` | Get email |
| POST | `/emails` | Send email |
| PATCH | `/emails/{id}` | Update email |
| DELETE | `/emails/{id}` | Delete email |
| GET | `/emails/sync` | Sync from Outlook |

### Threads
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/threads` | List threads |
| GET | `/threads/{id}` | Get thread with emails |
| PATCH | `/threads/{id}` | Update thread |
| POST | `/threads/{id}/resolve` | Mark resolved |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/notify` | Receive notifications |
| POST | `/webhooks/subscribe` | Create subscription |
| DELETE | `/webhooks/subscribe` | Delete subscription |

### Signatures & Templates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/signatures` | List signatures |
| POST | `/signatures` | Create signature |
| GET | `/templates` | List templates |
| POST | `/templates` | Create template |
| POST | `/templates/{id}/render` | Render template |

## Email Threading Algorithm

The module uses a 6-layer threading algorithm:

1. **Microsoft Conversation ID** (100% confidence)
2. **X-Tax-Email-ID header** (95% confidence)
3. **RFC 5322 In-Reply-To** (99% confidence)
4. **RFC 5322 References** (95% confidence)
5. **Subject line matching** (70% confidence)
6. **Time + recipient matching** (50% confidence)

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── config.py        # Configuration
│   └── database.py      # DB connections
├── models/
│   ├── user.py
│   ├── client.py
│   ├── email.py
│   ├── signature.py
│   └── audit_log.py
├── routes/
│   ├── auth.py
│   ├── emails.py
│   ├── threads.py
│   ├── webhooks.py
│   ├── signatures.py
│   └── clients.py
├── services/
│   ├── auth_service.py
│   ├── graph_service.py
│   ├── threading_engine.py
│   ├── classification_service.py
│   └── email_service.py
├── tasks/
│   ├── celery_app.py
│   └── email_tasks.py
├── utils/
│   ├── decorators.py
│   ├── encryption.py
│   └── exceptions.py
├── tests/
├── requirements.txt
└── .env.example
```

## License

Proprietary - Tax Automation Platform
