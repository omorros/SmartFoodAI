import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import AddItemInteractive from "./pages/AddItemInteractive";
import ItemsList from "./pages/ItemsList";
import Settings from "./pages/Settings";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

export default function App() {
  const [active, setActive] = useState("add");

  return (
    <Router>
      <div style={{ display: "flex", height: "100vh" }}>
        <Sidebar active={active} setActive={setActive} />
        <div style={{ flex: 1, overflowY: "auto" }}>
          <Routes>
            <Route path="/" element={<AddItemInteractive />} />
            <Route path="/items" element={<ItemsList />} />
            <Route path="/urgent" element={<ItemsList urgent />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
