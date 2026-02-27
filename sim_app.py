import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import random

# ==========================================
# CẤU HÌNH TRANG & STATE
# ==========================================
st.set_page_config(page_title="Riken Viet - Gas Simulator", layout="wide", initial_sidebar_state="expanded")

# Khởi tạo các biến toàn cục (Session State)
if 'running' not in st.session_state: st.session_state.running = False
if 'current_val' not in st.session_state: st.session_state.current_val = 0.0
if 'target_val' not in st.session_state: st.session_state.target_val = 0.0
if 'history' not in st.session_state: st.session_state.history = [0.0] * 60  # Lưu 60 giây lịch sử
if 'a1_latched' not in st.session_state: st.session_state.a1_latched = False
if 'a2_latched' not in st.session_state: st.session_state.a2_latched = False
if 'fault_latched' not in st.session_state: st.session_state.fault_latched = False

# Ngưỡng cài đặt (Set-points)
A1_SP = 25.0 # 25% LEL
A2_SP = 50.0 # 50% LEL

# ==========================================
# GIAO DIỆN ĐIỀU KHIỂN (SIDEBAR)
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Riken_Keiki_logo.svg/2560px-Riken_Keiki_logo.svg.png", width=150) # Tạm thay logo web
    st.markdown("### 🎛️ BẢNG ĐIỀU KHIỂN SỰ CỐ")
    st.info("Nhập các kịch bản để mô phỏng Tủ trung tâm.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔥 Xì khí (25%)", help="Rò rỉ nhỏ"):
            st.session_state.target_val = 30.0
            st.session_state.fault_latched = False
    with col2:
        if st.button("💥 Vỡ ống (60%)", help="Rò rỉ lớn"):
            st.session_state.target_val = 65.0
            st.session_state.fault_latched = False
            
    if st.button("💨 Quạt xả (Purge / Clean)", use_container_width=True):
        st.session_state.target_val = 0.0
        
    st.markdown("---")
    st.markdown("### ⚙️ THAO TÁC TỦ RM-6000")
    
    if st.button("🔄 Bấm RESET (Acknowledge)", type="primary", use_container_width=True):
        if st.session_state.current_val < A1_SP: st.session_state.a1_latched = False
        if st.session_state.current_val < A2_SP: st.session_state.a2_latched = False
        st.session_state.fault_latched = False
        
    if st.button("⚠️ Tạo lỗi Đứt cáp (Fault)", use_container_width=True):
        st.session_state.fault_latched = True
        st.session_state.current_val = 0.0
        st.session_state.target_val = 0.0
        
    st.markdown("---")
    # Nút Bật/Tắt vòng lặp Real-time
    run_btn_text = "⏸️ Dừng Mô phỏng" if st.session_state.running else "▶️ Chạy Thời gian thực"
    if st.button(run_btn_text, type="secondary", use_container_width=True):
        st.session_state.running = not st.session_state.running
        st.rerun()

# ==========================================
# ENGINE TOÁN HỌC (CẬP NHẬT LOGIC)
# ==========================================
if st.session_state.running:
    # Mô phỏng T90: Giá trị tiến dần về Target theo hàm mũ (như thật)
    diff = st.session_state.target_val - st.session_state.current_val
    st.session_state.current_val += diff * 0.15 
    
    # Thêm nhiễu (Noise) ngẫu nhiên để biểu đồ dao động thực tế
    if st.session_state.current_val > 1.0:
        st.session_state.current_val += random.uniform(-0.5, 0.5)
        
    # Chốt chặn min-max
    st.session_state.current_val = max(0.0, min(100.0, st.session_state.current_val))
    
    # Kích hoạt báo động (Latching)
    if st.session_state.current_val >= A1_SP: st.session_state.a1_latched = True
    if st.session_state.current_val >= A2_SP: st.session_state.a2_latched = True
    
    # Cập nhật lịch sử biểu đồ
    st.session_state.history.append(st.session_state.current_val)
    if len(st.session_state.history) > 60:
        st.session_state.history.pop(0)

# ==========================================
# GIAO DIỆN HMI (MAIN DASHBOARD)
# ==========================================
st.title("🛡️ HMI Tủ Trung Tâm - Riken Viet Simulator")

# --- KHU VỰC 1: ĐÈN LED TRẠNG THÁI ---
st.markdown("### 🚥 Trạng thái Đèn Báo (LED Indicators)")
led_col1, led_col2, led_col3, led_col4 = st.columns(4)

