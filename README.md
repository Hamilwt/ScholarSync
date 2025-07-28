# 🎓 ScholarSync (Streamlit + Firebase Firestore)

A web-based **ScholarSync Student Tracker** built using **Streamlit** and **Google Firebase Firestore**.  
This app allows users to **register/view student details** and participate in a **real-time global chat system**.

---

## 🌐 Deployment
The ScholarSync app is deployed and accessible here:  
👉 **[https://your-deployed-link.com](https://your-deployed-link.com)**

---

## 🚀 Features

- **Student Registration & Update**  
  Add or update student details like name, email, course, semester, subjects, attendance, marks, and academic progress.
- **Student Info Viewer**  
  Retrieve and view detailed student information stored in Firestore.
- **Real-time Global Chat System**  
  Students can chat in a shared chat room with real-time updates using Firestore.
- **Firebase Integration**  
  Secure and scalable backend powered by **Google Firebase Firestore**.

---

## 🛠 Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Backend/Database:** [Google Firebase Firestore](https://firebase.google.com/products/firestore)
- **Authentication & Config:** Firebase Admin SDK
- **Language:** Python 3.13

---

## 🔧 Setup & Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/hamilwt/scholarsync.git
cd scholarsync
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Firebase

1. Create a Firebase project in [Firebase Console](https://console.firebase.google.com/).
2. Generate a Service Account Key (JSON) from Project Settings → Service Accounts.
3. Store the credentials securely in Streamlit's `secrets.toml` file:

```toml
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
```

⚠️ **Important:** Never commit your credentials JSON file. Always use Streamlit `secrets.toml`.

### 4️⃣ Run the app

```bash
streamlit run app.py
```

Your app will run locally at: `http://localhost:8501`

---

## ✨ Usage

### 📝 Student Registration / Update
1. Enter Roll Number.
2. Select "Register / Update Info".
3. Fill in the form and click Save.

### 🔍 View Student Info
1. Enter Roll Number.
2. Select "View Info" to see student details.

### 💬 Global Chat
1. Enter your name and message.
2. Click Send to chat in real-time.

---

## 🔒 Security Notes

- Keep Firebase credentials private using Streamlit secrets.
- Use Firestore Security Rules to restrict access (e.g., only authenticated users can update student info).

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m "Added feature"`)
4. Push and create a Pull Request

---

## 📜 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

Developed by [Mohammed Hamil P R]  
📧 Contact: [mohammedhamil100@gmail.com]
