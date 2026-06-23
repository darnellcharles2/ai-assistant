# Blessedly Stressed OS MVP

This repository contains a minimal implementation of the *Blessedly Stressed OS* as
outlined in the **Complete Blessedly Stressed OS Agent Blueprint v1**. The goal
is to provide a starting point that Codex can extend into a fully featured
system. It includes a simple Express API server, agent modules, data
memory files and integration stubs.

## Features

- **Idea intake**: Accepts a raw idea and routes it to the appropriate agent.
- **Routing logic**: Classifies ideas into music, lessons, Skool modules, digital products,
  brand assets, automation scenarios or general guidance.
- **Agent architecture**: Separate modules for music generation, lessons,
  Skool building, digital products, brand visuals, automation, stewardship and more.
- **Data memory**: JSON files under `data/` capture the spiritual guardrails,
  state check definitions, SAVIOR Made posture, DC Flow prompts, course
  framework and schema definitions.
- **Integration stubs**: Placeholder modules for Google Drive, Google Sheets,
  Make.com webhooks and Skool exports.

## Getting Started

1. **Install dependencies**:

   ```bash
   npm install express body-parser axios
   ```

2. **Configure environment variables**: Copy `.env.example` to `.env` and fill in
   the required values such as `MAKE_WEBHOOK_URL` and any Google API keys.

3. **Run the server**:

   ```bash
   node app.js
   ```

   The server will start on `http://localhost:3000` by default.

4. **Submit an idea**:

   Send a POST request to `/intake` with a JSON body containing at least
   `raw_input`. For example:

   ```bash
   curl -X POST http://localhost:3000/intake \
     -H 'Content-Type: application/json' \
     -d '{"raw_input": "Write a song about redemption and grace"}'
   ```

   The server will respond with the classified idea and a stub output from
   the selected agent.

## File Structure

```
blessedly-stressed-os/
├── app.js              – Express server entry point
├── agents/             – Agent modules implementing specific roles
├── data/               – JSON memory files with guardrails and frameworks
├── routes/             – Optional modular route definitions
├── integrations/       – Stubs for external API integrations
├── outputs/            – Directory for generated files (empty in MVP)
├── README.md           – This file
└── .env.example        – Sample environment configuration
```

## Next Steps

This MVP intentionally leaves many functions unimplemented. The Codex build
agent should extend this codebase to:

- Persist ideas, songs, lessons and products to a database (Google Sheets,
  Baserow or Supabase).
- Implement the review gate logic outlined in the blueprint.
- Generate real song lyrics using the DC Flow prompts and integrate with
  Suno or other music tools.
- Build actual PDF workbooks and digital products using templates.
- Connect to Skool's API or automation tooling to create modules and posts.
- Integrate with Google Drive/Sheets for storage and file management.
- Add authentication, user management and a front-end interface.

## Disclaimer

This code is a learning exercise and an illustration of how the Blessedly
Stressed OS could be structured. It is not intended to replace Jesus,
Scripture, prayer, church, counsel, recovery support, medical care, legal
responsibility or real community. Always seek God first and follow the
order of operations: **Jesus -> Scripture -> Prayer -> State Check -> SAVIOR Made ->
Kingdom Flow -> DC Flow -> Savior Saved -> Bible & Beats -> Skool/Course -> Digital
Products -> Community Support -> Service**.
