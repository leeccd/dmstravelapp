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
    html, body, [class*="css"] {
        font-size: 19px !important;
    }
    .stButton button {
        width: 100% !important;
        height: 60px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
    }
    .chinese-card {
        background-color: #FFF9E6;
        border: 3px solid #FFA500;
        padding: 20px;
        border-radius: 15px;
        color: #000000;
    }
    /* Distinct styling for administrative controls */
    .admin-box {
        background-color: #F0F2F6;
        border: 2px dashed #31333F;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
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

# Check URL parameters for admin authorization link rule
# Access via: https://your-app.streamlit.app/?role=admin
is_admin = st.query_params.get("role") == "admin"

# ==============================================================================
# 4. TYPOGRAPHY HEADER & NAVIGATION
# ==============================================================================
st.markdown("# 🇨🇳 FAMILY TRAVEL GUIDE")

if is_admin:
    st.markdown('<div class="admin-box">⚡ <b>Admin Mode Active</b>: Data writing enabled.</div>', unsafe_allow_html=True)

st.markdown("### Tap your current city below to see today's plan:")

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

view_mode = st.radio("What do you want to see?", ["🗺️ Today's Schedule", "🏨 Hotel & Train Tickets"], horizontal=True)

# ==============================================================================
# 5. DYNAMIC SCHEDULE ENGINE (WITH INLINE EDITING FOR ADMIN)
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
                    
                    # ADMIN COMPONENT: EDIT/DELETE EXISTING ITEMS
                    if is_admin:
                        with st.expander("🛠️ Edit This Block"):
                            with st.form(key=f"edit_form_{item.get('id')}"):
                                edit_activity = st.text_input("Edit Activity Description", value=item.get('activity', ''))
                                edit_time = st.text_input("Edit Time Label", value=item.get('time_label', ''))
                                edit_loc = st.text_input("Edit Place Name", value=item.get('location_name', ''))
                                edit_notes = st.text_area("Edit Tips/Notes", value=item.get('notes', ''))
                                
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.form_submit_button("💾 Save Changes"):
                                        supabase.table("daily_itinerary").update({
                                            "activity": edit_activity,
                                            "time_label": edit_time,
                                            "location_name": edit_loc,
                                            "notes": edit_notes
                                        }).eq("id", item.get("id")).execute()
                                        st.success("Changes Saved!")
                                        st.rerun()
                                with c2:
                                    if st.form_submit_button("🗑️ Delete Item"):
                                        supabase.table("daily_itinerary").delete().eq("id", item.get("id")).execute()
                                        st.warning("Item Removed.")
                                        st.rerun()
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
                    b_type = booking.get('booking_type', 'Booking Log Item')
                    provider = booking.get('provider', 'Not Specified')
                    ref_code = booking.get('reference_code')
                    addr_zh = booking.get('address_chinese')
                    contact = booking.get('emergency_contact')

                    st.markdown(f"## {b_type} Details")
                    st.markdown(f"**Company/Provider:** {provider}")
                    
                    if ref_code:
                        st.markdown(f"**Confirmation Code (Show to Agent):**\n# `{ref_code}`")
                    
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

# ==============================================================================
# 7. GLOBAL ADMIN ENTRY FORM (FLOATS AT BOTTOM FOR CREATING NEW ENTRIES)
# ==============================================================================
if is_admin:
    st.markdown("---")
    st.markdown("## ➕ Add New Itinerary Record")
    
    with st.form(key="global_add_itinerary", clear_on_submit=True):
        new_date = st.date_input("Target Date", value=datetime.today())
        new_day = st.number_input("Itinerary Day Number (e.g., Day 1)", min_value=1, step=1)
        new_time = st.text_input("Time Window Label (e.g., Morning, 14:00, Full Day)", value="Morning")
        new_act = st.text_input("Activity Description *")
        new_place = st.text_input("Location/Venue Name")
        new_notes = st.text_area("Internal Travel Guidelines / Tips")
        
        if st.form_submit_button("🚀 Publish to Cloud Database"):
            if not new_act:
                st.error("Activity Description is required.")
            else:
                try:
                    supabase.table("daily_itinerary").insert({
                        "trip_id": ACTIVE_TRIP_ID,
                        "city_cluster": current_city,
                        "day_number": int(new_day),
                        "date": new_date.strftime("%Y-%m-%d"),
                        "time_label": new_time,
                        "activity": new_act,
                        "location_name": new_place,
                        "notes": new_notes
                    }).execute()
                    st.success(f"Successfully pinned to database under {current_city}!")
                    st.rerun()
                except Exception as ins_err:
                    st.error(f"Failed to post record: {ins_err}")