# demo/backend/prompts.py

INTENT_PROMPT = """\
Analyze the following topic and return a JSON object with these fields:
- reframed_topic (str): a clear, debate-ready restatement of the topic
- domain (str): the primary domain (e.g. "healthcare", "politics", "technology", "ethics")
- controversy_level (str): one of "low", "medium", "high"
- recommended_participants (int): how many distinct viewpoints exist (between 2 and 5)
- recommended_rounds (int): how many debate rounds are appropriate (1 for low controversy, 2 for medium, 3 for high)

Topic: {topic}

Return only valid JSON.
"""

TEAM_PROMPT = """\
Generate a debate team for this topic: "{topic}"
Domain: {domain}
Number of participants: {n}

Return a JSON object with a "participants" array. Each participant has:
- participant_id (str): snake_case unique identifier (e.g. "climate_scientist")
- label (str): short display name (e.g. "Climate Scientist")
- role (str): their role in the debate (e.g. "expert", "advocate", "skeptic", "moderator")
- stance (str): their position on the topic in one sentence

Ensure participants represent genuinely different and interesting viewpoints.
Return only valid JSON.
"""

CHALLENGE_PROMPT = """\
You are {challenger_label} ({challenger_stance}).

Topic being debated: "{topic}"

Your opponent ({target_label}) has argued:
{prior_argument}

Write a compelling challenge or rebuttal in 2-4 sentences. Be direct, specific, and intellectually sharp.
Also assign:
- a "topic_tag" (str): a 2-5 word snake_case label for the sub-topic being challenged
- a "confidence" (float 0.0-1.0): how confident you are in your argument

Return JSON with fields: challenge_text, topic_tag, confidence
"""

FIRST_ROUND_CHALLENGE_PROMPT = """\
You are {challenger_label} ({challenger_stance}).

Topic being debated: "{topic}"

Open the debate by making your strongest argument in 2-4 sentences. Be direct and intellectually sharp.
Also assign:
- a "topic_tag" (str): a 2-5 word snake_case label for the sub-topic you are raising
- a "confidence" (float 0.0-1.0): how confident you are in your argument

Return JSON with fields: challenge_text, topic_tag, confidence
"""

JUDGE_PROMPT = """\
You are an impartial arbitrator evaluating an adversarial debate.

Participants:
{participants_json}

Challenges raised:
{challenges_json}

Valid winning_participant_id values (use exactly one of these per verdict):
{winning_options_json}

For each contested topic, return a verdict with:
- topic: the topic string
- winning_participant_id: one of the valid values above, or "unresolved"
- confidence: float 0.0-1.0
- rationale: explanation of the decision (2-3 sentences)
- open_questions: list of unresolved questions (0-3 items)
- consensus_level: "strong", "moderate", or "contested"

Return a JSON object with fields: verdicts, debate_summary, contested_topics.
"""

TRANSLATION_PROMPT = """\
Translate the following text to {locale}. 
Maintain the original tone and meaning. 
If the text contains specific identifiers or formatting (like bullet points or emojis), preserve them.
Return ONLY the translated text, do not add any markdown formatting or preamble.

Text:
{text}

Translation:
"""
