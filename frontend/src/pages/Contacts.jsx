import { useEffect, useState } from "react";
import { getContacts } from "../api/client";

function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadContacts() {
      try {
        const data = await getContacts();
        setContacts(data);
      } catch (error) {
        console.error("Failed to load contacts:", error);
      } finally {
        setLoading(false);
      }
    }

    loadContacts();
  }, []);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Contacts</h2>
          <p>People available for your campaigns</p>
        </div>

        <button className="primary-button">
          + Add Contact
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading contacts...</div>
      ) : contacts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">◎</div>
          <h3>No contacts</h3>
          <p>Add a contact to start building campaigns.</p>
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
              </tr>
            </thead>

            <tbody>
              {contacts.map((contact) => (
                <tr key={contact.id}>
                  <td>#{contact.id}</td>
                  <td>{contact.name}</td>
                  <td>{contact.email}</td>
                  <td>{contact.company}</td>
                  <td>{contact.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default Contacts;