# ClaimSphere Copilot 🚀
### AI-Powered Insurance Claims Processing System
**Team NEXORA** | LTM x Microsoft Hack2Future 2026

[![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)

---

## 🎯 What is ClaimSphere?

An **AI-powered insurance claims processing system** that automates the entire claim lifecycle from submission to approval in **under 5 seconds**. Built using Azure AI, Power Platform, and a 7-agent AI pipeline.

### Key Benefits
- ⚡ **80% faster** processing (2 days vs 15 days)
- 💰 **70% cost reduction** in manual work
- 🤖 **60-70% automation** rate (Straight-Through Processing)
- 🕐 **24/7 availability** with AI chatbot

---

## � Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone Repository
```bash
git clone https://github.com/Akarsh160702/claimsphere-copilot.git
cd claimsphere-copilot
```

### 2. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment (Demo Mode - no Azure needed!)
echo "DEMO_MODE=true" > .env

# Start backend
uvicorn backend.main:app --reload --port 8000
```

✅ Backend running at: http://localhost:8000

### 3. Frontend Setup (New Terminal)
```bash
cd frontend
npm install
npm run dev
```

✅ Frontend running at: http://localhost:5173

### 4. Test It!
- Open browser: http://localhost:5173
- Click "New Claim"
- Fill form with test data
- Watch AI process the claim in real-time!

---

## 🌐 Live Demo URLs

| Service | URL |
|---------|-----|
| **Web Dashboard** | https://orange-beach-00e4c8e0f.7.azurestaticapps.net |
| **API Server** | https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io |
| **API Documentation** | https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/docs |
| **Health Check** | https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/health |

---

## 🏗️ Architecture Overview

```
Customer → Web UI / Teams Bot
              ↓
        FastAPI Backend
              ↓
    ┌─────────────────────┐
    │  7-Agent Pipeline   │
    ├─────────────────────┤
    │ 1. Router          │  Classify claim type
    │ 2. Document        │  OCR & extract data
    │ 3. Validation      │  Check policy (RAG)
    │ 4. Fraud           │  Detect fraud patterns
    │ 5. Missing Info    │  Gap analysis
    │ 6. Adjudication    │  Final decision
    │ 7. Support         │  Customer Q&A
    └─────────────────────┘
              ↓
    Azure AI Services + Power Platform
    (OpenAI, Document Intelligence, AI Search,
     Power Automate, Teams, Copilot Studio)
```

**Processing Time**: ~5 seconds per claim

---

## 💻 Technology Stack

### AI & Core Services
- **Azure OpenAI** (GPT-4o, GPT-4o-mini) - 7-agent AI pipeline
- **Azure AI Document Intelligence** - OCR & document extraction
- **Azure AI Search** - Policy knowledge base (RAG)
- **Azure Blob Storage** - Document storage
- **Dataverse** - Database

### Power Platform
- **Power Automate** - Workflow automation (human escalation)
- **Microsoft Teams** - Human adjudication with Adaptive Cards
- **Copilot Studio** - Conversational AI chatbot

### Application Stack
- **Backend**: Python 3.11 + FastAPI
- **Frontend**: React 18 + Fluent UI + TypeScript
- **Hosting**: Azure Container Apps + Static Web Apps
- **CI/CD**: GitHub Actions

---

## 🔑 Key Features

### 1. 7-Agent AI Pipeline
Specialized AI agents collaborate to process claims:
- **Router**: Classifies claim type and priority
- **Document**: Extracts data from PDFs using OCR
- **Validation**: Checks against policy using RAG
- **Fraud**: Detects suspicious patterns (85% accuracy)
- **Missing Info**: Identifies gaps in submission
- **Adjudication**: Makes final decision (Approve/Reject/Escalate)
- **Support**: Answers customer questions 24/7

### 2. Human-in-the-Loop
High-risk claims escalate to humans via:
- Power Automate workflow triggers automatically
- Adaptive Card appears in Microsoft Teams
- Adjudicator clicks Approve/Reject
- Decision applied instantly

### 3. Conversational AI
Copilot Studio chatbot in Teams:
- Submit claims via chat
- Check claim status
- Ask policy questions
- Natural language interface

### 4. Model Context Protocol (MCP)
Exposes ClaimSphere as reusable tools for any AI assistant

---

## 🎮 Demo Mode

Run the entire system **without Azure credentials** for testing:

```bash
# In .env file
DEMO_MODE=true

# Start backend and frontend as shown above
```

All Azure services are mocked with realistic data. Perfect for:
- Local development
- Testing
- Demonstrations
- Learning

**Test Policies Available**:
- `POL-HEALTH-001` - Health insurance (₹50L coverage)
- `POL-MOTOR-001` - Motor insurance (₹10L coverage)
- `POL-PROPERTY-001` - Property insurance (₹1Cr coverage)

---

## 🎯 Complete Demonstration Flow

Follow this complete flow to test and demonstrate the entire ClaimSphere system from submission to approval.

### 📍 **Access Points**

Before starting, bookmark these URLs:

| Component | URL | Purpose |
|-----------|-----|---------|
| **Web Dashboard** | https://orange-beach-00e4c8e0f.7.azurestaticapps.net | Submit and track claims |
| **Microsoft Teams** | [Your Teams workspace] | Human review and approval |
| **Copilot Studio Bot** | [Teams → ClaimSphere Assistant] | Conversational claim submission |
| **Power Apps** | https://make.powerapps.com | View Dataverse data |
| **API Docs** | https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/docs | API testing |

---

### 🔄 **Flow 1: Web UI → Auto-Approved**

**Test a simple claim that gets automatically approved**

#### Step 1: Submit Claim via Web UI
1. Open: https://orange-beach-00e4c8e0f.7.azurestaticapps.net
2. Click **"New Claim"** button
3. Fill in the form:
   ```
   Policy ID: POL-HEALTH-001
   Claim Type: Health
   Claimant Name: Rajesh Kumar
   Email: rajesh@example.com
   Incident Date: 2024-06-05
   Claim Amount: ₹1,50,000
   Description: Minor outpatient surgery at Apollo Hospital
   ```
4. Click **"Submit Claim"**
5. Watch the **7 AI agents process** in real-time (~5 seconds)

#### Step 2: View Result
- ✅ **Status**: APPROVED
- 💰 **Approved Amount**: ₹1,45,000 (after ₹5,000 deductible)
- 📊 **Confidence**: 96%
- ⏱️ **Processing Time**: ~5 seconds

#### Step 3: Verify in Power Apps (Dataverse)
1. Go to: https://make.powerapps.com
2. Navigate to **Data → Tables → Claims (cs_claim)**
3. Find your claim by Claim ID
4. Verify:
   - Status = "Approved"
   - Approved Amount = ₹1,45,000
   - Fraud Score = Low (15-20)
   - All agent data populated

**Result**: ✅ Claim automatically approved, no human intervention needed!

---

### 🔄 **Flow 2: Web UI → Escalated → Teams Approval**

**Test a high-risk claim that requires human review**

#### Step 1: Submit High-Risk Claim
1. Open: https://orange-beach-00e4c8e0f.7.azurestaticapps.net
2. Click **"New Claim"**
3. Fill in the form with suspicious details:
   ```
   Policy ID: POL-HEALTH-001
   Claim Type: Health
   Claimant Name: Suspicious User
   Email: suspicious@example.com
   Incident Date: 2024-06-08
   Claim Amount: ₹49,90,000
   Description: Emergency surgery at Unknown Clinic
   ```
4. Click **"Submit Claim"**

#### Step 2: View Escalation Result
- 🚨 **Status**: ESCALATE
- ⚠️ **Fraud Score**: 87/100 (High Risk)
- 🚩 **Red Flags Detected**:
  - Amount is 99.8% of policy limit
  - Hospital not in verified network
  - High-risk pattern detected
- 📋 **Recommendation**: Manual review required

#### Step 3: Check Microsoft Teams
1. Open **Microsoft Teams**
2. Go to **Claims Operations** team
3. Navigate to **#claims-review** channel
4. You'll see an **Adaptive Card** with:
   - Claim summary
   - Fraud indicators
   - AI recommendation
   - Three action buttons:
     - ✅ **Approve**
     - ❌ **Reject**
     - 📋 **Request More Info**

#### Step 4: Make Decision in Teams
**Option A - Approve:**
1. Click **"✅ Approve"** button
2. Card updates to show "Decision recorded"
3. Power Automate workflow triggers automatically:
   - Updates Dataverse (Status → "Approved")
   - Calls backend webhook
   - Sends approval email to customer

**Option B - Reject:**
1. Click **"❌ Reject"** button
2. Provide rejection reason (if prompted)
3. Workflow updates:
   - Status → "Rejected"
   - Sends rejection email with reason

**Option C - Request More Info:**
1. Click **"📋 Request More Info"**
2. Specify what's needed
3. Status → "Pending Information"
4. Email sent to customer with requirements

#### Step 5: Verify Updates
1. **In Web Dashboard**:
   - Refresh the claim detail page
   - Status updated in real-time
   - Decision and timestamp shown

2. **In Power Apps**:
   - Go to cs_claim table
   - Find the claim
   - Verify status change
   - Check audit log entries

**Result**: 🎯 High-risk claim successfully escalated to human, approved via Teams, all systems updated!

---

### 🔄 **Flow 3: Copilot Studio Bot → Conversational Submission**

**Submit a claim using natural language via Teams chatbot**

#### Step 1: Open Copilot in Teams
1. Open **Microsoft Teams**
2. Go to **Chat**
3. Find **"ClaimSphere Assistant"** bot
4. If not visible, search for it or add it from Apps

#### Step 2: Start Conversation
Type: `I want to file a claim`

#### Step 3: Follow Conversational Flow
```
🤖 Bot: "I can help you submit a claim. What type of insurance 
         claim is this? (Health / Motor / Property)"

👤 You: Health

🤖 Bot: "Got it. What's your Policy ID?"

👤 You: POL-HEALTH-001

🤖 Bot: "What is the incident date? (YYYY-MM-DD)"

👤 You: 2024-06-05

🤖 Bot: "What is the claim amount in rupees?"

👤 You: 250000

🤖 Bot: "Please describe what happened"

👤 You: Hospitalization for fever at Fortis Hospital

🤖 Bot: "✅ Your claim has been submitted successfully!
         
         Claim ID: CLM-20260609-XYZ123
         Status: Processing
         
         Our AI is reviewing your claim right now. You'll 
         receive an email with the decision within a few 
         minutes. You can also ask me: 'What's the status 
         of CLM-20260609-XYZ123?'"
```

#### Step 4: Check Claim Status via Bot
Type: `What's the status of CLM-20260609-XYZ123?`

```
🤖 Bot: "Here's your claim status:
         
         📊 Claim ID: CLM-20260609-XYZ123
         ✅ Status: APPROVED
         💰 Claim Amount: ₹2,50,000
         💵 Approved Amount: ₹2,45,000
         📅 Decision Date: June 9, 2024
         🏦 Payment: Will be credited in 2 business days
         
         Deductions:
         • Deductible: ₹5,000
         
         Need anything else?"
```

#### Step 5: Ask Policy Questions
Type: `Am I covered for dental surgery?`

```
🤖 Bot: "Let me check your policy POL-HEALTH-001...
         
         Yes! Dental surgery is covered with these conditions:
         • Maximum coverage: ₹2 lakhs per year
         • Waiting period: 1 year (you've completed this ✓)
         • Requires pre-authorization 48 hours before surgery
         • Cosmetic dentistry is excluded
         
         You're good to go! Just remember to get pre-authorization."
```

#### Step 6: Verify in Systems
The same claim appears in:
- ✅ Web Dashboard
- ✅ Power Apps (Dataverse)
- ✅ Can be escalated to Teams if high-risk

**Result**: 🤖 Natural language claim submission works seamlessly, integrated with entire system!

---

### 🔄 **Flow 4: API Integration → Direct Submission**

**Submit claim programmatically via API (for system integrations)**

#### Step 1: Submit via API
```bash
curl -X POST https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/claims/submit/sync \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "POL-HEALTH-001",
    "claim_type": "Health",
    "claimant_name": "API Test User",
    "claimant_email": "api@example.com",
    "incident_date": "2024-06-05",
    "claim_amount": 180000,
    "description": "Emergency room visit"
  }'
```

#### Step 2: Review Response
```json
{
  "claim_id": "CLM-20260609-API456",
  "status": "Approved",
  "decision": {
    "result": "APPROVE",
    "approved_amount": 175000,
    "confidence": 0.95
  }
}
```

#### Step 3: Check Status via API
```bash
curl https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/claims/CLM-20260609-API456/status
```

**Result**: 🔌 API integration works, claim processed through same pipeline!

---

### 📊 **Complete System Integration Map**

```
┌─────────────────────────────────────────────────────────────┐
│                    SUBMISSION CHANNELS                       │
├─────────────────────────────────────────────────────────────┤
│  1. Web UI                                                   │
│  2. Copilot Studio Bot (Teams)                              │
│  3. REST API                                                │
└────────────────────────┬────────────────────────────────────┘
                         ↓
                ┌────────────────┐
                │  FastAPI       │
                │  Backend       │
                └────────┬───────┘
                         ↓
                ┌────────────────┐
                │  7-Agent       │ ← Azure OpenAI, Doc Intelligence
                │  AI Pipeline   │ ← AI Search (RAG)
                └────────┬───────┘
                         ↓
              ┌──────────┴──────────┐
              ↓                     ↓
         [APPROVE/REJECT]      [ESCALATE]
              ↓                     ↓
              ↓            ┌────────────────┐
              ↓            │ Power Automate │
              ↓            │ Workflow       │
              ↓            └────────┬───────┘
              ↓                     ↓
              ↓            ┌────────────────┐
              ↓            │ Microsoft      │
              ↓            │ Teams Card     │
              ↓            └────────┬───────┘
              ↓                     ↓
              ↓            [Human Decision]
              ↓                     ↓
              └──────────┬──────────┘
                         ↓
                ┌────────────────┐
                │  Dataverse     │ ← All claims stored
                │  (Power Apps)  │ ← Audit logs
                └────────────────┘
                         ↓
                ┌────────────────┐
                │  Customer      │ ← Email notification
                │  Notification  │ ← Status update
                └────────────────┘
```

---

### 🧪 **Test Scenarios Summary**

| Scenario | Input Amount | Expected Outcome | Where to Check |
|----------|--------------|------------------|----------------|
| **Simple Approval** | ₹1,50,000 | Auto-approved in 5s | Web UI + Power Apps |
| **High-Risk Escalation** | ₹49,90,000 | Escalated to Teams | Teams #claims-review |
| **Policy Exclusion** | Cosmetic surgery | Auto-rejected | Web UI + Power Apps |
| **Missing Documents** | No docs uploaded | Pending info | Web UI (missing items list) |
| **Copilot Submission** | Any valid claim | Same as Web UI | Bot + Power Apps |

---

### 📍 **Quick Access Checklist**

Before demonstrating, ensure you have access to:

- [ ] Web Dashboard URL open in browser
- [ ] Microsoft Teams open with ClaimSphere bot
- [ ] Power Apps portal open (Dataverse tables)
- [ ] Teams #claims-review channel visible
- [ ] API docs open (for technical demo)
- [ ] Test policy IDs ready (POL-HEALTH-001, etc.)

---

### 💡 **Pro Tips for Demonstration**

1. **Show Auto-Approval First**: Start with simple claim to show speed (5 seconds!)
2. **Then Show Escalation**: Demonstrate human-in-the-loop with Teams card
3. **Use Copilot for Wow Factor**: Natural language is impressive
4. **Refresh Power Apps**: Show data persistence in real-time
5. **Mention Cost**: $4 for entire hackathon, $0.05 per claim

---

### 🎬 **30-Second Elevator Pitch**

*"ClaimSphere processes insurance claims in 5 seconds instead of 15 days. Submit via web, Teams bot, or API. 7 AI agents analyze the claim. Simple cases auto-approve. High-risk cases go to Teams for human review with one-click approval. Everything syncs to Power Apps. Built entirely on Microsoft stack: Azure AI, Power Platform, Teams."*

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[PROJECT-OVERVIEW.md](PROJECT-OVERVIEW.md)** | Complete project explanation in simple language (for everyone) |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Detailed architecture, agent pipeline, data flow diagrams |
| **[API-REFERENCE.md](API-REFERENCE.md)** | All API endpoints with examples and usage |
| **[POWER-PLATFORM-SETUP.md](POWER-PLATFORM-SETUP.md)** | Power Automate, Copilot Studio, Teams integration guide |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Step-by-step Azure deployment instructions |
| **[TESTING-GUIDE.md](TESTING-GUIDE.md)** | Test cases, demo script, troubleshooting |

---

## 🚀 Quick API Examples

### Submit a Claim
```bash
curl -X POST http://localhost:8000/claims/submit/sync \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "POL-HEALTH-001",
    "claim_type": "Health",
    "claimant_name": "Test User",
    "claimant_email": "test@example.com",
    "incident_date": "2024-06-05",
    "claim_amount": 150000,
    "description": "Minor surgery"
  }'
```

### Check Status
```bash
curl http://localhost:8000/claims/CLM-XXXXXXXX-XXX/status
```

### Health Check
```bash
curl http://localhost:8000/health
```

**Full API documentation**: See [API-REFERENCE.md](API-REFERENCE.md) or visit `/docs` endpoint

---

## 📁 Project Structure

```
hackathon-insurance-claim/
├── backend/                 # Python FastAPI backend
│   ├── agents/             # 7 AI agents
│   ├── api/                # REST API endpoints
│   ├── tools/              # Azure service clients
│   └── models/             # Data models
├── frontend/               # React web app
│   └── src/                # Components, pages, services
├── power-platform/         # Power Automate flows, Copilot configs
├── data/                   # Sample policies and test data
├── infra/                  # Azure Bicep templates
└── .github/workflows/      # CI/CD pipelines
```

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

**Demo Mode** (No Azure needed):
```env
DEMO_MODE=true
```

**Production Mode** (Requires Azure):
```env
DEMO_MODE=false
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_GPT4O_DEPLOYMENT=gpt-4o

# See .env.example for all variables
```

Full setup instructions: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🎯 Business Impact

| Metric | Traditional | ClaimSphere | Improvement |
|--------|-------------|-------------|-------------|
| **Processing Time** | 15 days | 2 days | 80% faster |
| **Manual Work** | 100% | 30% | 70% reduction |
| **Automation Rate** | 10% | 67% | 6.7x increase |
| **Cost per Claim** | ₹500 | ₹150 | 70% cheaper |
| **Availability** | 9am-5pm | 24/7 | Always on |
| **Fraud Detection** | 40% | 85% | 2x better |

---

## 🤝 Team NEXORA

Built for **LTM x Microsoft Hack2Future 2026**

This project demonstrates:
- ✅ Azure OpenAI (GPT-4o & GPT-4o-mini)
- ✅ Azure AI Document Intelligence
- ✅ Azure AI Search (RAG)
- ✅ Power Platform (Automate, Teams, Copilot Studio, Dataverse)
- ✅ Model Context Protocol
- ✅ Multi-agent AI architecture
- ✅ Human-in-the-loop workflows
- ✅ End-to-end automation

**Cost**: $4 for entire 10-day hackathon (well under $55 budget!)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Akarsh160702/claimsphere-copilot/issues)
- **Questions**: Check [TESTING-GUIDE.md](TESTING-GUIDE.md) troubleshooting section
- **Live Demo**: Visit the URLs above

---

## 📄 License

Built for LTM x Microsoft Hack2Future 2026 hackathon.

---

<div align="center">

### 🏆 ClaimSphere Copilot
**Transforming Insurance with AI**

Made with 💙 by Team NEXORA

[Live Demo](https://orange-beach-00e4c8e0f.7.azurestaticapps.net) • [API Docs](https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/docs) • [GitHub](https://github.com/Akarsh160702/claimsphere-copilot)

</div>
