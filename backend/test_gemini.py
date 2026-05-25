"""
Chạy: python test_gemini.py
Test toàn bộ pipeline 3 stages (parsing skipped vì input là text, không phải PDF):
  - Stage 2: Gemini NER
  - Stage 3: Groq Llama verification
"""
import logging
import sys
import uuid

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

from src.mkge.application.pipeline.ner import extract_entities_and_relations
from src.mkge.application.pipeline.service import build_graph_from_text


SAMPLE_TEXT = """
Bệnh nhân nam 65 tuổi được chẩn đoán tăng huyết áp và đái tháo đường type 2.
Triệu chứng bao gồm đau đầu, chóng mặt và khó thở khi gắng sức.
Bác sĩ kê đơn Enalapril 10mg để điều trị tăng huyết áp, kèm Metformin 500mg
cho đái tháo đường. Bệnh nhân cũng được chỉ định Atorvastatin 20mg để điều trị
rối loạn lipid máu. Amlodipine được thêm vào do huyết áp chưa kiểm soát tốt.
Enalapril chống chỉ định trong thai kỳ. Metformin có thể gây buồn nôn và tiêu chảy.
Bệnh nhân được làm điện tâm đồ và siêu âm tim để đánh giá biến chứng tim mạch.
"""


def main():
    print("=" * 70)
    print("STAGE 2: Gemini NER trực tiếp")
    print("=" * 70)
    try:
        result = extract_entities_and_relations(SAMPLE_TEXT)
        print(f"\n→ Entities raw: {len(result['entities'])}")
        for e in result["entities"]:
            print(f"   • {e}")
        print(f"\n→ Relationships raw: {len(result['relationships'])}")
        for r in result["relationships"]:
            print(f"   • {r}")
    except Exception as exc:
        print(f"\n!!! Gemini call FAILED: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 70)
    print("STAGE 2 + 3: NER → dedupe → Groq verification")
    print("=" * 70)
    entities, relationships = build_graph_from_text(SAMPLE_TEXT, uuid.uuid4())
    print(f"\n→ Final entities: {len(entities)}")
    for e in entities:
        print(f"   • [{e.type.value}] {e.name} (norm={e.normalized_name})")
    print(f"\n→ Final verified relationships: {len(relationships)}")
    for r in relationships:
        src = next((e for e in entities if e.id == r.source_id), None)
        tgt = next((e for e in entities if e.id == r.target_id), None)
        src_name = src.name if src else "?"
        tgt_name = tgt.name if tgt else "?"
        print(f"   • [{r.type.value}] {src_name} → {tgt_name} (conf={r.confidence:.2f})")


if __name__ == "__main__":
    main()
