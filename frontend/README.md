# Compliance Tracker – Frontend

Next.js 14 dashboard for the Compliance Tracker MVP.

## Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**

## Setup

1. Install dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Copy env and set API URL (optional; default is `http://localhost:8000`):

   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local` if your backend runs on a different host/port:

   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Run the backend (from `backend/`) so the API is available.

## Run

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

- **Dashboard** (`/`) – table of documents with name, category, expiry date, status (Expired / Expiring Soon / Active).
- **Upload** (`/upload`) – upload a file; on success you are redirected to the dashboard.

## Scripts

| Command      | Description              |
|-------------|--------------------------|
| `npm run dev`   | Start dev server (port 3000) |
| `npm run build` | Production build            |
| `npm run start` | Start production server     |
| `npm run lint`  | Run ESLint                  |
