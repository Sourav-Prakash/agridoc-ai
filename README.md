# AgriDoc AI: AI-Powered Crop Disease Diagnosis & Remedy Advisor 🌾🔬

AgriDoc AI is an intelligent agricultural extension tool that allows farmers, agronomists, and gardeners to capture or upload images of diseased crops, instantly identifies the plant and pathogen using Google Gemini Multimodal Vision, and prescribes actionable chemical medicines (with exact dosages), organic remedies, and preventive agronomic practices.

---

## Key Features

- 📸 **Live Camera Capture**: Real-time camera viewfinder with smartphone front/rear camera switching (`facingMode: environment`) and leaf alignment guides.
- 📁 **Instant File Upload**: Drag-and-drop or select photos from your device (JPEG, PNG, WEBP up to 20MB).
- 🧠 **Google Gemini Vision AI**: Uses `gemini-2.5-flash` with structured Pydantic schemas for reliable, hallucination-resistant crop diagnosis.
- 💊 **Exact Agrochemical Dosages**: Recommends commercial and generic fungicides/insecticides with precise dilution rates (e.g. `2.5 g / Liter`), spray timing, and Pre-Harvest Intervals (PHI).
- 🌿 **Organic & Biological Solutions**: Eco-friendly remedies (cold-pressed neem oil recipes, Trichoderma viride, bio-fungicides) to combat pathogen resistance.
- 🛡️ **Agronomic Prevention**: Cultural guidelines including drip irrigation, leaf pruning, canopy aeration, and crop rotation.
- 🖨️ **Printable Prescription Card**: Formatted agricultural pharmacy prescription sheet ready to print or save as PDF to present at local agricultural supply stores.
- 🔑 **Dual API Key Management**: Automatic loading from `.env` or dynamic updates through the in-app Settings modal.

---

## Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Install Dependencies
Open PowerShell or your terminal in this project directory:
```powershell
pip install -r requirements.txt
```

### 3. Configure Gemini API Key
You can obtain a free Gemini API key at [Google AI Studio](https://aistudio.google.com/).

Option A: Add it to your `.env` file:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
Option B: Launch the app and paste your API key directly into the in-app **Settings** modal.

### 4. Run the Application
```powershell
python -m uvicorn app:app --port 8000 --reload
```
or run:
```powershell
python app.py
```

### 5. Open in Browser
Navigate to:
```
http://127.0.0.1:8000
```
On mobile devices on the same local network, access `http://<your-computer-ip>:8000`.

---

## Project Structure

```
ANTIGRAVITY-WORKSHOP/
├── app.py                 # FastAPI backend, Gemini vision client, Pydantic schemas & routes
├── requirements.txt       # Python dependencies (FastAPI, uvicorn, google-genai, pillow, etc.)
├── .env.example           # Environment template
├── .env                   # Local configuration (holds GEMINI_API_KEY)
├── README.md              # Project documentation and usage guide
└── static/
    ├── index.html         # Responsive web dashboard with camera & upload interfaces
    ├── app.js             # Camera capture, upload handler, API integration & DOM rendering
    └── styles.css         # Camera viewfinder, badge styling & print prescription CSS
```

---

## Safety Disclaimer
AgriDoc AI provides guidance based on computer vision models. Always verify local pesticide regulations, follow agrochemical safety label instructions, wear personal protective equipment (PPE), and respect Pre-Harvest Intervals before harvesting crops for human consumption.
