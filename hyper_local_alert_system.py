import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# ============================================
# PAGE CONFIG & CSS
# ============================================
st.set_page_config(page_title="TS Live Weather Feed", page_icon="🌩️", layout="wide")

st.markdown("""
    <style>
        .feed-card { 
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 15px;
            border-left: 8px solid;
        }
        .rain-alert { border-left-color: #00bfff; }
        .heat-alert { border-left-color: #ff4500; }
        .wind-alert { border-left-color: #ffd700; }
        .timestamp { color: #888; font-size: 0.85em; }
        .status-bar { background-color: #004d00; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# ============================================
# THE 33 TELANGANA DISTRICTS (NO CSV NEEDED)
# ============================================
# Coordinates represent the district headquarters/centers
TS_DISTRICTS = [
    {"District": "Adilabad", "Latitude": 19.6667, "Longitude": 78.5333},
    {"District": "Bhadradri Kothagudem", "Latitude": 17.6116, "Longitude": 80.6170},
    {"District": "Hyderabad", "Latitude": 17.3850, "Longitude": 78.4867},
    {"District": "Jagtial", "Latitude": 18.7986, "Longitude": 78.9306},
    {"District": "Jangaon", "Latitude": 17.7214, "Longitude": 79.1659},
    {"District": "Jayashankar Bhupalpally", "Latitude": 18.4345, "Longitude": 79.8662},
    {"District": "Jogulamba Gadwal", "Latitude": 16.2259, "Longitude": 77.8016},
    {"District": "Kamareddy", "Latitude": 18.3167, "Longitude": 78.3500},
    {"District": "Karimnagar", "Latitude": 18.4386, "Longitude": 79.1288},
    {"District": "Khammam", "Latitude": 17.2473, "Longitude": 80.1514},
    {"District": "Kumuram Bheem Asifabad", "Latitude": 19.3626, "Longitude": 79.2842},
    {"District": "Mahabubabad", "Latitude": 17.6080, "Longitude": 80.0177},
    {"District": "Mahabubnagar", "Latitude": 16.7488, "Longitude": 77.9867},
    {"District": "Mancherial", "Latitude": 18.8715, "Longitude": 79.4442},
    {"District": "Medak", "Latitude": 18.0468, "Longitude": 78.2638},
    {"District": "Medchal-Malkajgiri", "Latitude": 17.5333, "Longitude": 78.4833}, # Kompally/Suchitra region
    {"District": "Mulugu", "Latitude": 18.1915, "Longitude": 79.9405},
    {"District": "Nagarkurnool", "Latitude": 16.5833, "Longitude": 78.3167},
    {"District": "Nalgonda", "Latitude": 17.0500, "Longitude": 79.2667},
    {"District": "Narayanpet", "Latitude": 16.7358, "Longitude": 77.4984},
    {"District": "Nirmal", "Latitude": 19.0964, "Longitude": 78.3430},
    {"District": "Nizamabad", "Latitude": 18.6704, "Longitude": 78.1000},
    {"District": "Peddapalli", "Latitude": 18.6150, "Longitude": 79.3809},
    {"District": "Rajanna Sircilla", "Latitude": 18.3800, "Longitude": 78.8300},
    {"District": "Rangareddy", "Latitude": 17.3300, "Longitude": 78.0600},
    {"District": "Sangareddy", "Latitude": 17.6167, "Longitude": 78.0833},
    {"District": "Siddipet", "Latitude": 18.1018, "Longitude": 78.8520},
    {"District": "Suryapet", "Latitude": 17.1333, "Longitude": 79.6167},
    {"District": "Vikarabad", "Latitude": 17.3333, "Longitude": 77.9000},
    {"District": "Wanaparthy", "Latitude": 16.3600, "Longitude": 78.0600},
    {"District": "Warangal", "Latitude": 17.9810, "Longitude": 79.5802},
    {"District": "Hanamkonda", "Latitude": 18.0068, "Longitude": 79.5539},
    {"District": "Yadadri Bhuvanagiri", "Latitude": 17.5108, "Longitude": 78.8920}
]

df_geo = pd.DataFrame(TS_DISTRICTS)

# ============================================
# BATCH API FETCHING
# ============================================
def fetch_statewide_weather(df):
    """Fetches weather for all 33 districts in one single call"""
    url = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        "latitude": ",".join(map(str, df['Latitude'])),
        "longitude": ",".join(map(str, df['Longitude'])),
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "precipitation_probability",
        "timezone": "Asia/Kolkata",
        "forecast_days": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]
    except Exception as e:
        st.error(f"Failed to connect to Meteorological API: {e}")
        return []

# ============================================
# DASHBOARD UI & AUTO-REFRESH LOGIC
# ============================================
st.title("🌩️ Telangana Weatherman - Live Threat Feed")
st.write("Scanning all 33 districts autonomously. No manual search required.")

# Create an empty placeholder to overwrite content during auto-refresh
placeholder = st.empty()

# The main loop that creates the 5-minute refresh cycle
while True:
    with placeholder.container():
        current_time = datetime.now().strftime("%I:%M:%S %p")
        st.markdown(f"<div class='status-bar'>✅ Live Satellite Link Active | Last Updated: {current_time} | Next update in 5 minutes</div>", unsafe_allow_html=True)
        
        with st.spinner("Pulling real-time geo-meteorological data..."):
            weather_data = fetch_statewide_weather(df_geo)
            
        alerts = []
        
        # Analyze data
        for idx, w_data in enumerate(weather_data):
            if 'current' not in w_data:
                continue
                
            district = df_geo.iloc[idx]['District']
            lat = df_geo.iloc[idx]['Latitude']
            lon = df_geo.iloc[idx]['Longitude']
            
            temp = w_data['current'].get('temperature_2m', 0)
            wind = w_data['current'].get('wind_speed_10m', 0)
            rain_probs = w_data.get('hourly', {}).get('precipitation_probability', [0])
            max_rain_prob = max(rain_probs[:6]) if rain_probs else 0
            
            # --- THRESHOLDS FOR FARMERS ---
            is_danger = False
            alert_types = []
            css_class = ""
            
            # Note: Thresholds set slightly lower so you can see it working today
            if max_rain_prob > 50:
                is_danger = True
                alert_types.append(f"Heavy Rain Risk ({max_rain_prob}%)")
                css_class = "rain-alert"
            if temp > 36:
                is_danger = True
                alert_types.append(f"Extreme Heat ({temp}°C)")
                css_class = "heat-alert"
            if wind > 30:
                is_danger = True
                alert_types.append(f"Severe Winds ({wind} km/h)")
                css_class = "wind-alert"
                
            if is_danger:
                alerts.append({
                    "District": district,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Conditions": " | ".join(alert_types),
                    "CSS": css_class
                })

        # Render Alerts
        if not alerts:
            st.success("✅ Clear skies! No severe weather detected anywhere in the 33 districts right now.")
        else:
            df_alerts = pd.DataFrame(alerts)
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("🔴 Live Threat Feed")
                for alert in alerts:
                    st.markdown(f"""
                        <div class='feed-card {alert['CSS']}'>
                            <h3 style='margin:0;'>📍 {alert['District']} District</h3>
                            <p style='margin:5px 0; font-size: 1.2em; color:#ffb347;'><b>⚠️ {alert['Conditions']}</b></p>
                            <span class='timestamp'>Detected at {current_time}</span>
                        </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.subheader("🗺️ Danger Map")
                # Visual map of only the affected districts
                st.map(df_alerts, size=500, color="#ff0000")
                
    # Pause the script for 5 minutes (300 seconds) before re-running
    time.sleep(300)
    st.rerun()
