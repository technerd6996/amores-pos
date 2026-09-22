"""
Emergency admin/shop PIN reset — run locally when the dashboard itself is unreachable.
Usage: python reset_admin.py
"""
from supabase import create_client

SUPABASE_URL = "https://zioniculywkhdfnuthcs.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inppb25pY3VseXdraGRmbnV0aGNzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDA4NTE5MiwiZXhwIjoyMTA1NjYxMTkyfQ.ogTiN35fMKhZWs12HITid0Qii9KCmpOubK7chRl0quM"

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

users = client.auth.admin.list_users()
print("\nAvailable accounts:")
for i, u in enumerate(users):
    print(f"  [{i}] {u.email}  (uid: {u.id})")

idx = int(input("\nPick account number to reset: "))
new_pin = input("New 8-character PIN: ").strip()

if len(new_pin) != 8:
    print("PIN must be exactly 8 characters. Aborted.")
else:
    target = users[idx]
    client.auth.admin.update_user_by_id(target.id, {"password": new_pin})
    print(f"\nPIN reset for {target.email}.")