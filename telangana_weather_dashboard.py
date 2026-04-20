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
    page_title="Telangana Weather Forecast",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced aesthetics
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Playfair+Display:wght@700&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        h1 {
            font-family: 'Playfair Display', serif;
            color: #1a472a;
            text-align: center;
            font-size: 3em;
            margin-bottom: 0.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        h2 {
            font-family: 'Playfair Display', serif;
            color: #2d6a4f;
            border-bottom: 3px solid #40916c;
            padding-bottom: 10px;
        }
        
        h3 {
            color: #40916c;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f1faee 0%, #ffffff 100%);
            border-left: 5px solid #40916c;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .weather-alert {
            background: linear-gradient(135deg, #fff5e1 0%, #fffacd 100%);
            border-left: 5px solid #ff9800;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .danger-alert {
            background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
            border-left: 5px solid #d32f2f;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #f1faee 0%, #e8f5e9 100%);
        }
        
        .stMetric {
            background-color: transparent;
        }
    </style>
""", unsafe_allow_html=True)

# Telangana Districts and Mandals Data
TELANGANA_DATA = {
    "Adilabad": ["Adilabad", "Bheemini", "Bhenkarla", "Hajipur", "Kasipet", "Luxettipet", "Utnoor"],
    "Medak": ["Medak", "Tandur", "Gajwel", "Wanaparthy"],
    "Warangal": ["Warangal Urban", "Warangal Rural", "Hanamkonda", "Suryapet"],
    "Nizamabad": ["Nizamabad", "Kamareddy", "Armoor"],
    "Karimnagar": ["Karimnagar", "Jagtyal", "Jaiashankar", "Raikal"],
    "Khammam": ["Khammam", "Alair", "Chintakunta", "Kothagudem"],
    "Telangana": ["Telanglang", "Wair", "Tandur", "Wanaparthy"],
    "Hyderabad": ["Hyderabad City", "Kompally", "LB Nagar", "Tolichowki", "Kukatpally", 
                   "Secunderabad", "Serilingampally", "Keesaragutta", "Gachibowli", "Banjara Hills",
                   "Dilsukhnagar", "Charminar", "Begumpet", "Yousufguda", "HITEC City"],
    "Rangareddy": ["Rangareddy", "Mahbubnagar", "Tandur", "Vikarabad"],
    "Nalgonda": ["Nalgonda", "Miryalaguda", "Mungantiyal", "Choutuppal"],
    "Medchal-Malkajgiri": ["Medchal", "Malkajgiri", "Tandur"],
    "Mulugu": ["Mulugu", "Kasipet", "Luxettipet"],
    "Yadadri Bhongir": ["Bhongir", "Yadadri", "Nalgonda"],
    "Vikarabad": ["Vikarabad", "Tandur", "Wanaparthy"],
    "Mahbubnagar": ["Mahbubnagar", "Tandur", "Wanaparthy", "Jurala"],
    "Suryapet": ["Suryapet", "Huzurabad", "Tandur"],
    "Jagtial": ["Jagtial", "Karimnagar", "Tandur"],
    "Kamareddy": ["Kamareddy", "Tandur", "Armoor"],
    "Mancherial": ["Mancherial", "Tandur", "Armoor"],
    "Peddapalli": ["Peddapalli", "Tandur", "Karimnagar"],
    "Rajanna Sircilla": ["Rajanna", "Sircilla", "Tandur"],
    "Sangareddy": ["Sangareddy", "Tandur", "Medak"],
    "Siddipet": ["Siddipet", "Tandur", "Medak"],
    "Nirmal": ["Nirmal", "Tandur", "Adilabad"],
    "Jagtiyal": ["Jagtiyal", "Tandur", "Karimnagar"],
}

def get_coordinates(mandal_name, district_name):
    """Get latitude and longitude for a mandal"""
    # Sample coordinates - in production, use a geocoding API
    coordinates = {
        # Hyderabad City Areas (EXPANDED)
        ("Hyderabad City", "Hyderabad"): (17.3850, 78.4867),
        ("Kompally", "Hyderabad"): (17.5042, 78.5640),  # Kompally - North Hyderabad
        ("LB Nagar", "Hyderabad"): (17.3650, 78.5450),  # LB Nagar - East Hyderabad
        ("Tolichowki", "Hyderabad"): (17.3850, 78.5200),  # Tolichowki - South Hyderabad
        ("Kukatpally", "Hyderabad"): (17.4669, 78.4150),  # Kukatpally - West Hyderabad
        ("Secunderabad", "Hyderabad"): (17.3667, 78.5033),  # Secunderabad - Central
        ("Serilingampally", "Hyderabad"): (17.3500, 78.3667),  # Serilingampally - West
        ("Keesaragutta", "Hyderabad"): (17.2833, 78.3000),  # Keesaragutta - Southwest
        ("Gachibowli", "Hyderabad"): (17.4398, 78.5533),  # Gachibowli - East
        ("Banjara Hills", "Hyderabad"): (17.3904, 78.4599),  # Banjara Hills - Central
        ("Dilsukhnagar", "Hyderabad"): (17.3667, 78.5500),  # Dilsukhnagar - South
        ("Charminar", "Hyderabad"): (17.3604, 78.4741),  # Charminar - Old City
        ("Begumpet", "Hyderabad"): (17.3767, 78.4672),  # Begumpet - Central
        ("Yousufguda", "Hyderabad"): (17.4167, 78.4667),  # Yousufguda - West
        ("HITEC City", "Hyderabad"): (17.4409, 78.4414),  # HITEC City - IT Hub
        
        # Other Districts
        ("Rangareddy", "Rangareddy"): (17.3850, 78.5500),
        ("Warangal Urban", "Warangal"): (17.9689, 79.5941),
        ("Nizamabad", "Nizamabad"): (19.2757, 78.1368),
        ("Adilabad", "Adilabad"): (19.6752, 78.5337),
        ("Karimnagar", "Karimnagar"): (18.4394, 78.1381),
        ("Khammam", "Khammam"): (17.2505, 79.1206),
        ("Nalgonda", "Nalgonda"): (17.6869, 79.1300),
        ("Medak", "Medak"): (18.7669, 78.2869),
        ("Sangareddy", "Sangareddy"): (17.4669, 78.1300),
    }
    return coordinates.get((mandal_name, district_name), (17.3850, 78.4867))

@lru_cache(maxsize=128)
def fetch_weather_data(lat, lon):
    """Fetch weather data from Open-Meteo API (free, no API key required)"""
    try:
        # Using Open-Meteo API - completely free
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
            "timezone": "Asia/Kolkata",
            "forecast_days": 14
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None

def interpret_weather_code(code):
    """Interpret WMO weather codes"""
    weather_codes = {
        0: ("Clear Sky", "☀️", "#FFD700"),
        1: ("Mainly Clear", "🌤️", "#FFA500"),
        2: ("Partly Cloudy", "⛅", "#87CEEB"),
        3: ("Overcast", "☁️", "#D3D3D3"),
        45: ("Foggy", "🌫️", "#808080"),
        48: ("Foggy (Rime)", "🌫️", "#696969"),
        51: ("Light Drizzle", "🌧️", "#4682B4"),
        53: ("Moderate Drizzle", "🌧️", "#1E90FF"),
        55: ("Dense Drizzle", "🌧️", "#0000CD"),
        61: ("Slight Rain", "🌧️", "#4682B4"),
        63: ("Moderate Rain", "🌧️", "#1E90FF"),
        65: ("Heavy Rain", "⛈️", "#0000CD"),
        71: ("Slight Snow", "❄️", "#B0E0E6"),
        73: ("Moderate Snow", "❄️", "#87CEEB"),
        75: ("Heavy Snow", "❄️", "#4169E1"),
        77: ("Snow Grains", "❄️", "#6495ED"),
        80: ("Slight Rain Showers", "🌦️", "#4682B4"),
        81: ("Moderate Rain Showers", "🌦️", "#1E90FF"),
        82: ("Violent Rain Showers", "⛈️", "#0000CD"),
        85: ("Slight Snow Showers", "❄️", "#87CEEB"),
        86: ("Heavy Snow Showers", "❄️", "#4169E1"),
        95: ("Thunderstorm", "⛈️", "#8B0000"),
        96: ("Thunderstorm with Hail", "⛈️", "#800000"),
        99: ("Thunderstorm with Hail", "⛈️", "#800000"),
    }
    return weather_codes.get(code, ("Unknown", "❓", "#808080"))

def get_health_alerts(temp, humidity, rain_prob, wind_speed):
    """Generate health and safety alerts based on weather"""
    alerts = []
    
    if temp > 38:
        alerts.append(("🔴 EXTREME HEAT WARNING", "Temperature above 38°C. Stay hydrated, limit outdoor activities.", "danger-alert"))
    elif temp > 35:
        alerts.append(("🟠 HEAT ALERT", "High temperature (>35°C). Use sun protection.", "weather-alert"))
    
    if temp < 5:
        alerts.append(("🔵 COLD WARNING", "Temperature below 5°C. Wear warm clothing.", "danger-alert"))
    elif temp < 10:
        alerts.append(("🟦 COLD ALERT", "Moderately cold. Dress warmly.", "weather-alert"))
    
    if rain_prob > 80:
        alerts.append(("🟠 HEAVY RAIN EXPECTED", "Probability >80%. Avoid non-essential travel.", "weather-alert"))
    elif rain_prob > 60:
        alerts.append(("🟡 RAIN LIKELY", "Carry umbrella. Monsoon precautions advised.", "weather-alert"))
    
    if wind_speed > 30:
        alerts.append(("🔴 HIGH WIND WARNING", "Wind speed >30 km/h. Exercise caution outdoors.", "danger-alert"))
    elif wind_speed > 20:
        alerts.append(("🟠 WINDY CONDITIONS", "Moderate wind. Secure loose objects.", "weather-alert"))
    
    if humidity > 80:
        alerts.append(("💧 HIGH HUMIDITY", "Humidity >80%. Uncomfortable conditions.", "weather-alert"))
    
    return alerts

def create_hourly_chart(hourly_data, hours=24):
    """Create hourly forecast chart"""
    df_hourly = pd.DataFrame({
        'time': pd.to_datetime(hourly_data['time'][:hours]),
        'temp': hourly_data['temperature_2m'][:hours],
        'humidity': hourly_data['relative_humidity_2m'][:hours],
        'rain_prob': hourly_data['precipitation_probability'][:hours],
        'wind': hourly_data['wind_speed_10m'][:hours],
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_hourly['time'],
        y=df_hourly['temp'],
        name='Temperature (°C)',
        mode='lines+markers',
        line=dict(color='#ff6b6b', width=2),
        marker=dict(size=4),
        yaxis='y1'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_hourly['time'],
        y=df_hourly['rain_prob'],
        name='Rain Probability (%)',
        mode='lines',
        line=dict(color='#4ecdc4', width=2, dash='dash'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=f'<b>Hourly Forecast (Next {hours} Hours)</b>',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Temperature (°C)', titlefont=dict(color='#ff6b6b'), tickfont=dict(color='#ff6b6b')),
        yaxis2=dict(title='Rain Probability (%)', titlefont=dict(color='#4ecdc4'), tickfont=dict(color='#4ecdc4'), overlaying='y', side='right'),
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=0, r=50, t=40, b=0)
    )
    
    return fig

def create_daily_chart(daily_data):
    """Create daily forecast chart"""
    df_daily = pd.DataFrame({
        'date': pd.to_datetime(daily_data['time']),
        'temp_max': daily_data['temperature_2m_max'],
        'temp_min': daily_data['temperature_2m_min'],
        'rain_prob': daily_data['precipitation_probability_max'],
        'rain_sum': daily_data['precipitation_sum'],
    })
    
    fig = go.Figure()
    
    # Add temperature range
    fig.add_trace(go.Scatter(
        x=df_daily['date'],
        y=df_daily['temp_max'],
        name='Max Temp',
        mode='lines',
        line=dict(color='#ff6b6b', width=2),
    ))
    
    fig.add_trace(go.Scatter(
        x=df_daily['date'],
        y=df_daily['temp_min'],
        name='Min Temp',
        mode='lines',
        line=dict(color='#4ecdc4', width=2),
        fill='tonexty',
        fillcolor='rgba(78, 205, 196, 0.2)'
    ))
    
    fig.add_trace(go.Bar(
        x=df_daily['date'],
        y=df_daily['rain_prob'],
        name='Rain Probability (%)',
        marker=dict(color='#95e1d3', opacity=0.6),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='<b>14-Day Forecast</b>',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Temperature (°C)', titlefont=dict(color='#ff6b6b')),
        yaxis2=dict(title='Rain Probability (%)', overlaying='y', side='right'),
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=0, r=50, t=40, b=0)
    )
    
    return fig

# Main App
st.markdown("<h1>🌤️ Telangana Weather Forecast</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 1.1em; margin-bottom: 2em;'>Hyper-local weather predictions powered by multiple meteorological models</p>", unsafe_allow_html=True)

# Sidebar for selection
with st.sidebar:
    st.markdown("### 📍 Location Selection")
    
    selected_district = st.selectbox(
        "Select District",
        list(TELANGANA_DATA.keys()),
        index=7  # Default to Hyderabad
    )
    
    selected_mandal = st.selectbox(
        "Select Mandal",
        TELANGANA_DATA[selected_district]
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Display Options")
    
    view_option = st.radio(
        "Select Forecast View",
        ["Current", "Hourly (24h)", "Daily (14 days)", "All"],
        index=3
    )
    
    st.markdown("---")
    st.info("📡 Data updated every 6 hours from Open-Meteo API")

# Get coordinates and fetch data
lat, lon = get_coordinates(selected_mandal, selected_district)
weather_data = fetch_weather_data(lat, lon)

if weather_data:
    current = weather_data.get('current', {})
    hourly = weather_data.get('hourly', {})
    daily = weather_data.get('daily', {})
    
    # Current conditions
    if view_option in ["Current", "All"]:
        st.markdown("## 🌡️ Current Conditions")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        temp = current.get('temperature_2m', 'N/A')
        humidity = current.get('relative_humidity_2m', 'N/A')
        wind = current.get('wind_speed_10m', 'N/A')
        rain_prob = current.get('precipitation', 0)
        weather_code = current.get('weather_code', 0)
        
        weather_desc, emoji, color = interpret_weather_code(weather_code)
        
        with col1:
            st.metric("Temperature", f"{temp}°C", f"Feels like {current.get('apparent_temperature', 'N/A')}°C")
        with col2:
            st.metric("Humidity", f"{humidity}%", f"Moisture level")
        with col3:
            st.metric("Wind Speed", f"{wind} km/h", f"Current winds")
        with col4:
            st.metric("Precipitation", f"{rain_prob} mm", f"Recent rainfall")
        with col5:
            st.metric("Conditions", f"{emoji} {weather_desc}", "Current status")
        
        st.markdown("---")
        
        # Health and Safety Alerts
        st.markdown("## ⚠️ Health & Safety Alerts")
        alerts = get_health_alerts(temp, humidity, 
                                  daily['precipitation_probability_max'][0] if daily.get('precipitation_probability_max') else 0,
                                  wind)
        
        if alerts:
            for title, message, alert_type in alerts:
                st.markdown(f"<div class='{alert_type}'><b>{title}</b><br/>{message}</div>", unsafe_allow_html=True)
        else:
            st.success("✅ No alerts. Conditions are favorable.")
    
    # 2-Hour Detailed Forecast
    st.markdown("## ⏰ Next 2 Hours - Detailed Breakdown")
    
    col_2hr_title = st.columns([3, 1])
    with col_2hr_title[0]:
        st.markdown("### Minute-by-Minute Weather")
    
    # Create 2-hour detailed forecast (first 12 30-min intervals = 2 hours if hourly, or use first 2 data points)
    times_2hr = pd.to_datetime(hourly['time'][:3])  # First 3 hourly points covers ~2 hours
    temps_2hr = hourly['temperature_2m'][:3]
    humidity_2hr = hourly['relative_humidity_2m'][:3]
    rain_prob_2hr = hourly['precipitation_probability'][:3]
    wind_2hr = hourly['wind_speed_10m'][:3]
    
    # Create 2-hour gauge chart
    fig_2hr = go.Figure()
    
    # Current + Next 2 hours
    for i in range(min(3, len(times_2hr))):
        time_str = times_2hr[i].strftime("%H:%M")
        temp = temps_2hr[i]
        humidity = humidity_2hr[i]
        rain = rain_prob_2hr[i]
        wind = wind_2hr[i]
        
        # Color based on temperature
        if temp > 35:
            color = '#ff6b6b'
        elif temp > 25:
            color = '#ffa500'
        else:
            color = '#4ecdc4'
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <h4 style='text-align: center; margin: 0;'>{time_str}</h4>
                <p style='font-size: 1.8em; text-align: center; color: {color}; margin: 10px 0;'>{temp}°C</p>
                <small style='text-align: center; display: block;'>Temperature</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <h4 style='text-align: center; margin: 0;'>{time_str}</h4>
                <p style='font-size: 1.8em; text-align: center; color: #4ecdc4; margin: 10px 0;'>{humidity}%</p>
                <small style='text-align: center; display: block;'>Humidity</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='metric-card'>
                <h4 style='text-align: center; margin: 0;'>{time_str}</h4>
                <p style='font-size: 1.8em; text-align: center; color: #95e1d3; margin: 10px 0;'>{rain}%</p>
                <small style='text-align: center; display: block;'>Rain Chance</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class='metric-card'>
                <h4 style='text-align: center; margin: 0;'>{time_str}</h4>
                <p style='font-size: 1.8em; text-align: center; color: #b19cd9; margin: 10px 0;'>{wind}</p>
                <small style='text-align: center; display: block;'>Wind km/h</small>
            </div>
            """, unsafe_allow_html=True)
    
    # 2-Hour Trend Chart
    st.markdown("### 2-Hour Trend Analysis")
    
    fig_2hr_trend = go.Figure()
    
    fig_2hr_trend.add_trace(go.Scatter(
        x=times_2hr,
        y=temps_2hr,
        mode='lines+markers',
        name='Temperature',
        line=dict(color='#ff6b6b', width=3),
        marker=dict(size=10),
        hovertemplate='<b>%{x}</b><br>Temp: %{y}°C<extra></extra>'
    ))
    
    fig_2hr_trend.add_trace(go.Scatter(
        x=times_2hr,
        y=rain_prob_2hr,
        mode='lines+markers',
        name='Rain Probability',
        line=dict(color='#4ecdc4', width=3, dash='dash'),
        marker=dict(size=10),
        yaxis='y2',
        hovertemplate='<b>%{x}</b><br>Rain: %{y}%<extra></extra>'
    ))
    
    fig_2hr_trend.update_layout(
        title='<b>Temperature & Rain Probability (Next 2 Hours)</b>',
        xaxis=dict(title='Time (IST)'),
        yaxis=dict(title='Temperature (°C)', titlefont=dict(color='#ff6b6b')),
        yaxis2=dict(title='Rain Probability (%)', overlaying='y', side='right', titlefont=dict(color='#4ecdc4')),
        hovermode='x unified',
        template='plotly_white',
        height=350,
        margin=dict(l=0, r=50, t=40, b=0)
    )
    
    st.plotly_chart(fig_2hr_trend, use_container_width=True)
    
    # 2-Hour Alert System
    st.markdown("### ⚠️ Next 2 Hours - Critical Alerts")
    
    alerts_2hr = []
    for i in range(min(3, len(temps_2hr))):
        temp = temps_2hr[i]
        humidity = humidity_2hr[i]
        rain = rain_prob_2hr[i]
        wind = wind_2hr[i]
        time_str = times_2hr[i].strftime("%H:%M")
        
        if temp > 38:
            alerts_2hr.append((f"🔴 EXTREME HEAT at {time_str}", f"Temperature {temp}°C - Stay indoors", "danger-alert"))
        if rain > 80:
            alerts_2hr.append((f"🔴 HEAVY RAIN at {time_str}", f"Rain probability {rain}% - Take shelter", "danger-alert"))
        if wind > 30:
            alerts_2hr.append((f"🔴 HIGH WINDS at {time_str}", f"Wind speed {wind} km/h - Secure objects", "danger-alert"))
    
    if alerts_2hr:
        for title, message, alert_type in alerts_2hr:
            st.markdown(f"<div class='{alert_type}'><b>{title}</b><br/>{message}</div>", unsafe_allow_html=True)
    else:
        st.success("✅ No critical alerts for next 2 hours. Conditions are stable.")
    
    st.markdown("---")
    
    # Hourly forecast
    if view_option in ["Hourly (24h)", "All"]:
        st.markdown("## 📊 Hourly Forecast (24 Hours)")
        hourly_chart = create_hourly_chart(hourly, hours=24)
        st.plotly_chart(hourly_chart, use_container_width=True)
        
        # Hourly table
        with st.expander("📋 Detailed Hourly Data"):
            df_hourly_table = pd.DataFrame({
                'Time': pd.to_datetime(hourly['time'][:24]),
                'Temp (°C)': hourly['temperature_2m'][:24],
                'Humidity (%)': hourly['relative_humidity_2m'][:24],
                'Rain Prob (%)': hourly['precipitation_probability'][:24],
                'Wind (km/h)': hourly['wind_speed_10m'][:24],
            })
            st.dataframe(df_hourly_table, use_container_width=True)
    
    # Daily forecast
    if view_option in ["Daily (14 days)", "All"]:
        st.markdown("## 📅 14-Day Forecast")
        daily_chart = create_daily_chart(daily)
        st.plotly_chart(daily_chart, use_container_width=True)
        
        # Daily table
        with st.expander("📋 Detailed Daily Data"):
            df_daily_table = pd.DataFrame({
                'Date': pd.to_datetime(daily['time']),
                'Max Temp (°C)': daily['temperature_2m_max'],
                'Min Temp (°C)': daily['temperature_2m_min'],
                'Precipitation (mm)': daily['precipitation_sum'],
                'Rain Probability (%)': daily['precipitation_probability_max'],
                'Wind Speed (km/h)': daily['wind_speed_10m_max'],
            })
            df_daily_table['Conditions'] = [interpret_weather_code(code)[0] for code in daily['weather_code']]
            st.dataframe(df_daily_table, use_container_width=True)
    
    # Additional insights
    st.markdown("---")
    st.markdown("## 💡 Insights & Recommendations")
    
    col_insight1, col_insight2, col_insight3 = st.columns(3)
    
    with col_insight1:
        avg_temp = np.mean(daily['temperature_2m_max'][:7])
        st.markdown(f"""
        <div class='metric-card'>
            <h4>📈 7-Day Average</h4>
            <p style='font-size: 1.5em; color: #ff6b6b;'>{avg_temp:.1f}°C</p>
            <small>Average high temperature for next week</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_insight2:
        max_rain = max(daily['precipitation_sum'][:7])
        st.markdown(f"""
        <div class='metric-card'>
            <h4>🌧️ Peak Rain Day</h4>
            <p style='font-size: 1.5em; color: #4ecdc4;'>{max_rain:.1f} mm</p>
            <small>Maximum rainfall expected this week</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_insight3:
        st.markdown(f"""
        <div class='metric-card'>
            <h4>📍 Location</h4>
            <p style='font-size: 1em;'><b>{selected_mandal}</b></p>
            <p style='font-size: 0.9em; color: #666;'>{selected_district}</p>
            <small>Lat: {lat:.2f}°, Lon: {lon:.2f}°</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<small style='text-align: center; color: #999;'>💻 Built with Streamlit | 🌐 Data from Open-Meteo API | 📡 Updates every 6 hours</small>", unsafe_allow_html=True)

else:
    st.error("Unable to fetch weather data. Please try again later.")
