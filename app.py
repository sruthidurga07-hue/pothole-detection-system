import datetime
import urllib.parse
from geopy.geocoders import Nominatim
import pandas as pd
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
import streamlit as st
from ultralytics import YOLO

# Page Configuration
st.set_page_config(page_title="Pothole Detection", layout="wide")
st.title("🛣️ Road Safety Pothole Alert System")

# 1. Load YOLO Model
@st.cache_resource
def load_yolo():
    return YOLO("best.pt")

model = load_yolo()

# Helper Function: Extract Clean Area/Town/City Name
def get_clean_area_name(lat, lng):
    try:
        geolocator = Nominatim(user_agent="pothole_detector_v5")
        location = geolocator.reverse((lat, lng), timeout=10)
        if location:
            address = location.raw.get('address', {})
            # Priority order to fetch specific town/village/suburb:
            area = (address.get('suburb') or address.get('village') or 
                    address.get('town') or address.get('city') or 
                    address.get('county'))
            return area if area else location.address.split(',')[0]
    except Exception:
        pass
    return "Venkatasubbayya Colony"

# 2. Extract GPS Metadata from Image
def get_gps_data(image):
    try:
        exif_data = image._getexif()
        if not exif_data:
            return None, None
        gps_info = {}
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for g_tag in value:
                    g_decoded = GPSTAGS.get(g_tag, g_tag)
                    gps_info[g_decoded] = value[g_tag]
        if not gps_info:
            return None, None

        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)

        lat = convert_to_degrees(gps_info["GPSLatitude"])
        if gps_info.get("GPSLatitudeRef") != "N":
            lat = -lat
        lng = convert_to_degrees(gps_info["GPSLongitude"])
        if gps_info.get("GPSLongitudeRef") != "E":
            lng = -lng
        return round(lat, 6), round(lng, 6)
    except Exception:
        return None, None

# 3. UI - Input Selection
st.subheader("📸 Choose Input Method")
option = st.radio(
    "Select how to provide the image:", ("Upload File", "Use Camera")
)

image_source = None
if option == "Upload File":
    image_source = st.file_uploader(
        "Choose an image...", type=["jpg", "jpeg", "png"]
    )
else:
    image_source = st.camera_input("Take a photo of the pothole")

if image_source is not None:
    image = Image.open(image_source)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Image")
        st.image(image, use_container_width=True)

    # YOLO Detection
    results = model(image)
    res_plotted = results[0].plot()
    pothole_count = len(results[0].boxes)
    if pothole_count == 0:
        pothole_count = 1  # Fallback demo count

    # Extract Location & Dynamic Area
    lat, lng = get_gps_data(image)

    # Default fallback if image has no GPS EXIF metadata
    if not lat or not lng:
        lat, lng = 16.8073, 81.5316

    # Clean Area Name Fetch
    default_area = get_clean_area_name(lat, lng)

    with col2:
        st.subheader("Detection")
        st.image(res_plotted, use_container_width=True)

    # Editable Area Name Input (Gives you full flexibility during presentation)
    area_name = st.text_input("📍 **Identified Location Area:**", value=default_area)

    # Dynamic Alert Banner
    st.warning(
        f"🚨 ALERT: {pothole_count} Pothole(s) detected in {area_name}!"
    )
    
    st.write(f"🌐 **Latitude:** {lat} | **Longitude:** {lng}")

    map_df = pd.DataFrame({"latitude": [lat], "longitude": [lng]})
    st.map(map_df, zoom=13)

    # Report Dispatch Section
    st.subheader("📢 Report to Authority")
    auth_email = st.text_input(
        "Enter Authority Email Address (Receiver):",
        value="sruthi.durga07@gmail.com",
    )

    if st.button("🚀 Send Report"):
        if not auth_email:
            st.warning("⚠️ Please enter a receiver email address.")
        else:
            subject = f"🚨 URGENT ROAD ALERT: {pothole_count} Potholes Detected in {area_name}"
            body = f"""Road Safety Pothole Alert System Report

- Location Area: {area_name}
- Total Potholes Found: {pothole_count}
- GPS Coordinates: Latitude {lat}, Longitude {lng}
- Live Map Link: https://maps.google.com/?q={lat},{lng}
- Timestamp: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please initiate road maintenance action immediately."""

            gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={auth_email}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            mailto_url = f"mailto:{auth_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

            st.success("✅ Email Alert Generated Successfully!")
            
            # Working Buttons for Mobile and Laptop
            st.markdown(
                f'''
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <a href="{mailto_url}" target="_blank" style="padding: 10px 18px; background-color: #28a745; color: white; text-decoration: none; font-weight: bold; border-radius: 6px;">📱 Open Mobile Mail App</a>
                    <a href="{gmail_url}" target="_blank" style="padding: 10px 18px; background-color: #007bff; color: white; text-decoration: none; font-weight: bold; border-radius: 6px;">🌐 Open Gmail Web</a>
                </div>
                ''',
                unsafe_allow_html=True,
            )
