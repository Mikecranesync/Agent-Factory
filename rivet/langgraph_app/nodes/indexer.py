"""
Indexer Node - Write atoms to database with embeddings

Stores validated atoms in Postgres with pgvector embeddings.
"""

import logging
import requests
from typing import Dict, Any, List
import psycopg
from psycopg.rows import dict_row
from langgraph_app.state import RivetState
from langgraph_app.config import settings

logger = logging.getLogger(__name__)


def indexer_node(state: RivetState) -> Dict[str, Any]:
    """
    Index atoms into PostgreSQL database with embeddings

    Steps:
    1. Generate embeddings for each atom
    2. Insert atoms into database
    3. Insert embeddings for semantic search

    Args:
        state: Current workflow state

    Returns:
        Updated state with indexing stats
    """
    logger.info(f"[{state.job_id}] Indexer node started with {len(state.atoms)} atoms")

    if not state.atoms:
        state.errors.append("No atoms to index")
        return state.dict()

    try:
        # Connect to database
        conn = psycopg.connect(settings.POSTGRES_DSN, row_factory=dict_row)

        indexed_count = 0

        for i, atom in enumerate(state.atoms, 1):
            try:
                # Generate embedding for atom
                embedding = generate_embedding(atom)

                # Insert into database
                insert_atom(conn, atom, embedding)

                indexed_count += 1
                logger.debug(f"[{state.job_id}] Indexed atom {i}/{len(state.atoms)}")

            except Exception as e:
                error_msg = f"Failed to index atom {i}: {str(e)}"
                state.errors.append(error_msg)
                logger.error(f"[{state.job_id}] {error_msg}")

        conn.commit()
        conn.close()

        state.stats["atoms_indexed"] = indexed_count
        state.logs.append(f"Indexed {indexed_count}/{len(state.atoms)} atoms")

        logger.info(f"[{state.job_id}] Indexing complete: {indexed_count} atoms")

    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        state.errors.append(error_msg)
        logger.error(f"[{state.job_id}] {error_msg}")

    return state.dict()


def generate_embedding(atom: Dict[str, Any]) -> List[float]:
    """
    Generate embedding vector for atom using Ollama

    Args:
        atom: Atom dictionary

    Returns:
        Embedding vector (list of floats)
    """
    # Combine relevant fields for embedding
    text_to_embed = f"{atom.get('title', '')} {atom.get('summary', '')} {atom.get('content', '')}"

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": settings.OLLAMA_EMBED_MODEL,
                "prompt": text_to_embed[:1000]  # Limit to 1000 chars
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        embedding = result.get("embedding", [])

        logger.debug(f"Generated embedding of dimension {len(embedding)}")
        return embedding

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        # Return zero vector as fallback
        return [0.0] * 768  # Typical embedding dimension


def insert_atom(conn: psycopg.Connection, atom: Dict[str, Any], embedding: List[float]) -> None:
    """
    Insert atom into database with embedding

    Args:
        conn: Database connection
        atom: Atom dictionary
        embedding: Embedding vector
    """
    cursor = conn.cursor()

    # Convert embedding to pgvector format
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'

    # Insert atom
    cursor.execute("""
        INSERT INTO knowledge_atoms (
            atom_type, vendor, product,
            title, summary, content,
            code, symptoms, causes, fixes,
            pattern_type, prerequisites, steps,
            keywords, difficulty,
            source_url, source_pages,
            embedding
        ) VALUES (
            %(atom_type)s, %(vendor)s, %(product)s,
            %(title)s, %(summary)s, %(content)s,
            %(code)s, %(symptoms)s, %(causes)s, %(fixes)s,
            %(pattern_type)s, %(prerequisites)s, %(steps)s,
            %(keywords)s, %(difficulty)s,
            %(source_url)s, %(source_pages)s,
            %(embedding)s::vector
        )
    """, {
        "atom_type": atom.get("atom_type"),
        "vendor": atom.get("vendor"),
        "product": atom.get("product"),
        "title": atom.get("title"),
        "summary": atom.get("summary"),
        "content": atom.get("content"),
        "code": atom.get("code"),
        "symptoms": atom.get("symptoms", []),
        "causes": atom.get("causes", []),
        "fixes": atom.get("fixes", []),
        "pattern_type": atom.get("pattern_type"),
        "prerequisites": atom.get("prerequisites", []),
        "steps": atom.get("steps", []),
        "keywords": atom.get("keywords", []),
        "difficulty": atom.get("difficulty"),
        "source_url": atom.get("source_url"),
        "source_pages": atom.get("source_pages"),
        "embedding": embedding_str
    })

    cursor.close()
