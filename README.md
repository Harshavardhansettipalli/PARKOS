# PARKOS — Smart Parking Management System

## Color Palette
| Token     | Hex       | Role                              |
|-----------|-----------|-----------------------------------|
| Void      | `#091413` | Background, base surface          |
| Deep      | `#285A48` | Buttons, headers, accents         |
| Mid       | `#408A71` | Slot grid, interactive elements   |
| Mint      | `#B0E4CC` | Highlights, values, KPIs          |

---

## Project Files
```
PARKOS/
├── index.html          ← Full web UI (open in any browser — no server needed)
├── parking_system.py   ← Python backend + Flask REST API
├── requirements.txt    ← pip dependencies
└── README.md
```

---

## Quick Start

### Option A — Web UI only (no Python needed)
Just open `index.html` in any modern browser. All logic runs in the browser.

### Option B — Run the Python REST API
```bash
# Install dependencies
pip install -r requirements.txt

# Start Flask server (runs on http://localhost:5000)
python parking_system.py
```

### Option C — CLI demo
```bash
python parking_system.py
```
Runs a built-in demo with sample vehicles and prints results to the terminal.

---

## REST API Endpoints
| Method | Endpoint          | Description                        |
|--------|-------------------|------------------------------------|
| POST   | `/api/park`       | Park a vehicle                     |
| POST   | `/api/exit`       | Process exit & calculate fee       |
| GET    | `/api/slots`      | All slot statuses                  |
| GET    | `/api/stats`      | Occupancy & revenue summary        |
| GET    | `/api/tickets`    | All transactions (filter by status)|

**Park a vehicle:**
```bash
curl -X POST http://localhost:5000/api/park \
  -H "Content-Type: application/json" \
  -d '{"vehicle_number": "TN38AB1234"}'
```

**Process exit:**
```bash
curl -X POST http://localhost:5000/api/exit \
  -H "Content-Type: application/json" \
  -d '{"vehicle_number": "TN38AB1234"}'
```

---

## Fee Structure
| Duration         | Charge              |
|------------------|---------------------|
| ≤ 15 minutes     | **FREE** (grace)    |
| First hour       | **₹50.00** flat     |
| Each extra hour  | **₹40.00 / hr**     |

---

## Run Commands Summary
```bash
# Navigate into the folder
cd PARKOS

# Install Python deps
pip install -r requirements.txt

# Start the backend
python parking_system.py

# Open the UI (macOS)
open index.html

# Open the UI (Windows)
start index.html

# Open the UI (Linux)
xdg-open index.html
```
