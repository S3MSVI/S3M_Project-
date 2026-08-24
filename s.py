import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import time
import requests
from datetime import datetime
import pytz
import jdatetime
import math
import os

# 1. Page Configuration
st.set_page_config(
    page_title="MPPT Solar Monitoring",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Base CSS Styling
st.markdown("""
<style>
    * { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; }
    .stApp, [data-testid="stHeader"] { background-color: transparent !important; }

    /* Bright Background Image */
    [data-testid="stAppViewContainer"] { 
        background-image: linear-gradient(rgba(255, 255, 255, 0.4), rgba(240, 248, 255, 0.6)), url('Gemini_Generated_Image_qlhpm3qlhpm3qlhp.jpg') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
    }

    h1 {
        font-family: 'Times New Roman', Tahoma, serif !important;
        font-size: 38px !important; color: #0f172a !important; font-weight: bold !important; 
        text-align: center !important; margin-bottom: 30px !important;
        text-shadow: 0 2px 6px rgba(255, 255, 255, 0.9); letter-spacing: 2px;
    }

    [data-testid="stAppViewBlockContainer"], .main .block-container {
        max-width: 1600px !important; padding-top: 1.5rem !important; padding-bottom: 2rem !important;
    }

    .header-box {
        background-color: rgba(255, 255, 255, 0.95); backdrop-filter: blur(12px);
        border-radius: 16px; padding: 18px 20px; border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); margin-bottom: 25px;
        display: flex; flex-direction: column; align-items: center; gap: 15px;
    }
    .header-item { color: #1e293b; font-size: 16px; font-weight: bold; }
    .header-highlight { color: #2563eb; font-weight: bold; font-family: 'Courier New', Courier, monospace !important; }
    .header-highlight.green { color: #10b981 !important; }
    .header-highlight.red { color: #ef4444 !important; }

    .live-data-box {
        background-color: rgba(255, 255, 255, 0.92); backdrop-filter: blur(12px);
        border-radius: 16px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); margin-bottom: 25px;
    }
    .live-data-title {
        text-align: center; font-size: 20px; font-weight: bold; color: #0f172a;
        margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;
        text-transform: uppercase; letter-spacing: 1px;
    }

    .metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
    .metric-item {
        background: rgba(241, 245, 249, 0.6); border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px; padding: 12px 5px; text-align: center;
    }
    .energy-item {
        grid-column: span 2; background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(52, 211, 153, 0.25));
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .metric-title { color: #475569; font-size: 14px; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; }
    .metric-val { color: #0f172a; font-size: 24px; font-weight: bold; font-family: 'Courier New', Courier, monospace !important; display: inline-block; }
    .energy-val { color: #047857; font-size: 28px; }

    h5 { font-size: 16px !important; color: #1e293b !important; font-weight: bold !important; text-align: center !important; margin-top: 15px !important; margin-bottom: 8px !important; text-transform: uppercase; }
    
    div[data-testid="stRadio"] { display: flex !important; justify-content: center !important; align-items: center !important; width: 100% !important; margin-bottom: 15px; }
    div[role="radiogroup"] {
        display: inline-flex !important; justify-content: center !important; align-items: center !important; flex-wrap: wrap !important;
        background: rgba(255, 255, 255, 0.95) !important; backdrop-filter: blur(8px) !important; padding: 8px 15px !important;
        border-radius: 50px !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important; border: 1px solid rgba(226, 232, 240, 0.9) !important;
    }
    div[role="radiogroup"] label p { font-size: 14px !important; font-weight: bold !important; color: #0f172a !important; }

    div[data-testid="stVegaLiteChart"], div[data-testid="stArrowVegaLiteChart"] {
        background-color: #ffffff !important; border-radius: 0px !important; padding: 10px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; border: 1px solid rgba(203, 213, 225, 0.9) !important; overflow: hidden !important;
    }
    div[data-testid="stVegaLiteChart"] summary, div[data-testid="stArrowVegaLiteChart"] summary { display: none !important; }

    .save-box {
        background-color: rgba(255, 255, 255, 0.95); border: 1px solid #e2e8f0; border-radius: 0px; 
        padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### ⚙️ Settings")
live_update = st.sidebar.checkbox("🔄 Live Update", value=True)

# 3. Weather Fetcher
@st.cache_data(ttl=300)
def get_tehran_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=35.6892&longitude=51.3890&current=temperature_2m,relative_humidity_2m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=6)
        data = response.json()
        if 'current' in data:
            temp = data['current']['temperature_2m']
            hum = data['current']['relative_humidity_2m']
            return f"{temp} °C", f"{hum} %"
    except:
        pass
    return "28.0 °C", "35 %"

tehran_tz = pytz.timezone('Asia/Tehran')
now_tehran = datetime.now(tehran_tz)
j_date = jdatetime.datetime.fromgregorian(datetime=now_tehran)
date_str = j_date.strftime("%Y/%m/%d") 
time_str = now_tehran.strftime("%H:%M:%S")
tehran_temp, tehran_hum = get_tehran_weather()

# ==========================================
# 4. DYNAMIC SUN ORB ENGINE (CSS)
# ==========================================
hour = now_tehran.hour
minute = now_tehran.minute
time_in_hours = hour + minute / 60.0

if 5 <= time_in_hours <= 19:
    progress = (time_in_hours - 5) / 14.0 
    sun_x = 10 + (80 * progress)          
    sun_y = 85 - (75 * math.sin(math.pi * progress)) 
    
    sun_orb_css = f"""
    <div style="
        position: fixed;
        width: 250px;
        height: 250px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(255,223,0,0.8) 30%, transparent 70%);
        box-shadow: 0 0 120px 60px rgba(255, 200, 0, 0.4);
        left: {sun_x}%;
        top: {sun_y}%;
        transform: translate(-50%, -50%);
        z-index: -1;
        pointer-events: none;
    "></div>
    """
    st.markdown(sun_orb_css, unsafe_allow_html=True)


# ==========================================
# 5. Live Memory with AUTO-BACKUP RECOVERY
# ==========================================
@st.cache_resource
def get_mppt_data_v8():
    data = {
        'voltage': 0.0, 'current': 0.0, 'power': 0.0, 'temp': 0.0, 'lux': 0.0, 'watts': 0.0,
        'total_energy_mWh': 0.0, 'last_power_time': 0.0,
        'hist_voltage': [], 'hist_current': [], 'hist_power': [], 'hist_temp': [], 'hist_lux': [], 'hist_watts': [], 'hist_energy': [],
        'timestamps': [], 'log_records': [], 'last_time': '', 'mqtt_connected': False, 'msg_count': 0
    }
    # ریکاوری خودکار داده‌ها در صورت ریبوت شدن سرور یا ویرایش کد
    if os.path.exists('mppt_backup.csv'):
        try:
            df = pd.read_csv('mppt_backup.csv').tail(20000)
            data['timestamps'] = df['Time'].tolist()
            data['hist_voltage'] = df['Voltage (V)'].tolist()
            data['hist_current'] = df['Current (mA)'].tolist()
            data['hist_power'] = df['Power (mW)'].tolist()
            data['hist_energy'] = df['Energy (mWh)'].tolist()
            data['hist_temp'] = df['Temp (°C)'].tolist()
            data['hist_lux'] = df['Lux'].tolist()
            data['hist_watts'] = df['Irradiance (W/m²)'].tolist()
            data['log_records'] = df.to_dict('records')
            if not df.empty:
                data['total_energy_mWh'] = df['Energy (mWh)'].iloc[-1]
                data['voltage'] = df['Voltage (V)'].iloc[-1]
                data['current'] = df['Current (mA)'].iloc[-1]
                data['power'] = df['Power (mW)'].iloc[-1]
                data['temp'] = df['Temp (°C)'].iloc[-1]
                data['lux'] = df['Lux'].iloc[-1]
                data['watts'] = df['Irradiance (W/m²)'].iloc[-1]
        except: pass
    return data

sensor_data = get_mppt_data_v8()

# 6. MQTT Logic & Auto-Save
def on_connect(client, userdata, flags, rc, properties=None):
    sensor_data['mqtt_connected'] = True
    client.subscribe("my_powerplant/#")

def on_message(client, userdata, msg):
    topic = msg.topic.lower()
    payload = msg.payload.decode().strip('\x00').strip()
    sensor_data['msg_count'] += 1
    
    try:
        value = float(payload)
        sensor_name = topic.split('/')[-1]
        
        if sensor_name == "voltage": sensor_data['voltage'] = value
        elif sensor_name == "current": sensor_data['current'] = value
        elif sensor_name == "power":
            sensor_data['power'] = value
            current_t = time.time()
            if sensor_data['last_power_time'] != 0:
                delta_h = (current_t - sensor_data['last_power_time']) / 3600.0
                if delta_h < 0.1: sensor_data['total_energy_mWh'] += value * delta_h
            sensor_data['last_power_time'] = current_t
        elif sensor_name == "temperature": sensor_data['temp'] = value
        elif sensor_name == "lux": sensor_data['lux'] = value
        elif sensor_name == "watts": sensor_data['watts'] = value
            
        current_time_str = datetime.now(tehran_tz).strftime("%H:%M:%S")
        if sensor_data['last_time'] != current_time_str:
            sensor_data['last_time'] = current_time_str
            
            sensor_data['timestamps'].append(current_time_str)
            sensor_data['hist_voltage'].append(sensor_data['voltage'])
            sensor_data['hist_current'].append(sensor_data['current'])
            sensor_data['hist_power'].append(sensor_data['power'])
            sensor_data['hist_temp'].append(sensor_data['temp'])
            sensor_data['hist_lux'].append(sensor_data['lux'])
            sensor_data['hist_watts'].append(sensor_data['watts'])
            sensor_data['hist_energy'].append(sensor_data['total_energy_mWh'])
            
            record = {
                'Time': current_time_str,
                'Voltage (V)': sensor_data['voltage'], 'Current (mA)': sensor_data['current'],
                'Power (mW)': sensor_data['power'], 'Energy (mWh)': round(sensor_data['total_energy_mWh'], 3),
                'Temp (°C)': sensor_data['temp'], 'Lux': sensor_data['lux'], 'Irradiance (W/m²)': sensor_data['watts']
            }
            sensor_data['log_records'].append(record)

            # بک‌آپ‌گیری خودکار در فایل CSV دائمی
            try:
                df_save = pd.DataFrame([record])
                df_save.to_csv('mppt_backup.csv', mode='a', header=not os.path.exists('mppt_backup.csv'), index=False)
            except: pass

            if len(sensor_data['timestamps']) > 20000:
                sensor_data['timestamps'].pop(0); sensor_data['hist_voltage'].pop(0)
                sensor_data['hist_current'].pop(0); sensor_data['hist_power'].pop(0)
                sensor_data['hist_temp'].pop(0); sensor_data['hist_lux'].pop(0)
                sensor_data['hist_watts'].pop(0); sensor_data['hist_energy'].pop(0)
                sensor_data['log_records'].pop(0)
    except:
        pass

# 7. MQTT Init
@st.cache_resource
def init_mqtt_v8():
    try: client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    except: 
        try: client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except: client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try: client.connect("broker.emqx.io", 1883, keepalive=60)
    except: client.connect("broker.hivemq.com", 1883, keepalive=60)
    client.loop_start()
    return client

try: mqtt_client = init_mqtt_v8()
except Exception as e: st.error(f"Error: {e}")

# ==========================================
# Main UI Layout
# ==========================================
st.markdown("<h1>MPPT SOLAR MONITORING</h1>", unsafe_allow_html=True)
col_left, col_right = st.columns([1, 1.8], gap="large")

with col_left:
    mqtt_status_cls = "green" if sensor_data['mqtt_connected'] else "red"
    mqtt_status_txt = "Connected" if sensor_data['mqtt_connected'] else "Waiting..."
    
    st.markdown(f"""
    <div class="header-box">
        <div style="display: flex; justify-content: center; gap: 40px; width: 100%; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px;">
            <div class="header-item">🌤️ Tehran Temp: <span class="header-highlight">{tehran_temp}</span></div>
            <div class="header-item">💧 Humidity: <span class="header-highlight">{tehran_hum}</span></div>
        </div>
        <div style="display: flex; justify-content: space-around; width: 100%; flex-wrap: wrap; gap: 12px; padding-top: 5px;">
            <div class="header-item">📅 Date: <span class="header-highlight">{date_str}</span></div>
            <div class="header-item">⏰ Time: <span class="header-highlight">{time_str}</span></div>
            <div class="header-item">🌐 MQTT: <span class="header-highlight {mqtt_status_cls}">{mqtt_status_txt}</span></div>
            <div class="header-item" style="color: #64748b;">📨 Msgs: <span class="header-highlight">{sensor_data['msg_count']}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="live-data-box">
        <div class="live-data-title">LIVE SYSTEM DATA</div>
        <div class="metrics-grid">
            <div class="metric-item energy-item">
                <div class="metric-title">⚡ Total Energy</div>
                <div class="metric-val energy-val">{sensor_data['total_energy_mWh']:.3f} <span style="font-size: 16px;">mWh</span></div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔌 Current</div>
                <div class="metric-val">{sensor_data['current']:.2f} <span style="font-size: 14px;">mA</span></div>
            </div>
            <div class="metric-item">
                <div class="metric-title">⚡ Voltage</div>
                <div class="metric-val">{sensor_data['voltage']:.2f} <span style="font-size: 14px;">V</span></div>
            </div>
            <div class="metric-item">
                <div class="metric-title">☀️ Illuminance</div>
                <div class="metric-val">{sensor_data['lux']:.1f} <span style="font-size: 14px;">Lux</span></div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔋 Power</div>
                <div class="metric-val">{sensor_data['power']:.2f} <span style="font-size: 14px;">mW</span></div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🌡️ Panel Temp</div>
                <div class="metric-val">{sensor_data['temp']:.1f} <span style="font-size: 14px;">°C</span></div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔆 Irradiance</div>
                <div class="metric-val">{sensor_data['watts']:.2f} <span style="font-size: 14px;">W/m²</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='save-box'>
        <div style='text-align: center; color: #10b981; font-size: 16px; font-weight: bold; margin-bottom: 10px; text-transform: uppercase;'>
            🟢 Live Auto-Backup Active
        </div>
    """, unsafe_allow_html=True)
    
    if len(sensor_data['log_records']) > 0:
        df_logs = pd.DataFrame(sensor_data['log_records'])
        st.dataframe(df_logs.tail(3).iloc[::-1], use_container_width=True)
        
        # دکمه دانلود از فایل ذخیره‌شده اصلی (تا همه دیتای قدیمی هم داخلش باشه)
        if os.path.exists('mppt_backup.csv'):
            with open('mppt_backup.csv', 'rb') as f:
                st.download_button(label="📥 Download CSV Archive", data=f, file_name=f"solar_log_{date_str.replace('/','-')}.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("Waiting for sensor data...")
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    timeframe = st.radio(label="Timeframe", options=["1 Min", "5 Mins", "15 Mins", "1 Hour", "12 Hours", "All-Time"], horizontal=True, index=1, label_visibility="collapsed")
    limit_map = {"1 Min": 12, "5 Mins": 60, "15 Mins": 180, "1 Hour": 720, "12 Hours": 8640, "All-Time": None}
    point_limit = limit_map[timeframe]

    def draw_chart(data_list, time_list, chart_name, line_color, limit=None):
        if len(data_list) > 0 and len(time_list) == len(data_list):
            sub_data = data_list[-limit:] if limit and len(data_list) > limit else data_list
            sub_time = time_list[-limit:] if limit and len(data_list) > limit else time_list
            df = pd.DataFrame({'Time': sub_time, chart_name: sub_data}).set_index('Time')
            st.line_chart(df, color=line_color, height=210)
        else:
            st.info("Collecting data...")

    chart_col_left, chart_col_right = st.columns(2)

    with chart_col_right:
        st.markdown("##### ⚡ Voltage (V)")
        draw_chart(sensor_data['hist_voltage'], sensor_data['timestamps'], "Voltage", "#2563eb", limit=point_limit)
        st.markdown("##### 🔋 Power (mW)")
        draw_chart(sensor_data['hist_power'], sensor_data['timestamps'], "Power", "#059669", limit=point_limit)
        st.markdown("##### 🔆 Irradiance (W/m²)")
        draw_chart(sensor_data['hist_watts'], sensor_data['timestamps'], "Irradiance", "#ea580c", limit=point_limit)

    with chart_col_left:
        st.markdown("##### 🔌 Current (mA)")
        draw_chart(sensor_data['hist_current'], sensor_data['timestamps'], "Current", "#d97706", limit=point_limit)
        st.markdown("##### ☀️ Illuminance (Lux)")
        draw_chart(sensor_data['hist_lux'], sensor_data['timestamps'], "Illuminance", "#ca8a04", limit=point_limit)
        st.markdown("##### ⚡ Energy (mWh)")
        draw_chart(sensor_data['hist_energy'], sensor_data['timestamps'], "Energy", "#10b981", limit=point_limit)

if live_update:
    time.sleep(3.5)
    st.rerun()