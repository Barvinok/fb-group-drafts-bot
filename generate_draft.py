"""
generate_draft.py

Decides which recurring post is due today, asks Claude to write a fresh
version of it (fixed structure, varied hook/wording so it doesn't feel
copy-pasted week to week), and appends the draft to a Google Sheet.

You (or a co-admin) open the Sheet, copy the "Draft Text" for any row with
Status = "Ready", and paste it into Facebook's native post scheduler for
the group. Facebook does NOT allow third-party apps to publish to Groups
via API (this was fully deprecated), so this script intentionally stops
at "prepare the draft" rather than trying to auto-post.
"""

import os
import datetime
from anthropic import Anthropic
from sheets import append_draft

# ---- CONFIG -----------------------------------------------------------

ANTHROPIC_MODEL = "claude-sonnet-5"

# Rotating list for "How AI is Changing Role X" — cycles by month number
ROLE_ROTATION = [
    "QA / Test Engineer",
    "Product Manager",
    "Data Analyst",
    "Frontend Developer",
    "Backend Developer",
    "UX/UI Designer",
    "Business Analyst",
    "DevOps Engineer",
    "Project Manager",
    "Technical Writer",
    "Recruiter / Talent",
    "Customer Support / CS",
]

TEMPLATES = {
    "interview_debrief": """💬 **Interview Debrief Wednesday**
Had an interview recently? Share it with us — even a quick version helps someone else prepare.

- Company/role type (name optional)
- What they asked (tech + behavioral)
- Any AI-related questions? (tool knowledge, "how do you use AI in your work," take-home with AI allowed/not)
- What surprised you
- How you think it went

No interview is too small to share — even a "bad" one teaches the group something. 🙌""",

    "win_of_week": """🏆 **Win of the Week**
Big or small — offer letter, salary bump, finished a certification, survived a tough interview, negotiated something, or just made it through a hard week. Share it here.

This is a no-judgment, no-"humble brag" zone. Celebrate yourself. 🎉

💡 Bonus: if your win connects to your expertise, consider turning it into a short LinkedIn post or article too — a lesson learned, an AI project you shipped, a skill you leveled up in. It's great visibility, and it helps others in the group learn from you. Drop the link below if you write one — we'll like & share! 🔗""",

    "ai_tools": """🛠️ **AI Tools I Actually Use At Work**
Skip the hype — what do you actually use, and for what?

- Tool name
- What you use it for (specific task, not vibes)
- One thing it's genuinely saved you time on
- One thing it's bad at / you don't trust it for

Real workflows only — this isn't a tool-recommendation thread. 🙂""",

    "how_ai_changing_role": """🤖 **How AI is Changing: {role}**

- What's actually changing day-to-day
- New skills becoming expected
- What's *not* changing (don't panic)
- Tools people in this role are using now

If you work as a {role} — jump in the comments and share your real experience. Requests for next role? Drop them below. 👇""",

    "contributor_of_month": """🌟 **Contributor of the Month**
Reminder for admins: pick this month's contributor and post the shoutout template.

Tag someone below who's helped you this month — let's spread the appreciation.""",
}


def month_index(dt: datetime.date, length: int) -> int:
    return (dt.year * 12 + dt.month) % length


def is_last_day_of_month(dt: datetime.date) -> bool:
    return (dt + datetime.timedelta(days=1)).month != dt.month


def decide_post_type(dt: datetime.date) -> str | None:
    weekday = dt.weekday()  # Monday = 0

    # Monthly specials take priority over the weekly slot on the same day
    if weekday == 0 and dt.day <= 7:
        return "how_ai_changing_role"
    if weekday == 2 and dt.day <= 7:
        return "ai_hot_take"
    if is_last_day_of_month(dt):
        return "contributor_of_month"

    # Regular weekly rotation
    if weekday == 0:
        return "ai_tools"
    if weekday == 2:
        return "interview_debrief"
    if weekday == 4:
        return "win_of_week"

    return None  # no post scheduled today


def build_base_text(post_type: str, dt: datetime.date) -> str:
    if post_type == "how_ai_changing_role":
        role = ROLE_ROTATION[month_index(dt, len(ROLE_ROTATION))]
        return TEMPLATES[post_type].format(role=role)
    return TEMPLATES[post_type]


