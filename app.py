import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="Trip Hub", layout="centered")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# Define the logical city sequence for the 28-day itinerary
CITY_SEQUENCE = ["Beijing", "Luoyang", "Xi'an", "Chongqing", "Yangtze Cruise", "Chengdu"]
ACTIVE_TRIP_ID = "CHINA2027"

st.title("🇨🇳 Global Travel Sync")
st.caption("Context-Aware Multi-City Dynamic Planner")

# ==========================================
# CRITICAL COMPONENT: THE GLOBAL CITY FILTER
# ==========================================
# This acts as the single source of truth for the rest of the UI tabs
selected_city = st.selectbox(
    "📍 Select Current Location Hub:", 
    options=CITY_SEQUENCE,
    index=0
)

st.markdown("---")

# Mobile UI Navigation Tabs
t_itin, t_stay, t_vlog = st.tabs(["🗺️ Isolate Plan", "🏨 Hotel Log", "🎬 Vlog Checklist"])

# ------------------------------------------
# TAB 1: DYNAMIC DAILY ITINERARY VIEW
# ------------------------------------------
with t_itin:
    st.subheader(f"Schedule: {selected_city}")
    
    # Query Supabase for slots explicitly tied to the selected city context
    itin_db = (
        supabase.table("daily_itinerary")
        .select("*")
        .eq("trip_id", ACTIVE_TRIP_ID)
        .eq("city_cluster", selected_city)
        .order("date")
        .execute()
    )
    
    if itin_db.data:
        for idx, item in enumerate(itin_db.data):
            # Parse friendly date structure
            parsed_date = datetime.strptime(item['date'], "%Y-%m-%d").strftime("%b %d")
            
            with st.expander(f"Day {item['day_number']} | {parsed_date} ({item['time_label']})"):
                st.markdown(f"**⚡ Activity:** {item['activity']}")
                if item['location_name']:
                    st.markdown(f"**📍 Target Location:** `{item['location_name']}`")
                if item['notes']:
                    st.info(f"📝 **Notes:** {item['notes']}")
    else:
        st.info(f"No itinerary items scheduled under the {selected_city} cluster.")

# ------------------------------------------
# TAB 2: DYNAMIC CONTEXT-AWARE STAY & TRANSIT LOG
# ------------------------------------------
with t_stay:
    st.subheader(f"Bookings & Transit in {selected_city}")
    
    # Query for flights, trains, cruises, or hotels matching this specific city cluster
    bookings_db = (
        supabase.table("bookings_log")
        .select("*")
        .eq("trip_id", ACTIVE_TRIP_ID)
        .eq("city_cluster", selected_city)
        .order("date_time")
        .execute()
    )
    
    if bookings_db.data:
        for booking in bookings_db.data:
            b_time = datetime.fromisoformat(booking['date_time'].replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M") if booking['date_time'] else "N/A"
            
            with st.container(border=True):
                st.markdown(f"### {booking['booking_type']} • {booking['provider']}")
                st.markdown(f"**📅 Schedule/Check-in:** `{b_time}`")
                if booking['reference_code']:
                    st.markdown(f"**Confirmation Code:** `{booking['reference_code']}`")
                if booking['address_chinese']:
                    st.warning(f"🇨🇳 **Local Address (For Taxi):** {booking['address_chinese']}")
                if booking['emergency_contact']:
                    st.markdown(f"📞 **Contact:** {booking['emergency_contact']}")
    else:
        st.info(f"No explicit booking items linked to {selected_city} found.")

# ------------------------------------------
# TAB 3: DYNAMIC VLOG PRODUCTION PLANNER
# ------------------------------------------
with t_vlog:
    st.subheader(f"Shot List Context: {selected_city}")
    
    # Query shot list isolated exclusively to the locations you are moving through today
    vlog_db = (
        supabase.table("vlog_tracker")
        .select("*")
        .eq("trip_id", ACTIVE_TRIP_ID)
        .eq("city_cluster", selected_city)
        .execute()
    )
    
    if vlog_db.data:
        v_df = pd.DataFrame(vlog_db.data)
        
        # Interactive status updates directly on the data view layout
        for idx, shot in v_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{shot['shot_type']}** - {shot['scene_description']}")
                with col2:
                    # Dynamically check off state live to the cloud database
                    current_status = shot['status']
                    is_captured = current_status == "Captured"
                    
                    action = st.checkbox("Captured", value=is_captured, key=f"vlog_chk_{shot['id']}")
                    new_status = "Captured" if action else "To Film"
                    
                    if new_status != current_status:
                        supabase.table("vlog_tracker").update({"status": new_status}).eq("id", int(shot['id'])).execute()
                        st.rerun()
    else:
        st.info(f"No custom vlog scripts mapped for {selected_city} yet.")