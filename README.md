# 🔎 OpportunityLens AI

> **Turn opportunity overload into clear, personalized decisions.**

OpportunityLens AI is an AI-powered opportunity analysis and decision-support platform designed for students and early-career applicants.

Instead of manually reading long descriptions for internships, hackathons, fellowships, scholarships, and jobs, users can paste an opportunity description into OpportunityLens AI. The system extracts the important information, evaluates it against the user's profile and preferences, and generates a personalized **Fit Score out of 100** with actionable next steps.

---

## 🚀 Live Demo

**Live Application:**
https://syed-0507-opportunitylens-ai-app-xzabwy.streamlit.app/

**Source Code:**
https://github.com/Syed-0507/OpportunityLens-AI

---

## 🎯 Problem Statement

Students and early-career applicants encounter hundreds of opportunities online, but determining whether an opportunity is actually suitable can be difficult.

Important information is often buried inside lengthy descriptions or scattered across different sections.

Users may overlook:

* Eligibility restrictions
* Registration fees
* Application deadlines
* Required skills
* Location requirements
* Travel and accommodation conditions
* Certificate availability
* Prizes and benefits
* Experience requirements

This can result in wasted time, missed deadlines, and applications to opportunities for which the applicant may not be eligible.

### The problem

> **Finding opportunities is easy. Understanding which opportunities are actually worth applying for is the difficult part.**

OpportunityLens AI addresses this decision-making problem.

---

## 💡 Our Solution

OpportunityLens AI converts an unstructured opportunity description into a structured, personalized analysis.

### User workflow

```text
Opportunity Description
          ↓
     AI Extraction
          ↓
Structured Opportunity Data
          ↓
Profile & Constraint Matching
          ↓
Custom Scoring Engine
          ↓
     Fit Score / 100
          ↓
Analysis + Warnings + Checklist
```

The platform combines **AI-powered information extraction** with a **deterministic Python scoring engine**.

This separation allows the AI to understand the opportunity while the scoring logic applies consistent rules to the user's preferences.

---

## ✨ Key Features

### 🤖 AI-Powered Extraction

Extracts relevant information from natural-language opportunity descriptions.

The system identifies:

* Opportunity title
* Organization
* Opportunity type
* Eligibility
* Deadline
* Registration fee
* Certificate availability
* Location
* Required skills
* Prizes
* Goodies
* Travel support
* Accommodation support
* Application steps
* Red flags
* Missing information

---

### 🎯 Personalized Fit Score

Each opportunity receives a score out of **100** based on multiple factors.

| Category    |  Weight |
| ----------- | ------: |
| Eligibility |      30 |
| Skills      |      20 |
| Cost        |      15 |
| Certificate |      10 |
| Location    |      10 |
| Benefits    |      10 |
| Deadline    |       5 |
| **Total**   | **100** |

The score is calculated using the user's configured preferences rather than relying only on the language model.

---

### 🚨 Hard Eligibility Detection

OpportunityLens AI gives special treatment to explicit eligibility conflicts.

For example:

> "Students and fresh graduates are not eligible."

This is treated differently from an opportunity where eligibility information is simply missing.

The system can identify conflicts involving factors such as:

* Student status
* Professional experience
* Graduation requirements
* Degree restrictions
* Branch restrictions
* Other explicit eligibility conditions

This helps prevent an attractive opportunity from receiving a misleadingly high score when the applicant is clearly ineligible.

---

### 💰 Cost Awareness

The system considers the user's maximum acceptable participation fee.

For the configured student profile:

**Maximum acceptable fee: ₹500**

This allows the scoring engine to distinguish between:

* Free opportunities
* Opportunities within the acceptable fee range
* Opportunities exceeding the user's limit

---

### 📍 Location & Travel Analysis

Location is evaluated based on the user's preferences.

The system distinguishes between:

* Online opportunities
* Opportunities in Hyderabad
* Opportunities outside Hyderabad
* Opportunities that provide travel and accommodation support
* Opportunities where participants must arrange their own travel/accommodation

