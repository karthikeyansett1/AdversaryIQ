# AdversaryIQ — Start Here

This is the complete standalone AdversaryIQ project. It is built to run on Streamlit Community Cloud, with hosted OpenAI Responses API inference using a visitor-provided key. No local inference server is needed.

## 1. Run locally for development (optional)

```bash
cd AdversaryIQ
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

## 2. Use the live model

Enter your own OpenAI API key in the sidebar. In Attack Studio select AIQ-001, the baseline policy, and run one investigation. View the actual `execute_probe` trace and download the resulting evidence.

## 3. Publish

See `DEPLOYMENT_CHECKLIST.md` for exact GitHub and Streamlit Cloud steps. GitHub repo and live app URLs should be added only after they actually exist.

## Budget note

Each experiment can use up to five provider requests. A three-attempt per-session UI control does not guarantee a global spending limit. Do not publish your API key or supply an owner-funded unrestricted key to a public app.
