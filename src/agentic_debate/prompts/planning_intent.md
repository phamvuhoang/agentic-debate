Analyze the following topic and return a JSON object with these fields:
- reframed_topic (str): a clear, debate-ready restatement of the topic
- domain (str): the primary domain
- controversy_level (str): one of "low", "medium", "high"
- recommended_participants (int): the number of distinct viewpoints to include (between {participant_min} and {participant_max})
- recommended_rounds (int): the number of rounds to run (between {round_min} and {round_max})

Topic: {topic}

Return only valid JSON.
