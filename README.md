🔗 **Live Demo:** https://edb1b02f-3405-48b9-920e-8062b52a411b.plotly.app/
*(Best viewed on desktop, live data replay enabled)*

---

# Noche — Energy Timing Gamification (MVP)

Noche is a gamified energy platform that rewards users not for using less energy, but for using it at the right time.

This repository contains the MVP User Dashboard, designed for students living in dorms or shared apartments (e.g., USC housing). The app visualizes energy usage from smart plugs, highlights optimal usage windows, and drives behavior change through points, streaks, challenges, and leaderboards.

---

## ✨ Key Idea

> **We don’t ask people to use less energy, instead we reward them for using it at the right time.**

Noche aligns individual behavior with grid-friendly energy usage by:
- Encouraging consumption during Green Hours
- Discouraging usage during Busy Hours
- Making energy timing visible, simple, and competitive

---

## 🚀 MVP Features

### 👤 User Dashboard
- **Live indicator** showing real-time / replayed energy data
- **Green vs Busy Hours usage**
  - kWh per student
  - Percentage of daily usage
- **Daily Points**
  - Reset every day for immediate feedback
- **Weekly Points**
  - Accumulate across the week
  - Used for competition
- **Green Streak**
  - Rewards consistent behavior over time
  - Bonus increases as streak grows
- **Weekly Challenges**
  - Fixed dorm-level challenges
  - Automatic reward allocation
- **Leaderboard**
  - Normalized per student (fair across dorm sizes)
  - Rank movement indicators (up / down / same)
  - Top 8 visible with user highlighted

---

## 🧠 How Scoring Works (Simplified)

- **Green Hours** → highest points (with streak bonus)
- **Normal Hours** → medium points
- **Busy Hours** → penalty
- **Weekly Challenges** → fixed bonus points
- **Leaderboard** → compares points per student, not per dorm

---

## 🏗️ Tech Stack

- **Python**
- **Dash (Plotly)**
- **Dash Bootstrap Components**
- **Pandas**
- **CSS (custom styling + animations)**

No backend or database is required for the MVP — all data is replayed from CSV.

---

## 📁 Project Structure
```
noche_app_mvp/
├── app/
│   ├── app.py
│   ├── config.py
│   ├── data_service.py
│   ├── ui_components.py
├── assets/
│   └── style.css
├── data/
│   └── demo_data.csv
├── requirements.txt
└── README.md
```
---

## ▶️ How to Run

```bash
pip install -r requirements.txt
python util/make_csv.py
python app/app.py
```

Then open: http://127.0.0.1:8040

---

## 🧪 What This MVP Demonstrates

- Behavioral energy nudging works without restricting usage
- Gamification can shift demand away from busy hours
- Normalizing per student makes competition fair

---

## 🛣️ Future Work

- Smart plug API integration
- Admin dashboard for campuses
- Forecast-driven recommendations
- Mobile-first UI

