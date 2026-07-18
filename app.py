import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ==============================================================================
# 1. PAGE CONFIGURATION & LAYOUT CONSTRAINTS
# ==============================================================================
st.set_page_config(
    page_title="China Travel Hub", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. INJECT ACCESS-FIRST CSS (LARGE FONTS & TAP TARGETS)
# ==============================================================================
st.markdown("""
<style>
    /* Scale global font sizes for readability */
    html, body, [class*="css"] {
        font-size: 19px !important;
    }
    /* Expand touch sizes for simple mobile interaction */
    .stButton button {
        width: 100% !important;
        height: 60px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
    }
    /* Accessible high-visibility layout container for local taxi drivers */
    .chinese-card {
        background-color: #FFF9E6;
        border: 3px solid #FFA500;
        padding: 20px;
        border-radius: 15px;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. DATABASE HANDSHAKE INITIALIZATION
# ==============================================================================
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Failed to initialize Supabase connection: {e}")
    st.stop()

ACTIVE_TRIP_ID = "CHINA2027"

# ==============================================================================
# 4. TYPOGRAPHY HEADER & NAVIGATION
# ==============================================================================
st.markdown("# 🇨🇳 FAMILY TRAVEL GUIDE")
st.markdown("### Tap your current city below to see today's plan:")

# Initialize session persistence tracking for active regional layout
if "active_city" not in st.session_state:
    st.session_state.active_city = "Beijing"

# Large touch selector block mapping
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

# Navigation switches
view_mode = st.radio("What do you want to see?", ["🗺️ Today's Schedule", "🏨 Hotel & Train Tickets"], horizontal=True)

# ==============================================================================
# 5. DYNAMIC SCHEDULE ENGINE
# ==============================================================================
if view_mode == "🗺️ Today's Schedule":
    try:
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
                # Fallback parse routine if date string patterns contain issues
                try:
                    parsed_date = datetime.strptime(item.get('date', ''), "%Y-%m-%d").strftime("%B %d")
                except:
                    parsed_date = "Scheduled Day"
                
                with st.container(border=True):
                    st.markdown(f"## 📅 {parsed_date}")
                    st.markdown(f"**⏰ Time:** {item.get('time_label', 'All Day')}")
                    st.markdown(f"**🎯 What We Are Doing:**\n# {item.get('activity', 'Rest & Exploration')}")
                    
                    loc_name = item.get('location_name')
                    if loc_name:
                        st.markdown(f"**📍 Place:** `{loc_name}`")
                        
                    notes = item.get('notes')
                    if notes:
                        st.markdown(f"ℹ️ *Tip: {notes}*")
        else:
            st.info(f"📍 No events scheduled for {current_city} yet.")
    except Exception as db_err:
        st.error(f"Database Read Failure (daily_itinerary): {db_err}")

# ==============================================================================
# 6. FAULT-TOLERANT TRANSIT & ACCOMMODATION DATA PIPELINE
# ==============================================================================
else:
    try:
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
                    # Defensive parsing using dictionary keys safely via .get() overrides
                    b_type = booking.get('booking_type', 'Booking Log Item')
                    provider = booking.get('provider', 'Not Specified')
                    ref_code = booking.get('reference_code')
                    addr_zh = booking.get('address_chinese')
                    contact = booking.get('emergency_contact')

                    st.markdown(f"## {b_type} Details")
                    st.markdown(f"**Company/Provider:** {provider}")
                    
                    if ref_code:
                        st.markdown(f"**Confirmation Code (Show to Agent):**\n# `{ref_code}`")
                    
                    # Safely handles localized address string injection dynamically 
                    if addr_zh:
                        st.markdown("### 🚖 SHOW THIS TO THE TAXI DRIVER:")
                        st.markdown(
                            f'<div class="chinese-card"><h1>{addr_zh}</h1></div>', 
                            unsafe_allow_html=True
                        )
                    if contact:
                        st.markdown(f"📞 **Phone Number:** {contact}")
        else:
            st.info(f"📍 No booking details or transit logs saved for {current_city} yet.")
    except Exception as db_err:
        st.error(f"Database Read Failure (bookings_log): {db_err}")
        st.info("💡 Tip: If you haven't run the table creation query in your Supabase SQL editor yet, the table may not be live.")