function Sidebar({ currentPage, setCurrentPage }) {
  const navigation = [
    {
      name: "Dashboard",
      key: "dashboard",
      icon: "▦",
    },
    {
      name: "Contacts",
      key: "contacts",
      icon: "◎",
    },
    {
      name: "Campaigns",
      key: "campaigns",
      icon: "✉",
    },
  ];

  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-mark">A</div>
        <span>AutoMail</span>
      </div>

      <nav className="navigation">
        <p className="nav-label">WORKSPACE</p>

        {navigation.map((item) => (
          <button
            key={item.key}
            className={`nav-item ${
              currentPage === item.key ? "active" : ""
            }`}
            onClick={() => setCurrentPage(item.key)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.name}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="status-dot"></div>
        <div>
          <div className="status-title">Backend</div>
          <div className="status-subtitle">Local API</div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;