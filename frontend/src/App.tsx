import { Routes, Route } from "react-router-dom";
import { Dashboard } from "@/pages/Dashboard";
import { NewClaim } from "@/pages/NewClaim";
import { ClaimsRegister } from "@/pages/ClaimsRegister";
import { ClaimDetail } from "@/pages/ClaimDetail";
import { AgentMonitor } from "@/pages/AgentMonitor";
import { PolicySearch } from "@/pages/PolicySearch";
import { ReviewQueue } from "@/pages/ReviewQueue";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { useBackendHealth } from "@/hooks/useClaimsData";

export default function App() {
  useBackendHealth();

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/intake" element={<NewClaim />} />
      <Route path="/claims" element={<ClaimsRegister />} />
      <Route path="/claims/:id" element={<ClaimDetail />} />
      <Route path="/monitor" element={<AgentMonitor />} />
      <Route path="/search" element={<PolicySearch />} />
      <Route path="/review" element={<ReviewQueue />} />
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
