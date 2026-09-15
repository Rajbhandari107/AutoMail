import { useEffect, useState } from "react";

import {
  createCampaign,
  getCampaigns,
  getContacts,
  uploadAttachment,
} from "../api/client";


function Campaigns({ onOpenCampaign }) {
  const [campaigns, setCampaigns] = useState([]);
  const [contacts, setContacts] = useState([]);

  const [showBuilder, setShowBuilder] = useState(false);

  const [name, setName] = useState("");
  const [template, setTemplate] = useState("internship.txt");
  const [delay, setDelay] = useState(2);

  const [selectedContacts, setSelectedContacts] = useState([]);

  const [attachment, setAttachment] = useState(null);
  const [uploadedAttachment, setUploadedAttachment] = useState(null);

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [uploading, setUploading] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");


  // --------------------------------------------------
  // Load campaigns and contacts
  // --------------------------------------------------

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const [
        campaignsData,
        contactsData,
      ] = await Promise.all([
        getCampaigns(),
        getContacts(),
      ]);

      setCampaigns(campaignsData);
      setContacts(contactsData);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadData();
  }, []);


  // --------------------------------------------------
  // Reset builder
  // --------------------------------------------------

  function resetBuilder() {
    setName("");
    setTemplate("internship.txt");
    setDelay(2);

    setSelectedContacts([]);

    setAttachment(null);
    setUploadedAttachment(null);

    setError("");
    setSuccess("");
  }


  // --------------------------------------------------
  // Open builder
  // --------------------------------------------------

  function openBuilder() {
    resetBuilder();
    setShowBuilder(true);
  }


  // --------------------------------------------------
  // Close builder
  // --------------------------------------------------

  function closeBuilder() {
    if (creating || uploading) {
      return;
    }

    setShowBuilder(false);
    resetBuilder();
  }


  // --------------------------------------------------
  // Select / deselect contact
  // --------------------------------------------------

  function toggleContact(contactId) {
    setSelectedContacts((current) => {
      if (current.includes(contactId)) {
        return current.filter(
          (id) => id !== contactId
        );
      }

      return [
        ...current,
        contactId,
      ];
    });
  }


  // --------------------------------------------------
  // Select all contacts
  // --------------------------------------------------

  function toggleAllContacts() {
    if (
      selectedContacts.length === contacts.length
    ) {
      setSelectedContacts([]);
      return;
    }

    setSelectedContacts(
      contacts.map((contact) => contact.id)
    );
  }


  // --------------------------------------------------
  // File selection
  // --------------------------------------------------

  function handleFileChange(event) {
    const file = event.target.files?.[0];

    if (!file) {
      setAttachment(null);
      setUploadedAttachment(null);
      return;
    }

    setError("");
    setSuccess("");

    setAttachment(file);
    setUploadedAttachment(null);
  }


  // --------------------------------------------------
  // Upload attachment
  // --------------------------------------------------

  async function handleUpload() {
    if (!attachment) {
      setError("Please select an attachment first.");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setSuccess("");

      const result = await uploadAttachment(
        attachment
      );

      setUploadedAttachment(result);

      setSuccess(
        `${result.filename} uploaded successfully.`
      );

    } catch (err) {
      setUploadedAttachment(null);
      setError(err.message);

    } finally {
      setUploading(false);
    }
  }


  // --------------------------------------------------
  // Create campaign
  // --------------------------------------------------

  async function handleCreateCampaign(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!name.trim()) {
      setError(
        "Please enter a campaign name."
      );
      return;
    }

    if (selectedContacts.length === 0) {
      setError(
        "Please select at least one contact."
      );
      return;
    }

    if (delay < 0) {
      setError(
        "Delay cannot be negative."
      );
      return;
    }

    if (!uploadedAttachment) {
      setError(
        "Please upload an attachment before creating the campaign."
      );
      return;
    }

    try {
      setCreating(true);

      const campaign = await createCampaign({
        name: name.trim(),
        contact_ids: selectedContacts,
        template,
        attachment_path:
          uploadedAttachment.path,
        delay_seconds: Number(delay),
      });

      setSuccess(
        "Campaign created successfully."
      );

      await loadData();

      setShowBuilder(false);
      resetBuilder();

      if (onOpenCampaign) {
        onOpenCampaign(campaign.campaign_id);
      }

    } catch (err) {
      setError(err.message);

    } finally {
      setCreating(false);
    }
  }


  // --------------------------------------------------
  // Loading state
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="page-content">
        <div className="page-header">
          <div>
            <h2>Campaigns</h2>
            <p>
              Create and manage email campaigns
            </p>
          </div>
        </div>

        <div className="loading-state">
          Loading campaigns...
        </div>
      </div>
    );
  }


  // --------------------------------------------------
  // Builder
  // --------------------------------------------------

  if (showBuilder) {
    return (
      <div className="page-content">

        <div className="page-header">
          <div>
            <h2>New Campaign</h2>
            <p>
              Configure your email outreach campaign
            </p>
          </div>

          <button
            className="secondary-button"
            onClick={closeBuilder}
            disabled={creating || uploading}
          >
            Cancel
          </button>
        </div>


        {error && (
          <div className="error-message">
            {error}
          </div>
        )}


        {success && (
          <div className="success-message">
            {success}
          </div>
        )}


        <form
          className="campaign-builder"
          onSubmit={handleCreateCampaign}
        >

          {/* ---------------------------------------- */}
          {/* Campaign information */}
          {/* ---------------------------------------- */}

          <div className="builder-section">

            <div className="builder-section-header">
              <div>
                <h3>Campaign Details</h3>
                <p>
                  Basic campaign configuration
                </p>
              </div>
            </div>


            <div className="form-group">
              <label>
                Campaign Name
              </label>

              <input
                type="text"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                placeholder="e.g. Software Internship Outreach"
                disabled={creating}
              />
            </div>


            <div className="form-row">

              <div className="form-group">
                <label>
                  Template
                </label>

                <select
                  value={template}
                  onChange={(event) =>
                    setTemplate(event.target.value)
                  }
                  disabled={creating}
                >
                  <option value="internship.txt">
                    internship.txt
                  </option>
                </select>
              </div>


              <div className="form-group">
                <label>
                  Delay Between Emails
                </label>

                <input
                  type="number"
                  min="0"
                  value={delay}
                  onChange={(event) =>
                    setDelay(event.target.value)
                  }
                  disabled={creating}
                />

                <span className="form-hint">
                  Seconds between recipients
                </span>
              </div>

            </div>

          </div>


          {/* ---------------------------------------- */}
          {/* Attachment */}
          {/* ---------------------------------------- */}

          <div className="builder-section">

            <div className="builder-section-header">
              <div>
                <h3>Attachment</h3>
                <p>
                  Upload the resume or document to attach
                </p>
              </div>
            </div>


            <div className="file-upload-area">

              <input
                id="campaign-attachment"
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileChange}
                disabled={creating || uploading}
              />

              {attachment && (
                <div className="selected-file">

                  <div>
                    <strong>
                      {attachment.name}
                    </strong>

                    <span>
                      {(
                        attachment.size /
                        1024
                      ).toFixed(1)} KB
                    </span>
                  </div>


                  {!uploadedAttachment && (
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={handleUpload}
                      disabled={
                        uploading ||
                        creating
                      }
                    >
                      {uploading
                        ? "Uploading..."
                        : "Upload"}
                    </button>
                  )}

                </div>
              )}


              {uploadedAttachment && (
                <div className="upload-success">

                  <span>
                    ✓
                  </span>

                  <div>
                    <strong>
                      {uploadedAttachment.filename}
                    </strong>

                    <small>
                      Uploaded successfully
                    </small>
                  </div>

                </div>
              )}


              {!attachment && (
                <p className="form-hint">
                  PDF, DOC, or DOCX · Maximum 5 MB
                </p>
              )}

            </div>

          </div>


          {/* ---------------------------------------- */}
          {/* Recipients */}
          {/* ---------------------------------------- */}

          <div className="builder-section">

            <div className="builder-section-header">

              <div>
                <h3>Recipients</h3>
                <p>
                  Select the contacts who should receive this campaign
                </p>
              </div>


              <button
                type="button"
                className="text-button"
                onClick={toggleAllContacts}
                disabled={creating}
              >
                {selectedContacts.length ===
                contacts.length
                  ? "Deselect All"
                  : "Select All"}
              </button>

            </div>


            {contacts.length === 0 ? (

              <div className="empty-state">
                No contacts available.
              </div>

            ) : (

              <div className="contact-selection">

                {contacts.map((contact) => (

                  <label
                    key={contact.id}
                    className={`contact-option ${
                      selectedContacts.includes(
                        contact.id
                      )
                        ? "selected"
                        : ""
                    }`}
                  >

                    <input
                      type="checkbox"
                      checked={selectedContacts.includes(
                        contact.id
                      )}
                      onChange={() =>
                        toggleContact(
                          contact.id
                        )
                      }
                      disabled={creating}
                    />


                    <div className="contact-option-info">

                      <strong>
                        {contact.name}
                      </strong>

                      <span>
                        {contact.email}
                      </span>

                      <small>
                        {contact.company} ·{" "}
                        {contact.role}
                      </small>

                    </div>

                  </label>

                ))}

              </div>

            )}

          </div>


          {/* ---------------------------------------- */}
          {/* Summary */}
          {/* ---------------------------------------- */}

          <div className="campaign-summary">

            <div>
              <span>
                Recipients
              </span>

              <strong>
                {selectedContacts.length}
              </strong>
            </div>


            <div>
              <span>
                Attachment
              </span>

              <strong>
                {uploadedAttachment
                  ? "Ready"
                  : "Required"}
              </strong>
            </div>


            <div>
              <span>
                Delay
              </span>

              <strong>
                {delay}s
              </strong>
            </div>

          </div>


          {/* ---------------------------------------- */}
          {/* Actions */}
          {/* ---------------------------------------- */}

          <div className="builder-actions">

            <button
              type="button"
              className="secondary-button"
              onClick={closeBuilder}
              disabled={
                creating ||
                uploading
              }
            >
              Cancel
            </button>


            <button
              type="submit"
              className="primary-button"
              disabled={
                creating ||
                uploading ||
                selectedContacts.length === 0 ||
                !uploadedAttachment
              }
            >
              {creating
                ? "Creating..."
                : "Create Campaign"}
            </button>

          </div>

        </form>

      </div>
    );
  }


  // --------------------------------------------------
  // Campaign list
  // --------------------------------------------------

  return (
    <div className="page-content">

      <div className="page-header">

        <div>
          <h2>Campaigns</h2>
          <p>
            Create and manage email campaigns
          </p>
        </div>


        <button
          className="primary-button"
          onClick={openBuilder}
        >
          + New Campaign
        </button>

      </div>


      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      {campaigns.length === 0 ? (

        <div className="empty-state">
          <h3>No campaigns yet</h3>

          <p>
            Create your first campaign to get started.
          </p>

          <button
            className="primary-button"
            onClick={openBuilder}
          >
            Create Campaign
          </button>
        </div>

      ) : (

        <div className="campaign-list">

          {campaigns.map((campaign) => (

            <div
              key={campaign.id}
              className="campaign-card"
            >

              <div className="campaign-card-main">

                <div className="campaign-card-title">

                  <h3>
                    {campaign.name}
                  </h3>

                  <span
                    className={`status-badge status-${campaign.status.toLowerCase()}`}
                  >
                    {campaign.status}
                  </span>

                </div>


                <div className="campaign-card-meta">

                  <span>
                    Template:{" "}
                    {campaign.template ||
                      "Not set"}
                  </span>

                  <span>
                    Delay:{" "}
                    {campaign.delay_seconds ??
                      2}s
                  </span>

                  <span>
                    {campaign.created_at}
                  </span>

                </div>

              </div>


              <button
                className="secondary-button"
                onClick={() =>
                  onOpenCampaign &&
                  onOpenCampaign(
                    campaign.id
                  )
                }
              >
                View
              </button>

            </div>

          ))}

        </div>

      )}

    </div>
  );
}


export default Campaigns;