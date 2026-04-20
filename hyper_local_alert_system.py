import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from functools import lru_cache
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Hyper-Local Weather Alerts - Telangana",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Playfair+Display:wght@700&display=swap');
        
        * { font-family: 'Poppins', sans-serif; }
        
        h1 {
            font-family: 'Playfair Display', serif;
            color: #1a472a;
            text-align: center;
            font-size: 3em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        h2 {
            color: #2d6a4f;
            border-bottom: 3px solid #40916c;
            padding-bottom: 10px;
        }
        
        .severe-storm-alert {
            background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 8px solid #990000;
            margin: 15px 0;
            font-size: 1.1em;
            font-weight: 600;
            animation: pulse-red 1.5s infinite;
        }
        
        @keyframes pulse-red {
            0%, 100% { box-shadow: 0 0 20px rgba(255,68,68,0.5); }
            50% { box-shadow: 0 0 40px rgba(255,68,68,0.8); }
        }
        
        .moderate-storm-alert {
            background: linear-gradient(135deg, #FF6B35 0%, #FF8C00 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 8px solid #CC3300;
            margin: 10px 0;
        }
        
        .safe-alert {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 8px solid #2E7D32;
            margin: 10px 0;
        }
        
        .mandal-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-left: 5px solid #40916c;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .time-info {
            text-align: center;
            color: #666;
            font-size: 1.1em;
            margin: 15px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        
        .forecast-box {
            background: linear-gradient(135deg, #fff9e6 0%, #fffacd 100%);
            border-left: 5px solid #FFC107;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .high-temp-warning {
            background: linear-gradient(135deg, #ffcccc 0%, #ff9999 100%);
            color: #8B0000;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 5px 0;
            font-weight: 600;
        }
        
        .high-rain-warning {
            background: linear-gradient(135deg, #99ccff 0%, #6699ff 100%);
            color: #001a4d;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 5px 0;
            font-weight: 600;
        }
        
        .priority-section {
            background: linear-gradient(135deg, #ffe6e6 0%, #ffcccc 100%);
            border: 3px solid #FF0000;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .priority-header {
            color: #8B0000;
            font-size: 1.3em;
            font-weight: 700;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================
# TELANGANA MANDALS WITH VILLAGES
# ============================================

TELANGANA_MANDALS_VILLAGES = {
    "Hyderabad": {
        "Hyderabad City": {
            "lat": 17.3850,
            "lon": 78.4867,
            "villages": ["Banjara Hills", "Jubilee Hills", "Kondapur", "Manikonda", "Raidurg"]
        },
        "Kompally": {
            "lat": 17.5042,
            "lon": 78.5640,
            "villages": ["Kompally", "Ameerpet", "Mahabubnagar", "Kapra"]
        },
        "Secunderabad": {
            "lat": 17.3667,
            "lon": 78.5033,
            "villages": ["Secunderabad", "Begumpet", "Bowenpally", "Yapral"]
        },
        "Gachibowli": {
            "lat": 17.4398,
            "lon": 78.5533,
            "villages": ["Gachibowli", "Narsingi", "Manikonda", "HITEC City"]
        },
    },
    "Rangareddy": {
        "Rangareddy": {
            "lat": 17.3850,
            "lon": 78.5500,
            "villages": ["Rangareddy", "Tandur", "Chevella", "Shamirpet"]
        },
        "Vikarabad": {
            "lat": 17.3833,
            "lon": 78.4500,
            "villages": ["Vikarabad", "Tandur", "Bijapur", "Ameerpet"]
        },
    },
    "Medak": {
        "Medak": {
            "lat": 18.7669,
            "lon": 78.2869,
            "villages": ["Medak", "Tandur", "Gajwel", "Wanaparthy"]
        },
        "Sangareddy": {
            "lat": 17.4669,
            "lon": 78.1300,
            "villages": ["Sangareddy", "Gummadidala", "Rudram", "Ameenpur"]
        },
    },
    "Karimnagar": {
        "Karimnagar": {
            "lat": 18.4394,
            "lon": 78.1381,
            "villages": ["Karimnagar", "Jagtial", "Kamkole", "Narsapur"]
        },
        "Jogipet": {
            "lat": 18.5333,
            "lon": 78.3167,
            "villages": ["Jogipet", "Pulkal", "Zaheerabad", "Tandur"]
        },
    },
    "Nizamabad": {
        "Nizamabad": {
            "lat": 19.2757,
            "lon": 78.1368,
            "villages": ["Nizamabad", "Kamareddy", "Armoor", "Tandur"]
        },
    },
    "Khammam": {
        "Khammam": {
            "lat": 17.2505,
            "lon": 79.1206,
            "villages": ["Khammam", "Alair", "Kothagudem", "Chintakunta"]
        },
    },
    "Nalgonda": {
        "Nalgonda": {
            "lat": 17.6869,
            "lon": 79.1300,
            "villages": ["Nalgonda", "Miryalaguda", "Choutuppal", "Tandur"]
        },
    },
    "Adilabad": {
        "Adilabad": {
            "lat": 19.6752,
            "lon": 78.5337,
            "villages": ["Adilabad", "Nirmal", "Kasipet", "Luxettipet"]
        },
    },
}

# ============================================
# FETCH REAL WEATHER DATA WITH HOURLY
# ============================================

@lru_cache(maxsize=256)
def get_weather_for_mandal(lat, lon):
    """Fetch real weather data with hourly forecast"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "timezone": "Asia/Kolkata",
            "forecast_days": 3
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

# ============================================
# ANALYZE 2HR & 6HR FORECASTS FOR VILLAGES
# ============================================

def analyze_2hr_6hr_forecast(weather_data, mandal_name, villages):
    """Analyze next 2 hours and 6 hours for each village"""
    
    if not weather_data:
        return None
    
    try:
        hourly = weather_data.get('hourly', {})
        current = weather_data.get('current', {})
        
        times = hourly.get('time', [])
        temps = hourly.get('temperature_2m', [])
        rain_probs = hourly.get('precipitation_probability', [])
        winds = hourly.get('wind_speed_10m', [])
        
        # Get current time
        now = datetime.now()
        
        # Analyze 2 hours (0-2 hours ahead)
        forecast_2hr = {
            "hours": [],
            "high_temp_villages": [],
            "high_rain_villages": [],
            "avg_temp": 0,
            "max_rain_prob": 0,
            "max_wind": 0
        }
        
        # Analyze 6 hours (2-6 hours ahead)
        forecast_6hr = {
            "hours": [],
            "high_temp_villages": [],
            "high_rain_villages": [],
            "avg_temp": 0,
            "max_rain_prob": 0,
            "max_wind": 0
        }
        
        # Process hourly data
        temps_2hr = []
        temps_6hr = []
        rains_2hr = []
        rains_6hr = []
        winds_2hr = []
        winds_6hr = []
        
        for i in range(min(6, len(temps))):  # Next 6 hours
            temp = temps[i]
            rain = rain_probs[i] if i < len(rain_probs) else 0
            wind = winds[i] if i < len(winds) else 0
            
            if i < 2:  # Next 2 hours
                temps_2hr.append(temp)
                rains_2hr.append(rain)
                winds_2hr.append(wind)
            else:  # 2-6 hours
                temps_6hr.append(temp)
                rains_6hr.append(rain)
                winds_6hr.append(wind)
        
        # Calculate 2HR stats
        if temps_2hr:
            forecast_2hr["avg_temp"] = round(np.mean(temps_2hr), 1)
            forecast_2hr["max_rain_prob"] = round(max(rains_2hr), 1)
            forecast_2hr["max_wind"] = round(max(winds_2hr), 1)
            
            # Classify villages for 2 hours
            if forecast_2hr["avg_temp"] > 35:
                forecast_2hr["high_temp_villages"] = villages
            
            if forecast_2hr["max_rain_prob"] > 70:
                forecast_2hr["high_rain_villages"] = villages
        
        # Calculate 6HR stats
        if temps_6hr:
            forecast_6hr["avg_temp"] = round(np.mean(temps_6hr), 1)
            forecast_6hr["max_rain_prob"] = round(max(rains_6hr), 1)
            forecast_6hr["max_wind"] = round(max(winds_6hr), 1)
            
            # Classify villages for 6 hours
            if forecast_6hr["avg_temp"] > 35:
                forecast_6hr["high_temp_villages"] = villages
            
            if forecast_6hr["max_rain_prob"] > 70:
                forecast_6hr["high_rain_villages"] = villages
        
        return {
            "mandal": mandal_name,
            "villages": villages,
            "forecast_2hr": forecast_2hr,
            "forecast_6hr": forecast_6hr
        }
    
    except Exception as e:
        return None

# ============================================
# ANALYZE WEATHER & GENERATE ALERTS
# ============================================

def analyze_weather_for_alert(weather_data, mandal_name):
    """Analyze real weather and classify severity"""
    
    if not weather_data:
        return None, None
    
    try:
        current = weather_data.get('current', {})
        hourly = weather_data.get('hourly', {})
        
        temp = current.get('temperature_2m', 0)
        humidity = current.get('relative_humidity_2m', 0)
        wind = current.get('wind_speed_10m', 0)
        rain_prob = hourly.get('precipitation_probability', [0])[0] if hourly else 0
        
        # Determine alert level based on REAL data
        if wind > 40 and rain_prob > 80:
            alert_type = "CRITICAL"
            emoji = "⛈️🌨️"
            title = "DANGEROUS HAILSTORMS"
            color = "#8B0000"
        elif wind > 30 and rain_prob > 70:
            alert_type = "HIGH"
            emoji = "⛈️"
            title = "SEVERE STORMS"
            color = "#FF6B35"
        elif rain_prob > 60:
            alert_type = "MODERATE"
            emoji = "🌧️"
            title = "SCATTERED STORMS"
            color = "#FF9800"
        else:
            alert_type = "SAFE"
            emoji = "✅"
            title = "SAFE CONDITIONS"
            color = "#4CAF50"
        
        alert_data = {
            "type": alert_type,
            "emoji": emoji,
            "title": title,
            "color": color,
            "temp": round(temp, 1),
            "humidity": round(humidity, 1),
            "wind": round(wind, 1),
            "rain_prob": round(rain_prob, 1),
            "mandal": mandal_name,
        }
        
        return alert_type, alert_data
    
    except Exception as e:
        return None, None

# ============================================
# GET ALL MANDALS WITH REAL DATA
# ============================================

def get_all_mandals_weather(district):
    """Get weather data for all mandals in a district"""
    
    mandals_data = TELANGANA_MANDALS_VILLAGES.get(district, {})
    
    results = []
    forecasts = []
    
    for mandal_name, mandal_info in mandals_data.items():
        lat = mandal_info["lat"]
        lon = mandal_info["lon"]
        villages = mandal_info["villages"]
        
        weather_data = get_weather_for_mandal(lat, lon)
        alert_type, alert_data = analyze_weather_for_alert(weather_data, mandal_name)
        
        if alert_data:
            alert_data["villages"] = villages
            results.append(alert_data)
        
        # Get 2hr and 6hr forecast
        forecast = analyze_2hr_6hr_forecast(weather_data, mandal_name, villages)
        if forecast:
            forecasts.append(forecast)
    
    return results, forecasts

# ============================================
# MAIN APP
# ============================================

# Display current date and time
current_time = datetime.now().strftime("%A, %d %B %Y | %H:%M:%S IST")
st.markdown(f"<div class='time-info'>📍 Last Updated: {current_time}</div>", unsafe_allow_html=True)

st.markdown("<h1>⛈️ HYPER-LOCAL WEATHER ALERTS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 1.1em;'>Real-Time Mandal & Village Level Severe Weather Warnings</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📍 LOCATION SELECTION")
    
    district = st.selectbox(
        "Select District",
        list(TELANGANA_MANDALS_VILLAGES.keys())
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ DISPLAY OPTIONS")
    
    show_option = st.radio(
        "Show",
        ["Critical Alerts Only", "All Alerts", "All Mandals Data"],
        index=1
    )

# Main content
st.markdown("## 🔴 REAL-TIME WEATHER ALERTS")

# Fetch data for selected district
with st.spinner(f"Fetching real-time data for {district}..."):
    all_alerts, all_forecasts = get_all_mandals_weather(district)

if not all_alerts:
    st.info("No data available. Check internet connection.")
else:
    
    # ============================================
    # PRIORITY SECTION: NEXT 2HR & 6HR FOR FARMERS
    # ============================================
    
    st.markdown("""
    <div class='priority-section'>
    <div class='priority-header'>⚠️ 🌾 FARMER ALERT - NEXT 2 HOURS & 6 HOURS FORECAST 🌾 ⚠️</div>
    <p style='text-align: center; color: #8B0000; font-weight: 600;'>Protect Your Farms! Check High Rain & Temperature Alert Below</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display 2HR and 6HR forecasts
    for forecast in all_forecasts:
        mandal = forecast["mandal"]
        villages = forecast["villages"]
        forecast_2hr = forecast["forecast_2hr"]
        forecast_6hr = forecast["forecast_6hr"]
        
        # Show mandal name
        st.markdown(f"### 📍 {mandal}")
        st.markdown(f"**Villages in this Mandal:** {', '.join(villages)}")
        
        # 2 HOUR FORECAST
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⏱️ NEXT 2 HOURS")
            
            st.markdown(f"""
            <div class='forecast-box'>
            <p><b>🌡️ Avg Temperature:</b> {forecast_2hr['avg_temp']}°C</p>
            <p><b>🌧️ Max Rain Probability:</b> {forecast_2hr['max_rain_prob']}%</p>
            <p><b>💨 Max Wind Speed:</b> {forecast_2hr['max_wind']} km/h</p>
            </div>
            """, unsafe_allow_html=True)
            
            # High Temperature Warning
            if forecast_2hr["high_temp_villages"]:
                st.markdown("<p style='color: #8B0000; font-weight: 700;'>🔥 HIGH TEMPERATURE WARNING:</p>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='high-temp-warning'>
                All Villages: {', '.join(forecast_2hr['high_temp_villages'])}
                <br/>Temperature will be > 35°C
                <br/>⚠️ Protect crops from excessive heat
                </div>
                """, unsafe_allow_html=True)
            
            # High Rain Warning
            if forecast_2hr["high_rain_villages"]:
                st.markdown("<p style='color: #001a4d; font-weight: 700;'>💧 HEAVY RAIN WARNING:</p>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='high-rain-warning'>
                All Villages: {', '.join(forecast_2hr['high_rain_villages'])}
                <br/>Rain Probability > 70%
                <br/>⚠️ URGENT: Cover crops, Secure farm equipment, Prepare for flooding
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### ⏱️ NEXT 6 HOURS (2-6 hrs ahead)")
            
            st.markdown(f"""
            <div class='forecast-box'>
            <p><b>🌡️ Avg Temperature:</b> {forecast_6hr['avg_temp']}°C</p>
            <p><b>🌧️ Max Rain Probability:</b> {forecast_6hr['max_rain_prob']}%</p>
            <p><b>💨 Max Wind Speed:</b> {forecast_6hr['max_wind']} km/h</p>
            </div>
            """, unsafe_allow_html=True)
            
            # High Temperature Warning
            if forecast_6hr["high_temp_villages"]:
                st.markdown("<p style='color: #8B0000; font-weight: 700;'>🔥 HIGH TEMPERATURE WARNING:</p>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='high-temp-warning'>
                All Villages: {', '.join(forecast_6hr['high_temp_villages'])}
                <br/>Temperature will be > 35°C
                <br/>⚠️ Protect crops from excessive heat
                </div>
                """, unsafe_allow_html=True)
            
            # High Rain Warning
            if forecast_6hr["high_rain_villages"]:
                st.markdown("<p style='color: #001a4d; font-weight: 700;'>💧 HEAVY RAIN WARNING:</p>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='high-rain-warning'>
                All Villages: {', '.join(forecast_6hr['high_rain_villages'])}
                <br/>Rain Probability > 70%
                <br/>⚠️ URGENT: Cover crops, Secure farm equipment, Prepare for flooding
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # ============================================
    # CURRENT SEVERE WEATHER ALERTS
    # ============================================
    
    st.markdown("## 🚨 CURRENT SEVERE WEATHER ALERTS")
    
    # Filter alerts based on selection
    if show_option == "Critical Alerts Only":
        critical_alerts = [a for a in all_alerts if a["type"] == "CRITICAL"]
        display_alerts = critical_alerts
    elif show_option == "All Alerts":
        display_alerts = [a for a in all_alerts if a["type"] != "SAFE"]
    else:
        display_alerts = all_alerts
    
    if not display_alerts:
        st.success("✅ No severe weather alerts. All areas safe!")
    else:
        # Display alerts
        for alert in display_alerts:
            
            # Choose styling based on severity
            if alert["type"] == "CRITICAL":
                alert_class = "severe-storm-alert"
            elif alert["type"] == "HIGH":
                alert_class = "severe-storm-alert"
            else:
                alert_class = "moderate-storm-alert"
            
            st.markdown(f"""
            <div class='{alert_class}'>
            <h3>{alert['emoji']} {alert['title']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Show mandal details
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🌡️ Temperature", f"{alert['temp']}°C")
            with col2:
                st.metric("💧 Humidity", f"{alert['humidity']}%")
            with col3:
                st.metric("💨 Wind Speed", f"{alert['wind']} km/h")
            with col4:
                st.metric("🌧️ Rain Prob", f"{alert['rain_prob']}%")
            
            # Show mandal and villages
            st.markdown(f"""
            <div class='mandal-card'>
            <h4>📍 {alert['mandal']}</h4>
            <p><b>Villages Affected:</b> {', '.join(alert['villages'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")

# ============================================
# STATISTICS
# ============================================

st.markdown("## 📊 DISTRICT OVERVIEW")

col1, col2, col3, col4 = st.columns(4)

critical_count = len([a for a in all_alerts if a["type"] == "CRITICAL"])
high_count = len([a for a in all_alerts if a["type"] == "HIGH"])
moderate_count = len([a for a in all_alerts if a["type"] == "MODERATE"])
safe_count = len([a for a in all_alerts if a["type"] == "SAFE"])

with col1:
    st.metric("🔴 Critical", critical_count)
with col2:
    st.metric("🟠 High", high_count)
with col3:
    st.metric("🟡 Moderate", moderate_count)
with col4:
    st.metric("🟢 Safe", safe_count)

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.9em;'>
    <p>💻 Real-Time Hyper-Local Weather Alert System</p>
    <p>🌐 Data: Open-Meteo API (GFS, ECMWF, ICON Models)</p>
    <p>📍 Village-Level Precision | 🔄 Updates Every 5 Minutes</p>
    <p>🌾 Dedicated to Farmer Safety & Crop Protection</p>
    <p>⏰ Last Updated: """ + datetime.now().strftime("%H:%M:%S IST") + """</p>
</div>
""", unsafe_allow_html=True)
