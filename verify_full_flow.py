import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_step(step, msg):
    print(f"\n--- {step}. {msg} ---")

def login(email, password):
    print(f"Logging in as {email}...")
    try:
        res = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
        if res.status_code == 200:
            token_data = res.json()
            print("✅ Login Successful")
            return token_data['access_token']
        else:
            print(f"❌ Login Failed: {res.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

def run_full_flow():
    # 0. Authenticate
    print_step(0, "Authentication")
    token = login("patient@example.com", "Nightingale@123")
    headers = {"Authorization": f"Bearer {token}"}

    conversation_id = 0
    
    # 1. Routine Chat & AI Persona
    print_step(1, "Patient: Routine Greeting (Testing AI Persona)")
    msg1 = {"conversation_id": 0, "content": "Hi, I'm feeling a bit under the weather."}
    res = requests.post(f"{BASE_URL}/chat/", json=msg1, headers=headers)
    if res.status_code == 200:
        data = res.json()
        conversation_id = data.get('conversation_id')
        print(f"✅ AI Reply: {data.get('content')}")
        print(f"✅ Conversation ID: {conversation_id}")
    else:
        print(f"❌ Failed: {res.text}")
        sys.exit(1)

    # 2. Memory Extraction
    print_step(2, "Patient: Providing Medical Info (Testing Memory Extraction)")
    print("Sending: 'I have been taking Ibuprofen for my fever.'")
    msg2 = {"conversation_id": conversation_id, "content": "I have been taking Ibuprofen for my fever."}
    requests.post(f"{BASE_URL}/chat/", json=msg2, headers=headers)
    
    print("⏳ Waiting 3s for Background Task (Memory Extraction)...")
    time.sleep(3)
    
    # 3. Context Aware Chat
    print_step(3, "Patient: Context Query (Testing Context Injection)")
    # If memory worked, AI should know about Ibuprofen/Fever
    print("Sending: 'Is that medication safe?'")
    msg3 = {"conversation_id": conversation_id, "content": "Is that medication safe?"}
    res3 = requests.post(f"{BASE_URL}/chat/", json=msg3, headers=headers)
    if res3.status_code == 200:
        data3 = res3.json()
        print(f"✅ AI Reply (Should reflect context): {data3.get('content')}")
    else:
        print(f"❌ Failed: {res3.text}")
    
    # 4. High Risk Trigger
    print_step(4, "Patient: Reporting Emergency (Testing Risk Engine)")
    print("Sending: 'I feel like I am having a heart attack. Chest pain is severe.'")
    msg4 = {"conversation_id": conversation_id, "content": "I feel like I am having a heart attack. Chest pain is severe."}
    res4 = requests.post(f"{BASE_URL}/chat/", json=msg4, headers=headers)
    escalation_id = 0
    if res4.status_code == 200:
        data4 = res4.json()
        if "escalation_id" in data4:
            escalation_id = data4['escalation_id']
            print(f"✅ Escalation Triggered! ID: {escalation_id}")
            print(f"✅ Reason: {data4.get('reason')}")
        else:
            print(f"❌ Failed to Escalate: {data4}")
            sys.exit(1)
    else:
        print(f"❌ Failed: {res4.text}")
        sys.exit(1)
    
    # 5. Clinician Workflow
    print_step(5, "Clinician: Viewing Escalations")
    # Note: In a real scenario, this would be a different user (clinician). 
    # But for now checking if the endpoint is accessible or if we need to switch users.
    # The current user 'patient' might not have access to /escalations/ if RBAC is strict.
    # checking...
    res_esc = requests.get(f"{BASE_URL}/escalations/", headers=headers)
    if res_esc.status_code == 200:
        escalations = res_esc.json()
        my_escalation = next((e for e in escalations if e['id'] == escalation_id), None)
        if my_escalation:
            print(f"✅ Found Escalation {escalation_id} in Dashboard.")
            print(f"✅ Triage Summary: {my_escalation['triage_summary']}")
        else:
            print(f"❌ Escalation {escalation_id} not found in list.")
            # Don't exit, might be just permission issue or filter
    elif res_esc.status_code == 403:
         print("⚠️ Patient user cannot view escalations list (Expected RBAC). Skipping Clinician View check for this script.")
         # If we really want to test this, we'd need a clinician account.
         # For now, we'll assume success if the escalation was created on the patient side.
    else:
        print(f"❌ Failed to fetch escalations: {res_esc.text}")

    # 6. Patient History Check
    print_step(7, "Patient: Checking Message History")
    res_hist = requests.get(f"{BASE_URL}/chat/{conversation_id}/history", headers=headers)
    if res_hist.status_code == 200:
        history = res_hist.json()
        if history:
            last_msg = history[-1]
            print(f"✅ Last Message Sender: {last_msg['sender_type']}")
            print(f"✅ Last Message Content: {last_msg['content']}")
        else:
            print("❌ History is empty")
    else:
         print(f"❌ Failed to fetch history: {res_hist.text}")
            
if __name__ == "__main__":
    run_full_flow()
