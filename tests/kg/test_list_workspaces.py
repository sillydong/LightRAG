# tests/kg/test_list_workspaces.py
import os
import tempfile

import pytest
from lightrag.base import StorageNameSpace
from lightrag.kg.json_doc_status_impl import JsonDocStatusStorage
from lightrag.kg.networkx_impl import NetworkXStorage


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


# ---------------------------------------------------------------------------
# PGDocStatusStorage tests
# ---------------------------------------------------------------------------

from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_pg_doc_status_list_workspaces():
    from lightrag.kg.postgres_impl import PGDocStatusStorage

    storage = PGDocStatusStorage.__new__(PGDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = "ws1"
    storage.global_config = {}

    mock_db = MagicMock()
    mock_db.query = AsyncMock(
        return_value=[
            {"workspace": ""},
            {"workspace": "ws1"},
            {"workspace": "ws2"},
        ]
    )
    storage.db = mock_db

    result = await storage.list_workspaces()
    assert result == ["", "ws1", "ws2"]
    mock_db.query.assert_awaited_once()
    called_sql = mock_db.query.call_args[0][0]
    assert "DISTINCT" in called_sql.upper()
    assert "LIGHTRAG_DOC_STATUS" in called_sql.upper()


@pytest.mark.asyncio
async def test_pg_doc_status_list_workspaces_no_db():
    """Returns [] gracefully when db is not yet initialized."""
    from lightrag.kg.postgres_impl import PGDocStatusStorage

    storage = PGDocStatusStorage.__new__(PGDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = "ws1"
    storage.global_config = {}
    storage.db = None

    result = await storage.list_workspaces()
    assert result == []


# ---------------------------------------------------------------------------
# MongoDocStatusStorage tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mongo_doc_status_list_workspaces():
    from lightrag.kg.mongo_impl import MongoDocStatusStorage

    storage = MongoDocStatusStorage.__new__(MongoDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = "ws1"
    storage.final_namespace = "ws1_doc_status"
    storage.global_config = {}

    mock_db = AsyncMock()
    mock_db.list_collection_names = AsyncMock(
        return_value=[
            "doc_status",           # root workspace
            "ws1_doc_status",
            "ws2_doc_status",
            "ws1_text_chunks",      # should be ignored (wrong namespace)
            "unrelated_collection", # should be ignored
        ]
    )
    storage.db = mock_db

    result = await storage.list_workspaces()
    assert result == ["", "ws1", "ws2"]


@pytest.mark.asyncio
async def test_mongo_doc_status_list_workspaces_no_db():
    from lightrag.kg.mongo_impl import MongoDocStatusStorage

    storage = MongoDocStatusStorage.__new__(MongoDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = "ws1"
    storage.final_namespace = "ws1_doc_status"
    storage.global_config = {}
    storage.db = None

    result = await storage.list_workspaces()
    assert result == []


# ---------------------------------------------------------------------------
# RedisDocStatusStorage tests
# ---------------------------------------------------------------------------

from contextlib import asynccontextmanager


def _make_redis_doc_status_storage(workspace: str = "ws1"):
    """Build a RedisDocStatusStorage-like object with fields we need."""
    from lightrag.kg.redis_impl import RedisDocStatusStorage

    storage = RedisDocStatusStorage.__new__(RedisDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = workspace if workspace else "_"
    storage.final_namespace = (
        f"{workspace}_doc_status" if workspace else "doc_status"
    )
    storage.global_config = {}
    storage._initialized = True

    mock_redis = AsyncMock()

    @asynccontextmanager
    async def _conn():
        yield mock_redis

    storage._get_redis_connection = _conn
    storage._mock_redis = mock_redis
    return storage


@pytest.mark.asyncio
async def test_redis_doc_status_list_workspaces():
    from lightrag.kg.redis_impl import LIGHTRAG_WORKSPACE_REGISTRY_KEY

    storage = _make_redis_doc_status_storage("ws1")
    storage._mock_redis.smembers = AsyncMock(
        return_value={b"", b"ws1", b"ws2"}
    )

    result = await storage.list_workspaces()
    assert result == ["", "ws1", "ws2"]
    storage._mock_redis.smembers.assert_awaited_once_with(LIGHTRAG_WORKSPACE_REGISTRY_KEY)


@pytest.mark.asyncio
async def test_redis_doc_status_list_workspaces_root_workspace():
    """Root workspace (empty string) is represented as '' in registry."""
    from lightrag.kg.redis_impl import LIGHTRAG_WORKSPACE_REGISTRY_KEY

    storage = _make_redis_doc_status_storage("")  # root workspace
    storage._mock_redis.smembers = AsyncMock(return_value={b""})

    result = await storage.list_workspaces()
    assert result == [""]


@pytest.mark.asyncio
async def test_redis_doc_status_initialize_registers_workspace():
    from lightrag.kg.redis_impl import LIGHTRAG_WORKSPACE_REGISTRY_KEY
    from unittest.mock import patch

    storage = _make_redis_doc_status_storage("ws1")
    storage._mock_redis.ping = AsyncMock(return_value=True)
    storage._mock_redis.sadd = AsyncMock(return_value=1)
    storage._initialized = False

    @asynccontextmanager
    async def _fake_lock():
        yield

    with patch("lightrag.kg.redis_impl.get_data_init_lock", _fake_lock):
        await storage.initialize()

    storage._mock_redis.sadd.assert_awaited_once_with(LIGHTRAG_WORKSPACE_REGISTRY_KEY, "ws1")


@pytest.mark.asyncio
async def test_redis_doc_status_drop_deregisters_workspace():
    from lightrag.kg.redis_impl import LIGHTRAG_WORKSPACE_REGISTRY_KEY

    storage = _make_redis_doc_status_storage("ws1")
    storage._mock_redis.scan = AsyncMock(return_value=(0, []))
    storage._mock_redis.srem = AsyncMock(return_value=1)

    result = await storage.drop()
    assert result["status"] == "success"
    storage._mock_redis.srem.assert_awaited_once_with(LIGHTRAG_WORKSPACE_REGISTRY_KEY, "ws1")


# ---------------------------------------------------------------------------
# Neo4JStorage tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_neo4j_list_workspaces():
    from lightrag.kg.neo4j_impl import Neo4JStorage

    storage = Neo4JStorage.__new__(Neo4JStorage)
    storage.namespace = "chunk_entity_relation"
    storage.workspace = "ws1"
    storage.global_config = {}
    storage.embedding_func = None
    storage.cosine_better_than_threshold = 0.2
    storage.meta_fields = set()
    storage._DATABASE = "neo4j"

    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[
        {"name": "base"},
        {"name": "ws1"},
        {"name": "ws2"},
    ])
    mock_result.consume = AsyncMock()

    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_driver = MagicMock()
    mock_driver.session = MagicMock(return_value=mock_session)
    storage._driver = mock_driver

    result = await storage.list_workspaces()
    assert result == ["base", "ws1", "ws2"]


@pytest.mark.asyncio
async def test_neo4j_list_workspaces_no_driver():
    from lightrag.kg.neo4j_impl import Neo4JStorage

    storage = Neo4JStorage.__new__(Neo4JStorage)
    storage.workspace = "ws1"
    storage.global_config = {}
    storage._driver = None

    result = await storage.list_workspaces()
    assert result == []


# ---------------------------------------------------------------------------
# MemgraphStorage tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memgraph_list_workspaces():
    from lightrag.kg.memgraph_impl import MemgraphStorage

    storage = MemgraphStorage.__new__(MemgraphStorage)
    storage.namespace = "chunk_entity_relation"
    storage.workspace = "ws1"
    storage.global_config = {}
    storage.embedding_func = None
    storage.cosine_better_than_threshold = 0.2
    storage.meta_fields = set()

    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[{"name": "base"}, {"name": "ws1"}])
    mock_result.consume = AsyncMock()

    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_driver = MagicMock()
    mock_driver.session = MagicMock(return_value=mock_session)
    storage._driver = mock_driver

    result = await storage.list_workspaces()
    assert result == ["base", "ws1"]


@pytest.mark.asyncio
async def test_memgraph_list_workspaces_no_driver():
    from lightrag.kg.memgraph_impl import MemgraphStorage

    storage = MemgraphStorage.__new__(MemgraphStorage)
    storage.workspace = "ws1"
    storage.global_config = {}
    storage._driver = None

    result = await storage.list_workspaces()
    assert result == []


# ---------------------------------------------------------------------------
# OpenSearchDocStatusStorage tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_opensearch_doc_status_list_workspaces():
    from unittest.mock import AsyncMock, MagicMock

    from lightrag.kg.opensearch_impl import OpenSearchDocStatusStorage

    storage = OpenSearchDocStatusStorage.__new__(OpenSearchDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = "ws1"
    storage.final_namespace = "ws1_doc_status"
    storage._index_name = "ws1_doc_status"
    storage.global_config = {}

    mock_client = AsyncMock()
    mock_client.indices = MagicMock()
    mock_client.indices.get = AsyncMock(
        return_value={
            "doc_status": {},           # root workspace
            "ws1_doc_status": {},
            "ws2_doc_status": {},
            "ws1_text_chunks": {},      # different namespace — should be ignored
        }
    )
    storage.client = mock_client

    result = await storage.list_workspaces()
    assert result == ["", "ws1", "ws2"]


@pytest.mark.asyncio
async def test_opensearch_doc_status_list_workspaces_no_client():
    from lightrag.kg.opensearch_impl import OpenSearchDocStatusStorage

    storage = OpenSearchDocStatusStorage.__new__(OpenSearchDocStatusStorage)
    storage.namespace = "doc_status"
    storage.workspace = "ws1"
    storage.final_namespace = "ws1_doc_status"
    storage._index_name = "ws1_doc_status"
    storage.global_config = {}
    storage.client = None

    result = await storage.list_workspaces()
    assert result == []
