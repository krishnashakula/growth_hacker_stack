# 🚀 Growth‑Hacker LinkedIn Automation Stack

Self‑hosted **n8n** workflows with AI keyword mining, auto‑posting, engagement capture, analytics, and reinforcement learning.

## Quickstart

```bash
git clone https://github.com/yourname/growth_hacker_stack.git
cd growth_hacker_stack
cp .env.example .env   # fill in all keys
docker-compose up -d db
sleep 10
psql postgres://n8n_user:changeme@localhost:5432/n8n -f sql/init.sql
docker-compose up -d
```

- n8n UI: http://localhost:5678  
- Keyword API: http://localhost:8000/keywords  
- Analytics Fetcher: http://localhost:8001/health
- Metabase: http://localhost:3000

Import `workflows/linkedin_workflow.json` into n8n (Settings ➜ Import).

## Stack

| Layer        | Tool                     |
|--------------|--------------------------|
| Orchestration| n8n (Docker)             |
| AI Keywords  | FastAPI + HF Transformers|
| Analytics    | LinkedIn Analytics Fetcher|
| Scheduler    | n8n Cron → LinkedIn node |
| Analytics DB | PostgreSQL               |
| Dashboards   | Metabase                 |

## Reinforcement Logic

A simple ε‑greedy bandit picks one of four hook styles. Post performance is written hourly → `post_stats`.  
Success rates update `hook_performance`, slowly biasing toward better hooks over time.

## Notes

- All calls use official LinkedIn Marketing API, keeping the project ToS‑safe.  
- Replace `urn:li:person:xxxxxxxxxxxxxxxx` with your own URN or set `LINKEDIN_PERSON_URN` in `.env`.  
- Stay under LinkedIn’s daily post limits to avoid rate‑limit issues (recommend ≤ 30/day).

Enjoy autonomous growth! 🚀
