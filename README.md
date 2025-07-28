# 🎓 ScholarSync (Streamlit + Firebase Firestore)

A web-based **ScholarSync Student Tracker** built using **Streamlit** and **Google Firebase Firestore**.  
This app allows users to **register/view student details** and participate in a **real-time global chat system**.

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
- **Language:** Python 3.x

---

🚀 Getting Started

Follow these instructions to get a local copy up and running.

Prerequisites

    Python 3.8 or higher

    A Google Firebase account

1. Clone the Repository

First, clone the project to your local machine.
Bash

git clone https://github.com/Hamilwt/ScholarSync.git
cd ScholarSync

2. Install Dependencies

Install the required Python packages using the requirements.txt file. It's recommended to use a virtual environment.
Bash

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install packages
pip install -r requirements.txt

3. Set up Google Firebase

This application requires a Firebase project to store data.

    Go to the Firebase Console and create a new project.

    In your project dashboard, go to Project Settings > Service accounts.

    Click on "Generate new private key". A JSON file containing your service account credentials will be downloaded. Keep this file safe.

4. Configure Streamlit Secrets

Streamlit uses a secrets.toml file to securely store credentials.

    Create a new folder named .streamlit in the root directory of the project.

    Inside this folder, create a file named secrets.toml.

    Open your downloaded Firebase JSON key and the secrets.toml file. Copy the key-value pairs from the JSON file into the secrets.toml file under a [FIREBASE] heading, like so:
    Ini, TOML

    # .streamlit/secrets.toml

    [FIREBASE]
    type = "service_account"
    project_id = "your-firebase-project-id"
    private_key_id = "your-private-key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
    client_email = "your-firebase-client-email"
    client_id = "your-client-id"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "your-client-cert-url"

    Important: For the private_key value, you must wrap the entire key string in double quotes (") and replace single backslashes (\) with double backslashes (\\) or use a multi-line string as shown above.

🖥️ Running the Application

Once the setup is complete, you can run the Streamlit application with the following command:
Bash

streamlit run student_tracker.py

Navigate to http://localhost:8501 in your web browser to start using ScholarSync!

🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

    Fork the Project

    Create your Feature Branch (git checkout -b feature/AmazingFeature)

    Commit your Changes (git commit -m 'Add some AmazingFeature')

    Push to the Branch (git push origin feature/AmazingFeature)

    Open a Pull Request

📜 License

This project is distributed under the MIT License. See LICENSE for more information.
