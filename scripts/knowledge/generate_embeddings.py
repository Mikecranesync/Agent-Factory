"""
Generate embeddings for knowledge atoms using OpenAI API.

Usage:
    poetry run python scripts/knowledge/generate_embeddings.py \
        --input data/atoms-core-repos.json \
        --output data/atoms-with-embeddings.json \
        --model text-embedding-3-small
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import openai
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_atoms(input_path: Path) -> List[Dict[str, Any]]:
    """Load atoms from JSON file."""
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)
        # Handle both raw list and wrapped structure with metadata
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'atoms' in data:
            return data['atoms']
        else:
            raise ValueError("Invalid JSON structure: expected list or dict with 'atoms' key")


def generate_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Generate embedding using OpenAI API."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


def create_embedding_text(atom: Dict[str, Any]) -> str:
    """Create text to embed from atom fields."""
    parts = [
        atom.get("title", ""),
        atom.get("summary", ""),
        atom.get("content", "")
    ]
    # Add keywords if present
    if "keywords" in atom:
        parts.append(" ".join(atom["keywords"]))

    return " ".join(filter(None, parts))


def add_embeddings(atoms: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """Add embeddings to atoms."""
    atoms_with_embeddings = []

    for atom in tqdm(atoms, desc="Generating embeddings"):
        embedding_text = create_embedding_text(atom)
        embedding = generate_embedding(embedding_text, model)

        atom_with_embedding = atom.copy()
        atom_with_embedding["embedding"] = embedding
        atoms_with_embeddings.append(atom_with_embedding)

    return atoms_with_embeddings


def calculate_cost(num_atoms: int, avg_tokens_per_atom: int = 200, model: str = "text-embedding-3-small") -> float:
    """Calculate estimated cost."""
    # text-embedding-3-small: $0.02 per 1M tokens
    total_tokens = num_atoms * avg_tokens_per_atom
    cost_per_token = 0.02 / 1_000_000
    return total_tokens * cost_per_token


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for knowledge atoms")
    parser.add_argument("--input", default="data/atoms-core-repos.json", help="Input JSON file")
    parser.add_argument("--output", default="data/atoms-with-embeddings.json", help="Output JSON file")
    parser.add_argument("--model", default="text-embedding-3-small", help="OpenAI embedding model")
    parser.add_argument("--dry-run", action="store_true", help="Show cost estimate without running")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Load atoms
    atoms = load_atoms(input_path)
    print(f"Loaded {len(atoms)} atoms from {input_path}")

    # Cost estimate
    estimated_cost = calculate_cost(len(atoms))
    print(f"Estimated cost: ${estimated_cost:.4f}")

    if args.dry_run:
        print("Dry run - exiting without generating embeddings")
        return

    # Generate embeddings
    atoms_with_embeddings = add_embeddings(atoms, args.model)

    # Save to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(atoms_with_embeddings, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(atoms_with_embeddings)} atoms with embeddings to {output_path}")

    # Verify embedding dimensions
    sample_embedding = atoms_with_embeddings[0]["embedding"]
    print(f"Embedding dimensions: {len(sample_embedding)}")
    print(f"Sample embedding (first 5 values): {sample_embedding[:5]}")


if __name__ == "__main__":
    main()
