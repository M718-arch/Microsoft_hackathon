# 🍽️ Franco-Arabic ABSA (Aspect-Based Sentiment Analysis)

A production-ready AI application for analyzing restaurant reviews in **Arabic, Franco-Arabic (Arabizi), and Egyptian Arabic** using Aspect-Based Sentiment Analysis (ABSA).

## 📖 Overview

### What is Franco-Arabic ABSA?

Franco-Arabic ABSA is an intelligent sentiment analysis system designed specifically for the Egyptian market, where customers often write reviews in **Franco-Arabic (Arabizi)** — a hybrid of Arabic written using Latin characters and numbers.

**Example:** `"el akl gamed"` → "الأكل جامد" → "The food is great"

The application combines state-of-the-art Natural Language Processing (NLP) with a modern, user-friendly interface to help businesses understand customer feedback at a granular level. By identifying both **what** customers are talking about (aspects) and **how** they feel about it (sentiment), businesses can make data-driven decisions to improve their services.

### Why Aspect-Based Sentiment Analysis?

Traditional sentiment analysis only tells you if a review is positive or negative. **Aspect-Based Sentiment Analysis (ABSA)** goes deeper by identifying:

| Traditional Sentiment | Aspect-Based Sentiment |
|----------------------|----------------------|
| "The food was great but service was slow." → **Positive** | Food → Positive ✅<br>Service → Negative ❌ |

This provides actionable insights:

- ✅ **Food** → Positive → Keep the menu
- ❌ **Service** → Negative → Train staff
- 😐 **Price** → Neutral → Review pricing strategy
---

## 🎯 Supported Aspects

| Aspect                | Description                                      |
| --------------------- | ------------------------------------------------ |
| 🍽️ **Food**          | Food quality, taste, and overall food experience |
| 🤝 **Service**        | Restaurant and customer service                  |
| 💰 **Price**          | Price, cost, and value                           |
| 🧹 **Cleanliness**    | Restaurant cleanliness and hygiene               |
| 🚚 **Delivery**       | Delivery experience                              |
| ✨ **Ambiance**        | Restaurant atmosphere and environment            |
| 📱 **App Experience** | Restaurant application experience                |
| 💬 **General**        | General restaurant feedback                      |

---

## 🖼️ Application Examples

The application provides an interactive interface for analyzing restaurant reviews, translating Franco-Arabic text, and processing multiple reviews at once.

### 🔍 1. Restaurant Review Analyzer

Analyze individual restaurant reviews and detect their aspects and sentiment.

