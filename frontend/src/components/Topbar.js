import React from "react";
import { AppBar, Toolbar, Typography } from "@mui/material";

const Topbar = () => {
  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: "#4caf50",
      }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          SmartFood AI
        </Typography>
      </Toolbar>
    </AppBar>
  );
};

export default Topbar;
