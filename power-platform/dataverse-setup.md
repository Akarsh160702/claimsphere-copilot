# Dataverse Tables Setup — ClaimSphere

Creates three custom tables so the backend can persist claims, documents,
and audit logs to Dataverse instead of in-memory.

---

## Step 1 — Open Power Apps

1. Go to https://make.powerapps.com
2. Make sure environment is **Sandbox AI Labs 1010**

---

## Step 2 — Create `cs_claims` table

1. **Tables → + New table → Add columns manually**
2. Table name: `Claim`  (schema name auto-fills as `cs_claim`)
3. Add these columns:

| Display name | Schema name | Type |
|---|---|---|
| Claim Number | cs_claimnumber | Single line of text |
| Policy ID | cs_policyid | Single line of text |
| Claim Type | cs_claimtype | Single line of text |
| Status | cs_status | Single line of text |
| Claimant Name | cs_claimantname | Single line of text |
| Claimant Email | cs_claimantemail | Single line of text |
| Claim Amount | cs_claimamount | Currency |
| Incident Date | cs_incidentdate | Date only |
| Channel | cs_channel | Single line of text |
| Priority | cs_priority | Single line of text |
| Fraud Score | cs_fraudscore | Whole number |
| Fraud Risk Level | cs_fraudrisklevel | Single line of text |
| Decision | cs_decision | Single line of text |
| Approved Amount | cs_approvedamount | Currency |
| Final Payout | cs_finalpayout | Currency |
| Rationale | cs_rationale | Multiple lines of text |
| Confidence Score | cs_confidencescore | Decimal number |
| STP Flag | cs_stpflag | Yes/No |
| Escalated | cs_escalated | Yes/No |
| Description | cs_description | Multiple lines of text |

4. Click **Save**

---

## Step 3 — Create `cs_claimdocuments` table

1. **Tables → + New table**
2. Table name: `Claim Document` (schema: `cs_claimdocument`)
3. Add columns:

| Display name | Schema name | Type |
|---|---|---|
| Claim ID | cs_claimid | Single line of text |
| Document Type | cs_documenttype | Single line of text |
| Blob URL | cs_bloburl | URL |
| Extracted Data | cs_extracteddata | Multiple lines of text |

4. Click **Save**

---

## Step 4 — Create `cs_claimauditlogs` table

1. **Tables → + New table**
2. Table name: `Claim Audit Log` (schema: `cs_claimauditlog`)
3. Add columns:

| Display name | Schema name | Type |
|---|---|---|
| Claim ID | cs_claimid | Single line of text |
| Agent Name | cs_agentname | Single line of text |
| Action | cs_action | Single line of text |
| Details | cs_details | Multiple lines of text |

4. Click **Save**

---

## Step 5 — Add DATAVERSE_CLIENT_SECRET to GitHub

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Click **Environments → sandbox**
3. Click **Add secret**:
   - Name: `DATAVERSE_CLIENT_SECRET`
   - Value: the client secret for your `AZURE_SANDBOX_CLIENT_ID` app registration

To find the secret:
- Azure Portal → Azure Active Directory → App registrations → find the app with client ID matching `AZURE_SANDBOX_CLIENT_ID`
- Certificates & secrets → New client secret → copy the value

---

## Step 6 — Redeploy backend

After adding the secret, go to GitHub Actions → Deploy backend (sandbox) → Run workflow.

The backend will now write all claims, documents, and audit logs to Dataverse in real time.
