import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
from datetime import datetime
import base64
import pandas as pd
import re
import altair as alt

# --- Constants and Configuration ---
PAGE_TITLE = "ScholarSync"
PAGE_ICON = "🎓"
LAYOUT = "wide"
STUDENTS_COLLECTION = "students"
CHAT_COLLECTION = "chat"
ACADEMIC_PROGRESS_LEVELS = ["Excellent", "Good", "Average", "Needs Improvement"]


# --- Firebase Initialization ---
def initialize_firebase():
    """Initializes the Firebase Admin SDK if not already initialized."""
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(dict(st.secrets["FIREBASE"]))
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase initialization failed: {e}")
            st.stop()
    return firestore.client()

db = initialize_firebase()


# --- Helper Functions ---
def hash_password(pw: str) -> bytes:
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

def verify_password(pw: str, hashed_pw: bytes) -> bool:
    """Verifies a password against a stored hash."""
    return bcrypt.checkpw(pw.encode(), hashed_pw)

def encode_image(file):
    """Encodes an uploaded image file to a base64 string."""
    return base64.b64encode(file.read()).decode('utf-8')

def decode_image(b64_string):
    """Decodes a base64 string back to bytes for display."""
    return base64.b64decode(b64_string)

def is_valid_email(email):
    """Simple regex check for email validity."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


# --- Authentication UI ---
def render_authentication():
    """Displays the login/register page and handles authentication logic."""
    # --- EDITED SECTION: Centered Alignment ---
    # Use columns to center the authentication form
    _ , center_col, _ = st.columns([1, 1.5, 1])

    with center_col:
        st.title(f"{PAGE_ICON} ScholarSync - Welcome!")
        st.markdown("Please log in or register to continue.")

        mode = st.radio("Choose action:", ["Login", "Register"], horizontal=True, key="auth_mode")

        with st.form("auth_form"):
            email = st.text_input("Email", key="auth_email")
            password = st.text_input("Password", type="password", key="auth_pw")
            submit_button = st.form_submit_button("Submit", use_container_width=True)

            if submit_button:
                if not email or not password:
                    st.error("⚠️ Please enter both email and password.")
                    return
                if not is_valid_email(email):
                    st.error("⚠️ Please enter a valid email address.")
                    return

                # Using the email as the document ID for the user's auth info
                user_doc_ref = db.collection('users_auth').document(email)
                user_doc = user_doc_ref.get()

                if mode == "Register":
                    if user_doc.exists:
                        st.error("User already exists. Please login.")
                    else:
                        hashed_pw = hash_password(password)
                        user_doc_ref.set({
                            "password": hashed_pw,
                            "created_at": datetime.utcnow()
                        })
                        st.success("✅ Registration successful! Please proceed to login.")
                else:  # Login
                    if user_doc.exists and verify_password(password, user_doc.to_dict().get("password")):
                        st.session_state.user = email
                        st.rerun()
                    else:
                        st.error("❌ Incorrect email or password.")
    st.stop()


# --- Sidebar UI ---
def render_sidebar():
    """Renders the sidebar content for logged-in users."""
    st.sidebar.title(f"{PAGE_ICON} Dashboard")
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}**")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Search Students")
    search_query = st.sidebar.text_input("Search by Name or Course", key="search_query")
    if search_query:
        # Case-insensitive search requires querying a dedicated lowercase field
        query_lower = search_query.lower()
        name_results = db.collection(STUDENTS_COLLECTION).where("name_lower", ">=", query_lower).where("name_lower", "<=", query_lower + '\uf8ff').stream()
        course_results = db.collection(STUDENTS_COLLECTION).where("course_lower", ">=", query_lower).where("course_lower", "<=", query_lower + '\uf8ff').stream()

        results = list(name_results) + list(course_results)
        if results:
            st.sidebar.markdown("##### Results:")
            for r in results:
                s = r.to_dict()
                st.sidebar.info(f"**{s['name']}** ({s['course']}) - Roll: `{r.id}`")
        else:
            st.sidebar.warning("No students found.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Manage Student Records")
    action = st.sidebar.selectbox("Action", ["View / Update Info", "Add New Student", "Delete Student"], key="action_select")
    roll_no = st.sidebar.text_input("Enter Student Roll Number", key="roll_no_input")

    return action, roll_no.strip()


# --- Data Management and Forms ---
def _parse_form_data(name, course, semester, subjects, attendance, marks_input, progress, profile_pic_file, existing_pic=None):
    """Helper to parse and validate data from add/update forms."""
    if not all([name, course, semester, subjects, marks_input]):
        st.error("⚠️ Please fill all required fields.")
        return None

    try:
        marks_dict = {m.split(':')[0].strip(): int(m.split(':')[1].strip()) for m in marks_input.split(',') if ':' in m}
    except (ValueError, IndexError):
        st.error("❌ Invalid format for Marks. Use 'Subject:Score, Subject2:Score2'.")
        return None

    pic_b64 = existing_pic
    if profile_pic_file:
        pic_b64 = encode_image(profile_pic_file)

    return {
        "name": name,
        "course": course,
        "name_lower": name.lower(),
        "course_lower": course.lower(),
        "semester": int(semester),
        "subjects": [s.strip() for s in subjects.split(',') if s.strip()],
        "attendance": f"{int(attendance)}%",
        "marks": marks_dict,
        "academic_progress": progress,
        "profile_pic": pic_b64
    }

def render_student_management(action, roll_no):
    """Handles the UI logic for adding, viewing, updating, and deleting students."""
    st.header(f"🧑‍🎓 {action}")

    if action == "Add New Student":
        with st.form("add_form", clear_on_submit=True):
            # Form fields
            name, course = st.text_input("Full Name"), st.text_input("Course")
            semester = st.number_input("Semester", 1, 8, 1)
            subjects = st.text_input("Subjects (comma separated)", placeholder="e.g., Math, Science, History")
            attendance = st.slider("Attendance %", 0, 100, 75)
            marks_input = st.text_area("Marks", placeholder="e.g., Math:85, Science:92, History:78")
            progress = st.selectbox("Academic Progress", ACADEMIC_PROGRESS_LEVELS)
            profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"])
            submitted = st.form_submit_button("💾 Save New Student")

            if submitted:
                student_data = _parse_form_data(name, course, semester, subjects, attendance, marks_input, progress, profile_pic)
                if student_data:
                    student_data.update({"created_by": st.session_state.user, "created_at": datetime.utcnow()})
                    db.collection(STUDENTS_COLLECTION).document(roll_no).set(student_data)
                    st.success(f"✅ Student '{name}' with Roll No '{roll_no}' added successfully!")

    elif action in ["View / Update Info", "Delete Student"]:
        student_doc = db.collection(STUDENTS_COLLECTION).document(roll_no).get()
        if not student_doc.exists:
            st.warning("⚠️ Student not found. Use 'Add New Student' to register or check the Roll Number.")
            return

        student = student_doc.to_dict()
        st.subheader(f"📄 Details for {student.get('name', 'N/A')} (Roll: {roll_no})")

        if action == "View / Update Info":
            col1, col2 = st.columns([1, 2])
            with col1:
                if student.get("profile_pic"):
                    st.image(decode_image(student["profile_pic"]), caption="Profile Picture", use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150", caption="No Image", use_container_width=True)
            with col2:
                st.markdown(f"**Course:** {student.get('course', 'N/A')}")
                st.markdown(f"**Semester:** {student.get('semester', 'N/A')}")
                st.markdown(f"**Attendance:** {student.get('attendance', 'N/A')}")
                st.markdown(f"**Progress:** {student.get('academic_progress', 'N/A')}")
                st.markdown(f"**Subjects:** {', '.join(student.get('subjects', []))}")
                st.markdown("**Marks:**")
                for sub, mk in student.get('marks', {}).items():
                    st.text(f"- {sub}: {mk}/100")

            with st.expander("✏️ Edit Record"):
                with st.form("edit_form"):
                    name = st.text_input("Full Name", value=student.get('name'))
                    course = st.text_input("Course", value=student.get('course'))
                    semester = st.number_input("Semester", 1, 8, value=student.get('semester'))
                    subjects = st.text_input("Subjects", value=", ".join(student.get('subjects', [])))
                    attendance = st.slider("Attendance %", 0, 100, value=int(student.get('attendance', '0%').strip('%')))
                    marks = ", ".join([f"{k}:{v}" for k, v in student.get('marks', {}).items()])
                    marks_input = st.text_area("Marks", value=marks)
                    progress = st.selectbox("Academic Progress", ACADEMIC_PROGRESS_LEVELS, index=ACADEMIC_PROGRESS_LEVELS.index(student.get('academic_progress', 'Average')))
                    new_pic = st.file_uploader("Update Profile Picture", type=["jpg", "jpeg", "png"])
                    updated = st.form_submit_button("💾 Update Record")

                    if updated:
                        updated_data = _parse_form_data(name, course, semester, subjects, attendance, marks_input, progress, new_pic, student.get("profile_pic"))
                        if updated_data:
                            updated_data["updated_at"] = datetime.utcnow()
                            db.collection(STUDENTS_COLLECTION).document(roll_no).update(updated_data)
                            st.success(f"✅ Record for '{name}' updated.")
                            st.rerun()

        elif action == "Delete Student":
            st.warning(f"**DANGER ZONE**: You are about to delete {student.get('name')}.")
            if st.button("🗑️ Confirm Deletion", type="primary"):
                db.collection(STUDENTS_COLLECTION).document(roll_no).delete()
                st.success(f"✅ Student '{student.get('name')}' has been deleted.")
                st.rerun()


# --- Dashboard UI ---
def render_dashboard():
    """Displays the main dashboard with statistics."""
    st.header("📊 Main Dashboard")
    students_stream = db.collection(STUDENTS_COLLECTION).stream()
    students_list = [doc.to_dict() for doc in students_stream if 'name' in doc.to_dict()]  # Filter out auth-only users

    if not students_list:
        st.info("No student data available yet. Add a student to see dashboard statistics.")
        return

    df = pd.DataFrame(students_list)
    total_students = len(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Students", value=total_students)
    with col2:
        avg_attendance = df['attendance'].str.strip('%').astype(float).mean()
        st.metric(label="Average Attendance", value=f"{avg_attendance:.1f}%")
    with col3:
        avg_semester = df['semester'].mean()
        st.metric(label="Average Semester", value=f"{avg_semester:.1f}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Academic Progress Chart
    with col1:
        st.subheader("Academic Progress Distribution")
        progress_counts = df['academic_progress'].value_counts().reset_index()
        progress_counts.columns = ["Academic Progress", "Count"]

        chart1 = alt.Chart(progress_counts).mark_bar().encode(
            x=alt.X("Academic Progress", sort=None),
            y=alt.Y("Count", scale=alt.Scale(domain=[0, progress_counts["Count"].max() + 1])),
            tooltip=["Academic Progress", "Count"]
        ).properties(height=300)
        st.altair_chart(chart1, use_container_width=True)

    # Students per Course Chart
    with col2:
        st.subheader("Students per Course")
        course_counts = df['course'].value_counts().reset_index()
        course_counts.columns = ["Course", "Count"]

        chart2 = alt.Chart(course_counts).mark_bar().encode(
            x=alt.X("Course", sort=None),
            y=alt.Y("Count", scale=alt.Scale(domain=[0, course_counts["Count"].max() + 1])),
            tooltip=["Course", "Count"]
        ).properties(height=300)
        st.altair_chart(chart2, use_container_width=True)


    # Students per Course Chart
    with col2:
        st.subheader("Students per Course")
        course_counts = df['course'].value_counts().reset_index()
        course_counts.columns = ["Course", "Count"]

        chart2 = alt.Chart(course_counts).mark_bar().encode(
            x=alt.X("Course", sort=None),
            y=alt.Y("Count", scale=alt.Scale(domain=[0, course_counts["Count"].max() + 1])),
            tooltip=["Course", "Count"]
        ).properties(height=300)
        st.altair_chart(chart2, use_container_width=True)


# --- Chat UI ---
def render_chat_room():
    """Displays the global chat room."""
    st.header("💬 Global Chat Room")
    with st.form("chat_form", clear_on_submit=True):
        msg = st.text_area("Your message:", key="chat_message")
        submitted = st.form_submit_button("✉️ Send")
        if submitted and msg.strip():
            chat_ref = db.collection(CHAT_COLLECTION)
            chat_ref.add({
                "user": st.session_state.user,
                "message": msg.strip(),
                "timestamp": firestore.SERVER_TIMESTAMP
            })

    st.markdown("##### Recent Messages")
    messages = db.collection(CHAT_COLLECTION).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20).stream()
    for m in reversed(list(messages)):
        data = m.to_dict()
        ts = data.get('timestamp')
        timestr = ts.strftime('%b %d, %H:%M') if ts else 'sending...'
        st.markdown(f"**`{data['user'].split('@')[0]}`** *({timestr})*: {data['message']}")


# --- Main Application ---
def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)

    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        render_authentication()
    else:
        action, roll_no = render_sidebar()

        if roll_no:
            render_student_management(action, roll_no)
        else:
            render_dashboard()

        st.markdown("---")
        render_chat_room()

        st.markdown("---")
        st.caption("Built with ❤️ using Streamlit & Firebase")

if __name__ == "__main__":
    main()
