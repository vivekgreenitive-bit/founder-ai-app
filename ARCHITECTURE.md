# 🏗️ Technical Architecture Document
## Founder AI — Closed-Loop Executive Operating System

---

## 1. System Overview & Key Design Principles

**Founder AI** is engineered as a hybrid desktop-cloud system combining **Offline-First Data Privacy** with **Cloud-Powered Scalable Intelligence**.

### Core Architectural Principles:
1. **Zero-Trust Client Security**: Master API keys (Gemini, Razorpay, Circle) are isolated in **Google Cloud Secret Manager** and invoked via serverless **Cloud Run Microservices**. Client desktop apps carry zero private secrets.
2. **Closed-Loop Execution Loop**: Diagnoses auto-populate SQLite action items. Recorded outcomes are fed back into future multi-agent context windows to enable continuous AI learning.
3. **Hybrid Inference Engine**: Local Llama 3.2-3B via Ollama for offline privacy; Google Gemini 1.5 Pro via GCP Vertex AI for deep cloud reasoning and 1:1 advisory consultation.
4. **Deterministic Governance**: All agentic payments and operational triggers pass through `PolicyEngine` with double-entry validation and emergency kill-switches.

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FOUNDER AI ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ CLIENT LAYER (PyQt6 Native Desktop OS)                                          │   │
│   │ • Executive Command Center (Today)   • AI Business Diagnosis (Diagnose)        │   │
│   │ • Actions & Outcomes Workspace       • Diagnostic Tools (Tax, Velocity, 60s)  │   │
│   │ • 1:1 GCP Advisory Chat Workspace   • 13 Proprietary Framework Library         │   │
│   └────────────────────────────────────────┬────────────────────────────────────────┘   │
│                                            │                                            │
│                                            ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ LOCAL SERVICES & PERSISTENCE LAYER                                              │   │
│   │ • CompanyProfileService (JSON)      • ActionsService (SQLite)                   │   │
│   │ • DiagnosisSessionService          • PolicyEngine & Governance                 │   │
│   │ • ConsultingService (Client)       • EntitlementService                        │   │
│   └────────────────────────────────────────┬────────────────────────────────────────┘   │
│                                            │                                            │
│                        ┌───────────────────┴───────────────────┐                        │
│                        ▼                                       ▼                        │
│   ┌────────────────────────────────────────┐  ┌─────────────────────────────────────┐  │
│   │ MULTI-AGENT REASONING PIPELINE         │  │ GOOGLE CLOUD PLATFORM (GCP)         │  │
│   │ 1. AssessmentAgent (Context & Goal)    │  │ • Cloud Run Microservices (Proxy)   │  │
│   │ 2. FrameworkSelectionAgent (13 FW)     │  │ • Vertex AI (Gemini 1.5 Pro)        │  │
│   │ 3. RAG Knowledge Retrieval             │  │ • Cloud Firestore Session DB        │  │
│   │ 4. Outcome Context Memory Injection    │  │ • Cloud Secret Manager (API Keys)   │  │
│   │ 5. Strategy & Execution Agents         │  │ • Cloud Logging & Audit Trail       │  │
│   └────────────────────────────────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Multi-Agent Reasoning Pipeline

The diagnosis engine executes a 7-stage sequential multi-agent workflow:

```
           ┌───────────────────────────────────────────────────────┐
           │                  Founder Input & Context               │
           └──────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────────────┐
           │ Stage 1: AssessmentAgent                              │
           │ Injects Profile, Quarterly Goal & Past Outcomes       │
           └──────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────────────┐
           │ Stage 2: FrameworkSelectionAgent                      │
           │ Evaluates & Auto-Selects 1 of 13 Proprietary Frameworks│
           └──────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────────────┐
           │ Stage 3: RAG Retrieval (ChromaDB Vectorstore)         │
           │ Fetches domain-specific framework knowledge           │
           └──────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────────────┐
           │ Stage 4: StrategyAgent                                │
           │ Generates root cause diagnosis & bottleneck tax       │
           └──────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────────────┐
           │ Stage 5: ExecutionAgent                               │
           │ Formulates SMART priority action items                │
           └──────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────────────┐
           │ Stage 6: GovernanceAgent / PolicyEngine               │
           │ Validates agentic payment triggers against limits     │
           └──────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────────────┐
           │ Stage 7: CompositionAgent & PDF Exporter              │
           │ Renders markdown report + generates shareable PDF     │
           └───────────────────────────────────────────────────────┘
```

