# Copilot Studio Bot Setup — ClaimSphere Assistant

## Overview
ClaimSphere Assistant is a Teams bot that lets policyholders:
- Ask questions about their coverage ("Am I covered for cardiac surgery?")
- Check claim status ("What's the status of CLM-20260606-3DE38D?")
- Get claim summaries
- Escalate to a human agent

The bot connects to ClaimSphere's live backend API.

---

## Step 1 — Create the bot (5 min)

1. Go to [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com)
2. Sign in with `odl_user_XXXXXXX@sandboxailabs1010.onmicrosoft.com`
3. Click **Create** → **New copilot**
4. Name: `ClaimSphere Assistant`
5. Description: `AI-powered insurance claims assistant for Team NEXORA`
6. Language: English
7. Click **Create**

---

## Step 2 — Add HTTP Actions (15 min)

For each action below, go to **Actions → Add action → New action → HTTP request**

### Action 1: Ask a policy question

| Field | Value |
|---|---|
| Action name | `AskPolicyQuestion` |
| Description | `Answer questions about insurance policy coverage using AI` |
| Method | POST |
| URL | `https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/support/query` |
| Content-Type | `application/json` |
| Request body schema | See below |

Request body:
```json
{
  "query": "{User.Message}",
  "policy_id": ""
}
```

Response mapping:
- `answer` → output variable `PolicyAnswer`
- `sources` → output variable `Sources`

### Action 2: Check claim status

| Field | Value |
|---|---|
| Action name | `CheckClaimStatus` |
| Description | `Look up the current status of an insurance claim by ID` |
| Method | GET |
| URL | `https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/claims/{ClaimID}/status` |

Response mapping:
- `status` → `ClaimStatus`
- `decision` → `ClaimDecision`

---

## Step 3 — Add Topics

### Topic: Policy Question
- Trigger phrases:
  - "What does my policy cover?"
  - "Am I covered for [condition]?"
  - "What are the exclusions?"
  - "What is my deductible?"
- Action: Call `AskPolicyQuestion` with user message
- Response: Display `{PolicyAnswer}`

### Topic: Check Claim Status
- Trigger phrases:
  - "Check my claim"
  - "What is the status of my claim"
  - "Where is my claim [CLM-ID]?"
- Ask: "Please enter your Claim ID (e.g., CLM-20260606-3DE38D)"
- Action: Call `CheckClaimStatus` with ClaimID
- Response: "Your claim **{ClaimID}** is currently **{ClaimStatus}**. Decision: {ClaimDecision}"

### Topic: Escalate to Human
- Trigger phrases:
  - "Speak to a human"
  - "Connect me to an agent"
  - "I need help"
- Action: **Escalate** (built-in escalation to live agent)

---

## Step 4 — Connect to Teams

1. In Copilot Studio → **Channels** → **Microsoft Teams**
2. Click **Turn on Teams**
3. Click **Open bot** → it opens in Teams
4. Share the bot with your team: **Availability → Share with my organization**

---

## Step 5 — Test

In Teams, start a chat with **ClaimSphere Assistant** and try:
- "What does my health policy cover?"
- "Check claim CLM-20260606-3DE38D"
- "Am I covered for cardiac surgery?"

---

## MCP Connection (Advanced)

ClaimSphere also exposes an MCP server at:
```
https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io/mcp
```

To connect Copilot Studio to MCP tools:
1. Actions → Add action → **Model Context Protocol**
2. Server URL: the above MCP endpoint
3. This gives the bot direct access to all ClaimSphere tools
