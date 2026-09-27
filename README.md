# 🏋️ NovaFit AI — Personal Fitness & Workout Coach Agent

![NovaFit AI Live Agent Demo](./agent_demo.gif)

**NovaFit AI** is an intelligent, conversational fitness coach built with the Google Agent Development Kit (ADK) and Gemini. NovaFit AI helps users plan personalized workout routines, query an exercise database, track workout logs, calculate training metrics, search nearby fitness venues, generate form illustrations, and stream exercise video demonstrations.

---

## 🌟 Key Features & Google Cloud Architecture

### 🧠 Cross-Session Long-Term Memory
- **Vertex AI Memory Bank**: Integrates `PreloadMemoryTool` and an event callback (`add_session_to_memory`) to remember user preferences, fitness goals, medical conditions, and allergies across sessions. NovaFit automatically tailors all routines and nutritional guidance around user health restrictions.

### 🗄️ Exercise Database & Workout Logging
- **Google Cloud Firestore**: Interacts with a Firestore database to:
  - Search exercise catalogs by keyword, target muscle group, and difficulty level (`search_exercises`).
  - Retrieve detailed exercise mechanics, equipment requirements, and safety tips (`get_exercise_details`).
  - Add custom exercises into the user database (`add_custom_exercise`).
  - Log completed workouts with sets, reps, weight, and duration (`log_workout`).

### 🎨 Generative Media (Images & Videos)
- **Imagen (`gemini-3.1-flash-lite-image`)**: Generates custom workout form illustrations and motivational visual guides (`generate_fitness_image`), uploading outputs to Google Cloud Storage.
- **Gemini Omni Model (`gemini-omni-flash-preview`)**: Generates short video demonstrations for exercises (`generate_exercise_video`).
- **Google Cloud Storage (GCS)**: Stores generated image and video assets in a public Cloud Storage bucket and returns direct HTTPS URLs for instant in-app rendering.
- **ADK Artifacts**: Saves generated media directly into the ADK Playground Artifacts panel using `tool_context.save_artifact`.

### 🖥️ Rich A2UI Interface Rendering
- **Google ADK A2UI Engine**: Uses `A2uiSchemaManager`, `BasicCatalog`, and `a2ui_callback` to emit rich UI cards (Cards, Columns, Rows, Text, and Images) natively rendered in both ADK Web and custom frontends.

### 🧪 Secure Code Execution & Calculations
- **Vertex AI Agent Engine Sandbox**: Executes Python calculations in a sandboxed environment (`AgentEngineSandboxCodeExecutor`) for complex math and metrics.
- **Fitness Calculations**:
  - `calculate_heart_rate_zones`: Target heart rate training zones based on age and resting heart rate.
  - `calculate_one_rep_max`: Estimated 1-Rep Max (1RM) using Epley & Brzycki formulas.
  - `fetch_nutrition_info`: Macronutrient and caloric breakdowns for meal items.

### 📍 Location & Venue Search
- **Google Maps Platform APIs**:
  - `geocode_address`: Converts text addresses into geographic coordinates.
  - `find_nearby_places`: Discovers nearby gyms, fitness centers, and outdoor parks.

---

## 📁 Repository Structure

```text
fitness-coach-agent/
├── app/
│   ├── agent.py            # ADK Root Agent definition, tools, and callbacks
│   ├── tools.py            # Firestore, GCS, Imagen, Omni, Maps, and calc tools
│   ├── a2ui_utils.py       # A2UI callback transformer for rich card display
│   └── fast_api_app.py     # FastAPI server proxying A2A requests
├── frontend/
│   ├── main.py             # FastAPI entrypoint for web UI
│   └── static/
│       └── index.html      # Modern chat interface with Dark Mode & prompt chips
├── agents-cli-manifest.yaml# ADK agent manifest configuration
├── deployment_metadata.json# Agent Runtime deployment metadata
└── agent_demo.gif          # Looping demo recording
```

---

## 🛠️ Local Setup & Running Instructions

### Prerequisites
- Python 3.10+
- Google Cloud Project with Vertex AI, Firestore, and Cloud Storage enabled
- Authenticated `gcloud` CLI (`gcloud auth application-default login`)

### 1. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export GOOGLE_CLOUD_PROJECT="<your-gcp-project-id>"
export GOOGLE_CLOUD_REGION="us-east1"
export GOOGLE_MAPS_API_KEY="<your-google-maps-api-key>"
export AGENT_ENGINE_RESOURCE_NAME="<your-agent-runtime-resource-name>"
export AGENT_DIRECTORY="app"
```

### 3. Run the Agent Locally with ADK Web
```bash
adk web app/
```

### 4. Run the FastAPI Proxy & Frontend Locally
```bash
cd frontend
python main.py
```
*(Open your browser to the local server port displayed in the console output to interact with NovaFit AI.)*
