TRANSLATION_PROMPT = """\
Translate the following text to {locale}. 
Maintain the original tone and meaning. 
If the text contains specific identifiers or formatting (like bullet points or emojis), preserve them.
Return ONLY the translated text, do not add any markdown formatting or preamble.

Text:
{text}

Translation:
"""
