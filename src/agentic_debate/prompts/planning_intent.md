Analyze the following topic and return a JSON object with these fields:
- reframed_topic (str): a clear, debate-ready restatement of the topic
- domain (str): the primary domain
- controversy_level (str): one of "low", "medium", "high"
- recommended_participants (int): the number of distinct viewpoints to include (between 2 and 5)
- recommended_rounds (int): the number of rounds to run (between 1 and 3)

Topic: {topic}

Return only valid JSON.
