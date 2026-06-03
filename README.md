# Minimal QC Data API Test

## Install

```bash
pip install -r requirements.txt
```

## Start API

```bash
uvicorn data_api:app --reload --port 8001
```

Test:

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/results
```

## Start Streamlit

```bash
streamlit run app.py
```

Results are written to:

```text
data/minimal_results.csv
```
