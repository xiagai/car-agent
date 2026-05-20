from .podcast import search_podcast, TOOL_SPEC as PODCAST_TOOL

ALL_TOOLS = [PODCAST_TOOL]

TOOL_HANDLERS = {
    "search_podcast": search_podcast,
}
