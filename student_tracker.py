import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
from datetime import datetime, timedelta
import base64
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import re

# ==================== CONFIGURATION ====================
st.set_page_config(
    page_title="🎓 ScholarSync",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .student-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .chat-message {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stSelectbox > div > div {
        background-color: white;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
    }
    
    .warning-message {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ffeaa7;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FIREBASE INITIALIZATION ====================
@st.cache_resource
def initialize_firebase():
    """Initialize Firebase connection with caching"""
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(dict(st.secrets["FIREBASE"]))
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase initialization failed: {e}")
            st.stop()
    return firestore.client()

db = initialize_firebase()
students_ref = db.collection("students")
chat_ref = db.collection("chat")
analytics_ref = db.collection("analytics")

# ==================== UTILITY FUNCTIONS ====================
class SecurityUtils:
    @staticmethod
    def hash_password(password: str) -> bytes:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    @staticmethod
    def verify_password(password: str, hashed: bytes) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hashed)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class ImageUtils:
    @staticmethod
    def encode_image(file) -> str:
        """Encode uploaded file to base64"""
        if file is None:
            return None
        return base64.b64encode(file.read()).decode('utf-8')
    
    @staticmethod
    def decode_image(b64_string: str) -> bytes:
        """Decode base64 string to bytes"""
        return base64.b64decode(b64_string)

class DataValidator:
    @staticmethod
    def validate_marks(marks_input: str) -> Dict[str, int]:
        """Parse and validate marks input"""
        marks = {}
        if not marks_input.strip():
            return marks
            
        try:
            for item in marks_input.split(','):
                if ':' in item:
                    subject, mark = item.split(':', 1)
                    subject = subject.strip()
                    mark = int(mark.strip())
                    if 0 <= mark <= 100 and subject:
                        marks[subject] = mark
        except ValueError:
            st.error("Invalid marks format. Use 'Subject:Mark' format.")
        return marks
    
    @staticmethod
    def validate_subjects(subjects_input: str) -> List[str]:
        """Parse and validate subjects input"""
        if not subjects_input.strip():
            return []
        return [s.strip() for s in subjects_input.split(",") if s.strip()]

# ==================== DATABASE OPERATIONS ====================
class StudentDB:
    @staticmethod
    def get_student(roll_no: str) -> Optional[Dict]:
        """Get student by roll number"""
        try:
            doc = students_ref.document(roll_no).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            st.error(f"Error fetching student: {e}")
            return None
    
    @staticmethod
    def search_students(query: str) -> List[Dict]:
        """Search students by name or course"""
        results = []
        try:
            # Search by name
            name_results = students_ref.where("name", ">=", query).where("name", "<=", query + "\uf8ff").stream()
            results.extend([r.to_dict() for r in name_results])
            
            # Search by course if no name matches
            if not results:
                course_results = students_ref.where("course", ">=", query).where("course", "<=", query + "\uf8ff").stream()
                results.extend([r.to_dict() for r in course_results])
            
            # Search by roll number
            if not results:
                roll_results = students_ref.where("roll_no", ">=", query).where("roll_no", "<=", query + "\uf8ff").stream()
                results.extend([r.to_dict() for r in roll_results])
                
        except Exception as e:
            st.error(f"Search error: {e}")
        
        return results
    
    @staticmethod
    def get_all_students() -> List[Dict]:
        """Get all students for analytics"""
        try:
            docs = students_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Error fetching students: {e}")
            return []

class ChatDB:
    @staticmethod
    def add_message(user: str, message: str) -> bool:
        """Add message to chat"""
        try:
            chat_ref.add({
                "user": user,
                "message": message.strip(),
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            st.error(f"Error sending message: {e}")
            return False
    
    @staticmethod
    def get_recent_messages(limit: int = 50) -> List[Dict]:
        """Get recent chat messages"""
        try:
            messages = chat_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
            return list(reversed([m.to_dict() for m in messages]))
        except Exception as e:
            st.error(f"Error fetching messages: {e}")
            return []

# ==================== AUTHENTICATION ====================
def render_auth_page():
    """Render authentication page"""
    st.markdown('<div class="main-header"><h1>🎓 ScholarSync</h1><p>Student Management System</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Authentication")
        
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("📧 Email", placeholder="Enter your email")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
                
                if login_btn:
                    if not email or not password:
                        st.error("⚠️ Please fill in all fields")
                    elif not SecurityUtils.validate_email(email):
                        st.error("⚠️ Please enter a valid email address")
                    else:
                        try:
                            doc = students_ref.document(email).get()
                            if doc.exists:
                                data = doc.to_dict()
                                if SecurityUtils.verify_password(password, data.get("password")):
                                    st.session_state.user = email
                                    st.session_state.user_data = data
                                    st.success("✅ Login successful!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect password")
                            else:
                                st.error("❌ User not found. Please register first.")
                        except Exception as e:
                            st.error(f"❌ Login error: {e}")
        
        with tab2:
            with st.form("register_form"):
                reg_email = st.text_input("📧 Email", placeholder="Enter your email")
                reg_password = st.text_input("🔒 Password", type="password", placeholder="Create a password")
                reg_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
                full_name = st.text_input("👤 Full Name", placeholder="Enter your full name")
                role = st.selectbox("👥 Role", ["Student", "Teacher", "Admin"])
                register_btn = st.form_submit_button("📝 Register", use_container_width=True)
                
                if register_btn:
                    if not all([reg_email, reg_password, reg_confirm, full_name]):
                        st.error("⚠️ Please fill in all fields")
                    elif not SecurityUtils.validate_email(reg_email):
                        st.error("⚠️ Please enter a valid email address")
                    elif len(reg_password) < 6:
                        st.error("⚠️ Password must be at least 6 characters")
                    elif reg_password != reg_confirm:
                        st.error("⚠️ Passwords do not match")
                    else:
                        try:
                            doc = students_ref.document(reg_email).get()
                            if doc.exists:
                                st.error("❌ User already exists. Please login.")
                            else:
                                pwd_hash = SecurityUtils.hash_password(reg_password)
                                students_ref.document(reg_email).set({
                                    "password": pwd_hash,
                                    "full_name": full_name,
                                    "role": role,
                                    "created_at": datetime.utcnow(),
                                    "is_active": True
                                })
                                st.success("✅ Registration successful! Please login.")
                        except Exception as e:
                            st.error(f"❌ Registration error: {e}")

# ==================== ANALYTICS DASHBOARD ====================
def render_analytics():
    """Render analytics dashboard"""
    st.markdown("### 📊 Analytics Dashboard")
    
    students = StudentDB.get_all_students()
    if not students:
        st.warning("No student data available for analytics.")
        return
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(students)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card"><h3>👥 Total Students</h3><h2>{}</h2></div>'.format(len(students)), unsafe_allow_html=True)
    
    with col2:
        if 'course' in df.columns:
            unique_courses = df['course'].nunique()
            st.markdown('<div class="metric-card"><h3>📚 Courses</h3><h2>{}</h2></div>'.format(unique_courses), unsafe_allow_html=True)
    
    with col3:
        if 'attendance' in df.columns:
            avg_attendance = df['attendance'].str.rstrip('%').astype(int).mean()
            st.markdown('<div class="metric-card"><h3>📈 Avg Attendance</h3><h2>{:.1f}%</h2></div>'.format(avg_attendance), unsafe_allow_html=True)
    
    with col4:
        if 'academic_progress' in df.columns:
            excellent_count = (df['academic_progress'] == 'Excellent').sum()
            st.markdown('<div class="metric-card"><h3>⭐ Excellent</h3><h2>{}</h2></div>'.format(excellent_count), unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if 'course' in df.columns:
            st.markdown("#### 📊 Students by Course")
            course_counts = df['course'].value_counts()
            fig = px.pie(values=course_counts.values, names=course_counts.index, 
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'academic_progress' in df.columns:
            st.markdown("#### 📈 Academic Progress Distribution")
            progress_counts = df['academic_progress'].value_counts()
            fig = px.bar(x=progress_counts.index, y=progress_counts.values,
                        color=progress_counts.values, color_continuous_scale='viridis')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ==================== STUDENT MANAGEMENT ====================
def render_student_form(action: str, roll_no: str = None, student_data: Dict = None):
    """Render student add/edit form"""
    is_edit = action == "edit" and student_data is not None
    
    st.markdown(f"### {'✏️ Edit Student' if is_edit else '➕ Add New Student'}")
    
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Full Name", value=student_data.get('name', '') if is_edit else '')
            course = st.text_input("📚 Course", value=student_data.get('course', '') if is_edit else '')
            semester = st.number_input("📅 Semester", min_value=1, max_value=8, step=1, 
                                     value=student_data.get('semester', 1) if is_edit else 1)
            if not is_edit:
                roll_no_input = st.text_input("🎫 Roll Number", value=roll_no or '')
        
        with col2:
            subjects = st.text_input("📖 Subjects (comma separated)", 
                                   value=", ".join(student_data.get('subjects', [])) if is_edit else '')
            attendance = st.number_input("📊 Attendance %", min_value=0, max_value=100, step=1,
                                       value=int(student_data.get('attendance', '0').rstrip('%')) if is_edit else 75)
            progress = st.selectbox("📈 Academic Progress", 
                                  ["Excellent", "Good", "Average", "Needs Improvement"],
                                  index=["Excellent", "Good", "Average", "Needs Improvement"].index(
                                      student_data.get('academic_progress', 'Good')) if is_edit else 1)
        
        marks_value = ""
        if is_edit and student_data.get('marks'):
            marks_value = ", ".join([f"{k}:{v}" for k, v in student_data['marks'].items()])
        
        marks_input = st.text_area("📝 Marks (e.g., Math:85, Python:90)", value=marks_value)
        
        profile_pic = st.file_uploader("📷 Profile Picture", type=["jpg", "jpeg", "png"])
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Student", use_container_width=True)
        with col2:
            if is_edit:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                if cancel:
                    st.session_state.edit_mode = False
                    st.rerun()
        
        if submitted:
            # Validation
            if not all([name, course, subjects]):
                st.error("⚠️ Please fill in all required fields")
                return
            
            if not is_edit and not roll_no_input:
                st.error("⚠️ Roll number is required")
                return
            
            # Process data
            subjects_list = DataValidator.validate_subjects(subjects)
            marks_dict = DataValidator.validate_marks(marks_input)
            
            pic_b64 = None
            if profile_pic:
                pic_b64 = ImageUtils.encode_image(profile_pic)
            elif is_edit:
                pic_b64 = student_data.get("profile_pic")
            
            student_doc_data = {
                "name": name,
                "course": course,
                "semester": semester,
                "subjects": subjects_list,
                "attendance": f"{attendance}%",
                "marks": marks_dict,
                "academic_progress": progress,
                "profile_pic": pic_b64,
                "updated_at": datetime.utcnow()
            }
            
            if not is_edit:
                student_doc_data.update({
                    "roll_no": roll_no_input,
                    "created_by": st.session_state.user,
                    "created_at": datetime.utcnow()
                })
            
            try:
                doc_id = roll_no if is_edit else roll_no_input
                
                if is_edit:
                    students_ref.document(doc_id).update(student_doc_data)
                    st.success("✅ Student updated successfully!")
                    st.session_state.edit_mode = False
                else:
                    # Check if student already exists
                    if StudentDB.get_student(doc_id):
                        st.error("❌ Student with this roll number already exists!")
                        return
                    
                    students_ref.document(doc_id).set(student_doc_data)
                    st.success("✅ Student added successfully!")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving student: {e}")

def render_student_details(roll_no: str, student: Dict):
    """Render student details view"""
    st.markdown(f'<div class="student-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if student.get("profile_pic"):
            st.image(ImageUtils.decode_image(student["profile_pic"]), width=150, caption="Profile Picture")
        else:
            st.image("https://via.placeholder.com/150x150/667eea/white?text=No+Photo", width=150)
    
    with col2:
        st.markdown(f"## 👤 {student['name']}")
        st.markdown(f"**🎫 Roll No:** {roll_no}")
        st.markdown(f"**📚 Course:** {student['course']}")
        st.markdown(f"**📅 Semester:** {student['semester']}")
        st.markdown(f"**📊 Attendance:** {student['attendance']}")
        st.markdown(f"**📈 Progress:** {student['academic_progress']}")
    
    with col3:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.edit_mode = True
            st.rerun()
        
        if st.button("🗑️ Delete", use_container_width=True, 
                    help="Delete this student record"):
            if st.button("⚠️ Confirm Delete", type="primary"):
                try:
                    students_ref.document(roll_no).delete()
                    st.success("✅ Student deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error deleting student: {e}")
    
    # Subjects and Marks
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📖 Subjects")
        for subject in student.get('subjects', []):
            st.markdown(f"• {subject}")
    
    with col2:
        st.markdown("#### 📝 Marks")
        marks = student.get('marks', {})
        if marks:
            for subject, mark in marks.items():
                percentage = (mark / 100) * 100
                st.markdown(f"**{subject}:** {mark}/100")
                st.progress(percentage / 100)
        else:
            st.markdown("*No marks recorded*")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== CHAT SYSTEM ====================
def render_chat():
    """Render chat system"""
    st.markdown("### 💬 Global Chat Room")
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            message = st.text_input("💭 Type your message...", placeholder="Share your thoughts...")
        with col2:
            send_btn = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send_btn and message.strip():
            if ChatDB.add_message(st.session_state.user, message):
                st.rerun()
    
    # Display messages
    st.markdown("#### 📨 Recent Messages")
    messages = ChatDB.get_recent_messages(30)
    
    if messages:
        for msg in messages:
            timestamp = msg.get('timestamp')
            time_str = timestamp.strftime('%H:%M:%S') if timestamp else ''
            
            st.markdown(f'''
            <div class="chat-message">
                <strong>👤 {msg['user']}</strong> 
                <span style="color: #666; font-size: 0.8em;">({time_str})</span>
                <br>
                {msg['message']}
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("💬 No messages yet. Be the first to start the conversation!")

# ==================== MAIN APPLICATION ====================
def main():
    """Main application function"""
    
    # Initialize session state
    if "user" not in st.session_state:
        st.session_state.user = None
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    
    # Authentication check
    if st.session_state.user is None:
        render_auth_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f'<div class="sidebar-section"><h3>🎓 ScholarSync</h3><p><strong>Welcome,</strong><br>{st.session_state.user}</p></div>', 
                   unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # Navigation
        page = st.selectbox("📋 Navigate", 
                          ["🏠 Dashboard", "👥 Student Management", "📊 Analytics", "💬 Chat"])
        
        st.markdown("---")
        
        # Search functionality
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("#### 🔍 Quick Search")
        search_query = st.text_input("Search students...", placeholder="Name, course, or roll no.")
        
        if search_query:
            results = StudentDB.search_students(search_query)
            if results:
                st.markdown("**Results:**")
                for student in results[:5]:  # Limit to 5 results
                    st.markdown(f"• **{student.get('name', 'Unknown')}** ({student.get('course', 'N/A')})")
            else:
                st.info("No students found.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    if page == "🏠 Dashboard":
        st.markdown('<div class="main-header"><h1>🎓 ScholarSync Dashboard</h1><p>Student Management System</p></div>', 
                   unsafe_allow_html=True)
        render_analytics()
        
    elif page == "👥 Student Management":
        st.markdown("# 👥 Student Management")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("### 🎛️ Actions")
            roll_no = st.text_input("🎫 Roll Number")
            action = st.selectbox("Choose Action", 
                                ["View Student", "Add New Student", "Edit Student"])
        
        with col2:
            if roll_no:
                student = StudentDB.get_student(roll_no)
                
                if action == "Add New Student":
                    if student:
                        st.warning("⚠️ Student with this roll number already exists!")
                        render_student_details(roll_no, student)
                    else:
                        render_student_form("add", roll_no)
                
                elif action == "View Student":
                    if student:
                        if st.session_state.edit_mode:
                            render_student_form("edit", roll_no, student)
                        else:
                            render_student_details(roll_no, student)
                    else:
                        st.warning("⚠️ Student not found. Use 'Add New Student' to register.")
                
                elif action == "Edit Student":
                    if student:
                        render_student_form("edit", roll_no, student)
                    else:
                        st.warning("⚠️ Student not found.")
            else:
                st.info("👆 Enter a roll number to get started")
    
    elif page == "📊 Analytics":
        st.markdown("# 📊 Analytics Dashboard")
        render_analytics()
        
    elif page == "💬 Chat":
        st.markdown("# 💬 Communication Hub")
        render_chat()

# ==================== APPLICATION ENTRY POINT ====================
if __name__ == "__main__":
    main()

# ==================== FOOTER & CREDITS ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            border-radius: 10px; margin-top: 2rem; color: white;">
    <h4>🎓 ScholarSync - Student Management System</h4>
    <p>Built with ❤️ using Streamlit & Firebase Firestore</p>
    <p style="font-size: 0.8em; opacity: 0.8;">
        © 2024 ScholarSync | Empowering Educational Excellence
    </p>
</div>
""", unsafe_allow_html=True)
