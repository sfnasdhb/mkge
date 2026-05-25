"""
Wipe toàn bộ data Neo4j (giữ schema). Chạy trước khi test pipeline mới.

Cẩn thận: XÓA TOÀN BỘ NODES + RELATIONSHIPS.
"""
import asyncio
from neo4j import AsyncGraphDatabase
from src.mkge.config import settings


async def wipe():
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        async with driver.session() as session:
            r = await session.run("MATCH (n) RETURN count(n) AS c")
            rec = await r.single()
            before = rec["c"] if rec else 0
            await session.run("MATCH (n) DETACH DELETE n")
            r2 = await session.run("MATCH (n) RETURN count(n) AS c")
            rec2 = await r2.single()
            after = rec2["c"] if rec2 else 0
            print(f"Wiped {before} nodes → remaining {after}")
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(wipe())
