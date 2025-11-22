import React from "react";
import { Link } from "react-router-dom";

export default function Sidebar({ active, setActive }) {
  const menuItems = [
    { name: "Add Item", path: "/" },
    { name: "View Items", path: "/items" },
    { name: "Settings", path: "/settings" },
  ];

  return (
    <div
      style={{
        width: "220px",
        background: "#111",
        color: "#fff",
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <h2 style={{ color: "#4CAF50" }}>SmartFood AI</h2>
      {menuItems.map((item) => (
        <Link
          key={item.name}
          to={item.path}
          onClick={() => setActive(item.name)}
          style={{
            padding: "0.8rem 1rem",
            borderRadius: "6px",
            background: active === item.name ? "#4CAF50" : "transparent",
            color: "white",
            textDecoration: "none",
            fontWeight: "bold",
          }}
        >
          {item.name}
        </Link>
      ))}
    </div>
  );
}
