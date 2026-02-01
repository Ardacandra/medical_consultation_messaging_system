import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_escalation_flow():
    print("--- Testing Escalation Flow ---")
    
    # 1. Trigger High Risk (Chest Pain)
    print("1. Sending High Risk Message...")
    resp = requests.post(f"{BASE_URL}/chat/", json={"conversation_id": 0, "content": "I have chest pain"})
    if resp.status_code != 200:
        print("❌ FAILED: Chat endpoint error", resp.text)
        return
    
    data = resp.json()
    if "escalation_id" not in data:
        print("❌ FAILED: Expected escalation_id")
        return
        
    escalation_id = data["escalation_id"]
    print(f"✅ Escalation Triggered: ID {escalation_id}")
    
    # 2. List Escalations
    print("2. Listing Escalations...")
    resp = requests.get(f"{BASE_URL}/escalations/")
    escalations = resp.json()
    pending = [e for e in escalations if e["id"] == escalation_id]
    if not pending:
        print("❌ FAILED: New escalation not found in list")
        return
    print(f"✅ Escalation found in list: {pending[0]['triage_summary']}")
    
    # 3. Clinician Reply
    print("3. Clinician Replying...")
    reply_payload = {"content": "Please stay calm, an ambulance is on the way."}
    resp = requests.post(f"{BASE_URL}/escalations/{escalation_id}/reply", json=reply_payload)
    if resp.status_code != 200:
        print("❌ FAILED: Reply endpoint error", resp.text)
        return
    
    msg_data = resp.json()
    if msg_data["sender_type"] != "clinician":
        print("❌ FAILED: Message sender_type != clinician")
        return
    print("✅ Reply Sent Successfully (Sender: Clinician)")
    
    # 4. Verify History (Polling Sim)
    print("4. Verifying Chat History...")
    conv_id = data["conversation_id"] # Should be persisted from first call logic? Wait, first call returns it?
    # Actually escalation response implies conversation exists.
    # The API might not return conversation_id in EscalationResponse? Let's check schema.
    # EscalationResponse has conversation_id? No, let's check.
    # Schema check:
    # class EscalationResponse(BaseModel): message: str, escalation_id: int, reason: str
    # It misses conversation_id! I need to add it to schema or fetch from escalation list.
    # List escalation returns conversation_id.
    conv_id_from_list = pending[0]["conversation_id"]
    
    resp = requests.get(f"{BASE_URL}/chat/{conv_id_from_list}/history")
    history = resp.json()
    last_msg = history[-1]
    if last_msg["sender_type"] == "clinician" and "ambulance" in last_msg["content"]:
        print("✅ History Verified: Clinician message present.")
    else:
        print(f"❌ FAILED: Clinician message not at end of history. Last: {last_msg}")

if __name__ == "__main__":
    test_escalation_flow()
