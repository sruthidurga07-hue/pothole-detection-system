import streamlit as st
import urllib.parse
import datetime
from geopy.geocoders import Nominatim
from twilio.rest import Client

# Location component
from streamlit_geolocation import streamlit_geolocation


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Pothole Detection & Alert System",
    page_icon="🛣️",
    layout="centered"
)

st.title("🛣️ Road Safety & Pothole Tracking System")
st.write("Detect potholes and send road safety alerts to the authority.")


# --------------------------------------------------
# NOMINATIM
# --------------------------------------------------

geolocator = Nominatim(
    user_agent="pothole_detection_alert_system"
)


# --------------------------------------------------
# GET AREA NAME
# --------------------------------------------------

def get_live_area_name(lat, lng):

    try:
        location = geolocator.reverse(
            (lat, lng),
            timeout=10,
            language="en"
        )

        if location:

            address = location.raw.get("address", {})

            area = (
                address.get("suburb")
                or address.get("village")
                or address.get("town")
                or address.get("city")
                or address.get("county")
                or address.get("state_district")
            )

            if area:
                return area

            return location.address.split(",")[0]

    except Exception:
        pass

    return "Detected Area"


# --------------------------------------------------
# SEND SMS USING TWILIO
# --------------------------------------------------

def send_sms_alert(area_name, lat, lng, count):

    try:

        # Read credentials from Streamlit Secrets
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        twilio_number = st.secrets["TWILIO_PHONE_NUMBER"]
        authority_number = st.secrets["AUTHORITY_PHONE_NUMBER"]

        client = Client(
            account_sid,
            auth_token
        )

        map_url = f"https://maps.google.com/?q={lat},{lng}"

        sms_text = (
            f"URGENT ROAD ALERT!\n"
            f"{count} pothole(s) detected.\n"
            f"Area: {area_name}\n"
            f"Location: {map_url}"
        )

        message = client.messages.create(
            body=sms_text,
            from_=twilio_number,
            to=authority_number
        )

        return True, message.sid

    except Exception as e:

        return False, str(e)


# --------------------------------------------------
# LOCATION
# --------------------------------------------------

st.subheader("📍 Current Location")

st.info(
    "Click the button below and allow location permission "
    "when your browser asks."
)

location = streamlit_geolocation()


# --------------------------------------------------
# LOCATION RESULT
# --------------------------------------------------

if location:

    lat = location.get("latitude")
    lng = location.get("longitude")

    if lat is not None and lng is not None:

        st.success("📍 Device location detected successfully!")

        st.write(
            f"**Latitude:** {lat:.6f}"
        )

        st.write(
            f"**Longitude:** {lng:.6f}"
        )

        # Get area
        area_name = get_live_area_name(
            lat,
            lng
        )

        st.markdown(
            f"### 🏘️ Identified Area: **{area_name}**"
        )

        # Map
        st.map(
            [
                {
                    "lat": lat,
                    "lon": lng
                }
            ]
        )

        # Google Maps
        map_url = (
            f"https://maps.google.com/"
            f"?q={lat},{lng}"
        )

        st.link_button(
            "🗺️ Open Location in Google Maps",
            map_url
        )

        st.session_state["latitude"] = lat
        st.session_state["longitude"] = lng
        st.session_state["area_name"] = area_name

    else:

        st.warning(
            "Location was not received. "
            "Please allow location permission and try again."
        )

else:

    st.warning(
        "📍 Click the location button above and "
        "allow browser location permission."
    )


# --------------------------------------------------
# POTHOLE COUNT
# --------------------------------------------------

st.divider()

st.subheader("🚨 Pothole Detection Result")

pothole_count = st.number_input(
    "Number of Potholes Detected",
    min_value=1,
    value=1,
    step=1
)

st.session_state["pothole_count"] = pothole_count

st.write(
    f"🔎 **Potholes detected:** {pothole_count}"
)


# --------------------------------------------------
# AUTHORITY EMAIL
# --------------------------------------------------

st.divider()

st.subheader("📢 Report to Authority")

auth_email = st.text_input(
    "Authority Email Address",
    value="sruthi.durga07@gmail.com"
)


# --------------------------------------------------
# DISPATCH BUTTON
# --------------------------------------------------

if st.button(
    "🚀 Dispatch Report (Email & SMS)",
    use_container_width=True
):

    # Check location
    if (
        "latitude" not in st.session_state
        or "longitude" not in st.session_state
    ):

        st.error(
            "❌ Location not available. "
            "Please enable location first."
        )

    else:

        lat = st.session_state["latitude"]
        lng = st.session_state["longitude"]
        area_name = st.session_state["area_name"]

        # --------------------------------------------------
        # SMS
        # --------------------------------------------------

        sms_status, sms_result = send_sms_alert(
            area_name,
            lat,
            lng,
            pothole_count
        )

        if sms_status:

            st.success(
                "📱 SMS Alert sent successfully!"
            )

        else:

            st.error(
                "❌ SMS could not be sent."
            )

            st.code(
                sms_result
            )


        # --------------------------------------------------
        # EMAIL BODY
        # --------------------------------------------------

        current_time = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        map_url = (
            f"https://maps.google.com/"
            f"?q={lat},{lng}"
        )

        subject = (
            f"URGENT ROAD ALERT: "
            f"{pothole_count} Pothole(s) at {area_name}"
        )

        body = f"""
Road Safety Pothole Alert System Report

Location Area: {area_name}

Total Potholes Found: {pothole_count}

GPS Coordinates:
Latitude: {lat}
Longitude: {lng}

Live Map:
{map_url}

Date & Time:
{current_time}

Please initiate immediate road maintenance action.
"""


        # --------------------------------------------------
        # EMAIL LINKS
        # --------------------------------------------------

        gmail_web_url = (
            "https://mail.google.com/mail/"
            "?view=cm&fs=1"
            f"&to={urllib.parse.quote(auth_email)}"
            f"&su={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(body)}"
        )

        mailto_url = (
            f"mailto:{auth_email}"
            f"?subject={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(body)}"
        )


        st.success(
            "✅ Email Alert Report Generated!"
        )

        st.markdown(
            f"""
            <div style="text-align:center;">

            <a href="{mailto_url}"
            target="_blank"
            style="
            display:block;
            padding:12px;
            background-color:#28a745;
            color:white;
            text-decoration:none;
            border-radius:8px;
            font-weight:bold;
            margin-bottom:10px;
            ">
            📱 Open Mobile Mail App
            </a>

            <a href="{gmail_web_url}"
            target="_blank"
            style="
            display:block;
            padding:12px;
            background-color:#007bff;
            color:white;
            text-decoration:none;
            border-radius:8px;
            font-weight:bold;
            ">
            🌐 Open Gmail
            </a>

            </div>
            """,
            unsafe_allow_html=True
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "🛣️ Pothole Detection & Road Safety Alert System"
)
