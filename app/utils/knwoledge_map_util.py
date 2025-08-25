from typing import Any, Dict, List, Optional
from itertools import combinations

from loguru import logger
from sqlalchemy import and_

from app.constants import ChatGptMessagePayload
from app.database.models.knowledge_map_node_document import NodeDocumentModel
from app.database.models.knowledge_map_nodes import KnowledgeNodeModel
from app.database.object_repository import ObjectRepository
from app.database.query_manager import query_with_filter, query_with_join_and_filter
from app.database.models.knowledge_map_edges import KnowledgeEdgeModel
from app.utils.c_gpt import fetch_response_from_model


def normalize_topic(name: str) -> str:
    return " ".join(name.strip().split())


def update_knowledge_map_nodes_for_user(user_id: str, topics_list: List[str]):
    for topic in topics_list:
        knowledge_map_node: KnowledgeNodeModel = KnowledgeNodeModel(
            user_id=user_id, name=normalize_topic(topic)
        )

        ObjectRepository.insert_single_object(
            object_to_be_inserted=knowledge_map_node, without_upsert_call=True
        )
        logger.info(f"Update knowledge map node for user. Latest node: {knowledge_map_node.id}")


def update_knowledge_map_node_document_for_user(
    user_id: str, file_id: str, node_id: str, page_number: str
):
    knowledge_map_node_document: NodeDocumentModel = NodeDocumentModel(
        user_id=user_id, file_id=file_id, node_id=node_id, page_number=page_number
    )
    ObjectRepository.insert_single_object(knowledge_map_node_document, without_upsert_call=True)
    logger.info(
        f"Update knowledge map node docuemnt for user. Latest node docuemnt: {knowledge_map_node_document.id}"
    )


def _upsert_edge(user_id: str, a: str, b: str) -> bool:
    """
    Create an edge between node a and b for user_id if it does not already exist.
    Returns True if inserted, False if already existed.
    Always stores (src, tgt) in sorted order to avoid duplicates.
    """
    src, tgt = (a, b) if a < b else (b, a)

    edge = KnowledgeEdgeModel(
        user_id=user_id,
        source_node_id=src,
        target_node_id=tgt,
    )
    ObjectRepository.insert_single_object(object_to_be_inserted=edge, without_upsert_call=True)
    logger.info(f"Created edge {edge.id} for user={user_id} ({src} ↔ {tgt})")

    return True


def update_knowledge_map_edges_for_file(user_id: str, file_id: str, node_id: str) -> int:
    other_ids = get_other_nodes_for_file(user_id, file_id, node_id)
    created = 0
    for other_id in other_ids:
        created += 1 if _upsert_edge(user_id, node_id, other_id) else 0
    return created


def get_other_nodes_for_file(user_id: str, file_id: str, exclude_node_id: str) -> list[str]:
    rows = query_with_join_and_filter(
        model=[NodeDocumentModel.node_id.label("node_id")],
        join=(KnowledgeNodeModel, KnowledgeNodeModel.id == NodeDocumentModel.node_id),
        isouter=False,
        filters=and_(
            NodeDocumentModel.file_id == file_id,
            KnowledgeNodeModel.user_id == user_id,
            NodeDocumentModel.node_id != exclude_node_id,
        ),
        group_by=(NodeDocumentModel.node_id,),
        order_by=None,
        limit=None,
        offset=None,
    )
    logger.info(f"response from get_other_nodes_for_file: {rows}")
    return [r.node_id for r in rows if r.get("node_id") is not None]


def get_all_nodes_for_file(user_id: str, file_id: str) -> List[str]:
    """
    All node_ids linked to this file for this user (deduped).
    """
    rows = query_with_join_and_filter(
        model=[NodeDocumentModel.node_id.label("node_id")],
        join=(KnowledgeNodeModel, KnowledgeNodeModel.id == NodeDocumentModel.node_id),
        isouter=False,
        filters=and_(
            NodeDocumentModel.file_id == file_id,
            KnowledgeNodeModel.user_id == user_id,
        ),
        group_by=(NodeDocumentModel.node_id,),
    )
    logger.info(f"Rows from get_all_nodes_for_file : {rows}")
    return [r.node_id for r in rows if r.node_id]


def fetch_pairs_in_topics(
    new_topics: List[str], existing_topics: List[str]
) -> List[Dict[str, str]]:
    """
    Uses LLM to decide relatedness between new and existing topics.
    Returns list of {"a": new_topic, "b": existing_topic} for related pairs.
    """
    if not new_topics or not existing_topics:
        return []

    payload = ChatGptMessagePayload.get_message_payload_for_topic_relations(
        new_topics, existing_topics
    )
    data = fetch_response_from_model(payload) or {}
    results = data.get("results", [])

    logger.info(f"Response for knowledgem map : {results}")

    related_pairs = [{"a": r["a"], "b": r["b"]} for r in results if r.get("related") is True]
    return related_pairs


