---
name: testing-blessedly-stressed-os
description: Test the Blessedly Stressed OS Express API end-to-end. Use when verifying routing, agent dispatch, state check gate, or intake endpoint changes.
---

# Testing the Blessedly Stressed OS API

## Prerequisites

- Node.js installed
- Dependencies installed: `npm install`
- No external credentials needed for local testing (all integrations are stubs)

## Devin Secrets Needed

None required for local testing. Integration stubs (Google Drive, Sheets, Make.com, Skool) check env vars but return stub responses when unconfigured.

## Starting the Server

```bash
cd /home/ubuntu/repos/ai-assistant
node app.js
# Server starts on http://localhost:3000
```

Verify with: `curl http://localhost:3000/` — should return JSON with `name: "Blessedly Stressed OS"`.

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | System info and order of operations |
| `/intake` | POST | Submit an idea for classification and routing |
| `/intake/categories` | GET | List all 8 available categories |

## Testing Patterns

### Basic idea submission
```bash
curl -X POST http://localhost:3000/intake \
  -H 'Content-Type: application/json' \
  -d '{"raw_input": "Write a song about redemption"}'
```

### With state check
```bash
curl -X POST http://localhost:3000/intake \
  -H 'Content-Type: application/json' \
  -d '{"raw_input": "Write a song", "state_check": {"spiritual": "green", "emotional": "green"}}'
```

### Validation error
```bash
curl -X POST http://localhost:3000/intake \
  -H 'Content-Type: application/json' \
  -d '{}'
# Returns HTTP 400
```

## Routing Categories and Keywords

The router in `agents/router.js` classifies ideas by keyword matching with scoring. Multi-word keywords score higher (e.g., "bible study" scores 2 vs "study" scoring 1).

| Category | Example Keywords | Agent Name |
|----------|-----------------|------------|
| music | song, beat, lyric, worship | Bible & Beats / DC Flow Music Agent |
| lessons | lesson, bible study, devotional | Lessons & Teaching Agent |
| skool | skool, module, course | Skool Community Builder Agent |
| digitalProducts | workbook, pdf, template, ebook | Digital Products Agent |
| brand | logo, brand, design, graphic | Brand & Visual Identity Agent |
| automation | automate, webhook, workflow | Automation & Workflow Agent |
| stewardship | steward, budget, tithe | Stewardship & Accountability Agent |
| general | (fallback - no keywords match) | No agent field; returns guidance + orderReminder |

## Known Edge Cases

- **Tie-breaking**: When keywords from two categories score equally, `Object.entries` iteration order determines the winner. For example, "Create a workbook for the course" ties between skool ("course"=1) and digitalProducts ("workbook"=1), and skool wins due to iteration order. Use more specific keywords to avoid ambiguity.
- **General fallback response structure**: The general category returns a different JSON structure (`guidance`, `orderReminder`) without an `agent` field, unlike all other categories.
- **State Check gate**: Any `"red"` value in the `state_check` object blocks processing. Only red keys are listed in `redStates`; green/yellow keys are ignored. The response has `idea_processed: false` and no `agentOutput`.

## Testing Approach

This is an API-only app (no frontend). Test via shell commands with curl. No browser/GUI recording needed. Use Python inline assertions for automated verification:

```bash
curl -s -X POST http://localhost:3000/intake \
  -H 'Content-Type: application/json' \
  -d '{"raw_input": "your idea"}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data['idea']['category'] == 'expected_category'
print('PASS')
"
```
