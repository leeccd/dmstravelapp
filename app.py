import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# At the top of your app, check the browser URL parameters
query_params = st.query_params

# If you visit the app via: https://your-app.streamlit.app/?role=admin
is_admin = query_params.get("role") == "admin"

# Mobile UI Navigation Tabs
if is_admin:
    # Admin gets all tabs including editing controls
    t_itin, t_spend, t_log, t_pack, t_vlog = st.tabs(["🗺️ Plan", "📊 Money", "💸 Log", "🎒 Pack", "🎬 Vlog"])
else:
    # Your friends only see these three view-only tabs
    t_itin, t_spend, t_pack = st.tabs(["🗺️ Plan", "📊 Money", "🎒 Pack"])
    
# Configure clean, accessible page parameters
st.set_page_config(page_title="China Travel Hub", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS injection to heavily scale up mobile font sizes and touch targets
st.markdown("""
    <style>
        /* Scale up text globally */
        html, body, [class*="css"] {
            font-size: 19px !important;
        }
        /* Make form buttons and tabs larger for easier tapping */
        .stButton button {
            width: 100% !important;
            height: 60px !important;
            font-size: 22px !important;
            font-weight: bold !important;
            border-radius: 12px !important;
        }
        /* Style Chinese text boxes for maximum visibility */
        .chinese-card {
            background-color: #FFF9E6;
            border: 3px solid #FFA500;
            padding: 20px;
            border-radius: 15px;
            color: #000000;
        }
    </style>
""", unsafe_allow_input=True)

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()
ACTIVE_TRIP_ID = "CHINA2027"

# --- HUGE ACCESSIBLE HEADER ---
st.markdown("# 🇨🇳 FAMILY TRAVEL GUIDE")
st.markdown("### Tap your current city below to see today's plan:")

# --- SENIOR FRIENDLY CITY SELECTOR (GIANT BUTTONS) ---
# Instead of a small dropdown, use big buttons that set a session state variable
if "active_city" not in st.session_state:
    st.session_state.active_city = "Beijing"

col1, col2 = st.columns(2)
with col1:
    if st.button("🔴 BEIJING"): st.session_state.active_city = "Beijing"
    if st.button("🧱 LUOYANG"): st.session_state.active_city = "Luoyang"
    if st.button("🗿 XI'AN"): st.session_state.active_city = "Xi'an"
with col2:
    if st.button("🌶️ CHONGQING"): st.session_state.active_city = "Chongqing"
    if st.button("🚢 YANGTZE CRUISE"): st.session_state.active_city = "Yangtze Cruise"
    if st.button("🐼 CHENGDU"): st.session_state.active_city = "Chengdu"

current_city = st.session_state.active_city

st.markdown(f"## 📍 Currently Showing: {current_city.upper()}")
st.markdown("---")

# Simple, intuitive view selector
view_mode = st.radio("What do you want to see?", ["🗺️ Today's Schedule", "🏨 Hotel & Train Tickets"], horizontal=True)

# ------------------------------------------
# SCHEDULE VIEW
# ------------------------------------------
if view_mode == "🗺️ Today's Schedule":
    itin_db = (
        supabase.table("daily_itinerary")
        .select("*")
        .eq("trip_id", ACTIVE_TRIP_ID)
        .eq("city_cluster", current_city)
        .order("date")
        .execute()
    )
    
    if itin_db.data:
        for item in itin_db.data:
            parsed_date = datetime.strptime(item['date'], "%Y-%m-%d").strftime("%B %d")
            
            # Render clean, open cards instead of nested accordion toggles
            with st.container(border=True):
                st.markdown(f"## 📅 {parsed_date}")
                st.markdown(f"**⏰ Time:** {item['time_label']}")
                st.markdown(f"**🎯 What We Are Doing:**\n# {item['activity']}")
                if item['location_name']:
                    st.markdown(f"**📍 Place:** `{item['location_name']}`")
                if item['notes']:
                    st.markdown(f"ℹ️ *Tip: {item['notes']}*")
    else:
        st.info(f"No events scheduled for {current_city} yet.")

# ------------------------------------------
# HOTEL & TRANSIT VIEW (CRITICAL FOR TAXIS)
# ------------------------------------------
else:
    bookings_db = (
        supabase.table("bookings_log")
        .select("*")
        .eq("trip_id", ACTIVE_TRIP_ID)
        .eq("city_cluster", current_city)
        .execute()
    )
    
    if bookings_db.data:
        for booking in bookings_db.data:
            with st.container(border=True):
                st.markdown(f"## {booking['booking_type']} Details")
                st.markdown(f"**Company/Provider:** {booking['provider']}")
                if booking['reference_code']:
                    st.markdown(f"**Confirmation Code (Show to Agent):**\n# `{booking['reference_code']}`")
                
                # Big card configuration for showing to Chinese drivers
                if booking['address_chinese']:
                    st.markdown("### 🚖 SHOW THIS TO THE TAXI DRIVER:")
                    st.markdown(
                        f'<div class="chinese-card"><h1>{booking["address_chinese"]}</h1></div>', 
                        unsafe_allow_input=True
                    )
                if booking['emergency_contact']:
                    st.markdown(f"📞 **Phone Number:** {booking['emergency_contact']}")
    else:
        st.info(f"No booking tickets logged for {current_city}.")