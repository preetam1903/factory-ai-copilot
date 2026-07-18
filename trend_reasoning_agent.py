# ==========================================================
# TREND REASONING AGENT
# ==========================================================

from openai import OpenAI


class TrendReasoningAgent:

    def __init__(self, api_key):

        self.client = OpenAI(api_key=api_key)

    # ======================================================
    # Generate Executive Investigation Report
    # ======================================================

    def generate(self, trend_facts):

        system_prompt = """
You are an expert manufacturing investigation consultant.

You are investigating manufacturing performance.

You will receive investigation facts already calculated by the AI Investigation Engine.

IMPORTANT RULES

1. Never invent numbers.

2. Never modify values.

3. Never perform calculations.

4. Only use the supplied investigation facts.

5. Write like a senior manufacturing consultant.

6. Never mention JSON.

7. Never mention AI.

8. Never mention LLM.

9. Never mention ChatGPT.

10. Keep the report executive friendly.

Generate the report using exactly the following sections.

## Investigation Verdict

Briefly explain whether the user's assumption is supported.

## Evidence Summary

Summarize the most important evidence.

## Business Interpretation

Explain what the evidence means.

Explain whether the production reduction is likely planning related or operational.

## Recommended Next Investigation

Recommend what operational investigation should happen next.

Mention the investigation priority.

Maximum 250 words.
"""

        user_prompt = f"""
Investigation Facts

{trend_facts}
"""

        response = self.client.chat.completions.create(

            model="gpt-5",

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": user_prompt
                }

            ],

            temperature=0.2

        )

        return response.choices[0].message.content
