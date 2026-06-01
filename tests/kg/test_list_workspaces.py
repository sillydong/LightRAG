# tests/kg/test_list_workspaces.py
import os
import tempfile

import pytest
from lightrag.base import StorageNameSpace
from lightrag.kg.json_doc_status_impl import JsonDocStatusStorage
from lightrag.kg.networkx_impl import NetworkXStorage


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


@pytest.mark.asyncio
async def test_base_list_workspaces_can_be_overridden():
    """Verify the method is overridable by concrete implementations."""

    class _OverrideStorage(_ConcreteStorage):
        async def list_workspaces(self) -> list[str]:
            return ["ws1", "ws2"]

    storage = _OverrideStorage(
        namespace="test_ns",
        workspace="ws1",
        global_config={},
    )
    result = await storage.list_workspaces()
    assert result == ["ws1", "ws2"]


# ---------------------------------------------------------------------------
# JsonDocStatusStorage tests
# ---------------------------------------------------------------------------


def _make_json_doc_status(working_dir: str, workspace: str = "") -> JsonDocStatusStorage:
    storage = JsonDocStatusStorage.__new__(JsonDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = workspace
    storage.global_config = {"working_dir": working_dir}
    # Simulate __post_init__ side-effect: compute _file_name
    if workspace:
        ws_dir = os.path.join(working_dir, workspace)
        os.makedirs(ws_dir, exist_ok=True)
        storage._file_name = os.path.join(ws_dir, "kv_store_doc_status.json")
    else:
        storage._file_name = os.path.join(working_dir, "kv_store_doc_status.json")
    storage._data = None
    storage._storage_lock = None
    storage.storage_updated = None
    return storage


@pytest.mark.asyncio
async def test_json_doc_status_list_workspaces_multiple():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create workspace directories with sentinel files
        for ws in ("alpha", "beta", "gamma"):
            ws_dir = os.path.join(tmpdir, ws)
            os.makedirs(ws_dir)
            open(os.path.join(ws_dir, "kv_store_doc_status.json"), "w").close()
        # Root workspace sentinel
        open(os.path.join(tmpdir, "kv_store_doc_status.json"), "w").close()

        storage = _make_json_doc_status(tmpdir, "alpha")
        result = await storage.list_workspaces()
        assert result == ["", "alpha", "beta", "gamma"]


@pytest.mark.asyncio
async def test_json_doc_status_list_workspaces_skips_dirs_without_sentinel():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Directory without sentinel should be ignored
        os.makedirs(os.path.join(tmpdir, "empty_dir"))
        # Directory with sentinel
        ws_dir = os.path.join(tmpdir, "valid_ws")
        os.makedirs(ws_dir)
        open(os.path.join(ws_dir, "kv_store_doc_status.json"), "w").close()

        storage = _make_json_doc_status(tmpdir, "valid_ws")
        result = await storage.list_workspaces()
        assert result == ["valid_ws"]


@pytest.mark.asyncio
async def test_json_doc_status_list_workspaces_skips_invalid_names():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Directories with non-alphanumeric/underscore characters should be ignored
        bad_dir = os.path.join(tmpdir, "bad-ws")
        os.makedirs(bad_dir)
        open(os.path.join(bad_dir, "kv_store_doc_status.json"), "w").close()
        # Valid directory
        good_dir = os.path.join(tmpdir, "good_ws")
        os.makedirs(good_dir)
        open(os.path.join(good_dir, "kv_store_doc_status.json"), "w").close()

        storage = _make_json_doc_status(tmpdir, "good_ws")
        result = await storage.list_workspaces()
        assert result == ["good_ws"]


@pytest.mark.asyncio
async def test_json_doc_status_list_workspaces_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = _make_json_doc_status(tmpdir, "ws1")
        result = await storage.list_workspaces()
        assert result == []


# ---------------------------------------------------------------------------
# NetworkXStorage tests
# ---------------------------------------------------------------------------


def _make_networkx_storage(working_dir: str, workspace: str = "") -> NetworkXStorage:
    storage = NetworkXStorage.__new__(NetworkXStorage)
    storage.namespace = "chunk_entity_relation"
    storage.workspace = workspace
    storage.global_config = {"working_dir": working_dir}
    storage.embedding_func = None
    storage.cosine_better_than_threshold = 0.2
    storage.meta_fields = set()
    return storage


@pytest.mark.asyncio
async def test_networkx_list_workspaces_multiple():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Root workspace graph file
        open(os.path.join(tmpdir, "graph_chunk_entity_relation.graphml"), "w").close()
        # Named workspace graph files
        for ws in ("ws1", "ws2"):
            ws_dir = os.path.join(tmpdir, ws)
            os.makedirs(ws_dir)
            open(os.path.join(ws_dir, "graph_chunk_entity_relation.graphml"), "w").close()

        storage = _make_networkx_storage(tmpdir, "ws1")
        result = await storage.list_workspaces()
        assert result == ["", "ws1", "ws2"]


@pytest.mark.asyncio
async def test_networkx_list_workspaces_skips_no_graphml():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "empty_dir"))
        storage = _make_networkx_storage(tmpdir, "ws1")
        result = await storage.list_workspaces()
        assert result == []



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


@pytest.mark.asyncio
async def test_base_list_workspaces_can_be_overridden():
    """Verify the method is overridable by concrete implementations."""

    class _OverrideStorage(_ConcreteStorage):
        async def list_workspaces(self) -> list[str]:
            return ["ws1", "ws2"]

    storage = _OverrideStorage(
        namespace="test_ns",
        workspace="ws1",
        global_config={},
    )
    result = await storage.list_workspaces()
    assert result == ["ws1", "ws2"]
