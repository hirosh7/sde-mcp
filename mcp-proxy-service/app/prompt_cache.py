"""Prompt-caching helpers shared by the Claude adapters"""


def mark_last_turn_for_cache(messages: list) -> None:
    """Put a cache breakpoint on the last replayed history turn.

    The history is rebuilt the same way on every call, so the next call in the
    session reads system + history up to here from the cache. The new query is
    appended after this point and is the only uncached part.

    Every turn is converted to text-block form, so a turn sends the same bytes
    whether or not it carries the breakpoint on this call.
    """
    for message in messages:
        if isinstance(message["content"], str):
            message["content"] = [{"type": "text", "text": message["content"]}]
    if messages:
        last = messages[-1]["content"]
        last[-1] = {**last[-1], "cache_control": {"type": "ephemeral"}}
