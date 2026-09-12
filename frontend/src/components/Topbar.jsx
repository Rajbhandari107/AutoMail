function Topbar({ currentPage }) {
  const titles = {
    dashboard: {
      title: "Dashboard",
      subtitle: "Overview of your outreach activity",
    },
    contacts: {
      title: "Contacts",
      subtitle: "Manage your outreach contacts",
    },
    campaigns: {
      title: "Campaigns",
      subtitle: "Create and manage email campaigns",
    },
  };

  const page = titles[currentPage];

  return (
    <header className="topbar">
      <div>
        <h1>{page.title}</h1>
        <p>{page.subtitle}</p>
      </div>

      <div className="topbar-actions">
        <div className="api-status">
          <span></span>
          API Connected
        </div>

        <div className="avatar">BR</div>
      </div>
    </header>
  );
}

export default Topbar;