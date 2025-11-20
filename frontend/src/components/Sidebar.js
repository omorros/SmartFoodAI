import React from "react";
import { Drawer, List, ListItem, ListItemButton, ListItemText } from "@mui/material";

const Sidebar = ({ setPage }) => {
  const pages = ["Dashboard", "Add Item", "Items List", "Settings"];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: 200,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: 200,
          boxSizing: "border-box",
          backgroundColor: "#222",
          color: "#fff",
        },
      }}
    >
      <List>
        {pages.map((text) => (
          <ListItem key={text} disablePadding>
            <ListItemButton onClick={() => setPage(text)}>
              <ListItemText primary={text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;