![Restaurant Review Analyzer](https://raw.githubusercontent.com/M718-arch/Microsoft_hackathon/4d57f05d770b47b5a53ee648a9fe90a6775daf89/Restaurant%20Review%20Analyzer.png)

**How it works:**

1. User enters a review (Arabic, Franco-Arabic, or mixed)
2. Optionally adds a star rating
3. AI analyzes the text
4. Results show:
   - Detected aspects (e.g., Food, Service)
   - Sentiment for each aspect (Positive/Neutral/Negative)
   - 3D animated face reflecting overall sentiment

---

### 🔄 2. Franco-Arabic Translator

Convert Franco-Arabic (Arabizi) expressions into Arabic using the built-in translator.

![Franco-Arabic Translator](https://raw.githubusercontent.com/M718-arch/Microsoft_hackathon/4d57f05d770b47b5a53ee648a9fe90a6775daf89/Franco-Arabic%20Translator.png)

**Features:**

- Two-panel design: Franco-Arabic input → Arabic output
- Common phrases for quick testing
- Copy translation to clipboard
- Real-time translation

**Example translations:**

| Franco-Arabic | Arabic | English |
|---------------|--------|---------|
| `ana 3ayez akl` | انا عايز اكل | I want food |
| `shukran 7abibi` | شكرا حبيبي | Thank you |
| `el 5idma 7elwa` | الخدمة حلوة | Good service |

---

### 📁 3. Batch Upload

Upload multiple restaurant reviews using `.txt`, `.csv`, or `.xlsx` files and analyze them together.

![Batch Upload](https://raw.githubusercontent.com/M718-arch/Microsoft_hackathon/4d57f05d770b47b5a53ee648a9fe90a6775daf89/Batch%20Upload.png)

**Supported file formats:**

- `.txt` — One review per line
- `.csv` — Reviews in a column
- `.xlsx` — Reviews in a column

**Results include:**

- Total reviews processed
- Sentiment distribution (Positive/Neutral/Negative)
- Aspect detection breakdown
- Individual review previews

---

## 🏗️ Tech Stack

### 💻 Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI Framework |
| TypeScript | 5.2.2 | Type Safety |
| Vite | 4.4.11 | Build Tool |
| Tailwind CSS | 3.3.5 | Styling |
| Framer Motion | 10.16.4 | Animations |
| Lucide React | 0.292.0 | Icons |
| Axios | 1.6.2 | API Client |
| React Hot Toast | 2.4.1 | Notifications |

### 🐍 Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Runtime |
| FastAPI | 0.104.1 | Web Framework |
| PyTorch | 2.1.0 | Deep Learning |
| Transformers | 4.40.0 | NLP Models |
| XLM-RoBERTa-base | - | Multilingual Model |
| Pandas | 2.2.2 | Data Processing |
| Uvicorn | 0.24.0 | ASGI Server |

---

## 📁 Project Structure

```text
Microsoft_hackathon/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI server with Arabizi detection
│   ├── requirements.txt         # Python dependencies
│   └── run.py                   # Server runner
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BatchUpload.tsx      # Bulk file upload
│   │   │   ├── ReviewInput.tsx      # Review text input
│   │   │   ├── SentimentScale.tsx   # 3D sentiment faces
│   │   │   ├── Translator.tsx       # Franco-Arabic translator
│   │   │   ├── Sidebar/             # Navigation sidebar
│   │   │   └── CategoryCard/        # Aspect display
│   │   ├── styles/
│   │   │   ├── globals.css          # Global styles
│   │   │   ├── layout.css           # Layout styles
│   │   │   ├── batch.css            # Batch upload styles
│   │   │   └── translator.css       # Translator styles
│   │   ├── services/
│   │   │   └── api.ts               # API client
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript types
│   │   └── App.tsx                  # Main application
│   ├── public/
│   │   ├── restaurant.png           # Background image
│   │   ├── food.png                 # Food aspect icon
│   │   ├── service.png              # Service aspect icon
│   │   └── ...                      # Other aspect icons
│   ├── package.json                 # Node dependencies
│   └── vite.config.ts               # Vite configuration
│
├── models/
│   └── best_model.pt                # Trained XLM-RoBERTa model (1.06 GB)
│
├── predictions/
│   └── submission.json              # Generated predictions
│
├── Batch Upload.png
├── Franco-Arabic Translator.png
├── Restaurant Review Analyzer.png
│
├── .gitignore                       # Git ignore file
├── README.md                        # This file
└── LICENSE                          # MIT License
```

---

## 🚀 Quick Start

### 📋 Prerequisites

- **Node.js** v18 or higher
- **Python** v3.10 or higher
- **pip** v23 or higher
- **npm** v9 or higher
- **Git** v2.40 or higher

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/M718-arch/Microsoft_hackathon.git
cd Microsoft_hackathon
```

### 2️⃣ Backend Setup

```bash
cd backend

python -m venv venv
```

#### 🪟 Windows

```bash
venv\Scripts\activate
```

#### 🐧 Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend server:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3️⃣ Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

### 4️⃣ 🌐 Access the Application

| Service | URL |
|---------|-----|
| 🎨 Frontend | http://localhost:5173 |
| ⚙️ Backend API | http://localhost:8000 |
| 📚 API Documentation | http://localhost:8000/docs |

### 5️⃣ 📥 Model Setup

The trained model is approximately **1.06 GB** and may not be included directly in the repository.

#### Option A: 🤗 Hugging Face

```bash
pip install huggingface-hub

huggingface-cli download M718-arch/franco-arabic-absa-model best_model.pt --local-dir ./models/
```

#### Option B: ☁️ Google Drive

```bash
pip install gdown

gdown --id YOUR_GOOGLE_DRIVE_FILE_ID -O models/best_model.pt
```

#### Option C: 🧪 Demo Mode

If no trained model is available, the application can run using the project's available fallback/demo sentiment processing.

---

## 🔌 API Endpoints

### ❤️ Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### 🧠 Model Information

```http
GET /model/info
```

**Response:**

```json
{
  "model_loaded": true,
  "model_path": "../models/best_model.pt",
  "threshold": 0.55,
  "device": "cuda",
  "mode": "trained"
}
```

### 🔍 Predict Single Review

```http
POST /predict
Content-Type: application/json
```

**Request Body:**

```json
{
  "text": "el akl gamed",
  "star_rating": 5,
  "threshold": 0.55
}
```

**Response:**

```json
{
  "text": "el akl gamed",
  "translated": "الاكل جامد",
  "aspects": ["food"],
  "aspect_sentiments": {
    "food": "positive"
  },
  "sentiment_counts": {
    "positive": 1,
    "negative": 0,
    "neutral": 0
  }
}
```

### 📁 Batch Upload

```http
POST /upload
Content-Type: multipart/form-data
```

**Supported files:**

- `.txt`
- `.csv`
- `.xlsx`

**Request:**

- `file` — Review file
- `threshold` — Optional analysis threshold

**Response:**

```json
{
  "filename": "reviews.txt",
  "total_processed": 10,
  "results": [],
  "summary": {
    "positive": 7,
    "negative": 2,
    "neutral": 1
  }
}
```

### 🔄 Translate

```http
POST /translate
Content-Type: application/json
```

**Request:**

```json
{
  "text": "el akl gamed"
}
```

**Response:**

```json
{
  "original": "el akl gamed",
  "translated": "الاكل جامد"
}
```

---

## 🧪 Testing

### 💻 Test with cURL

#### 😊 Positive Review

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"el akl gamed"}'
```

#### 😞 Negative Review

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"el akl we7esh"}'
```

#### 😐 Neutral Review

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"el akl 3ady"}'
```

### 🐍 Test with Python

```python
import requests

url = "http://localhost:8000/predict"

data = {
    "text": "el akl gamed"
}

response = requests.post(url, json=data)

print(response.json())
```

### 🖥️ Test with Frontend

1. Open `http://localhost:5173`
2. Enter a restaurant review.
3. Add an optional star rating.
4. Click **Analyze Review**.
5. View the sentiment result.
6. View detected aspects.
7. Open the Franco-Arabic Translator when needed.
8. Use Batch Upload to analyze multiple reviews.

---

## 🎯 Supported Arabic Expressions

### 😊 Positive Expressions

| Arabizi | Arabic | English |
|---------|--------|---------|
| `kol haga tohfa` | كل حاجة تحفة | Everything is excellent |
| `el akl gamed` | الأكل جامد | The food is great |
| `el service helw` | الخدمة حلوة | The service is good |
| `el makan nadeef` | المكان نظيف | The place is clean |
| `bgd gamed` | بجد جامد | Really great |
| `kol haga zy el fol` | كل حاجة زي الفل | Everything is perfect |

### 😞 Negative Expressions

| Arabizi | Arabic | English |
|---------|--------|---------|
| `el akl we7esh` | الأكل وحش | The food is bad |
| `kol haga zy el zft` | كل حاجة زي الزفت | Everything is terrible |
| `el service se2` | الخدمة سيء | The service is bad |
| `el makan wehsh` | المكان وحش | The place is bad |
| `mish helw` | مش حلو | Not good |

### 😐 Neutral Expressions

| Arabizi | Arabic | English |
|---------|--------|---------|
| `el akl 3ady` | الأكل عادي | The food is average |
| `el service normal` | الخدمة عادي | The service is average |

---

## 🎨 UI Components

| Component | Description |
|-----------|-------------|
| **ReviewInput** | Review text input with optional star rating |
| **SentimentScale** | 3D animated sentiment faces |
| **BatchUpload** | Bulk file upload and processing |
| **Translator** | Franco-Arabic to Arabic translation |
| **Sidebar** | Application navigation and threshold controls |
| **CategoryCard** | Detected aspect and sentiment display |

---

## 📊 Model Performance

| Metric | Score |
|--------|-------|
| **Validation F1** | 0.7231 |
| **Precision** | 0.6684 |
| **Recall** | 0.7655 |
| **Threshold** | 0.55 |
| **Training Samples** | 1,971 |
| **Validation Samples** | 500 |
| **Epochs** | 8 |
| **Aspects** | 8 |

### 📈 Training Progress

| Epoch | Loss | Val F1 | Precision | Recall |
|------:|-----:|-------:|----------:|--------:|
| 1 | 1.7543 | 0.4842 | 0.4683 | 0.5012 |
| 2 | 1.2084 | 0.5678 | 0.5115 | 0.6381 |
| 3 | 0.9619 | 0.6165 | 0.5585 | 0.6881 |
| 4 | 0.8138 | 0.6271 | 0.5568 | 0.7179 |
| 5 | 0.7060 | 0.6772 | 0.6428 | 0.7155 |
| 6 | 0.6176 | 0.6973 | 0.6395 | 0.7667 |
| 7 | 0.5491 | 0.7049 | 0.6515 | 0.7679 |
| **8** | **0.5259** | **0.7137** | **0.6684** | **0.7655** |

---

## 👥 Team

### 🚀 Project Team

This project was developed by:

| Team Member |
|-------------|
| **Yassmin Ahmed** |
| **Mario Sameh** |
| **Zeina Mohamed** |

---

### 💡 Inspiration

- 🏆 DeepX Hackathon challenge
- 🇪🇬 Egyptian Arabic sentiment analysis
- 🍽️ Restaurant review analysis applications

---

Made with ❤️ for the DeepX Hackathon
