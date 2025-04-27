import streamlit as st
import sqlite3
import pandas as pd
import json
import os

# First Streamlit command
st.set_page_config(page_title="Video Description", layout="centered")

# Set your admin email here
ADMIN_EMAIL = "admin@buffalo.edu"

# Load tasks
@st.cache_data
def load_video_tasks():
    with open("video_assignment_with_guest.json", "r") as f:
        return json.load(f)

# video_tasks = load_video_tasks()
video_tasks_raw = load_video_tasks()
video_tasks = {k.lower(): v for k, v in video_tasks_raw.items()}
DB_FILE = "results.db"

# Ensure the database and table exist
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

# Run DB initializer once
init_db()

# Display experimental notice
st.markdown("""
### Experimental Considerations

Thank you for participating in this study. This task is part of a research project aimed at understanding how people describe human motion in videos.

**a) Purpose & Data Use**  
Your responses will be used solely for academic research. The collected data will be stored securely and may be shared in anonymized form for future scientific analysis.

**b) Privacy**  
We do **not** collect any personal information such as your name, email address, or IP address.

**c) Anonymity Reminder**  
Please **do not include any identifying information** in your response (e.g., your name or any personally identifiable details).

**d) Voluntary Participation**  
Your participation is completely voluntary. You may choose to stop or opt out at any time without any consequences.
""", unsafe_allow_html=True)


# 示范视频展示 + 教学性说明
st.markdown("""
### Example Video & Expected Description

Below is an example video and a sample description. This will help you understand what kind of details we’re expecting in your response.

""")

#  示例视频 iframe (你可以换成你自己的 Google Drive preview 链接)
example_video_url = "https://drive.google.com/file/d/1Ph9CfExCacct5QiAeR8nyBuPdXP-noln/preview"
st.components.v1.iframe(example_video_url, height=360)

# 示例说明文本
st.markdown("""
Example Description:

     
This is a single-hand motion using the dominant hand in a '4' handshape, with four fingers extended. The palm faces inward, starting near the nose. 
The hand moves slightly outward and away from the face, representing the action of turning attention away. The accompanying facial expression conveys indifference or dismissal.

---
When writing your own description, please focus on:

- **Handshape**: Is this a single-hand or two-hand motion? What shape is the hand forming?
(e.g., “fist”, “flat hands”, “curved hand”, “index finger bent”, “fingers spread apart”, “flat hands with fingers extended and together”, “5-shape with fingers slightly curved”, 
“thumb and pinky extended, other fingers folded”, “thumb touching the tip of the middle finger”, “fists with thumbs extended”, “thumb and index finger touching”, ”Dominant hand in 'V' handshape (index and middle fingers extended and separated); non-dominant hand in flat hand” etc.)

    **The dominant hand** The dominant hand is the one you use most often, while the **non-dominant hand** plays a supporting role during the motion.
- **Palm Orientation**: Which direction is the palm facing?
(e.g., “palm facing upward/downward/outward/inward”, “non-dominant palm facing downward; dominant palm facing side”, “palms facing each other”, “palm facing side”, etc.)
- **Movement Trajectory**: How is the hand moving?
(e.g., “moves upward/downward/outward/backward”, “moves in a circle”, “moves toward and rests on the lips”, “hands wave slightly back and forth”, “hand moves from the chin downward to the chest”, etc.)
- **Location**: Where is the sign happening in space?
(e.g., “in front of the chest”, “near the forehead”, “near the mouth”, “near the side of the head”, “at waist level”, etc.)
- **Others**: What non-manual features are involved?
(e.g., facial expressions- "neutral facial expression", "facial expression conveys nausea or discomfort", etc)

""", unsafe_allow_html=True)


#  Start app
st.title("🎬 Video Description Task")
# email = st.text_input("Enter your email:")
email = st.text_input("Enter your email:").strip().lower()

if not email:
    st.stop()

# Admin mode
if email.strip().lower() == ADMIN_EMAIL:
    st.subheader("Admin Dashboard")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM annotations ORDER BY timestamp DESC", conn)
    conn.close()
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(" Download All Submissions", csv, "all_annotations.csv", "text/csv")
    
    #  新增：删除指定用户的数据
    st.markdown("---")
    st.subheader("🧹 Delete User Data")
    target_email = st.text_input("Enter the email of the user to delete all submissions for:")

    if st.button("Delete This User's Data"):
        if target_email.strip() == "":
            st.warning("Please enter a valid email.")
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM annotations WHERE email = ?", (target_email.strip(),))
            conn.commit()
            conn.close()
            st.success(f"All data for {target_email.strip()} has been deleted.")
            st.rerun()
        
    st.stop()

# Student mode
if email not in video_tasks:
    st.warning("No tasks found for this email.")
    st.stop()

st.success(f"Welcome, {email}! You have {len(video_tasks[email])} videos assigned.")

# Check completed
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("SELECT video_id FROM annotations WHERE email=?", (email,))
completed_ids = [row[0] for row in cursor.fetchall()]
conn.close()

#  Find next video
next_video = None
for item in video_tasks[email]:
    if item["id"] not in completed_ids:
        next_video = item
        break

if next_video:
    st.subheader(f"Video_ID: {next_video['id']}")
    st.components.v1.iframe(next_video["url"], height=360)
    desc = st.text_area("Please provide a detailed description of the motion, " \
    "with particular focus on the handshape, palm orientation, movement trajectory, and spatial location.", height=100, key="description_box", \
    value=st.session_state.get("description_box", ""))
   

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
            st.success("Submitted!")

            if "description_box" in st.session_state:
                del st.session_state["description_box"]

            st.rerun()
else:
    st.balloons()
    st.success("All tasks completed!")

    # Show previous submissions
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""  
        SELECT video_id, description, timestamp
        FROM annotations WHERE email = ?
        ORDER BY timestamp
    """, conn, params=(email,))
    conn.close()

    if not df.empty:
        st.subheader(" Your Submissions")
        st.dataframe(df)
    else:
        st.info("No submissions found.")