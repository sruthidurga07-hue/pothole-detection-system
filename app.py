import datetime
import urllib.parse

import pandas as pd
import streamlit as st
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
from geopy.geocoders import Nominatim
from ultralytics import YOLO


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Pothole Detection",
    page_icon="🛣️",
    layout="wide"
)

st.title("🛣️ Road Safety Pothole Detection System")


# =========================================================
# LOAD YOLO MODEL
# =========================================================

@st.cache_resource
def load_model():
    return YOLO("best.pt")


try:
    model = load_model()
except Exception as e:
    st.error("❌ Could not load best.pt")
    st.error(str(e))
    st.stop()


# =========================================================
# GET AREA NAME FROM LATITUDE AND LONGITUDE
# =========================================================

def get_area_name(lat, lon):

    try:

        geolocator = Nominatim(
            user_agent="pothole_detection_system"
        )

        location = geolocator.reverse(
            (lat, lon),
            timeout=10
        )

        if location:

            address = location.raw.get("address", {})

            area = (
                address.get("suburb")
                or address.get("neighbourhood")
                or address.get("village")
                or address.get("town")
                or address.get("city")
                or address.get("municipality")
            )

            if area:
                return area

    except Exception:
        pass

    return None


# =========================================================
# GET GPS FROM PHOTO
# =========================================================

def get_photo_gps(image):

    try:

        exif = image.getexif()

        if not exif:
            return None, None

        gps_info = None

        for tag_id, value in exif.items():

            tag_name = TAGS.get(tag_id, tag_id)

            if tag_name == "GPSInfo":
                gps_info = value
                break

        if not gps_info:
            return None, None

        gps = {}

        for key, value in gps_info.items():

            name = GPSTAGS.get(key, key)

            gps[name] = value

        if (
            "GPSLatitude" not in gps
            or "GPSLongitude" not in gps
        ):
            return None, None

        def convert_to_degrees(value):

            degrees = float(value[0])
            minutes = float(value[1])
            seconds = float(value[2])

            return (
                degrees
                + minutes / 60
                + seconds / 3600
            )

        lat = convert_to_degrees(
            gps["GPSLatitude"]
        )

        lon = convert_to_degrees(
            gps["GPSLongitude"]
        )

        if gps.get("GPSLatitudeRef") == "S":
            lat = -lat

        if gps.get("GPSLongitudeRef") == "W":
            lon = -lon

        return round(lat, 6), round(lon, 6)

    except Exception:
        return None, None


# =========================================================
# INPUT METHOD
# =========================================================

st.subheader("📸 Choose Input Method")

option = st.radio(
    "Select how to provide the image:",
    ["Upload File", "Use Camera"],
    horizontal=True
)

image_source = None


if option == "Upload File":

    image_source = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png"]
    )

else:

    image_source = st.camera_input(
        "Take a photo of the road"
    )


# =========================================================
# PROCESS IMAGE
# =========================================================

