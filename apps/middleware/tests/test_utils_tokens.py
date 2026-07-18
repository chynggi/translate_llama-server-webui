from translator_studio.utils.tokens import count_tokens, estimate_tokens


class _OkClient:
    async def count_tokens(self, text: str) -> int:
        return 42


class _FailClient:
    async def count_tokens(self, text: str) -> int:
        raise RuntimeError("llama-server unreachable")


async def test_count_tokens_uses_client():
    assert await count_tokens("hello", _OkClient()) == 42


async def test_count_tokens_falls_back_on_error():
    result = await count_tokens("abcdef", _FailClient())
    assert result == estimate_tokens("abcdef")


async def test_count_tokens_empty_is_zero():
    assert await count_tokens("", _OkClient()) == 0


def test_estimate_tokens_is_positive_and_monotonic():
    assert estimate_tokens("ab") >= 1
    assert estimate_tokens("abcdefgh") > estimate_tokens("ab")
