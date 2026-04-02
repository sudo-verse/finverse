# AI-Stock Analysis Engine 🚀

An AI-powered stock discovery and event detection engine tailored for analyzing news and announcements (like NSE announcements). The system extracts named entities, performs sentiment analysis using Transformers (`pipeline`), triggers keyword-based signals, implements logical rules for BUY/SELL/HOLD recommendations, and optionally visualizes data with an interactive Streamlit dashboard.

## Features
- **Real-Time Data Extraction**: Scrapes, parses and pulls from NSE announcements via `nsepython`.
- **Entity & Sentiment Extraction**: Uses `spacy` to identify company names and `transformers` (BERT/RoBERTa) for sophisticated market sentiment detection.
- **Rules Engine & Strategy**: Combines structural event triggers with sentiment confidence to issue action signals (Buy/Sell/Hold).
- **Interactive Dashboard**: A simple user-friendly Streamlit frontend to consume and filter signals easily.

## Project Structure
```
ai-stock/
│
├── app/                  # Main Application logic
│   ├── ingestion/        # Modules to fetch NSE or MoneyControl news
│   ├── nlp/              # NER and sentiment analysis models
│   ├── engine/           # Event detection, algorithmic signal triggers
│   ├── market/           # Integration with yfinance stock pricing
│   ├── utils/            # Helper functions (storage, mappers, logging)
│   ├── config.py         # Global App Configurations
│   └── dashboard.py      # Streamlit Frontend UI
│   
├── notebooks/            # Scratchpads for exploration and model validation
│   ├── intraday.ipynb
│   ├── moneycontrol.ipynb
│   └── notebook.ipynb
│
├── requirements.txt      # Project library dependencies
├── .env                  # Environment Variables (Secrets)
└── .gitignore            # Git exclusion rules
```

## Setup Instructions

### 1. Requirements

Ensure you have Python 3.9+ installed.

### 2. Install Dependencies
Set up your virtual environment, then install the necessary libraries:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Install NLP Spacy Models
To parse English text for named entities, we use Spacy. Download the required model with:
```bash
python -m spacy download en_core_web_sm
```

### 4. Configure API Keys
Copy your `API_KEY` into a `.env` file at the root. (If you don't have one, create a file named `.env`).

*`.env` contents:*
```env
API_KEY=your_secured_news_or_platform_key_here
```

## Running the Application

**To run the primary NLP extraction and signal engine:**
```bash
# General Unified Engine
python -m app.main

# Real-Time NSE Engine
python -m app.main_nse
```

**To start the Streamlit Dashboard UI:**
```bash
streamlit run app/dashboard.py
```

## Contributing
Please branch out, open PRs, and follow standard Python formatting if contributing features or fixes back to this repository. Make sure not to commit data dumps (`*.csv`, `*.xlsx`) or the `.env` file!
