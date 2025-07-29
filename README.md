# 🎓 ScholarSync

A comprehensive student management system built with Streamlit and Firebase that enables educators to manage student records, track academic progress, and facilitate communication through an integrated chat system.

## 🌐 Deployment
The ScholarSync app is deployed and accessible here:  
👉 **[https://scholarsync.streamlit.app/](https://scholarsync.streamlit.app/)**

## ✨ Features

### 🔐 Authentication System
- **Secure Login/Registration**: User authentication with bcrypt password hashing
- **Email-based Authentication**: Simple email and password authentication system
- **Session Management**: Persistent login sessions during app usage

### 👥 Student Management
- **Complete Student Profiles**: Store comprehensive student information including:
  - Personal details (name, course, semester)
  - Academic records (subjects, marks, attendance)
  - Profile pictures with base64 encoding
  - Academic progress tracking
- **CRUD Operations**: Full Create, Read, Update, Delete functionality
- **Advanced Search**: Search students by name or course with real-time results
- **Data Validation**: Comprehensive input validation and error handling

### 📊 Dashboard & Analytics
- **Real-time Statistics**: 
  - Total student count
  - Average attendance across all students
  - Average semester distribution
- **Visual Analytics**:
  - Academic progress distribution charts
  - Students per course visualization
  - Interactive bar charts using Streamlit's native charting

### 💬 Communication Hub
- **Global Chat Room**: Real-time messaging system for all users
- **Message History**: Persistent chat history with timestamps
- **User Identification**: Messages tagged with sender information

### 🔍 Advanced Features
- **Case-insensitive Search**: Efficient searching with lowercase indexing
- **Image Management**: Profile picture upload and storage
- **Data Export Ready**: Pandas DataFrame integration for potential exports
- **Responsive Design**: Clean, intuitive interface with proper spacing and layout

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Firebase Account and Project

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd scholarsync
   ```

2. **Install required packages**
   ```bash
   pip install streamlit firebase-admin bcrypt pandas
   ```

3. **Set up Firebase**
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
   - Generate a service account key (JSON file)
   - Enable Firestore Database
   - Set up the following collections:
     - `users_auth` - for user authentication
     - `students` - for student records
     - `chat` - for chat messages

4. **Configure Streamlit Secrets**
   
   Create a `.streamlit/secrets.toml` file in your project root:
   ```toml
   [FIREBASE]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "your-private-key-id"
   private_key = "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
   client_email = "your-client-email"
   client_id = "your-client-id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "your-cert-url"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 📚 Usage Guide

### First Time Setup
1. **Register an Account**: Create your educator account using email and password
2. **Login**: Access the dashboard with your credentials
3. **Add Students**: Start by adding student records through the sidebar

### Managing Students

#### Adding a New Student
1. Select "Add New Student" from the sidebar
2. Fill in all required fields:
   - Full Name
   - Course
   - Semester (1-8)
   - Subjects (comma-separated)
   - Attendance percentage
   - Marks (format: Subject:Score, Subject2:Score2)
   - Academic Progress level
   - Profile Picture (optional)
3. Enter a unique Roll Number
4. Click "Save New Student"

#### Viewing/Updating Student Records
1. Select "View / Update Info" from the sidebar
2. Enter the student's Roll Number
3. View complete student profile with image
4. Use the "Edit Record" expander to modify information
5. Save changes with the "Update Record" button

#### Searching Students
- Use the search box in the sidebar
- Search by student name or course
- Results display instantly with roll numbers

### Using the Chat System
1. Navigate to the Global Chat Room section
2. Type your message in the text area
3. Click "Send" to post your message
4. View recent messages from all users with timestamps

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Backend**: Firebase Firestore (NoSQL database)
- **Authentication**: Firebase Authentication + bcrypt
- **Data Processing**: Pandas
- **Image Handling**: Base64 encoding/decoding

### Database Structure

#### Collections:
- **`users_auth`**: User authentication data
  ```json
  {
    "password": "hashed_password",
    "created_at": "timestamp"
  }
  ```

- **`students`**: Student records
  ```json
  {
    "name": "Student Name",
    "name_lower": "student name",
    "course": "Course Name",
    "course_lower": "course name",
    "semester": 3,
    "subjects": ["Math", "Science"],
    "attendance": "85%",
    "marks": {"Math": 85, "Science": 92},
    "academic_progress": "Good",
    "profile_pic": "base64_string",
    "created_by": "user@email.com",
    "created_at": "timestamp"
  }
  ```

- **`chat`**: Chat messages
  ```json
  {
    "user": "user@email.com",
    "message": "Hello everyone!",
    "timestamp": "server_timestamp"
  }
  ```

## 🔧 Configuration

### Academic Progress Levels
The system supports four academic progress levels:
- Excellent
- Good
- Average
- Needs Improvement

### Search Functionality
- Uses lowercase indexing for efficient case-insensitive search
- Supports partial matching with Firebase's range queries
- Searches both student names and course names

## 🚀 Deployment

### Streamlit Cloud
1. Push your code to GitHub
2. Connect your repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add your Firebase secrets in the Streamlit Cloud dashboard
4. Deploy your app

### Local Development
```bash
streamlit run app.py --server.port 8501
```

## 🛡️ Security Features

- **Password Hashing**: Uses bcrypt for secure password storage
- **Input Validation**: Comprehensive validation for all user inputs
- **Email Validation**: Regex-based email format verification
- **Session Management**: Secure session handling with Streamlit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Known Issues

- Profile pictures are stored as base64 strings (consider cloud storage for production)
- Chat messages are limited to last 20 messages
- Search results don't remove duplicates when students match both name and course

## 📞 Support

For support, email your-mohammedhamil100@gmail.com or create an issue in the GitHub repository.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Database powered by [Firebase](https://firebase.google.com/)
- Password security with [bcrypt](https://pypi.org/project/bcrypt/)
- Data analysis with [Pandas](https://pandas.pydata.org/)

---

**Made with ❤️ for educators and students everywhere**
