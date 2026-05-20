import httpx

PODCAST_INDEX_BASE = "https://api.podcastindex.org/api/1.0"


async def search_podcast(query: str, limit: int = 5) -> list[dict]:
    """搜索播客，返回候选列表"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PODCAST_INDEX_BASE}/search/byterm",
            params={"q": query, "max": limit},
        )
        data = resp.json()
    feeds = data.get("feeds", [])
    return [
        {
            "title": f["title"],
            "description": f.get("description", ""),
            "url": f["url"],
            "image": f.get("image", ""),
        }
        for f in feeds
    ]


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_podcast",
        "description": "搜索播客节目，根据用户兴趣或当前场景推荐",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词，如'科技 脱口秀'"},
            },
            "required": ["query"],
        },
    },
}
