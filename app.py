import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Trip Hub", layout="centered")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

st.title("🇨🇳 Global Travel Sync")
st.caption("Multi-City, Multi-Trip Planner & Shared Expenses")

# 1. Fetch Active Journeys
trips_db = supabase.table("master_trips").select("*").execute()
if trips_db.data:
    trips_df = pd.DataFrame(trips_db.data)
    trip_map = dict(zip(trips_df['trip_name'], trips_df['trip_id']))
    selected_trip_name = st.selectbox("Active Journey:", options=list(trip_map.keys()))
    trip_id = trip_map[selected_trip_name]
else:
    st.error("Please run the Supabase database script first.")
    st.stop()

# Mobile UI Bottom-Navigation Emulation
t_itin, t_spend, t_log, t_pack, t_vlog = st.tabs(["🗺️ Plan", "📊 Money", "💸 Log", "🎒 Pack", "🎬 Vlog"])

# TAB 1: ITINERARY VIEW
with t_itin:
    st.subheader("Daily Schedule")
    itin_db = supabase.table("daily_itinerary").select("*").eq("trip_id", trip_id).order("date").execute()
    if itin_db.data:
        for item in itin_db.data:
            with st.expander(f"Day {item['day_number']} | {item['city_cluster']} ({item['date']})"):
                st.markdown(f"**⏰ Time:** {item['time_label']}")
                st.markdown(f"**📍 Location:** {item['location_name']}")
                st.info(f"📋 {item['notes']}")
    else:
        st.info("No schedule entries loaded for this journey.")

# TAB 2: SPEND & SETTLEMENT ENGINE
with t_spend:
    st.subheader("Group Balances")
    exp_db = supabase.table("expense_tracker").select("*").eq("trip_id", trip_id).execute()
    if exp_db.data:
        df = pd.DataFrame(exp_db.data)
        st.dataframe(df[['item', 'paid_by', 'local_amount', 'home_amount_aud']], use_container_width=True)
        st.metric("Total Shared Group Spend", f"${df['home_amount_aud'].sum():,.2f} AUD")
    else:
        st.info("Clean ledger! No expenses found.")

# TAB 3: DYNAMIC BILL LOGGER
with t_log:
    st.subheader("Log an Expense")
    friends = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    
    with st.form("spend_form", clear_on_submit=True):
        item_title = st.text_input("Item Description:", placeholder="e.g., Luoyang Water Banquet")
        payer = st.selectbox("Paid By:", options=friends)
        amt_local = st.number_input("Local Amount (Foreign Currency):", min_value=0.0, step=5.0)
        ex_rate = st.number_input("Exchange Rate (Amount local per 1 AUD):", min_value=0.01, value=4.6200, format="%.4f")
        split_with = st.multiselect("Split cleanly between:", options=friends, default=friends)
        
        if st.form_submit_button("Publish Ledger Record"):
            if item_title and amt_local > 0:
                supabase.table("expense_tracker").insert({
                    "trip_id": trip_id, "item": item_title, "paid_by": payer,
                    "local_amount": amt_local, "exchange_rate": ex_rate, "who_owes": split_with,
                    "split_type": "Equal" if len(split_with) == len(friends) else "Specific"
                }).execute()
                st.success("Transaction written to Supabase! Refreshing...")
                st.rerun()

# TAB 4: CLIMATE-AWARE PACKING
with t_pack:
    st.subheader("Group Packing Checklist")
    pack_db = supabase.table("packing_checklist").select("*").eq("trip_id", trip_id).execute()
    if pack_db.data:
        for idx, pc in enumerate(pack_db.data):
            status = st.checkbox(f"{pc['item']} ({pc['climate_tag']}) — [{pc['assigned_to']}]", value=pc['is_packed'], key=f"pack_{idx}")
            if status != pc['is_packed']:
                supabase.table("packing_checklist").update({"is_packed": status}).eq("id", pc['id']).execute()
    else:
        st.info("No bags packed yet.")

# TAB 5: VLOG PRODUCTION PLANNER
with t_vlog:
    st.subheader("Vlog Scene Production Tracker")
    vlog_db = supabase.table("vlog_tracker").select("*").eq("trip_id", trip_id).execute()
    if vlog_db.data:
        v_df = pd.DataFrame(vlog_db.data)
        st.dataframe(v_df[['city_cluster', 'scene_description', 'shot_type', 'status']], use_container_width=True)
    else:
        st.info("No scheduled scenes recorded.")