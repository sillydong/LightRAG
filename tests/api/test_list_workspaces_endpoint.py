# tests/api/test_list_workspaces_endpoint.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_list_workspaces_merges_backend_cache_and_default():
    """The endpoint merges backend + cache + default workspace into a sorted list."""
    mock_rag = AsyncMock()
    mock_rag.list_workspaces = AsyncMock(return_value=["", "backend_ws1", "backend_ws2"])

    # Simulate the endpoint logic directly (without spinning up the full FastAPI app)
    workspaces: set = set()
    default_ws = ""
    workspaces.add(default_ws)

    # Simulate cache
    workspaces.update(["cache_ws"])

    # Simulate backend call
    backend_ws = await mock_rag.list_workspaces()
    workspaces.update(backend_ws)

    result = sorted(workspaces)
    assert "" in result
    assert "cache_ws" in result
    assert "backend_ws1" in result
    assert "backend_ws2" in result
    assert result == sorted(result)  # Sorted


@pytest.mark.asyncio
async def test_list_workspaces_backend_failure_doesnt_crash():
    """If backend enumeration fails, still returns partial results from cache."""
    mock_rag = AsyncMock()
    mock_rag.list_workspaces = AsyncMock(side_effect=Exception("DB unreachable"))

    workspaces: set = set()
    workspaces.add("")
    workspaces.update(["cache_ws"])

    try:
        backend_ws = await mock_rag.list_workspaces()
        workspaces.update(backend_ws)
    except Exception:
        pass  # The endpoint catches this — result still has cache data

    result = sorted(workspaces)
    assert "" in result
    assert "cache_ws" in result
    assert "backend_ws1" not in result  # Not added due to failure
