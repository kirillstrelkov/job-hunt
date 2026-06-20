def get_agent():
    settings = GoogleModelSettings(google_thinking_config={"thinking_budget": 0})

    return Agent(
        model="gemini-2.5-flash-lite",
        output_type=EmotionAnalysis,
        instructions="""
        You are an expert audio sentiment analyzer. Listen to the provided audio and analyze:
        1. The primary emotions expressed by the speaker
        2. The overall sentiment polarity (positive/negative/neutral)
        3. The intensity of the emotional expression
        4. A brief description of the emotional characteristics and a rationale for your choices
        Be precise and analytical in your assessment.
        """,
        model_settings=settings,
    )
