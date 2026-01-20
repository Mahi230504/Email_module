# Email Module - Comprehensive Test UI Guide

## 🚀 Quick Start

### Starting the Test UI

```bash
cd /Users/kabeer/Downloads/TCO-email-module/backend
./venv/bin/streamlit run streamlit_test_ui.py --server.port 8502
```

The UI will open at: **http://localhost:8502**

### Prerequisites

1. **Backend API running**: Make sure the FastAPI backend is running on port 8000
   ```bash
   ./venv/bin/uvicorn app.main:app --reload --port 8000
   ```

2. **Services running**: Ensure Docker services are up
   ```bash
   docker-compose up -d
   ```

---

## 📋 Features Overview

The test UI provides a **professional email inbox interface** for comprehensive real-time testing of all backend functionality.

### Main Components

#### 1. **📨 Inbox Tab** (Email Management Interface)
Professional three-panel layout matching the design:

**Left Panel - Categories:**
- All emails, filtered by type
- Email classifications:
  - Compliance
  - Info Checklist
  - COI (Cost of Interest)
  - ITR (Income Tax Return)
  - JSON
  - ITR-V
  - Acknowledgement
  - Generic
  - Action Required
  - FYI
  - High Priority
- Status filters:
  - Unassigned
  - Unread
  - Sent
  - Drafts

**Middle Panel - Email List:**
- List of emails with sender, subject, time
- Visual indicators for unread (🔴), attachments (📎), flags (🚩)
- Email type badges
- Corporate/Non-Corporate tabs
- Search functionality
- Refresh button
- Sync from Outlook button

**Right Panel - Email Viewer/Composer:**
- **Email Viewer**:
  - Full email details
  - Sender, recipients (To, CC, BCC)
  - Email body with HTML rendering
  - Action buttons: Reply, Reply All, Forward, Mark as Read/Unread
  - Category badges
  - Attachment list

- **Email Composer**:
  - Template selection dropdown
  - Recipient fields (To, CC, BCC)
  - Subject line
  - Rich text body area
  - Client selection
  - Signature selection
  - Send / Save Draft buttons

#### 2. **🧪 Testing Panel Tab** (Backend Testing)
Comprehensive testing interface with 8 sub-tabs:

**🏥 Health Tab:**
- Check backend health status
- Get API information
- View system configuration

**👥 Clients Tab:**
- Load all clients from database
- Create test clients with validation
- Fields: Name, Email, Phone, Type, PAN, GSTIN
- View client data in JSON format

**🧵 Threads Tab:**
- Load all email threads
- View thread statistics (email count, status, last activity)
- Get available thread statuses
- Display threads in table format

**📝 Templates Tab:**
- Load all email templates
- View template details (name, subject, body, variables)
- Expandable template views

**✍️ Signatures Tab:**
- Load all email signatures
- View signature HTML and text versions
- Signature management

**🔔 Webhooks Tab:**
- Check webhook subscription status
- Create new webhook subscriptions for real-time email sync
- Delete existing subscriptions
- View subscription expiration details

**🔍 Search Tab:**
- Full-text search across emails
- Search by keywords
- View search results in table format
- Real-time Elasticsearch integration

**📊 Results Tab:**
- Test execution summary
- Pass/fail statistics
- Performance metrics
- Detailed test results table
- Exportable test data

---

## 🔐 Authentication

### Login Process

**Option 1: Login with Microsoft (Recommended)**
1. Click **🔐 Login with Microsoft** button.
2. You will be redirected to sign in with your Microsoft account.
3. After login, you will be redirected back to the Test UI.
4. The system will automatically authenticate and load your data.

**Option 2: Manual Token Login**
1. On the top navigation, enter a **User ID / Token**.
2. Click **Login**.
3. Use this only if you have a valid User ID from a previous session or database.

**Note:** For real-time email syncing and sending, you **MUST** use Option 1 to ensure valid Graph API tokens. Test users created via scripts with dummy tokens will fail on sync/send operations.

---

## 📧 Testing Email Functionality

### 1. **Sync Emails from Outlook**

**Steps:**
1. Navigate to **Inbox Tab**
2. Select a category (e.g., "All" or "Compliance")
3. Choose Corporate or Non-Corporate tab
4. Click **📥 Sync from Outlook**
5. Wait for sync to complete
6. Emails will populate in the list

**What it tests:**
- `/emails/sync` endpoint
- Microsoft Graph API integration
- Email synchronization service
- Threading engine (6-layer algorithm)
- Email classification service

### 2. **View Email Details**

**Steps:**
1. Click on any email in the list
2. Email details appear in right panel
3. View sender, recipients, body, attachments

**What it tests:**
- `/emails/{id}` endpoint
- Email retrieval
- Mark as read functionality
- Email rendering

### 3. **Send New Email**

**Steps:**
1. Click **✉️ New Message** in sidebar
2. (Optional) Select a template
3. Fill in:
   - To recipients (comma-separated)
   - CC/BCC (optional)
   - Subject
   - Body text
   - Client (optional)
   - Signature (optional)
4. Click **📤 Send**

