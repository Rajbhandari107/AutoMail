import { useState } from "react";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

import Dashboard from "./pages/Dashboard";
import Contacts from "./pages/Contacts";
import Campaigns from "./pages/Campaigns";
import CampaignDetails from "./pages/CampaignDetails";


function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const [selectedCampaignId, setSelectedCampaignId] =
    useState(null);


  function openCampaign(campaignId) {
    setSelectedCampaignId(campaignId);
    setCurrentPage("campaign-details");
  }


  function backToCampaigns() {
    setSelectedCampaignId(null);
    setCurrentPage("campaigns");
  }


  function renderPage() {
    switch (currentPage) {

      case "contacts":
        return <Contacts />;


      case "campaigns":
        return (
          <Campaigns
            onOpenCampaign={openCampaign}
          />
        );


      case "campaign-details":
        return (
          <CampaignDetails
            campaignId={selectedCampaignId}
            onBack={backToCampaigns}
          />
        );


      case "dashboard":
      default:
        return <Dashboard />;

    }
  }


  return (
    <div className="app">

      <Sidebar
        currentPage={currentPage}
        setCurrentPage={(page) => {
          setSelectedCampaignId(null);
          setCurrentPage(page);
        }}
      />


      <main className="main-content">

        <Topbar
          currentPage={
            currentPage === "campaign-details"
              ? "campaigns"
              : currentPage
          }
        />


        <div className="page-content">
          {renderPage()}
        </div>

      </main>

    </div>
  );
}


export default App;