"""
Enhanced Streamlit Test Dashboard for Email Module Backend

Comprehensive interactive testing interface with real API integration.
Run with: streamlit run streamlit_app.py --server.port 8501
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import subprocess

# Configuration
API_BASE_URL = "http://localhost:8000"

# Session state initialization
if "test_results" not in st.session_state:
    st.session_state.test_results = []
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None


# ============================================================================
# API Testing Functions
# ============================================================================

def make_api_call(method: str, endpoint: str, data: dict = None, params: dict = None, headers: dict = None) -> dict:
    """Make API request and return response with metadata."""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Add auth header if token exists
    if not headers:
        headers = {}
    if st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
    
    start_time = datetime.now()
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return {"error": f"Unknown method: {method}"}
        
        duration = (datetime.now() - start_time).total_seconds()
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        return {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "data": response_data,
            "duration": duration,
            "method": method,
            "endpoint": endpoint,
            "timestamp": start_time.isoformat()
        }
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            "success": False,
            "error": str(e),
            "duration": duration,
            "method": method,
            "endpoint": endpoint,
            "timestamp": start_time.isoformat()
        }


def display_api_response(result: dict, test_name: str = None):
    """Display API response with formatting."""
    if test_name:
        st.markdown(f"### {test_name}")
    
    # Status indicator
    if result.get("success"):
        st.success(f"✅ {result['method']} {result['endpoint']} - {result['status_code']} ({result['duration']:.3f}s)")
    else:
        st.error(f"❌ {result['method']} {result['endpoint']} - {result.get('status_code', 'ERROR')} ({result['duration']:.3f}s)")
    
    # Response data
    with st.expander("📄 Response Data"):
        if "error" in result:
            st.error(result["error"])
        else:
            st.json(result.get("data", {}))
    
    # Add to test results
    st.session_state.test_results.append({
        "test": test_name or result['endpoint'],
        "success": result.get("success", False),
        "status": result.get("status_code", "ERROR"),
        "duration": result.get("duration", 0),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    })


# ============================================================================
# Test Suites
# ============================================================================

def run_health_checks():
    """Run basic health checks."""
    st.markdown("## 🏥 Health Checks")
    
    tests = [
        ("API Health", "GET", "/health", None, None),
        ("API Info", "GET", "/api/info", None, None),
        ("Root Endpoint", "GET", "/", None, None),
    ]
    
    for test_name, method, endpoint, data, params in tests:
        result = make_api_call(method, endpoint, data, params)
        display_api_response(result, test_name)


def run_client_tests():
    """Run client management tests."""
    st.markdown("## 👥 Client Management Tests")
    
    # Create test client
    st.markdown("### Create Test Client")
    test_client_data = {
        "name": f"Test Client {datetime.now().strftime('%H%M%S')}",
        "email": "testclient@example.com",
        "phone": "9876543210",
        "client_type": "corporate",
        "pan": f"TEST{datetime.now().strftime('%H%M')}X",
        "gstin": f"27TEST{datetime.now().strftime('%H%M')}X1Z5"
    }
    
    result = make_api_call("POST", "/clients", data=test_client_data)
    display_api_response(result, "Create Client")
    
    if result.get("success"):
        client_id = result["data"].get("client", {}).get("id")
        
        if client_id:
            # List clients
            result = make_api_call("GET", "/clients", params={"limit": 10})
            display_api_response(result, "List Clients")
            
            # Get specific client
            result = make_api_call("GET", f"/clients/{client_id}")
            display_api_response(result, "Get Client Details")
            
            # Update client
            result = make_api_call("PATCH", f"/clients/{client_id}", data={"email": "updated@example.com"})
            display_api_response(result, "Update Client")


def run_thread_tests():
    """Run thread management tests."""
    st.markdown("## 🧵 Thread Management Tests")
    
    # List threads
    result = make_api_call("GET", "/threads", params={"limit": 10})
    display_api_response(result, "List Threads")
    
    # Get thread statuses
    result = make_api_call("GET", "/threads/statuses")
    display_api_response(result, "Get Thread Statuses")


def run_email_tests():
    """Run email operation tests."""
    st.markdown("## 📧 Email Operations Tests")
    
    # List emails
    result = make_api_call("GET", "/emails", params={"limit": 10})
    display_api_response(result, "List Emails")
    
    # Get email types
    result = make_api_call("GET", "/emails/types")
    display_api_response(result, "Get Email Types")


def run_webhook_tests():
    """Run webhook tests."""
    st.markdown("## 🔔 Webhook Tests")
    
    # Get subscription status
    result = make_api_call("GET", "/webhooks/status")
    display_api_response(result, "Get Webhook Status")


# ============================================================================
# Pytest Runner
# ============================================================================

def run_pytest_suite():
    """Run pytest test suite and display results."""
    st.markdown("## 🧪 Running Pytest Suite")
    
    with st.spinner("Running automated tests..."):
        cmd = [
            "./venv/bin/pytest",
            "tests/test_threading.py",
            "tests/test_classification.py",
            "tests/test_api_clients.py",
            "tests/test_api_threads.py",
            "tests/test_api_webhooks.py",
            "-v",
            "--tb=no",
            "-q"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/Users/kabeer/Downloads/TCO-email-module/backend"
        )
        
        # Display output
        st.code(result.stdout, language="text")
        
        if result.returncode == 0:
            st.success("✅ All tests passed!")
        else:
            st.warning("⚠️ Some tests failed. See output above.")


# ============================================================================
# Main Application
# ============================================================================

def main():
    st.set_page_config(
        page_title="Email Module Test Dashboard",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 Email Module - Comprehensive Test Dashboard")
    st.markdown("Interactive testing interface for all backend endpoints")
    
    # Sidebar - Configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Auth token
        token_input = st.text_input("Auth Token (User ID)", value="", type="password")
        if st.button("Set Token"):
            st.session_state.auth_token = token_input
            st.success("Token set!")
        
        if st.session_state.auth_token:
            st.info(f"✅ Token: {st.session_state.auth_token[:10]}...")
        
        st.markdown("---")
        
        # Clear results
        if st.button("🗑️ Clear Test Results"):
            st.session_state.test_results = []
            st.success("Results cleared!")
        
        # Export results
        if st.button("💾 Export Results as JSON"):
            if st.session_state.test_results:
                results_json = json.dumps(st.session_state.test_results, indent=2)
                st.download_button(
                    "Download JSON",
                    data=results_json,
                    file_name=f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    # Main tabs
    tabs = st.tabs([
        "🏥 Health & Info",
        "🧪 API Testing",
        "🤖 Automated Tests",
        "📊 Test Results",
        "📖 Documentation"
    ])
    
    # Tab 1: Health Checks
    with tabs[0]:
        st.markdown("### System Health Checks")
        if st.button("Run Health Checks"):
            run_health_checks()
    
    # Tab 2: API Testing
    with tabs[1]:
        st.markdown("### Manual API Testing")
        
        test_category = st.selectbox(
            "Select Test Suite",
            ["Client Management", "Thread Management", "Email Operations", "Webhooks", "Custom Request"]
        )
        
        if test_category == "Client Management":
            if st.button("Run Client Tests"):
                run_client_tests()
        
        elif test_category == "Thread Management":
            if st.button("Run Thread Tests"):
                run_thread_tests()
        
        elif test_category == "Email Operations":
            if st.button("Run Email Tests"):
                run_email_tests()
        
        elif test_category == "Webhooks":
            if st.button("Run Webhook Tests"):
                run_webhook_tests()
        
        elif test_category == "Custom Request":
            st.markdown("#### Custom API Request")
            
            col1, col2 = st.columns(2)
            with col1:
                method = st.selectbox("Method", ["GET", "POST", "PATCH", "DELETE"])
            with col2:
                endpoint = st.text_input("Endpoint", value="/health")
            
            if method in ["POST", "PATCH"]:
                data_input = st.text_area("Request Body (JSON)", value="{}")
                try:
                    data = json.loads(data_input)
                except:
                    data = None
                    st.error("Invalid JSON")
            else:
                data = None
            
            if st.button("Send Request"):
                result = make_api_call(method, endpoint, data=data)
                display_api_response(result, "Custom Request")
    
    # Tab 3: Automated Tests
    with tabs[2]:
        st.markdown("### Automated Pytest Suite")
        st.markdown("Run the comprehensive pytest test suite")
        
        if st.button("▶️ Run All Pytest Tests"):
            run_pytest_suite()
        
        st.markdown("---")
        st.markdown("**Test Coverage:**")
        st.markdown("""
        - ✅ Threading Engine (21 tests)
        - ✅ Classification Service (20 tests)
        - ✅ Client API (12 tests)
        - ✅ Thread Management (14 tests)
        - ✅ Webhooks (7 tests)
        - ✅ Authentication (10 tests)
        - ✅ Email Operations (13 tests)
        """)
    
    # Tab 4: Test Results
    with tabs[3]:
        st.markdown("### Test Results Summary")
        
        if st.session_state.test_results:
            df = pd.DataFrame(st.session_state.test_results)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Tests", len(df))
            with col2:
                passed = len(df[df["success"] == True])
                st.metric("Passed", passed, f"{passed/len(df)*100:.1f}%")
            with col3:
                failed = len(df[df["success"] == False])
                st.metric("Failed", failed)
            with col4:
                avg_duration = df["duration"].mean()
                st.metric("Avg Duration", f"{avg_duration:.3f}s")
            
            # Results table
            st.markdown("#### Detailed Results")
            st.dataframe(df, use_container_width=True)
            
            # Status chart
            st.markdown("#### Test Status Distribution")
            status_counts = df["success"].value_counts()
            st.bar_chart(status_counts)
        else:
            st.info("No test results yet. Run some tests to see results here.")
    
    # Tab 5: Documentation
    with tabs[4]:
        st.markdown("### API Documentation")
        
        st.markdown("""
        #### Available Endpoints
        
        **Authentication**:
        - `GET /auth/login` - Get OAuth login URL
        - `GET /auth/callback` - OAuth callback
        - `POST /auth/logout` - Logout
        - `GET /auth/me` - Get current user
        
        **Clients**:
        - `GET /clients` - List clients
        - `POST /clients` - Create client
        - `GET /clients/{id}` - Get client
        - `PATCH /clients/{id}` - Update client
        - `GET /clients/{id}/emails` - Get client emails
        - `GET /clients/{id}/threads` - Get client threads
        
        **Emails**:
        - `GET /emails` - List emails
        - `GET /emails/{id}` - Get email
        - `POST /emails` - Send email
        - `PATCH /emails/{id}` - Update email
        - `DELETE /emails/{id}` - Delete email
        - `GET /emails/sync` - Sync from Outlook
        
        **Threads**:
        - `GET /threads` - List threads
        - `GET /threads/{id}` - Get thread
        - `PATCH /threads/{id}` - Update thread
        - `POST /threads/{id}/resolve` - Resolve thread
        - `POST /threads/{id}/archive` - Archive thread
        
        **Webhooks**:
        - `GET /webhooks/status` - Get subscription status
        - `POST /webhooks/subscribe` - Create subscription
        - `DELETE /webhooks/subscribe` - Delete subscription
        
        #### Full API Documentation
        Visit: [http://localhost:8000/docs](http://localhost:8000/docs)
        """)


if __name__ == "__main__":
    main()
