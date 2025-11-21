import React from "react";
import { Drawer, List, ListItem, ListItemText, Toolbar } from "@mui/material";

const drawerWidth = 220;

export default function Sidebar({ setPage }) {
  const menuItems = ["Dashboard", "Add Item", "Items List", "Settings"];

  return (
    <Drawer
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
        },
      }}
      variant="permanent"
      anchor="left"
    >
      <Toolbar />
      <List>
        {menuItems.map((text) => (
          <ListItem button key={text} onClick={() => setPage(text)}>
            <ListItemText primary={text} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}
