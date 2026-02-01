import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_step(step, msg):
    print(f"\n--- {step}. {msg} ---")

def run_full_flow():
    conversation_id = 0
    
    # 1. Routine Chat & AI Persona
    print_step(1, "Patient: Routine Greeting (Testing AI Persona)")
    msg1 = {"conversation_id": 0, "content": "Hi, I'm feeling a bit under the weather."}
    res = requests.post(f"{BASE_URL}/chat/", json=msg1)
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
    requests.post(f"{BASE_URL}/chat/", json=msg2)
    
    print("⏳ Waiting 3s for Background Task (Memory Extraction)...")
    time.sleep(3)
    
    # 3. Context Aware Chat
    print_step(3, "Patient: Context Query (Testing Context Injection)")
    # If memory worked, AI should know about Ibuprofen/Fever
    print("Sending: 'Is that medication safe?'")
    msg3 = {"conversation_id": conversation_id, "content": "Is that medication safe?"}
    res3 = requests.post(f"{BASE_URL}/chat/", json=msg3)
    if res3.status_code == 200:
        data3 = res3.json()
        print(f"✅ AI Reply (Should reflect context): {data3.get('content')}")
    
    # 4. High Risk Trigger
    print_step(4, "Patient: Reporting Emergency (Testing Risk Engine)")
    print("Sending: 'I feel like I am having a heart attack. Chest pain is severe.'")
    msg4 = {"conversation_id": conversation_id, "content": "I feel like I am having a heart attack. Chest pain is severe."}
    res4 = requests.post(f"{BASE_URL}/chat/", json=msg4)
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
    
    # 5. Clinician Workflow
    print_step(5, "Clinician: Viewing Escalations")
    res_esc = requests.get(f"{BASE_URL}/escalations/")
    if res_esc.status_code == 200:
        escalations = res_esc.json()
        my_escalation = next((e for e in escalations if e['id'] == escalation_id), None)
        if my_escalation:
            print(f"✅ Found Escalation {escalation_id} in Dashboard.")
            print(f"✅ Triage Summary: {my_escalation['triage_summary']}")
        else:
            print(f"❌ Escalation {escalation_id} not found in list.")
            sys.exit(1)

    print_step(6, "Clinician: Replying to Patient")
    reply_payload = {"content": "This is Nurse Sarah. Please call 911 immediately. I am engaging emergency protocol."}
    res_reply = requests.post(f"{BASE_URL}/escalations/{escalation_id}/reply", json=reply_payload)
    if res_reply.status_code == 200:
        print("✅ Clinician Reply Sent Successfully.")
    else:
        print(f"❌ Failed to reply: {res_reply.text}")

    # 6. Patient History Check
    print_step(7, "Patient: Checking Message History")
    res_hist = requests.get(f"{BASE_URL}/chat/{conversation_id}/history")
    if res_hist.status_code == 200:
        history = res_hist.json()
        last_msg = history[-1]
        print(f"✅ Last Message Sender: {last_msg['sender_type']}")
        print(f"✅ Last Message Content: {last_msg['content']}")
        
        if last_msg['sender_type'] == 'clinician':
            print("\n🎉 SUCCESS: Full End-to-End Cycle Verified!")
        else:
            print("\n❌ FAILED: Last message was not from clinician.")
            
if __name__ == "__main__":
    run_full_flow()
