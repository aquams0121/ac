import streamlit as st
import time
import datetime
import json
import os
import pandas as pd

# --- 설정 및 데이터 관리 ---
st.set_page_config(page_title="통합 알람시계", page_icon="⏰", layout="centered")

ALARM_FILE = "alarms.json"

def load_alarms():
    if os.path.exists(ALARM_FILE):
        with open(ALARM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_alarms(alarms):
    with open(ALARM_FILE, "w", encoding="utf-8") as f:
        json.dump(alarms, f, ensure_ascii=False, indent=4)

# 세션 상태 초기화
if 'alarms' not in st.session_state:
    st.session_state.alarms = load_alarms()
if 'sw_running' not in st.session_state:
    st.session_state.sw_running = False
if 'sw_start_time' not in st.session_state:
    st.session_state.sw_start_time = None
if 'sw_elapsed' not in st.session_state:
    st.session_state.sw_elapsed = 0.0
if 'sw_laps' not in st.session_state:
    st.session_state.sw_laps = []
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'timer_end_time' not in st.session_state:
    st.session_state.timer_end_time = None
if 'timer_paused_time' not in st.session_state:
    st.session_state.timer_paused_time = 0

# --- 공통 UI: 탭 구성 ---
tab_alarm, tab_stopwatch, tab_timer = st.tabs(["⏰ 알람", "⏱ 스톱워치", "⏲ 타이머"])

# ==========================================
# 탭 1: 알람 (Alarm)
# ==========================================
with tab_alarm:
    st.title("알람 관리")
    
    # 새 알람 추가 폼
    with st.expander("+ 새 알람 추가"):
        col1, col2 = st.columns(2)
        with col1:
            alarm_time = st.time_input("시간 설정", value=datetime.time(7, 30))
        with col2:
            label = st.text_input("라벨 (최대 20자)", max_chars=20, placeholder="예: 출근, 약 먹기")
            
        repeat = st.selectbox("반복 설정", ["안 함", "매일", "평일(월~금)", "주말(토~일)"])
        sound = st.selectbox("알람음", ["기본음 1", "기본음 2", "자연의 소리", "무음"])
        vibration = st.checkbox("진동 켜기", value=True)
        
        # 버튼에 key 추가
        if st.button("알람 저장", key="btn_save_alarm", use_container_width=True):
            new_alarm = {
                "id": str(time.time()),
                "time": alarm_time.strftime("%H:%M"),
                "label": label if label else "알람",
                "repeat": repeat,
                "sound": sound,
                "vibration": vibration,
                "active": True
            }
            st.session_state.alarms.append(new_alarm)
            save_alarms(st.session_state.alarms)
            st.success("알람이 추가되었습니다!")
            st.rerun()

    st.markdown("---")
    st.subheader("알람 목록")
    
    # 시간순 정렬
    sorted_alarms = sorted(st.session_state.alarms, key=lambda x: x['time'])
    
    if not sorted_alarms:
        st.info("설정된 알람이 없습니다.")
    else:
        for idx, alarm in enumerate(sorted_alarms):
            c1, c2, c3 = st.columns([5, 2, 1])
            is_active = alarm['active']
            color = "normal" if is_active else "gray"
            
            with c1:
                st.markdown(f"<h2 style='color: {color}; margin-bottom: 0px;'>{alarm['time']}</h2>", unsafe_allow_html=True)
                st.caption(f"라벨: {alarm['label']} | 반복: {alarm['repeat']}")
            with c2:
                # On/Off 토글 (이미 고유 key 있음)
                toggle = st.toggle("On", value=is_active, key=f"toggle_{alarm['id']}")
                if toggle != is_active:
                    st.session_state.alarms[idx]['active'] = toggle
                    save_alarms(st.session_state.alarms)
                    st.rerun()
            with c3:
                # 삭제 버튼 (이미 고유 key 있음)
                if st.button("❌", key=f"del_{alarm['id']}"):
                    st.session_state.alarms.pop(idx)
                    save_alarms(st.session_state.alarms)
                    st.rerun()
            st.divider()

# ==========================================
# 탭 2: 스톱워치 (Stopwatch)
# ==========================================
with tab_stopwatch:
    st.title("스톱워치")
    
    current_sw_time = st.session_state.sw_elapsed
    if st.session_state.sw_running:
        current_sw_time += time.time() - st.session_state.sw_start_time

    mins = int(current_sw_time // 60)
    secs = int(current_sw_time % 60)
    millis = int((current_sw_time * 100) % 100)
    time_str = f"{mins:02d}:{secs:02d}.{millis:02d}"
    
    st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{time_str}</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.sw_running:
            # 스톱워치 일시정지 (key 부여)
            if st.button("⏸ 일시정지", key="sw_pause", use_container_width=True):
                st.session_state.sw_elapsed += time.time() - st.session_state.sw_start_time
                st.session_state.sw_running = False
                st.rerun()
        else:
            # 스톱워치 시작 (key 부여)
            if st.button("▶️ 시작", key="sw_start", use_container_width=True):
                st.session_state.sw_start_time = time.time()
                st.session_state.sw_running = True
                st.rerun()
    with col2:
        if st.session_state.sw_running:
            # 랩 (key 부여)
            if st.button("⏱ 랩", key="sw_lap", use_container_width=True):
                lap_time = current_sw_time
                prev_lap = st.session_state.sw_laps[-1]['누적 시간'] if st.session_state.sw_laps else 0
                interval = lap_time - prev_lap
                
                st.session_state.sw_laps.append({
                    "랩": len(st.session_state.sw_laps) + 1,
                    "구간 시간": f"{int(interval//60):02d}:{int(interval%60):02d}.{int((interval*100)%100):02d}",
                    "누적 시간": f"{mins:02d}:{secs:02d}.{millis:02d}",
                    "_raw_interval": interval 
                })
                st.rerun()
        else:
            # 초기화 (key 부여)
            if st.button("🔄 초기화", key="sw_reset", use_container_width=True):
                st.session_state.sw_elapsed = 0.0
                st.session_state.sw_laps = []
                st.session_state.sw_running = False
                st.rerun()
                
    if st.session_state.sw_laps:
        st.subheader("랩타임 기록")
        df_laps = pd.DataFrame(st.session_state.sw_laps)
        if len(df_laps) > 1:
            max_idx = df_laps['_raw_interval'].idxmax()
            min_idx = df_laps['_raw_interval'].idxmin()
            
            def highlight_laps(row):
                if row.name == max_idx: return ['color: red'] * len(row)
                if row.name == min_idx: return ['color: blue'] * len(row)
                return [''] * len(row)
                
            st.dataframe(df_laps.drop(columns=['_raw_interval']).style.apply(highlight_laps, axis=1), use_container_width=True)
        else:
            st.dataframe(df_laps.drop(columns=['_raw_interval']), use_container_width=True)

# ==========================================
# 탭 3: 타이머 (Timer)
# ==========================================
with tab_timer:
    st.title("타이머")
    
    st.markdown("**프리셋**")
    p1, p2, p3, p4 = st.columns(4)
    preset_time = 0
    # 프리셋 버튼들에 key 부여
    if p1.button("3분", key="preset_3", use_container_width=True): preset_time = 3 * 60
    if p2.button("5분", key="preset_5", use_container_width=True): preset_time = 5 * 60
    if p3.button("10분", key="preset_10", use_container_width=True): preset_time = 10 * 60
    if p4.button("30분", key="preset_30", use_container_width=True): preset_time = 30 * 60
    
    if not st.session_state.timer_running and st.session_state.timer_paused_time == 0:
        col_h, col_m, col_s = st.columns(3)
        with col_h: h = st.number_input("시", min_value=0, max_value=23, value=preset_time//3600, key="t_hour")
        with col_m: m = st.number_input("분", min_value=0, max_value=59, value=(preset_time%3600)//60, key="t_min")
        with col_s: s = st.number_input("초", min_value=0, max_value=59, value=preset_time%60, key="t_sec")
        total_seconds = h * 3600 + m * 60 + s
    else:
        if st.session_state.timer_running:
            remains = max(0, st.session_state.timer_end_time - time.time())
            if remains == 0:
                st.session_state.timer_running = False
                st.success("🚨 타이머 종료! (알람음 재생)")
                st.balloons()
        else:
            remains = st.session_state.timer_paused_time
            
        rh, rm, rs = int(remains // 3600), int((remains % 3600) // 60), int(remains % 60)
        st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: tomato;'>{rh:02d}:{rm:02d}:{rs:02d}</h1>", unsafe_allow_html=True)
        total_seconds = remains

    st.markdown("<br>", unsafe_allow_html=True)
    col_start, col_cancel = st.columns(2)
    
    with col_start:
        if st.session_state.timer_running:
            # 타이머 일시정지 (key 부여)
            if st.button("⏸ 일시정지", key="timer_pause", use_container_width=True):
                st.session_state.timer_paused_time = remains
                st.session_state.timer_running = False
                st.rerun()
        else:
            # 타이머 시작 (key 부여)
            if st.button("▶️ 시작", key="timer_start", use_container_width=True, disabled=(total_seconds <= 0)):
                st.session_state.timer_end_time = time.time() + total_seconds
                st.session_state.timer_running = True
                st.session_state.timer_paused_time = 0
                st.rerun()
                
    with col_cancel:
        # 타이머 취소 (key 부여)
        if st.button("⏹ 취소/초기화", key="timer_cancel", use_container_width=True):
            st.session_state.timer_running = False
            st.session_state.timer_paused_time = 0
            st.rerun()

# 작동 중 실시간 UI 업데이트를 위한 헬퍼 (Streamlit 제약 극복용)
if st.session_state.sw_running or st.session_state.timer_running:
    time.sleep(0.1)
    st.rerun()
