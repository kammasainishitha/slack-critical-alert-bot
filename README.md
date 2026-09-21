# slack-critical-alert-bot

Watches a Slack channel for urgent/critical tickets and phones a static list
of on-call people via Twilio when one appears. Runs for free as a GitHub
Actions scheduled workflow — no server, no laptop needing to stay on.

## How it works

Every 5 minutes, `.github/workflows/poll.yml` runs `python -m app.poll`,
which:

1. For each channel in `config.yaml`, fetches messages posted since the
   last run (via Slack's `conversations.history` Web API).
2. Flags a message as urgent/critical if its text contains a configured
   keyword (`urgent`, `critical`, `p0`, `sev1`, ...), or if it carries a
   `Priority` field (block/attachment) matching `priority_field_values`.
   This covers both plain human messages and structured notifications from
   a ticketing bot (Jira, DevRev, etc.).
3. For each match, calls everyone in `on_call` (in `config.yaml`) via
   Twilio's Voice API with a `<Say>` TwiML message reading out the alert,
   staggered by `call_stagger_seconds`.
4. Commits `state/state.json` back to the repo — this tracks the
   last-seen timestamp per channel (so old messages are never reprocessed)
   and a rolling window of processed message IDs (dedupe) and recent call
   attempts (audit log).

The first run for a newly-added channel just records the current time as
the watermark — it won't dial anyone for pre-existing history.

## Why polling, not a live listener

A real-time listener needs a persistent connection, which needs an
always-on server (costs money). Running this for free means something
that wakes up, checks, and exits — hence a 5-minute-interval GitHub
Actions job instead of a live Slack Socket Mode process. Worst case
latency from ticket to phone call is ~5-10 minutes (occasionally more if
GitHub's scheduler is under load) — not instant, but zero-cost.

**This repo needs to stay public** for GitHub Actions minutes to be
unlimited/free. On a private repo, a 5-minute interval would burn through
the free 2,000 min/month tier; you'd need to drop to ~every 15 minutes to
stay within it.

## Setup

### 1. Slack app

Create a Slack app at api.slack.com/apps with:
- Bot token scopes: `channels:history` (public channels) and/or
  `groups:history` (private channels)
- Install the app to your workspace, invite the bot to the channel(s) you
  want to watch

You only need the bot token (`xoxb-...`) — no Socket Mode / app-level
token / signing secret required for polling.

### 2. Twilio

Get `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and a `TWILIO_FROM_NUMBER`
capable of making outbound voice calls, from console.twilio.com.

### 3. GitHub repo secrets

In the repo's Settings > Secrets and variables > Actions, add:
`SLACK_BOT_TOKEN`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
`TWILIO_FROM_NUMBER`.

### 4. Configure `config.yaml`

- `watched_channels`: Slack **channel IDs** (not names) to monitor
- `keywords` / `priority_field_values`: what counts as urgent/critical
- `on_call`: static list of `{name, phone}` to call. Add `match_keywords`
  to an entry to only call that person when those keywords also appear.

### 5. That's it

The workflow runs automatically every 5 minutes once pushed. To trigger a
run manually (e.g. to test), go to the Actions tab and run
"poll-slack-alerts" via "Run workflow", or:

```bash
gh workflow run poll.yml
```

## Local testing

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in real or dummy credentials
.venv/bin/python -m app.poll
```

## Known limitations

- On-call mapping is static (edited in `config.yaml`), not a rotation.
- No retry/escalation if a call goes unanswered — Twilio status callbacks
  would be needed to detect no-answer and call the next person.
- ~5-10 minute latency, not real-time. For true real-time alerting you'd
  need an always-on host running a Slack Socket Mode process instead —
  that costs a few dollars a month but removes the delay.
- If more than 200 messages land in a channel within one 5-minute window,
  only the most recent 200 are fetched (Slack API pagination isn't
  implemented) — fine for normal use, not for very high-traffic channels.
