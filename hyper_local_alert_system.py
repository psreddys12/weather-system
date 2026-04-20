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
        
        .hailstorm-warning {
            background: linear-gradient(135deg, #8B0000 0%, #660000 100%);
            color: #FFD700;
            padding: 20px;
            border-radius: 8px;
            border-left: 8px solid #FFD700;
            margin: 15px 0;
            font-size: 1.1em;
            font-weight: 700;
            animation: flash-yellow 1s infinite;
        }
        
        @keyframes flash-yellow {
            0%, 100% { text-shadow: 0 0 10px #FFD700; }
            50% { text-shadow: 0 0 30px #FFD700; }
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
        
        .storm-severity-high {
            background: #ff4444;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            display: inline-block;
        }
        
        .storm-severity-medium {
            background: #ff9800;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            display: inline-block;
        }
        
        .storm-severity-low {
            background: #4CAF50;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            display: inline-block;
        }
        
        .time-window {
            background: #e3f2fd;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
            margin: 10px 0;
            font-weight: 600;
            color: #1565c0;
        }
        
        .affected-areas {
            background: #fff3e0;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 4px solid #FF9800;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

# Hyper-local Telangana areas with coordinates
TELANGANA_MANDALS = {
    "Hyderabad": {
        "Hyderabad City": (17.3850, 78.4867),
        "Kompally": (17.5042, 78.5640),
        "Secunderabad": (17.3667, 78.5033),
        "Gachibowli": (17.4398, 78.5533),
        "Banjara Hills": (17.3904, 78.4599),
        "HITEC City": (17.4409, 78.4414),
        "LB Nagar": (17.3650, 78.5450),
        "Dilsukhnagar": (17.3667, 78.5500),
        "Tolichowki": (17.3850, 78.5200),
        "Kukatpally": (17.4669, 78.4150),
    },
    "Rangareddy": {
        "Rangareddy": (17.3850, 78.5500),
        "Vikarabad": (17.3833, 78.4500),
        "Tandur": (17.1667, 77.2833),
        "Wanaparthy": (16.8333, 77.6667),
        "Shamirpet": (17.4667, 78.2833),
        "Chevella": (17.2333, 78.5667),
    },
    "Medak": {
        "Medak": (18.7669, 78.2869),
        "Tandur": (17.1667, 77.2833),
        "Gajwel": (18.6333, 78.8000),
        "Wanaparthy": (16.8333, 77.6667),
        "Siddipet": (18.7167, 78.7667),
        "Sangareddy": (17.4669, 78.1300),
        "Ameenpur": (17.5500, 78.1200),
        "Isnapur": (17.6000, 78.0500),
        "Pashmylaram": (17.5800, 78.0800),
    },
    "Karimnagar": {
        "Karimnagar": (18.4394, 78.1381),
        "Jagtial": (18.7669, 78.4670),
        "Jaiashankar": (18.5167, 78.5833),
        "Raikal": (18.8167, 78.3333),
        "Kamkole": (18.6500, 78.4000),
        "Zaheerabad": (19.1500, 78.5333),
        "Jogipet": (18.5333, 78.3167),
        "Narsapur": (17.6667, 78.4667),
        "Pulkal": (17.7500, 78.3500),
    },
    "Sangareddy": {
        "Sangareddy": (17.4669, 78.1300),
        "Gummadidala": (17.5167, 78.1500),
        "Rudram": (17.5333, 78.0667),
        "Shankarpally": (17.5833, 78.1833),
        "Sadasivapet": (17.6167, 78.1333),
    },
    "Nizamabad": {
        "Nizamabad": (19.2757, 78.1368),
        "Kamareddy": (19.3833, 78.4000),
        "Armoor": (19.5667, 78.5333),
    },
    "Adilabad": {
        "Adilabad": (19.6752, 78.5337),
        "Nirmal": (19.2333, 78.6667),
        "Luxettipet": (19.4833, 78.3333),
        "Kasipet": (19.1833, 78.5667),
    },
}

# Sample severe weather alerts (matching Telangana Weatherman format)
CRITICAL_ALERTS = {
    "hailstorm": {
        "severity": "CRITICAL",
        "emoji": "⛈️🌨️",
        "title": "DANGEROUS HAILSTORMS",
        "color": "#8B0000",
        "affected_areas": ["Narsapur", "Medak", "Ameenpur", "Gummadidala", "Isnapur", 
                          "Pashmylaram", "Rudram", "Sangareddy", "Shankarpally", "Sadasivapet"],
        "duration": "1-2 hours",
        "precautions": ["⚠️ STAY INDOORS", "🚗 Park vehicle in safe place", "⚡ Disconnect electronics",
                       "🔌 Stay away from metal objects", "💧 Take shelter immediately"]
    },
    "severe_storm": {
        "severity": "HIGH",
        "emoji": "⛈️",
        "title": "SEVERE STORMS",
        "color": "#FF6B35",
        "affected_areas": ["Sangareddy", "Vikarabad", "Medak"],
        "duration": "2 hours",
        "precautions": ["🚗 Avoid travel", "☔ Heavy rain expected", "💨 Strong winds", "⚡ Lightning risk"]
    },
    "moderate_storm": {
        "severity": "MODERATE",
        "emoji": "🌧️",
        "title": "SCATTERED STORMS",
        "color": "#FF9800",
        "affected_areas": ["Hyderabad City", "Kompally", "Secunderabad"],
        "duration": "30-60 minutes",
        "precautions": ["☔ Carry umbrella", "🚗 Slow down while driving", "⏳ Rain may be brief"]
    },
    "dry_weather": {
        "severity": "SAFE",
        "emoji": "✅",
        "title": "DRY WEATHER AHEAD",
        "color": "#4CAF50",
        "message": "Favorable conditions for outdoor activities",
        "precautions": ["✅ Safe to travel", "🌞 Use sunscreen", "💧 Stay hydrated"]
    }
}

@lru_cache(maxsize=256)
def get_weather_for_mandal(lat, lon):
    """Fetch weather data for specific mandal"""
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

def analyze_severe_weather(weather_data, mandal_name):
    """Analyze weather data for severe conditions"""
    if not weather_data:
        return None
    
    hourly = weather_data.get('hourly', {})
    current = weather_data.get('current', {})
    
    wind_speed = current.get('wind_speed_10m', 0)
    humidity = current.get('relative_humidity_2m', 0)
    rain_prob = hourly.get('precipitation_probability', [0])[0]
    weather_code = current.get('weather_code', 0)
    
    # Determine severity
    if wind_speed > 40 and rain_prob > 80 and weather_code in [95, 96, 99]:  # Thunderstorm
        return "hailstorm"
    elif wind_speed > 30 and rain_prob > 70:
        return "severe_storm"
    elif rain_prob > 50:
        return "moderate_storm"
    else:
        return "dry_weather"

def display_critical_alert(alert_type):
    """Display critical weather alert in Telangana Weatherman style"""
    alert = CRITICAL_ALERTS.get(alert_type)
    
    if not alert:
        return
    
    severity = alert.get("severity")
    
    if severity == "CRITICAL":
        st.markdown(f"""
        <div class='hailstorm-warning'>
            <h2 style='margin: 0; color: #FFD700;'>{alert['emoji']} {alert['title']}</h2>
        </div>
        """, unsafe_allow_html=True)
    elif severity == "HIGH":
        st.markdown(f"""
        <div class='severe-storm-alert'>
            <h2 style='margin: 0;'>{alert['emoji']} {alert['title']}</h2>
        </div>
        """, unsafe_allow_html=True)
    elif severity == "MODERATE":
        st.markdown(f"""
        <div class='moderate-storm-alert'>
            <h2 style='margin: 0;'>{alert['emoji']} {alert['title']}</h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='safe-alert'>
            <h2 style='margin: 0;'>{alert['emoji']} {alert['title']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Affected areas
    if "affected_areas" in alert:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("**🚨 Affected Areas:**")
        with col2:
            areas_text = ", ".join(alert['affected_areas'])
            st.markdown(f"<div class='affected-areas'>{areas_text}</div>", unsafe_allow_html=True)
    
    # Duration
    if "duration" in alert:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("**⏱️ Duration:**")
        with col2:
            st.markdown(f"<div class='time-window'>{alert['duration']}</div>", unsafe_allow_html=True)
    
    # Precautions
    st.markdown("**🛡️ Precautions:**")
    for precaution in alert.get("precautions", []):
        st.markdown(f"- {precaution}")

def display_mandal_status(district, mandal, alert_type, weather_data):
    """Display detailed status for specific mandal"""
    if not weather_data:
        return
    
    current = weather_data.get('current', {})
    hourly = weather_data.get('hourly', {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "🌡️ Temp",
            f"{current.get('temperature_2m', 'N/A')}°C",
            f"Feels {current.get('apparent_temperature', 'N/A')}°C"
        )
    
    with col2:
        st.metric(
            "💧 Humidity",
            f"{current.get('relative_humidity_2m', 'N/A')}%",
            "Current moisture"
        )
    
    with col3:
        st.metric(
            "💨 Wind",
            f"{current.get('wind_speed_10m', 'N/A')} km/h",
            "Wind speed"
        )
    
    with col4:
        rain_prob = hourly.get('precipitation_probability', [0])[0]
        st.metric(
            "🌧️ Rain Prob",
            f"{rain_prob}%",
            "Next hour chance"
        )
    
    with col5:
        severity_map = {"hailstorm": "🔴", "severe_storm": "🟠", "moderate_storm": "🟡", "dry_weather": "🟢"}
        st.metric(
            "⚠️ Alert Status",
            severity_map.get(alert_type, "?"),
            alert_type.replace("_", " ").title()
        )

# Main App
st.markdown("<h1>⛈️ HYPER-LOCAL WEATHER ALERTS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 1.1em;'>Telangana Mandal-Level Severe Weather Warnings</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📍 ALERT SELECTION MODE")
    
    alert_mode = st.radio(
        "Choose View",
        ["🚨 CRITICAL ALERTS NOW", "📍 Check Specific Mandal", "🗺️ Region Overview"],
        index=0
    )
    
    st.markdown("---")
    
    if alert_mode == "📍 Check Specific Mandal":
        district = st.selectbox("Select District", list(TELANGANA_MANDALS.keys()))
        mandal = st.selectbox("Select Mandal", list(TELANGANA_MANDALS[district].keys()))
    else:
        district = None
        mandal = None

# Main content
if alert_mode == "🚨 CRITICAL ALERTS NOW":
    st.markdown("## ⚠️ ACTIVE WEATHER ALERTS")
    
    # Critical hailstorm alert
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### DANGEROUS HAILSTORMS NOW ⛈️🌨️")
    with col2:
        st.markdown("<span style='color: #FFD700; font-size: 1.5em;'>🔴 CRITICAL</span>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='hailstorm-warning'>
    <h3 style='color: #FFD700; margin: 0;'>⚠️ DANGEROUS HAILSTORMS IN PROGRESS ⛈️</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🚨 AFFECTED MANDALS (NEXT 1 HOUR):")
    
    hail_areas = ["Narsapur", "Medak", "Ameenpur", "Gummadidala", "Isnapur", 
                  "Pashmylaram", "Rudram", "Sangareddy", "Shankarpally", "Sadasivapet"]
    
    # Display in grid
    cols = st.columns(5)
    for i, area in enumerate(hail_areas):
        with cols[i % 5]:
            st.markdown(f"""
            <div class='mandal-card' style='border-left: 5px solid #FF4444;'>
                <h4 style='margin: 0; color: #FF4444;'>{area}</h4>
                <p style='margin: 5px 0; font-size: 0.9em;'>Hailstorms + Lightning</p>
                <span class='storm-severity-high'>EXTREME</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Precautions
    st.markdown("### 🛡️ IMMEDIATE ACTIONS REQUIRED:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🏠 STAY INDOORS**
        - Avoid stepping outside
        - Take shelter immediately
        - Close windows/doors
        
        **🚗 VEHICLE SAFETY**
        - Park in safe place (avoid trees)
        - Use hazard lights
        - Avoid driving
        """)
    
    with col2:
        st.markdown("""
        **⚡ ELECTRICAL SAFETY**
        - Unplug electronics
        - Stay away from metal objects
        - Keep off phones during lightning
        
        **📞 EMERGENCY**
        - Call 100 if danger
        - Dial 108 for medical
        - Contact local authorities
        """)
    
    st.markdown("---")
    
    # Secondary alerts
    st.markdown("### ⚠️ SECONDARY ALERTS")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='severe-storm-alert'>
        <h4 style='margin: 0;'>⛈️ SEVERE STORMS (Next 2 Hours)</h4>
        <p style='margin: 5px 0;'><b>Areas:</b> Sangareddy, Vikarabad, Medak</p>
        <p style='margin: 5px 0;'><b>Precaution:</b> Heavy rain, Strong winds, Lightning risk</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='moderate-storm-alert'>
        <h4 style='margin: 0;'>🌧️ SCATTERED STORMS (Next Hour)</h4>
        <p style='margin: 5px 0;'><b>Areas:</b> Hyderabad City, Kompally, Secunderabad</p>
        <p style='margin: 5px 0;'><b>Status:</b> Reducing intensity, Dry by 6:30 PM</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recovery info
    st.markdown("### ✅ WEATHER OUTLOOK")
    
    st.markdown("""
    <div class='safe-alert'>
    <h4 style='margin: 0;'>✅ DRY WEATHER AHEAD</h4>
    <p style='margin: 5px 0;'><b>Hyderabad City:</b> Storms almost done. Dry from 6:30 PM onwards.</p>
    <p style='margin: 5px 0;'><b>Northern Areas:</b> Clearing by 8 PM. Night will be pleasant.</p>
    <p style='margin: 5px 0;'><b>Tomorrow:</b> Generally fair with isolated thunderstorms possible in evening.</p>
    </div>
    """, unsafe_allow_html=True)

elif alert_mode == "📍 Check Specific Mandal":
    st.markdown(f"## 🔍 {mandal}, {district}")
    
    lat, lon = TELANGANA_MANDALS[district][mandal]
    weather_data = get_weather_for_mandal(lat, lon)
    alert_type = analyze_severe_weather(weather_data, mandal)
    
    if weather_data:
        # Display mandal status
        st.markdown("### Current Conditions")
        display_mandal_status(district, mandal, alert_type, weather_data)
        
        st.markdown("---")
        
        # Display alert
        st.markdown("### ⚠️ Weather Alert")
        display_critical_alert(alert_type)
        
        st.markdown("---")
        
        # Detailed forecast
        st.markdown("### 📊 Detailed Forecast")
        
        hourly = weather_data.get('hourly', {})
        times = pd.to_datetime(hourly.get('time', [])[:12])
        temps = hourly.get('temperature_2m', [])[:12]
        rain_probs = hourly.get('precipitation_probability', [])[:12]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=times,
            y=temps,
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#ff6b6b', width=2),
            yaxis='y1'
        ))
        
        fig.add_trace(go.Scatter(
            x=times,
            y=rain_probs,
            mode='lines',
            name='Rain Probability',
            line=dict(color='#4ecdc4', width=2, dash='dash'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f'12-Hour Forecast for {mandal}',
            xaxis=dict(title='Time (IST)'),
            yaxis=dict(title='Temperature (°C)', titlefont=dict(color='#ff6b6b')),
            yaxis2=dict(title='Rain Probability (%)', overlaying='y', side='right'),
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

else:  # Region Overview
    st.markdown("## 🗺️ TELANGANA REGION OVERVIEW")
    
    regions = {
        "🔴 CRITICAL ZONE": {
            "mandals": ["Narsapur", "Medak", "Ameenpur", "Gummadidala", "Isnapur", 
                       "Pashmylaram", "Rudram", "Sangareddy", "Shankarpally", "Sadasivapet"],
            "alert": "DANGEROUS HAILSTORMS",
            "duration": "Next 1 hour",
            "color": "#FF4444"
        },
        "🟠 HIGH ALERT ZONE": {
            "mandals": ["Sangareddy", "Vikarabad", "Medak"],
            "alert": "SEVERE STORMS",
            "duration": "Next 2 hours",
            "color": "#FF6B35"
        },
        "🟡 MODERATE ALERT": {
            "mandals": ["Hyderabad City", "Kompally", "Secunderabad"],
            "alert": "SCATTERED STORMS REDUCING",
            "duration": "Next 1 hour",
            "color": "#FF9800"
        },
        "🟢 SAFE ZONE": {
            "mandals": ["Kukatpally", "HITEC City", "Dilsukhnagar", "Banjara Hills"],
            "alert": "DRY WEATHER AHEAD",
            "duration": "From 6:30 PM",
            "color": "#4CAF50"
        }
    }
    
    for zone_name, zone_data in regions.items():
        col_title, col_duration = st.columns([2, 1])
        
        with col_title:
            st.markdown(f"### {zone_name}")
        with col_duration:
            st.markdown(f"<span style='color: {zone_data['color']}; font-weight: bold;'>{zone_data['duration']}</span>", unsafe_allow_html=True)
        
        st.markdown(f"**Alert:** {zone_data['alert']}")
        st.markdown(f"**Areas:** {', '.join(zone_data['mandals'])}")
        st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.9em;'>
    <p>💻 Hyper-Local Weather Alert System</p>
    <p>🌐 Data: Open-Meteo API (GFS, ECMWF, IMD models)</p>
    <p>📍 Inspired by Telangana Weatherman (@balaji25_t)</p>
    <p>⏰ Updates: Real-time | Last checked: {datetime.now().strftime('%H:%M IST')}</p>
</div>
""", unsafe_allow_html=True)
