# Face-Attendance System

A high-performance, distributed ecosystem designed to automate student attendance tracking using real-time facial recognition.

## 🏗️ Architecture: Edge-to-Central Strategy

The system is physically decoupled into two specialized services to ensure scalability, data privacy, and network efficiency:

### 1. Central Service (Lightweight Cloud API)
The orchestrator of business logic and data persistence.
* **Core:** FastAPI (Python 3.13) with an asynchronous architecture.
* **Database:** PostgreSQL with the `pgvector` extension for ultra-fast vector similarity searches.
* **Real-time:** WebSockets for instant teacher dashboard updates.
* **Security:** JWT-based authentication for teachers and API-key validation for Edge nodes.
* **Data Flow:** Receives lightweight JSON events (face embeddings) and matches them against the student database.

### 2. Edge Service (Heavyweight Local Node)
Deployed on-site (university campus) to handle high-load computer vision tasks.
* **Computer Vision:** OpenCV for capturing multi-camera RTSP streams.
* **AI Inference:** ONNX Runtime for high-speed face detection and embedding extraction (FaceNet/ArcFace).
* **Task Queue:** RabbitMQ + Celery to process video frames in parallel using Multiprocessing.
* **Privacy First:** Raw video streams never leave the local network. Only 512-dimension face embeddings are transmitted via JSON.

## 🛠️ Technology Stack

| Component            | Technology                                      |
|----------------------|-------------------------------------------------|
| **Backend** | Python 3.13, FastAPI (Asynchronous)            |
| **Database** | PostgreSQL 18 + `pgvector`                      |
| **ORM** | SQLAlchemy 2.0 (psycopg3)                       |
| **AI/CV** | OpenCV, ONNX Runtime                            |
| **Message Broker** | RabbitMQ + Celery                               |
| **Communication** | WebSockets, REST (JSON events)                  |
| **Infrastructure** | Docker Compose, Domain-Driven Design (DDD)      |

## 🚀 Key Features

- **High-Load Ready:** Asynchronous processing and vector-optimized database.
- **Privacy-Centric:** No biometric images are stored or transmitted globally—only mathematical embeddings.
- **Instant Updates:** Teachers see student attendance in real-time through a reactive interface.
- **Edge Computing:** Minimal bandwidth usage by processing heavy video data locally.
