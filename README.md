# slack-critical-alert-bot

Watches a Slack channel for urgent/critical messages and phones a static
list of on-call people via Twilio when one appears — no Slack app, no bot
token, no OAuth install required.

## How it works (no Slack app needed)

Instead of a bot reading the channel (which needs a Slack app + API
token, often gated behind admin/org approval), this uses **Slack's
built-in Workflow Builder**:

1. A Slack workflow (native Slack feature, not an installed app) triggers
   whenever a message containing a keyword (`urgent`, `critical`, `p0`,
   etc.) is posted in the watched channel.
2. That workflow's step sends an HTTP request straight to GitHub's API,
   firing a `repository_dispatch` event on this repo with the message
   text as payload — no polling, no Slack token, real-time.
3. GitHub Actions (`.github/workflows/alert.yml`) receives that event and
   runs `python -m app.dispatch`, which calls everyone in `on_call` (in
   `config.yaml`) via Twilio's Voice API with a `<Say>` TwiML message
   reading out the alert, staggered by `call_stagger_seconds`.
4. Each call attempt is appended to `state/state.json` (committed back to
   the repo) as an audit log.

Filtering on "is this urgent/critical" happens entirely inside the Slack
workflow's trigger config (you choose the keywords there) — the app code
trusts whatever Slack sends it.

## Setup

### 1. Build the Slack workflow

In Slack: **Tools → Workflow Builder** (or the "+" next to the message
box → **Workflow**) → **Create Workflow**.

- **Trigger**: "From a message in Slack" → pick the channel to watch →
  set it to fire when the message **contains** any of your keywords
  (e.g. `urgent`, `critical`, `p0`, `p1`, `sev1`, `sev2`)
- **Step**: add **Send a webhook** (a built-in Workflow Builder step —
  this requires a Slack plan that supports it; Pro and above typically
  do, check if you don't see it as an option)
  - URL: `https://api.github.com/repos/kammasainishitha/slack-critical-alert-bot/dispatches`
  - Method: `POST`
  - Headers:
    - `Accept: application/vnd.github+json`
    - `Authorization: Bearer <your GitHub token — see step 2>`
  - Body (JSON), using the message-text variable Workflow Builder gives
    you in place of `{{message text}}`:
    ```json
    {
      "event_type": "slack_urgent_alert",
      "client_payload": {
        "text": "{{message text}}",
        "channel": "{{channel name}}"
      }
    }
    ```
- **Publish** the workflow

If your workspace restricts who can create/publish workflows, that's a
much smaller ask than requesting a new Slack app be installed — worth
checking with whoever manages your Slack workspace if you hit a
permission wall here.

### 2. Create a GitHub token for Slack to call

Go to **github.com/settings/tokens** → generate a token:
- Prefer a **fine-grained token** scoped to only this one repo, with
  "Contents" permission set to read/write
- If that 403s when Slack calls it, fall back to a **classic token**
  with the `repo` scope

This token goes directly into the Workflow Builder webhook step's
`Authorization` header above — it never touches GitHub Secrets, since
Slack (not GitHub Actions) is the one making the call.

### 3. Twilio

Get `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and a `TWILIO_FROM_NUMBER`
from console.twilio.com, then add them as GitHub repo secrets at
**Settings → Secrets and variables → Actions**:
`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`.

Trial Twilio accounts can only call numbers verified under Console →
Phone Numbers → **Verified Caller IDs**.

### 4. Set the on-call list

Edit `on_call` in `config.yaml` — name + phone (E.164 format, e.g.
`+919876543210`). Add `match_keywords` to an entry to only call that
person when those words also appear in the message.

### 5. Test

Post a message with one of your trigger keywords in the Slack channel.
Check the repo's **Actions** tab — a `slack-workflow-alert` run should
appear within seconds. If it doesn't appear at all, the problem is on the
Slack workflow/webhook side (check Workflow Builder's run history in
Slack); if it appears but fails, check the run's logs.

## Older approach: Slack API polling (kept for reference, disabled)

`app/poll.py` and `.github/workflows/poll.yml` implement an alternative
that polls Slack's `conversations.history` API every 5 minutes — this
needs a Slack bot token (i.e. an actual Slack app), which is why the
Workflow Builder approach above is the primary path. That workflow is
currently disabled. Ignore it unless Slack app access becomes available
later and you'd prefer true (5-min-interval) polling over the
webhook-trigger model.

## Known limitations

- On-call mapping is static (edited in `config.yaml`), not a rotation.
- No retry/escalation if a call goes unanswered.
- Relies on Slack Workflow Builder's keyword-match trigger being
  available on your plan, and on whoever administers your workspace
  allowing workflow creation/publishing.
- The GitHub token in the webhook header is visible to anyone who can
  edit that Slack workflow — scope it to this repo only and rotate it
  periodically.
