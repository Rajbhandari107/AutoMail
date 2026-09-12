import { useEffect, useState } from "react";

import {
  getContacts,
  createContact,
  updateContact,
  deleteContact,
} from "../api/client";


const EMPTY_FORM = {
  name: "",
  email: "",
  company: "",
  role: "",
};


function Contacts() {
  const [contacts, setContacts] = useState([]);

  const [loading, setLoading] = useState(true);

  const [saving, setSaving] = useState(false);

  const [deletingId, setDeletingId] = useState(null);

  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);

  const [editingContact, setEditingContact] = useState(null);

  const [form, setForm] = useState(EMPTY_FORM);


  // ----------------------------------------
  // Load contacts
  // ----------------------------------------

  async function loadContacts() {
    try {
      setLoading(true);
      setError("");

      const data = await getContacts();

      setContacts(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadContacts();
  }, []);


  // ----------------------------------------
  // Form helpers
  // ----------------------------------------

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }


  function openAddForm() {
    setEditingContact(null);
    setForm(EMPTY_FORM);
    setError("");
    setShowForm(true);
  }


  function openEditForm(contact) {
    setEditingContact(contact);

    setForm({
      name: contact.name,
      email: contact.email,
      company: contact.company,
      role: contact.role,
    });

    setError("");
    setShowForm(true);
  }


  function closeForm() {
    if (saving) {
      return;
    }

    setShowForm(false);
    setEditingContact(null);
    setForm(EMPTY_FORM);
  }


  // ----------------------------------------
  // Save contact
  // ----------------------------------------

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");

    const cleanedContact = {
      name: form.name.trim(),
      email: form.email.trim().toLowerCase(),
      company: form.company.trim(),
      role: form.role.trim(),
    };


    if (
      !cleanedContact.name ||
      !cleanedContact.email ||
      !cleanedContact.company ||
      !cleanedContact.role
    ) {
      setError("All fields are required.");
      return;
    }


    try {
      setSaving(true);

      if (editingContact) {
        await updateContact(
          editingContact.id,
          cleanedContact
        );
      } else {
        await createContact(cleanedContact);
      }

      await loadContacts();

      closeForm();

    } catch (error) {
      setError(error.message);
    } finally {
      setSaving(false);
    }
  }


  // ----------------------------------------
  // Delete contact
  // ----------------------------------------

  async function handleDelete(contact) {
    const confirmed = window.confirm(
      `Delete ${contact.name} (${contact.email})?`
    );

    if (!confirmed) {
      return;
    }


    try {
      setDeletingId(contact.id);
      setError("");

      await deleteContact(contact.id);

      await loadContacts();

    } catch (error) {
      setError(error.message);
    } finally {
      setDeletingId(null);
    }
  }


  // ----------------------------------------
  // Render
  // ----------------------------------------

  return (
    <div className="contacts-page">

      <section className="panel">

        {/* Header */}

        <div className="panel-header">

          <div>
            <h2>Contacts</h2>

            <p>
              Manage the people you want to reach
            </p>
          </div>


          <button
            className="primary-button"
            onClick={openAddForm}
          >
            + Add Contact
          </button>

        </div>


        {/* Error */}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}


        {/* Contact form */}

        {showForm && (
          <div className="contact-form-container">

            <div className="form-title">

              <div>
                <h3>
                  {editingContact
                    ? "Edit Contact"
                    : "Add Contact"}
                </h3>

                <p>
                  {editingContact
                    ? "Update this contact's information."
                    : "Add someone to your contact database."}
                </p>
              </div>

            </div>


            <form onSubmit={handleSubmit}>

              <div className="form-grid">

                <div className="form-group">
                  <label htmlFor="name">
                    Name
                  </label>

                  <input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="John Doe"
                    value={form.name}
                    onChange={handleChange}
                    disabled={saving}
                  />
                </div>


                <div className="form-group">
                  <label htmlFor="email">
                    Email
                  </label>

                  <input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="john@example.com"
                    value={form.email}
                    onChange={handleChange}
                    disabled={saving}
                  />
                </div>


                <div className="form-group">
                  <label htmlFor="company">
                    Company
                  </label>

                  <input
                    id="company"
                    name="company"
                    type="text"
                    placeholder="ABC Technologies"
                    value={form.company}
                    onChange={handleChange}
                    disabled={saving}
                  />
                </div>


                <div className="form-group">
                  <label htmlFor="role">
                    Role
                  </label>

                  <input
                    id="role"
                    name="role"
                    type="text"
                    placeholder="Software Engineer Intern"
                    value={form.role}
                    onChange={handleChange}
                    disabled={saving}
                  />
                </div>

              </div>


              <div className="form-actions">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingContact
                    ? "Save Changes"
                    : "Add Contact"}
                </button>

              </div>

            </form>

          </div>
        )}


        {/* Loading */}

        {loading ? (

          <div className="loading">
            Loading contacts...
          </div>

        ) : contacts.length === 0 ? (

          <div className="empty-state">

            <div className="empty-icon">
              ◎
            </div>

            <h3>
              No contacts
            </h3>

            <p>
              Add a contact to start building campaigns.
            </p>

          </div>

        ) : (

          <div className="table-container">

            <table>

              <thead>

                <tr>
                  <th>ID</th>
                  <th>NAME</th>
                  <th>EMAIL</th>
                  <th>COMPANY</th>
                  <th>ROLE</th>
                  <th>ACTIONS</th>
                </tr>

              </thead>


              <tbody>

                {contacts.map((contact) => (

                  <tr key={contact.id}>

                    <td>
                      #{contact.id}
                    </td>

                    <td>
                      <strong>
                        {contact.name}
                      </strong>
                    </td>

                    <td>
                      {contact.email}
                    </td>

                    <td>
                      {contact.company}
                    </td>

                    <td>
                      {contact.role}
                    </td>

                    <td>

                      <div className="table-actions">

                        <button
                          className="action-button"
                          onClick={() =>
                            openEditForm(contact)
                          }
                          disabled={
                            deletingId === contact.id
                          }
                        >
                          Edit
                        </button>


                        <button
                          className="action-button danger"
                          onClick={() =>
                            handleDelete(contact)
                          }
                          disabled={
                            deletingId === contact.id
                          }
                        >
                          {deletingId === contact.id
                            ? "Deleting..."
                            : "Delete"}
                        </button>

                      </div>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </section>

    </div>
  );
}


export default Contacts;