#!/usr/bin/env python3
"""
Meteo Dashboard — Fancy UI + Location Search + Consultations + 7-day Forecast
"""

import os, io, smtplib
from datetime import datetime
import requests
from flask import Flask, request, jsonify, render_template_string, send_file
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# PDF support (optional)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as rl_canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

PORT = int(os.environ.get("PORT", 5000))
app = Flask(__name__, static_folder=None)

# ---------------- EMAIL CONFIG ----------------
# 🔐 Use env vars in real deployment
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "vignesht3154@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "waqu yjeb nsnc qicf")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASS)
        server.sendmail(SMTP_EMAIL, to, msg.as_string())
        server.quit()

        print("[INFO] Email sent successfully")
        return True
    except Exception as e:
        print("[ERROR] Email failed:", e)
        return False


# In-memory consultations
consultations = []

# ---------------- HTML / JS (AWESOME UI + 7-day forecast + quick cities) ----------------
INDEX = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meteo — Pro Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
:root{
  --bg:#020617;
  --bg-panel:rgba(15,23,42,0.92);
  --bg-card:rgba(15,23,42,0.9);
  --bg-soft:rgba(15,23,42,0.7);
  --border-soft:rgba(148,163,184,0.25);
  --muted:#94a3b8;
  --accent:#38bdf8;
  --accent-soft:rgba(56,189,248,0.15);
  --success:#22c55e;
  --warning:#facc15;
  --danger:#f97373;
  --text:#e2e8f0;
  --text-strong:#f9fafb;
}

[data-theme="light"]{
  --bg:#e5ecf4;
  --bg-panel:rgba(255,255,255,0.95);
  --bg-card:#ffffff;
  --bg-soft:#f8fafc;
  --border-soft:rgba(148,163,184,0.3);
  --muted:#6b7280;
  --accent:#0ea5e9;
  --accent-soft:rgba(14,165,233,0.12);
  --success:#16a34a;
  --warning:#f59e0b;
  --danger:#ef4444;
  --text:#0f172a;
  --text-strong:#020617;
}

*{box-sizing:border-box;font-family:Inter,system-ui,Arial,sans-serif}
html,body{margin:0;height:100%;}
body{
  background:
    radial-gradient(circle at 10% 0%, rgba(56,189,248,0.20), transparent 55%),
    radial-gradient(circle at 90% 100%, rgba(59,130,246,0.18), transparent 55%),
    radial-gradient(circle at 0% 100%, rgba(45,212,191,0.14), transparent 50%),
    var(--bg);
  color:var(--text);
}

.app{
  display:flex;
  min-height:100vh;
  backdrop-filter: blur(16px);
}

#map{
  flex:1;
  min-width:320px;
  height:100vh;
}

/* Side panel */
.panel{
  width:440px;
  max-width:100%;
  padding:20px 18px 18px;
  background:var(--bg-panel);
  border-left:1px solid rgba(15,23,42,0.7);
  box-shadow:-12px 0 40px rgba(15,23,42,0.7);
  display:flex;
  flex-direction:column;
}

.header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:14px;
}

.brand{
  display:flex;
  align-items:center;
  gap:10px;
}

.brand-logo{
  width:32px;
  height:32px;
  border-radius:12px;
  background:conic-gradient(from 180deg,#38bdf8,#22c55e,#6366f1,#38bdf8);
  display:flex;
  align-items:center;
  justify-content:center;
  color:white;
  font-weight:800;
  font-size:15px;
  box-shadow:0 8px 18px rgba(59,130,246,0.7);
}

.title-block{
  display:flex;
  flex-direction:column;
}

.app-title{
  font-weight:700;
  font-size:19px;
  color:var(--text-strong);
}

.app-sub{
  font-size:12px;
  color:var(--muted);
}

.controls{
  display:flex;
  gap:8px;
  align-items:center;
}

.btn{
  background:var(--accent);
  color:#0b1120;
  border:none;
  padding:8px 12px;
  border-radius:999px;
  cursor:pointer;
  font-weight:600;
  font-size:13px;
  display:inline-flex;
  align-items:center;
  gap:6px;
  box-shadow:0 8px 20px rgba(56,189,248,0.35);
  transition:transform .14s ease, box-shadow .14s ease, background .14s ease;
}
.btn span.icon{
  font-size:15px;
}
.btn:hover{
  transform:translateY(-1px);
  box-shadow:0 12px 26px rgba(56,189,248,0.45);
}
.btn.ghost{
  background:transparent;
  color:var(--accent);
  border:1px solid var(--border-soft);
  box-shadow:none;
}
.btn.ghost:hover{
  background:var(--accent-soft);
  box-shadow:none;
}
.btn.sm{
  padding:6px 8px;
  font-size:11px;
}

.theme-toggle{
  width:30px;
  height:30px;
  border-radius:999px;
  display:flex;
  align-items:center;
  justify-content:center;
  background:var(--bg-soft);
  border:1px solid var(--border-soft);
  cursor:pointer;
  font-size:15px;
}

/* Cards & layout */
.section-scroll{
  flex:1;
  overflow:auto;
  padding-right:2px;
  scrollbar-width:thin;
}
.section-scroll::-webkit-scrollbar{width:6px;}
.section-scroll::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.45);border-radius:999px;}

