import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
from datetime import datetime

# --- Initialize Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()
students_ref = db.collection("students")
chat_ref = db.collection("chat")

# --- Helper functions ---
def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

def verify_password(pw: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed)

# --- Page config ---
st.set_page_config(page_title="Student Tracker", layout="wide")

# --- Authentication ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🔐 Login / Register")
    mode = st.radio("Choose action:", ["Login", "Register"])

    email = st.text_input("Email", key="auth_email")
    password = st.text_input("Password", type="password", key="auth_pw")

    if st.button("Submit", key="auth_submit"):
        if mode == "Register":
            if email and password:
                doc = students_ref.document(email).get()
                if doc.exists:
                    st.error("User already exists. Please login.")
                else:
                    pwd_hash = hash_password(password)
                    students_ref.document(email).set({
                        "password": pwd_hash,
                        "created_at": datetime.utcnow()
                    })
                    st.success("Registration successful! Please login.")
            else:
                st.error("Enter both email and password.")
        else:  # Login
            if email and password:
                doc = students_ref.document(email).get()
                if doc.exists:
                    data = doc.to_dict()
                    if verify_password(password, data.get("password")):
                        st.session_state.user = email
                        st.experimental_rerun()
                    else:
                        st.error("Incorrect password.")
                else:
                    st.error("User not found. Please register.")
            else:
                st.error("Enter both email and password.")
    st.stop()

# --- Main App after login ---
user = st.session_state.user
st.sidebar.title(f"Welcome, {user}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.experimental_rerun()

st.title("📘 Student Tracker App")

# --- Sidebar: Select student by roll number ---
st.sidebar.header("👤 Student Dashboard")
roll_no = st.sidebar.text_input("Roll Number (for student record)")
action = st.sidebar.selectbox("Action", ["View / Update Info", "Add New Student", "Delete Student"])

# --- Common record loader ---
def get_student(rec):
    doc = students_ref.document(rec).get()
    return doc.to_dict() if doc.exists else None

# --- Add / Update / Delete logic ---
if roll_no:
    if action == "Add New Student":
        st.subheader("Register New Student")
        with st.form("add_form"):
            name = st.text_input("Full Name")
            course = st.text_input("Course")
            semester = st.number_input("Semester", min_value=1, max_value=8, step=1)
            subjects = st.text_input("Subjects (comma separated)")
            attendance = st.number_input("Attendance %", min_value=0, max_value=100, step=1)
            marks_input = st.text_area("Marks (e.g., Math:85, Python:90)")
            progress = st.selectbox("Academic Progress", ["Excellent", "Good", "Average", "Needs Improvement"])
            submitted = st.form_submit_button("Save")
            if submitted:
                data = {
                    "name": name,
                    "course": course,
                    "semester": semester,
                    "subjects": [s.strip() for s in subjects.split(",") if s.strip()],
                    "attendance": f"{attendance}%",
                    "marks": {m.split(':')[0].strip(): int(m.split(':')[1]) for m in marks_input.split(',') if ':' in m},
                    "academic_progress": progress,
                    "created_by": user,
                    "created_at": datetime.utcnow()
                }
                students_ref.document(roll_no).set(data)
                st.success("Student added successfully!")

    elif action == "View / Update Info":
        student = get_student(roll_no)
        if student:
            st.subheader(f"Details for {student['name']}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Course:** {student['course']}")
                st.markdown(f"**Semester:** {student['semester']}")
                st.markdown(f"**Attendance:** {student['attendance']}")
                st.markdown(f"**Progress:** {student['academic_progress']}")
            with col2:
                st.markdown("**Subjects:**")
                st.write(", ".join(student['subjects']))
                st.markdown("**Marks:**")
                for sub, mk in student['marks'].items():
                    st.write(f"{sub}: {mk}/100")

            if st.button("Edit Record"):
                with st.form("edit_form"):
                    name = st.text_input("Full Name", value=student['name'])
                    course = st.text_input("Course", value=student['course'])
                    semester = st.number_input("Semester", value=student['semester'], min_value=1, max_value=8)
                    subjects = st.text_input("Subjects", value=", ".join(student['subjects']))
                    attendance = st.number_input("Attendance %", value=int(student['attendance'].strip('%')))
                    marks = ", ".join([f"{k}:{v}" for k, v in student['marks'].items()])
                    marks_input = st.text_area("Marks", value=marks)
                    progress = st.selectbox("Academic Progress", ["Excellent","Good","Average","Needs Improvement"], 
                                            index=["Excellent","Good","Average","Needs Improvement"].index(student['academic_progress']))
                    updated = st.form_submit_button("Update")
                    if updated:
                        students_ref.document(roll_no).update({
                            "name": name,
                            "course": course,
                            "semester": semester,
                            "subjects": [s.strip() for s in subjects.split(",")],
                            "attendance": f"{attendance}%",
                            "marks": {m.split(':')[0].strip(): int(m.split(':')[1]) for m in marks_input.split(',') if ':' in m},
                            "academic_progress": progress,
                            "updated_at": datetime.utcnow()
                        })
                        st.success("Record updated.")
        else:
            st.warning("Student not found. Use 'Add New Student' to register.")

    else:  # Delete
        student = get_student(roll_no)
        if student:
            if st.button("Confirm Delete"):
                students_ref.document(roll_no).delete()
                st.success("Student deleted.")
        else:
            st.warning("Student not found.")

# --- Chat Section ---
st.header("💬 Global Chat Room")
with st.form("chat_form", clear_on_submit=True):
    msg = st.text_area("Message")
    if st.form_submit_button("Send") and msg.strip():
        chat_ref.add({
            "user": user,
            "message": msg.strip(),
            "timestamp": firestore.SERVER_TIMESTAMP
        })

st.markdown("---")
messages = chat_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
for m in reversed(list(messages)):
    data = m.to_dict()
    ts = data.get('timestamp')
    timestr = ts.strftime('%Y-%m-%d %H:%M:%S') if ts else ''
    st.write(f"**{data['user']}** ({timestr}): {data['message']}")

# --- Footer ---
st.markdown("---")
st.caption("Built with ❤️ using Streamlit and Firestore")
