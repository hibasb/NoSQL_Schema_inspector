NoSQL Schema Inspector


Automatic schema discovery, interactive visualization, and security auditing for document-oriented NoSQL databases.


NoSQL Schema Inspector is an open-source, web-based tool built with Python and Streamlit. It connects to MongoDB, CouchDB, and Firebase Firestore instances, automatically infers their hidden schemas, visualizes them interactively, and runs a ten-rule security audit engine — all from a single interface.

Features

Schema inference — Automatically detects field names, data types, nesting depth, and presence frequency across all documents in a collection.
Interactive visualization — Renders inferred schemas as hierarchical treemaps using Plotly, with color-coded presence indicators.
Security audit — Scans sampled field values against 10 built-in security rules (plaintext credentials, PII exposure, NoSQL injection patterns, weak hashes, financial data leaks, missing audit trails) and computes a 0–100 security score.
Sensitive data masking — Automatically masks values that trigger security rules during display.
Report export — Downloads audit and schema results in JSON, CSV, and professionally formatted PDF.
AI assistant — Integrated chatbot powered by Groq (LLaMA 3) to help interpret findings and suggest remediation steps.
Multi-backend support — Supports MongoDB, CouchDB, and Firebase Firestore out of the box. Easily extensible to other NoSQL engines via the BaseConnector interface.


Requirements

Python ≥ 3.11
pip or Conda
Compatible with Windows, Linux, and macOS
A running instance of MongoDB, CouchDB, or Firebase Firestore
A Groq API key (for the AI assistant feature)


Installation


1. Clone the repository
bashgit clone https://github.com/hibasb/NoSQL_Schema_inspector.git
cd NoSQL_Schema_inspector
2. Create a virtual environment and install dependencies
bashpython -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
Key dependencies include: streamlit, pymongo, firebase-admin, requests, plotly, reportlab, pandas, groq, python-dotenv.
3. Configure environment variables
bashcp .env.example .env
Open .env and add your Groq API key to enable the AI assistant:
GROQ_API_KEY=your_api_key_here


Usage


Launch the application:
bashstreamlit run app.py
The interface opens automatically in your browser at http://localhost:8501.
Quick start:

Select your database type from the sidebar (MongoDB, CouchDB, or Firebase Firestore)
Enter your connection URI or credentials
Click Connect and analyze
Explore the Schema & Visualization tab for field analysis
Switch to the Security Audit tab to review vulnerabilities and your security score
Download your report in JSON, CSV, or PDF format


Project Structure


NoSQL_Schema_inspector/
│

├── app.py  # Main Streamlit interface and orchestration layer

├── connectors/ # Database connector classes (MongoDB, CouchDB, Firestore)

├── schema_inferrer.py      # Recursive schema inference engine

├── security_auditor.py     # Ten-rule security evaluation engine

├── visualizer.py           # Plotly treemap and gauge chart generation

├── exporter.py             # JSON, CSV, and PDF report generation

├── chatbot.py              # Groq/LLaMA 3 AI assistant widget

├── requirements.txt        # Python dependencies

├── .env.example            # Environment variable template

└── README.md



Screenshots



<img width="727" height="340" alt="image" src="https://github.com/user-attachments/assets/14d81a10-757c-485a-9a4c-34742e8d4373" />


<img width="724" height="342" alt="image" src="https://github.com/user-attachments/assets/ad4c53df-e67d-430f-aaf7-d50b3cce1aac" />


<img width="727" height="343" alt="image" src="https://github.com/user-attachments/assets/57718382-7dea-4b90-8123-add8589d2f29" />




Citation


If you use NoSQL Schema Inspector in your research, please cite:
bibtex@article{hanine2026nosql,
  title     = {NoSQL Schema Inspector: A Semi-Automatic Tool for Discovering,
               Visualizing, and Auditing Document Database Structures},
  author    = {Razzouk Majda ,Chokri, Zahra and Sebban Hiba  },
  journal   = {SoftwareX},
  year      = {2026},
}



Contact


For questions or support, contact: mrazzouk233@gmail.com , zahraechokrii@gmail.com  or zahraechokrii@gmail.com 
National School of Applied Sciences (ENSA), Chouaib Doukkali University, El Jadida, Morocco
