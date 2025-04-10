import streamlit as st
import sqlite3
import pandas as pd
import json
import os

# ✅ First Streamlit command
st.set_page_config(page_title="Video Description", layout="centered")

# 🔐 Set your admin email here
ADMIN_EMAIL = "admin@buffalo.edu"

# ✅ Load tasks
@st.cache_data
def load_video_tasks():
    with open("fullvideo.json", "r") as f:
        return json.load(f)

video_tasks = load_video_tasks()
DB_FILE = "results.db"

# ✅ Ensure the database and table exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            video_id TEXT NOT NULL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 🚀 Run DB initializer once
init_db()

# ✅ Start app
st.title("🎬 Video Description Task")
email = st.text_input("Enter your email:")

if not email:
    st.stop()

# ✅ Admin mode
if email.strip().lower() == ADMIN_EMAIL:
    st.subheader("🛠️ Admin Dashboard")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM annotations ORDER BY timestamp DESC", conn)
    conn.close()
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download All Submissions", csv, "all_annotations.csv", "text/csv")
    st.stop()

# ✅ Student mode
if email not in video_tasks:
    st.warning("No tasks found for this email.")
    st.stop()

st.success(f"Welcome, {email}! You have {len(video_tasks[email])} videos assigned.")

# ✅ Check completed
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("SELECT video_id FROM annotations WHERE email=?", (email,))
completed_ids = [row[0] for row in cursor.fetchall()]
conn.close()

# ✅ Find next video
next_video = None
for item in video_tasks[email]:
    if item["id"] not in completed_ids:
        next_video = item
        break

if next_video:
    st.subheader(f"Video_ID: {next_video['id']}")
    st.components.v1.iframe(next_video["url"], height=360)
    desc = st.text_area("Please provide a detailed description of the motion, with particular focus on the handshape, palm orientation, movement trajectory, and spatial location.", height=100)

    if st.button("Submit"):
        if desc.strip() == "":
            st.warning("Description cannot be empty.")
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO annotations (email, video_id, description) VALUES (?, ?, ?)",
                           (email, next_video["id"], desc.strip()))
            conn.commit()
            conn.close()
            st.success("✅ Submitted!")
            st.rerun()
else:
    st.balloons()
    st.success("🎉 All tasks completed!")

    # Show previous submissions
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""  
        SELECT video_id, description, timestamp
        FROM annotations WHERE email = ?
        ORDER BY timestamp
    """, conn, params=(email,))
    conn.close()

    if not df.empty:
        st.subheader("📝 Your Submissions")
        st.dataframe(df)
    else:
        st.info("No submissions found.")