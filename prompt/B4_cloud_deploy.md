Read `CONTEXT_B.md` and `CONTRACT.md` first. `server/`, `dashboard/` and `kb/billing_app.md` already exist and work locally.
Don't change any API path or field. CONTRACT.md stays exactly the same.

TASK B4: Put the session server + dashboard on the internet, so FixPilot.exe on ANY PC (any wifi) can connect with a code.
Primary: Google Cloud Run. Backup: a Cloudflare quick tunnel. Build both, so the demo never depends on one.

## 1. Make the server cloud-ready (small edits only)
- Port: read `PORT` from the env (default 9000). Cloud Run sets PORT=8080.
- Paths: the kb/ and dashboard/ paths must be resolved from `__file__` (they must work inside the container).
- Add a `GET /version` → {"version": "<git short sha or 'dev'>", "started_at": ...} so we can see which build is live.
- Optional shared secret: if env `FIXPILOT_TOKEN` is set, every POST except `/sessions` must carry the header
  `X-FixPilot-Token: <token>`, otherwise 401. If it's not set, no check (local dev stays easy). Add this to the contract notes
  for Person A as an OPTIONAL header. Do NOT change any paths.

## 2. Container
- `Dockerfile` at the repo root: python:3.11-slim. Copy ONLY server/, dashboard/, kb/. pip install -r server/requirements.txt.
  CMD: `uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8080}` (use the sh -c form so ${PORT} expands).
- `.dockerignore`: .venv, .env, logs, agent, app, pitch, prompts, *.md except kb/*.md, .git.
- Test locally if Docker is installed: `docker build -t fixpilot-server . ; docker run -p 9000:8080 fixpilot-server`.
  If Docker isn't installed, skip it. Cloud Run builds from source anyway.

## 3. Deploy to Cloud Run: `server/deploy_cloudrun.ps1`
Write the script AND explain each command to me before running anything. I'll run the login myself.
```
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy fixpilot-server --source . --region asia-south1 --allow-unauthenticated `
  --min-instances 1 --max-instances 1 --memory 512Mi --set-env-vars FIXPILOT_TOKEN=<optional>
```
IMPORTANT: sessions live in memory, so the server must run as exactly ONE instance (min 1, max 1). Otherwise a code created on
one instance won't be found on another. Explain this in a comment in the script.
asia-south1 = Mumbai (lowest latency for India). At the end, print the service URL.
If gcloud isn't installed, give me the download link and the exact steps, and wait.

## 4. Backup: Cloudflare quick tunnel `server/tunnel.ps1`
- Uses `cloudflared` (free, no account needed): `cloudflared tunnel --url http://localhost:9000`.
- The script: check cloudflared exists (if not, print the winget command `winget install --id Cloudflare.cloudflared`), start the
  local server if it isn't running, start the tunnel, and print the https://*.trycloudflare.com URL in BIG text.

## 5. Update the test script
`server/test_flow.ps1` must accept `-BaseUrl https://...` and must pass against BOTH the Cloud Run URL and the tunnel URL.

## Done when
1. `server/test_flow.ps1 -BaseUrl <cloud-run-url>` → all PASS.
2. The dashboard opens at `<cloud-run-url>/` from a PHONE on mobile data (proves it works from any network).
3. `server/tunnel.ps1` prints a trycloudflare URL, and test_flow passes against it too.
4. `<url>/version` shows the version.
Finally, write `server/DEPLOY.md` (max 20 lines): the live URL, how to redeploy, how to start the tunnel backup, and the env vars.
Then tell me the URL so I can send it to Person A (he puts it in SERVER_URL for FixPilot.exe).
