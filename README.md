# 🎯 Smart Task Analyzer

<div align="center">

![Smart Task Analyzer Banner](https://img.shields.io/badge/🎯_Smart_Task_Analyzer-Intelligent_Priority_Engine-667eea?style=for-the-badge&labelColor=1a1a2e)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=flat-square&logo=django&logoColor=white)](https://djangoproject.com)
[![REST API](https://img.shields.io/badge/REST_API-DRF-ff1709?style=flat-square&logo=django&logoColor=white)](https://django-rest-framework.org)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

**An intelligent task prioritization system that helps you focus on what matters most.**

[🚀 Live Demo](#-live-demo) • [✨ Features](#-features) • [🧠 Algorithm](#-algorithm) • [📖 API Docs](#-api-documentation) • [🛠️ Setup](#-quick-start)

</div>

---

## 🎬 Live Demo

> **🌐 [View Live Demo on Railway](https://smarttaskanalyzer.up.railway.app/)**

<div align="center">

<!-- Replace with actual screenshot - you can add one later -->
<img src="docs/Screenshot 2025-11-28 001640.png" alt="Smart Task Analyzer Demo" width="100%">

*_Add tasks, select a strategy, and get AI-powered prioritization recommendations_*

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔧 Backend Capabilities
- ✅ RESTful API with Django REST Framework
- ✅ Multi-factor scoring algorithm (4 strategies)
- ✅ Circular dependency detection (DFS)
- ✅ Comprehensive input validation
- ✅ Detailed score breakdowns
- ✅ Edge case handling

</td>
<td width="50%">

### 🎨 Frontend Experience
- ✅ Modern dark-themed UI
- ✅ Form & JSON input modes
- ✅ Real-time importance slider
- ✅ Visual priority indicators
- ✅ Top 3 recommendations modal
- ✅ Priority distribution chart

</td>
</tr>
</table>

---

## 🧠 Algorithm

The priority scoring algorithm balances multiple competing factors:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRIORITY SCORE FORMULA                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Score = (Urgency × W₁) + (Importance × W₂) +                   │
│          (Effort × W₃) + (Dependencies × W₄)                    │
│                                                                 │
│  Where W₁ + W₂ + W₃ + W₄ = 100%                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Urgency Scoring
```
Overdue:        100 + (days_overdue × 5), max 150
Due today:      100
Due tomorrow:   90
Due in 3 days:  80-85
Due in 1 week:  70-80
Due in 2 weeks: 50-70
Due in 1 month: 30-50
No due date:    20
```

### Effort Scoring (Quick Wins)
```
< 30 min:  100 (quick win!)
< 1 hour:  95
1-2 hours: 70-90
2-4 hours: 50-70
4-8 hours: 30-50
> 8 hours: 10-30
```

### Dependency Scoring
```
Blocks 0 tasks:  40 (baseline)
Blocks 1 task:   70
Blocks 2-3:      85
Blocks 4+:       100 (critical path)
```

</details>

---

## 🚀 Quick Start

### Option 1: Deploy to Railway (Recommended) 🚂

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Go to [railway.app](https://railway.app)
2. Sign up/in with **GitHub**
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select this repository
5. Railway auto-detects Django and deploys! ✨
6. Get your free `.railway.app` subdomain 

**Environment Variables (optional):**
```
SECRET_KEY=your-super-secret-key
DEBUG=False
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/task-analyzer.git
cd task-analyzer

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (new terminal)
cd frontend
python -m http.server 3000  # Or open index.html directly
```

Visit `http://localhost:3000` to use the app!

---

## 📚 API Documentation

### Base URL
```
Production: https://your-app.railway.app/api
Local:      http://localhost:8000/api
```

### Endpoints

<details>
<summary><code>POST /api/tasks/analyze/</code> - Analyze & Prioritize Tasks</summary>

**Request:**
```json
{
  "tasks": [
    {
      "id": "task_1",
      "title": "Fix login bug",
      "due_date": "2025-01-15",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    }
  ],
  "strategy": "smart_balance"
}
```

**Response:**
```json
{
  "tasks": [...],
  "total_count": 5,
  "strategy": "smart_balance",
  "weights": { "urgency": 30, "importance": 35, "effort": 15, "dependency": 20 },
  "circular_dependencies": [],
  "priority_distribution": { "high": 2, "medium": 2, "low": 1 }
}
```
</details>

<details>
<summary><code>POST /api/tasks/suggest/</code> - Get Top Recommendations</summary>

**Request:**
```json
{
  "tasks": [...],
  "strategy": "smart_balance",
  "count": 3
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "rank": 1,
      "task": {...},
      "recommendation_reason": "High urgency + blocks other tasks",
      "actionable_insight": "Complete this first to unblock downstream work"
    }
  ]
}
```
</details>

---

## 🧪 Testing

```bash
cd backend
python manage.py test tasks -v 2
```

**Test Coverage:**
- ✅ Urgency scoring (all date scenarios)
- ✅ Importance scaling
- ✅ Effort calculations
- ✅ Circular dependency detection
- ✅ Input validation
- ✅ Edge cases

---

## 🎨 Design Decisions

| Decision | Reasoning |
|----------|-----------|
| **Multi-factor scoring** | Single-factor (e.g., due date only) misses complexity |
| **4 strategies** | Different contexts need different approaches |
| **Client-side state** | Simplicity; easily extendable to persistent storage |
| **Circular dependency detection** | Prevents infinite loops; uses DFS algorithm |
| **Score capping at 100** | Intuitive interpretation; overdue gets bonus |

---

## 🔮 Future Roadmap

- [ ] 📊 Eisenhower Matrix visualization
- [ ] 📅 Weekend/holiday-aware deadlines
- [ ] 🧠 ML-based personalization
- [ ] 💾 Database persistence
- [ ] 👥 Team collaboration
- [ ] 📤 Calendar integration (iCal)

---

## 👤 Author : Tarra Nikhitha

**Software Development Intern Candidate**

Built using Python, Django, and vanilla JavaScript.

---

<div align="center">

### ⭐ Star this repo if you found it helpful!

</div>
