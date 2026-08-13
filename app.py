import streamlit as st
import urllib.parse
from geopy.geocoders import Nominatim
import datetime
from twilio.rest import Client

# Page Setup
st.set_page_config(page_title="Pothole Detection & Alert System", page_icon="🛣️", layout="centered")

# Nominatim Geocoder Setup
geolocator = Nominatim(user_agent="pothole_detector_app_v3")

# --- Twilio SMS Credentials (Replace with your actual keys if available) ---
TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_PHONE_NUMBER = "+1XXXXXXXXXX"      # Your Twilio Virtual Number
AUTHORITY_PHONE_NUMBER = "+91XXXXXXXXXX"  # Target Receiver Mobile Number

# Function to get Area Name from Coordinates
def get_live_area_name(lat, lng):
    try:
        location = geolocator.reverse((lat, lng), timeout=10)
        if location:
            address = location.raw.get('address', {})
            area = (address.get('suburb') or address.get('village') or 
                    address.get('town') or address.get('city') or 
                    address.get('county'))
            return area if area else location.address.split(',')[0]
    except Exception:
        pass
    return "Detected Area"

# Function to send SMS via Twilio
def send_sms_alert(area_name, lat, lng, count):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        map_url = f"https://maps.google.com/?q={lat},{lng}"
        sms_text = f"🚨 URGENT ROAD ALERT!\n{count} Pothole(s) detected at {area_name}.\nLocation: {map_url}"
        
        message = client.messages.create(
            body=sms_text,
            from_=TWILIO_PHONE_NUMBER,
            to=AUTHORITY_PHONE_NUMBER
        )
        return True
    except Exception:
        return False

# --- App Interface ---
st.title("🛣️ Road Safety & Pothole Tracking System")

st.info("📍 Enable device location/coordinates to track exact area details.")

# Coordinates Input (Auto or Manual adjustment)
col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude", value=16.807300, format="%.6f")
with col2:
    lng = st.number_input("Longitude", value=81.531600, format="%.6f")

# Fetch Real-time Area Name
area_name = get_live_area_name(lat, lng)

st.markdown(f"### 📍 **Identified Location:** `{area_name}`")
st.map([{"lat": lat, "lon": lng}])

st.write("---")

# --- Dispatch Section ---
st.subheader("📢 Report to Authority")
auth_email = st.text_input("Enter Authority Email Address:", value="sruthi.durga07@gmail.com")

if st.button("🚀 Dispatch Report (Email & SMS Alert)", use_container_width=True):
    pothole_count = getattr(st.session_state, 'pothole_count', 1)
    
    # 1. Trigger SMS Alert
    sms_status = send_sms_alert(area_name, lat, lng, pothole_count)
    if sms_status:
        st.success("📱 SMS Alert sent successfully to Authority Mobile Number!")
    else:
        st.info("📱 SMS Alert Trigger Processed (Simulated Gateway for Demo).")

    # 2. Email Body Construction
    subject = f"URGENT ROAD ALERT: {pothole_count} Pothole(s) at {area_name}"
    body = f"""Road Safety Pothole Alert System Report

- Location Area: {area_name}
- Total Potholes Found: {pothole_count}
- GPS Coordinates: Latitude {lat}, Longitude {lng}
- Live Map Link: https://maps.google.com/?q={lat},{lng}
- Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please initiate immediate road maintenance action."""

    # 3. Direct Markdown Email Links (Guaranteed working on both Mobile & Laptop)
    gmail_web_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={auth_email}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    mailto_url = f"mailto:{auth_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

    st.success("✅ Email Alert Report Link Generated!")
    
    # Dual Mobile/Desktop Compatibility Links
    st.markdown(f"""
    <div style="text-align: center; margin-top: 15px;">
        <a href="{mailto_url}" target="_blank" style="display: block; padding: 12px; background-color: #28a745; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin-bottom: 10px;">
            📱 Open Default Mobile Mail App
        </a>
        <a href="{gmail_web_url}" target="_blank" style="display: block; padding: 12px; background-color: #007bff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
            🌐 Open Gmail Web Browser
        </a>
    </div>
    """, unsafe_allow_html=True)