def draw_led(label, color, is_on):
    bg_color = color if is_on else "#333333"
    shadow = f"box-shadow: 0 0 15px {color};" if is_on else ""
    st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #222; border-radius: 10px; border: 1px solid #444;">
            <div style="width: 30px; height: 30px; border-radius: 50%; background-color: {bg_color}; margin: 0 auto; {shadow}"></div>
            <h4 style="color: white; margin-top: 10px;">{label}</h4>
        </div>
    """, unsafe_allow_html=True)

with led_col1: draw_led("POWER", "#00FF00", True) # Đèn nguồn luôn xanh
with led_col2: draw_led("ALARM 1", "#FFD700", st.session_state.a1_latched) # Vàng
with led_col3: draw_led("ALARM 2", "#FF0000", st.session_state.a2_latched) # Đỏ
with led_col4: draw_led("FAULT", "#FFA500", st.session_state.fault_latched) # Cam

st.markdown("<br>", unsafe_allow_html=True)

# --- KHU VỰC 2: GAUGE CHART & EXTERNAL RELAYS ---
col_gauge, col_relay = st.columns([2, 1])

with col_gauge:
    # Thiết kế mặt đồng hồ (Gauge) cực ngầu bằng Plotly
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = st.session_state.current_val,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Nồng độ Khí Methane (CH4)", 'font': {'size': 24, 'color': 'white'}},
        number = {'suffix': " %LEL", 'font': {'size': 50, 'color': 'white'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white"},
            'bar': {'color': "#00FFAA"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, A1_SP], 'color': "rgba(0, 255, 0, 0.2)"},
                {'range': [A1_SP, A2_SP], 'color': "rgba(255, 255, 0, 0.3)"},
                {'range': [A2_SP, 100], 'color': "rgba(255, 0, 0, 0.4)"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': A2_SP}
        }
    ))
    fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=350, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_relay:
    st.markdown("### 🔌 Liên động Thiết bị")
    
    # Logic của Rơ-le: A1 bật quạt, A2 đóng van
    fan_on = st.session_state.a1_latched
    valve_closed = st.session_state.a2_latched
    
    # Hiển thị Quạt hút
    fan_color = "#00FF00" if fan_on else "#555555"
    fan_text = "ĐANG CHẠY" if fan_on else "TẮT"
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid {fan_color};">
            <h3 style="margin:0; color: {fan_color};">💨 QUẠT HÚT KHÍ</h3>
            <p style="margin:0; color: #AAA; font-size: 18px;">Trạng thái: <b>{fan_text}</b></p>
            <p style="margin:0; color: #666; font-size: 12px;">(Kích hoạt bởi Alarm 1)</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Hiển thị Van ngắt
    valve_color = "#FF0000" if valve_closed else "#00FF00"
    valve_text = "ĐÃ KHÓA (SHUT-OFF)" if valve_closed else "ĐANG MỞ (OPEN)"
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid {valve_color};">
            <h3 style="margin:0; color: {valve_color};">🛑 VAN CẤP KHÍ</h3>
            <p style="margin:0; color: #AAA; font-size: 18px;">Trạng thái: <b>{valve_text}</b></p>
            <p style="margin:0; color: #666; font-size: 12px;">(Kích hoạt bởi Alarm 2)</p>
        </div>
    """, unsafe_allow_html=True)


# --- KHU VỰC 3: LIVE TREND CHART (BIỂU ĐỒ XU HƯỚNG) ---
st.markdown("### 📈 Biểu đồ Xu hướng (Live Trend 60s)")
df_hist = pd.DataFrame({"Thời gian": range(60), "Nồng độ (%LEL)": st.session_state.history})

fig_line = go.Figure()
fig_line.add_trace(go.Scatter(x=df_hist["Thời gian"], y=df_hist["Nồng độ (%LEL)"], mode='lines+markers', line=dict(color='#00FFAA', width=3), marker=dict(size=4), fill='tozeroy', fillcolor='rgba(0, 255, 170, 0.1)'))

# Vẽ đường nét đứt biểu diễn set-point
fig_line.add_hline(y=A1_SP, line_dash="dash", line_color="yellow", annotation_text="ALARM 1 (25%)", annotation_position="top right")
fig_line.add_hline(y=A2_SP, line_dash="dash", line_color="red", annotation_text="ALARM 2 (50%)", annotation_position="top right")

fig_line.update_layout(
    xaxis=dict(title="Thời gian trôi qua (Tick)", autorange="reversed", gridcolor="#333"), # Lật ngược trục X để chạy từ phải sang trái
    yaxis=dict(title="% LEL", range=[0, 100], gridcolor="#333"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=300, margin=dict(l=0, r=0, t=30, b=0),
    font=dict(color="white")
)
st.plotly_chart(fig_line, use_container_width=True)


# ==========================================
# VÒNG LẶP AUTO-REFRESH TẠO HIỆU ỨNG REAL-TIME
# ==========================================
if st.session_state.running:
    time.sleep(0.4) # Tốc độ quét 400ms / nhịp
    st.rerun()
