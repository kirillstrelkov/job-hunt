"""Helper constants for Pandas DataFrame columns."""

from typing import ClassVar


class ModelStatsDisplayCols:
    """Display column names for Model execution stats DataFrame."""

    MODEL = "Model"
    TOTAL_TIME = "Total Time (s)"
    LOAD_TIME = "Load Time (s)"
    PROMPT_TOKENS = "Prompt Tokens"
    GEN_TOKENS = "Gen Tokens"
    GEN_SPEED = "Gen Speed (t/s)"
    RESPONSE_CHARS = "Response Chars"
    RESPONSE_WORDS = "Response Words"
    GPU_USAGE = "GPU Usage"
    GPU_INFO = "GPU Info"
    OPTIONS = "Options"

    COLUMNS: ClassVar[list[str]] = [
        MODEL,
        TOTAL_TIME,
        LOAD_TIME,
        PROMPT_TOKENS,
        GEN_TOKENS,
        GEN_SPEED,
        RESPONSE_CHARS,
        RESPONSE_WORDS,
        GPU_USAGE,
        GPU_INFO,
        OPTIONS,
    ]


class ModelStatsCols:
    """Raw column names and clean display names for Model execution stats DataFrame."""

    MODEL = "model"
    TOTAL_TIME = "total_time"
    LOAD_TIME = "load_time"
    PROMPT_TOKENS = "prompt_tokens"
    GEN_TOKENS = "gen_tokens"
    TOKENS_PER_SEC = "tokens_per_sec"
    CHAR_COUNT = "char_count"
    WORD_COUNT = "word_count"
    GPU_USAGE = "gpu_usage"
    GPU_INFO = "gpu_info"
    OPTIONS_STR = "options_str"

    # Preserved ordering of columns for the dataframe
    COLUMNS_ORDER: ClassVar[list[str]] = [
        MODEL,
        TOTAL_TIME,
        LOAD_TIME,
        PROMPT_TOKENS,
        GEN_TOKENS,
        TOKENS_PER_SEC,
        CHAR_COUNT,
        WORD_COUNT,
        GPU_USAGE,
        GPU_INFO,
        OPTIONS_STR,
    ]

    # Readable display name mappings
    DISPLAY_MAP: ClassVar[dict[str, str]] = {
        MODEL: ModelStatsDisplayCols.MODEL,
        TOTAL_TIME: ModelStatsDisplayCols.TOTAL_TIME,
        LOAD_TIME: ModelStatsDisplayCols.LOAD_TIME,
        PROMPT_TOKENS: ModelStatsDisplayCols.PROMPT_TOKENS,
        GEN_TOKENS: ModelStatsDisplayCols.GEN_TOKENS,
        TOKENS_PER_SEC: ModelStatsDisplayCols.GEN_SPEED,
        CHAR_COUNT: ModelStatsDisplayCols.RESPONSE_CHARS,
        WORD_COUNT: ModelStatsDisplayCols.RESPONSE_WORDS,
        GPU_USAGE: ModelStatsDisplayCols.GPU_USAGE,
        GPU_INFO: ModelStatsDisplayCols.GPU_INFO,
        OPTIONS_STR: ModelStatsDisplayCols.OPTIONS,
    }

    # Readable display columns in correct order
    DISPLAY_COLUMNS: ClassVar[list[str]] = ModelStatsDisplayCols.COLUMNS

