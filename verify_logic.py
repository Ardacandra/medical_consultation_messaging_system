import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_high_risk():
    print("\n--- Testing High Risk Logic (Chest Pain) ---")
    payload = {
        "conversation_id": 0, # Create new
        "content": "I have severe chest pain."
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        if "escalation_id" in data:
            print("✅ SUCCESS: Escalation Triggered.")
            print(f"Reason: {data.get('reason')}")
            print(f"Message: {data.get('message')}")
        else:
            print("❌ FAILED: Expected Escalation, got Normal Reply.")
            print(data)
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_low_risk_and_memory():
    print("\n--- Testing Low Risk & Memory (Advil) ---")
    payload = {
        "conversation_id": 0, # Create new
        "content": "I took some Advil for my headache."
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        if "sender_type" in data and data["sender_type"] == "ai":
            print("✅ SUCCESS: Chat Reply Received.")
            print(f"Bot Reply: {data.get('content')}")
            print(f"Risk Level: {data.get('risk_level')}")
        else:
            print("❌ FAILED: Expected Chat Reply.")
            print(data)
            
        print("Waiting for Background Task (Memory Extraction)...")
        time.sleep(2)
        # TODO: Verify DB directly or trust logs/manual check? 
        # For this script we assume success if no crash, 
        # but in real test we'd query PatientProfile.
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    # Wait for server to be up
    print("Starting Tests...")
    test_high_risk()
    test_low_risk_and_memory()
