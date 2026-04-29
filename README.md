# 🚀 AI-Powered Job Recommendation Platform

![Status](https://img.shields.io/badge/Status-Completed-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B)
![Groq](https://img.shields.io/badge/AI_Engine-Groq_Llama3-orange)
![Machine Learning](https://img.shields.io/badge/Tech-Machine_Learning-purple)

A next-generation, full-stack recruitment platform that bridges the gap between top talent and employers using advanced Machine Learning and Generative AI. 

Built as a comprehensive 8th-semester university project, this platform moves beyond keyword-matching. It leverages semantic analysis, dynamic salary estimation, and LLM-driven career coaching to provide an unparalleled experience for both candidates and recruiters.

## ✨ Core Features

### 👨‍💼 For Candidates
* **Smart Resume Parsing:** Automatically extracts skills, education, and experience from uploaded resumes.
* **Resume Scorecard & Builder:** Analyzes profile strength and provides actionable feedback to improve ATS visibility.
* **AI Interview Coach:** Generates customized, role-specific interview questions and grades your answers using the Groq API.
* **Auto Cover-Letter Generator:** Drafts hyper-personalized cover letters tailored to specific job descriptions.
* **Market Insights:** Real-time salary estimation and predictive analytics for specific AI and Tech roles.

### 🏢 For Employers
* **Intelligent Candidate Matching:** Uses advanced ML algorithms to rank applicants based on semantic skill alignment, not just exact keywords.
* **Employer Dashboard:** A clean, intuitive CRM for tracking job postings, viewing applicant scorecards, and managing the hiring pipeline.
* **Automated Screening:** Instantly flags candidates missing critical hard skills.

### 🔐 System & Admin
* **Role-Based Access Control (RBAC):** Secure, isolated dashboards for Candidates, Employers, and System Admins.
* **OTP Email Verification:** Robust email validation for secure account registration.
* **Dark/Light Mode Theme Toggle:** A premium, responsive UI that scales perfectly across devices.

## 🗂️ Technical Architecture

* **Frontend:** Streamlit (with custom injected CSS for a modern, glassmorphic UI).
* **AI & LLM:** Groq API (`llama-3.3-70b-versatile`) for natural language generation, chatbot, and interview logic.
* **Data Layer:** Pandas for high-performance, in-memory data manipulation and CSV-based persistent storage.
* **ML Algorithms:** Custom categorization detectors, string distance metrics, and semantic skill matchers.

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* A valid `GROQ_API_KEY`

### Installation

1. Clone this repository:
```bash
git clone https://github.com/Shiva-keerth/ai-job-recommendation-platform.git
cd ai-job-recommendation-platform
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your keys:
```env
GROQ_API_KEY=your_api_key_here
EMAIL_SENDER=your_email@example.com
EMAIL_PASSWORD=your_app_password
```

4. Launch the application:
```bash
streamlit run app.py
```

## 🤝 Contributing
This project is currently maintained by Shiva-keerth. Contributions, issues, and feature requests are welcome.

## 📜 License
Distributed under the MIT License.
