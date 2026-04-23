# PolicyClaw Frontend (Next.js)

Separate Next.js frontend for PolicyClaw MVP.

## Prerequisites

- Node.js 20+

## Run

1. Install dependencies:

   ```powershell
   cd frontend
   npm install
   ```

2. Configure API base URL:

   ```powershell
   copy .env.local.example .env.local
   ```

3. Start frontend:

   ```powershell
   npm run dev
   ```

4. Open website:

   - http://127.0.0.1:3000

## Backend requirement

Run backend separately at:

- http://127.0.0.1:8000

The frontend uses `NEXT_PUBLIC_API_BASE_URL` (default: `http://127.0.0.1:8000`).
