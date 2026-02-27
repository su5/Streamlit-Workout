import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Dependency Check - This will trigger if requirements.txt is missing
try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    st.error("Missing dependency: Please ensure 'plotly' is in your requirements.txt file.")
    st.stop()

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="Iron Ledger", layout="wide")

DEFAULT_ROUTINES = ["Bench Press", "Hammer Curl", "Frenchman's Dilemma", "Preacher Curl"]

if 'user_name' not in st.session_state:
    st.session_state.user_name = "Clay"
if 'workout_logs' not in st.session_state:
    st.session_state.workout_logs = []
if 'weight_logs' not in st.session_state:
    st.session_state.weight_logs = pd.DataFrame(columns=["UID", "Timestamp", "User", "Weight", "Location", "Notes"])
if 'theme_dark' not in st.session_state:
    st.session_state.theme_dark = False
if 'edit_buffer' not in st.session_state:
    st.session_state.edit_buffer = None

# Theme CSS
if st.session_state.theme_dark:
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        [data-testid="stMetric"] { background-color: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 15px; }
        div[data-testid="stExpander"] { background-color: #161B22; border: 1px solid #30363D; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
def get_routines():
    logged = list(set([w['Routine'] for w in st.session_state.workout_logs]))
    return sorted(list(set(DEFAULT_ROUTINES + logged)))

def get_pr_table():
    if not st.session_state.workout_logs:
        return pd.DataFrame()
    
    routines = get_routines()
    pr_rows = []
    
    for r in routines:
        logs = [w for w in st.session_state.workout_logs if w['Routine'] == r]
        if not logs: continue
        
        # All-time PR
        all_sets = []
        for l in logs:
            for s in l['Sets']:
                all_sets.append({**s, "date": l['Timestamp']})
        pr_set = max(all_sets, key=lambda x: x['weight'])
        
        # Latest log
        latest_log = sorted(logs, key=lambda x: x['Timestamp'])[-1]
        latest_set = max(latest_log['Sets'], key=lambda x: x['weight'])
        
        pr_rows.append({
            "Routine": r,
            "Max Weight": f"{pr_set['weight']} lbs",
            "Reps @ Max": pr_set['reps'],
            "Date of Max": pr_set['date'],
            "Last Max": f"{latest_set['weight']} lbs",
            "Last Reps": latest_set['reps'],
            "Date Last Logged": latest_log['Timestamp']
        })
    return pd.DataFrame(pr_rows)

def check_for_pb(session):
    routine = session['Routine']
    session_date = datetime.strptime(session['Timestamp'], "%Y-%m-%d %H:%M")
    past_sessions = [
        w for w in st.session_state.workout_logs 
        if w['Routine'] == routine and datetime.strptime(w['Timestamp'], "%Y-%m-%d %H:%M") < session_date
    ]
    if not past_sessions: return True
    all_past_weights = [s['weight'] for p in past_sessions for s in p['Sets']]
    max_past = max(all_past_weights) if all_past_weights else 0
    current_max = max([s['weight'] for s in session['Sets']])
    return current_max > max_past

def create_massive_dummy_data():
    weight_entries = []
    current_w = 195.0
    start_date = datetime.now() - timedelta(days=730)
    for i in range(100):
        log_dt = start_date + timedelta(days=i * 7.3)
        current_w += random.uniform(-0.8, 0.6)
        weight_entries.append({"UID": 1000 + i, "Timestamp": log_dt.strftime("%Y-%m-%d %H:%M"), 
                               "User": st.session_state.user_name, "Weight": round(current_w, 1), 
                               "Location": "Home", "Notes": "Historical"})
    st.session_state.weight_logs = pd.DataFrame(weight_entries)

    new_workouts = []
    for i in range(1000):
        log_dt = start_date + timedelta(hours=i * 17.5)
        if log_dt > datetime.now(): break
        rt = random.choice(get_routines())
        progression = (i / 1000) * 85
        new_workouts.append({
            "UID": 20000 + i, "Timestamp": log_dt.strftime("%Y-%m-%d %H:%M"),
            "User": st.session_state.user_name, "Routine": rt,
            "Sets": [{"reps": random.randint(5, 10), "weight": float(random.randint(95, 150) + progression)} for _ in range(3)]
        })
    st.session_state.workout_logs = new_workouts
    st.success("Generated 1,100 logs!")

# --- 3. UI TABS ---
tabs = st.tabs(["🏠 Home", "⚖️ Weight", "💪 Log Workout", "📊 Summaries", "📋 Logs", "⚙️ Admin"])
tab_home, tab_weight, tab_workout, tab_summaries, tab_logs, tab_admin = tabs

# --- HOME ---
with tab_home:
    st.title(f"Dashboard: {st.session_state.user_name}")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current Weight")
        if not st.session_state.weight_logs.empty:
            st.metric("Latest", f"{st.session_state.weight_logs.iloc[-1]['Weight']} lbs")
        
        st.divider()
        st.subheader("📅 7 Days Ago")
        target_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_ago = [w for w in st.session_state.workout_logs if target_date in w['Timestamp']]
        if week_ago:
            s = week_ago[0]
            st.markdown(f"**{s['Routine']}** {'🏆 **PB!**' if check_for_pb(s) else ''}")
            for set_item in s['Sets']:
                st.write(f"- {set_item['weight']} lbs x {set_item['reps']}")
        else: st.write("No session found 7 days ago.")

    with col2:
        st.subheader("🕒 Last Session Recap")
        if st.session_state.workout_logs:
            last = sorted(st.session_state.workout_logs, key=lambda x: x['Timestamp'])[-1]
            st.markdown(f"### {last['Routine']} {'🏆 **PB!**' if check_for_pb(last) else ''}")
            for set_item in last['Sets']:
                st.write(f"- {set_item['weight']} lbs x {set_item['reps']}")
            vol = sum([s['weight'] * s['reps'] for s in last['Sets']])
            st.metric("Total Volume", f"{int(vol)} lbs")
        else: st.warning("No workouts logged.")

    st.divider()
    st.subheader("🏆 Personal Records & Latest Hits")
    pr_df = get_pr_table()
    if not pr_df.empty:
        st.dataframe(pr_df, hide_index=True, use_container_width=True)

# --- WEIGHT LOGGING ---
with tab_weight:
    st.header("Body Weight")
    with st.form("weight_entry", clear_on_submit=True):
        cw1, cw2 = st.columns(2)
        w_in = cw1.number_input("Weight (lbs)", step=0.1)
        l_in = cw2.text_input("Location", value="Home")
        if st.form_submit_button("Save Weight"):
            new_row = pd.DataFrame([{"UID": random.randint(100, 9999), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                     "User": st.session_state.user_name, "Weight": w_in, "Location": l_in}])
            st.session_state.weight_logs = pd.concat([st.session_state.weight_logs, new_row], ignore_index=True)
            st.rerun()

    if not st.session_state.weight_logs.empty:
        df_w = st.session_state.weight_logs.copy()
        df_w['Date'] = pd.to_datetime(df_w['Timestamp']).dt.date
        fig_w = go.Figure(go.Scatter(x=df_w['Date'], y=df_w['Weight'], mode='lines+markers', name="Weight", line=dict(color='#00f2ff')))
        fig_w.update_layout(template="plotly_dark" if st.session_state.theme_dark else "plotly_white", height=400)
        st.plotly_chart(fig_w, use_container_width=True)

# --- WORKOUT LOGGING ---
with tab_workout:
    if st.session_state.edit_buffer:
        st.warning(f"Editing Session ID: {st.session_state.edit_buffer['UID']}")
        if st.button("Cancel Edit"):
            st.session_state.edit_buffer = None
            st.rerun()
        init_routine = st.session_state.edit_buffer['Routine']
        init_sets = len(st.session_state.edit_buffer['Sets'])
        init_data = st.session_state.edit_buffer['Sets']
    else:
        init_routine = get_routines()[0] if get_routines() else ""
        init_sets = 3
        init_data = []

    st.header("Training Entry")
    r_choice = st.selectbox("Routine", get_routines(), index=get_routines().index(init_routine) if init_routine in get_routines() else 0)
    n_sets = st.number_input("Number of Sets", min_value=1, max_value=20, value=init_sets)
    
    with st.form("workout_form"):
        sets_data = []
        for i in range(n_sets):
            st.markdown(f"**Set {i+1}**")
            c1, c2 = st.columns(2)
            val_w = init_data[i]['weight'] if i < len(init_data) else 0.0
            val_r = init_data[i]['reps'] if i < len(init_data) else 0
            wt = c1.number_input(f"Weight (lbs)", step=2.5, key=f"wt_{i}", value=float(val_w))
            rp = c2.number_input(f"Reps", step=1, key=f"rp_{i}", value=int(val_r))
            sets_data.append({"weight": wt, "reps": rp})
        
        if st.form_submit_button("Save Session"):
            if st.session_state.edit_buffer:
                for idx, log in enumerate(st.session_state.workout_logs):
                    if log['UID'] == st.session_state.edit_buffer['UID']:
                        st.session_state.workout_logs[idx]['Routine'] = r_choice
                        st.session_state.workout_logs[idx]['Sets'] = sets_data
                st.session_state.edit_buffer = None
            else:
                st.session_state.workout_logs.append({
                    "UID": random.randint(10000, 99999), 
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Routine": r_choice, "Sets": sets_data
                })
            st.success("Session Stored!")
            st.rerun()

# --- SUMMARIES TAB ---
with tab_summaries:
    st.subheader("🏆 Personal Records & Latest Hits")
    pr_df_sum = get_pr_table()
    if not pr_df_sum.empty:
        st.dataframe(pr_df_sum, hide_index=True, use_container_width=True)
    
    st.divider()
    st.header("Visual Strength Trends")
    
    if st.session_state.workout_logs:
        target = st.selectbox("Select Routine to Plot", get_routines())
        p_data = [{"Date": pd.to_datetime(w['Timestamp']), "Max": max([s['weight'] for s in w['Sets']])} 
                  for w in st.session_state.workout_logs if w['Routine'] == target]
        if p_data:
            df_p = pd.DataFrame(p_data).sort_values("Date")
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=df_p['Date'], y=df_p['Max'], mode='markers+lines', name="Max Weight", marker=dict(color='#ff4b4b')))
            if len(df_p) >= 4:
                df_p = df_p.set_index("Date")
                df_p['MA'] = df_p['Max'].rolling(window='30D').mean()
                fig_p.add_trace(go.Scatter(x=df_p.index, y=df_p['MA'], mode='lines', name="30D Moving Avg", line=dict(color='#00f2ff', width=3)))
            fig_p.update_layout(template="plotly_dark" if st.session_state.theme_dark else "plotly_white", height=500)
            st.plotly_chart(fig_p, use_container_width=True)