**What it tests:**
- `/emails` POST endpoint
- Email sending via Graph API
- Template rendering
- Signature insertion
- Client association
- Email threading

### 4. **Email Actions**

**Available actions:**
- **Reply**: Reply to sender
- **Reply All**: Reply to all recipients
- **Forward**: Forward email to others
- **Mark as Read/Unread**: Toggle read status

**What it tests:**
- `/emails/{id}` PATCH endpoint
- Email status updates
- Graph API update operations

---

## 👥 Testing Client Management

### Create Test Client

**Steps:**
1. Go to **Testing Panel Tab**
2. Select **👥 Clients** tab
3. Fill in the form:
   - Client Name (auto-generated with timestamp)
   - Email
   - Phone (Indian format: 10 digits)
   - Type (Corporate/Non-Corporate)
   - PAN (10 characters: 5 letters + 4 digits + 1 letter)
   - GSTIN (15 characters)
4. Click **Create Client**

**What it tests:**
- `/clients` POST endpoint
- Input validation (PAN, GSTIN, phone)
- Client creation service
- Database insertion

### Load Clients

**Steps:**
1. Click **Load All Clients**
2. View total count and client data

**What it tests:**
- `/clients` GET endpoint
- Pagination
- Client listing

---

## 🧵 Testing Thread Management

### View Email Threads

**Steps:**
1. Go to **Testing Panel** → **🧵 Threads**
2. Click **Load All Threads**
3. View thread table with:
   - Thread ID
   - Subject
   - Status (awaiting_reply, replied, resolved, archived)
   - Email count
   - Last activity timestamp

**What it tests:**
- `/threads` GET endpoint
- Thread aggregation
- Thread status tracking

### Thread Statuses

**Steps:**
1. Click **Get Thread Statuses**
2. View available statuses

**What it tests:**
- `/threads/statuses` endpoint
- Thread status enumeration

---

## 📝 Testing Templates & Signatures

### Load Templates

**Steps:**
1. Go to **Testing Panel** → **📝 Templates**
2. Click **Load All Templates**
3. Expand templates to view:
   - Template name
   - Subject template
   - Body template (HTML & text)
   - Variables list

**What it tests:**
- `/templates` GET endpoint
- Template retrieval
- Variable extraction

### Load Signatures

**Steps:**
1. Go to **Testing Panel** → **✍️ Signatures**
2. Click **Load All Signatures**
3. View signature HTML and text versions

**What it tests:**
- `/signatures` GET endpoint
- Signature management

---

## 🔔 Testing Webhooks

### Check Webhook Status

**Steps:**
1. Go to **Testing Panel** → **🔔 Webhooks**
2. Click **Get Webhook Status**
3. View:
   - Active status
   - Subscription ID
   - Expiration date

**What it tests:**
- `/webhooks/status` endpoint
- Subscription tracking

### Create Subscription

**Steps:**
1. Click **Create Subscription**
2. System creates Microsoft Graph webhook subscription
3. View subscription details

**What it tests:**
- `/webhooks/subscribe` POST endpoint
- Graph API subscription creation
- Real-time notification setup

**What happens:**
- Microsoft will send notifications to `/webhooks/notify` when emails arrive
- Backend auto-syncs emails in < 5 seconds

### Delete Subscription

**Steps:**
1. Click **Delete Subscription**
2. Webhook subscription is removed

**What it tests:**
- `/webhooks/subscribe` DELETE endpoint
- Subscription cleanup

---

## 🔍 Testing Search

### Full-Text Search

**Steps:**
1. Go to **Testing Panel** → **🔍 Search**
2. Enter search query (e.g., "NIL filing", "tax return", client name)
3. Click **Search Emails**
4. View results in table format

**What it tests:**
- `/search` GET endpoint
- Elasticsearch integration
- Full-text indexing
- Search ranking
- Filter capabilities

**Search features:**
- Subject text search
- Body content search
- Sender/recipient search
- Email type filtering
- Date range filtering

---

## 📊 Viewing Test Results

### Results Summary

**Location:** Testing Panel → **📊 Results** tab

**Metrics:**
- Total tests run
- Passed count
- Failed count
- Average duration

**Features:**
- Detailed results table
- Pass/fail status for each test
- Response times
- Timestamp tracking
- Exportable data

---

## 🎯 Complete Testing Workflow

### End-to-End Testing Scenario

1. **Setup**
   - Login with user ID
   - Check health status

2. **Data Preparation**
   - Create test clients
   - Load templates and signatures

3. **Email Operations**
   - Sync emails from Outlook
   - Browse emails by category
   - View email details
   - Mark as read/unread
   - Send test email using template

4. **Advanced Features**
   - Create webhook subscription
   - Test real-time sync
   - Search for emails
   - View email threads
   - Check thread statuses

5. **Verification**
   - Review test results
   - Export test data
   - Check all APIs responded successfully

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "Not authenticated" warning**
- **Solution**: Login with a valid user ID in the top form
- Create a user first or use existing user ID from database

**Issue: "No emails to display"**
- **Solution**: Click "Sync from Outlook" button
- Ensure Microsoft OAuth tokens are valid
- Check if backend can connect to Microsoft Graph API

