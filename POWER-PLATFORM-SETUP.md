# Power Platform Integration Guide

Complete setup guide for Power Automate, Copilot Studio, Microsoft Teams, and Dataverse integration.

## Table of Contents
- [Power Automate Setup](#power-automate-setup)
- [Microsoft Teams Configuration](#microsoft-teams-configuration)
- [Copilot Studio Setup](#copilot-studio-setup)
- [Dataverse Tables](#dataverse-tables)

---

## Power Automate Setup

### Flow 1: Human Escalation Workflow

**Flow Name**: `ClaimSphere - Human Escalation Flow`

**Purpose**: Automatically post escalated claims to Teams for human review

#### Flow Design

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: When a Dataverse row is modified                    │
│ Table: cs_claim                                             │
│ Condition: Status equals "Under Human Review"              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Get claim details from Dataverse                    │
│ Fields: Claim ID, Type, Amount, Fraud Score, Documents     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Post Adaptive Card to Teams Channel                 │
│ Channel: "Claims Review Team"                               │
│ Card includes:                                              │
│   • Claim summary                                           │
│   • Fraud indicators                                        │
│   • AI recommendation                                       │
│   • Action buttons: Approve / Reject / Request More Info   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Wait for User Response                              │
│ Timeout: 24 hours                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Condition - User's Decision                         │
│ If APPROVE → Go to Approve Branch                           │
│ If REJECT → Go to Reject Branch                             │
│ If REQUEST_INFO → Go to Request Info Branch                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ APPROVE      │  │ REJECT       │  │ REQUEST MORE INFO│
│ Branch       │  │ Branch       │  │ Branch           │
└──────────────┘  └──────────────┘  └──────────────────┘
        ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Update       │  │ Update       │  │ Update Status    │
│ Dataverse    │  │ Dataverse    │  │ Send Email       │
│ Call Backend │  │ Send Email   │  │ List missing     │
│ Webhook      │  │              │  │ items            │
└──────────────┘  └──────────────┘  └──────────────────┘
```

#### Setup Steps

1. **Create New Flow**
   - Go to https://make.powerautomate.com
   - Click "+ Create" → "Automated cloud flow"
   - Name: `ClaimSphere - Human Escalation Flow`

2. **Add Trigger**
   - Search for "Dataverse"
   - Select "When a row is added, modified or deleted"
   - Configure:
     - Change type: "Modified"
     - Table name: "Claims" (cs_claim)
     - Scope: "Organization"
     - Filter rows: `statuscode eq 'Under Human Review'`

3. **Add Action: Post Adaptive Card**
   - Add action → "Microsoft Teams"
   - Select "Post adaptive card and wait for a response"
   - Configure:
     - Team: Select your team
     - Channel: `Claims Review Team`
     - Message: Use the Adaptive Card JSON below
     - Update message: "Decision recorded"

4. **Add Condition: Check Response**
   - Add "Condition" action
   - Expression: `body('Post_adaptive_card')?['data']?['action']`
   - Equals: "approve" / "reject" / "request_info"

5. **Add Actions for Each Branch**
   - See detailed branch configurations below

#### Adaptive Card Template

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "Container",
      "style": "warning",
      "items": [
        {
          "type": "TextBlock",
          "text": "⚠️ HIGH-RISK CLAIM REQUIRES REVIEW",
          "weight": "Bolder",
          "size": "Large",
          "color": "Attention"
        }
      ]
    },
    {
      "type": "FactSet",
      "facts": [
        {"title": "Claim ID:", "value": "@{triggerOutputs()?['body/cs_claimnumber']}"},
        {"title": "Claimant:", "value": "@{triggerOutputs()?['body/cs_claimantname']}"},
        {"title": "Policy:", "value": "@{triggerOutputs()?['body/cs_policyid']}"},
        {"title": "Type:", "value": "@{triggerOutputs()?['body/cs_claimtype']}"},
        {"title": "Amount:", "value": "₹@{triggerOutputs()?['body/cs_claimamount']}"},
        {"title": "Fraud Score:", "value": "@{triggerOutputs()?['body/cs_fraudscore']}/100 🚨"}
      ]
    },
    {
      "type": "TextBlock",
      "text": "🚩 AI Recommendation:",
      "weight": "Bolder"
    },
    {
      "type": "TextBlock",
      "text": "@{triggerOutputs()?['body/cs_rationale']}",
      "wrap": true
    }
  ],
  "actions": [
    {
      "type": "Action.Submit",
      "title": "✅ Approve",
      "style": "positive",
      "data": {
        "action": "approve",
        "claimId": "@{triggerOutputs()?['body/cs_claimid']}"
      }
    },
    {
      "type": "Action.Submit",
      "title": "❌ Reject",
      "style": "destructive",
      "data": {
        "action": "reject",
        "claimId": "@{triggerOutputs()?['body/cs_claimid']}"
      }
    },
    {
      "type": "Action.Submit",
      "title": "📋 Request More Info",
      "data": {
        "action": "request_info",
        "claimId": "@{triggerOutputs()?['body/cs_claimid']}"
      }
    }
  ]
}
```

#### Approve Branch Actions

1. **Update Dataverse Row**
   - Table: Claims (cs_claim)
   - Row ID: `@{triggerOutputs()?['body/cs_claimid']}`
   - Fields:
     - Status: "Approved"
     - Decision: "Approve"
     - Processed Date: `@{utcNow()}`

2. **HTTP Action: Call Backend Webhook**
   - Method: POST
   - URI: `https://your-backend.com/webhooks/human-decision`
   - Body:
   ```json
   {
     "claim_id": "@{triggerOutputs()?['body/cs_claimnumber']}",
     "decision": "approve",
     "adjudicator": "@{body('Post_adaptive_card')?['responder']?['displayName']}"
   }
   ```

3. **Send Email (Approval)**
   - To: `@{triggerOutputs()?['body/cs_claimantemail']}`
   - Subject: "Your Claim has been Approved!"
   - Body: "Your claim @{triggerOutputs()?['body/cs_claimnumber']} has been approved..."

---

## Microsoft Teams Configuration

### Create Teams Structure

1. **Create Team**
   - Name: `Claims Operations`
   - Type: Private
   - Description: ClaimSphere human review team

2. **Create Channels**
   - `#claims-review` - Main escalation channel
   - `#fraud-alerts` - High-risk claims only
   - `#general` - Team coordination

3. **Add Members**
   - Add claims adjusters
   - Add supervisors
   - Set permissions

### Configure Connectors

1. Go to channel → "⋯" → "Connectors"
2. Configure "Incoming Webhook" (for backend notifications)
3. Copy webhook URL to backend `.env`:
   ```env
   TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
   ```

---

## Copilot Studio Setup

### Create ClaimSphere Assistant

1. **Go to Copilot Studio**
   - Navigate to https://copilotstudio.microsoft.com
   - Sign in with M365 credentials

2. **Create New Copilot**
   - Click "Create" → "New copilot"
   - Name: `ClaimSphere Assistant`
   - Description: "AI-powered insurance claim assistant"
   - Language: English

### Configure MCP Connection

1. **Add MCP Server**
   - Go to Settings → "Model Context Protocol"
   - Click "Add server"
   - Configuration:
     ```json
     {
       "name": "ClaimSphere Backend",
       "url": "https://your-backend.com/mcp",
       "authentication": "none"
     }
     ```

2. **Verify Tools**
   - Should see 6 tools discovered:
     - submit_claim
     - get_claim_status
     - search_policy
     - check_coverage
     - list_claims
     - get_fraud_score

### Create Topics

#### Topic 1: Submit New Claim

**Trigger Phrases**:
- "file a claim"
- "submit claim"
- "new claim"
- "I want to make a claim"

**Conversation Node**s:
1. **Ask Question**: "What type of insurance claim? (Health / Motor / Property)"
2. **Save Response**: Variable `claimType`
3. **Ask Question**: "What's your Policy ID?"
4. **Save Response**: Variable `policyId`
5. **Ask Question**: "What is the incident date? (YYYY-MM-DD)"
6. **Save Response**: Variable `incidentDate`
7. **Ask Question**: "What is the claim amount?"
8. **Save Response**: Variable `claimAmount`
9. **Ask Question**: "Please describe what happened"
10. **Save Response**: Variable `description`
11. **Call MCP Tool**: `submit_claim`
    - Parameters:
      ```
      policy_id: {policyId}
      claim_type: {claimType}
      claim_amount: {claimAmount}
      incident_date: {incidentDate}
      description: {description}
      ```
12. **Show Message**: 
    ```
    ✅ Your claim has been submitted successfully!
    
    Claim ID: {toolOutput.claim_id}
    Status: {toolOutput.status}
    
    You'll receive an email with the decision shortly.
    ```

#### Topic 2: Check Claim Status

**Trigger Phrases**:
- "check status"
- "where is my claim"
- "claim update"

**Conversation Nodes**:
1. **Ask Question**: "Please provide your Claim ID"
2. **Save Response**: Variable `claimId`
3. **Call MCP Tool**: `get_claim_status`
   - Parameters: `{claim_id: claimId}`
4. **Condition**: Check status
   - If "Approved" → Show approval message
   - If "Rejected" → Show rejection message
   - If "Processing" → Show in-progress message

#### Topic 3: Policy Q&A

**Trigger Phrases**:
- "what is covered"
- "am I covered for"
- "policy question"

**Conversation Nodes**:
1. **Ask Question**: "What would you like to know about your policy?"
2. **Save Response**: Variable `query`
3. **Ask Question**: "What's your Policy ID?"
4. **Save Response**: Variable `policyId`
5. **Call MCP Tool**: `search_policy`
   - Parameters: `{policy_id: policyId, query: query}`
6. **Show Message**: Display answer with sources

### Deploy to Teams

1. **Publish Copilot**
   - Click "Publish" button
   - Wait for publishing to complete

2. **Add to Teams**
   - Go to "Channels"
   - Click "Microsoft Teams"
   - Click "Add to Teams"
   - Select team/channels
   - Confirm

---

## Dataverse Tables

### Table 1: cs_claim (Claims)

**Display Name**: Claim  
**Plural Name**: Claims  
**Primary Column**: Claim Number (cs_claimnumber)

**Columns**:

| Column Name | Display Name | Type | Description |
|-------------|--------------|------|-------------|
| cs_claimid | Claim | GUID | Primary key (auto) |
| cs_claimnumber | Claim Number | String | CLM-YYYYMMDD-XXX |
| cs_claimtype | Claim Type | Choice | Health/Motor/Property/Travel |
| cs_status | Status | Choice | Received/Processing/Approved/Rejected/Escalated |
| cs_claimantname | Claimant Name | String | Customer name |
| cs_claimantemail | Email | Email | Contact email |
| cs_policyid | Policy ID | String | Policy number |
| cs_claimamount | Claim Amount | Currency | Requested amount |
| cs_approvedamount | Approved Amount | Currency | Final amount |
| cs_fraudscore | Fraud Score | Integer | 0-100 |
| cs_decision | Decision | Choice | Approve/Reject/Escalate |
| cs_rationale | Rationale | Multiline Text | AI explanation |
| cs_incidentdate | Incident Date | Date | When occurred |
| cs_submitteddate | Submitted Date | DateTime | When filed |
| cs_processeddate | Processed Date | DateTime | When decided |
| cs_confidencescore | Confidence | Decimal | 0.0-1.0 |
| cs_stpeligible | STP Eligible | Boolean | Auto-process flag |

**Create via Power Apps**:
1. Go to https://make.powerapps.com
2. Data → Tables → New table
3. Add columns as above
4. Save and publish

### Table 2: cs_claimdocument (Documents)

**Columns**:

| Column Name | Display Name | Type |
|-------------|--------------|------|
| cs_documentid | Document | GUID |
| cs_claimid | Claim | Lookup (cs_claim) |
| cs_documenttype | Document Type | Choice |
| cs_bloburl | Blob URL | URL |
| cs_extractionconfidence | Extraction Confidence | Decimal |
| cs_uploadeddate | Uploaded Date | DateTime |

### Table 3: cs_claimauditlog (Audit Log)

**Columns**:

| Column Name | Display Name | Type |
|-------------|--------------|------|
| cs_auditid | Audit Log | GUID |
| cs_claimid | Claim | Lookup (cs_claim) |
| cs_agentname | Agent Name | String |
| cs_action | Action | String |
| cs_timestamp | Timestamp | DateTime |
| cs_details | Details | Multiline Text (JSON) |

---

## Testing Power Platform Integration

### Test Escalation Flow

1. **Trigger Escalation**:
   ```bash
   curl -X POST http://localhost:8000/claims/submit/sync \
     -d '{"claim_amount": 4990000, ...}'
   ```

2. **Verify**:
   - Check Dataverse: Status should be "Under Human Review"
   - Check Teams: Adaptive Card should appear
   - Click "Approve" in Teams
   - Verify status updates to "Approved"

### Test Copilot

1. Open Teams
2. Find ClaimSphere Assistant bot
3. Type: "I want to file a claim"
4. Follow conversation
5. Verify claim created in backend

---

For detailed Dataverse API access from Python, see `backend/tools/dataverse.py`.
