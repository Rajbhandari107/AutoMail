const API_BASE_URL = "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      // Keep the default error.
    }

    throw new Error(message);
  }

  return response.json();
}


// ------------------------------
// Health
// ------------------------------

export function getHealth() {
  return request("/health");
}


// ------------------------------
// Contacts
// ------------------------------

export function getContacts() {
  return request("/contacts");
}

export function createContact(contact) {
  return request("/contacts", {
    method: "POST",
    body: JSON.stringify(contact),
  });
}

export function updateContact(contactId, contact) {
  return request(`/contacts/${contactId}`, {
    method: "PUT",
    body: JSON.stringify(contact),
  });
}

export function deleteContact(contactId) {
  return request(`/contacts/${contactId}`, {
    method: "DELETE",
  });
}


// ------------------------------
// Campaigns
// ------------------------------

export function getCampaigns() {
  return request("/campaigns");
}

export function getCampaign(campaignId) {
  return request(`/campaigns/${campaignId}`);
}

export function createCampaign(campaign) {
  return request("/campaigns", {
    method: "POST",
    body: JSON.stringify(campaign),
  });
}

export function dryRunCampaign(campaignId) {
  return request(`/campaigns/${campaignId}/dry-run`, {
    method: "POST",
  });
}

export function removeCampaignRecipient(
  campaignId,
  recipientId
) {
  return request(
    `/campaigns/${campaignId}/recipients/${recipientId}`,
    {
      method: "DELETE",
    }
  );
}