---

### 📋 Actionable Checklist

Instead of stopping at a summary, OpportunityLens AI generates practical next steps.

Example:

```text
☐ Confirm eligibility
☐ Complete registration
☐ Prepare required project
☐ Submit before deadline
```

This turns analysis into an actionable workflow.

---

### ⚠️ Red Flags & Missing Information

The platform highlights factual issues that may require attention, such as:

* Registration fees
* Eligibility conflicts
* Missing deadlines
* Missing travel information
* Missing accommodation information
* Unclear requirements

It also separates **missing information** from confirmed facts rather than assuming information that was not provided.

---

## 🧠 Example Scoring

The built-in scoring test demonstrates how different opportunities can produce different outcomes.

| Opportunity                               |      Result | Interpretation            |
| ----------------------------------------- | ----------: | ------------------------- |
| Strong student-focused online opportunity | **100/100** | Strong Match              |
| Paid offline opportunity without support  |  **72/100** | Good Match                |
| Opportunity explicitly excluding students |  **20/100** | Hard eligibility conflict |

This demonstrates that OpportunityLens AI does not simply assign a high score to every opportunity.

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │     User Input      │
                    │ Opportunity Text    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Gemini 3.6 Flash │
                    │   AI Extraction     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Structured Pydantic │
                    │       Models        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Python Scoring      │
                    │      Engine         │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌────────────────┐          ┌────────────────┐
        │   Fit Score    │          │   Analysis &   │
        │     / 100      │          │    Checklist   │
        └────────────────┘          └────────────────┘
```

---

## 🛠️ Technology Stack

### Programming Language

* Python

### Application Framework

* Streamlit

### Artificial Intelligence

* Google Gemini API
* Gemini 3.6 Flash
* Google GenAI SDK

### Data Validation

* Pydantic

### Configuration

* python-dotenv
* Streamlit Secrets

### Scoring

* Custom Python rule-based scoring engine

### Version Control

* Git
* GitHub

### Deployment

* Streamlit Community Cloud

---

## 📁 Project Structure

```text
OpportunityLens-AI/
│
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
│
└── .streamlit/
    └── config.toml
```

> API credentials are stored through environment variables / Streamlit Secrets and are not included in the repository.

---

## ⚙️ Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/Syed-0507/OpportunityLens-AI.git
cd OpportunityLens-AI
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Gemini API key

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

### 4. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

---

## 🔐 Security

API credentials are not stored directly in the source code.

The project uses:

* `.env` for local development
* Streamlit Secrets for cloud deployment
* `.gitignore` to prevent secret files from being committed

---

## 👤 Personalized Student Profile

The current application is configured around a student profile with preferences such as:

* Final-year Computer Science student
* Python, Java, C
* AI and Web Development
* Maximum acceptable fee: ₹500
* Certificate preferred
* Goodies preferred
* Online opportunities preferred
* Hyderabad preferred
* Travel/accommodation support required for eligible opportunities outside the preferred city

The architecture can be extended to allow users to configure their own profiles.

---

## 🔮 Future Scope

Potential future improvements include:

* User accounts and customizable profiles
* Opportunity bookmarking
* Application deadline reminders
* Opportunity history and tracking
* Automated opportunity discovery
* Resume-to-opportunity matching
* Personalized skill-gap analysis
* Email or notification reminders
* Multi-opportunity comparison
* Support for additional opportunity sources
* More configurable scoring preferences

---

## 🏆 Hackathon Goal

OpportunityLens AI is designed around a simple idea:

> **Don't just find opportunities. Understand whether they are actually worth pursuing.**

By combining AI extraction with transparent rule-based personalization, OpportunityLens AI helps students move from **information overload** to **clear, actionable decisions**.

---

## 👨‍💻 Project

**OpportunityLens AI**

**GitHub:**
https://github.com/Syed-0507/OpportunityLens-AI

**Live Demo:**
https://syed-0507-opportunitylens-ai-app-xzabwy.streamlit.app/

---

## 📜 License

This project was created as a hackathon project.
