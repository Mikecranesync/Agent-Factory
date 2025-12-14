"""
Indexer node: Store atoms in Postgres with pgvector embeddings
"""

import logging
import psycopg
import requests
from typing import List, Dict, Any
from langgraph_app.state import RivetState
from langgraph_app.config import settings

logger = logging.getLogger(__name__)


def generate_embedding(text: str, model: str = None) -> List[float]:
    """Generate embedding vector using Ollama"""
    model = model or settings.OLLAMA_EMBED_MODEL
    url = f"{settings.OLLAMA_BASE_URL}/api/embeddings"

    payload = {"model": model, "prompt": text}

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json().get("embedding", [])


def indexer_node(state: RivetState) -> RivetState:
    """Index atoms into Postgres with pgvector"""
    state.logs.append("Starting indexing")

    if not state.atoms:
        state.errors.append("No atoms to index")
        return state

    try:
        with psycopg.connect(settings.POSTGRES_DSN) as conn:
            indexed_count = 0

            for atom in state.atoms:
                searchable_text = f"{atom.get('title', '')} {atom.get('content', '')}"
                embedding = generate_embedding(searchable_text)

                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO knowledge_atoms (
                            atom_type, title, content, embedding, source_url
                        ) VALUES (%s, %s, %s, %s::vector, %s) RETURNING id""",
                        (atom.get("type"), atom.get("title"), atom.get("content"),
                         embedding, state.source_url)
                    )
                    conn.commit()
                    indexed_count += 1

            state.atoms_indexed = indexed_count
            state.logs.append(f"Indexed {indexed_count} atoms")

    except Exception as e:
        state.errors.append(f"Indexing failed: {str(e)}")

    return state