.card{
  background:var(--bg-card);
  border-radius:18px;
  padding:14px 14px 12px;
  margin-bottom:12px;
  border:1px solid var(--border-soft);
  box-shadow:0 14px 35px rgba(15,23,42,0.7);
}

.card.soft{
  background:var(--bg-soft);
  box-shadow:none;
}

/* Search + pills + quick cities */
.input-wrap{
  display:flex;
  gap:8px;
  margin-bottom:8px;
}

.input{
  flex:1;
  padding:8px 10px;
  border-radius:999px;
  border:1px solid var(--border-soft);
  background:rgba(15,23,42,0.7);
  color:var(--text);
  font-size:13px;
  outline:none;
}
[data-theme="light"] .input{
  background:#f8fafc;
}
.input::placeholder{color:var(--muted);font-size:12px;}

.coord-pill{
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:5px 9px;
  border-radius:999px;
  background:rgba(15,23,42,0.7);
  border:1px dashed var(--border-soft);
  font-size:11px;
  color:var(--muted);
}

.quick-cities{
  margin-top:8px;
  display:flex;
  flex-wrap:wrap;
  gap:6px;
}
.city-chip{
  font-size:11px;
  padding:5px 10px;
  border-radius:999px;
  border:1px solid var(--border-soft);
  background:rgba(15,23,42,0.8);
  color:var(--muted);
  cursor:pointer;
}
.city-chip:hover{
  background:var(--accent-soft);
  color:var(--text);
}

/* Weather hero block */
.weather-hero{
  display:flex;
  gap:12px;
  align-items:stretch;
}

.hero-icon{
  width:80px;
  min-width:80px;
  height:80px;
  border-radius:24px;
  background:radial-gradient(circle at 0% 0%,rgba(250,250,250,0.7),transparent 60%),
             radial-gradient(circle at 100% 100%,rgba(56,189,248,0.7),transparent 65%),
             #0f172a;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:36px;
  box-shadow:0 16px 32px rgba(15,23,42,0.90);
}

.hero-main{
  flex:1;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
}

.hero-top{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
}

.loc-name{
  font-size:14px;
  font-weight:600;
  color:var(--text-strong);
}
.wx-desc{
  font-size:12px;
  color:var(--muted);
}

.temp-main{
  text-align:right;
}
.temp-value{
  font-size:30px;
  font-weight:800;
}
.temp-feels{
  font-size:12px;
  color:var(--muted);
}

/* Metrics chips */
.metrics{
  display:flex;
  gap:8px;
  margin-top:8px;
}
.metric{
  flex:1;
  padding:8px 8px;
  border-radius:12px;
  background:radial-gradient(circle at 0% 0%,rgba(56,189,248,0.15),transparent 65%),
             rgba(15,23,42,0.9);
  border:1px solid rgba(148,163,184,0.25);
}
.metric-label{
  font-size:11px;
  color:var(--muted);
}
.metric-val{
  font-size:16px;
  font-weight:600;
}

/* Risk badge */
.badge{
  display:inline-flex;
  padding:5px 10px;
  border-radius:999px;
  font-weight:600;
  font-size:11px;
  border:1px solid transparent;
  align-items:center;
  gap:6px;
}
.badge.dot::before{
  content:"";
  width:8px;
  height:8px;
  border-radius:999px;
}
.risk-low{background:rgba(34,197,94,0.12);border-color:rgba(34,197,94,0.45);color:var(--success);}
.risk-low.dot::before{background:var(--success);}
.risk-med{background:rgba(234,179,8,0.12);border-color:rgba(234,179,8,0.5);color:var(--warning);}
.risk-med.dot::before{background:var(--warning);}
.risk-high{background:rgba(248,113,113,0.12);border-color:rgba(248,113,113,0.6);color:var(--danger);}
.risk-high.dot::before{background:var(--danger);}

