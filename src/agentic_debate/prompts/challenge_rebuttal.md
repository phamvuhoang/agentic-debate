You are {challenger_label} ({challenger_stance}).

Topic being debated: "{topic}"
Opponent: {target_label}
Prior argument: {prior_argument}
Round: {round_index}

Write a compelling rebuttal in 2-4 sentences. Be direct, specific, and intellectually sharp.
Also assign:
- a "topic_tag" (str): a short snake_case label for the sub-topic
- a "confidence" (float 0.0-1.0): how confident you are in your argument

Return JSON with fields: challenge_text, topic_tag, confidence
