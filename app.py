import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Configure Mobile Responsiveness & Viewport
st.set_page_config(page_title="Trip Hub", layout="centered")

# Initialize Supabase Connection
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["https://vdoyjmfadgcphplvquvg.supabase.co"]
    key = st.secrets["sb_publishable_2gJlsMkASfpdNd0MvxMbhw_A60EDhha"]
    return create_client(url, key)

supabase = init_supabase()

# App Header & Countdown
st.title("🇨🇳 Rail & River Odyssey")
st.caption("Group Itinerary & Shared Expense Hub")

# Multi-Trip Switcher Setup
trips_data = supabase.table("master_trips").select("*").execute()
trips_df = pd.DataFrame(trips_data.data)
selected_trip = st.selectbox("Select Active Journey:", trips_df['trip_name'])
trip_id = trips_df[trips_df['trip_name'] == selected_trip]['trip_id'].values[0]

# Bottom Navigation Bar Emulator (Excellent for Mobile)
tab1, tab2, tab3 = st.tabs(["🗺️ Plan", "💰 Money", "➕ Log Cost"])

with tab1:
    st.subheader("Daily Itinerary")
    itin_data = supabase.table("daily_itinerary").select("*").eq("trip_id", trip_id).order("date").execute()
    if itin_data.data:
        itin_df = pd.DataFrame(itin_data.data)
        for _, row in itin_df.iterrows():
            with st.expander(f"📅 {row['date']} - {row['city_cluster']}"):
                st.markdown(f"**⏰ Time:** {row['time_label']}")
                st.markdown(f"**📍 Location:** {row['location_name']}")
                st.markdown(f"**📝 Details:** {row['notes']}")
    else:
        st.info("No itinerary slots generated yet.")

with tab2:
    st.subheader("Trip Balances")
    exp_data = supabase.table("expense_tracker").select("*").eq("trip_id", trip_id).execute()
    if exp_data.data:
        df = pd.DataFrame(exp_data.data)
        st.dataframe(df[['item', 'paid_by', 'local_amount', 'home_amount_aud']], use_container_width=True)
        
        # Simple breakdown logic display
        total_spent = df['home_amount_aud'].sum()
        st.metric("Total Shared Group Spend (AUD)", f"${total_spent:,.2f}")
    else:
        st.info("No expenses logged yet.")

with tab3:
    st.subheader("Log a New Group Expense")
    friends = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    
    with st.form("expense_form", clear_on_submit=True):
        item = st.text_input("What did you buy?", placeholder="e.g., Chongqing Hotpot")
        payer = st.selectbox("Who paid?", options=friends)
        local_amt = st.number_input("Local Currency Amount (RMB)", min_value=0.0, step=1.0)
        ex_rate = st.number_input("Effective Exchange Rate (AUD/RMB)", min_value=0.01, value=4.6200, format="%.4f")
        
        st.caption("Who splits this?")
        who_owes = st.multiselect("Select participants:", options=friends, default=friends)
        
        submitted = st.form_submit_button("Submit Transaction to Cloud")
        if submitted and item and local_amt > 0:
            payload = {
                "trip_id": trip_id,
                "item": item,
                "paid_by": payer,
                "local_amount": local_amt,
                "exchange_rate": ex_rate,
                "who_owes": who_owes,
                "split_type": "Equal" if len(who_owes) == len(friends) else "Specific"
            }
            supabase.table("expense_tracker").insert(payload).execute()
            st.success("Logged successfully! Pull down page to refresh.")