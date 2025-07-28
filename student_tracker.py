import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- Initialize Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Firestore Collections ---
students_ref = db.collection("students")
chat_ref = db.collection("chat")

st.set_page_config(page_title="ScholarSync", layout="wide")
st.title("🎓 ScholarSync - Student Tracker App")

# --- Sidebar: Add or Select Student ---
st.sidebar.header("👤 Student Login / Register")

roll_no = st.sidebar.text_input("Enter Roll Number")
action = st.sidebar.radio("Action", ["View Info", "Register / Update Info"])

# --- Register / Update Student Info ---
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

                students_ref.document(roll_no).set({
                    "name": name,
                    "mail": mail,
                    "course": course,
                    "semester": semester,
                    "subjects": subject_list,
                    "marks": marks_dict,
                    "attendance": attendance,
                    "academic_progress": progress
                })
                st.sidebar.success("✅ Student info saved successfully!")

# --- View Student Info ---
    elif action == "View Info":
        doc = students_ref.document(roll_no).get()
        if doc.exists:
            student = doc.to_dict()
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

# --- Real-Time Chat System with Firestore ---
st.header("💬 Global Student Chat")

with st.form("chat_form", clear_on_submit=True):
    user = st.text_input("Name", value=name)
    message = st.text_area("Message")
    send = st.form_submit_button("Send")

    if send and user and message.strip():
        chat_ref.add({
            "user": user,
            "message": message.strip(),
            "timestamp": firestore.SERVER_TIMESTAMP
        })

# Show latest 100 chat messages (ordered by timestamp)
st.markdown("### 📢 Chat Room")
messages = chat_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
chat_list = list(messages)

if chat_list:
    for msg in reversed(chat_list):
        m = msg.to_dict()
        st.info(f"**{m['user']}**: {m['message']}")
else:
    st.info("No messages yet.")