/* Chart + hourly strip */
.chart-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:6px;
}
.chart-title{
  font-size:12px;
  font-weight:600;
}
.chart-sub{
  font-size:11px;
  color:var(--muted);
}

#hourChart{
  width:100%;
  height:170px;
}

.hourly-strip{
  display:flex;
  gap:8px;
  margin-top:10px;
  overflow-x:auto;
  padding-bottom:4px;
  scrollbar-width:thin;
}
.hourly-strip::-webkit-scrollbar{height:6px;}
.hourly-strip::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.55);border-radius:999px;}

.hour-chip{
  min-width:70px;
  padding:6px 6px 5px;
  border-radius:12px;
  background:rgba(15,23,42,0.9);
  border:1px solid var(--border-soft);
  font-size:11px;
  display:flex;
  flex-direction:column;
  gap:2px;
  align-items:flex-start;
}
.hour-chip .time{color:var(--muted);font-size:10px;}
.hour-chip .val{font-weight:600;}
.hour-chip .mini{font-size:10px;color:var(--muted);}

/* Daily 7-day strip */
.daily-card{
  margin-top:10px;
}
.daily-strip{
  display:flex;
  gap:8px;
  overflow-x:auto;
  padding-bottom:4px;
  scrollbar-width:thin;
}
.daily-strip::-webkit-scrollbar{height:6px;}
.daily-strip::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.55);border-radius:999px;}
.day-card{
  min-width:90px;
  padding:7px 7px 6px;
  border-radius:14px;
  background:rgba(15,23,42,0.9);
  border:1px solid var(--border-soft);
  font-size:11px;
  display:flex;
  flex-direction:column;
  gap:2px;
  align-items:flex-start;
}
.day-name{
  font-weight:600;
  font-size:11px;
}
.day-icon{
  font-size:16px;
}
.day-temps{
  font-size:11px;
}
.day-temps span{
  font-weight:600;
}
.day-rain{
  font-size:10px;
  color:var(--muted);
}

/* Consultations */
.section-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:4px;
}
.section-title{
  font-size:13px;
  font-weight:600;
}
.section-sub{
  font-size:11px;
  color:var(--muted);
}

.consult-item{
  padding:8px;
  border-radius:12px;
  background:var(--bg-soft);
  border:1px solid var(--border-soft);
  margin-bottom:8px;
  font-size:12px;
}
.consult-item-header{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
}
.consult-item-meta{
  font-size:11px;
  color:var(--muted);
}

/* Modal */
.modal{
  position:fixed;
  left:50%;
  top:50%;
  transform:translate(-50%,-50%);
  width:820px;
  max-width:96%;
  background:var(--bg-panel);
  border-radius:18px;
  padding:16px;
  box-shadow:0 30px 80px rgba(15,23,42,0.9);
  z-index:1000;
  max-height:80vh;
  overflow:auto;
  border:1px solid var(--border-soft);
}
.modal pre{
  white-space:pre-wrap;
  background:var(--bg-soft);
  padding:10px;
  border-radius:12px;
  font-size:12px;
}

.footer{
  font-size:11px;
  color:var(--muted);
  margin-top:4px;
  text-align:center;
}

