import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_ai_flow():
    # 1. Start Conversation
    print("--- 1. Testing Routine Chat (AI Reply) ---")
    msg = {"conversation_id": 0, "content": "I have a mild headache."}
    res = requests.post(f"{BASE_URL}/chat/", json=msg)
    if res.status_code == 200:
        data = res.json()
        print(f"✅ AI Reply: {data.get('content')}")
        conversation_id = data.get('conversation_id')
    else:
        print(f"❌ Failed: {res.text}")
        return

    # 2. Testing Memory Extraction
    print("\n--- 2. Testing Memory Extraction (Wait for Background Task) ---")
    print("Sending: 'I took 2 Advil for the pain.'")
    msg2 = {"conversation_id": conversation_id, "content": "I took 2 Advil for the pain."}
    requests.post(f"{BASE_URL}/chat/", json=msg2)
    
    print("Waiting 5s for background task...")
    time.sleep(5) 
    
    # We don't have a direct endpoint to view profile yet, but we can infer from next chat context 
    # if we had a debug endpoint. For now, we trust the logs or just proceed.
    
    # 3. Testing High Risk (AI Reasoning)
    print("\n--- 3. Testing High Risk (AI Reasoning) ---")
    print("Sending: 'I suddenly can't breathe and my chest feels heavy.'")
    msg3 = {"conversation_id": conversation_id, "content": "I suddenly can't breathe and my chest feels heavy."}
    res3 = requests.post(f"{BASE_URL}/chat/", json=msg3)
    if res3.status_code == 200:
        data3 = res3.json()
        if "escalation_id" in data3:
            print(f"✅ High Risk Escalated! Reason: {data3.get('reason')}")
        else:
            print(f"❌ Failed to Escalate: {data3}")
    else:
        print(f"❌ Error: {res3.text}")

if __name__ == "__main__":
    test_ai_flow()
