import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import time
import requests
from datetime import datetime
import pytz
import jdatetime

# ۱. تنظیمات اصلی صفحه
st.set_page_config(
    page_title="Solar & MPPT Dashboard",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ۲. استایل‌های CSS (رفع باگ آیکون‌های روی‌هم‌افتاده و فونت‌ها)
st.markdown("""
<style>
    /* فراخوانی فونت B Nazanin */
    @font-face {
        font-family: 'B Nazanin';
        src: url('https://cdn.fontcdn.ir/Font/Persian/BNazanin/BNazanin.woff2') format('woff2');
        font-weight: normal;
        font-style: normal;
    }
    @font-face {
        font-family: 'B Nazanin';
        src: url('https://cdn.fontcdn.ir/Font/Persian/BNazanin/BNazanin-Bold.woff2') format('woff2');
        font-weight: bold;
        font-style: normal;
    }

    /* شفاف کردن لایه‌های رویی استریم‌لیت */
    .stApp, [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* عکس پس‌زمینه با کیفیت و تم روشن */
    [data-testid="stAppViewContainer"] { 
        background-image: linear-gradient(rgba(255, 255, 255, 0.75), rgba(240, 248, 255, 0.85)), url('https://images.unsplash.com/photo-1509391365360-2e959784a276?q=85&w=2560&auto=format&fit=crop') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
    }

    /* اعمال فونت فقط روی تگ‌های متنی (حذف span برای جلوگیری از خرابی آیکون‌ها) */
    p, h1, h2, h3, h4, h5, h6, label, button, input, select, textarea, div.metric-title {
        font-family: 'B Nazanin', Tahoma, 'Times New Roman', serif !important;
    }

    [data-testid="stAppViewBlockContainer"], .main .block-container {
        max-width: 1000px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        margin: 0 auto !important;
    }

    /* باکس هدر بالا */
    .header-box {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 16px 24px;
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        direction: rtl;
    }
    .header-item { color: #1e293b; font-size: 19px; font-weight: bold; }
    .header-highlight { color: #2563eb; font-weight: bold; font-family: 'Times New Roman', serif !important; }

    /* باکس کشویی‌ها */
    [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        margin-bottom: 20px !important;
    }
    [data-testid="stExpander"] details summary {
        direction: rtl;
    }
    [data-testid="stExpander"] details summary p {
        font-family: 'B Nazanin', Tahoma, serif !important;
        font-size: 21px !important;
        font-weight: bold !important;
        width: 100%;
        text-align: center !important;
        color: #0f172a !important;
    }

    /* پنل مقادیر زنده */
    .metrics-container {
        padding: 15px 5px;
        display: flex;
        flex-direction: column;
        gap: 30px;
        direction: rtl;
    }
    .metrics-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }
    .metric-item {
        flex: 1;
        min-width: 150px;
        text-align: center;
    }
    .metric-title {
        color: #475569;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .metric-val {
        color: #0f172a;
        font-size: 28px;
        font-weight: bold;
        font-family: 'Times New Roman', serif !important;
        direction: ltr;
        unicode-bidi: embed;
        display: inline-block;
    }

    /* عناوین */
    h1 { 
        font-size: 33px !important; 
        color: #0f172a !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin-bottom: 20px !important;
        text-shadow: 0 1px 6px rgba(255, 255, 255, 0.9);
    }
    h2, h3, .stSubheader { 
        font-size: 26px !important; 
        color: #0f172a !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin-bottom: 15px !important;
        text-shadow: 0 1px 6px rgba(255, 255, 255, 0.9);
    }
    h5 { 
        font-size: 21px !important; 
        color: #1e293b !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin-top: 25px !important; 
        margin-bottom: 10px !important;
    }
    
    /* وسط‌چین کردن دکمه‌های تایم‌فریم */
    div[data-testid="stRadio"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    div[role="radiogroup"] {
        display: inline-flex !important;
        justify-content: center !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        margin: 0 auto !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(8px) !important;
        padding: 12px 25px !important;
        border-radius: 50px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        direction: rtl !important;
    }
    div[role="radiogroup"] label {
        display: inline-flex !important;
        align-items: center !important;
        margin: 0 10px !important;
        cursor: pointer !important;
    }
    div[role="radiogroup"] label p { 
        font-family: 'B Nazanin', Tahoma, serif !important;
        font-size: 19px !important; 
        font-weight: bold !important; 
        color: #0f172a !important; 
        direction: rtl !important;
        unicode-bidi: embed !important;
    }

    /* کادر نمودارها */
    div[data-testid="stVegaLiteChart"], div[data-testid="stArrowVegaLiteChart"] {
        direction: ltr !important;
        background-color: #ffffff !important;
        border-radius: 16px !important;
        padding: 14px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        overflow: hidden !important;
    }
    div[data-testid="stVegaLiteChart"] summary, div[data-testid="stArrowVegaLiteChart"] summary {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# تنظیمات بروزرسانی در سایدبار
st.sidebar.markdown("### ⚙️ تنظیمات داشبورد")
live_update = st.sidebar.checkbox("🔄 بروزرسانی زنده (Live)", value=True, help="برای توقف موقت دریافت داده‌ها، این تیک را بردارید.")

# ۳. دریافت دمای هوای تهران
@st.cache_data(ttl=300)
def get_tehran_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=35.6892&longitude=51.3890&current=temperature_2m&current_weather=true"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=6)
        data = response.json()
        if 'current' in data and 'temperature_2m' in data['current']:
            temp = data['current']['temperature_2m']
        elif 'current_weather' in data:
            temp = data['current_weather']['temperature']
        else:
            temp = 28.5
        return f"{temp} °C"
    except:
        return "28.0 °C"

# ۴. محاسبه زمان و تاریخ تهران
tehran_tz = pytz.timezone('Asia/Tehran')
now_tehran = datetime.now(tehran_tz)
j_date = jdatetime.datetime.fromgregorian(datetime=now_tehran)
shamsi_date_str = j_date.strftime("%Y/%m/%d")
time_str = now_tehran.strftime("%H:%M:%S")
tehran_weather = get_tehran_weather()

st.markdown(f"""
<div class="header-box">
    <div class="header-item">📅 تاریخ: <span class="header-highlight">{shamsi_date_str}</span></div>
    <div class="header-item">⏰ ساعت: <span class="header-highlight">{time_str}</span></div>
    <div class="header-item">🌤️ دمای هوای تهران: <span class="header-highlight" dir="ltr">{tehran_weather}</span></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h1>🔋 مانیتورینگ جامع پنل خورشیدی و سیستم <span dir='ltr'>MPPT</span></h1>", unsafe_allow_html=True)

# ۵. حافظه رم زنده برای دیتای سنسورها
@st.cache_resource
def get_sensor_data():
    return {
        'voltage': 0.0, 'current': 0.0, 'power': 0.0, 'temp': 0.0, 'lux': 0.0, 'watts': 0.0,
        'hist_voltage': [], 'hist_current': [], 'hist_power': [], 'hist_temp': [], 'hist_lux': [], 'hist_watts': [],
        'timestamps': [],
        'log_records': [],
        'last_time': '',
        'mqtt_connected': False,
        'msg_count': 0,
        'last_topic': '-',
        'last_payload': '-'
    }

sensor_data = get_sensor_data()

# ۶. توابع دریافت پیام MQTT
def on_connect(client, userdata, flags, rc, properties=None):
    sensor_data['mqtt_connected'] = True
    client.subscribe("my_powerplant/#")

def on_message(client, userdata, msg):
    topic = msg.topic.lower()
    payload = msg.payload.decode().strip('\x00').strip()
    
    sensor_data['msg_count'] += 1
    sensor_data['last_topic'] = topic
    sensor_data['last_payload'] = payload
    
    try:
        value = float(payload)
        current_time = datetime.now(tehran_tz).strftime("%H:%M:%S")
        sensor_name = topic.split('/')[-1]
        
        if sensor_name == "voltage":
            sensor_data['voltage'] = value
        elif sensor_name == "current":
            sensor_data['current'] = value
        elif sensor_name == "power":
            sensor_data['power'] = value
        elif sensor_name == "temperature":
            sensor_data['temp'] = value
        elif sensor_name == "lux":
            sensor_data['lux'] = value
        elif sensor_name == "watts":
            sensor_data['watts'] = value
            
        if sensor_data['last_time'] != current_time:
            sensor_data['last_time'] = current_time
            
            sensor_data['timestamps'].append(current_time)
            sensor_data['hist_voltage'].append(sensor_data['voltage'])
            sensor_data['hist_current'].append(sensor_data['current'])
            sensor_data['hist_power'].append(sensor_data['power'])
            sensor_data['hist_temp'].append(sensor_data['temp'])
            sensor_data['hist_lux'].append(sensor_data['lux'])
            sensor_data['hist_watts'].append(sensor_data['watts'])
            
            record = {
                'زمان ثبت': current_time,
                'ولتاژ (V)': sensor_data['voltage'],
                'جریان (mA)': sensor_data['current'],
                'توان (mW)': sensor_data['power'],
                'دمای پنل (°C)': sensor_data['temp'],
                'شدت روشنایی (Lux)': sensor_data['lux'],
                'توان تابشی (W/m2)': sensor_data['watts']
            }
            sensor_data['log_records'].append(record)

            if len(sensor_data['timestamps']) > 20000:
                sensor_data['timestamps'].pop(0)
                sensor_data['hist_voltage'].pop(0)
                sensor_data['hist_current'].pop(0)
                sensor_data['hist_power'].pop(0)
                sensor_data['hist_temp'].pop(0)
                sensor_data['hist_lux'].pop(0)
                sensor_data['hist_watts'].pop(0)
                sensor_data['log_records'].pop(0)
    except:
        pass

# ۷. اتصال هوشمند MQTT
@st.cache_resource
def init_mqtt():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    except:
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except:
            client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect("broker.emqx.io", 1883, keepalive=60)
    except:
        client.connect("broker.hivemq.com", 1883, keepalive=60)
        
    client.loop_start()
    return client

try:
    mqtt_client = init_mqtt()
except Exception as e:
    st.error(f"خطا در ایجاد کلاینت MQTT: {e}")

# ۸. پنل کشویی وضعیت اتصال شبکه
with st.expander("🛠️ وضعیت اتصال و شبکه MQTT", expanded=not sensor_data['mqtt_connected']):
    status_color = "🟢 متصل به سرور" if sensor_data['mqtt_connected'] else "🔴 در حال اتصال..."
    st.markdown(f"<div style='text-align: center; font-size: 19px;'><b>وضعیت شبکه‌:</b> {status_color}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 19px;'><b>تعداد کل پیام‌ها:</b> <span style='font-family: Times New Roman, serif;'>{sensor_data['msg_count']}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 19px;'><b>آخرین تاپیک:</b> <span style='font-family: Times New Roman, serif; color: #2563eb;'>{sensor_data['last_topic']}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 19px;'><b>آخرین داده:</b> <span style='font-family: Times New Roman, serif; color: #2563eb;'>{sensor_data['last_payload']}</span></div>", unsafe_allow_html=True)

st.divider()

# ۹. مقادیر عددی زنده
with st.expander("📊 مقادیر زنده پنل خورشیدی و سیستم", expanded=True):
    metrics_html = f"""
    <div class="metrics-container">
        <div class="metrics-row">
            <div class="metric-item">
                <div class="metric-title">⚡ ولتاژ کاری</div>
                <div class="metric-val">{sensor_data['voltage']:.2f} V</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔌 جریان خروجی</div>
                <div class="metric-val">{sensor_data['current']:.2f} mA</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔋 توان تولیدی</div>
                <div class="metric-val">{sensor_data['power']:.2f} mW</div>
            </div>
        </div>
        <div class="metrics-row">
            <div class="metric-item">
                <div class="metric-title">🌡️ دمای سطح پنل</div>
                <div class="metric-val">{sensor_data['temp']:.2f} °C</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">☀️ شدت روشنایی</div>
                <div class="metric-val">{sensor_data['lux']:.1f} Lux</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔆 توان تابشی</div>
                <div class="metric-val">{sensor_data['watts']:.2f} W/m²</div>
            </div>
        </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)

st.divider()

# ۱۰. رسم نمودارها
st.subheader("📈 نمودارهای رفتاری سیستم")

st.markdown("<div style='text-align: center; font-size: 20px; font-weight: bold; color: #0f172a; margin-bottom: 12px;'>⏱️ انتخاب بازه زمانی نمایش (تایم‌فریم):</div>", unsafe_allow_html=True)

timeframe = st.radio(
    label="بازه زمانی", 
    options=["۱ دقیقه اخیر", "۵ دقیقه اخیر", "۱۵ دقیقه اخیر", "۱ ساعت اخیر", "۱۲ ساعت اخیر", "کل تاریخچه"],
    horizontal=True,
    index=1,
    label_visibility="collapsed"
)

limit_map = {
    "۱ دقیقه اخیر": 12,
    "۵ دقیقه اخیر": 60,
    "۱۵ دقیقه اخیر": 180,
    "۱ ساعت اخیر": 720,
    "۱۲ ساعت اخیر": 8640,
    "کل تاریخچه": None
}
point_limit = limit_map[timeframe]

def draw_chart(data_list, time_list, chart_name, line_color, limit=None):
    if len(data_list) > 0 and len(time_list) == len(data_list):
        if limit and len(data_list) > limit:
            sub_data = data_list[-limit:]
            sub_time = time_list[-limit:]
        else:
            sub_data = data_list
            sub_time = time_list
            
        df = pd.DataFrame({
            'زمان ثبت': sub_time,
            chart_name: sub_data
        })
        df = df.set_index('زمان ثبت')
        st.line_chart(df, color=line_color, height=280)
    else:
        st.info("در حال جمع‌آوری داده‌ها...")

st.markdown("##### ⚡ نوسانات ولتاژ (V)")
draw_chart(sensor_data['hist_voltage'], sensor_data['timestamps'], "ولتاژ (V)", "#2563eb", limit=point_limit)

st.markdown("##### 🔌 نوسانات جریان (mA)")
draw_chart(sensor_data['hist_current'], sensor_data['timestamps'], "جریان (mA)", "#d97706", limit=point_limit)

st.markdown("##### 🔋 تغییرات توان (mW)")
draw_chart(sensor_data['hist_power'], sensor_data['timestamps'], "توان (mW)", "#059669", limit=point_limit)

st.markdown("##### ☀️ نوسانات شدت روشنایی (Lux)")
draw_chart(sensor_data['hist_lux'], sensor_data['timestamps'], "شدت روشنایی (Lux)", "#ca8a04", limit=point_limit)

st.markdown("##### 🔆 نوسانات توان تابشی خورشید (W/m²)")
draw_chart(sensor_data['hist_watts'], sensor_data['timestamps'], "توان تابشی (W/m²)", "#ea580c", limit=point_limit)

st.markdown("##### 🌡️ تغییرات دمای پنل (°C)")
draw_chart(sensor_data['hist_temp'], sensor_data['timestamps'], "دمای پنل (°C)", "#dc2626", limit=point_limit)

st.divider()

# ۱۱. جدول آرشیو داده‌ها
with st.expander("🗃️ مشاهده و دانلود جدول آرشیو زمان‌دار داده‌ها", expanded=False):
    if len(sensor_data['log_records']) > 0:
        df_logs = pd.DataFrame(sensor_data['log_records'])
        st.dataframe(df_logs.iloc[::-1], width='stretch', height=280)
        
        csv_data = df_logs.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 دریافت فایل CSV داده‌ها",
            data=csv_data,
            file_name=f"solar_log_{shamsi_date_str.replace('/','-')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("در حال دریافت داده‌ها از سخت‌افزار...")

# ۱۲. بروزرسانی خودکار با دکمه کنترل
if live_update:
    time.sleep(3)
    st.rerun()