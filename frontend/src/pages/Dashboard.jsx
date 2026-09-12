import { useEffect, useState } from "react";
import { getCampaigns, getContacts } from "../api/client";

function Dashboard() {
  const [contacts, setContacts] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [contactsData, campaignsData] = await Promise.all([
          getContacts(),
          getCampaigns(),
        ]);

        setContacts(contactsData);
        setCampaigns(campaignsData);
      } catch (error) {
        console.error("Failed to load dashboard:", error);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const completedCampaigns = campaigns.filter(
    (campaign) => campaign.status === "COMPLETED"
  ).length;

  const draftCampaigns = campaigns.filter(
    (campaign) => campaign.status === "DRAFT"
  ).length;

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">TOTAL CONTACTS</div>
          <div className="stat-value">
            {loading ? "—" : contacts.length}
          </div>
          <div className="stat-description">
            Contacts in your database
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">TOTAL CAMPAIGNS</div>
          <div className="stat-value">
            {loading ? "—" : campaigns.length}
          </div>
          <div className="stat-description">
            Campaigns created
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">COMPLETED</div>
          <div className="stat-value">
            {loading ? "—" : completedCampaigns}
          </div>
          <div className="stat-description">
            Campaigns completed
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">DRAFTS</div>
          <div className="stat-value">
            {loading ? "—" : draftCampaigns}
          </div>
          <div className="stat-description">
            Campaigns awaiting launch
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Recent Campaigns</h2>
              <p>Your latest outreach campaigns</p>
            </div>
          </div>

          {campaigns.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✉</div>
              <h3>No campaigns yet</h3>
              <p>Create your first campaign to get started.</p>
            </div>
          ) : (
            <div className="campaign-list">
              {campaigns.slice(0, 5).map((campaign) => (
                <div className="campaign-row" key={campaign.id}>
                  <div>
                    <strong>{campaign.name}</strong>
                    <span>Campaign #{campaign.id}</span>
                  </div>

                  <span
                    className={`badge ${campaign.status.toLowerCase()}`}
                  >
                    {campaign.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>System</h2>
              <p>AutoMail backend status</p>
            </div>
          </div>

          <div className="system-item">
            <div className="system-indicator"></div>
            <div>
              <strong>FastAPI</strong>
              <span>Backend API</span>
            </div>
            <b>Online</b>
          </div>

          <div className="system-item">
            <div className="system-indicator"></div>
            <div>
              <strong>SQLite</strong>
              <span>Database</span>
            </div>
            <b>Online</b>
          </div>

          <div className="system-item">
            <div className="system-indicator"></div>
            <div>
              <strong>Frontend</strong>
              <span>React application</span>
            </div>
            <b>Online</b>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Dashboard;