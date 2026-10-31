# AdversaryIQ — deployment checklist

## Local validation

```bash
cd AdversaryIQ
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

The unit tests should complete without contacting the OpenAI API.

## GitHub preparation

- [ ] No real API key in any file or screenshot.
- [ ] `.env`, `.streamlit/secrets.toml`, `.venv/` are not included in the commit.
- [ ] README repository placeholder is updated only after the actual GitHub repository exists.
- [ ] Screenshots show this application's interface and no credentials.

## Publish

```bash
git init
git branch -M main
git add .
git status
git commit -m "Initial AdversaryIQ security workbench"
git remote add origin https://github.com/YOUR-USERNAME/AdversaryIQ.git
git push -u origin main
```

Create the empty GitHub repository first. If `origin` already exists, use `git remote set-url origin <actual URL>` instead of `git remote add origin`.

## Streamlit Community Cloud

- Connect GitHub repository, branch `main`.
- Main file: `app.py`.
- Python: 3.12 where available.
- Streamlit Secrets: **none necessary**.
- On the deployed public URL, confirm Mission Control, Case Library, and Method & Evidence load without a key.
- Use your private BYOK field to conduct **one** hosted run and verify `execute_probe` in its actual trace.
- Download the actual JSON and Markdown evidence. Never publish synthetic or mocked fixtures as real hosted measurements.
- Update the README demo link to the real deployed URL and push the change.

## Budget/production note

Three runs per session are an interface-level convenience, **not** a global security boundary. There is no server-side shared owner key, request queue, persistent user authentication, or guaranteed cost ceiling. If offering a production public service with an owner-funded key, implement authenticated quotas, billing-level controls, and server-side monitoring first.
