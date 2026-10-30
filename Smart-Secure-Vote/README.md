# Smart Secure Vote – AI-Based Secure Serverless Voting System

A B.Tech college-project demo of an online voting system.
Voters are **pre-registered by an administrator** (there is no public sign-up), verify with **Voter ID + SMS OTP**, vote **exactly once**, and receive a confirmation SMS. Every step is audit-logged and watched by **rule-based checks plus a scikit-learn IsolationForest** model. The backend is built to run locally *or* serverless on AWS (Lambda + API Gateway + KMS + SNS, deployed with AWS SAM).

> **All data is fake.** Demo voters (`VOT1001`–`VOT1008`) and phone numbers (`+1555555010x`) are invented. Do not use this project for a real election.

---

## 1. Feature status (read this first)

| Feature | Status |
|---|---|
| React + Vite frontend, navy/white responsive UI (Home, Verify, OTP, Vote, Confirmation, Admin login, Admin dashboard) | Implemented |
| FastAPI backend, SQLAlchemy, PostgreSQL with automatic **SQLite fallback** | Implemented |
| No public voter registration; admin adds voters one by one or by **CSV import** | Implemented |
| Voter ID + OTP verification (6-digit, HMAC-hashed, 5 min expiry, 3 attempts, single use) | Implemented |
| One vote per voter: backend check + atomic claim + `UNIQUE(votes.voter_pk)` DB constraint | Implemented |
| Vote confirmation SMS (mock provider for local use, **AWS SNS** provider) | Mock: implemented and used in tests. SNS: implemented, **not tested against real AWS** |
| Admin login (scrypt password hash, JWT, lock-out after 5 failures), candidate management, audit logs, security alerts | Implemented |
| Rule-based detection (OTP brute force, ID guessing, many voters from one IP, duplicate vote attempts, admin brute force) | Implemented |
| AI scan: IsolationForest scoring per-IP activity (admin clicks **Run AI scan**) | Implemented, but trained on **synthetic** data only (demo quality, not production-validated) |
| AWS SAM template: Lambda (container image), API Gateway HTTP API, IAM role, KMS key, Secrets Manager | Written and YAML-parsed; **never deployed** in my build environment |
| Docker + Docker Compose (PostgreSQL + API + nginx-served frontend) | Written; **never built/run** in my build environment |
| Automated pytest backend tests | Written (see section 8 for what was and was not executed) |

**Not implemented / needs external services**
* Real SMS needs an AWS account with SNS SMS enabled (new accounts start in the *SMS sandbox*; sending to India may also require DLT registration). Use `SMS_PROVIDER=mock` for the demo.
* The SAM template does **not** create the database or host the frontend. You supply a PostgreSQL URL (e.g. Amazon RDS) and host the built frontend yourself (S3/CloudFront, Amplify, Netlify…).
* The AI scan runs on demand from the dashboard. It is not scheduled automatically.
* No email, no database migrations tool (tables are created automatically with `create_all`), no HTTPS termination (use API Gateway / a reverse proxy).
* Ballot secrecy is limited: the `votes` table links a voter row to a candidate (needed for the simple UNIQUE constraint). An administrator with direct database access could therefore see who voted for whom. The UI, SMS messages and audit logs never reveal the choice. A real system would use a more elaborate anonymous-ballot design.

---

## 2. Project structure

```
smart-secure-vote/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, security headers, bootstrap (tables, first admin, demo data)
│   │   ├── config.py          all settings from environment variables
│   │   ├── database.py        SQLAlchemy engine (PostgreSQL or SQLite fallback)
│   │   ├── models.py          Voter, Candidate, Vote (UNIQUE per voter), OTPCode, AuditLog, SecurityAlert, Admin
│   │   ├── security.py        scrypt password hashing, OTP HMAC, JWT
│   │   ├── routes_voter.py    verify, OTP, candidates, vote
│   │   ├── routes_admin.py    login, stats, candidates, voters, CSV import, audit logs, alerts, AI scan
│   │   ├── monitoring.py      audit logging + rule-based detection + AI scan orchestration
│   │   ├── ml.py              IsolationForest (scikit-learn)
│   │   ├── sms.py             mock + AWS SNS
│   │   ├── seed.py            fake demo data
│   │   └── lambda_handler.py  AWS Lambda entry point (Mangum)
│   ├── tests/                 pytest suite
│   ├── requirements.txt / requirements-dev.txt
│   ├── Dockerfile / Dockerfile.lambda
│   └── .env.example
├── frontend/                  React + Vite app (src/pages/*, src/api.js, styles.css)
├── samples/voters_sample.csv  example CSV for import
├── template.yaml              AWS SAM template
├── docker-compose.yml
├── .env.example               variables for docker compose
└── README.md
```

