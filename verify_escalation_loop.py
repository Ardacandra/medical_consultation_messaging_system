
import requests
import time

BASE_URL = "http://localhost:8000"

def test_escalation_loop():
    # 1. Login as patient
    print("Logging in as patient...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "patient@example.com", "password": "Nightingale@123"})
    patient_token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {patient_token}"}

    # 2. Send high-risk message
    print("Sending high-risk message...")
    msg_hit = requests.post(
        f"{BASE_URL}/api/v1/chat/",
        json={"conversation_id": 0, "content": "I am having severe crushing chest pain and I can't breathe."},
        headers=headers
    )
    data = msg_hit.json()
    print(f"Response Status: {msg_hit.status_code}")
    print(f"Response Data: {data}")

    if "escalation_id" in data:
        print("✅ Escalation triggered successfully.")
        esc_id = data["escalation_id"]
        conv_id = data["conversation_id"]
    else:
        print("❌ Escalation NOT triggered.")
        return

    # 3. Login as clinician
    print("\nLogging in as clinician...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": "clinician@example.com", "password": "Nightingale@123"})
    clinician_token = resp.json()["access_token"]
    c_headers = {"Authorization": f"Bearer {clinician_token}"}

    # 4. Check triage queue
    print("Checking triage queue...")
    resp = requests.get(f"{BASE_URL}/api/v1/escalations/?status=pending", headers=c_headers)
    escalations = resp.json()
    print(f"Found {len(escalations)} pending escalations.")
    
    found = False
    for esc in escalations:
        if esc["id"] == esc_id:
            print(f"✅ Escalation #{esc_id} found in queue.")
            print(f"Triage Summary: {esc['triage_summary']}")
            found = True
            break
    
    if not found:
        print("❌ Escalation NOT found in queue.")
        return

    # 5. Reply to escalation
    print("\nClinician replying to escalation...")
    reply_resp = requests.post(
        f"{BASE_URL}/api/v1/escalations/{esc_id}/reply",
        json={"content": "Please stay calm. I have dispatched emergency services to your location. Do not hang up."},
        headers=c_headers
    )
    print(f"Reply Status: {reply_resp.status_code}")

    # 6. Verify reply in patient history
    print("\nVerifying clinician reply in patient history...")
    time.sleep(1) # Wait for commit
    hist_resp = requests.get(f"{BASE_URL}/api/v1/chat/{conv_id}/history", headers=headers)
    history = hist_resp.json()
    
    last_msg = history[-1]
    print(f"Last message sender: {last_msg['sender_type']}")
    print(f"Last message content: {last_msg['content']}")
    
    if last_msg["sender_type"] == "clinician":
        print("✅ Clinician reply successfully verified in history.")
    else:
        print("❌ Clinician reply NOT found in history.")

if __name__ == "__main__":
    test_escalation_loop()
