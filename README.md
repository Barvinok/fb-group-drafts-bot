# FB Group Post Draft Generator

Auto-generates the week's recurring post drafts for your Facebook group in
one batch and logs them to a Google Sheet, with a **Recommended Day**
column so you know when to schedule each one. You copy-paste the "Ready"
drafts into Facebook's **native post scheduler** (Group admin tools →
create post → schedule icon). Facebook does not allow apps to publish to
Groups via API, so this tool intentionally stops one step before
publishing.

## Schedule

Runs once a week (Sundays, via GitHub Actions) and generates every post
due in the coming Monday–Sunday in a single run:

| Day | Post type |
|---|---|
| Monday | AI Tools I Actually Use |
| Wednesday | Interview Debrief |
| Friday | Win of the Week (+ LinkedIn cross-post encouragement) |
| 1st Monday of month | How AI is Changing Role X (auto-rotates role) |
| 1st Wednesday of month | AI Hot Take — Claude searches the web for a current, debate-worthy AI/jobs story and writes a discussion post in a provocative-but-respectful style. Source article link is logged in the **Links** column. |
| Last day of month | Contributor of the Month (reminder only — you pick the person) |

## Sheet columns

`Date | Post Type | Draft Text | Status | Links | Recommended Day`

**Date** is when the row was generated (i.e. the Sunday the script ran).
**Recommended Day** is when to actually post it (e.g. `Wednesday
(2026-08-12)`) — sort or filter by this column to plan your week.

The **Links** column is only populated for `ai_hot_take` posts (the source
article Claude based the post on). Worth a quick skim before posting —
Claude is instructed not to invent facts, but always sanity-check a
provocative post against its source before publishing.

## Setup

1. **Google Sheet**: create a new sheet (or reuse your Instagram one), share
   it with the same service account email you already use for the
   Instagram scheduler (`sheets.py` there references `GOOGLE_SHEETS_CREDENTIALS_JSON`).
   Copy its ID into `SPREADSHEET_ID`.
2. **GitHub repo**: create a new repo (or a `fb-group-scheduler/` folder in
   an existing one), add these files, put `weekly_drafts.yml` under
   `.github/workflows/`.
3. **Secrets**: in the repo's Settings → Secrets and variables → Actions,
   add `ANTHROPIC_API_KEY`, `GOOGLE_SHEETS_CREDENTIALS_JSON`, `SPREADSHEET_ID`.
4. **Test locally first**:
   ```bash
   pip install -r requirements.txt --break-system-packages
   export ANTHROPIC_API_KEY=...
   export GOOGLE_SHEETS_CREDENTIALS_JSON='...'
   export SPREADSHEET_ID=...
   python generate_draft.py
   ```
5. Once it works, let the GitHub Action run daily, or trigger manually via
   the "Run workflow" button (workflow_dispatch is enabled).

## Weekly routine for you

The Action runs Sunday morning and drops the whole week's drafts into the
Sheet at once. Open it any time after that, review, and schedule everything
for the week in Facebook's native scheduler — sorted by **Recommended Day**.


## Notes

- Bullet points/questions in each template stay fixed on purpose — that
  consistency is what makes them easy for members to reply to. Only the
  opening hook line is varied by Claude.
- "Contributor of the Month" can't be picked by AI — it just drops a
  reminder row so you don't forget to post the shoutout.
- If you want a notification (e.g. email) instead of checking the Sheet
  manually, that can be added later via a simple GitHub Actions step or
  Zapier watching the Sheet.
