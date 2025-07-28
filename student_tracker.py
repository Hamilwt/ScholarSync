import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import pandas as pd
import altair as alt
import io
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="🎓 ScholarSync",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Firebase Initialization ---
def initialize_firebase():
    """Initializes the Firebase Admin SDK if not already initialized."""
    if not firebase_admin._apps:
        try:
            # Get the bucket name from secrets or construct it
            firebase_config = dict(st.secrets["FIREBASE"])
            bucket_name = firebase_config.get("storageBucket")
            if not bucket_name:
                bucket_name = firebase_config["project_id"] + ".appspot.com"
            
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred, {'storageBucket': bucket_name})
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {e}")
            st.stop()
    return firestore.client()

db = initialize_firebase()
users_ref = db.collection("users")
students_ref = db.collection("students")
chat_ref = db.collection("chat")

# --- Session State Management ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = {}
    st.session_state.role = None
    st.session_state.page = "Login"

# --- HELPER & AUTHENTICATION FUNCTIONS ---
def login(email, password):
    """Validates user credentials against Firestore."""
    user_doc = users_ref.document(email).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        # NOTE: In a real app, use hashed passwords (e.g., with bcrypt)
        if user_data.get("password") == password:
            st.session_state.logged_in = True
            st.session_state.user_info = user_data
            st.session_state.role = user_data.get("role")
            st.session_state.email = email
            # Default page after login
            st.session_state.page = "Dashboard" if st.session_state.role == "Admin" else "My Profile"
            st.rerun()
        else:
            st.sidebar.error("Incorrect password.")
    else:
        st.sidebar.error("User not found.")

def logout():
    """Logs the user out and resets session state."""
    st.session_state.logged_in = False
    st.session_state.user_info = {}
    st.session_state.role = None
    st.session_state.email = None
    st.session_state.page = "Login"
    st.sidebar.success("Logged out successfully!")
    st.rerun()

def parse_marks(marks_input):
    """Parses comma-separated marks string into a dictionary."""
    marks_dict = {}
    for m in marks_input.split(","):
        if ":" in m:
            parts = m.strip().split(":", 1)
            sub = parts[0].strip()
            try:
                mark = int(parts[1].strip())
                marks_dict[sub] = mark
            except (ValueError, IndexError):
                continue
    return marks_dict

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🎓 ScholarSync")

if not st.session_state.logged_in:
    st.sidebar.header("👤 Login")
    with st.sidebar.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.form_submit_button("Login"):
            login(email, password)
else:
    st.sidebar.write(f"Welcome, **{st.session_state.user_info.get('name', '')}**!")
    st.sidebar.write(f"Role: **{st.session_state.role}**")
    
    # Navigation for logged-in users
    if st.session_state.role == "Admin":
        st.session_state.page = st.sidebar.radio(
            "Navigation", ["Dashboard", "Student Management", "Chat"],
            key="nav_admin"
        )
    else: # Student Navigation
        st.session_state.page = st.sidebar.radio(
            "Navigation", ["My Profile", "Chat"],
            key="nav_student"
        )

    st.sidebar.button("Logout", on_click=logout, use_container_width=True)


# --- PAGE RENDERING LOGIC ---

# =================================================================
# 1. DASHBOARD PAGE (Admin Only)
# =================================================================
if st.session_state.page == "Dashboard" and st.session_state.role == "Admin":
    st.title("📊 Admin Dashboard")
    st.markdown("Welcome to the central hub for student management.")

    all_students_docs = students_ref.stream()
    all_students = [doc.to_dict() for doc in all_students_docs]

    # --- Key Metrics ---
    total_students = len(all_students)
    total_attendance = 0
    valid_attendance_count = 0
    for student in all_students:
        try:
            attendance_str = student.get('attendance', '0%').replace('%', '')
            total_attendance += float(attendance_str)
            valid_attendance_count += 1
        except (ValueError, TypeError):
            continue
    avg_attendance = (total_attendance / valid_attendance_count) if valid_attendance_count > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Students", value=total_students)
    with col2:
        st.metric(label="Average Attendance", value=f"{avg_attendance:.2f}%")
    st.markdown("---")
    st.header("Quick Access")
    st.info("Use the sidebar navigation to manage students or chat.")

