import os
import json
import asyncio
import logging
import glob
from dotenv import load_dotenv
from agents import RunConfig, Runner
from src.react.agent import ReactAgentManager, create_react_agent

load_dotenv(verbose=True)

# Configuration
INPUT_DIR = "data/summary/"
OUTPUT_DIR = "data/transcript_summary_output_json/"
no_tracing_config = RunConfig(tracing_disabled=True)

# Prompt for extracting structured financial info
TRANSCRIPT_SUMMARY_EXTRACTION_PROMPT = """
You are a wealth management assistant. Review summaries of advisor-client meetings.
If a client's does not hold any Canadian assests, return an empty JSON. 

Extract the following information from the meeting summary:
1. Client's profile
2. Topics discussed related to Canadian tax regulations
3. Products discussed (e.g. TFSA, RRSP, GIC, Stocks)
4. Current investments or accounts
5. Advisor's recommendations
6. Any questions or concerns raised by the client

Return only a valid JSON object. Do not include any explanations or markdown formatting like ```json.

Use this format:
{
  "client_profile": [...],
  "topics_discussed": [...]  
  "goals": [...],
  "products_discussed": [...],
  "current_investments": [...],
  "recommendations": [...],
  "client_questions": [...]
}
Ensure the JSON is syntactically correct and complete.
"""


class TranscriptSummaryExtractionAgent:
    def __init__(self):
        self.agent_manager = ReactAgentManager()

    async def initialize_agent(self):
        await self.agent_manager.initialize(agent_name="Transcript Summary Extraction Agent")
        self.agent_manager.agent.instructions = TRANSCRIPT_SUMMARY_EXTRACTION_PROMPT

    async def cleanup_agent(self):
        await self.agent_manager.cleanup()

    async def process_transcript_file(self, transcript_path: str):
        agent = self.agent_manager.get_agent()

        filename = os.path.basename(transcript_path)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")

        with open(transcript_path, "r") as f:
            transcript = f.read()

        response = await Runner.run(
            agent,
            input=transcript,
            run_config=no_tracing_config,
        )

        raw_output = response.final_output.strip()

        # Clean backtick-wrapped JSON, if present
        if raw_output.startswith("```"):
            if raw_output.startswith("```json") and raw_output.endswith("```"):
                raw_output = raw_output[7:-3].strip()
            elif raw_output.startswith("```") and raw_output.endswith("```"):
                raw_output = raw_output[3:-3].strip()

        try:
            structured_data = json.loads(raw_output)
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON for {filename}. Raw output:\n{response.final_output}")
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_path, "w") as out_f:
            json.dump(structured_data, out_f, indent=2)

        logging.info(f"Processed and saved: {output_path}")

    async def run_batch(self):
        await self.initialize_agent()

        transcript_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.md")))
        if not transcript_files:
            logging.warning("No transcript files found in input directory.")
            return

        for transcript_file in transcript_files:
            await self.process_transcript_file(transcript_file)

        await self.cleanup_agent()


async def main():
    logging.basicConfig(level=logging.INFO)
    runner = TranscriptSummaryExtractionAgent()
    await runner.run_batch()


if __name__ == "__main__":
    asyncio.run(main())
