# Medical Consultation Messaging System (Nightingale)

A secure, AI-powered medical consultation platform with built-in triage, privacy redaction, and clinician-in-the-loop escalation.

## Features
- **AI Triage & Triage summaries**: Automated medical risk assessment (High, Medium, Low).
- **Living Memory**: Extracting and managing patient medical history (medications, symptoms, allergies).
- **Privacy First**: Sensitive data (NRIC, Phone) is redacted before being sent to LLMs.
- **Clinician Escalation**: High/Medium risk cases are automatically escalated to a clinician dashboard.
- **RBAC**: Secure Role-Based Access Control for Patients and Clinicians.

---

## 🚀 Setup & Run Instructions

### Prerequisites
- Python 3.11+
- Node.js & npm
- PostgreSQL

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Environment Variables**:
Create a `.env` file in the `backend` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/nightingale
SECRET_KEY=your_super_secret_key
GOOGLE_API_KEY=your_gemini_api_key
```

**Database Initialization**:
```bash
# Reset and seed initial users (patient@example.com / clinician@example.com)
python reset_db.py
```

**Run Server**:
```bash
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The app will be available at `http://localhost:5173`.

---

## 🧪 How to Run Tests

The system includes a suite of micro-tests covering core functionality.

```bash
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/
```

**Test Coverage**:
- `test_risk_escalation.py`: Verifies AI safety stops and escalation logic.
- `test_memory_mutation.py`: Verifies extraction of medical facts and state transitions.
- `test_redaction.py`: Verifies PII redaction logic.
- `test_access_control.py`: Verifies security boundaries and roles.
- `test_grounding.py`: Verifies AI citations.

---

## 🔒 Data Privacy & Redaction

**Where it happens**: [backend/app/core/privacy.py](file:///home/ardacandra/Documents/Repos/medical_consultation_messaging_system/backend/app/core/privacy.py)

The system automatically redacts PII (NRIC and Phone numbers) using regex patterns before the text is:
1. Sent to any LLM (Gemini).
2. Saved in "Redacted" columns in the database for logging.
3. Displayed in audit logs.

Raw content is kept only in encrypted-ready fields for medical record parity, but never exposed to the AI logic.

---

## 🛡️ RBAC Enforcement

**How it's enforced**: [backend/app/api/deps.py](file:///home/ardacandra/Documents/Repos/medical_consultation_messaging_system/backend/app/api/deps.py)

The system uses **JWT-based Authentication** and FastAPI dependencies to enforce roles:
- **`get_current_user`**: Validates the JWT and fetches the user from the DB.
- **`get_current_clinician`**: A dependency wrapper that ensures `user.role == "clinician"`.

Endpoints are protected by these dependencies:
- `/api/v1/chat/`: Accessible by `patient` role.
- `/api/v1/escalations/`: Accessible ONLY by `clinician` role.

---

## 🏥 Clinician Lifecycle
1. **Detection**: `RiskAnalysisService` flags a message.
2. **Escalation**: AI advice stops; an `Escalation` record is created with a triage summary.
3. **Queue**: Clinicians view the **Triage Queue** on their dashboard.
4. **Resolution**: Clinician sends a verified reply, which becomes "Ground Truth" for future AI interactions.
