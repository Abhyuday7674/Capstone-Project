import pandas as pd
import numpy as np
import json
from pathlib import Path

# ---------------------------------------------------
# PATH SETUP
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "raw"
OUTPUT_PATH = BASE_DIR / "data"

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
def load_data():
    users = pd.read_csv(RAW_PATH / "users.csv")
    sessions = pd.read_csv(RAW_PATH / "sessions.csv")
    events = pd.read_csv(RAW_PATH / "events.csv")
    orders = pd.read_csv(RAW_PATH / "orders.csv")
    order_items = pd.read_csv(RAW_PATH / "order_items.csv")
    campaigns = pd.read_csv(RAW_PATH / "campaigns.csv")

    with open(RAW_PATH / "products.json") as f:
        products = pd.DataFrame(json.load(f))

    return users, sessions, events, orders, order_items, products, campaigns

# ---------------------------------------------------
# CLEANING FUNCTIONS
# ---------------------------------------------------
def clean_sessions(df):
    df["session_start_ts"] = pd.to_datetime(df["session_start_ts"])
    df = df.sort_values("session_start_ts").drop_duplicates(subset="session_id", keep="first")
    df["channel"] = df["channel"].str.lower().str.strip().fillna("organic")
    df["device"] = df["device"].str.lower().str.strip().fillna("unknown")
    return df

def clean_events(df):
    df["event_type"] = df["event_type"].str.lower().str.strip()
    df["event_ts"] = pd.to_datetime(df["event_ts"])
    return df.sort_values(["session_id", "event_ts"])

def clean_orders(df):
    df["order_ts"] = pd.to_datetime(df["order_ts"])
    cap_value = df["net_amount"].quantile(0.99)
    df["revenue_outlier_flag"] = np.where(df["net_amount"] > cap_value, 1, 0)
    df["net_amount"] = np.where(df["net_amount"] > cap_value, cap_value, df["net_amount"])
    return df

# ---------------------------------------------------
# BUILD FACT SESSIONS (Includes Time-to-Step & Revenue)
# ---------------------------------------------------
def build_fact_sessions(sessions, events, orders):
    # Funnel Flags [cite: 60]
    funnel = events.pivot_table(index="session_id", columns="event_type", aggfunc="size", fill_value=0)
    funnel = (funnel > 0).astype(int)
    funnel.columns = [f"has_{col}" for col in funnel.columns]
    
    # Time-to-Step Calculations [cite: 61, 62]
    first_ts = sessions.set_index("session_id")["session_start_ts"]
    
    def get_time_diff(event_type):
        event_ts = events[events["event_type"] == event_type].groupby("session_id")["event_ts"].min()
        return (event_ts - first_ts).dt.total_seconds().fillna(0)

    time_metrics = pd.DataFrame({
        "time_to_cart_sec": get_time_diff("add_to_cart"),
        "time_to_checkout_sec": get_time_diff("begin_checkout"),
        "time_to_purchase_sec": get_time_diff("purchase")
    })

    # Total Duration [cite: 61]
    duration = events.groupby("session_id")["event_ts"].agg(["min", "max"])
    time_metrics["session_duration_sec"] = (duration["max"] - duration["min"]).dt.total_seconds()

    # Merge Revenue Fields [cite: 63]
    rev_data = orders.groupby("session_id")[["net_amount", "gross_amount", "discount_amount"]].sum()

    fact_sessions = sessions.merge(funnel, on="session_id", how="left")
    fact_sessions = fact_sessions.merge(time_metrics, on="session_id", how="left")
    fact_sessions = fact_sessions.merge(rev_data, on="session_id", how="left").fillna(0)
    
    return fact_sessions

# ---------------------------------------------------
# BUILD FACT ORDERS (Includes Category Mix)
# ---------------------------------------------------
def build_fact_orders(orders, order_items, products):
    items = order_items.merge(products, on="product_id", how="left")
    items["total_cost"] = items["quantity"] * items["cost"]

    # Category Mix JSON String [cite: 70]
    cat_mix = items.groupby(["order_id", "category"])["quantity"].sum().unstack(fill_value=0)
    cat_mix_json = cat_mix.apply(lambda x: x.to_dict(), axis=1).astype(str)

    order_summary = items.groupby("order_id").agg({
        "quantity": "sum",
        "product_id": "nunique",
        "category": lambda x: x.mode()[0] if not x.mode().empty else None,
        "rating": "mean",
        "total_cost": "sum"
    })
    
    order_summary["category_mix"] = cat_mix_json
    fact_orders = orders.merge(order_summary, on="order_id", how="left")
    fact_orders["margin_proxy"] = fact_orders["net_amount"] - fact_orders["total_cost"] # [cite: 74]
    
    return fact_orders

# ---------------------------------------------------
# BUILD DIM USERS (Includes First/Last Order Dates)
# ---------------------------------------------------
def build_dim_users(users, fact_sessions, fact_orders):
    user_metrics = fact_orders.groupby("user_id").agg({
        "order_id": "count",
        "net_amount": "sum",
        "order_ts": ["min", "max"] # [cite: 80]
    })
    user_metrics.columns = ["lifetime_orders", "total_ltv", "first_order_date", "last_order_date"]
    
    user_dim = users.merge(user_metrics, on="user_id", how="left").fillna(0)
    user_dim["repeat_flag"] = np.where(user_dim["lifetime_orders"] >= 2, 1, 0) # [cite: 83]
    user_dim["user_value_band"] = pd.qcut(user_dim["total_ltv"].rank(method='first'), 3, labels=["low", "medium", "high"]) # [cite: 84]
    
    return user_dim

# ---------------------------------------------------
# EXPORT & MAIN
# ---------------------------------------------------
def main():
    users, sessions, events, orders, order_items, products, campaigns = load_data()
    
    sessions = clean_sessions(sessions)
    events = clean_events(events)
    orders = clean_orders(orders)

    fact_sessions = build_fact_sessions(sessions, events, orders)
    fact_orders = build_fact_orders(orders, order_items, products)
    dim_users = build_dim_users(users, fact_sessions, fact_orders)

    OUTPUT_PATH.mkdir(exist_ok=True)
    fact_sessions.to_csv(OUTPUT_PATH / "fact_sessions.csv", index=False)
    fact_orders.to_csv(OUTPUT_PATH / "fact_orders.csv", index=False)
    dim_users.to_csv(OUTPUT_PATH / "dim_users_enriched.csv", index=False)
    print("ETL Completed Successfully with all project requirements!")

if __name__ == "__main__":
    main()