import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import time
import requests
from datetime import datetime
import pytz
import jdatetime

# ۱. تنظیمات اصلی صفحه (تغییر به حالت Wide برای چیدمان دو ستونه)
st.set_page_config(
    page_title="Solar & MPPT Dashboard",
    page_icon="⚡",
    layout="wide",  # تغییر کلیدی برای تمام‌صفحه شدن
    initial_sidebar_state="collapsed"
)

# ۲. استایل‌های CSS (سازگار با چیدمان عریض و نقشه جدید)
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

    /* عکس پس‌زمینه با کیفیت */
    [data-testid="stAppViewContainer"] { 
        background-image: linear-gradient(rgba(255, 255, 255, 0.75), rgba(240, 248, 255, 0.85)), url('https://images.unsplash.com/photo-1509391365360-2e959784a276?q=85&w=2560&auto=format&fit=crop') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
    }

    /* اعمال فونت روی تگ‌های متنی */
    p, h1, h2, h3, h4, h5, h6, label, button, input, select, textarea, div.metric-title {
        font-family: 'B Nazanin', Tahoma, 'Times New Roman', serif !important;
    }

    /* حذف محدودیت عرض برای حالت Wide */
    [data-testid="stAppViewBlockContainer"], .main .block-container {
        max-width: 1600px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* باکس هدر بالا (ساعت و تاریخ) */
    .header-box {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 18px 20px;
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 25px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        direction: rtl;
    }
    .header-item { color: #1e293b; font-size: 19px; font-weight: bold; }
    .header-highlight { color: #2563eb; font-weight: bold; font-family: 'Times New Roman', serif !important; }

    /* باکس دیتاهای لحظه‌ای */
    .live-data-box {
        background-color: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 25px;
    }
    .live-data-title {
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        color: #0f172a;
        margin-bottom: 20px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px;
    }

    /* چیدمان شبکه‌ای مقادیر زنده برای ستون باریک */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
        direction: rtl;
    }
    .metric-item {
        background: rgba(241, 245, 249, 0.6);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px;
        padding: 12px 5px;
        text-align: center;
    }
    .energy-item {
        grid-column: span 2;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(52, 211, 153, 0.25));
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .metric-title {
        color: #475569;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-val {
        color: #0f172a;
        font-size: 24px;
        font-weight: bold;
        font-family: 'Times New Roman', serif !important;
        direction: ltr;
        unicode-bidi: embed;
        display: inline-block;
    }
    .energy-val { color: #047857; font-size: 30px; }

    /* کشویی‌ها (وضعیت شبکه و آرشیو) */
    [data-testid="stExpander"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        margin-bottom: 15px !important;
    }
    [data-testid="stExpander"] details {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08) !important;
        padding: 0 !important;
    }
    [data-testid="stExpander"] details summary { direction: rtl; }
    [data-testid="stExpander"] details summary p {
        font-family: 'B Nazanin', Tahoma, serif !important;
        font-size: 20px !important;
        font-weight: bold !important;
        width: 100%;
        text-align: center !important;
        color: #0f172a !important;
    }

    /* عناوین نمودارها */
    h5 { 
        font-size: 20px !important; 
        color: #1e293b !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin-top: 15px !important; 
        margin-bottom: 8px !important;
    }
    
    /* تایم‌فریم */
    div[data-testid="stRadio"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin-bottom: 15px;
    }
    div[role="radiogroup"] {
        display: inline-flex !important;
        justify-content: center !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(8px) !important;
        padding: 10px 20px !important;
        border-radius: 50px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        direction: rtl !important;
    }
    div[role="radiogroup"] label p { 
        font-family: 'B Nazanin', Tahoma, serif !important;
        font-size: 18px !important; 
        font-weight: bold !important; 
        color: #0f172a !important; 
        direction: rtl !important;
    }

    /* کادر نمودارها */
    div[data-testid="stVegaLiteChart"], div[data-testid="stArrowVegaLiteChart"] {
        direction: ltr !important;
        background-color: #ffffff !important;
        border-radius: 14px !important;
        padding: 10px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        overflow: hidden !important;
    }
    div[data-testid="stVegaLiteChart"] summary, div[data-testid="stArrowVegaLiteChart"] summary { display: none !important; }
</style>
""", unsafe_allow_html=True)

# تنظیمات بروزرسانی در سایدبار
st.sidebar.markdown("### ⚙️ تنظیمات داشبورد")
live_update = st.sidebar.checkbox("🔄 بروزرسانی زنده (Live)", value=True)

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

# ۴. محاسبه زمان و تاریخ
tehran_tz = pytz.timezone('Asia/Tehran')
now_tehran = datetime.now(tehran_tz)
j_date = jdatetime.datetime.fromgregorian(datetime=now_tehran)
shamsi_date_str = j_date.strftime("%Y/%m/%d")
time_str = now_tehran.strftime("%H:%M:%S")
tehran_weather = get_tehran_weather()

# ۵. حافظه رم زنده برای دیتای سنسورها
@st.cache_resource
def get_sensor_data():
    return {
        'voltage': 0.0, 'current': 0.0, 'power': 0.0, 'temp': 0.0, 'lux': 0.0, 'watts': 0.0,
        'total_energy_mWh': 0.0, 'last_power_time': 0.0,
        'hist_voltage': [], 'hist_current': [], 'hist_power': [], 'hist_temp': [], 'hist_lux': [], 'hist_watts': [], 'hist_energy': [],
        'timestamps': [], 'log_records': [], 'last_time': '', 'mqtt_connected': False, 'msg_count': 0,
        'last_topic': '-', 'last_payload': '-'
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
        current_time_str = datetime.now(tehran_tz).strftime("%H:%M:%S")
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
                'زمان ثبت': current_time_str,
                'ولتاژ (V)': sensor_data['voltage'], 'جریان (mA)': sensor_data['current'],
                'توان (mW)': sensor_data['power'], 'انرژی (mWh)': round(sensor_data['total_energy_mWh'], 4),
                'دما (°C)': sensor_data['temp'], 'روشنایی (Lux)': sensor_data['lux'], 'تابش (W/m2)': sensor_data['watts']
            }
            sensor_data['log_records'].append(record)

            if len(sensor_data['timestamps']) > 20000:
                sensor_data['timestamps'].pop(0); sensor_data['hist_voltage'].pop(0)
                sensor_data['hist_current'].pop(0); sensor_data['hist_power'].pop(0)
                sensor_data['hist_temp'].pop(0); sensor_data['hist_lux'].pop(0)
                sensor_data['hist_watts'].pop(0); sensor_data['hist_energy'].pop(0)
                sensor_data['log_records'].pop(0)
    except:
        pass

# ۷. راه‌اندازی MQTT
@st.cache_resource
def init_mqtt():
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

try: mqtt_client = init_mqtt()
except Exception as e: st.error(f"خطا در MQTT: {e}")

# ==========================================
# پیاده‌سازی ساختار دو ستونه بر اساس نقشه
# ==========================================
st.markdown("<h1 style='margin-bottom: 30px;'>🔋 مانیتورینگ جامع پنل خورشیدی و سیستم <span dir='ltr'>MPPT</span></h1>", unsafe_allow_html=True)

# ستون چپ (کادر دیتاها) و ستون راست (نمودارها)
col_left, col_right = st.columns([1, 1.8], gap="large")

# ----------------- ستون سمت چپ -----------------
with col_left:
    # بخش ۱: هدر زمان و تاریخ
    st.markdown(f"""
    <div class="header-box">
        <div class="header-item">📅 تاریخ: <span class="header-highlight">{shamsi_date_str}</span></div>
        <div class="header-item">⏰ ساعت: <span class="header-highlight">{time_str}</span></div>
        <div class="header-item">🌤️ دمای تهران: <span class="header-highlight" dir="ltr">{tehran_weather}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # بخش ۲: دیتاهای لحظه‌ای (جدول ۲ ستونه متناسب با فضای باریک)
    st.markdown(f"""
    <div class="live-data-box">
        <div class="live-data-title">دیتاهای لحظه‌ای سیستم</div>
        <div class="metrics-grid">
            <div class="metric-item energy-item">
                <div class="metric-title">⚡ مجموع انرژی (کنتور)</div>
                <div class="metric-val energy-val">{sensor_data['total_energy_mWh']:.3f} <span style="font-size: 18px;">mWh</span></div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔌 جریان</div>
                <div class="metric-val">{sensor_data['current']:.2f} mA</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">⚡ ولتاژ</div>
                <div class="metric-val">{sensor_data['voltage']:.2f} V</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">☀️ شدت نور</div>
                <div class="metric-val">{sensor_data['lux']:.1f} Lux</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔋 توان</div>
                <div class="metric-val">{sensor_data['power']:.2f} mW</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🌡️ دمای پنل</div>
                <div class="metric-val">{sensor_data['temp']:.1f} °C</div>
            </div>
            <div class="metric-item">
                <div class="metric-title">🔆 تابش</div>
                <div class="metric-val">{sensor_data['watts']:.2f} W/m²</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # بخش ۳: کادرهای کشویی پایین (وضعیت شبکه و آرشیو)
    with st.expander("🛠️ وضعیت اتصال و شبکه MQTT", expanded=False):
        status_color = "🟢 متصل" if sensor_data['mqtt_connected'] else "🔴 قطعی"
        st.markdown(f"<div style='text-align: center; font-size: 18px;'>وضعیت: {status_color} | پیام‌ها: <span dir='ltr'>{sensor_data['msg_count']}</span></div>", unsafe_allow_html=True)

    with st.expander("🗃️ دانلود جدول آرشیو داده‌ها", expanded=False):
        if len(sensor_data['log_records']) > 0:
            df_logs = pd.DataFrame(sensor_data['log_records'])
            csv_data = df_logs.to_csv(index=False).encode('utf-8-sig')
            st.download_button(label="📥 دریافت فایل CSV", data=csv_data, file_name=f"solar_log_{shamsi_date_str.replace('/','-')}.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("در حال جمع‌آوری دیتا...")

# ----------------- ستون سمت راست -----------------
with col_right:
    # بخش ۱: انتخابگر تایم‌فریم
    timeframe = st.radio(
        label="بازه زمانی", 
        options=["۱ دقیقه اخیر", "۵ دقیقه اخیر", "۱۵ دقیقه اخیر", "۱ ساعت اخیر", "۱۲ ساعت اخیر", "کل تاریخچه"],
        horizontal=True, index=1, label_visibility="collapsed"
    )

    limit_map = {"۱ دقیقه اخیر": 12, "۵ دقیقه اخیر": 60, "۱۵ دقیقه اخیر": 180, "۱ ساعت اخیر": 720, "۱۲ ساعت اخیر": 8640, "کل تاریخچه": None}
    point_limit = limit_map[timeframe]

    def draw_chart(data_list, time_list, chart_name, line_color, limit=None):
        if len(data_list) > 0 and len(time_list) == len(data_list):
            sub_data = data_list[-limit:] if limit and len(data_list) > limit else data_list
            sub_time = time_list[-limit:] if limit and len(data_list) > limit else time_list
            df = pd.DataFrame({'زمان': sub_time, chart_name: sub_data}).set_index('زمان')
            st.line_chart(df, color=line_color, height=210) # ارتفاع کمتر برای جا شدن در صفحه
        else:
            st.info("در حال جمع‌آوری...")

    # بخش ۲: شبکه نمودارها (دو ستون داخلی برای ستون راست)
    chart_col_left, chart_col_right = st.columns(2)

    # ستون راستِ نمودارها (ولتاژ، توان، وات بر متر نور)
    with chart_col_right:
        st.markdown("##### ⚡ نمودار ولتاژ (V)")
        draw_chart(sensor_data['hist_voltage'], sensor_data['timestamps'], "ولتاژ", "#2563eb", limit=point_limit)

        st.markdown("##### 🔋 نمودار توان (mW)")
        draw_chart(sensor_data['hist_power'], sensor_data['timestamps'], "توان", "#059669", limit=point_limit)

        st.markdown("##### 🔆 وات بر متر نور (W/m²)")
        draw_chart(sensor_data['hist_watts'], sensor_data['timestamps'], "توان تابشی", "#ea580c", limit=point_limit)

    # ستون چپِ نمودارها (جریان، شدت نور، انرژی)
    with chart_col_left:
        st.markdown("##### 🔌 نمودار جریان (mA)")
        draw_chart(sensor_data['hist_current'], sensor_data['timestamps'], "جریان", "#d97706", limit=point_limit)

        st.markdown("##### ☀️ نمودار شدت نور (Lux)")
        draw_chart(sensor_data['hist_lux'], sensor_data['timestamps'], "شدت نور", "#ca8a04", limit=point_limit)

        st.markdown("##### ⚡ نمودار انرژی تولیدی (mWh)")
        draw_chart(sensor_data['hist_energy'], sensor_data['timestamps'], "انرژی", "#10b981", limit=point_limit)

# بروزرسانی زنده
if live_update:
    time.sleep(3.5)
    st.rerun()