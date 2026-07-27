# Oilseeds Model Integration Scripts

This repository contains the backend scripts and APIs for the Agricultural Intelligence platform. It provides a FastAPI-based machine learning service to predict crop yields, prices, risks, and profitability, assisting in optimal crop recommendations.

## Project Structure

- `agri-intel-api/`: Contains the FastAPI application and model serving logic.
- `agri_backend/`: Contains additional backend scripts and integration logic.

## Prerequisites

- Python 3.8 or higher
- `pip` (Python package manager)
- Virtual Environment (recommended)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Bhavikpim123/oilseeds-model-integration-scripts.git
   cd oilseeds-model-integration-scripts
   ```

2. **Navigate to the API folder:**
   ```bash
   cd agri-intel-api
   ```

3. **Create and activate a virtual environment:**
   - **Windows:**
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

4. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Model Placement

Machine learning models (`.pkl` files) are intentionally excluded from version control to keep the repository size manageable and for security reasons.

Before running the API, ensure you place the required pre-trained `.pkl` models inside the `agri-intel-api/models/` directory:
- `yield_model.pkl`
- `price_model.pkl`
- `risk_model.pkl`
- `crop_reco_model.pkl`
- `soil_suit_model.pkl`
- `profit_model.pkl`
- `production_model.pkl`

## Running the API Locally

1. From within the `agri-intel-api` directory, start the server using `uvicorn`:
   ```bash
   uvicorn app:app --reload
   ```

2. Open your browser and navigate to:
   - **API Base:** `http://127.0.0.1:8000/`
   - **Interactive API Docs (Swagger UI):** `http://127.0.0.1:8000/docs`

## Configuration

Sensitive configuration files (e.g., `.env`) and deployment descriptors (e.g., `render.yaml`) are ignored in Git to prevent accidental exposure of secrets. Ensure you create your own `.env` locally if required by the backend.
