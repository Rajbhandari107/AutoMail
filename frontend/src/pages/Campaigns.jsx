import { useEffect, useState } from "react";
import { getCampaigns } from "../api/client";

function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCampaigns() {
      try {
        const data = await getCampaigns();
        setCampaigns(data);
      } catch (error) {
        console.error("Failed to load campaigns:", error);
      } finally {
        setLoading(false);
      }
    }

    loadCampaigns();
  }, []);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Campaigns</h2>
          <p>Create and manage your email outreach</p>
        </div>

        <button className="primary-button">
          + New Campaign
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading campaigns...</div>
      ) : campaigns.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✉</div>
          <h3>No campaigns</h3>
          <p>Create your first campaign to begin.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>CAMPAIGN</th>
                <th>STATUS</th>
                <th>TEMPLATE</th>
                <th>DELAY</th>
              </tr>
            </thead>

            <tbody>
              {campaigns.map((campaign) => (
                <tr key={campaign.id}>
                  <td>#{campaign.id}</td>
                  <td>{campaign.name}</td>
                  <td>
                    <span
                      className={`badge ${campaign.status.toLowerCase()}`}
                    >
                      {campaign.status}
                    </span>
                  </td>
                  <td>{campaign.template || "—"}</td>
                  <td>
                    {campaign.delay_seconds ?? "—"} sec
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default Campaigns;