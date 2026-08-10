# 📑 Product Requirement Document (PRD v3.0)
## Founder AI — Closed-Loop Executive Operating System

---

## 1. Executive Summary

### 1.1 Product Vision
**Founder AI** is a production-grade, closed-loop executive operating platform designed specifically for startup founders, CEOs, and executive leaders. 

Unlike generic AI chatbots (like ChatGPT or Claude) that deliver one-off text answers, Founder AI acts as an **AI Co-Founder & Fractional Chief Operating Officer (COO)**. It pairs 13 proprietary structured business frameworks with an evidence-backed multi-agent engine, quantitative diagnostic tools, an automated action tracker, a continuous learning outcome loop, Customer Intelligence, and a 1:1 Google Cloud-secured advisory chat workspace.

### 1.2 The Core Problem
Most founders fail not due to a lack of effort, but due to **misaligned execution**:
1. **Diagnosis Failure**: Founders treat surface symptoms (*e.g. "We need more marketing"*) rather than root constraints (*e.g. "Onboarding friction causes 40% 7-day drop-off"*).
2. **Founder Micromanagement Tax**: Founders spend 15–25 hours/week on low-leverage operational tasks instead of high-value strategic growth.
3. **Open-Loop Execution**: Strategic advice remains trapped in static documents without follow-up, outcome measurement, or learning.

### 1.3 The Solution Loop
$$\text{Connect Business Data} \longrightarrow \text{Diagnose Bottleneck} \longrightarrow \text{Auto-Extract Actions} \longrightarrow \text{Execute & Measure} \longrightarrow \text{AI Learns from Outcomes}$$

---

## 2. Target User Personas

| Persona | Description | Primary Pain Point | Desired Outcome |
|---|---|---|---|
| **Early-Stage Founder (0 to 1)** | Solopreneur / Co-founders (Pre-seed to Seed) | Overwhelmed by generic advice; lacks structured frameworks | Clear 1-page diagnosis and prioritized action items |
| **Growth CEO (1 to 10)** | Managing a team of 5–25 employees ($10k-$100k MRR) | Bogged down in operations (Founder Tax > $10k/mo) | Quantified bottleneck financial audit and delegation plan |
| **Bootstrapped Founder** | Focused on profitability & cash runway | Needs evidence-backed decisions without hiring a $200k/yr COO | Fast decision cycle time and execution velocity tracking |

---

## 3. System Architecture & Technical Stack

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                               FOUNDER AI SYSTEM ARCHITECTURE                          │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   ┌───────────────────────────────────────────────────────────────────────────────┐   │
│   │ DESKTOP & WORKSPACE SHELL (PyQt6 / QSS Design System)                         │   │
│   └───────────────────────────────────────┬───────────────────────────────────────┘   │
│                                           │                                           │
│                                           ▼                                           │
│   ┌───────────────────────────────────────────────────────────────────────────────┐   │
│   │ SERVICES & PERSISTENCE LAYER                                                  │   │
│   │ • CompanyProfileService        • DiagnosisSessionService                      │   │
│   │ • ActionsService (SQLite)      • EntitlementService                           │   │
│   │ • GovernanceService            • ConsultingService (GCP Vertex AI)            │   │
│   └───────────────────────────────────────┬───────────────────────────────────────┘   │
│                                           │                                           │
│                                           ▼                                           │
│   ┌───────────────────────────────────────────────────────────────────────────────┐   │
│   │ MULTI-AGENT REASONING PIPELINE                                                │   │
│   │ Assessment ──► Framework Selection ──► RAG Retrieval ──► Memory Context        │   │
│   │               ──► Strategy Agent ──► Execution Agent ──► Composition Agent    │   │
│   └───────────────────────────────────────┬───────────────────────────────────────┘   │
│                                           │                                           │
│                                           ▼                                           │
│   ┌───────────────────────────────────────┬───────────────────────────────────────┐   │
│   │ LOCAL AI ENGINE (Llama 3.2-3B)        │ CLOUD AI ENGINE (Google Gemini 1.5)  │   │
│   │ 100% Offline Privacy Mode             │ Cloud Pro Mode & Advisory Chat        │   │
│   └───────────────────────────────────────┴───────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Technology Stack
- **UI Framework**: Python 3.14 + PyQt6 (Native Cross-Platform Desktop OS).
- **Design Tokens**: Custom CSS/QSS tokens (`ui/theme.py`) matching `#1a7a3c` Forest Green brand palette.
- **Local AI Inference**: LangChain + Llama 3.2-3B via Ollama / HuggingFace Embeddings + ChromaDB.
- **Cloud AI Inference**: Google Cloud Vertex AI / Gemini 1.5 Pro via `google-genai` SDK and Cloud Run Proxy.
- **Persistence**: Local SQLite (`~/.founder_ai/conversation_history.db`) for zero-cloud data leaks.
- **Payment & Cloud Gateway**: Razorpay REST API + Google Cloud Run zero-trust payment microservice.
- **Document Processing**: PyPDF2, pandas, docx, CSV/TXT text extractors.
- **PDF Generation**: `fpdf2` PDF report engine.