# Style reference only — Claude is told to match this tone/structure,
# not to copy it. It's never sent back verbatim.
HOT_TAKE_STYLE_EXAMPLE = """AI interview assistants are becoming a hot topic.
Some tools like ParakeetAI, Final Round AI, LockedIn AI, and Interview Sidekick can listen to interview questions, generate answers in real time, and even use your resume to tailor those answers.
A friend recently told me his team interviewed a candidate with only 2–3 years of experience. The candidate answered several very niche technical questions that usually require years of hands-on experience. The team was shocked and suspected the candidate was using an AI teleprompter.
This made me think...
Where is the line between preparing with AI and cheating?
Silicon Valley has long had the saying, "Fake it till you make it." Is AI just the next version of that? Personally, I don't like it, but maybe these are the new rules of the game?
And one more question: If you use AI to get the job, what happens on your first week at work? What do you do when there is no AI answering every question for you?
I'd love to hear both sides:
- As an employer, would you hire someone using an AI interview assistant?
- As a candidate, would you use one? Why or why not?
- Where do you draw the ethical line?"""


def generate_hot_take(client: Anthropic) -> tuple[str, str]:
    """
    Searches the web for a genuinely current, debate-worthy AI story
    (job market, hiring, workplace disruption, ethics — anything that fits
    "AI is changing everything") and writes a discussion-provoking post in
    the group's established style. Returns (draft_text, source_url).
    """
    prompt = f"""Search the web for one recent (last 2-4 weeks), genuinely
notable or controversial AI-related story about jobs, hiring, or the
workplace — something people would want to argue about in the comments.
Examples of the kind of topic (don't limit yourself to these): AI
interview-cheating tools, AI replacing entry-level roles, a company's AI
policy causing backlash, AI-generated work controversies, layoffs blamed
on AI, etc.

Then write a Facebook post for a private group of women in tech (mostly
from the former USSR, group language is English). Match this style and
structure closely (voice, pacing, personal-anecdote framing, ending in
open discussion questions) — this is a STYLE REFERENCE only, do not reuse
its specific facts or wording:

---
{HOT_TAKE_STYLE_EXAMPLE}
---

Requirements:
- Base it on what you actually find via search — do not invent facts, tool names, or statistics
- Paraphrase news content in your own words; do not quote more than a few words from any source
- Under 200 words
- End with 2-4 open discussion questions, framed to invite both sides of the debate
- Tone: thought-provoking and a little provocative, but respectful — not clickbait, not mean

Return ONLY the finished post text, nothing else (no preamble, no "Here's a draft")."""

    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=900,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        messages=[{"role": "user", "content": prompt}],
    )

    text_parts = []
    source_url = ""

    for block in resp.content:
        if block.type == "text":
            text_parts.append(block.text)
            for citation in (getattr(block, "citations", None) or []):
                url = getattr(citation, "url", None)
                if url and not source_url:
                    source_url = url
        elif block.type == "web_search_tool_result" and not source_url:
            results = block.content if isinstance(block.content, list) else []
            for item in results:
                url = getattr(item, "url", None) or (
                    item.get("url") if isinstance(item, dict) else None
                )
                if url:
                    source_url = url
                    break

    draft_text = "\n".join(p for p in text_parts if p).strip()
    return draft_text, source_url


def freshen_with_claude(client: Anthropic, post_type: str, base_text: str) -> str:
    """
    Keep the structure/questions identical (that's what makes it easy for
    members to reply to) but ask Claude to vary the opening hook line so
    regulars don't see the exact same intro every week.
    """
    prompt = f"""This is a recurring post template for a private Facebook group
for women in tech (mostly from the former USSR, group language is English).

Rewrite ONLY the first line (the hook/greeting) to feel fresh and not
repetitive week over week. Keep it warm, concise, no more than 1 sentence,
no hashtags, no emoji spam (max 1-2 emoji total). Keep every bullet point
and every question in the template EXACTLY as written below — do not
remove, reorder, or reword the bullets. Return the full post, ready to
paste into Facebook.

TEMPLATE:
{base_text}"""

    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def main():
    api_key = os.environ["ANTHROPIC_API_KEY"]
    client = Anthropic(api_key=api_key)

    today = datetime.date.today()
    post_type = decide_post_type(today)

    if post_type is None:
        print(f"{today}: no post scheduled today.")
        return

    if post_type == "ai_hot_take":
        draft_text, source_url = generate_hot_take(client)
    else:
        base_text = build_base_text(post_type, today)
        draft_text = freshen_with_claude(client, post_type, base_text)
        source_url = ""

    append_draft(
        date=today.isoformat(),
        post_type=post_type,
        draft_text=draft_text,
        status="Ready",
        link=source_url,
    )
    print(f"{today}: generated '{post_type}' draft and logged to Sheet.")


if __name__ == "__main__":
    main()
