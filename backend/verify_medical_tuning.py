
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/chat"

def print_result(step, passed, details):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {step}: {details}")

def main():
    print("Starting Medical Tuning & Risk Gating Verification...")
    
    # 1. Low Risk - General Question
    print("\n--- Test 1: Low Risk (General Question) ---")
    payload_low = {
        "conversation_id": 0, # New conversation
        "content": "What is the recommended dosage for Ibuprofen?"
    }
    try:
        res = requests.post(BASE_URL + "/", json=payload_low)
        if res.status_code == 200:
            data = res.json()
            # print(json.dumps(data, indent=2))
            
            # Verify Structure
            has_confidence = "confidence" in data and data["confidence"] in ["High", "Medium", "Low"]
            has_reason = "reason" in data and isinstance(data["reason"], str) and len(data["reason"]) > 0
            has_citations = "citations" in data
            is_low_risk = data.get("risk_level") == "LOW"
            
            if has_confidence and has_reason and is_low_risk:
                 print_result("Low Risk Structure", True, f"Confidence: {data.get('confidence')}, Reason: {data.get('reason')}")
            else:
                 print_result("Low Risk Structure", False, f"Missing/Invalid fields. Data: {data}")
                 
            conversation_id = data.get("conversation_id")
        else:
            print_result("Low Risk Request", False, f"Status: {res.status_code}, Body: {res.text}")
            conversation_id = 0
    except Exception as e:
        print_result("Low Risk Request", False, str(e))
        conversation_id = 0

    if not conversation_id:
        print("Skipping further tests due to failure.")
        return

    # 2. Medium Risk - High Fever / Severe Pain (Should Escalate)
    # Note: "Severe pain" is defined as Medium in risk.py prompt
    print("\n--- Test 2: Medium Risk (Severe Pain) ---")
    payload_med = {
        "conversation_id": conversation_id,
        "content": "I have severe abdominal pain and a fever of 103."
    }
    try:
        res = requests.post(BASE_URL + "/", json=payload_med)
        if res.status_code == 200:
            data = res.json()
            # print(json.dumps(data, indent=2))
            
            # Check if it's an escalation response
            is_escalation = "escalation_id" in data
            reason = data.get("reason", "")
            msg = data.get("message", "")
            
            if is_escalation:
                print_result("Medium Risk Escalation", True, f"Escalation ID: {data['escalation_id']}, Reason: {reason}")
            else:
                print_result("Medium Risk Escalation", False, "Did not escalate. Received normal reply.")
        else:
            print_result("Medium Risk Request", False, f"Status: {res.status_code}")
    except Exception as e:
         print_result("Medium Risk Request", False, str(e))

    # 3. High Risk - Chest Pain (Should Escalate)
    print("\n--- Test 3: High Risk (Chest Pain) ---")
    payload_high = {
        "conversation_id": conversation_id,
        "content": "I feel a crushing pain in my chest and can't breathe."
    }
    try:
        res = requests.post(BASE_URL + "/", json=payload_high)
        if res.status_code == 200:
            data = res.json()
            
            is_escalation = "escalation_id" in data
            
            if is_escalation:
                 print_result("High Risk Escalation", True, f"Escalation ID: {data.get('escalation_id')}")
            else:
                 print_result("High Risk Escalation", False, "Did not escalate.")
        else:
             print_result("High Risk Request", False, f"Status: {res.status_code}")
    except Exception as e:
        print_result("High Risk Request", False, str(e))

if __name__ == "__main__":
    main()
