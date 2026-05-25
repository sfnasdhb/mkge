import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.mkge.application.query.service import GraphRAGQueryService


@pytest.mark.anyio
@patch("src.mkge.application.query.service.redis.from_url")
@patch("src.mkge.application.query.service.embed_text")
@patch("src.mkge.application.query.service.VectorRepository")
@patch("src.mkge.application.query.service.generate_graphrag_answer")
@patch("src.mkge.application.query.service.QueryHistoryRepository")
@patch("src.mkge.application.query.service.GraphRepository")
async def test_query_flow_cache_miss(
    mock_graph_repo_class,
    mock_history_repo_class,
    mock_generate_answer,
    mock_vector_repo_class,
    mock_embed_text,
    mock_redis_from_url,
):
    # Setup Redis mock
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Cache miss
    mock_redis_from_url.return_value = mock_redis
    
    # Setup Embed text mock
    mock_embed_text.return_value = [0.1] * 768
    
    # Setup Qdrant search mock returning relevant chunks
    mock_vector_repo = MagicMock()
    mock_vector_repo.search.return_value = [
        {"text": "Aspirin lowers risk of heart attacks", "page": 1, "doc_id": "doc1", "entity_ids": ["aspirin-id", "heart-attack-id"]}
    ]
    mock_vector_repo_class.return_value = mock_vector_repo
    
    # Setup Neo4j graph repo mock returning subgraph
    mock_graph_repo = AsyncMock()
    mock_graph_repo.get_subgraph_by_entities.return_value = {
        "nodes": [
            {"id": "aspirin-id", "name": "Aspirin", "type": "DRUG"},
            {"id": "heart-attack-id", "name": "Myocardial Infarction", "type": "DISEASE"}
        ],
        "edges": [
            {"source": "aspirin-id", "target": "heart-attack-id", "type": "TREATS"}
        ]
    }
    mock_graph_repo_class.return_value = mock_graph_repo
    
    # Setup LLM response mock
    mock_generate_answer.return_value = "Aspirin can be used to treat heart attacks."
    
    # Setup Postgres session + QueryHistoryRepository
    db_mock = MagicMock()
    history_repo_instance = mock_history_repo_class.return_value
    history_repo_instance.create = AsyncMock()

    with patch("src.mkge.infrastructure.db.postgres.audit_repo.AuditRepository") as mock_audit_repo:
        audit_instance = mock_audit_repo.return_value
        audit_instance.create = AsyncMock()
        
        service = GraphRAGQueryService(neo4j_driver=MagicMock(), db=db_mock)
        user_uuid = str(uuid.uuid4())
        
        res = await service.query("What does Aspirin treat?", user_id=user_uuid)
        
        assert res["answer"] == "Aspirin can be used to treat heart attacks."
        assert len(res["citations"]) == 1
        assert res["citations"][0]["doc_id"] == "doc1"
        assert len(res["subgraph"]["nodes"]) == 2
        
        # Verify integrations
        mock_embed_text.assert_called_once()
        mock_vector_repo.search.assert_called_once()
        mock_graph_repo.get_subgraph_by_entities.assert_called_once()
        mock_generate_answer.assert_called_once()
        mock_redis.set.assert_called_once()
        history_repo_instance.create.assert_called_once()
        audit_instance.create.assert_called_once()