---

## 4. Product Modules & Screen Specifications

The platform is organized into **10 dedicated workspaces** across 4 main sidebar navigation sections:

```
FOUNDER AI

CORE JOURNEY
  1. Today                      Executive Command Center & Key Metrics
  2. Diagnose                   Framework-Backed AI Business Diagnosis
  3. Actions                    Interactive Action Item Tracker
  4. Outcomes                   Execution History & Metric Validation Log

DIAGNOSTIC TOOLS
  5. Bottleneck Tax Calculator  Quantified Dollar Leak ($/mo) Calculator
  6. Execution Velocity Grader  0–100 Operational Velocity Scorecard
  7. 60s Bottleneck Diagnostic  5-Domain Operational Bottleneck Diagnostic

KNOWLEDGE & DATA
  8. Frameworks                 13 Proprietary Founder Framework Library
  9. Business Data              Attach P&L, CSV, and Customer Context Files

SUPPORT & ADVISORY
  10. 💬 Advisory Chat         1:1 GCP-Powered Strategic Co-Pilot Chat
```

---

### 4.1 Core Journey Workspaces

#### 1. Today (Executive Command Center)
- **Purpose**: Answers the founder's daily question: *"What needs my attention right now?"*
- **Features**:
  - **Top Metric Cards**:
    - 💰 **Bottleneck Tax**: Monthly financial leak calculation (*e.g. $9,742/mo*).
    - ⚡ **Execution Velocity**: 0–100 operational speed score (*e.g. 85/100*).
    - 🎯 **Open Actions**: Total active pending/in-progress items.
  - **Proactive AI Follow-up**: Prompts founder on open action items from previous diagnoses.
  - **Recent Diagnoses**: Quick access cards for past session constraints.

#### 2. Diagnose (AI Business Diagnosis)
- **Purpose**: Evidence-backed root cause analysis using 13 proprietary frameworks.
- **Features**:
  - Focus Area Selector pills (*All, Revenue & Sales, Customer & Churn, Product & Operations, Execution*).
  - Document Context Uploader (CSV, PDF, P&L statements).
  - **Customer Intelligence Button**: Runs Gemini structured persona & competitive gap analysis.
  - Executive 5-Section Markdown Output with **`📋 Copy`** and **`📄 Export PDF`** buttons.

#### 3. Actions (Execution Workspace)
- **Purpose**: Manages auto-extracted action items to close the loop between strategy and work.
- **Features**:
  - Auto-extracts action items from section `## 5. Priority Actions` of every diagnosis.
  - Tabbed views: **Pending**, **In Progress**, **Completed**.
  - `Start Working` button moves items to *In Progress*.
  - `Record Outcome` modal captures qualitative notes and quantitative metrics (*e.g. "Conversion up 12%"*).

#### 4. Outcomes (Performance Log)
- **Purpose**: Audit log of verified execution metrics.
- **Features**:
  - Formats past results into `ActionsService.build_outcome_context()`.
  - Automatically injects past outcomes into `AssessmentAgent` for future AI diagnoses.

---

### 4.2 Diagnostic Tools

#### 5. Founder Bottleneck Tax Calculator
- **Purpose**: Quantifies the financial leak caused by founder micromanagement.
- **Formula**:
  $$\text{Monthly Tax} = (\text{Low Leverage Hours/wk} \times 4.33) \times \text{Hourly Rate}$$
- **Features**:
  - Inputs: Target Hourly Value ($/hr), Low-Leverage Hours/wk, Monthly Revenue.
  - Outputs: Monthly Tax ($), Annualized Leak ($), Severity Grade (Critical, High, Moderate, Low).
  - `⚡ Generate AI Delegation Plan` button auto-fills `Diagnose` with a prompt to recover lost hours.

#### 6. Execution Velocity Grader
- **Purpose**: Measures startup execution speed (0–100).
- **Formula**:
  $$\text{Velocity Score} = (0.4 \times \text{Completion Rate}) + (0.4 \times \text{Speed Factor}) + (0.2 \times \text{Evidence Ratio})$$
- **Features**:
  - Real-time meter progress bar.
  - Metrics breakdown: Completed Actions count, Completion Rate %, Avg Cycle Time (Days).
  - Status badges (**High Velocity 🚀**, **Moderate Velocity ⚡**, **Execution Bottleneck ⚠️**).

#### 7. 60-Second Business Bottleneck Diagnostic
- **Purpose**: 5-domain questionnaire isolating the #1 growth constraint.
- **Domains**: Delegation, Operations, Sales Pipeline, Customer Churn, Cashflow Runway.
- **Features**:
  - Instant analysis pinpointing primary bottleneck domain.
  - Recommends matching Founder Framework (*ADMINS ER, RUN DCMS ER, PFA SAAS SME, etc.*) with 1-click diagnostic trigger.

