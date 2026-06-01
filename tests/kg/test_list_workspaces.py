# tests/kg/test_list_workspaces.py
import pytest
from lightrag.base import StorageNameSpace


class _ConcreteStorage(StorageNameSpace):
    """Minimal concrete subclass satisfying abstract methods."""

    async def index_done_callback(self) -> None:
        pass

    async def drop(self) -> dict:
        return {"status": "success", "message": "data dropped"}


@pytest.mark.asyncio
async def test_base_list_workspaces_returns_empty_list():
    storage = _ConcreteStorage(
        namespace="test_ns",
        workspace="ws1",
        global_config={},
    )
    result = await storage.list_workspaces()
    assert result == []