def update_full_knowledge_map_for_file(
    user_id: str,
    file_id: str,
    topics_list: List[str],
    page_number: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full update pipeline for a file:
      1. Add nodes for new topics
      2. Link them to file in NodeDocumentModel
      3. Find related topics (new ↔ existing and new ↔ new)
      4. Create edges between related nodes
    """
    # Normalize + dedupe
    norm_topics = sorted(set(normalize_topic(t) for t in topics_list if t and t.strip()))
    if not norm_topics:
        return {"nodeIds": [], "edgesCreated": 0}

    # Insert nodes for these topics
    update_knowledge_map_nodes_for_user(user_id, norm_topics)

    # Map topic → node_id (after insert)
    topic_id_map = {}
    rows = query_with_filter(
        model=KnowledgeNodeModel,
        filters=and_(
            KnowledgeNodeModel.user_id == user_id,
            KnowledgeNodeModel.name.in_(norm_topics),
        ),
    )
    for r in rows:
        topic_id_map[r.name] = r.id

    # Link each node to file
    for topic, node_id in topic_id_map.items():
        update_knowledge_map_node_document_for_user(
            user_id=user_id, file_id=file_id, node_id=node_id, page_number=page_number or ""
        )

    # Fetch existing topics from other files
    existing_rows = query_with_join_and_filter(
        model=(KnowledgeNodeModel,),
        join=(NodeDocumentModel, NodeDocumentModel.node_id == KnowledgeNodeModel.id),
        isouter=False,
        filters=and_(KnowledgeNodeModel.user_id == user_id, NodeDocumentModel.file_id != file_id),
        group_by=(KnowledgeNodeModel.id,),
    )
    logger.info(f"Rows: {existing_rows}")
    existing_topics_map = {r.name: r.id for r in existing_rows}

    # Step 6: Relatedness check using GPT
    related_pairs = []
    if existing_topics_map:
        related_pairs.extend(
            fetch_pairs_in_topics(list(topic_id_map.keys()), list(existing_topics_map.keys()))
        )
    if len(topic_id_map) > 1:
        combos = list(combinations(topic_id_map.keys(), 2))
        related_pairs.extend(fetch_pairs_in_topics([a for a, _ in combos], [b for _, b in combos]))

    edges_created = 0
    for pair in related_pairs:
        a_id = topic_id_map.get(pair["a"]) or existing_topics_map.get(pair["a"])
        b_id = topic_id_map.get(pair["b"]) or existing_topics_map.get(pair["b"])
        if a_id and b_id:
            if _upsert_edge(user_id, a_id, b_id):
                edges_created += 1

    logger.info(
        f"[KM] file={file_id} user={user_id} nodes={len(topic_id_map)} edges_created={edges_created}"
    )
    return {"nodeIds": list(topic_id_map.values()), "edgesCreated": edges_created}


def get_knowledge_map_for_user(
    user_id: str, file_id: Optional[str] = None
) -> Dict[str, List[Dict]]:
    """
    Fetch the knowledge map for a user.
    If file_id is provided, fetch only nodes & edges related to that file.
    Response is manually formatted (no dict_response from query).
    """
    # --- Fetch nodes ---
    if file_id:
        node_ids = get_all_nodes_for_file(user_id=user_id, file_id=file_id)
        node_objs = query_with_filter(
            filters=KnowledgeNodeModel.id.in_(node_ids), model=KnowledgeNodeModel
        )
    else:
        node_objs = query_with_filter(
            filters=KnowledgeNodeModel.user_id == user_id, model=KnowledgeNodeModel
        )

    nodes_list = [{"id": node.id, "name": node.name, "user_id": node.user_id} for node in node_objs]

    if file_id:
        node_ids_set = {n["id"] for n in nodes_list}
        edge_objs = query_with_filter(
            filters=and_(
                KnowledgeEdgeModel.user_id == user_id,
                KnowledgeEdgeModel.source_node_id.in_(node_ids_set),
                KnowledgeEdgeModel.target_node_id.in_(node_ids_set),
            ),
            model=KnowledgeEdgeModel,
        )
    else:
        edge_objs = query_with_filter(
            filters=KnowledgeEdgeModel.user_id == user_id, model=KnowledgeEdgeModel
        )

    edges_list = [
        {
            "id": edge.id,
            "source_node_id": edge.source_node_id,
            "target_node_id": edge.target_node_id,
            "user_id": edge.user_id,
        }
        for edge in edge_objs
    ]

    return {"nodes": nodes_list, "edges": edges_list}