# =================================================================
# 2. MY PROFILE PAGE (Student View)
# =================================================================
elif st.session_state.page == "My Profile" and st.session_state.role == "Student":
    st.title("👤 My Profile")
    email = st.session_state.email
    student_doc = students_ref.document(email).get()
    
    if not student_doc.exists:
        st.warning("Your student profile has not been created yet. Please contact an admin.")
    else:
        student = student_doc.to_dict()
        col1, col2 = st.columns([1, 2])
        
        with col1:
            try:
                bucket = storage.bucket()
                blob = bucket.blob(f"profile_pics/{email}")
                profile_pic_url = blob.generate_signed_url(expiration=datetime.timedelta(minutes=15))
                st.image(profile_pic_url, caption="Profile Picture", width=150)
            except Exception:
                st.image("https://via.placeholder.com/150", caption="No Profile Picture", width=150)

            st.header(student.get('name', 'N/A'))
            st.markdown(f"**Roll No:** {student.get('roll_no', 'N/A')}")
            st.markdown(f"**Email:** {email}")

        with col2:
            st.subheader("Update Your Profile Picture")
            uploaded_file = st.file_uploader("Choose a JPG or PNG file", type=['jpg', 'png'])
            if uploaded_file and st.button("Upload Picture"):
                try:
                    bucket = storage.bucket()
                    blob = bucket.blob(f"profile_pics/{email}")
                    blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
                    st.success("✅ Profile picture updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to upload picture: {e}")

        st.markdown("---")
        tab1, tab2 = st.tabs(["📄 Academic Details", "📈 Performance Chart"])
        with tab1:
            st.subheader("Academic Details")
            st.markdown(f"**Course:** {student.get('course', 'N/A')}")
            st.markdown(f"**Semester:** {student.get('semester', 'N/A')}")
            st.markdown(f"**Attendance:** `{student.get('attendance', 'N/A')}`")
            st.markdown(f"**Academic Progress:** `{student.get('academic_progress', 'N/A')}`")
            with st.expander("View Subjects and Marks"):
                st.write(", ".join(student.get("subjects", [])))
                marks = student.get("marks", {})
                if marks:
                    for subject, mark in marks.items():
                        st.write(f"- {subject}: **{mark} / 100**")
                else:
                    st.info("No marks recorded.")
        with tab2:
            st.subheader("Marks Analysis")
            marks_data = student.get("marks", {})
            if marks_data:
                df_marks = pd.DataFrame(list(marks_data.items()), columns=['Subject', 'Score'])
                chart = alt.Chart(df_marks).mark_bar().encode(
                    x=alt.X('Subject:N', sort=None, title='Subjects'),
                    y=alt.Y('Score:Q', title='Marks Obtained'),
                    tooltip=['Subject', 'Score']
                ).properties(title='Your Marks Distribution')
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No marks available for charting.")

