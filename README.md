# 🔥 FIRE Calculator — Edelweiss Themed (Streamlit)

A simple, India-ready **FIRE (Financial Independence, Retire Early)** calculator built with Streamlit, themed with **Edelweiss Life Insurance** colours.

## ✨ Features
- Lean / Barista / Fat FIRE modes
- Income, inflation, income growth, SIP growth
- Safe Withdrawal Rate (SWR) slider
- Earliest-FI detection + Coast-FIRE check
- Corpus vs Required Corpus chart (Altair)
- Edelweiss blue/orange theme (config + CSS)

---

## 📁 Project Structure
```
.
├── fire_app_eli.py                # Streamlit app
├── requirements.txt
├── .streamlit/
│   └── config.toml               # Theme (Edelweiss colours)
├── Dockerfile                    # Optional: containerized deploy
├── app_entry.sh                  # Entrypoint for Docker (or PaaS)
├── render.yaml                   # Optional: Render.com one-click deploy
└── README.md
```

---

## 🖥️ Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run fire_app_eli.py
```
Streamlit will open on `http://localhost:8501`.

---

## ☁️ Deploy Options

### 1) Streamlit Community Cloud (fastest)
1. Push these files to a public Git repo (GitHub/GitLab).
2. Go to **streamlit.io → Deploy an app** and connect the repo.
3. Set **Main file path** to `fire_app_eli.py`.
4. (Optional) Add `SECRETS` if needed — *not required for this app*.

> Streamlit Cloud auto-installs packages from `requirements.txt` and picks up theme from `.streamlit/config.toml`.

---

### 2) Render.com (free tier friendly)
1. Push to GitHub.
2. On Render, create a **Web Service** → **Build & deploy from repo**.
3. Render will read `render.yaml` for build/run commands.

**If you prefer manual setup**  
- Build Command: `pip install -r requirements.txt`  
- Start Command: `./app_entry.sh`

---

### 3) Docker (any server)
Build and run:
```bash
docker build -t fire-app .
docker run -p 8501:8501 -e PORT=8501 fire-app
```
Then open `http://localhost:8501`.

---

## 🔧 Configuration

### Theme
We pin the palette both via `.streamlit/config.toml` and a small CSS block in the app for accents.
- **Primary Blue:** `#034EA2`
- **Accent Orange:** `#F79421`
- **Background:** `#F9FAFB`
- **Text:** `#1F2937`

### Ports
- Streamlit defaults to **8501**. On PaaS (Render/Cloud Run), the platform sets `PORT`. Our Docker entrypoint respects `$PORT` automatically.

---

## 🧪 Health check
If deploying behind a load balancer (Render/NGINX), expose `/` on the service to allow health checks.

---

## 📝 Notes
- This tool is **educational**, not investment advice.
- Feel free to rename the app file; update the commands accordingly.
- For custom logos, place a PNG/SVG and I’ll wire it into the header and as a favicon.

---

## 🐛 Troubleshooting
- **App boots but shows 404 on PaaS:** Ensure the process binds to `0.0.0.0` and uses `$PORT`.
- **Charts not rendering:** Some hardened environments block WebGL; Altair will fall back to SVG.
- **Module not found:** Confirm `requirements.txt` is deployed.
