# AI-Powered-Customer-Review-Insights


<img width="932" height="477" alt="Screenshot 2025-08-27 161447" src="https://github.com/user-attachments/assets/1ab10183-3947-4b98-9691-843e25a77596" />


# AI-Powered Review Insights (Streamlit Multi-Tab Dashboard)

## Overview
This project provides a Streamlit dashboard to ingest customer reviews, analyze sentiment & topics, extract problems & suggestions, and export enriched data.

## Files
- `app.py` - Main Streamlit multi-tab dashboard
- `data_ingester.py` - Handles JSON/CSV/TXT ingestion and simple normalization
- `review_analyzer.py` - Runs sentiment & zero-shot topic pipelines and rule-based extractors
- `utils.py` - Helper functions for rating parsing and rule-based heuristics
- `sample_reviews.json` - Example reviews to test the app
- `requirements.txt` - Python dependencies

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Prerequisites
Python 3.8 or higher

pip package manager

Installation
bash
# Clone the repository
'''git clone https://github.com/BhushanMasters/AI-Powered-Customer-Review-Insights.git

# Navigate to project directory
cd AI-Powered-Customer-Review-Insights

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
Running the Application
bash
# Start the Streamlit dashboard
streamlit run app.py '''

## Notes
- First run will download Hugging Face models (internet required).
- If you want to avoid model downloads, edit `review_analyzer.py` to skip pipeline creation or use smaller/local models.