/* Responsive */
@media (max-width:900px){
  .panel{
    position:absolute;
    right:0;
    width:100%;
    max-width:none;
    height:70vh;
    bottom:0;
    border-radius:18px 18px 0 0;
    box-shadow:0 -18px 60px rgba(15,23,42,0.95);
  }
  #map{
    height:30vh;
  }
}
</style>
</head>
<body>
<div class="app">
  <div id="map"></div>

  <div class="panel">
    <div class="header">
      <div class="brand">
        <div class="brand-logo">M</div>
        <div class="title-block">
          <div class="app-title">Meteo Pro</div>
          <div class="app-sub">Live weather • Anywhere on Earth</div>
        </div>
      </div>
      <div class="controls">
        <button id="themeToggle" class="theme-toggle" title="Toggle theme">🌙</button>
      </div>
    </div>

    <div class="card soft">
      <div class="input-wrap">
        <input id="searchBox" class="input" list="recentList"
               placeholder="Search city, state or country...">
        <button id="searchBtn" class="btn sm"><span class="icon">🔍</span><span>Go</span></button>
        <button id="locBtn" class="btn sm ghost"><span class="icon">📍</span><span>My loc</span></button>
      </div>
      <datalist id="recentList"></datalist>
      <div class="coord-pill">
        <span style="font-size:13px;">📌</span>
        <span id="locLabel">Drag the map or search to begin</span>
      </div>
      <div class="quick-cities">
        <div class="city-chip" data-city="Chennai">Chennai</div>
        <div class="city-chip" data-city="Delhi">Delhi</div>
        <div class="city-chip" data-city="Mumbai">Mumbai</div>
        <div class="city-chip" data-city="Bengaluru">Bengaluru</div>
        <div class="city-chip" data-city="Hyderabad">Hyderabad</div>
        <div class="city-chip" data-city="Coimbatore">Coimbatore</div>
      </div>
    </div>

    <div class="section-scroll">

      <div id="weatherCard" class="card" style="display:none;">
        <div class="weather-hero">
          <div class="hero-icon" id="wxIcon">☀️</div>
          <div class="hero-main">
            <div class="hero-top">
              <div>
                <div class="loc-name" id="locNameText">Selected location</div>
                <div class="wx-desc" id="wxDesc"></div>
              </div>
              <div class="temp-main">
                <div class="temp-value" id="tempVal">--°C</div>
                <div class="temp-feels">Feels like <span id="feelsVal">--°C</span></div>
              </div>
            </div>
            <div class="metrics">
              <div class="metric">
                <div class="metric-label">Wind</div>
                <div class="metric-val" id="windVal">-- m/s</div>
              </div>
              <div class="metric">
                <div class="metric-label">Humidity</div>
                <div class="metric-val" id="humVal">--%</div>
              </div>
              <div class="metric">
                <div class="metric-label">Pressure</div>
                <div class="metric-val" id="presVal">-- hPa</div>
              </div>
            </div>
          </div>
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;">
          <div id="riskBadge" class="badge dot risk-low">
            <span>Risk: Low</span>
          </div>
          <div style="display:flex;gap:6px;">
            <button id="openConsult" class="btn sm"><span class="icon">📝</span><span>Consult</span></button>
            <button id="downloadPDF" class="btn sm ghost"><span class="icon">⬇</span><span>JSON</span></button>
          </div>
        </div>

        <div style="margin-top:12px" class="card soft">
          <div class="chart-header">
            <div>
              <div class="chart-title">Next 24 hours</div>
              <div class="chart-sub">Temperature trend at this location</div>
            </div>
            <div class="chart-sub">Hourly • local time</div>
          </div>
          <canvas id="hourChart"></canvas>
          <div id="hourlyChips" class="hourly-strip"></div>
        </div>

        <div class="card soft daily-card">
          <div class="chart-header">
            <div>
              <div class="chart-title">7-day outlook</div>
              <div class="chart-sub">High / low • rain chance</div>
            </div>
          </div>
          <div id="dailyStrip" class="daily-strip"></div>
        </div>
      </div>

      <div class="card">
        <div class="section-header">
          <div>
            <div class="section-title">Consultation history</div>
            <div class="section-sub">Previous reports generated for any location</div>
          </div>
          <button id="viewAll" class="btn sm ghost"><span class="icon">📂</span><span>Refresh</span></button>
        </div>
        <div id="consultationsList"></div>
      </div>

      <div class="footer">Powered by Open-Meteo • Drag the marker or search to explore global weather.</div>
    </div>
  </div>
</div>

<!-- Report modal -->
<div id="reportModal" class="modal" style="display:none;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <div style="font-weight:600;font-size:14px;">Consultation Report</div>
    <div style="display:flex;gap:6px;">
      <button id="modalPdf" class="btn sm"><span class="icon">⬇</span><span>PDF</span></button>
      <button id="closeModal" class="btn sm ghost">Close</button>
    </div>
  </div>
  <div id="reportBody"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
