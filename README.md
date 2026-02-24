# FIFO Shipping

A web-based warehouse shipping management application for Vintech Plastics. It enforces First-In-First-Out (FIFO) inventory compliance when loading containers onto shipments, integrating directly with the Plex ERP system.

## Features

- **Shipper Selection** - Browse open shipper orders within a configurable date range
- **FIFO Container Loading** - View available containers sorted oldest-first and scan them onto shipments
- **Barcode Scanner Support** - Scan container serial numbers with automatic validation and audio/visual feedback
- **Master Unit Handling** - Scan master units (prefix "M") to process bulk container shipments
- **ERP Integration** - Real-time reads and writes against Plex ERP datasources for container location updates and shipment loading

## Tech Stack

- **Backend**: FastAPI, Uvicorn, Python 3.11
- **Frontend**: HTML5, JavaScript, Bootstrap 5.3.3, Jinja2 templates
- **Data**: Pandas, Plex ERP API (no local database)
- **Deployment**: GitHub Actions CI/CD to Azure Web Apps

## Project Structure

```
FIFO_Shipping/
├── main.py                        # FastAPI application
├── requirements.txt               # Python dependencies
├── web.config                     # IIS reverse proxy config (Azure)
├── backend/
│   ├── data.py                    # ERP data fetch test script
│   └── test.py                    # Unit tests
├── templates/
│   ├── index.html                 # Shipper selection page
│   └── shipper_containers.html    # Container scanning page
├── static/
│   ├── index.js                   # Shipper selection logic
│   ├── index.css
│   ├── shipper_containers.js      # Scanning and validation logic
│   ├── shipper_containers.css
│   └── assets/                    # Logo, sounds, favicon
└── .github/workflows/
    └── update_fifoshipping.yml    # Azure deployment workflow
```

## Setup

### Prerequisites

- Python 3.11+
- Access to Plex ERP API

### Installation

```bash
git clone <repository-url>
cd FIFO_Shipping
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running Locally

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in a browser.

## Application Flow

1. User opens the app and sees a list of open shippers
2. User selects a shipper to view its parts and available containers (FIFO sorted)
3. Warehouse staff scans a container serial number
4. The system validates the scan against the FIFO list
5. On success: updates the container location in ERP, plays a success sound, and clears the scanner
6. On error: plays an error sound and displays an alert

## FIFO Logic

The `get_valid_containers()` function in `main.py` determines which containers are eligible for scanning:

1. Filters containers by part number
2. Sorts by `Add_Date` (oldest first)
3. Includes containers up to the demand quantity
4. Extends the window to include containers within 3 days of the cutoff
5. Only these containers are accepted during scanning

## Deployment

Pushes to the `update` branch trigger automatic deployment to Azure via GitHub Actions. The app runs behind IIS as a reverse proxy to Uvicorn on port 8000.
