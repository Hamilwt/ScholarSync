# 📘 Student Tracker App (Streamlit + Firebase Firestore)

A web-based **Student Tracker Application** built using **Streamlit** and **Google Firebase Firestore**.  
This app allows users to **register/view student details** and participate in a **real-time global chat system**.

---

## 🚀 Features
- **Student Registration & Update**  
  - Add or update student details such as name, email, course, semester, subjects, attendance, marks, and academic progress.
  
- **Student Info Viewer**  
  - Retrieve and view detailed student information from Firestore.

- **Real-time Global Chat System**  
  - Students can chat in a shared chat room with real-time updates using Firestore.

- **Firebase Integration**  
  - Secure and scalable backend powered by **Google Firebase Firestore**.

---

## 🛠 Tech Stack
- **Frontend:** [Streamlit](https://streamlit.io/)
- **Backend/Database:** [Google Firebase Firestore](https://firebase.google.com/products/firestore)
- **Authentication & Config:** Firebase Admin SDK
- **Language:** Python 3.x

---

## 📂 Project Structure

📦 student-tracker-app
┣ 📜 app.py # Main Streamlit application
┣ 📜 requirements.txt # Python dependencies
┣ 📜 README.md # Project documentation
┗ 🔑 secrets.toml # Firebase credentials (in .streamlit/secrets.toml)


---

## 🔧 Setup & Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/student-tracker-app.git
cd student-tracker-app

2️⃣ Install dependencies

pip install -r requirements.txt

3️⃣ Configure Firebase

    Create a Firebase project in Firebase Console.

    Generate a Service Account Key (JSON) from Project Settings → Service Accounts.

    Store the credentials securely in Streamlit's secrets.toml file:

# .streamlit/secrets.toml
[FIREBASE]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk@your-project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk"

⚠️ Important: Never commit your credentials JSON file. Always use Streamlit secrets.toml.
4️⃣ Run the app

streamlit run app.py

Your app will run locally at: http://localhost:8501
✨ Usage
📝 Student Registration / Update

    Enter Roll Number → Select "Register / Update Info" → Fill in the form → Click Save.

🔍 View Student Info

    Enter Roll Number → Select "View Info" to see student details.

💬 Global Chat

    Enter a name and message → Click Send → Messages update in real time.

📸 Screenshots

Add screenshots or demo GIFs here to showcase UI.
🔒 Security Notes

    Keep Firebase credentials private using Streamlit secrets.

    Use Firestore Security Rules to restrict access (e.g., only authenticated users can update student info).

🤝 Contributing

Contributions are welcome!

    Fork the repository

    Create a feature branch (git checkout -b feature/your-feature)

    Commit changes (git commit -m "Added feature")

    Push and create a Pull Request

📜 License

This project is licensed under the MIT License.
👨‍💻 Author

Developed by [Your Name]
📧 Contact: [your.email@example.com]