if image_source is not None:

    image = Image.open(
        image_source
    ).convert("RGB")


    # =====================================================
    # DISPLAY ORIGINAL IMAGE
    # =====================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📷 Original Image")

        st.image(
            image,
            use_container_width=True
        )


    # =====================================================
    # YOLO DETECTION
    # =====================================================

    with st.spinner(
        "🔍 Detecting potholes..."
    ):

        results = model.predict(
            source=image,
            conf=0.50,
            verbose=False
        )

    result = results[0]


    # =====================================================
    # COUNT POTHOLES
    # =====================================================

    pothole_count = 0

    if result.boxes is not None:

        for box in result.boxes:

            confidence = float(
                box.conf[0]
            )

            class_id = int(
                box.cls[0]
            )

            class_name = str(
                model.names[class_id]
            ).lower()

            # Count only pothole detections
            if (
                "pothole" in class_name
                and confidence >= 0.50
            ):
                pothole_count += 1


    # =====================================================
    # DETECTION RESULT
    # =====================================================

    with col2:

        st.subheader(
            "🔍 Detection Result"
        )

        if pothole_count > 0:

            detected_image = result.plot()

            st.image(
                detected_image,
                use_container_width=True
            )

        else:

            st.image(
                image,
                use_container_width=True
            )


    # =====================================================
    # ALERT
    # =====================================================

    if pothole_count > 0:

        st.error(
            f"🚨 ALERT: {pothole_count} "
            f"pothole(s) detected!"
        )

    else:

        st.success(
            "✅ No pothole detected."
        )


    # =====================================================
    # LOCATION
    # =====================================================

    st.subheader("📍 Location")


    # First try location stored inside photo
    lat, lon = get_photo_gps(
        image
    )


    if lat is not None and lon is not None:

        location_source = (
            "GPS information from photo"
        )

    else:

        lat = None
        lon = None

        location_source = None


    # -----------------------------------------------------
    # LOCATION AVAILABLE
    # -----------------------------------------------------

    if lat is not None and lon is not None:

        area_name = get_area_name(
            lat,
            lon
        )

        if area_name:

            st.info(
                f"📍 **Area:** {area_name}"
            )

        else:

            st.info(
                "📍 **Area:** Area name unavailable"
            )

        st.write(
            f"🌐 **Latitude:** {lat}"
        )

        st.write(
            f"🌐 **Longitude:** {lon}"
        )

        st.caption(
            f"Location source: {location_source}"
        )


        # =================================================
        # MAP
        # =================================================

        st.subheader(
            "🗺️ Location Map"
        )

        map_data = pd.DataFrame(
            {
                "latitude": [lat],
                "longitude": [lon]
            }
        )

        st.map(
            map_data,
            zoom=15
        )


    # -----------------------------------------------------
    # LOCATION NOT AVAILABLE
    # -----------------------------------------------------

    else:

        st.warning(
            "⚠️ Location unavailable."
        )

        st.write(
            "The uploaded image does not contain GPS "
            "location information."
        )

        st.info(
            "For accurate photo location, use the "
            "original camera photo with Location/GPS "
            "enabled."
        )


    # =====================================================
    # REPORT TO AUTHORITY
    # =====================================================

    if pothole_count > 0:

        st.subheader(
            "📢 Report to Authority"
        )

        auth_email = st.text_input(
            "Enter Authority Email Address (Receiver):",
            placeholder="yourmail@gmail.com"
        )


        # -------------------------------------------------
        # SEND REPORT
        # -------------------------------------------------

        if st.button(
            "🚀 Send Report"
        ):

            if not auth_email:

                st.warning(
                    "⚠️ Please enter an email address."
                )

            elif "@" not in auth_email:

                st.error(
                    "❌ Please enter a valid email address."
                )

            elif lat is None or lon is None:

                st.error(
                    "❌ Report cannot be generated "
                    "because real location is unavailable."
                )

            else:

                area_for_mail = (
                    get_area_name(
                        lat,
                        lon
                    )
                    or "Area name unavailable"
                )


                # -----------------------------------------
                # EMAIL SUBJECT
                # -----------------------------------------

                subject = (
                    f"🚨 Pothole Alert - "
                    f"{pothole_count} Pothole(s) "
                    f"Detected in {area_for_mail}"
                )


                # -----------------------------------------
                # EMAIL BODY
                # -----------------------------------------

                body = f"""
ROAD SAFETY POTHOLE DETECTION REPORT

Location Area:
{area_for_mail}

Total Potholes Detected:
{pothole_count}

Latitude:
{lat}

Longitude:
{lon}

Google Maps Location:
https://maps.google.com/?q={lat},{lon}

Detection Time:
{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please take necessary road maintenance action.
"""


                # -----------------------------------------
                # ENCODE EMAIL
                # -----------------------------------------

                encoded_subject = urllib.parse.quote(
                    subject
                )

                encoded_body = urllib.parse.quote(
                    body
                )


                # -----------------------------------------
                # MOBILE MAIL
                # -----------------------------------------

                mobile_mail_url = (
                    f"mailto:{auth_email}"
                    f"?subject={encoded_subject}"
                    f"&body={encoded_body}"
                )


                # -----------------------------------------
                # GMAIL WEB
                # -----------------------------------------

                gmail_url = (
                    "https://mail.google.com/mail/"
                    "?view=cm&fs=1"
                    f"&to={urllib.parse.quote(auth_email)}"
                    f"&su={encoded_subject}"
                    f"&body={encoded_body}"
                )


                # -----------------------------------------
                # SUCCESS MESSAGE
                # -----------------------------------------

                st.success(
                    "✅ Email Alert Generated Successfully!"
                )


                # -----------------------------------------
                # TWO OPTIONS
                # -----------------------------------------

                st.markdown(
                    f"""
                    <div style="
                        display:flex;
                        gap:12px;
                        flex-wrap:wrap;
                        margin-top:15px;
                    ">

                    <a href="{mobile_mail_url}"
                       target="_blank"
                       style="
                       background-color:#28a745;
                       color:white;
                       padding:12px 18px;
                       border-radius:8px;
                       text-decoration:none;
                       font-weight:bold;">
                       📱 Open Mobile Mail App
                    </a>

                    <a href="{gmail_url}"
                       target="_blank"
                       style="
                       background-color:#4285F4;
                       color:white;
                       padding:12px 18px;
                       border-radius:8px;
                       text-decoration:none;
                       font-weight:bold;">
                       🌐 Open Gmail Web
                    </a>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


                st.caption(
                    "Open the preferred mail option and "
                    "press Send to deliver the report."
                )
