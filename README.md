# Savior Made CHECK

A simple AI agent that reviews public-facing messages with the Savior Made CHECK prompt.

## Local setup

The local project already expects:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

Keep the key in `.env.local` or your host's secret manager. Do not place it in browser code.

## Run

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Deploy

For Vercel, Replit, or Lovable-style hosting, add this secret in the project settings:

```env
OPENAI_API_KEY
```

The app calls OpenAI only from `app/api/check/route.ts`.

Vercel preview deployments are created from the `savior-made-check` branch.
