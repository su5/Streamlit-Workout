import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

# --- 1. DATABASE CORE ---
conn = sqlite3.connect('arena_vault.db', check_same_thread=False)
c = conn.cursor()

def create_tables(force_rebuild=False):
    if force_rebuild:
        c.execute('DROP TABLE IF EXISTS matches')
        c.execute('DROP TABLE IF EXISTS players')
        c.execute('DROP TABLE IF EXISTS games')
    
    c.execute('CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS games (title TEXT PRIMARY KEY)')
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 game TEXT, date TEXT, time TEXT, 
                 winners TEXT, losers TEXT, scores TEXT, notes TEXT)''')
    conn.commit()

def run_bootstrap():
    create_tables(force_rebuild=True)
    demo_players = ["Clay", "Henry", "Thomas", "Monica", "Clarence", "James", 
                    "Papa", "Tassy", "Wes", "Kat", "Ingrid", "Ansel"]
    demo_games = ["Catan", "Magic", "Mario Kart", "Monopoly", "Poker", "Go Fish"]
    for p in demo_players: c.execute("INSERT INTO players VALUES (?)", (p,))
    for g in demo_games: c.execute("INSERT INTO games VALUES (?)", (g,))
    for _ in range(50):
        g = random.choice(demo_games)
        p_s = random.sample(demo_players, 2)
        d = (datetime.now() - timedelta(days=random.randint(0, 20))).strftime("%Y-%m-%d")
        c.execute("INSERT INTO matches (game, date, time, winners, losers) VALUES (?,?,?,?,?)",
                  (g, d, "12:00", p_s[0], p_s[1]))
    conn.commit()

create_tables()

# --- 2. THEME & STYLING ---
if 'theme' not in st.session_state:
    st.session_state.theme = "dark"

t = {
    "dark": {"bg": "#0B0E14", "card": "#1C2128", "text": "#FFFFFF", "accent": "#00FFAA", "sub": "#8B949E", "border": "rgba(255,255,255,0.1)"},
    "light": {"bg": "#F0F2F5", "card": "#FFFFFF", "text": "#1C1E21", "accent": "#007AFF", "sub": "#65676B", "border": "rgba(0,0,0,0.05)"}
}[st.session_state.theme]

st.set_page_config(page_title="Arena Vault", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    
    /* TAB TEXT COLORS */
    button[data-baseweb="tab"] p {{
        color: {t['accent']} !important;
        font-size: 18px !important;
        font-weight: 800 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p {{
        color: #FFFFFF !important;
        text-shadow: 0px 0px 10px {t['accent']};
    }}

    h1, h2, h3, h4 {{ color: {t['accent']} !important; font-weight: 800 !important; }}
    .glass-card {{
        background: {t['card']}; padding: 20px; border-radius: 20px;
        border: 1px solid {t['border']}; margin-bottom: 15px;
    }}
    
    /* OLD STYLE STREAK PILLS */
    .streak-pill {{
        background: rgba(255, 75, 43, 0.1); 
        border: 1px solid #FF4B2B;
        padding: 10px 20px; border-radius: 50px;
        display: inline-block; margin: 5px;
        font-weight: 800; color: #FF4B2B;
    }}

    .session-pill {{
        background: rgba(0, 255, 170, 0.1); border: 1px solid {t['accent']};
        padding: 5px 15px; border-radius: 50px; display: inline-block; margin: 5px; font-size: 0.85rem;
    }}
    .stButton>button {{
        border-radius: 12px; font-weight: 700; background: {t['accent']}; color: black; border: none; width: 100%;
    }}
    .inventory-list {{
        max-height: 200px; overflow-y: auto; background: rgba(0,0,0,0.2); 
        border-radius: 10px; padding: 10px; border: 1px solid {t['border']};
        color: {t['accent']}; font-family: monospace;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ANALYTICS ---
def get_hot_streaks():
    df = pd.read_sql_query("SELECT game, winners, date FROM matches ORDER BY date ASC", conn)
    if df.empty: return []
    streaks = []
    for game in df['game'].unique():
        g_df = df[df['game'] == game]
        curr_p, count = None, 0
        for _, row in g_df.iterrows():
            if row['winners'] == curr_p: count += 1
            else:
                if curr_p and count >= 2: streaks.append({"p": curr_p, "g": game, "c": count})
                curr_p, count = row['winners'], 1
        if curr_p and count >= 2: streaks.append({"p": curr_p, "g": game, "c": count})
    return sorted(streaks, key=lambda x: x['c'], reverse=True)[:5]

def get_session_stats():
    all_m = pd.read_sql_query("SELECT * FROM matches ORDER BY id DESC", conn)
    if all_m.empty: return None, [], {}
    last_m = all_m.iloc[0]
    target_game = last_m['game']
    target_players = set([p.strip() for p in (last_m['winners'] + "," + last_m['losers']).split(",") if p.strip()])
    session_matches = []
    for _, row in all_m.iterrows():
        row_players = set([p.strip() for p in (row['winners'] + "," + row['losers']).split(",") if p.strip()])
        if row['game'] == target_game and row_players == target_players:
            session_matches.append(row)
        else: break
    stats = {p: 0 for p in target_players}
    for m in session_matches:
        for w in m['winners'].split(","):
            w_strip = w.strip()
            if w_strip in stats: stats[w_strip] += 1
    return target_game, sorted(list(target_players)), stats

# --- 4. TABS ---
tabs = st.tabs(["🏠 HOME", "📝 RECORD", "📋 LOG ARCHIVE", "➕ REGISTER", "⚙️ SETTINGS"])

with tabs[0]: # HOME
    st.header("Arena Dashboard")
    
    # OLD STYLE STREAKS (PILLS)
    streaks = get_hot_streaks()
    if streaks:
        st.write("🔥 **CURRENT HOT STREAKS**")
        streak_html = "".join([f'<div class="streak-pill">{s["p"]}: {s["c"]} Wins ({s["g"]})</div>' for s in streaks])
        st.markdown(streak_html, unsafe_allow_html=True)
        st.divider()

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("Leaderboards")
        df_stats = pd.read_sql_query("SELECT game, winners, losers FROM matches", conn)
        if not df_stats.empty:
            for g in sorted(df_stats['game'].unique()):
                with st.expander(f"🏆 {g.upper()}"):
                    players = [r[0] for r in c.execute("SELECT name FROM players").fetchall()]
                    g_m = df_stats[df_stats['game'] == g]
                    res = []
                    for p in players:
                        w = len(g_m[g_m['winners'].str.contains(p, na=False)])
                        l = len(g_m[g_m['losers'].str.contains(p, na=False)])
                        if (w+l) > 0: res.append({"Player": p, "W": w, "L": l, "Win %": f"{(w/(w+l))*100:.0f}%"})
                    st.dataframe(pd.DataFrame(res).sort_values("W", ascending=False), use_container_width=True, hide_index=True)
    with col_r:
        st.subheader("History")
        recent = pd.read_sql_query("SELECT game, winners, date FROM matches ORDER BY id DESC LIMIT 10", conn)
        for _, row in recent.iterrows():
            st.markdown(f'<div class="glass-card"><b>{row["game"]}</b><br><span style="color:{t["accent"]}">Winner: {row["winners"]}</span></div>', unsafe_allow_html=True)

with tabs[1]: # RECORD
    st.header("Match Control")
    s_game, s_players, s_stats = get_session_stats()
    if s_game:
        st.markdown('<div class="glass-card" style="border: 1px solid #00FFAA44;">', unsafe_allow_html=True)
        c_q1, c_q2 = st.columns([2, 1])
        with c_q1: st.subheader(f"⚡ Quick Log: {s_game}")
        with c_q2: st.markdown(" ".join([f'<div class="session-pill"><b>{k}:</b> {v}</div>' for k,v in s_stats.items()]), unsafe_allow_html=True)
        q_cols = st.columns(len(s_players))
        for i, p in enumerate(s_players):
            if q_cols[i].button(p, key=f"ql_{p}"):
                new_l = [pl for pl in s_players if pl != p]
                c.execute("INSERT INTO matches (game, date, time, winners, losers) VALUES (?,?,?,?,?)",
                          (s_game, datetime.now().strftime("%Y-%m-%d"), "Quick", p, ", ".join(new_l)))
                conn.commit(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📝 New Entry")
    all_p = [r[0] for r in c.execute("SELECT name FROM players ORDER BY name").fetchall()]
    all_g = [r[0] for r in c.execute("SELECT title FROM games ORDER BY title").fetchall()]
    c1, c2 = st.columns(2)
    with c1: rg_game = st.selectbox("Game", all_g)
    with c2: rg_date = st.date_input("Date", datetime.now())
    p_in = st.multiselect("Participants", all_p)
    if p_in:
        win, loss = [], []
        for p in p_in:
            if st.checkbox(f"{p} Won", key=f"m_{p}"): win.append(p)
            else: loss.append(p)
        if st.button("LOG MATCH"):
            if win:
                c.execute("INSERT INTO matches (game, date, time, winners, losers) VALUES (?,?,?,?,?)",
                          (rg_game, str(rg_date), "Manual", ", ".join(win), ", ".join(loss)))
                conn.commit(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]: # LOG ARCHIVE
    st.header("Archive")
    logs = pd.read_sql_query("SELECT * FROM matches ORDER BY id DESC", conn)
    edit_id = st.selectbox("Select ID", logs['id'].tolist())
    if edit_id:
        row = logs[logs['id'] == edit_id].iloc[0]
        with st.form("edit"):
            f_win = st.text_input("Winners", row['winners'])
            f_loss = st.text_input("Losers", row['losers'])
            if st.form_submit_button("Save"):
                c.execute("UPDATE matches SET winners=?, losers=? WHERE id=?", (f_win, f_loss, edit_id))
                conn.commit(); st.rerun()
            if st.form_submit_button("🗑️ Delete"):
                c.execute("DELETE FROM matches WHERE id=?", (edit_id,))
                conn.commit(); st.rerun()
    st.dataframe(logs, use_container_width=True, hide_index=True)

with tabs[3]: # REGISTER
    st.header("Expansion")
    cur_p = [r[0] for r in c.execute("SELECT name FROM players ORDER BY name").fetchall()]
    cur_g = [r[0] for r in c.execute("SELECT title FROM games ORDER BY title").fetchall()]
    c1, col2 = st.columns(2)
    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        p_in = st.text_input("Player")
        if p_in and st.button("Add"):
            c.execute("INSERT INTO players VALUES (?)", (p_in.strip(),)); conn.commit(); st.rerun()
        st.markdown(f'<div class="inventory-list">{"<br>".join(cur_p)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        g_in = st.text_input("Game")
        if g_in and st.button("Add Game"):
            c.execute("INSERT INTO games VALUES (?)", (g_in.strip(),)); conn.commit(); st.rerun()
        st.markdown(f'<div class="inventory-list">{"<br>".join(cur_g)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[4]: # SETTINGS
    st.header("System")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"; st.rerun()
    st.divider()
    
    # SAFETY GATE RESET
    if 'show_reset' not in st.session_state: st.session_state.show_reset = False
    if not st.session_state.show_reset:
        if st.button("DEBUG: BOOTSTRAP DATA"):
            st.session_state.show_reset = True
            st.rerun()
    else:
        st.error("⚠️ TOTAL DATA RESET")
        confirm = st.text_input("Type 'DELETE' to confirm reset:")
        c1, c2 = st.columns(2)
        if c1.button("PROCEED"):
            if confirm == "DELETE": run_bootstrap(); st.session_state.show_reset = False; st.rerun()
        if c2.button("CANCEL"):
            st.session_state.show_reset = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)