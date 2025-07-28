import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import hashlib
import re
from typing import Dict, List, Any
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="ScholarSync - Advanced Student Tracker",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .alert-high { background-color: #ffebee; border-left: 4px solid #f44336; }
    .alert-medium { background-color: #fff3e0; border-left: 4px solid #ff9800; }
    .alert-low { background-color: #e8f5e8; border-left: 4px solid #4caf50; }
    .chat-message {
        background: #f0f2f6;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Firebase ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(dict(st.secrets["FIREBASE"]))
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase initialization failed: {e}")
            return None
    return firestore.client()

db = init_firebase()
if not db:
    st.stop()

# --- Database Collections ---
students_ref = db.collection("students")
chat_ref = db.collection("chat")
assignments_ref = db.collection("assignments")
attendance_ref = db.collection("attendance")
grades_ref = db.collection("grades")
announcements_ref = db.collection("announcements")
study_groups_ref = db.collection("study_groups")

# --- Helper Functions ---
def hash_password(password: str) -> str:
    """Hash password for basic security"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_gpa(marks: Dict[str, float]) -> float:
    """Calculate GPA from marks"""
    if not marks:
        return 0.0
    
    grade_points = []
    for mark in marks.values():
        if mark >= 90:
            grade_points.append(4.0)
        elif mark >= 80:
            grade_points.append(3.0)
        elif mark >= 70:
            grade_points.append(2.0)
        elif mark >= 60:
            grade_points.append(1.0)
        else:
            grade_points.append(0.0)
    
    return sum(grade_points) / len(grade_points) if grade_points else 0.0

def get_performance_status(gpa: float) -> tuple:
    """Get performance status and color"""
    if gpa >= 3.5:
        return "Excellent", "green"
    elif gpa >= 3.0:
        return "Good", "blue"
    elif gpa >= 2.0:
        return "Average", "orange"
    else:
        return "Needs Improvement", "red"

def parse_attendance(attendance_str: str) -> float:
    """Parse attendance percentage from string"""
    try:
        return float(attendance_str.replace('%', ''))
    except:
        return 0.0

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'student'

# --- Main Header ---
st.markdown("""
<div class="main-header">
    <h1>🎓 ScholarSync - Advanced Student Management System</h1>
    <p>Comprehensive tracking, analytics, and collaboration platform</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar: Authentication & Navigation ---
with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.header("🔐 Authentication")
    
    if not st.session_state.logged_in:
        auth_tab = st.radio("", ["Login", "Register"])
        
        if auth_tab == "Login":
            with st.form("login_form"):
                roll_no = st.text_input("Roll Number")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login")
                
                if login_btn and roll_no and password:
                    # Verify credentials
                    doc = students_ref.document(roll_no).get()
                    if doc.exists:
                        student_data = doc.to_dict()
                        if student_data.get('password') == hash_password(password):
                            st.session_state.logged_in = True
                            st.session_state.current_user = roll_no
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.error("Student not found")
        
        else:  # Register
            with st.form("register_form"):
                st.subheader("Student Registration")
                roll_no = st.text_input("Roll Number*")
                password = st.text_input("Password*", type="password")
                confirm_password = st.text_input("Confirm Password*", type="password")
                name = st.text_input("Full Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone Number")
                course = st.selectbox("Course*", [
                    "Computer Science", "Electronics", "Mechanical", 
                    "Civil", "Chemical", "Biotechnology", "Mathematics", "Physics"
                ])
                semester = st.selectbox("Semester*", list(range(1, 9)))
                year = st.selectbox("Academic Year", [2024, 2025, 2026, 2027])
                
                register_btn = st.form_submit_button("Register")
                
                if register_btn:
                    if not all([roll_no, password, name, email, course]):
                        st.error("Please fill all required fields")
                    elif password != confirm_password:
                        st.error("Passwords don't match")
                    elif not validate_email(email):
                        st.error("Invalid email format")
                    else:
                        # Check if student already exists
                        doc = students_ref.document(roll_no).get()
                        if doc.exists:
                            st.error("Student with this roll number already exists")
                        else:
                            # Register new student
                            student_data = {
                                "name": name,
                                "email": email,
                                "phone": phone,
                                "course": course,
                                "semester": semester,
                                "year": year,
                                "password": hash_password(password),
                                "registration_date": datetime.now(),
                                "subjects": [],
                                "marks": {},
                                "attendance": "0%",
                                "academic_progress": "New Student",
                                "profile_complete": False
                            }
                            students_ref.document(roll_no).set(student_data)
                            st.success("Registration successful! Please login.")
    
    else:
        st.success(f"Welcome, {st.session_state.current_user}!")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Main App (Only if logged in) ---
if st.session_state.logged_in:
    current_user = st.session_state.current_user
    
    # Get current user data
    user_doc = students_ref.document(current_user).get()
    if not user_doc.exists:
        st.error("User data not found")
        st.stop()
    
    user_data = user_doc.to_dict()
    
    # --- Navigation Tabs ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Dashboard", "👤 Profile", "📝 Assignments", 
        "📈 Analytics", "💬 Chat", "👥 Study Groups", "📢 Announcements"
    ])
    
    # --- TAB 1: Dashboard ---
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics
        gpa = calculate_gpa(user_data.get('marks', {}))
        attendance_pct = parse_attendance(user_data.get('attendance', '0%'))
        total_subjects = len(user_data.get('subjects', []))
        performance, perf_color = get_performance_status(gpa)
        
        with col1:
            st.metric("Current GPA", f"{gpa:.2f}/4.0", delta=None)
        with col2:
            st.metric("Attendance", f"{attendance_pct:.1f}%", 
                     delta="Good" if attendance_pct >= 75 else "Low")
        with col3:
            st.metric("Subjects", total_subjects)
        with col4:
            st.metric("Performance", performance)
        
        # Recent Activity & Alerts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Recent Activity")
            # Mock recent activities
            activities = [
                "✅ Assignment 'Database Design' submitted",
                "📊 Quiz 'Data Structures' - Score: 85%",
                "📝 New assignment posted in 'Web Development'",
                "🎯 Attendance updated for 'Machine Learning'"
            ]
            for activity in activities:
                st.info(activity)
        
        with col2:
            st.subheader("⚠️ Alerts & Reminders")
            alerts = []
            
            if attendance_pct < 75:
                alerts.append(("🔴 Low Attendance", f"Current: {attendance_pct}% (Minimum: 75%)", "high"))
            if gpa < 2.0:
                alerts.append(("🔴 Low GPA", f"Current: {gpa:.2f} (Minimum: 2.0)", "high"))
            
            # Mock upcoming deadlines
            alerts.extend([
                ("🟡 Assignment Due", "Web Development Project - Due in 2 days", "medium"),
                ("🟢 Exam Schedule", "Database Systems - Next Monday", "low")
            ])
            
            for title, message, priority in alerts:
                alert_class = f"alert-{priority}"
                st.markdown(f'<div class="{alert_class}" style="padding: 10px; margin: 5px 0; border-radius: 5px;">'
                           f'<strong>{title}</strong><br>{message}</div>', unsafe_allow_html=True)
    
    # --- TAB 2: Profile Management ---
    with tab2:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 Edit Profile")
            
            with st.form("profile_form"):
                name = st.text_input("Full Name", value=user_data.get('name', ''))
                email = st.text_input("Email", value=user_data.get('email', ''))
                phone = st.text_input("Phone", value=user_data.get('phone', ''))
                course = st.selectbox("Course", [
                    "Computer Science", "Electronics", "Mechanical", 
                    "Civil", "Chemical", "Biotechnology", "Mathematics", "Physics"
                ], index=0 if user_data.get('course') == 'Computer Science' else 0)
                
                semester = st.selectbox("Semester", list(range(1, 9)), 
                                       index=user_data.get('semester', 1) - 1)
                
                subjects_input = st.text_area("Subjects (one per line)", 
                                            value='\n'.join(user_data.get('subjects', [])))
                
                # Marks input with better UI
                st.subheader("📊 Subject Marks")
                marks_data = user_data.get('marks', {})
                subjects_list = [s.strip() for s in subjects_input.split('\n') if s.strip()]
                
                updated_marks = {}
                for subject in subjects_list:
                    updated_marks[subject] = st.number_input(
                        f"{subject} Marks", 
                        min_value=0, max_value=100, 
                        value=int(marks_data.get(subject, 0))
                    )
                
                attendance_input = st.slider("Attendance Percentage", 0, 100, 
                                           int(attendance_pct))
                
                academic_progress = st.selectbox("Academic Progress", [
                    "Excellent", "Good", "Average", "Needs Improvement"
                ], index=0)
                
                if st.form_submit_button("Update Profile"):
                    updated_data = {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "course": course,
                        "semester": semester,
                        "subjects": subjects_list,
                        "marks": updated_marks,
                        "attendance": f"{attendance_input}%",
                        "academic_progress": academic_progress,
                        "profile_complete": True,
                        "last_updated": datetime.now()
                    }
                    
                    students_ref.document(current_user).update(updated_data)
                    st.success("Profile updated successfully!")
                    st.rerun()
        
        with col2:
            st.subheader("📈 Quick Stats")
            
            # GPA Gauge Chart
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = gpa,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "GPA"},
                delta = {'reference': 3.0},
                gauge = {
                    'axis': {'range': [None, 4]},
                    'bar': {'color': perf_color},
                    'steps': [
                        {'range': [0, 2], 'color': "lightgray"},
                        {'range': [2, 3], 'color': "yellow"},
                        {'range': [3, 4], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 3.5
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    # --- TAB 3: Assignment Management ---
    with tab3:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 My Assignments")
            
            # Get assignments for current user
            assignments_query = assignments_ref.where("student_id", "==", current_user).stream()
            assignments_list = []
            
            for assignment in assignments_query:
                assignment_data = assignment.to_dict()
                assignment_data['id'] = assignment.id
                assignments_list.append(assignment_data)
            
            if assignments_list:
                for assignment in assignments_list:
                    status_color = "🟢" if assignment.get('status') == 'completed' else "🔴"
                    st.markdown(f"""
                    **{status_color} {assignment.get('title', 'Untitled')}**
                    - Subject: {assignment.get('subject', 'N/A')}
                    - Due Date: {assignment.get('due_date', 'N/A')}
                    - Status: {assignment.get('status', 'pending').title()}
                    - Description: {assignment.get('description', 'No description')}
                    """)
                    
                    if assignment.get('status') != 'completed':
                        if st.button(f"Mark Complete", key=f"complete_{assignment['id']}"):
                            assignments_ref.document(assignment['id']).update({
                                'status': 'completed',
                                'completion_date': datetime.now()
                            })
                            st.success("Assignment marked as completed!")
                            st.rerun()
                    st.divider()
            else:
                st.info("No assignments found.")
        
        with col2:
            st.subheader("➕ Add New Assignment")
            
            with st.form("assignment_form"):
                title = st.text_input("Assignment Title")
                subject = st.selectbox("Subject", user_data.get('subjects', []))
                description = st.text_area("Description")
                due_date = st.date_input("Due Date")
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
                
                if st.form_submit_button("Add Assignment"):
                    if title and subject:
                        assignment_data = {
                            "student_id": current_user,
                            "title": title,
                            "subject": subject,
                            "description": description,
                            "due_date": due_date.strftime("%Y-%m-%d"),
                            "priority": priority,
                            "status": "pending",
                            "created_date": datetime.now()
                        }
                        assignments_ref.add(assignment_data)
                        st.success("Assignment added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill required fields")
    
    # --- TAB 4: Analytics ---
    with tab4:
        st.subheader("📈 Academic Analytics")
        
        # Subject-wise performance
        if user_data.get('marks'):
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart for marks
                subjects = list(user_data['marks'].keys())
                marks = list(user_data['marks'].values())
                
                fig_bar = px.bar(
                    x=subjects, y=marks,
                    title="Subject-wise Marks",
                    labels={'x': 'Subjects', 'y': 'Marks'},
                    color=marks,
                    color_continuous_scale='viridis'
                )
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Pie chart for grade distribution
                grades = []
                for mark in marks:
                    if mark >= 90:
                        grades.append('A+')
                    elif mark >= 80:
                        grades.append('A')
                    elif mark >= 70:
                        grades.append('B')
                    elif mark >= 60:
                        grades.append('C')
                    else:
                        grades.append('F')
                
                grade_counts = {grade: grades.count(grade) for grade in set(grades)}
                
                fig_pie = px.pie(
                    values=list(grade_counts.values()),
                    names=list(grade_counts.keys()),
                    title="Grade Distribution"
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Progress tracking (mock data)
            st.subheader("📊 Progress Over Time")
            
            # Generate mock progress data
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
            mock_gpa = [gpa + (i/10 - 0.5) for i in range(len(dates))]
            mock_attendance = [attendance_pct + (i*2 - 10) for i in range(len(dates))]
            
            progress_df = pd.DataFrame({
                'Date': dates,
                'GPA': mock_gpa,
                'Attendance': mock_attendance
            })
            
            fig_line = px.line(
                progress_df, x='Date', y=['GPA', 'Attendance'],
                title="Academic Progress Over Time",
                labels={'value': 'Score', 'variable': 'Metric'}
            )
            st.plotly_chart(fig_line, use_container_width=True)
    
    # --- TAB 5: Enhanced Chat System ---
    with tab5:
        st.subheader("💬 Student Chat Room")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Chat messages display
            messages = chat_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
            chat_list = list(messages)
            
            # Create chat container
            chat_container = st.container()
            
            with chat_container:
                if chat_list:
                    for msg in reversed(chat_list):
                        msg_data = msg.to_dict()
                        user = msg_data.get('user', 'Anonymous')
                        message = msg_data.get('message', '')
                        timestamp = msg_data.get('timestamp')
                        
                        # Format timestamp
                        if timestamp:
                            time_str = timestamp.strftime("%H:%M")
                        else:
                            time_str = "Unknown"
                        
                        # Style current user messages differently
                        if user == current_user:
                            st.markdown(f"""
                            <div style="text-align: right; margin: 10px 0;">
                                <div style="background: #e3f2fd; padding: 10px; border-radius: 10px; display: inline-block; max-width: 70%;">
                                    <strong>You</strong> <small>{time_str}</small><br>
                                    {message}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="text-align: left; margin: 10px 0;">
                                <div style="background: #f5f5f5; padding: 10px; border-radius: 10px; display: inline-block; max-width: 70%;">
                                    <strong>{user}</strong> <small>{time_str}</small><br>
                                    {message}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("No messages yet. Start the conversation!")
            
            # Message input
            with st.form("chat_form", clear_on_submit=True):
                message = st.text_area("Type your message...", height=100)
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    send_btn = st.form_submit_button("Send 📤")
                
                if send_btn and message.strip():
                    chat_ref.add({
                        "user": current_user,
                        "user_name": user_data.get('name', current_user),
                        "message": message.strip(),
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.rerun()
        
        with col2:
            st.subheader("👥 Online Users")
            # Mock online users
            online_users = ["Student123", "Alice456", "Bob789", current_user]
            for user in online_users:
                status = "🟢" if user == current_user else "🔵"
                display_name = "You" if user == current_user else user
                st.write(f"{status} {display_name}")
    
    # --- TAB 6: Study Groups ---
    with tab6:
        st.subheader("👥 Study Groups")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display existing study groups
            groups_query = study_groups_ref.stream()
            groups_list = []
            
            for group in groups_query:
                group_data = group.to_dict()
                group_data['id'] = group.id
                groups_list.append(group_data)
            
            if groups_list:
                for group in groups_list:
                    members = group.get('members', [])
                    is_member = current_user in members
                    
                    st.markdown(f"""
                    **📚 {group.get('name', 'Unnamed Group')}**
                    - Subject: {group.get('subject', 'N/A')}
                    - Members: {len(members)} students
                    - Description: {group.get('description', 'No description')}
                    """)
                    
                    col_a, col_b = st.columns([1, 1])
                    with col_a:
                        if not is_member:
                            if st.button(f"Join Group", key=f"join_{group['id']}"):
                                members.append(current_user)
                                study_groups_ref.document(group['id']).update({'members': members})
                                st.success("Joined group successfully!")
                                st.rerun()
                        else:
                            st.success("✅ You're a member")
                    
                    with col_b:
                        if is_member:
                            if st.button(f"Leave Group", key=f"leave_{group['id']}"):
                                members.remove(current_user)
                                study_groups_ref.document(group['id']).update({'members': members})
                                st.info("Left group successfully!")
                                st.rerun()
                    
                    st.divider()
            else:
                st.info("No study groups available. Create one!")
        
        with col2:
            st.subheader("➕ Create Study Group")
            
            with st.form("group_form"):
                group_name = st.text_input("Group Name")
                subject = st.selectbox("Subject", user_data.get('subjects', []))
                description = st.text_area("Description")
                max_members = st.number_input("Max Members", min_value=2, max_value=20, value=5)
                
                if st.form_submit_button("Create Group"):
                    if group_name and subject:
                        group_data = {
                            "name": group_name,
                            "subject": subject,
                            "description": description,
                            "creator": current_user,
                            "members": [current_user],
                            "max_members": max_members,
                            "created_date": datetime.now()
                        }
                        study_groups_ref.add(group_data)
                        st.success("Study group created successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill required fields")
    
    # --- TAB 7: Announcements ---
    with tab7:
        st.subheader("📢 Announcements")
        
        # Display announcements
        announcements_query = announcements_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream()
        announcements_list = list(announcements_query)
        
        if announcements_list:
            for announcement in announcements_list:
                ann_data = announcement.to_dict()
                priority = ann_data.get('priority', 'medium')
                
                if priority == 'high':
                    st.error(f"🔴 **{ann_data.get('title', 'Announcement')}**\n\n{ann_data.get('content', '')}")
                elif priority == 'medium':
                    st.warning(f"🟡 **{ann_data.get('title', 'Announcement')}**\n\n{ann_data.get('content', '')}")
                else:
                    st.info(f"🔵 **{ann_data.get('title', 'Announcement')}**\n\n{ann_data.get('content', '')}")
        else:
            # Add some mock announcements if none exist
            mock_announcements = [
                {
                    "title": "Mid-term Exam Schedule Released",
                    "content": "Mid-term examinations will begin on March 15th. Please check the detailed schedule on the academic portal.",
                    "priority": "high"
                },
                {
                    "title": "Library Hours Extended",
                    "content": "Library will remain open until 10 PM during exam period to accommodate student study needs.",
                    "priority": "medium"
                },
                {
                    "title": "New Study Resources Available",
                    "content": "Additional online resources have been added to the digital library. Access them through your student portal.",
                    "priority": "low"
                }
            ]
            
            for ann in mock_announcements:
                if ann['priority'] == 'high':
                    st.error(f"🔴 **{ann['title']}**\n\n{ann['content']}")
                elif ann['priority'] == 'medium':
                    st.warning(f"🟡 **{ann['title']}**\n\n{ann['content']}")
                else:
                    st.info(f"🔵 **{ann['title']}**\n\n{ann['content']}")

else:
    # Show welcome message for non-logged-in users
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h2>Welcome to ScholarSync! 🎓</h2>
        <p style="font-size: 1.2rem; color: #666;">
            Please login or register using the sidebar to access your personalized student dashboard.
        </p>
        
        <div style="margin: 2rem 0;">
            <h3>🌟 Features</h3>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; margin-top: 2rem;">
                <div style="text-align: center; margin: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; width: 200px;">
                    <h4>📊 Dashboard</h4>
                    <p>Comprehensive overview of your academic progress, GPA, attendance, and alerts</p>
                </div>
                <div style="text-align: center; margin: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; width: 200px;">
                    <h4>📈 Analytics</h4>
                    <p>Detailed charts and graphs showing your performance trends over time</p>
                </div>
                <div style="text-align: center; margin: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; width: 200px;">
                    <h4>📝 Assignments</h4>
                    <p>Track assignments, deadlines, and completion status with priority management</p>
                </div>
                <div style="text-align: center; margin: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; width: 200px;">
                    <h4>💬 Chat System</h4>
                    <p>Real-time communication with classmates and study groups</p>
                </div>
                <div style="text-align: center; margin: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; width: 200px;">
                    <h4>👥 Study Groups</h4>
                    <p>Create and join subject-specific study groups for collaborative learning</p>
                </div>
                <div style="text-align: center; margin: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; width: 200px;">
                    <h4>📢 Announcements</h4>
                    <p>Stay updated with important academic announcements and notifications</p>
                </div>
            </div>
        </div>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; margin: 2rem 0;">
            <h3>🚀 Getting Started</h3>
            <ol style="text-align: left; max-width: 500px; margin: 0 auto;">
                <li><strong>Register:</strong> Create your account with roll number and basic details</li>
                <li><strong>Complete Profile:</strong> Add subjects, current marks, and attendance</li>
                <li><strong>Explore Dashboard:</strong> View your academic metrics and alerts</li>
                <li><strong>Track Progress:</strong> Monitor your GPA and performance analytics</li>
                <li><strong>Connect:</strong> Join study groups and participate in discussions</li>
            </ol>
        </div>
        
        <div style="margin-top: 2rem;">
            <p style="color: #888; font-style: italic;">
                ScholarSync - Empowering students with comprehensive academic tracking and collaboration tools
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<div style="margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px; text-align: center;">
    <p style="margin: 0; color: #666;">
        🎓 ScholarSync v2.0 | Advanced Student Management System<br>
        <small>Built with Streamlit & Firebase | Secure • Scalable • User-Friendly</small>
    </p>
</div>
""", unsafe_allow_html=True)