# --- LOGS TAB ---
with tab_logs:
    st.header("Session Management")
    l_sub1, l_sub2 = st.tabs(["💪 Workout History", "⚖️ Weight History"])
    with l_sub1:
        search = st.text_input("Filter logs by routine...").lower()
        for log in reversed(st.session_state.workout_logs):
            if search in log['Routine'].lower():
                with st.expander(f"{log['Timestamp']} - {log['Routine']}"):
                    for s in log['Sets']:
                        st.write(f"- {s['weight']} lbs x {s['reps']}")
                    c_edit, c_del = st.columns(2)
                    if c_edit.button("Edit", key=f"e_{log['UID']}"):
                        st.session_state.edit_buffer = log
                        st.rerun()
                    if c_del.button("Delete", key=f"d_{log['UID']}", type="primary"):
                        st.session_state.workout_logs = [w for w in st.session_state.workout_logs if w['UID'] != log['UID']]
                        st.rerun()
    with l_sub2:
        if not st.session_state.weight_logs.empty:
            edited_w = st.data_editor(st.session_state.weight_logs, num_rows="dynamic")
            if st.button("Save Weight Edits"):
                st.session_state.weight_logs = edited_w
                st.rerun()

# --- ADMIN TAB ---
with tab_admin:
    st.header("System Controls")
    st.session_state.theme_dark = st.toggle("Dark Mode Aesthetic", value=st.session_state.theme_dark)
    if st.button("🚀 Populate 1100 Records"): create_massive_dummy_data(); st.rerun()
    if st.button("🗑️ Reset Database", type="primary"):
        st.session_state.workout_logs = []; st.session_state.weight_logs = st.session_state.weight_logs.iloc[0:0]
        st.rerun()