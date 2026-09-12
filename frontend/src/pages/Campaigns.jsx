import { useEffect, useState } from "react";

import {
  getCampaigns,
  getContacts,
  createCampaign,
} from "../api/client";

import CampaignDetails from "./CampaignDetails";


const EMPTY_FORM = {
  name: "",
  template: "internship.txt",
  delay_seconds: 2,
};


function Campaigns() {

  const [campaigns, setCampaigns] = useState([]);

  const [contacts, setContacts] = useState([]);

  const [selectedContacts, setSelectedContacts] =
    useState([]);

  const [loading, setLoading] = useState(true);

  const [creating, setCreating] = useState(false);

  const [showBuilder, setShowBuilder] =
    useState(false);

  const [selectedCampaignId, setSelectedCampaignId] =
    useState(null);

  const [form, setForm] =
    useState(EMPTY_FORM);

  const [error, setError] = useState("");


  // ----------------------------------------
  // Load data
  // ----------------------------------------

  async function loadData() {

    try {

      setLoading(true);
      setError("");

      const [
        campaignData,
        contactData,
      ] = await Promise.all([
        getCampaigns(),
        getContacts(),
      ]);

      setCampaigns(campaignData);
      setContacts(contactData);

    } catch (error) {

      setError(error.message);

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {
    loadData();
  }, []);


  // ----------------------------------------
  // Builder
  // ----------------------------------------

  function openBuilder() {

    setForm(EMPTY_FORM);

    setSelectedContacts([]);

    setError("");

    setShowBuilder(true);
  }


  function closeBuilder() {

    if (creating) {
      return;
    }

    setShowBuilder(false);

    setForm(EMPTY_FORM);

    setSelectedContacts([]);

    setError("");
  }


  function handleChange(event) {

    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }


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


  function toggleSelectAll() {

    if (
      selectedContacts.length ===
      contacts.length
    ) {

      setSelectedContacts([]);

      return;
    }

    setSelectedContacts(
      contacts.map(
        (contact) => contact.id
      )
    );
  }


  // ----------------------------------------
  // Create campaign
  // ----------------------------------------

  async function handleSubmit(event) {

    event.preventDefault();

    setError("");

    const campaignName =
      form.name.trim();


    if (!campaignName) {

      setError(
        "Campaign name is required."
      );

      return;
    }


    if (selectedContacts.length === 0) {

      setError(
        "Select at least one contact."
      );

      return;
    }


    const delay =
      Number(form.delay_seconds);


    if (
      !Number.isInteger(delay) ||
      delay < 0
    ) {

      setError(
        "Delay must be a non-negative whole number."
      );

      return;
    }


    try {

      setCreating(true);

      const created =
        await createCampaign({
          name: campaignName,
          contact_ids: selectedContacts,
          template: form.template,
          delay_seconds: delay,
        });


      await loadData();

      closeBuilder();

      setSelectedCampaignId(
        created.campaign_id
      );

    } catch (error) {

      setError(error.message);

    } finally {

      setCreating(false);

    }
  }


  // ----------------------------------------
  // Campaign details
  // ----------------------------------------

  if (selectedCampaignId !== null) {

    return (
      <CampaignDetails
        campaignId={
          selectedCampaignId
        }
        onBack={() => {
          setSelectedCampaignId(null);
          loadData();
        }}
      />
    );
  }


  // ----------------------------------------
  // Render
  // ----------------------------------------

  return (
    <div className="campaigns-page">

      <section className="panel">

        <div className="panel-header">

          <div>

            <h2>
              Campaigns
            </h2>

            <p>
              Create and manage your email outreach
            </p>

          </div>


          {!showBuilder && (

            <button
              className="primary-button"
              onClick={openBuilder}
            >
              + New Campaign
            </button>

          )}

        </div>


        {/* Error */}

        {error && (

          <div className="error-message">
            {error}
          </div>

        )}


        {/* Builder */}

        {showBuilder && (

          <div className="campaign-builder">

            <div className="builder-heading">

              <div>

                <h3>
                  Create Campaign
                </h3>

                <p>
                  Configure your campaign and
                  select the recipients.
                </p>

              </div>

            </div>


            <form
              onSubmit={handleSubmit}
            >

              <div className="builder-section">

                <h4>
                  Campaign Settings
                </h4>


                <div className="form-grid">

                  <div className="form-group">

                    <label>
                      Campaign Name
                    </label>

                    <input
                      name="name"
                      type="text"
                      placeholder="Internship Outreach"
                      value={form.name}
                      onChange={handleChange}
                      disabled={creating}
                    />

                  </div>


                  <div className="form-group">

                    <label>
                      Email Template
                    </label>

                    <select
                      name="template"
                      value={form.template}
                      onChange={handleChange}
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

                    <div className="input-with-unit">

                      <input
                        name="delay_seconds"
                        type="number"
                        min="0"
                        step="1"
                        value={
                          form.delay_seconds
                        }
                        onChange={handleChange}
                        disabled={creating}
                      />

                      <span>
                        seconds
                      </span>

                    </div>

                  </div>

                </div>

              </div>


              {/* Recipients */}

              <div className="builder-section">

                <div className="recipient-header">

                  <div>

                    <h4>
                      Recipients
                    </h4>

                    <p>
                      Select the contacts who should
                      receive this campaign.
                    </p>

                  </div>


                  <div className="recipient-controls">

                    <span className="selection-count">
                      {
                        selectedContacts.length
                      }{" "}
                      selected
                    </span>

                    <button
                      type="button"
                      className="select-all-button"
                      onClick={
                        toggleSelectAll
                      }
                      disabled={
                        creating ||
                        contacts.length === 0
                      }
                    >
                      {
                        selectedContacts.length ===
                        contacts.length
                          ? "Clear All"
                          : "Select All"
                      }
                    </button>

                  </div>

                </div>


                <div className="recipient-list">

                  {contacts.map(
                    (contact) => {

                      const selected =
                        selectedContacts.includes(
                          contact.id
                        );


                      return (

                        <label
                          key={contact.id}
                          className={`recipient-card ${
                            selected
                              ? "selected"
                              : ""
                          }`}
                        >

                          <input
                            type="checkbox"
                            checked={selected}
                            onChange={() =>
                              toggleContact(
                                contact.id
                              )
                            }
                            disabled={creating}
                          />


                          <div className="recipient-check">
                            {
                              selected
                                ? "✓"
                                : ""
                            }
                          </div>


                          <div className="recipient-info">

                            <strong>
                              {contact.name}
                            </strong>

                            <span>
                              {contact.email}
                            </span>

                          </div>


                          <div className="recipient-company">

                            <strong>
                              {contact.company}
                            </strong>

                            <span>
                              {contact.role}
                            </span>

                          </div>

                        </label>

                      );

                    }
                  )}

                </div>

              </div>


              {/* Summary */}

              <div className="campaign-summary">

                <div>

                  <span>
                    Recipients
                  </span>

                  <strong>
                    {
                      selectedContacts.length
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Template
                  </span>

                  <strong>
                    {form.template}
                  </strong>

                </div>


                <div>

                  <span>
                    Delay
                  </span>

                  <strong>
                    {form.delay_seconds}s
                  </strong>

                </div>

              </div>


              <div className="builder-actions">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={
                    closeBuilder
                  }
                  disabled={creating}
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="primary-button"
                  disabled={creating}
                >
                  {
                    creating
                      ? "Creating..."
                      : "Create Draft"
                  }
                </button>

              </div>

            </form>

          </div>

        )}


        {/* Campaign list */}

        {!showBuilder && (

          <>
            {loading ? (

              <div className="loading">
                Loading campaigns...
              </div>

            ) : campaigns.length === 0 ? (

              <div className="empty-state">

                <div className="empty-icon">
                  ✉
                </div>

                <h3>
                  No campaigns
                </h3>

                <p>
                  Create your first campaign
                  to begin.
                </p>

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
                      <th>ACTION</th>
                    </tr>

                  </thead>


                  <tbody>

                    {campaigns.map(
                      (campaign) => (

                        <tr
                          key={campaign.id}
                        >

                          <td>
                            #{campaign.id}
                          </td>

                          <td>
                            <strong>
                              {campaign.name}
                            </strong>
                          </td>

                          <td>

                            <span
                              className={`badge ${campaign.status.toLowerCase()}`}
                            >
                              {
                                campaign.status
                              }
                            </span>

                          </td>

                          <td>
                            {
                              campaign.template ||
                              "—"
                            }
                          </td>

                          <td>
                            {
                              campaign.delay_seconds ??
                              "—"
                            }{" "}
                            sec
                          </td>

                          <td>

                            <button
                              className="action-button"
                              onClick={() =>
                                setSelectedCampaignId(
                                  campaign.id
                                )
                              }
                            >
                              View
                            </button>

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

          </>

        )}

      </section>

    </div>
  );
}


export default Campaigns;