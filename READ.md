# AI Support Copilot

AI Support Copilot is a full-stack AI application that helps businesses automatically answer customer support questions using their own documentation.

The system uses **Retrieval-Augmented Generation (RAG)** to generate answers grounded in uploaded support documents instead of relying only on general AI knowledge.

Users can upload support documents such as policies, FAQs, or product documentation. The system processes these documents, generates embeddings, and stores them in a PostgreSQL database. When a user asks a question, the application retrieves the most relevant document sections and generates an answer using AI.

---

# Features

• Upload support documents (.txt, .md, .pdf)  
• Automatic document chunking  
• AI embedding generation  
• Semantic search using vector similarity  
• AI-generated answers based on uploaded documents  
• Confidence scoring for answers  
• Human review flag for low-confidence responses  
• Modern React frontend  
• FastAPI backend  
• PostgreSQL database  
• Docker-based deployment

---

# Tech Stack

Frontend  
React  
Vite  
JavaScript  

Backend  
FastAPI  
Python  

Database  
PostgreSQL  

AI  
Google Gemini API  

Infrastructure  
Docker  
Docker Compose

---

# How It Works

1. A user uploads support documents through the frontend.
2. The backend processes the document and splits it into smaller chunks.
3. Each chunk is converted into an embedding using an AI model.
4. The embeddings are stored in the PostgreSQL database.
5. When a user asks a question, the question is converted into an embedding.
6. The system performs similarity search to find the most relevant document chunks.
7. The AI model generates an answer using the retrieved context.
8. The system returns the answer along with a confidence score.

---

# Project Structure

```
ai-support-copilot-project
│
├── backend
│   ├── app
│   │   ├── main.py
│   │   ├── ai_service.py
│   │   ├── document_service.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── uploads
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend
│   ├── src
│   │   ├── App.jsx
│   │   ├── api.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── Dockerfile
│
└── docker-compose.yml
```

---

# Running the Project

Clone the repository

```
git clone https://github.com/yourusername/ai-support-copilot.git
cd ai-support-copilot
```

Create an environment file:

```
backend/.env
```

Example configuration:

```
GEMINI_API_KEY=YOUR_API_KEY
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/ai_support_copilot
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:5173
```

Start the application:

```
docker compose up --build
```

Open the application:

Frontend

```
http://localhost:5173
```

Backend API

```
http://localhost:8000
```

---

# Example Use Case

A company uploads documents such as:

• Shipping policy  
• Refund policy  
• Customer FAQ  

Customers can then ask questions like:

"How long does shipping take?"  
"Can I return a final sale item?"  

The system retrieves the relevant documentation and generates an accurate answer.

---

# Resume Description

Developed a full-stack AI customer support assistant using **FastAPI, React, PostgreSQL, and Gemini AI**. Implemented document ingestion, embedding generation, and semantic retrieval to enable **retrieval-augmented generation (RAG)** for answering support questions based on uploaded documentation. Deployed the system using **Docker Compose** with containerized frontend, backend, and database services.

---

# Future Improvements

• Chat history stored in the database  
• Authentication and multi-tenant support  
• Vector database optimization with pgvector  
• Admin dashboard for document management  
• Analytics for frequently asked questions