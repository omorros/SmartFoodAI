import React, { useState } from "react";
import { Box, Toolbar } from "@mui/material";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Dashboard from "./pages/Dashboard";
import AddItemForm from "./pages/AddItemForm";
import ItemsList from "./pages/ItemsList";
import Settings from "./pages/Settings";

function App() {
  const [page, setPage] = useState("Dashboard");

  const renderPage = () => {
    switch (page) {
      case "Add Item":
        return <AddItemForm />;
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
      <Box component="main" sx={{ flexGrow: 1, bgcolor: "#f5f5f5", height: "100vh" }}>
        <Topbar />
        <Toolbar />
        {renderPage()}
      </Box>
    </Box>
  );
}

export default App;
