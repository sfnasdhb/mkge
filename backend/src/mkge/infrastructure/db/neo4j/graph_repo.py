"""
Neo4j Graph Repository.
Tuân theo PROJECT_CONTEXT.md §4.2:
  Nodes: :Drug :Disease :Symptom :Document :Chunk
  Rels:  :TREATS :CAUSES_SE :HAS_SYMPTOM :COMORBID :CONTAINS :MENTIONS
  source_chunk_ids non-empty trên mỗi rel y khoa (anti-hallucination)
"""
import uuid
from typing import Sequence

from neo4j import AsyncDriver

from src.mkge.domain.entities.chunk import Chunk
from src.mkge.domain.entities.graph import EntityType, MedicalEntity, Relationship


_LABEL_BY_TYPE: dict[EntityType, str] = {
    EntityType.drug: "Drug",
    EntityType.disease: "Disease",
    EntityType.symptom: "Symptom",
}


class GraphRepository:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    async def ensure_constraints(self) -> None:
        async with self.driver.session() as session:
            for label in ("Drug", "Disease", "Symptom"):
                await session.run(
                    f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
                )
                await session.run(
                    f"CREATE INDEX {label.lower()}_norm IF NOT EXISTS "
                    f"FOR (n:{label}) ON (n.normalized_name)"
                )
            await session.run(
                "CREATE CONSTRAINT document_id IF NOT EXISTS "
                "FOR (d:Document) REQUIRE d.id IS UNIQUE"
            )
            await session.run(
                "CREATE CONSTRAINT chunk_id IF NOT EXISTS "
                "FOR (c:Chunk) REQUIRE c.id IS UNIQUE"
            )

    # --- Document + Chunks ----------------------------------------------

    async def upsert_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
    ) -> None:
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (d:Document {id: $id})
                SET d.user_id = $user_id, d.filename = $filename
                """,
                id=str(document_id),
                user_id=str(user_id),
                filename=filename,
            )

    async def create_chunks_batch(self, chunks: Sequence[Chunk]) -> None:
        if not chunks:
            return
        async with self.driver.session() as session:
            await session.run(
                """
                UNWIND $chunks AS c
                MATCH (d:Document {id: c.document_id})
                MERGE (chunk:Chunk {id: c.id})
                SET chunk.document_id = c.document_id,
                    chunk.page = c.page,
                    chunk.text = c.text,
                    chunk.qdrant_id = c.qdrant_id
                MERGE (d)-[:CONTAINS]->(chunk)
                """,
                chunks=[
                    {
                        "id": str(c.id),
                        "document_id": str(c.document_id),
                        "page": c.page,
                        "text": c.text,
                        "qdrant_id": str(c.qdrant_id) if c.qdrant_id else None,
                    }
                    for c in chunks
                ],
            )

    async def create_mentions_batch(
        self, mentions: Sequence[tuple[uuid.UUID, uuid.UUID]]
    ) -> None:
        """mentions = [(chunk_id, entity_id), ...]"""
        if not mentions:
            return
        async with self.driver.session() as session:
            await session.run(
                """
                UNWIND $pairs AS p
                MATCH (c:Chunk {id: p.chunk_id})
                MATCH (e) WHERE e.id = p.entity_id
                  AND (e:Drug OR e:Disease OR e:Symptom)
                MERGE (c)-[:MENTIONS]->(e)
                """,
                pairs=[
                    {"chunk_id": str(cid), "entity_id": str(eid)}
                    for cid, eid in mentions
                ],
            )

    # --- Entities + Relationships ---------------------------------------

    async def create_entities_batch(self, entities: Sequence[MedicalEntity]) -> None:
        if not entities:
            return
        by_type: dict[EntityType, list[MedicalEntity]] = {}
        for e in entities:
            by_type.setdefault(e.type, []).append(e)

        async with self.driver.session() as session:
            for etype, items in by_type.items():
                label = _LABEL_BY_TYPE[etype]
                await session.run(
                    f"""
                    UNWIND $entities AS e
                    MERGE (n:{label} {{id: e.id}})
                    SET n.name = e.name,
                        n.normalized_name = e.normalized_name,
                        n.document_id = e.document_id,
                        n.description = e.description
                    """,
                    entities=[
                        {
                            "id": str(e.id),
                            "name": e.name,
                            "normalized_name": e.normalized_name,
                            "document_id": str(e.document_id),
                            "description": e.description,
                        }
                        for e in items
                    ],
                )

    async def create_relationships_batch(
        self, relationships: Sequence[Relationship]
    ) -> None:
        if not relationships:
            return
        by_type: dict[str, list[Relationship]] = {}
        for r in relationships:
            by_type.setdefault(r.type.value, []).append(r)

        async with self.driver.session() as session:
            for rel_type, rels in by_type.items():
                await session.run(
                    f"""
                    UNWIND $rels AS r
                    MATCH (s) WHERE s.id = r.source_id AND (s:Drug OR s:Disease OR s:Symptom)
                    MATCH (t) WHERE t.id = r.target_id AND (t:Drug OR t:Disease OR t:Symptom)
                    MERGE (s)-[rel:{rel_type} {{id: r.id}}]->(t)
                    SET rel.document_id = r.document_id,
                        rel.confidence = r.confidence,
                        rel.evidence = r.evidence,
                        rel.source_chunk_ids = r.source_chunk_ids
                    """,
                    rels=[
                        {
                            "id": str(r.id),
                            "source_id": str(r.source_id),
                            "target_id": str(r.target_id),
                            "document_id": str(r.document_id),
                            "confidence": r.confidence,
                            "evidence": r.evidence,
                            "source_chunk_ids": [str(c) for c in r.source_chunk_ids],
                        }
                        for r in rels
                    ],
                )

    # --- Queries --------------------------------------------------------

    async def get_graph_for_document(self, document_id: uuid.UUID) -> dict:
        async with self.driver.session() as session:
            nodes_result = await session.run(
                """
                MATCH (e) WHERE e.document_id = $doc_id
                  AND (e:Drug OR e:Disease OR e:Symptom)
                RETURN e.id AS id,
                       e.name AS name,
                       labels(e)[0] AS label,
                       e.normalized_name AS normalized_name,
                       e.description AS description
                """,
                doc_id=str(document_id),
            )
            nodes = []
            async for record in nodes_result:
                d = dict(record)
                d["type"] = d.pop("label", "").upper()
                nodes.append(d)

            edges_result = await session.run(
                """
                MATCH (s)-[r]->(t)
                WHERE r.document_id = $doc_id
                  AND (s:Drug OR s:Disease OR s:Symptom)
                  AND (t:Drug OR t:Disease OR t:Symptom)
                RETURN r.id AS id, s.id AS source, t.id AS target,
                       type(r) AS type, r.confidence AS confidence,
                       r.evidence AS evidence,
                       r.source_chunk_ids AS source_chunk_ids
                """,
                doc_id=str(document_id),
            )
            edges = [dict(record) async for record in edges_result]

        return {"nodes": nodes, "edges": edges}

    async def delete_graph_for_document(self, document_id: uuid.UUID) -> None:
        async with self.driver.session() as session:
            # Xóa cả entity, chunk, document node của document này
            await session.run(
                """
                MATCH (n) WHERE n.document_id = $doc_id
                  AND (n:Drug OR n:Disease OR n:Symptom OR n:Chunk)
                DETACH DELETE n
                """,
                doc_id=str(document_id),
            )
            await session.run(
                "MATCH (d:Document {id: $doc_id}) DETACH DELETE d",
                doc_id=str(document_id),
            )

    async def get_overview(self) -> dict:
        async with self.driver.session() as session:
            type_counts: dict[str, int] = {}
            for label in ("Drug", "Disease", "Symptom"):
                r = await session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
                rec = await r.single()
                type_counts[label.upper()] = rec["c"] if rec else 0

            rel_count_result = await session.run(
                """
                MATCH ()-[r]->()
                WHERE type(r) IN ['TREATS','CAUSES_SE','HAS_SYMPTOM','COMORBID']
                RETURN count(r) AS c
                """
            )
            rel_record = await rel_count_result.single()
            rel_count = rel_record["c"] if rel_record else 0

        return {"entity_counts_by_type": type_counts, "relationship_count": rel_count}

    async def get_subgraph_by_entities(self, entity_ids: list[str]) -> dict:
        if not entity_ids:
            return {"nodes": [], "edges": []}
            
        async with self.driver.session() as session:
            nodes_result = await session.run(
                """
                MATCH (e) WHERE e.id IN $entity_ids AND (e:Drug OR e:Disease OR e:Symptom)
                OPTIONAL MATCH (e)-[r]-(n) WHERE (n:Drug OR n:Disease OR n:Symptom)
                WITH collect(e) AS es, collect(n) AS ns
                UNWIND (es + ns) AS node
                WITH DISTINCT node
                WHERE node IS NOT NULL
                RETURN node.id AS id,
                       node.name AS name,
                       labels(node)[0] AS label,
                       node.normalized_name AS normalized_name,
                       node.description AS description
                """,
                entity_ids=entity_ids,
            )
            nodes = []
            async for record in nodes_result:
                d = dict(record)
                d["type"] = d.pop("label", "").upper()
                nodes.append(d)

            node_ids = [n["id"] for n in nodes]
            edges = []
            if node_ids:
                edges_result = await session.run(
                    """
                    MATCH (s)-[r]->(t)
                    WHERE s.id IN $node_ids AND t.id IN $node_ids
                    RETURN r.id AS id, s.id AS source, t.id AS target,
                           type(r) AS type, r.confidence AS confidence,
                           r.evidence AS evidence,
                           r.source_chunk_ids AS source_chunk_ids
                    """,
                    node_ids=node_ids,
                )
                edges = [dict(record) async for record in edges_result]

        return {"nodes": nodes, "edges": edges}
