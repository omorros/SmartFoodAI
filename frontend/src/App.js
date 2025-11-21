import React, { useState } from "react";
import { Box, Toolbar } from "@mui/material";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

import Dashboard from "./pages/Dashboard";
import AddItemInteractive from "./pages/AddItemInteractive";
import ItemsList from "./pages/ItemsList";
import Settings from "./pages/Settings";

function App() {
  const [page, setPage] = useState("Dashboard");

  const renderPage = () => {
    switch (page) {
      case "Add Item":
        return <AddItemInteractive />;
      case "Items List":
        return <ItemsList />;
      case "Settings":
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Box sx={{ display: "flex" }}>
      <Sidebar setPage={setPage} />
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Topbar />
        {renderPage()}
      </Box>
    </Box>
  );
}

export default App;
