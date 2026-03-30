🚀 SmartHire ATS  

Production-Ready Applicant Tracking System (ATS)

\- built with FastAPI for scalable and secure recruitment workflows.



📌 Overview  

SmartHire ATS is a modern backend system designed to streamline hiring processes. 

It provides secure authentication, role-based access control, and structured recruitment workflows suitable for real-world deployment.



✨ Features  



🔐 Authentication \& Security  

\- JWT-based authentication  

\- OAuth2 password flow  

\- Secure protected routes  

\- Middleware-based security \& CORS handling  



👥 Role-Based Access Control  

\- \*\*Admin\*\* – Full system control  

\- \*\*Recruiter\*\* – Manage jobs \& applicants  

\- \*\*Candidate\*\* – Apply for jobs \& track applications  



📊 Core ATS Functionality  

\- Job \& company management  

\- Candidate application tracking  

\- Multi-stage hiring workflows  

\- Campus recruitment support  

\- Advanced filtering \& search  



🛠 Tech Stack  



| Layer           | Technology |

|-----------------|-----------|

| Backend         | FastAPI, Uvicorn |

| Database        | PostgreSQL, SQLAlchemy |

| Authentication  | JWT, OAuth2 |

| Validation      | Pydantic |

| Security        | CORS, Middleware |




⚡ Quick Start  



🔧 Prerequisites  



```bash```



Python 3.11+

PostgreSQL (or SQLite for development)



📥 Installation



git clone https://github.com/dineshkumar-account/smart\_hire\_ats.git

cd smart\_hire\_ats

pip install -r requirements.txt



▶️ Run the Application



\-Development Mode

uvicorn main:app --reload --port 8000



\-Production Mode

uvicorn main:app --host 0.0.0.0 --port 8000



🌐 API Documentation

http://localhost:8000/docs



🔑 Authentication Flow



\-Login

POST /auth/login

{

&#x20; "email": "admin@smarthire.com",

&#x20; "password": "password"

}



\-Access Protected Route

GET /users/me

Authorization: Bearer <JWT\_TOKEN>



📁 Project Structure



smart\_hire\_ats/

│

├── main.py              # Entry point

├── routers/             # API routes

│   ├── auth.py

│   ├── users.py

│   ├── jobs.py

│   └── applications.py

│

├── models/              # SQLAlchemy models

├── schemas/             # Pydantic schemas

├── services/            # Business logic

├── db/                  # Database configuration

└── requirements.txt     # Dependencies





🔌 Frontend Integration

This backend can be integrated with any frontend (Flask/React/etc.) using JWT authentication.



\-Flow:



1. Login → Receive token

2. Store token (localStorage/session)

3. Attach token in headers: Authorization: Bearer <token>

4. Fetch user data via /users/me



🧪 API Examples



\-Login Request



curl -X POST "http://localhost:8000/auth/login" \\

\-H "Content-Type: application/json" \\

\-d '{"email":"user@smarthire.com","password":"pass"}'



\-Protected Endpoint



curl -H "Authorization: Bearer YOUR\_JWT\_TOKEN" \\

http://localhost:8000/users/me



🚀 Deployment



\-Supported platforms: Railway, Render, Heroku.

\-Steps:

1. Connect GitHub repository

2. Set start command: uvicorn main:app --host 0.0.0.0 --port 8000

3. Configure environment variables: DATABASE\_URL=<your\_database\_url>

4. Deploy 🚀



📈 Why This Project?

* Built with modern FastAPI architecture
* Implements production-grade authentication
* Clean and scalable code structure
* Demonstrates real-world backend development skills



👨‍💻 Author


DineshKumar Appadurai

Backend Developer | Coimbatore, Tamil Nadu

B.Sc Information Technology (2025)

🔗 GitHub: https://github.com/dineshkumar-account/smart\_hire\_ats

📡 API Docs: http://localhost:8000/docs















