# 🔍 TruthLens — AI-Powered Content Credibility Analyzer

> Analyze any webpage for credibility, detect scams, hate speech, and misleading content — instantly.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- **🎯 Truth Score** — AI-calculated credibility rating (0-100) with visual indicators
- **📝 Smart Summary** — Concise 3-4 line summary of any webpage
- **🚨 Scam Detection** — Identifies phishing, deceptive patterns, and scam content
- **☠️ Hate Speech Detection** — Flags toxic, harmful, or hateful language
- **⚡ Misleading Content** — Detects clickbait, sensationalism, and manipulation
- **🔗 Domain Analysis** — Checks source credibility, HTTPS, and domain reputation
- **🕰️ Analysis History** — Track all your previously analyzed URLs
- **🌐 Multi-Language** — Supports English and Telugu (తెలుగు)
- **📱 Responsive Design** — Works beautifully on desktop and mobile
- **🎨 Dark Theme UI** — Premium glassmorphism design with smooth animations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Step 1: Navigate to the project

```bash
cd "c:\Users\DELL\jntuh hackathon\truthlens"
```

### Step 2: Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: (Optional) Set up OpenAI API

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
copy .env.example .env
```

Edit `.env` and replace `your_openai_api_key_here` with your actual key.

> **Note:** TruthLens works without an API key! It uses a built-in heuristic NLP engine as a fallback. The OpenAI integration enhances the analysis with GPT-4o-mini.

### Step 5: Run the server

```bash
python app.py
```

### Step 6: Open in browser

Navigate to: **http://localhost:5000**

---

## 📁 Project Structure

```
truthlens/
├── app.py                  # Flask backend (routes, analysis logic, API)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── static/
│   ├── css/
│   │   └── style.css       # Complete CSS design system
│   └── js/
│       └── app.js          # Frontend application logic
├── templates/
│   └── index.html          # Main HTML template (Jinja2)
└── README.md               # This file
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve the main application |
| `POST` | `/api/analyze` | Analyze a URL for credibility |
| `GET` | `/api/history` | Get analysis history |
| `GET` | `/api/translations/<lang>` | Get translation strings |

### POST `/api/analyze`

**Request:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com/article",
  "title": "Article Title",
  "summary": "A concise summary of the content...",
  "truth_score": 75,
  "is_scam": false,
  "is_toxic": false,
  "warnings": [],
  "domain_info": {
    "domain": "example.com",
    "is_credible_source": false,
    "has_https": true
  },
  "analysis_method": "heuristic"
}
```

---

## 🧠 How It Works

### Dual Analysis Engine

1. **OpenAI GPT-4o-mini** (when API key is available)
   - Uses AI to generate summaries, evaluate claims, and detect issues
   - More nuanced understanding of context and intent

2. **Built-in Heuristic Engine** (always available, no API needed)
   - 20+ scam pattern detectors (regex-based)
   - 9+ hate speech / toxic content patterns
   - 13+ misleading content indicators
   - Domain credibility database (Reuters, BBC, NYT, .gov, .edu, etc.)
   - Text quality metrics (caps ratio, exclamation density, sentence structure)

### Truth Score Breakdown

| Score | Rating | Color |
|-------|--------|-------|
| 70–100 | Highly Credible | 🟢 Green |
| 40–69 | Needs Verification | 🟡 Yellow |
| 0–39 | Low Credibility | 🔴 Red |

---

## 🌐 Multi-Language Support

TruthLens currently supports:
- 🇬🇧 **English** (default)
- 🇮🇳 **Telugu** (తెలుగు)

Toggle between languages using the buttons in the top navbar.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JavaScript |
| **Backend** | Python 3, Flask 3.1 |
| **Web Scraping** | Requests, BeautifulSoup4, lxml |
| **AI Analysis** | OpenAI GPT-4o-mini (optional) |
| **NLP Fallback** | TextBlob + Custom heuristic engine |
| **Fonts** | Inter, Space Grotesk, JetBrains Mono (Google Fonts) |

---

## 📋 License

MIT License — free to use, modify, and distribute.
