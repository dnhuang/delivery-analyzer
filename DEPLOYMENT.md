# Deployment Guide — 上海好吃米道

## Overview

The app is deployed via **Streamlit Community Cloud**, which pulls directly from the GitHub repository and redeploys automatically on every push to `main`. The password is stored securely in Streamlit Cloud's secrets manager — never in the repo.

---

## One-Time Setup

### 1. Merge `dev` into `main`

Streamlit Cloud deploys from `main`. Before deploying, ensure all changes are merged:

```bash
git checkout main
git merge dev
git push
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **"New app"**
3. Select the repository: `dnhuang/delivery-analyzer`
4. Set the main file path: `app.py`
5. Click **"Deploy"**

### 3. Configure the Password Secret

The app reads the password from Streamlit secrets in production. After deploying:

1. In the Streamlit Cloud dashboard, open your app
2. Go to **Settings → Secrets**
3. Add the following:
   ```toml
   password = "your_password_here"
   ```
4. Click **Save** — the app will restart automatically

The app falls back to `config.json` for local development, so no changes to the code are needed.

---

## Updating the App

Push changes to `main` and Streamlit Cloud redeploys automatically:

```bash
git checkout main
git merge dev
git push
```

---

## Updating the Password

1. Go to Streamlit Cloud dashboard → your app → **Settings → Secrets**
2. Edit the `password` value
3. Save — the app restarts with the new password

---

## Updating the Menu (`data/menu.csv`)

`menu.csv` is committed to the repo and loaded at runtime. To add or edit food items:

1. Edit `data/menu.csv` locally — add rows with `id`, `item_zh`, `item_short_zh`, `item_en`
2. Commit and push to `main`
3. Streamlit Cloud redeploys automatically

---

## Files Required in the Repo

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit entry point |
| `analyzer.py` | Parsing and analysis logic |
| `requirements.txt` | Python dependencies |
| `data/menu.csv` | Food item reference list |
| `.streamlit/config.toml` | Theme configuration |

**Not in the repo (gitignored):**
- `config.json` — local dev password
- `data/*.xlsx` — uploaded Excel files

---

## Troubleshooting

**App won't start** — check the deployment logs in the Streamlit Cloud dashboard for import errors or missing files.

**Password not working** — verify the secret is saved as `password = "..."` (TOML format) with no extra spaces or quotes issues.

**Orders not parsing** — ensure the uploaded file is a raw WeChat export `.xlsx`. The app validates structure and will show an error if the format is wrong.

**Item totals mismatch warning** — the parser found discrepancies between parsed quantities and the WeChat summary table. Check if `menu.csv` is missing any items that appear in the export.
