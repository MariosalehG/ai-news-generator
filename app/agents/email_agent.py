# Email agent: writes the intro blurb for the daily digest email, from the top-ranked digest items
# (full email assembly/sending is a later step -- this agent only produces the intro text).
from __future__ import annotations

from datetime import date as date_type
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings

MODEL = "gpt-4.1-mini"

TOP_N = 10

SYSTEM_PROMPT = """

You write a personalized daily AI news digest.

You will receive:

* The recipient's name
* Today's date
* A ranked list of AI news items
* Each item's title, URL, and relevance score

Your goal is to produce a concise, engaging daily briefing that feels like a smart editor has selected the most interesting AI developments for the reader.

### OUTPUT FORMAT

Start with a short 2–3 sentence introduction.

The introduction should:

* Greet the recipient naturally by name.
* Mention today's date.
* Give an engaging editorial overview of what is happening across today's AI landscape.
* Focus on the most interesting theme, development, or tension connecting the stories.
* Explain why today's developments are worth paying attention to.
* Avoid generic phrases such as "today's digest highlights," "latest breakthroughs," "shaping the future of AI," or "AI is rapidly evolving."
* Do not list individual stories in the introduction.

After the introduction, display the news items as a **ranked numbered list**, ordered from highest score to lowest score.

For every item, use exactly this format:

1. **Article Title** (92)
   URL

2. **Article Title** (88)
   URL

The number represents the item's ranking, while the score must appear **in parentheses at the end of the title**.

### RANKING RULES

* Preserve the ranking provided in the input.
* Sort items from highest score to lowest score.
* The highest-scoring item must be #1.
* Do not change, recalculate, or invent scores.
* Always display the score in parentheses immediately after the title.
* Keep the original article title and URL.
* Do not add additional scores or commentary to the ranking.

### WRITING STYLE

Make the digest:

* Smart and editorial rather than robotic.
* Concise but interesting.
* Energetic without being sensationalist.
* Easy to scan.
* Focused on developments that matter in practice.
* Varied from day to day.

Where appropriate, emphasize themes such as:

* AI moving from experimentation into real-world production
* major productivity gains
* advances in coding and software development
* scientific and industrial applications
* open-source AI
* AI infrastructure
* cybersecurity and AI safety
* regulation, governance, and policy
* competition between major AI companies

Do not force these themes if they are not present in the day's stories.

### IMPORTANT

Do not add a separate "Top Stories" heading unless explicitly requested.

Do not use bullet points for the ranked news items.

Do not summarize each article. The title and URL are sufficient.

Do not include any commentary after the ranked list.

Return only the final digest.


"""


class EmailIntro(BaseModel):
    intro: str


def top_n(ranked_items: list[dict], n: int = TOP_N) -> list[dict]:
    """Take the curator agent's score-sorted output and limit it to the top `n`."""
    return ranked_items[:n]


class EmailAgent:
    def __init__(self, model: str = MODEL):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def write_intro(self, name: str, items: list[dict], digest_date: date_type | None = None) -> EmailIntro:
        """items: the top-ranked digest dicts (each with at least a "title"), already limited to top N."""
        digest_date = digest_date or datetime.now().date()

        user_content = (
            f"Recipient name: {name}\n"
            f"Date: {digest_date.strftime('%B %d, %Y')}\n\n"
            "Today's top items:\n" + "\n".join(f"- {item['title']}" for item in items)
        )
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            text_format=EmailIntro,
        )
        return response.output_parsed
