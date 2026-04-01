Generate a debate team for the following topic.

Original topic: {topic}
Reframed topic: {reframed_topic}
Domain: {domain}
Controversy level: {controversy_level}
Participant count: {participant_count}
Round count: {round_count}

Return a JSON object with a "participants" array. Each participant has:
- participant_id (str): a unique snake_case identifier
- label (str): a short display name
- role (str): their role in the debate
- stance (str): their position in one sentence

Ensure the viewpoints are distinct and adversarial.
Return only valid JSON.
