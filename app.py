import datetime
import urllib.parse
import pandas as pd
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
import streamlit as st
from ultralytics import YOLO

# Mobile & Desktop Responsive Configuration
st.set_page_config(
    page_title="Pothole Detection", layout="centered", page_icon="🛣️"
)

st.title("🛣️ Road Safety Pothole Alert System")


# Load Model safely with caching
@st.cache_resource
def load_yolo_model():
    return YOLO("best.pt")


model = load_yolo_model()


# Extract GPS Metadata from Image
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
        return lat, lng
    except Exception:
        return None, None


# Input Selection
st.subheader("📸 Choose Input Method")
option = st.radio(
    "Select input source:",
    ("Upload File", "Use Camera"),
    horizontal=True,
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

    # YOLO Detection
    results = model(image)
    res_plotted = results[0].plot()
    pothole_count = len(results[0].boxes)

    # Extract Location
    lat, lng = get_gps_data(image)

    if not lat or not lng:
        lat, lng = 16.8073, 81.5316  # Default Coordinates

    area_name = "Local Area, Andhra Pradesh"

    # Mobile Friendly Tabs
    tab1, tab2 = st.tabs(["🖼️ Detection Result", "📍 Map Location"])

    with tab1:
        st.image(
            res_plotted,
            caption=f"Detected Potholes: {pothole_count}",
            use_container_width=True,
        )

    with tab2:
        st.write(f"📍 **Area:** {area_name}")
        st.write(f"🌐 **Latitude:** {lat} | **Longitude:** {lng}")
        map_df = pd.DataFrame({"latitude": [lat], "longitude": [lng]})
        st.map(map_df, zoom=13)

    # Dynamic Alert Display
    st.warning(
        f"🚨 ALERT: {pothole_count} Pothole(s) detected in {area_name}!"
    )

    # Email Dispatch Section
    st.markdown("---")
    st.subheader("📢 Report to Authority")
    auth_email = st.text_input(
        "Authority Email (Receiver):", value="sruthi.durga07@gmail.com"
    )

    if st.button("🚀 Send Report", use_container_width=True):
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

            st.success("✅ Email Alert Generated!")
            st.markdown(
                f'<a href="{gmail_url}" target="_blank" style="display: block; width: 100%; text-align: center; padding: 14px; background-color: #28a745; color: white; text-decoration: none; font-weight: bold; font-size: 16px; border-radius: 8px;">✉️ Click Here to Dispatch Email Alert</a>',
                unsafe_allow_html=True,
            )
