# Responsible-climate-change-mitigation-and-sustainability
# 🌍 Meteo Pro – Climate–SDG Weather Consultation Dashboard

Meteo Pro is a **real-time climate intelligence and SDG (Sustainable Development Goals) consultation system**.  
It combines live weather data, a simple Climate Risk Index (CRI), and a rich web dashboard to provide:

- Location-based weather insights  
- Risk levels (Low / Medium / High)  
- SDG-aligned recommendations  
- Email + PDF consultation reports

Built with **Flask, Open-Meteo API, Leaflet.js and Chart.js**.

---

## ✨ Key Features

- 🔍 **Location search & map**
  - Search by city name.
  - Drag marker on interactive map (Leaflet).
  - Auto-detect location using browser geolocation + IP fallback.

- 🌤 **Live weather & 7-day forecast**
  - Current conditions (temp, humidity, wind, weather code).
  - Hourly temperature chart for the next 24 hours (Chart.js).
  - 7-day high/low outlook with rain probability.

- 🚨 **Climate Risk Index (CRI)**
  - Simple rule / scoring model using temperature, humidity and wind speed.
  - Shows **Low / Medium / High** risk badge for the location.

- 🧭 **Climate–SDG consultation**
  - User enters name, email, industry & notes.
  - Backend generates a consultation report with:
    - current weather snapshot  
    - risk assessment  
    - SDG-oriented guidance  
  - Report is emailed to the user and available as PDF.

- 🗂 **Consultation history**
  - In-memory log of previous consultations.
  - Shown in the dashboard with time, location and industry.

- 📄 **Export**
  - Download raw weather JSON.
  - Download consultation report as **PDF** (ReportLab).

---

## 🏗 Tech Stack

**Backend**

- Python 3  
- Flask  
- Requests (HTTP client)  
- smtplib + email.mime (SMTP email)  
- ReportLab (PDF generation, optional)

**Frontend**

- HTML5 + CSS (custom UI, glassmorphism style)  
- Vanilla JavaScript  
- Leaflet.js (map & marker)  
- Chart.js (hourly temperature line chart)

**External Services**

- [Open-Meteo API](https://open-meteo.com/) – weather & forecast  
- [ipapi.co](https://ipapi.co/) – IP geolocation (fallback)  
- SMTP server (e.g., Gmail) – sending reports

---

## 📂 Project Structure

```text
.
├── cli.py              # Main Flask app (backend + embedded HTML/JS)
├── requirements.txt    # Python dependencies (optional)
└── README.md           # Project documentation
