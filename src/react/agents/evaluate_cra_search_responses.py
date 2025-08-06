import os
import json
import asyncio
import logging
import glob
from pathlib import Path
import pydantic
from typing import List, Optional
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from src.utils import (
    AsyncWeaviateKnowledgeBase,
    Configs,
    get_weaviate_async_client,
    gather_with_progress,
)
from src.utils.langfuse.shared_client import langfuse_client, flush_langfuse


# === Load env and logging ===
load_dotenv(verbose=True)
logging.basicConfig(level=logging.INFO)

# === Directories ===
INPUT_DIR = "data/eval_inputs"
OUTPUT_DIR = "output/eval_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Prompt Instructions ===
EVALUATOR_INSTRUCTIONS = """
You are a tax compliance auditor evaluating whether an AI assistant's answer is grounded in CRA (Canada Revenue Agency) documents.

Given the question, the assistant's answer, and a set of CRA documents retrieved based on the question:

- Check if the answer is factually supported by one or more of these documents and retreive document titles.
- Check if the assistant cites specific documents or sections correctly.
- Detect any hallucinated or unsupported claims.
- Rate confidence (0-5) in grounding.

Return a JSON object with:
{
  "valid_response": true|false,
  "hallucinated": true|false,
  "cited_documents": [...],
  "explanation": "...",
  "confidence_score": <0‑5>,
  "final_judgment": "Valid"|"Partially Valid"|"Invalid"
}
"""

# === Query template including retrieved docs ===
EVALUATOR_TEMPLATE = """\
# Question
{question}

# Assistant's Answer
{response}

# Retrieved CRA Documents
{docs}

## Task
Evaluate if the assistant's answer is accurately grounded in the CRA documents listed above.
Respond with the JSON schema specified in instructions.
"""

# === Define dataclasses ===
class EvaluatorQuery(pydantic.BaseModel):
    question: str
    response: str
    docs: List[str]

    def get_query(self) -> str:
        return EVALUATOR_TEMPLATE.format(
            question=self.question,
            response=self.response,
            docs="\n\n".join(self.docs) if self.docs else "No documents retrieved"
        )

class EvaluatorResponse(pydantic.BaseModel):
    valid_response: bool
    hallucinated: bool
    cited_documents: Optional[List[str]]
    explanation: Optional[str]
    confidence_score: int
    final_judgment: str

# === Build evaluator agent ===
async_openai = AsyncOpenAI()

def build_evaluator_agent():
    return Agent(
        name="CRA Evaluator Agent",
        instructions=EVALUATOR_INSTRUCTIONS,
        tools=[],  # No tools — all context is prompt-injected
        model=OpenAIChatCompletionsModel(
            model="gemini-2.5-flash",
            openai_client=async_openai
        ),
        output_type=EvaluatorResponse
    )

async def run_evaluator_agent(query: EvaluatorQuery) -> EvaluatorResponse:
    agent = build_evaluator_agent()
    result = await Runner.run(agent, input=query.get_query())
    return result.final_output_as(EvaluatorResponse)


# === Function to retrieve docs from CRA KB via Weaviate ===
async def retrieve_cra_docs(question: str, kb: AsyncWeaviateKnowledgeBase, top_k=3) -> List[str]:
    hits = await kb.search_knowledgebase(question)
    docs = [f"{hit.source.title}: {hit.highlight.text[0]}" for hit in hits]
    return docs

# === Main batch evaluation ===
async def main():
    configs = Configs.from_env_var()
    async_weaviate_client = get_weaviate_async_client(
        http_host=configs.weaviate_http_host,
        http_port=configs.weaviate_http_port,
        http_secure=configs.weaviate_http_secure,
        grpc_host=configs.weaviate_grpc_host,
        grpc_port=configs.weaviate_grpc_port,
        grpc_secure=configs.weaviate_grpc_secure,
        api_key=configs.weaviate_api_key,
    )
    async_openai_client = AsyncOpenAI()
    cra_kb = AsyncWeaviateKnowledgeBase(async_weaviate_client, collection_name="rbc_2_cra_public_documents")

    file_paths = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
    
    for path in file_paths:
        try:
            with open(path) as f:
                data = json.load(f)
            
            question = data["question"]
            response = data["agent_answer"]
            docs = await retrieve_cra_docs(question, cra_kb)

            eva_query = EvaluatorQuery(question=question, response=response, docs=docs)
            eva_response = await run_evaluator_agent(eva_query)

            result = eva_response.__dict__
            # Save per-file
            out_path = Path(OUTPUT_DIR) / f"{Path(path).stem}_result.json"
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)

            print(f"Saved result for {Path(path).name} to {out_path}")

        except Exception as e:
            print(f"Failed to process {path}: {e}")

    await async_weaviate_client.close()
        
    flush_langfuse()


if __name__ == "__main__":
    asyncio.run(main())