---

## 3. Windows 11 setup (local, no Docker)

### Prerequisites
* **Python 3.12** (https://www.python.org/downloads/ – tick *Add python.exe to PATH*)
* **Node.js 20 or newer** (https://nodejs.org – LTS)
* Optional: Docker Desktop (section 6), PostgreSQL (section 5), AWS CLI + SAM CLI (section 9)

Open **PowerShell** and check:
```powershell
py --version
node --version
```

### Backend (terminal 1)
```powershell
cd smart-secure-vote\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```
If PowerShell refuses to run `Activate.ps1`, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

Recommended: put a real random secret into `backend\.env`:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Paste the output after `JWT_SECRET=` in `backend\.env`.

Start the API (creates the SQLite database, the admin account and the demo data automatically):
```powershell
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### Frontend (terminal 2)
```powershell
cd smart-secure-vote\frontend
npm install
npm run dev
```
Open **http://localhost:5173**. Vite proxies `/api` to the backend on port 8000.

---

## 4. Demo walkthrough and credentials

| What | Value |
|---|---|
| Admin URL | http://localhost:5173/admin/login |
| Admin username | `admin` |
| Admin password | `ChangeMe-Demo-123` (demo value from `.env.example` – change it in `.env` *before the first start*; it is only read when no admin exists yet) |
| Demo voter IDs | `VOT1001` … `VOT1008` |

1. Open **Vote**, enter `VOT1001`. With `EXPOSE_DEMO_OTP=true` the OTP is shown on the next page (and printed in the backend console as a `[MOCK SMS]` line). Real mode never shows it.
2. Enter the OTP, choose a candidate, review, confirm. You get a receipt code; the backend console prints the mock confirmation SMS (it never contains your choice).
3. Try voting again with `VOT1001`: blocked (409). Check **Admin → Security alerts** for the duplicate-attempt alert.
4. In the admin dashboard: see live results, add/remove candidates, add voters, import `samples\voters_sample.csv`, read the audit log, close/reopen voting.
5. **Attack demo:** on the Verify page enter wrong IDs repeatedly (e.g. `HACK0001`, `HACK0002`…) or give wrong OTPs three times, then open **Security alerts**: rule-based alerts appear automatically. Click **Run AI scan** to let the IsolationForest score the recent activity per IP (it needs at least 8 events from one IP in the last hour before it will flag anything).

---

## 5. Using PostgreSQL locally (optional)

SQLite is used when `DATABASE_URL` is empty. For PostgreSQL create a database, then set in `backend\.env`:
```
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/smartsecurevote
```
Restart uvicorn. Tables are created automatically.

---

## 6. Docker Compose (PostgreSQL + API + frontend)

```powershell
cd smart-secure-vote
copy .env.example .env
```
Edit `.env`: set `POSTGRES_PASSWORD` (letters/digits only) and `JWT_SECRET` (see the command in section 3). Then:
```powershell
docker compose up --build
```
* App: http://localhost:8080 (nginx serves the frontend and proxies `/api`)
* API docs: http://localhost:8000/docs

Stop with `Ctrl+C`; remove containers and data with `docker compose down -v`.

---

## 7. Configuration (environment variables)

Nothing secret is stored in source code. See `backend/.env.example` for every variable. The important ones:

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | Empty = SQLite. Otherwise a PostgreSQL URL. |
| `JWT_SECRET` / `JWT_SECRET_ARN` | Token signing key, or (AWS) the ARN of a Secrets Manager secret. Required when `APP_ENV=production`. |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | First admin, created only if no admin exists. Must be ≥ 8 chars with letters and digits. |
| `SMS_PROVIDER` | `mock` (console) or `sns` (AWS SNS). |
| `EXPOSE_DEMO_OTP` | Shows the OTP in the UI for demos. Automatically ignored when `APP_ENV=production` or `SMS_PROVIDER=sns`. |
| `SEED_DEMO_DATA` | Create fake candidates/voters on first start. Ignored in production. |
| `CORS_ORIGINS` | Allowed frontend origins. |

Manual seeding (if `SEED_DEMO_DATA=false`): `python -m app.seed` from `backend`.

---

## 8. Tests

```powershell
cd smart-secure-vote\backend
.\.venv\Scripts\Activate.ps1
pytest -v
```
The tests use a temporary SQLite database, the mock SMS provider and fake data only. They cover: password hashing, OTP hashing, JWT role separation, the full voting flow, confirmation SMS content, duplicate-vote blocking (API **and** the raw DB unique constraint), OTP expiry / single use / lock-out, input validation, admin authorisation, candidate management, CSV import validation, audit logging, rule-based alerts and the AI scan.

**What was actually executed when this project was generated:** the sandbox had no internet, so `pip install fastapi sqlalchemy pytest …` and `npm install` were impossible. I therefore could **not** run the API tests, the Vite build, Docker or SAM. I did verify: all Python files compile; the five pure-Python tests (`tests/test_security.py`: password hashing, password policy, OTP hashing, JWT roles/tampering/expiry, IsolationForest flags an attack pattern and ignores normal behaviour) pass; every React page compiles and renders with React's server renderer; and `template.yaml` / `docker-compose.yml` parse as valid YAML. Please run `pytest -v` yourself and treat any failure as a bug to fix – the first full run on your machine is the real test.

---

## 9. AWS deployment (SAM)

Architecture: **React app → API Gateway (HTTP API, throttled) → Lambda (container image running FastAPI via Mangum) → PostgreSQL**; **SNS** for SMS; **KMS** key encrypts Lambda environment variables and the generated JWT secret in **Secrets Manager**; a least-privilege **IAM role** allows only SNS publish, reading that one secret and using that one key.

A container image is used because scikit-learn + numpy + scipy exceed Lambda's 250 MB zip limit.

Prerequisites: AWS account, AWS CLI (`aws configure`), AWS SAM CLI, Docker Desktop (running), and a reachable PostgreSQL database (e.g. an RDS instance, or any hosted PostgreSQL that accepts connections from Lambda).

```powershell
cd smart-secure-vote
sam build
sam deploy --guided
```
`sam deploy --guided` asks for the parameters: `DatabaseUrl` (e.g. `postgresql+psycopg2://user:password@host:5432/dbname`), `AdminUsername`, `AdminPassword`, `CorsOrigins` (your frontend URL), `SmsProvider` (`sns`, or `mock` for a dry run). `DatabaseUrl` and `AdminPassword` are `NoEcho`; do not commit `samconfig.toml` if it contains them. The stack outputs `ApiUrl`.

Check it: open `<ApiUrl>/docs` or `<ApiUrl>/api/health`.

Frontend:
```powershell
cd frontend
$env:VITE_API_URL = "https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com"
npm run build
```
Upload `frontend\dist` to S3 static hosting/CloudFront, Amplify or any static host, then redeploy with that site's URL in `CorsOrigins`.

SMS notes: SNS accounts begin in a sandbox where you may only text verified numbers. Request production access and (for India) complete any required sender/template registration. The function's SNS permission is `Resource: "*"` because SNS requires it for direct phone publishing.

If the database is inside a VPC, add a `VpcConfig` to the function (not included). Remove everything with `sam delete`.

---

## 10. Security design summary

* Passwords: scrypt with a random salt; constant-time comparison; dummy hash run for unknown usernames.
* OTPs: random 6 digits, stored only as an HMAC-SHA256 (keyed with `OTP_PEPPER`/`JWT_SECRET`), expire, single use, max 3 attempts, resend cooldown.
* Tokens: short-lived JWTs with a `role` claim (a voter token cannot call admin endpoints and vice versa).
* Input validation with Pydantic on every endpoint; SQL via SQLAlchemy parameters (no string-built SQL); React escapes output.
* Rate limits: per-IP limit on verification, admin login lock-out, API Gateway throttling on AWS.
* One vote per voter: `UPDATE voters SET has_voted=true WHERE has_voted=false` (atomic) + `UNIQUE(votes.voter_pk)`.
* Errors: unexpected errors return a generic 500 and are logged server-side only. Security headers are set on API responses.
* Audit log never stores OTPs, passwords or the chosen candidate.

---

## Important implementation note for this GitHub upload

The `backend/`, `frontend/` and `samples/` folders in this archive were generated as a starter implementation to complete the folder structure. They are **not verified to implement every feature in the original feature-status table above**.

The current starter supports a basic local demo flow: demo voter ID lookup, mock OTP, candidate selection, one-vote database constraint, receipt generation, basic admin login and results endpoint. It does not yet include all of the advanced security, audit, AI/IsolationForest, CSV import, production authentication, real SMS or tested AWS deployment features described earlier. See `PROJECT_NOTES.md` before publishing or demonstrating the project.

Do not use this starter for a real election or expose it publicly as a production voting system. Test it locally and revise feature claims to match what you have actually tested.
