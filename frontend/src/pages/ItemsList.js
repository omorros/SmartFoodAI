import React, { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Grid,
  Box,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material";

const API_BASE = "http://127.0.0.1:8000";

export default function ItemsList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editItem, setEditItem] = useState(null);
  const [sortUrgent, setSortUrgent] = useState(false); // toggle for sorting

  // Fetch all items from FastAPI
  const fetchItems = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/list_items`);
      const data = await res.json();

      const itemsArray = Array.isArray(data) ? data : data.items || [];
      setItems(itemsArray);
    } catch (err) {
      console.error("Error fetching items:", err);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  // --- Handle delete item
  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;
    try {
      const res = await fetch(`${API_BASE}/delete_item/${id}`, {
        method: "DELETE",
      });
      if (res.ok) fetchItems();
    } catch (err) {
      console.error("Error deleting item:", err);
    }
  };

  // --- Handle consume item
  const handleConsume = async (id) => {
    const amount = prompt("Enter amount to consume:");
    if (!amount) return;
    try {
      const res = await fetch(`${API_BASE}/consume_item/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: parseFloat(amount) }),
      });
      if (res.ok) fetchItems();
    } catch (err) {
      console.error("Error consuming item:", err);
    }
  };

  // --- Handle edit item
  const handleEdit = async () => {
    try {
      const res = await fetch(`${API_BASE}/update_item/${editItem.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editItem),
      });
      if (res.ok) {
        setEditItem(null);
        fetchItems();
      }
    } catch (err) {
      console.error("Error updating item:", err);
    }
  };

  // --- Helper: color-coded urgency
  const getUrgencyColor = (daysLeft) => {
    if (daysLeft === "Expired") return "#f44336"; // red
    if (daysLeft === null || daysLeft === undefined) return "#ccc"; // gray
    if (daysLeft <= 3) return "#ff9800"; // orange
    return "#4caf50"; // green
  };

  // --- Sorting logic
  const sortedItems = [...items].sort((a, b) => {
    if (!sortUrgent) return 0; // no sorting
    const getPriority = (d) =>
      d === "Expired" ? -9999 : d === null ? 9999 : d;
    return getPriority(a.days_left) - getPriority(b.days_left);
  });

  if (loading)
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 5 }}>
        <CircularProgress />
      </Box>
    );

  return (
    <Box sx={{ p: 4 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Typography variant="h4">Inventory Items</Typography>
        <Button
          variant={sortUrgent ? "contained" : "outlined"}
          onClick={() => setSortUrgent(!sortUrgent)}
        >
          {sortUrgent ? "Show Default Order" : "Sort by Urgency"}
        </Button>
      </Box>

      <Grid container spacing={3}>
        {sortedItems.map((item) => (
          <Grid item xs={12} sm={6} md={4} key={item.id}>
            <Card
              variant="outlined"
              sx={{
                borderLeft: `6px solid ${getUrgencyColor(item.days_left)}`,
                transition: "0.3s",
                "&:hover": { boxShadow: 4 },
              }}
            >
              <CardContent>
                <Typography variant="h6">{item.name}</Typography>
                <Typography color="textSecondary">
                  {item.category} • {item.location}
                </Typography>
                <Typography sx={{ mt: 1 }}>
                  <b>Quantity:</b> {item.qty} {item.unit}
                </Typography>
                <Typography>
                  <b>Expiry:</b> {item.expiry_on || "—"}
                </Typography>
                <Typography>
                  <b>Days Left:</b>{" "}
                  <span style={{ color: getUrgencyColor(item.days_left) }}>
                    {item.days_left === "Expired"
                      ? "Expired"
                      : item.days_left !== null
                      ? `${item.days_left} days`
                      : "unknown"}
                  </span>
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small" onClick={() => setEditItem(item)}>
                  Edit
                </Button>
                <Button
                  size="small"
                  color="error"
                  onClick={() => handleDelete(item.id)}
                >
                  Delete
                </Button>
                <Button size="small" onClick={() => handleConsume(item.id)}>
                  Consume
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* --- Edit Dialog --- */}
      <Dialog open={!!editItem} onClose={() => setEditItem(null)}>
        <DialogTitle>Edit Item</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            sx={{ mt: 2 }}
            value={editItem?.name || ""}
            onChange={(e) =>
              setEditItem({ ...editItem, name: e.target.value })
            }
          />
          <TextField
            fullWidth
            label="Quantity"
            sx={{ mt: 2 }}
            type="number"
            value={editItem?.qty || ""}
            onChange={(e) =>
              setEditItem({ ...editItem, qty: parseFloat(e.target.value) })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditItem(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleEdit}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