# =================================================================
# 3. STUDENT MANAGEMENT PAGE (Admin Only)
# =================================================================
elif st.session_state.page == "Student Management" and st.session_state.role == "Admin":
    st.title("🎓 Student Management")
    action = st.selectbox("Choose Action", ["View All Students", "Add New Student", "Update Student", "Delete Student"])

    if action == "View All Students":
        st.header("All Registered Students")
        all_students_docs = list(students_ref.stream())
        if not all_students_docs:
            st.info("No students found.")
        else:
            for student_doc in all_students_docs:
                student = student_doc.to_dict()
                with st.expander(f"**{student.get('name', 'N/A')}** (Roll No: {student.get('roll_no', 'N/A')})"):
                    st.markdown(f"**Email:** {student_doc.id}")
                    st.markdown(f"**Course:** {student.get('course', 'N/A')}")
                    st.json(student.get("marks", {}))
    
    elif action == "Add New Student":
        st.header("📝 Add a New Student Record")
        with st.form("add_student_form", clear_on_submit=True):
            email = st.text_input("Student Email (this will be their login ID)")
            password = st.text_input("Temporary Password", type="password")
            roll_no = st.text_input("Roll Number")
            name = st.text_input("Full Name")
            course = st.text_input("Course")
            semester = st.number_input("Semester", min_value=1, max_value=8, step=1)
            subjects = st.text_input("Subjects (comma-separated)")
            attendance = st.text_input("Attendance (e.g., 85%)")
            marks_input = st.text_area("Marks (e.g., Math:85, Python:90)")
            progress = st.selectbox("Academic Progress", ["Excellent", "Good", "Average", "Needs Improvement"])
            if st.form_submit_button("Add Student"):
                if not all([email, password, roll_no, name]):
                    st.error("Email, Password, Roll Number, and Name are required.")
                else:
                    users_ref.document(email).set({"name": name, "password": password, "role": "Student"})
                    students_ref.document(email).set({
                        "roll_no": roll_no, "name": name, "course": course, "semester": semester,
                        "subjects": [s.strip() for s in subjects.split(",")], "marks": parse_marks(marks_input),
                        "attendance": attendance, "academic_progress": progress
                    })
                    st.success(f"✅ Student '{name}' added successfully!")

    elif action == "Update Student":
        st.header("🔄 Update Student Information")
        student_emails = [doc.id for doc in students_ref.stream()]
        email_to_update = st.selectbox("Select Student Email to Update", student_emails)
        if email_to_update:
            student_data = students_ref.document(email_to_update).get().to_dict()
            with st.form("update_student_form"):
                # Pre-populate form with existing data
                roll_no = st.text_input("Roll Number", value=student_data.get("roll_no", ""))
                name = st.text_input("Full Name", value=student_data.get("name", ""))
                # ... populate all other fields ...
                marks_str = ", ".join([f"{k}:{v}" for k, v in student_data.get("marks", {}).items()])
                marks_input = st.text_area("Marks", value=marks_str)
                # ... and so on for all fields ...
                
                if st.form_submit_button("Update Student Info"):
                    updated_data = {
                         "roll_no": roll_no, "name": name, # ... etc
                         "marks": parse_marks(marks_input)
                    } # gather all updated data
                    students_ref.document(email_to_update).update(updated_data)
                    st.success(f"✅ Information for {name} updated!")

    elif action == "Delete Student":
        st.header("🗑️ Delete a Student Record")
        st.warning("⚠️ This action is irreversible.")
        student_emails = [doc.id for doc in students_ref.stream()]
        email_to_delete = st.selectbox("Select Student to Delete", student_emails)
        if email_to_delete:
            student_name = students_ref.document(email_to_delete).get().to_dict().get('name')
            if st.button(f"Confirm Deletion of {student_name}"):
                students_ref.document(email_to_delete).delete()
                users_ref.document(email_to_delete).delete()
                st.success(f"🗑️ Student '{student_name}' deleted.")
                st.rerun()

# =================================================================
# 4. CHAT PAGE (All Logged-in Users)
# =================================================================
elif st.session_state.page == "Chat":
    st.title("💬 Global Student Chat")
    with st.form("chat_form", clear_on_submit=True):
        user_name = st.session_state.user_info.get("name", "Anonymous")
        message = st.text_area("Your Message:", key="chat_message")
        if st.form_submit_button("Send 🚀") and message.strip():
            chat_ref.add({
                "user": user_name, "message": message.strip(), "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("Message sent!")

    st.markdown("---")
    st.header("📢 Chat Room")
    chat_container = st.container(height=400)
    messages_stream = chat_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
    chat_list = list(messages_stream)

    with chat_container:
        if not chat_list:
            st.info("No messages yet. Be the first to say something!")
        else:
            for msg_doc in reversed(chat_list):
                msg = msg_doc.to_dict()
                timestamp = msg.get('timestamp')
                ts_str = timestamp.astimezone().strftime("%b %d, %I:%M %p") if timestamp else "sending..."
                st.markdown(f"<sub>{ts_str}</sub>", unsafe_allow_html=True)
                st.info(f"**{msg.get('user', 'N/A')}**: {msg.get('message', '')}")

# --- Fallback for incorrect state ---
elif st.session_state.logged_in:
    st.title("Welcome!")
    st.info("Please select a page from the sidebar.")
