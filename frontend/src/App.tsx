import { Routes, Route } from "react-router-dom";
import { Dashboard } from "@/pages/Dashboard";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { useBackendHealth } from "@/hooks/useClaimsData";

export default function App() {
  // Poll backend health globally so the sidebar/topbar reflect connectivity.
  useBackendHealth();

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route
        path="/intake"
        element={
          <PlaceholderPage
            title="New Claim Intake"
            subtitle="Multi-step intake wizard with document auto-extraction"
            blurb="A guided wizard for submitting claims across channels, with drag-and-drop document upload and a live Azure Document Intelligence extraction preview before submission."
            planned={[
              "Channel select → upload → extraction preview → submit",
              "Drag-and-drop upload to POST /documents/upload",
              "Real-time pipeline view via POST /claims/submit",
            ]}
          />
        }
      />
      <Route
        path="/claims"
        element={
          <PlaceholderPage
            title="Claims Register"
            subtitle="Searchable, filterable register of all claims"
            blurb="The full claims registry backed by a virtualized TanStack table — search, filter by type/decision, sort, and drill into any claim."
            planned={[
              "Virtualized table over GET /claims/",
              "Filters: type, decision, fraud range, channel",
              "Row click → Claim Detail view",
            ]}
          />
        }
      />
      <Route
        path="/claims/:id"
        element={
          <PlaceholderPage
            title="Claim Detail"
            subtitle="Agent timeline, documents, adjudication reasoning"
            blurb="A complete view of a single claim: the agent action timeline, extracted documents, fraud gauge, and the adjudication rationale, with approve / reject / escalate controls."
            planned={[
              "Agent trace from GET /claims/{id}/full",
              "Fraud gauge + adjudication reasoning panel",
              "POST /claims/{id}/human-decision actions",
            ]}
          />
        }
      />
      <Route
        path="/monitor"
        element={
          <PlaceholderPage
            title="Agent Activity Monitor"
            subtitle="Real-time view of the multi-agent pipeline"
            blurb="A live feed of which of the seven agents are active, their processing steps, confidence scores, and token usage per claim."
            planned={[
              "Live agent status (SSE / polling)",
              "Per-agent confidence + token cost",
              "Pipeline throughput timeline",
            ]}
          />
        }
      />
      <Route
        path="/search"
        element={
          <PlaceholderPage
            title="Policy RAG Search"
            subtitle="Semantic search over the policy knowledge base"
            blurb="A semantic search experience for CSR agents, powered by Azure AI Search vector retrieval over policy documents, with cited passages."
            planned={[
              "Semantic query over Azure AI Search",
              "Cited source passages",
              "Grounded answers via /support/query",
            ]}
          />
        }
      />
      <Route
        path="/review"
        element={
          <PlaceholderPage
            title="Human Review Queue"
            subtitle="Escalated claims awaiting adjudicator decision"
            blurb="The human-in-the-loop queue: escalated claims surfaced as decision cards, mirrored to Microsoft Teams adaptive cards via Power Automate."
            planned={[
              "Escalated claims as decision cards",
              "Approve / reject / request-info actions",
              "Teams adaptive card parity",
            ]}
          />
        }
      />
      <Route
        path="*"
        element={
          <PlaceholderPage
            title="Page Not Found"
            subtitle="The page you requested does not exist"
            blurb="Use the navigation on the left to return to the dashboard."
            planned={[]}
          />
        }
      />
    </Routes>
  );
}