---

### 4.3 Support & Advisory

#### 8. 💬 Advisory Chat (1:1 GCP Advisory Workspace)
- **Purpose**: Direct confidential consultation powered by Google Cloud Vertex AI & Gemini 1.5 Pro.
- **Security & Cryptography**:
  - SHA-256 HMAC `founder_token` (`usr_...`) generated from founder email.
  - Cryptographic session IDs (`cs_...`).
- **Features**:
  - Auto-injects company stage, quarterly goal, Bottleneck Tax ($), and Velocity Score into system prompt.
  - Preset Quick Prompt Pills (*Fix Bottleneck Tax*, *Accelerate Velocity*, *Align Quarterly Goal*).
  - Async non-blocking worker thread execution.

---

## 5. The 13 Proprietary Founder Frameworks

Founder AI incorporates 13 specialized frameworks designed by Founder Frameworks Lab:

| Framework Code | Name | Primary Focus Domain |
|---|---|---|
| **ECG KISS** | Early Customer Growth | Pre-revenue to $1k MRR customer acquisition |
| **SLR CAMERAS** | Systematic Lead Retention | Sales pipeline conversion & retention |
| **ADMINS ER** | Founder Delegation & Admin | Recovering founder hours from low-leverage tasks |
| **RUN DCMS ER** | Revenue Engine Scaling | Scaling sales teams & GTM channels |
| **PFA SAAS SME** | Product-Fit & Retention | SaaS churn reduction & onboarding optimization |
| **OKS REC SME** | Operational Efficiency | Operations, SOPs, and process automation |
| **PS ERP** | Process Standardization | Scaling team workflows & governance |
| *(+6 Additional)* | Enterprise Growth Suite | Capital allocation, hiring, risk mitigation |

---

## 6. Governed Agentic Payments Architecture

Founder AI includes a policy-governed execution layer for agentic transactions:

- **PolicyEngine**: Enforces max transaction limits (*default $50/txn*), monthly caps (*$500/mo*), vendor allowlists, and double-entry ledger validation.
- **Emergency Circuit Breaker**: Instant kill-switch suspending all automated agent payment privileges.
- **Human-in-the-Loop Handoff**: Any transaction exceeding policy limits requires explicit founder approval via modal dialog.

---

## 7. Monetization & 3-Tier SaaS Subscription Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              3-TIER SUBSCRIPTION MATRIX                                 │
├──────────────────────────┬──────────────────────────────┬───────────────────────────────┤
│ FREE STARTER ($0/mo)     │ FOUNDER PRO ($49/mo)         │ ENTERPRISE GROWTH ($199/mo)   │
├──────────────────────────┼──────────────────────────────┼───────────────────────────────┤
│ • 2 Core Frameworks      │ • All 13 Frameworks          │ • Everything in Pro Plan      │
│ • Local Llama 3.2 AI     │ • Google Gemini 1.5 Pro AI   │ • Multi-user Team Workspace   │
│ • Basic Actions Tracker  │ • Customer Intelligence      │ • Custom SOP Generator        │
│ • Bottleneck Tax Calc    │ • 1:1 GCP Advisory Chat      │ • Governed Agentic Payments   │
│                          │ • PDF Report Exports         │ • Dedicated Human Advisor     │
└──────────────────────────┴──────────────────────────────┴───────────────────────────────┘
```

- **Checkout Gateway**: Razorpay REST API + Google Cloud Run zero-trust payment microservice (`CLOUD_RUN_PAYMENT_URL`).

---

## 8. Non-Functional Requirements & Security Matrix

### 8.1 Performance & Reliability
- **Local Diagnosis Latency**: < 3.5 seconds on M-series Mac / i7 PC.
- **Cloud Advisory Chat Latency**: < 1.8 seconds via GCP Cloud Run / Vertex AI.
- **UI Responsiveness**: 60 FPS Qt event loop (async QThread execution for all heavy AI operations).

### 8.2 Security & Data Privacy Matrix
- **Zero-Cloud Local Mode**: All CSVs, P&L Statements, and SQLite data stored locally in `~/.founder_ai`.
- **GCP Enterprise Terms**: Cloud chat data sent to Vertex AI is encrypted in-transit (TLS 1.3) and at-rest (AES-256) and **never used to train public LLM models**.
- **HMAC Founder Hashing**: Raw founder emails are hashed via SHA-256 HMAC before generating cloud session tokens.
- **Zero-Trust Cloud Run Proxies**: Private API key secrets (Razorpay Secret Key, Master Gemini API Key) remain isolated in GCP Secret Manager.

---

## 9. Verification & Quality Assurance

- **Unit Test Suite**: 42 automated unit tests covering all agents, services, databases, and UI screens.
- **Coverage**: 100% pass rate across failure handling, navigation synchronization, closed-loop persistence, payment policy enforcement, and diagnostic calculators.
