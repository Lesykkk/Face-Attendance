# <p align="center">Face-Attendance System</p>

<p align="center">
  <img src="central/admin/src/assets/logo.svg" alt="Face-Attendance Logo" width="200"/>
</p>

<p align="center">
  <strong>A high-performance, distributed ecosystem designed to automate student attendance tracking using real-time facial recognition.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python 3.13"/>
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB" alt="React"/>
  <img src="https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="TailwindCSS"/>
  <img src="https://img.shields.io/badge/opencv-%23white.svg?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV"/>
  <img src="https://img.shields.io/badge/ONNX-%23005CED.svg?style=for-the-badge&logo=onnx&logoColor=white" alt="ONNX"/>
</p>

---

## 🏗️ Architecture: Edge-to-Central Strategy

The system is physically decoupled into two specialized services to ensure scalability, data privacy, and network efficiency:

### 1. [Central Service](central/) (Lightweight Cloud API)
The orchestrator of business logic and data persistence.
* **Core:** FastAPI (Python 3.13) with an asynchronous architecture.
* **Database:** PostgreSQL with the `pgvector` extension for ultra-fast vector similarity searches.
* **Data Flow:** Receives lightweight JSON events (face embeddings) and matches them against the student database.

### 2. [Edge Service](edge/) (Heavyweight Local Node)
Deployed on-site (university campus) to handle high-load computer vision tasks.
* **Computer Vision:** OpenCV for capturing multi-camera RTSP streams.
* **AI Inference:** ONNX Runtime for high-speed face detection and embedding extraction.
* **Task Queue:** RabbitMQ + Celery to process video frames in parallel.
* **Privacy First:** Raw video streams never leave the local network. Only face embeddings are transmitted.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python 3.13, FastAPI (Asynchronous) |
| **Frontend** | React, Vite, TailwindCSS |
| **Database** | PostgreSQL 18 + `pgvector` |
| **ORM** | SQLAlchemy 2.0 (psycopg3) |
| **AI/CV** | OpenCV, ONNX Runtime |
| **Message Broker** | RabbitMQ + Celery |
| **Infrastructure** | Docker Compose, DDD |

---

## 🚀 Key Features

*   **⚡ High-Load Ready:** Asynchronous processing and vector-optimized database.
*   **🔒 Privacy-Centric:** No biometric images are stored or transmitted globally—only mathematical embeddings.
*   **📊 Instant Updates:** Teachers see student attendance in real-time through a reactive interface.
*   **🌐 Edge Computing:** Minimal bandwidth usage by processing heavy video data locally.

---

## 🚦 Getting Started

### Prerequisites
* **Docker & Docker Compose**
* **Python 3.13+** (for local development)

### 1️⃣ Central Infrastructure

Setup the core API, database, and admin dashboard:

```bash
cd central
cp .env.example .env
docker compose up --build -d
```

> [!TIP]
> **Admin Dashboard:** Access at [http://localhost:5173](http://localhost:5173)
> **API Docs:** Access at [http://localhost:8000/docs](http://localhost:8000/docs)

### 2️⃣ Edge Node

Setup a local edge node for real-time video processing:

```bash
cd edge
cp .env.example .env
docker compose up --build -d
```

> [!IMPORTANT]
> Ensure `CENTRAL_SERVER_URL` and `EDGE_API_KEY` in the `edge/.env` match your central server configuration.

---

## ⚙️ Configuration (.env)

| Service | Variable | Description |
| :--- | :--- | :--- |
| **Central** | `POSTGRES_*` | Database credentials and connection info |
| **Central** | `SECRET_KEY` | JWT signing key for teacher authentication |
| **Edge** | `CENTRAL_SERVER_URL` | URL of the central API (e.g., `http://localhost:8000`) |
| **Edge** | `EDGE_API_KEY` | Authentication key required for central API access |
| **Edge** | `DETECTION_THRESHOLD` | Sensitivity of the face detection model |
