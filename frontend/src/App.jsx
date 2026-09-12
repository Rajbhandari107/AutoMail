import { useState } from "react";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

import Dashboard from "./pages/Dashboard";
import Contacts from "./pages/Contacts";
import Campaigns from "./pages/Campaigns";

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  function renderPage() {
    switch (currentPage) {
      case "contacts":
        return <Contacts />;

      case "campaigns":
        return <Campaigns />;

      case "dashboard":
      default:
        return <Dashboard />;
    }
  }

  return (
    <div className="app">
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
      />

      <main className="main-content">
        <Topbar currentPage={currentPage} />

        <div className="page-content">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}

export default App;