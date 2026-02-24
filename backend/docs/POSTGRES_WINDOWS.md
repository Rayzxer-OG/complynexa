# Install PostgreSQL on Windows

Follow these steps to install PostgreSQL for the Compliance Tracker backend.

## 1. Download the installer

1. Open: **https://www.enterprisedb.com/downloads/postgres-postgresql-downloads**
2. Choose **Windows** and pick the latest **PostgreSQL 17** (or 16) **x86-64**.
3. Download the installer (e.g. `postgresql-17.x.x-windows-x64.exe`).

## 2. Run the installer

1. **Right‑click the .exe → Run as administrator.**
2. Click **Next** through the welcome screen.
3. **Installation directory:** leave default (e.g. `C:\Program Files\PostgreSQL\17`) → **Next**.
4. **Select components:** keep all (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools) → **Next**.
5. **Data directory:** leave default → **Next**.
6. **Password:** set a password for the `postgres` superuser. **Remember it** — you’ll use it in `DATABASE_URL`. → **Next**.
7. **Port:** leave **5432** → **Next**.
8. **Locale:** leave default → **Next**.
9. Click **Next** to confirm, then **Install**. Wait for it to finish → **Finish**.

## 3. Add PostgreSQL to PATH (optional but useful)

1. Press **Win + R**, type `sysdm.cpl`, Enter.
2. **Advanced** tab → **Environment Variables**.
3. Under **System variables**, select **Path** → **Edit** → **New**.
4. Add: `C:\Program Files\PostgreSQL\17\bin` (use your version number if different).
5. **OK** through all dialogs.

## 4. Create the database

1. Open **pgAdmin 4** from the Start menu (or run `psql` from a new Command Prompt if you added it to PATH).
2. In pgAdmin, under **Servers**, double‑click **PostgreSQL 17**.
3. Enter the `postgres` password you set.
4. Right‑click **Databases** → **Create** → **Database**.
5. **Database** name: `compliance_tracker`.
6. **Owner:** leave as `postgres` → **Save**.

Or from **Command Prompt** (with PostgreSQL in PATH):

```bat
psql -U postgres -c "CREATE DATABASE compliance_tracker;"
```

Enter the `postgres` password when asked.

## 5. Configure the backend

1. In the project, go to the **backend** folder.
2. Copy `.env.example` to `.env` if you haven’t already.
3. Edit `.env` and set `DATABASE_URL` with your password:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@localhost:5432/compliance_tracker
```

Replace `YOUR_PASSWORD_HERE` with the password you set for the `postgres` user.

## 6. Run migrations and restart the app

From the **backend** folder, with your virtual environment activated:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000/api/v1/health/ready**. You should see:

```json
{"status": "ok", "database": "connected"}
```

## Troubleshooting

| Issue | What to do |
|-------|------------|
| Installer won’t run | Right‑click → Run as administrator. |
| “Port 5432 in use” | Either stop the other service using 5432 or choose another port and use it in `DATABASE_URL`. |
| “Password authentication failed” | Use the exact password you set for `postgres` in `DATABASE_URL`. |
| `psql` not found | Add `C:\Program Files\PostgreSQL\17\bin` to PATH (step 3) and open a new Command Prompt. |
| Database already exists | You can use it as-is; just set `DATABASE_URL` and run `alembic upgrade head`. |