**Issue: "Backend is down" error**
- **Solution**: Start the FastAPI backend:
  ```bash
  ./venv/bin/uvicorn app.main:app --reload --port 8000
  ```

**Issue: Search not working**
- **Solution**: Check if Elasticsearch is running:
  ```bash
  docker-compose ps
  ```
  Start if needed:
  ```bash
  docker-compose up -d elasticsearch
  ```

**Issue: Webhook creation fails**
- **Solution**: 
  - Ensure you're authenticated
  - Check if Microsoft Graph API permissions are correct
  - Verify webhook notification URL is accessible

---

## 🔬 API Coverage

### Endpoints Tested

#### Authentication
- ✅ `GET /auth/me` - Get current user
- ✅ `GET /auth/status` - Auth status

#### Emails
- ✅ `GET /emails` - List emails with filters
- ✅ `GET /emails/{id}` - Get email details
- ✅ `POST /emails` - Send email
- ✅ `PATCH /emails/{id}` - Update email
- ✅ `GET /emails/sync` - Sync from Outlook
- ✅ `GET /emails/types` - Get email types

#### Threads
- ✅ `GET /threads` - List threads
- ✅ `GET /threads/{id}` - Get thread details
- ✅ `GET /threads/statuses` - Get statuses
- ✅ `PATCH /threads/{id}` - Update thread
- ✅ `POST /threads/{id}/resolve` - Resolve thread

#### Clients
- ✅ `GET /clients` - List clients
- ✅ `POST /clients` - Create client
- ✅ `GET /clients/{id}` - Get client
- ✅ `PATCH /clients/{id}` - Update client

#### Templates
- ✅ `GET /templates` - List templates
- ✅ `GET /templates/{id}` - Get template
- ✅ `POST /templates/{id}/render` - Render template

#### Signatures
- ✅ `GET /signatures` - List signatures
- ✅ `GET /signatures/{id}` - Get signature

#### Webhooks
- ✅ `GET /webhooks/status` - Get status
- ✅ `POST /webhooks/subscribe` - Create subscription
- ✅ `DELETE /webhooks/subscribe` - Delete subscription

#### Search
- ✅ `GET /search` - Full-text search
- ✅ `GET /search/suggestions` - Search suggestions

#### Health
- ✅ `GET /health` - Health check
- ✅ `GET /api/info` - API information

---

## 📝 Test Scenarios

### Scenario 1: First-Time Setup
1. Start backend and services
2. Open test UI
3. Login with user ID
4. Sync initial emails
5. Browse email categories
6. Create test client
7. Send test email

### Scenario 2: Email Management
1. View unread emails
2. Open email to view details
3. Mark as read
4. Reply to email
5. Search for specific email
6. Archive old emails

### Scenario 3: Real-Time Sync
1. Create webhook subscription
2. Send email from Outlook
3. Wait < 5 seconds
4. Refresh email list
5. Verify new email appears

### Scenario 4: Template-Based Sending
1. Load templates
2. Select template
3. Choose client
4. Render template with variables
5. Send email
6. Verify threading

---

## 💡 Tips

1. **Use realistic test data**: Create clients with valid PAN/GSTIN formats
2. **Test all categories**: Verify classification works for different email types
3. **Monitor performance**: Check response times in Results tab
4. **Test error cases**: Try invalid inputs to test validation
5. **Verify threading**: Send replies and check if threads are created correctly
6. **Test webhooks**: Enable webhooks for real-time experience
7. **Search extensively**: Test search with various keywords and filters

---

## 🎨 Design Details

The UI matches the provided screenshots with:
- Clean three-panel inbox layout
- Orange accent color (#ff6b35) for primary actions
- Unread indicator (orange left border)
- Category-based navigation
- Professional typography
- Hover effects and transitions
- Badge system for email types and priorities
- Responsive design

---

## 📦 What's Tested

### Backend Services
- ✅ Microsoft Graph API integration
- ✅ OAuth token management & refresh
- ✅ 6-layer email threading algorithm
- ✅ Email classification (7 types)
- ✅ Elasticsearch full-text search
- ✅ Real-time webhook notifications
- ✅ Template rendering
- ✅ Signature insertion
- ✅ Client management
- ✅ Audit logging
- ✅ Input validation (PAN, GSTIN, phone)

### Database Models
- ✅ User, Client, Email, EmailThread
- ✅ EmailAttachment, EmailSignature
- ✅ EmailTemplate, EmailFooter
- ✅ AuditLog

### External Integrations
- ✅ Microsoft Graph API
- ✅ PostgreSQL
- ✅ Redis
- ✅ Elasticsearch

---

## 🚀 Next Steps

After testing all features:
1. Export test results from Results tab
2. Document any issues found
3. Verify all critical workflows work end-to-end
4. Test with production-like data volumes
5. Perform load testing if needed

---

## 📞 Support

For issues or questions:
- Check backend logs: Terminal running uvicorn
- Check Streamlit logs: Terminal running streamlit
- View API docs: http://localhost:8000/docs
- View test UI: http://localhost:8502
