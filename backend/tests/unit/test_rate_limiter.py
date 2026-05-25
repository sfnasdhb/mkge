import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.mkge.infrastructure.cache.redis import check_rate_limit


@pytest.mark.anyio
@patch("src.mkge.infrastructure.cache.redis._get_redis")
async def test_rate_limit_allowed(mock_get_redis):
    # Mock Redis pipeline
    mock_redis = MagicMock()
    mock_pipeline = AsyncMock()
    mock_redis.pipeline.return_value = mock_pipeline
    mock_get_redis.return_value = mock_redis
    
    # Mock pipeline execution return values
    # results[1] is zcard which returns the number of requests in the window
    mock_pipeline.execute.return_value = [None, 3, None, None]

    allowed, count = await check_rate_limit("user-1", "query", max_count=5)
    
    assert allowed is True
    assert count == 3
    
    # Verify pipeline operations
    mock_pipeline.zremrangebyscore.assert_called_once()
    mock_pipeline.zcard.assert_called_once()
    mock_pipeline.zadd.assert_called_once()
    mock_pipeline.expire.assert_called_once()


@pytest.mark.anyio
@patch("src.mkge.infrastructure.cache.redis._get_redis")
async def test_rate_limit_exceeded(mock_get_redis):
    # Mock Redis pipeline
    mock_redis = MagicMock()
    mock_pipeline = AsyncMock()
    mock_redis.pipeline.return_value = mock_pipeline
    mock_redis.zrem = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    # results[1] is zcard which is 5 (equal to max_count, so not allowed)
    mock_pipeline.execute.return_value = [None, 5, None, None]

    allowed, count = await check_rate_limit("user-1", "query", max_count=5)
    
    assert allowed is False
    assert count == 5
    
    # Denied request should cleanup the added event
    mock_redis.zrem.assert_called_once()
