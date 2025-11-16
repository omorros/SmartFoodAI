import os
os.environ["USE_TF"] = "0"

from sentence_transformers import SentenceTransformer, util

# Load once globally
model = SentenceTransformer('all-MiniLM-L6-v2')

CATEGORIES = ["fruit", "vegetable", "meat", "fish", "dairy", "snack", "grain", "prepared food"]

def get_closest_category(food_name: str):
    """Return the closest known category for a food item, with similarity score."""
    try:
        # Encode both input and category list
        item_emb = model.encode([food_name], convert_to_tensor=True)
        cat_embs = model.encode(CATEGORIES, convert_to_tensor=True)

        # Compute cosine similarity
        sims = util.cos_sim(item_emb, cat_embs)[0]

        # Safely get best match
        best_idx = int(sims.argmax())
        best_category = CATEGORIES[best_idx]
        best_score = float(sims[best_idx])
        return best_category, best_score

    except Exception as e:
        print(f"Warning: semantic mapping failed ({e}). Falling back to manual input.")
        return None, 0.0
