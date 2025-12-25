import argparse
import json
import os
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI

def call_judge_llm(atom: Dict, judge_prompt: str) -> Dict:
    """
    Calls the judge LLM to evaluate a single knowledge atom.

    Args:
        atom: The knowledge atom to evaluate.
        judge_prompt: The prompt to use for the judge LLM.

    Returns:
        The evaluation results as a dictionary.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    
    prompt = f"{judge_prompt}\n\nInput Atom:\n{json.dumps(atom, indent=2)}"
    
    response = llm.invoke(prompt)
    
    try:
        # The response from the LLM is a string that needs to be parsed into a JSON object.
        # The response may contain markdown, so we need to find the JSON part.
        json_start = response.content.find('{')
        json_end = response.content.rfind('}') + 1
        json_response = response.content[json_start:json_end]
        return json.loads(json_response)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing JSON from LLM response: {e}")
        print(f"LLM response: {response.content}")
        return {"error": "Failed to parse JSON from LLM response", "atom_id": atom.get("id")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # Get the directory of the script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Construct the path to the judge prompt file
    judge_prompt_path = os.path.join(script_dir, '..', '..', 'docs', 'knowledge', 'knowledge_atom_judge_prompt.md')

    with open(judge_prompt_path, "r", encoding="utf-8") as f:
        judge_prompt = f.read()

    with open(args.input, "r", encoding="utf-8") as f:
        atoms: List[Dict] = json.load(f)
    
    evals: List[Dict] = []
    for atom in atoms:
        result = call_judge_llm(atom, judge_prompt)
        evals.append(result)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(evals, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
