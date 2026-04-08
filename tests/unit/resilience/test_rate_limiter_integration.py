"""Unit tests for rate limiter integration with aiolimiter."""

import asyncio

import pytest
from aiolimiter import AsyncLimiter


class TestRateLimiterIntegration:
    """Test aiolimiter rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_allows_requests_under_rate(self) -> None:
        """AsyncLimiter allows N requests within time period."""
        limiter = AsyncLimiter(max_rate=3, time_period=1.0)

        results = []
        for i in range(3):
            async with limiter:
                results.append(i)

        assert results == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_blocks_over_rate_requests(self) -> None:
        """AsyncLimiter blocks N+1th request until capacity replenishes."""
        limiter = AsyncLimiter(max_rate=2, time_period=1.0)
        timestamps = []

        async def timed_call() -> None:
            async with limiter:
                timestamps.append(asyncio.get_event_loop().time())

        tasks = [timed_call(), timed_call(), timed_call()]
        await asyncio.gather(*tasks)

        assert len(timestamps) == 3
        time_span = timestamps[-1] - timestamps[0]
        assert time_span >= 0.45

    @pytest.mark.asyncio
    async def test_has_capacity_check_non_blocking(self) -> None:
        """has_capacity() checks without blocking."""
        limiter = AsyncLimiter(max_rate=2, time_period=1.0)

        assert limiter.has_capacity()

        async with limiter:
            pass
        async with limiter:
            pass

        assert not limiter.has_capacity()