---

## 4. Security & Zero-Trust Cloud Architecture

### 4.1 Zero-Trust Client Model
Client desktop applications **never store master API keys**. 

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      SECURE ZERO-TRUST PROXY PATTERN                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [ Desktop Client App ]                                                  │
│   - Holds zero private keys inside executable code                       │
│   - Authenticates with HMAC Founder Token (`usr_...`)                     │
│                                                                          │
│                         │                                                │
│                         │ HTTPS POST (TLS 1.3)                           │
│                         ▼                                                │
│   ┌──────────────────────────────────────────────────────────┐           │
│   │ Google Cloud Run Serverless Gateway                      │           │
│   │ - Validates HMAC Signature                               │           │
│   │ - Accesses Cloud Secret Manager                          │           │
│   │ - Invokes Gemini 1.5 Pro / Razorpay API                  │           │
│   └──────────────────────────┬───────────────────────────────┘           │
│                              │                                           │
│                              ▼                                           │
│                 GCP Vertex AI / Payment Gateways                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Cryptographic Session Tokens
- **Founder Token**: `usr_` + `HMAC-SHA256(founder_email, APP_SECRET_SALT)[:16]`
- **Session Token**: `cs_` + `UUIDv4`

---

## 5. Database Schema & Data Models

### 5.1 Local SQLite Schema (`~/.founder_ai/conversation_history.db`)

#### `action_items` Table
```sql
CREATE TABLE IF NOT EXISTS action_items (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    action_text TEXT NOT NULL,
    status TEXT CHECK(status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    outcome_notes TEXT,
    metric_impact TEXT
);
```

#### `diagnosis_sessions` Table
```sql
CREATE TABLE IF NOT EXISTS diagnosis_sessions (
    session_id TEXT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_summary TEXT,
    framework_used TEXT NOT NULL,
    primary_constraint TEXT,
    confidence_score REAL,
    evidence_count INTEGER
);
```

---

### 5.2 Google Cloud Firestore Schema (Advisory Sessions)

```json
/founders/{founder_token}: {
  "email_hash": "sha256(email)",
  "plan": "PRO",
  "created_at": "2026-08-10T12:00:00Z"
}

/sessions/{session_id}: {
  "founder_token": "usr_8477a57f2751f208",
  "created_at": "2026-08-10T12:05:00Z",
  "messages": [
    {
      "id": "msg_9f2a",
      "sender": "founder",
      "text": "How do I cut my $9.7k Bottleneck Tax?",
      "timestamp": "13:34"
    },
    {
      "id": "msg_b31c",
      "sender": "advisor",
      "text": "Focus first on delegating operational tasks...",
      "timestamp": "13:34"
    }
  ]
}
```

---

## 6. Governed Agentic Payments Architecture

The `PolicyEngine` (`db/governance.py`) enforces strict double-entry ledger security for autonomous agent payments:

- **Transaction Threshold**: Hard cap of **$50.00** per individual agent transaction.
- **Monthly Limit**: Hard cap of **$500.00** cumulative per month.
- **Vendor Allowlists**: Only authorized domain providers (*e.g. AWS, GCP, Zoom, Razorpay*) are permitted.
- **Circuit Breaker**: Instant suspension of payment capabilities if 2 consecutive invalid requests occur.
- **Human Handoff Modal**: Any payment exceeding threshold triggers `PaymentApprovalDialog` requiring explicit founder confirmation.

---

## 7. Performance SLAs & System Constraints

| Operation | SLA Target | Actual Performance | Optimization Method |
|---|---|---|---|
| **Local Diagnosis Generation** | < 4.0s | ~2.4s | Local Llama 3.2-3B via Ollama |
| **GCP Advisory Chat Response** | < 2.0s | ~1.1s | Cloud Run + Vertex AI Gemini 1.5 Flash |
| **Customer Intelligence API** | < 3.0s | ~1.6s | Structured JSON Prompting |
| **PDF Report Export** | < 1.0s | ~0.3s | Native `fpdf2` Binary Stream |
| **UI Frame Rate** | 60 FPS | 60 FPS | PyQt6 Event Loop + Async QThreads |
