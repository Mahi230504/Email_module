from app.database import SessionLocal
from models.email import Email

db = SessionLocal()
# Get recent emails
emails = db.query(Email).order_by(Email.created_at.desc()).limit(10).all()

print(f"Found {len(emails)} recent emails")
print("-" * 40)

# Group by thread
threads = {}
for email in emails:
    if email.thread_id not in threads:
        threads[email.thread_id] = []
    threads[email.thread_id].append(email)

for thread_id, thread_emails in threads.items():
    print(f"\nThread ID: {thread_id}")
    print(f"Count: {len(thread_emails)}")
    for email in thread_emails:
        print(f"  - [{email.direction}] {email.subject} (ID: {email.id})")
        print(f"    From: {email.from_name} <{email.from_address}>")
        print(f"    To: {email.to_recipients}")
        print(f"    Created: {email.created_at}")
    print("-" * 20)
