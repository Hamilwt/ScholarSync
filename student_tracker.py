import streamlit as st
import pickle
import os

DATA_FILE = "student_data.pkl"
CHAT_FILE = "chat_data.pkl"

# --- Load/Save Helpers ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)

def load_chat():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "rb") as f:
            return pickle.load(f)
    return []

def save_chat(chat):
    with open(CHAT_FILE, "wb") as f:
        pickle.dump(chat, f)

# --- Load stored data ---
students = load_data()
chat_messages = load_chat()

st.set_page_config(page_title="Student Tracker", layout="wide")
st.title("📘 Student Tracker App")

# --- Sidebar: Add or Select Student ---
st.sidebar.header("👤 Student Login / Register")

roll_no = st.sidebar.text_input("Enter Roll Number")
action = st.sidebar.radio("Action", ["View Info", "Register / Update Info"])

if roll_no:
    if action == "Register / Update Info":
        with st.sidebar.form("student_form"):
            name = st.text_input("Full Name")
            mail = st.text_input("Email")
            course = st.text_input("Course")
            semester = st.number_input("Semester", min_value=1, max_value=8, step=1)
            subjects = st.text_input("Subjects (comma separated)")
            attendance = st.text_input("Attendance (e.g., 85%)")
            marks_input = st.text_area("Enter marks (e.g., Math:85, Python:90)")
            progress = st.text_input("Academic Progress (e.g., Good, Average)")

            submitted = st.form_submit_button("Save Student Info")

            if submitted:
                subject_list = [s.strip() for s in subjects.split(",") if s.strip()]
                marks_dict = {}
                for m in marks_input.split(","):
                    if ":" in m:
                        sub, mark = m.strip().split(":")
                        marks_dict[sub.strip()] = int(mark.strip())

                students[roll_no] = {
                    "name": name,
                    "mail": mail,
                    "course": course,
                    "semester": semester,
                    "subjects": subject_list,
                    "marks": marks_dict,
                    "attendance": attendance,
                    "academic_progress": progress
                }
                save_data(students)
                st.sidebar.success("Student info saved successfully!")

    elif action == "View Info":
        student = students.get(roll_no)
        if student:
            st.subheader(f"📄 Student Details for {student['name']}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Email:** {student['mail']}")
                st.markdown(f"**Course:** {student['course']}")
                st.markdown(f"**Semester:** {student['semester']}")
                st.markdown(f"**Attendance:** {student['attendance']}")
                st.markdown(f"**Progress:** {student['academic_progress']}")

            with col2:
                st.markdown("**Subjects:**")
                st.write(", ".join(student["subjects"]))
                st.markdown("**Marks:**")
                for subject, mark in student["marks"].items():
                    st.write(f"{subject}: {mark} / 100")
        else:
            st.warning("Student not found. Please register first.")

# --- Real-Time Chat System (Saved Locally) ---
st.header("💬 Global Student Chat")

with st.form("chat_form", clear_on_submit=True):
    user = st.text_input("Name", value=roll_no)
    message = st.text_area("Message")
    send = st.form_submit_button("Send")

    if send and user and message.strip():
        chat_messages.append((user, message.strip()))
        save_chat(chat_messages)

# Show recent messages
st.markdown("### 📢 Chat Room")
if chat_messages:
    for user, msg in reversed(chat_messages[-30:]):
        st.info(f"**{user}**: {msg}")
else:
    st.info("No messages yet.")