(async function(){
  // Initial theme: dark; toggle adds [data-theme="light"]
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  themeToggle.onclick = () => {
    if (root.getAttribute('data-theme') === 'light') {
      root.removeAttribute('data-theme');
      themeToggle.textContent = '🌙';
    } else {
      root.setAttribute('data-theme', 'light');
      themeToggle.textContent = '🌑';
    }
  };

  // Map & defaults
  let lat = 20.5937, lon = 78.9629;
  let hourChart = null, lastWeather = null;
  let lastLocationLabel = '';

  const map = L.map('map').setView([lat, lon], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom: 19,
    attribution: '© OpenStreetMap'
  }).addTo(map);
  const marker = L.marker([lat, lon], {draggable:true}).addTo(map);
  marker.on('dragend', (e) => {
    const p = e.target.getLatLng();
    setLocation(p.lat, p.lng, '');
    fetchWeather();
  });

  // Elements
  const locBtn = document.getElementById('locBtn');
  const openConsult = document.getElementById('openConsult');
  const downloadJSON = document.getElementById('downloadPDF');
  const reportModal = document.getElementById('reportModal');
  const closeModal = document.getElementById('closeModal');
  const modalPdf = document.getElementById('modalPdf');
  const searchBox = document.getElementById('searchBox');
  const searchBtn = document.getElementById('searchBtn');
  const recentList = document.getElementById('recentList');
  const cityChips = document.querySelectorAll('.city-chip');
  const RECENT_KEY = 'meteo_recent_locations';

  const locLabelEl = document.getElementById('locLabel');
  const locNameText = document.getElementById('locNameText');

  locBtn.onclick = tryGeolocation;
  searchBtn.onclick = searchLocation;
  searchBox.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') searchLocation();
  });

  cityChips.forEach(chip => {
    chip.onclick = () => {
      const name = chip.getAttribute('data-city');
      searchBox.value = name;
      searchLocation();
    };
  });

  // High accuracy geolocation with IP fallback
  async function tryGeolocation(){
    if(!navigator.geolocation){ await ipFallback(); return; }
    let got = false;
    const opts = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 };
    navigator.geolocation.getCurrentPosition((p)=>{
      got = true;
      setLocation(p.coords.latitude, p.coords.longitude, 'My location');
      map.setView([p.coords.latitude, p.coords.longitude], 11);
      fetchWeather();
    }, async (err)=>{
      console.warn('geolocation failed', err);
      await ipFallback();
    }, opts);
    setTimeout(()=>{ if(!got) ipFallback(); }, 11000);
  }

  // IP fallback using free IP geolocation. If blocked, fallback to default coords.
  async function ipFallback(){
    try{
      const resp = await fetch('https://ipapi.co/json/');
      if(!resp.ok) throw new Error('ip lookup failed');
      const j = await resp.json();
      if(j && j.latitude && j.longitude){
        setLocation(j.latitude, j.longitude, j.city || 'Your area');
        map.setView([j.latitude, j.longitude], 8);
        fetchWeather();
        return;
      }
    }catch(e){
      console.warn('IP fallback failed', e);
    }
    setLocation(lat, lon, 'Default view');
    fetchWeather();
  }

  function setLocation(a,b,label){
    lat = +a; lon = +b;
    marker.setLatLng([lat,lon]);
    lastLocationLabel = label || '';
    const coordText = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
    locLabelEl.textContent = label ? `${label} • ${coordText}` : coordText;
    locNameText.textContent = label || 'Selected location';
  }

  // Recent locations: load from localStorage into datalist
  function loadRecent() {
    let arr = [];
    try {
      arr = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
    } catch (e) {
      arr = [];
    }
    if (!Array.isArray(arr)) arr = [];
    recentList.innerHTML = arr
      .map(name => `<option value="${name}"></option>`)
      .join('');
  }

  // Save a searched name and refresh suggestions
  function saveRecent(name) {
    name = (name || '').trim();
    if (!name) return;
    let arr = [];
    try {
      arr = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
    } catch (e) {
      arr = [];
    }
    if (!Array.isArray(arr)) arr = [];
    arr = [name, ...arr.filter(x => x.toLowerCase() !== name.toLowerCase())].slice(0, 7);
    localStorage.setItem(RECENT_KEY, JSON.stringify(arr));
    loadRecent();
  }

  // Search by location name using Open-Meteo geocoding API
  async function searchLocation() {
    const q = searchBox.value.trim();
    if (!q) return alert("Enter location name");

    try {
      const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=1`;
      const resp = await fetch(url);
      const data = await resp.json();

      if (!data.results || !data.results.length)
        return alert("Location not found");

      const r = data.results[0];
      const labelParts = [r.name, r.admin1, r.country_code].filter(Boolean);
      const label = labelParts.join(", ");

      saveRecent(q);
      setLocation(r.latitude, r.longitude, label);
      map.setView([r.latitude, r.longitude], 10);
      fetchWeather();
    } catch (e) {
      console.error("search failed", e);
      alert("Search failed");
    }
  }

  async function fetchWeather(){
    try{
      const resp = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
      if(!resp.ok){
        const j = await resp.json().catch(()=>null);
        throw new Error((j && j.error) ? j.error : resp.statusText);
      }
      const j = await resp.json();
      lastWeather = j;
      renderWeather(j);
    }catch(e){
      console.error('weather fetch', e);
      const card = document.getElementById('weatherCard');
      card.style.display='block';
      document.getElementById('wxDesc').textContent = 'Error: '+e.message;
    }
  }

  function codeToEmoji(code){
    if(code>=95) return '⛈️';
    if(code>=80) return '🌩️';
    if(code>=60) return '🌧️';
    if(code>=30) return '🌦️';
    if(code>=10) return '🌤️';
    return '☀️';
  }

  function renderWeather(data){
    const card = document.getElementById('weatherCard');
    card.style.display='block';

    const cur = data.current;
    document.getElementById('tempVal').textContent = (cur.temp!==null?cur.temp:'--') + '°C';
    document.getElementById('feelsVal').textContent = (cur.feels_like!==null?cur.feels_like:'--') + '°C';
    document.getElementById('wxDesc').textContent =
      (cur.weather && cur.weather[0] && cur.weather[0].description) || 'Live conditions';
    document.getElementById('windVal').textContent = (cur.wind_speed||'-') + ' m/s';
    document.getElementById('humVal').textContent = (cur.humidity||'-') + '%';
    document.getElementById('presVal').textContent = (cur.pressure||'—') + ' hPa';

    const code = (cur.weather && cur.weather[0] && cur.weather[0].code) || 0;
    document.getElementById('wxIcon').textContent = codeToEmoji(code);

    // risk badge
    const risks = [];
    if(cur.temp && cur.temp>35) risks.push('High temperature');
    if(cur.wind_speed && cur.wind_speed>12) risks.push('Strong wind');
    if(cur.humidity && cur.humidity>80) risks.push('High humidity');

    const badge = document.getElementById('riskBadge');
    if(risks.length===0){
      badge.textContent = 'Risk: Low';
      badge.className = 'badge dot risk-low';
    } else if(risks.length===1){
      badge.textContent = 'Risk: Medium • ' + risks[0];
      badge.className = 'badge dot risk-med';
    } else {
      badge.textContent = 'Risk: High • ' + risks.join(', ');
      badge.className = 'badge dot risk-high';
    }

    // hourly chart & chips
    const hours = (data.hourly||[]).slice(0,24);
    const labels = hours.map(h => new Date(h.dt*1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}));
    const temps = hours.map(h => h.temp);
    const ctx = document.getElementById('hourChart').getContext('2d');
    if(hourChart) hourChart.destroy();
    hourChart = new Chart(ctx, {
      type:'line',
      data:{
        labels,
        datasets:[{
          label:'Temp (°C)',
          data:temps,
          fill:true,
          tension:0.35,
        }]
      },
      options:{
        plugins:{ legend:{display:false} },
        scales:{
          x:{ ticks:{ font:{size:10} } },
          y:{ beginAtZero:false, ticks:{ font:{size:10} } }
        }
      }
    });

    const strip = document.getElementById('hourlyChips');
    strip.innerHTML = hours.map((h,idx) => {
      const t = labels[idx];
      const temp = h.temp;
      return `
        <div class="hour-chip">
          <div class="time">${t}</div>
          <div class="val">${temp.toFixed(1)}°</div>
          <div class="mini">code:${h.weather[0].description.replace('code:','')}</div>
        </div>
      `;
    }).join('');

    // daily 7-day strip
    const dailyStrip = document.getElementById('dailyStrip');
    const daily = data.daily || [];
    dailyStrip.innerHTML = daily.map(d => {
      const date = new Date(d.dt*1000);
      const dayName = date.toLocaleDateString([], { weekday: 'short' });
      const icon = codeToEmoji(d.code || 0);
      const tmax = d.temp_max != null ? d.temp_max.toFixed(1) : '--';
      const tmin = d.temp_min != null ? d.temp_min.toFixed(1) : '--';
      const rain = d.rain_prob != null ? d.rain_prob : null;
      return `
        <div class="day-card">
          <div class="day-name">${dayName}</div>
          <div class="day-icon">${icon}</div>
          <div class="day-temps">
            <span>${tmax}°</span> / <span style="opacity:0.7;">${tmin}°</span>
          </div>
          <div class="day-rain">${rain !== null ? ('Rain: '+rain+'%') : ''}</div>
        </div>
      `;
    }).join('');
  }

  // consultations UI
  async function loadConsultations(){
    try{
      const r = await fetch('/api/consultations');
      const list = await r.json();
      const el = document.getElementById('consultationsList');
      if(!list || !list.length){
        el.innerHTML = '<div class="section-sub">No consultations yet. Generate one from the current weather card.</div>';
        return;
      }
      el.innerHTML = list.map(c=>`
        <div class="consult-item">
          <div class="consult-item-header">
            <div>
              <div style="font-weight:600;">#${c.id} ${c.name}</div>
              <div class="consult-item-meta">${c.industry} • ${new Date(c.createdAt).toLocaleString()}</div>
            </div>
            <div style="text-align:right;">
              <div class="consult-item-meta">Loc</div>
              <div class="consult-item-meta">${c.lat.toFixed(3)}, ${c.lon.toFixed(3)}</div>
            </div>
          </div>
        </div>
      `).join('');
    }catch(e){
      console.warn('load consults', e);
    }
  }

  document.getElementById('viewAll').onclick = loadConsultations;

  // open consult -> simple prompts
  if (openConsult){
    openConsult.onclick = async ()=>{
      try{
        const name = prompt('Your name');
        if(!name) return;
        const email = prompt('Email');
        if(!email) return;
        const industry = prompt('Industry (Agriculture/Aviation/Marine/Energy/Construction/General)','General') || 'General';
        const notes = prompt('Notes (optional)','') || '';
        const payload = { name, email, lat, lon, industry, notes };
        const resp = await fetch('/api/consult', {
          method:'POST',
          headers:{'content-type':'application/json'},
          body:JSON.stringify(payload)
        });
        const j = await resp.json();
        if(!resp.ok) throw new Error(j && j.error ? j.error : 'Server error');
        showReport(j.consultation);
        loadConsultations();
      }catch(e){
        alert('Error: '+e.message);
      }
    };
  }

  function showReport(c){
    const body = document.getElementById('reportBody');
    body.innerHTML = '';
    const header = document.createElement('div');
    header.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
        <div>
          <div style="font-weight:600;">#${c.id} ${c.name}</div>
          <div style="font-size:12px;color:var(--muted);">
            ${c.industry} • ${new Date(c.createdAt).toLocaleString()}
          </div>
        </div>
        <div style="text-align:right;font-size:12px;color:var(--muted);">
          ${c.lat.toFixed(4)}, ${c.lon.toFixed(4)}
        </div>
      </div>`;
    const pre = document.createElement('pre');
    pre.textContent = c.report;
    body.appendChild(header);
    body.appendChild(pre);
    reportModal.style.display='block';
    modalPdf.dataset.cid = c.id;
  }

  closeModal.onclick = ()=> reportModal.style.display='none';
  modalPdf.onclick = ()=> {
    const id = modalPdf.dataset.cid;
    if(!id) return alert('No report selected');
    window.open(`/api/report_pdf?id=${id}`,'_blank');
  };

  // Download JSON of last weather
  if (downloadJSON){
    downloadJSON.onclick = ()=>{
      if(!lastWeather) return alert('No weather loaded');
      const blob = new Blob([JSON.stringify(lastWeather, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'weather.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    };
  }

  // Kick things off
  tryGeolocation();
  loadConsultations();
  loadRecent();
})();
</script>
</body>
</html>
"""

# ---------------- Weather Formatter ----------------
def build_weather_payload_from_open_meteo(data):
    current = data.get("current_weather", {}) or {}
    hourly = data.get("hourly", {}) or {}
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weathercode", [])
    humid = hourly.get("relativehumidity_2m", [])

    daily = data.get("daily", {}) or {}
    d_times = daily.get("time", [])
    d_tmax = daily.get("temperature_2m_max", [])
    d_tmin = daily.get("temperature_2m_min", [])
    d_codes = daily.get("weathercode", [])
    d_rain = daily.get("precipitation_probability_max", [])

    hourly_list = []
    for i in range(min(len(times), len(temps), 48)):
        try:
            dt = int(datetime.fromisoformat(times[i]).timestamp())
        except Exception:
            dt = 0
        hourly_list.append({
            "dt": dt,
            "temp": temps[i],
            "weather": [{"description": f"code:{codes[i]}"}]
        })

    daily_list = []
    for i in range(min(len(d_times), len(d_tmax), len(d_tmin), len(d_codes))):
        try:
            dt = int(datetime.fromisoformat(d_times[i]).timestamp())
        except Exception:
            dt = 0
        rain_prob = None
        if i < len(d_rain):
            rain_prob = d_rain[i]
        daily_list.append({
            "dt": dt,
            "temp_max": d_tmax[i],
            "temp_min": d_tmin[i],
            "code": d_codes[i],
            "rain_prob": rain_prob
        })

    return {
        "current": {
            "temp": current.get("temperature"),
            "feels_like": current.get("temperature"),
            "wind_speed": current.get("windspeed"),
            "humidity": humid[0] if humid else None,
            "pressure": None,
            "visibility": None,
            "weather": [{
                "description": f"code:{current.get('weathercode')}",
                "code": current.get("weathercode")
            }],
        },
        "hourly": hourly_list,
        "daily": daily_list,
        "alerts": []
    }


# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template_string(INDEX)


@app.route("/api/weather")
def api_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "temperature_2m,weathercode,relativehumidity_2m,windspeed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
            "timezone": "UTC",
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return jsonify(build_weather_payload_from_open_meteo(data))
    except Exception as e:
        return jsonify({"error": "Failed to fetch weather", "details": str(e)}), 502


@app.route("/api/consult", methods=["POST"])
def api_consult():
    payload = request.get_json() or {}

    name = payload.get("name")
    email = payload.get("email")
    lat = payload.get("lat")
    lon = payload.get("lon")
    industry = payload.get("industry", "General")
    notes = payload.get("notes", "")

    if not name or not email:
        return jsonify({"error": "name and email required"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return jsonify({"error": "lat/lon must be numbers"}), 400

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "temperature_2m,weathercode,relativehumidity_2m,windspeed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
        "timezone": "UTC",
    }
    r = requests.get(url, params=params, timeout=10)
    weather_payload = build_weather_payload_from_open_meteo(r.json())

    cid = len(consultations) + 1
    created = datetime.utcnow().isoformat() + "Z"

    cur = weather_payload["current"]

    risks = []
    if cur["temp"] and cur["temp"] > 35:
        risks.append("High temperature — heat stress risk.")
    if cur["wind_speed"] and cur["wind_speed"] > 12:
        risks.append("Strong winds — caution required.")
    if cur["humidity"] and cur["humidity"] > 80:
        risks.append("High humidity.")

    risk_text = "\n".join(["- " + r for r in risks]) if risks else "- No major hazards."

    report = f"""
Consultation Report #{cid}
Generated: {created}

Location: {lat}, {lon}
Industry: {industry}

Current Weather:
- Temp: {cur['temp']}°C
- Feels Like: {cur['feels_like']}°C
- Wind: {cur['wind_speed']} m/s
- Humidity: {cur['humidity']}%

Risk Assessment:
{risk_text}

Notes:
{notes or 'None'}

(This report is auto-generated.)
""".strip()

    entry = {
        "id": cid,
        "name": name,
        "email": email,
        "lat": lat,
        "lon": lon,
        "industry": industry,
        "notes": notes,
        "createdAt": created,
        "weather": weather_payload,
        "report": report,
    }

    consultations.append(entry)
    send_email(email, f"Your Consultation Report #{cid}", report)

    return jsonify({"ok": True, "consultation": entry})


@app.route("/api/consultations")
def api_consultations():
    return jsonify(list(reversed(consultations)))


@app.route("/api/report_pdf")
def api_report_pdf():
    if not REPORTLAB_AVAILABLE:
        return jsonify({"error": "PDF unavailable"}), 501

    cid = request.args.get("id", type=int)
    match = next((c for c in consultations if c["id"] == cid), None)
    if not match:
        return jsonify({"error": "not found"}), 404

    buf = io.BytesIO()
    p = rl_canvas.Canvas(buf, pagesize=letter)
    p.setFont("Helvetica", 10)

    y = 760
    for line in match["report"].split("\n"):
        p.drawString(40, y, line)
        y -= 14

    p.showPage()
    p.save()
    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name=f"consult_{cid}.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    print(f"[INFO] Starting server on port {PORT}, PDF enabled: {REPORTLAB_AVAILABLE}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
