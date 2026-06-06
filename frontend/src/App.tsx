import { Routes, Route } from "react-router-dom";
import { Landing } from "@/pages/Landing";
import { Dashboard } from "@/pages/Dashboard";
import { NewClaim } from "@/pages/NewClaim";
import { ClaimsRegister } from "@/pages/ClaimsRegister";
import { ClaimDetail } from "@/pages/ClaimDetail";
import { AgentMonitor } from "@/pages/AgentMonitor";
import { PolicySearch } from "@/pages/PolicySearch";
import { ReviewQueue } from "@/pages/ReviewQueue";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { useBackendHealth, useClaimsData } from "@/hooks/useClaimsData";

export default function App() {
  useBackendHealth();
  useClaimsData(); // keeps dataSource ("live"/"synthetic") accurate on all pages

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard" element={<Dashboard />} />
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
