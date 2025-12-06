# clean_ecommerce_tables.py
import pandas as pd
import numpy as np
from pathlib import Path

# ===== Helper Utilities =====
def clean_text_col(s):
    return s.astype(str).str.strip().replace({"nan": None})

def clamp_numeric(x, minv=None, maxv=None):
    x = pd.to_numeric(x, errors='coerce')
    if minv is not None:
        x = x.clip(lower=minv)
    if maxv is not None:
        x = x.clip(upper=maxv)
    return x

def save(df, filename):
    if df is not None and not df.empty:
        df.to_csv(filename, index=False)
        print(f"[SAVED] {filename} rows={len(df)}")
    else:
        print(f"[SKIPPED] {filename} (empty)")

# ===== Clean PRODUCTS ONLY =====
def clean_products(df):
    if df is None:
        return None

    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    for col in ["product_name", "category", "brand"]:
        if col in df.columns:
            df[col] = clean_text_col(df[col])

    if "price" in df.columns:
        df["price"] = clamp_numeric(df["price"], 0, None)

    if "rating" in df.columns:
        df["rating"] = clamp_numeric(df["rating"], 1, 5)

    if "product_id" in df.columns:
        df = df.drop_duplicates(subset=["product_id"], keep="first")

    keep_cols = ["product_id", "product_name", "category", "brand", "price", "rating"]
    return df[[c for c in keep_cols if c in df.columns]]

# ===== Inventory Generation =====
def generate_inventory(products_file="cleaned_products.csv",
                       output_file="inventory.csv"):

    if not Path(products_file).exists():
        print(f"[ERROR] {products_file} not found. Cannot generate inventory.")
        return

    print("[INFO] Loading cleaned products...")
    df = pd.read_csv(products_file, dtype=str)

    if "product_id" not in df.columns:
        print("[ERROR] 'product_id' column missing in cleaned_products.csv")
        return

    products = df[["product_id"]].drop_duplicates()
    n = len(products)
    print(f"[INFO] Found {n} unique products")

    # ---- FIX: Make probabilities sum to 1 exactly ----
    stock_levels = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200, 300, 500]
    probs =        [0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
                    0.10, 0.10, 0.10, 0.10, 0.10, 0.10,
                    0.05, 0.05]  # sum = 1 now

    np.random.seed(42)
    stock_vals = np.random.choice(stock_levels, size=n, p=probs)

    inventory = pd.DataFrame({
        "product_id": products["product_id"],
        "stock": stock_vals
    })

    inventory.to_csv(output_file, index=False)
    print(f"[SAVED] {output_file} rows={n}")

# ===== MAIN =====
def main():
    # Clean products only
    if Path("products.csv").exists():
        products_clean = clean_products(pd.read_csv("products.csv", dtype=str))
        save(products_clean, "cleaned_products.csv")
    else:
        print("[ERROR] products.csv not found.")
        return

    # Generate inventory
    generate_inventory()

if __name__ == "__main__":
    main()
