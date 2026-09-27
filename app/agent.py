# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.memory import VertexAiMemoryBankService
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

from app.tools import (
    search_exercises,
    get_exercise_details,
    add_custom_exercise,
    log_workout,
    calculate_heart_rate_zones,
    calculate_one_rep_max,
    fetch_nutrition_info,
    geocode_address,
    find_nearby_places,
    generate_fitness_image,
    generate_exercise_video,
)

# Load Agent Engine resource name from deployment_metadata.json if available
metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
remote_agent_runtime_id = None
memory_bank_id = "7645904903507804160"

if metadata_file.exists():
    try:
        with open(metadata_file) as f:
            metadata = json.load(f)
            remote_agent_runtime_id = metadata.get("remote_agent_runtime_id")
            if remote_agent_runtime_id:
                memory_bank_id = remote_agent_runtime_id.split("/")[-1]
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=remote_agent_runtime_id
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to send completed session events to Vertex AI Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


def memory_bank_service_builder():
    """Memory service builder for deployed Agent Runtime or local Runner instantiation."""
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-01-1e2398f3750c",
        location="us-east1",
        agent_engine_id=memory_bank_id,
    )


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    elif "ny" in query.lower() or "new york" in query.lower():
        tz_identifier = "America/New_York"
    else:
        tz_identifier = "UTC"

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are NovaFit, an expert AI Fitness and Workout Coach. "
        "Your mission is to guide users through personalized workout routines, "
        "provide exercise details from your Firestore library, log completed workouts, "
        "calculate heart rate training zones and one-rep max targets, look up "
        "nutrition facts, locate nearby gyms or parks, generate fitness form illustrations, "
        "and execute Python code in a secure Agent Engine sandbox for complex calculations. "
        "MEMORY & HEALTH INSTRUCTION: You remember all user facts, preferences, medical conditions, "
        "and user allergies (such as food, drug, or environmental allergies) across sessions via Memory Bank. "
        "Always review preloaded user memories at the start of every session to identify any allergies or dietary restrictions, "
        "and strictly tailor all fitness, nutrition, and workout advice to accommodate and protect against those allergies."
    ),
    workflow_description="Analyze the user request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="fitness_coach_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        search_exercises,
        get_exercise_details,
        add_custom_exercise,
        log_workout,
        calculate_heart_rate_zones,
        calculate_one_rep_max,
        fetch_nutrition_info,
        geocode_address,
        find_nearby_places,
        generate_fitness_image,
        generate_exercise_video,
        get_current_time,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
