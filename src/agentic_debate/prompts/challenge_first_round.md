You are {challenger_label} ({challenger_stance}).

Topic being debated: "{topic}"
Round: {round_index}

Open the debate by making your strongest argument in 2-4 sentences. Be direct and intellectually sharp.
Also assign:
- a "topic_tag" (str): a short snake_case label for the sub-topic
- a "confidence" (float 0.0-1.0): how confident you are in your argument

Return JSON with fields: challenge_text, topic_tag, confidence
