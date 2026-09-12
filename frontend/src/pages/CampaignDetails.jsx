import { useEffect, useState } from "react";

import {
  getCampaign,
  dryRunCampaign,
  removeCampaignRecipient,
} from "../api/client";


function CampaignDetails({
  campaignId,
  onBack,
}) {
  const [campaign, setCampaign] = useState(null);

  const [loading, setLoading] = useState(true);

  const [dryRunning, setDryRunning] = useState(false);

  const [removingId, setRemovingId] = useState(null);

  const [dryRunResult, setDryRunResult] = useState(null);

  const [error, setError] = useState("");


  // ----------------------------------------
  // Load campaign
  // ----------------------------------------

  async function loadCampaign() {
    try {
      setLoading(true);
      setError("");

      const data = await getCampaign(campaignId);

      setCampaign(data);

    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadCampaign();
  }, [campaignId]);


  // ----------------------------------------
  // Dry run
  // ----------------------------------------

  async function handleDryRun() {
    try {
      setDryRunning(true);
      setError("");
      setDryRunResult(null);

      const result = await dryRunCampaign(
        campaignId
      );

      setDryRunResult(result);

      await loadCampaign();

    } catch (error) {
      setError(error.message);
    } finally {
      setDryRunning(false);
    }
  }


  // ----------------------------------------
  // Remove recipient
  // ----------------------------------------

  async function handleRemoveRecipient(recipient) {
    const confirmed = window.confirm(
      `Remove ${recipient.name} from this campaign?`
    );

    if (!confirmed) {
      return;
    }


    try {
      setRemovingId(recipient.id);
      setError("");

      await removeCampaignRecipient(
        campaignId,
        recipient.id
      );

      await loadCampaign();

    } catch (error) {
      setError(error.message);
    } finally {
      setRemovingId(null);
    }
  }


  // ----------------------------------------
  // Loading
  // ----------------------------------------

  if (loading) {
    return (
      <div className="campaign-details">

        <button
          className="back-button"
          onClick={onBack}
        >
          ← Back to Campaigns
        </button>

        <div className="loading">
          Loading campaign...
        </div>

      </div>
    );
  }


  // ----------------------------------------
  // Error / missing campaign
  // ----------------------------------------

  if (!campaign) {
    return (
      <div className="campaign-details">

        <button
          className="back-button"
          onClick={onBack}
        >
          ← Back to Campaigns
        </button>

        <div className="error-message">
          {error || "Campaign not found."}
        </div>

      </div>
    );
  }


  const {
    campaign: campaignInfo,
    recipients,
    counts,
  } = campaign;


  const isDraft =
    campaignInfo.status === "DRAFT";


  // ----------------------------------------
  // Render
  // ----------------------------------------

  return (
    <div className="campaign-details">


      {/* Back */}

      <button
        className="back-button"
        onClick={onBack}
      >
        ← Back to Campaigns
      </button>


      {/* Error */}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      {/* Header */}

      <section className="panel">

        <div className="campaign-detail-header">

          <div>

            <div className="detail-title-row">

              <h2>
                {campaignInfo.name}
              </h2>

              <span
                className={`badge ${campaignInfo.status.toLowerCase()}`}
              >
                {campaignInfo.status}
              </span>

            </div>

            <p>
              Campaign #{campaignInfo.id}
            </p>

          </div>


          <div className="detail-actions">

            {isDraft && (
              <button
                className="primary-button"
                onClick={handleDryRun}
                disabled={dryRunning}
              >
                {dryRunning
                  ? "Running..."
                  : "Dry Run"}
              </button>
            )}

          </div>

        </div>


        {/* Configuration */}

        <div className="campaign-config">

          <div>
            <span>Template</span>
            <strong>
              {campaignInfo.template || "—"}
            </strong>
          </div>

          <div>
            <span>Attachment</span>
            <strong>
              {campaignInfo.attachment_path || "None"}
            </strong>
          </div>

          <div>
            <span>Delay</span>
            <strong>
              {campaignInfo.delay_seconds ?? "—"} sec
            </strong>
          </div>

          <div>
            <span>Created</span>
            <strong>
              {campaignInfo.created_at}
            </strong>
          </div>

        </div>

      </section>


      {/* Dry run result */}

      {dryRunResult && (
        <section className="panel dry-run-panel">

          <div className="dry-run-header">

            <div>

              <div className="dry-run-title">
                ✓ Dry Run Complete
              </div>

              <p>
                No emails were sent.
                This was only a simulation.
              </p>

            </div>

          </div>


          <div className="dry-run-results">

            {dryRunResult.results.map(
              (result, index) => (

                <div
                  className="dry-run-recipient"
                  key={`${result.recipient}-${index}`}
                >

                  <span className="result-check">
                    ✓
                  </span>

                  <span>
                    Would send to{" "}
                    <strong>
                      {result.recipient}
                    </strong>
                  </span>

                </div>

              )
            )}

          </div>

        </section>
      )}


      {/* Recipient statistics */}

      <div className="recipient-stats">

        <div className="recipient-stat">
          <span>Total</span>
          <strong>{counts.TOTAL}</strong>
        </div>

        <div className="recipient-stat">
          <span>Pending</span>
          <strong>{counts.PENDING}</strong>
        </div>

        <div className="recipient-stat">
          <span>Sent</span>
          <strong>{counts.SENT}</strong>
        </div>

        <div className="recipient-stat">
          <span>Failed</span>
          <strong>{counts.FAILED}</strong>
        </div>

        <div className="recipient-stat">
          <span>Skipped</span>
          <strong>{counts.SKIPPED}</strong>
        </div>

      </div>


      {/* Recipients */}

      <section className="panel">

        <div className="panel-header">

          <div>

            <h2>
              Recipients
            </h2>

            <p>
              Contacts captured when this campaign
              was created
            </p>

          </div>

        </div>


        {recipients.length === 0 ? (

          <div className="empty-state">

            <div className="empty-icon">
              ◎
            </div>

            <h3>
              No recipients
            </h3>

            <p>
              This campaign currently has no recipients.
            </p>

          </div>

        ) : (

          <div className="table-container">

            <table>

              <thead>

                <tr>
                  <th>NAME</th>
                  <th>EMAIL</th>
                  <th>COMPANY</th>
                  <th>ROLE</th>
                  <th>STATUS</th>
                  {isDraft && (
                    <th>ACTIONS</th>
                  )}
                </tr>

              </thead>


              <tbody>

                {recipients.map(
                  (recipient) => (

                    <tr key={recipient.id}>

                      <td>
                        <strong>
                          {recipient.name}
                        </strong>
                      </td>

                      <td>
                        {recipient.email}
                      </td>

                      <td>
                        {recipient.company}
                      </td>

                      <td>
                        {recipient.role}
                      </td>

                      <td>

                        <span
                          className={`badge ${recipient.status.toLowerCase()}`}
                        >
                          {recipient.status}
                        </span>

                      </td>


                      {isDraft && (
                        <td>

                          <button
                            className="action-button danger"
                            onClick={() =>
                              handleRemoveRecipient(
                                recipient
                              )
                            }
                            disabled={
                              removingId ===
                              recipient.id
                            }
                          >
                            {removingId ===
                            recipient.id
                              ? "Removing..."
                              : "Remove"}
                          </button>

                        </td>
                      )}

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>

    </div>
  );
}


export default CampaignDetails;