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

import os
import json
import uuid
import base64
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.cloud import firestore, storage
from google.adk.tools import ToolContext

load_dotenv()

PROJECT_ID = "qwiklabs-gcp-01-1e2398f3750c"
GCS_BUCKET_NAME = "qwiklabs-gcp-01-1e2398f3750c-fitness-media"


def get_firestore_client():
    return firestore.Client(project=PROJECT_ID)


def search_exercises(category: str = "", target_muscle: str = "") -> List[Dict[str, Any]]:
    """Search for exercises in the catalog by category or target muscle group.

    Args:
        category: Optional category filter (e.g. Strength, Cardio, Core).
        target_muscle: Optional muscle group filter (e.g. Chest, Quadriceps, Abs, Biceps, Full Body).

    Returns:
        A list of matching exercise documents with their details.
    """
    db = get_firestore_client()
    docs = db.collection("exercises").stream()
    results = []
    
    cat_query = category.lower().strip() if category else ""
    muscle_query = target_muscle.lower().strip() if target_muscle else ""

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        
        doc_category = (data.get("category") or "").lower()
        doc_muscle = (data.get("target_muscle") or data.get("muscle_group") or "").lower()
        
        matches_cat = not cat_query or cat_query in doc_category
        matches_muscle = not muscle_query or muscle_query in doc_muscle
        
        if matches_cat and matches_muscle:
            results.append(data)
            
    return results


def get_exercise_details(exercise_id: str) -> Dict[str, Any]:
    """Retrieve detailed information about a specific exercise by its ID.

    Args:
        exercise_id: The ID of the exercise (e.g. push_ups, barbell_squats, plank).

    Returns:
        A dictionary containing exercise details or an error message if not found.
    """
    db = get_firestore_client()
    doc_ref = db.collection("exercises").document(exercise_id.strip().lower())
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    else:
        return {"error": f"Exercise '{exercise_id}' not found in the database."}


def add_custom_exercise(
    name: str,
    category: str,
    target_muscle: str,
    difficulty: str,
    instructions: str,
    equipment: str = "None",
) -> Dict[str, Any]:
    """Add a new custom exercise to the Firestore exercise library.

    Args:
        name: Name of the exercise.
        category: Category (e.g. Strength, Cardio, Flexibility, Core).
        target_muscle: Primary muscle worked (e.g. Chest, Back, Legs, Core).
        difficulty: Difficulty level (Beginner, Intermediate, Advanced).
        instructions: Instructions on how to perform the movement safely.
        equipment: Required equipment (e.g. Dumbbells, Barbell, None).

    Returns:
        A dictionary acknowledging successful addition to Firestore.
    """
    db = get_firestore_client()
    doc_id = name.lower().replace(" ", "_").replace("-", "_")
    doc_ref = db.collection("exercises").document(doc_id)
    
    exercise_data = {
        "name": name,
        "category": category,
        "target_muscle": target_muscle,
        "difficulty": difficulty,
        "instructions": instructions,
        "equipment": equipment,
    }
    doc_ref.set(exercise_data)
    
    return {
        "status": "success",
        "message": f"Added '{name}' to Firestore exercise database with ID '{doc_id}'.",
        "exercise": exercise_data,
    }


def log_workout(
    user_id: str,
    exercise_name: str,
    sets: int,
    reps: int,
    weight_lbs: float = 0.0,
) -> Dict[str, Any]:
    """Log a completed workout set/session for a user into Firestore.

    Args:
        user_id: ID or username of the person logging the workout.
        exercise_name: The name of the exercise performed.
        sets: Number of sets completed.
        reps: Number of repetitions per set.
        weight_lbs: Weight used in pounds (if applicable).

    Returns:
        A dictionary confirmation of the logged workout.
    """
    db = get_firestore_client()
    log_ref = db.collection("workout_logs").document()
    
    log_data = {
        "user_id": user_id,
        "exercise_name": exercise_name,
        "sets": sets,
        "reps": reps,
        "weight_lbs": weight_lbs,
        "timestamp": firestore.SERVER_TIMESTAMP,
    }
    log_ref.set(log_data)
    
    return {
        "status": "success",
        "log_id": log_ref.id,
        "message": f"Logged workout for {user_id}: {sets} sets of {reps} reps for {exercise_name}.",
    }


def calculate_heart_rate_zones(age: int, resting_hr: int = 60) -> Dict[str, Any]:
    """Calculate target heart rate training zones using the Karvonen formula.

    Args:
        age: Age of the user in years.
        resting_hr: Resting heart rate in beats per minute (bpm). Defaults to 60.

    Returns:
        A dictionary containing max heart rate, heart rate reserve, and calculated target bpm ranges for each zone.
    """
    max_hr = 220 - age
    hrr = max_hr - resting_hr

    def zone_range(min_pct: float, max_pct: float) -> str:
        low = round(resting_hr + (hrr * min_pct))
        high = round(resting_hr + (hrr * max_pct))
        return f"{low} - {high} bpm"

    return {
        "age": age,
        "max_heart_rate": max_hr,
        "resting_heart_rate": resting_hr,
        "zones": {
            "Warm Up (50-60%)": zone_range(0.50, 0.60),
            "Fat Burn (60-70%)": zone_range(0.60, 0.70),
            "Aerobic / Endurance (70-80%)": zone_range(0.70, 0.80),
            "Anaerobic / Performance (80-90%)": zone_range(0.80, 0.90),
            "Peak / Maximum (90-100%)": zone_range(0.90, 1.00),
        },
    }


def calculate_one_rep_max(weight_lbs: float, reps: int) -> Dict[str, Any]:
    """Calculate estimated 1-Rep Max (1RM) and percentage target weights using the Epley formula.

    Args:
        weight_lbs: Weight lifted in pounds.
        reps: Number of repetitions performed.

    Returns:
        A dictionary with estimated 1RM and target training weight loads.
    """
    if reps <= 1:
        one_rm = weight_lbs
    else:
        one_rm = round(weight_lbs * (1 + (reps / 30.0)), 1)

    return {
        "weight_lifted_lbs": weight_lbs,
        "reps_performed": reps,
        "estimated_1rm_lbs": one_rm,
        "training_targets_lbs": {
            "90% 1RM (Heavy Strength)": round(one_rm * 0.90, 1),
            "80% 1RM (Hypertrophy/Strength)": round(one_rm * 0.80, 1),
            "70% 1RM (Endurance/Volume)": round(one_rm * 0.70, 1),
        },
    }


def fetch_nutrition_info(query: str) -> Dict[str, Any]:
    """Fetch real-world nutrition facts (calories, protein, carbs, fat) for a food item or supplement using Open Food Facts public API.

    Args:
        query: The food or supplement to search for (e.g. 'whey protein', 'greek yogurt', 'chicken breast', 'banana').

    Returns:
        A dictionary with product nutrition information per 100g.
    """
    api_key = os.environ.get("NUTRITION_API_KEY", "")
    
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded_query}&search_simple=1&action=process&json=1&page_size=3"
    
    headers = {"User-Agent": "FitnessCoachAgent/1.0"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            products = data.get("products", [])

            if not products:
                return {"query": query, "message": f"No nutrition info found for '{query}'."}

            results = []
            for p in products[:3]:
                nutriments = p.get("nutriments", {})
                cals = nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal_value") or 0.0
                protein = nutriments.get("proteins_100g") or 0.0
                carbs = nutriments.get("carbohydrates_100g") or 0.0
                fat = nutriments.get("fat_100g") or 0.0

                results.append({
                    "product_name": p.get("product_name", query),
                    "brand": p.get("brands", "Generic"),
                    "calories_per_100g": round(float(cals), 1),
                    "protein_g_per_100g": round(float(protein), 1),
                    "carbs_g_per_100g": round(float(carbs), 1),
                    "fat_g_per_100g": round(float(fat), 1),
                })

            return {
                "query": query,
                "items": results,
            }
    except Exception as e:
        return {"query": query, "error": f"Failed to fetch nutrition data: {str(e)}"}


def geocode_address(address: str) -> Dict[str, Any]:
    """Convert a street address or city name into geographical latitude and longitude coordinates.

    Args:
        address: The address or place name to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'San Francisco, CA').

    Returns:
        A dictionary containing formatted address, latitude, and longitude.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    encoded_addr = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_addr}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "OK" and data.get("results"):
                first = data["results"][0]
                loc = first["geometry"]["location"]
                return {
                    "query": address,
                    "formatted_address": first.get("formatted_address"),
                    "location": {
                        "latitude": loc.get("lat"),
                        "longitude": loc.get("lng"),
                    },
                }
            return {"query": address, "error": f"Geocoding failed with status: {data.get('status')}"}
    except Exception as e:
        return {"query": address, "error": f"Geocoding request failed: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "gym",
    radius_meters: float = 3000.0,
) -> Dict[str, Any]:
    """Find nearby places of a specific type (e.g. 'gym', 'fitness_center', 'park') around coordinates using Google Places API (New).

    Args:
        latitude: Latitude coordinate of the search center.
        longitude: Longitude coordinate of the search center.
        place_type: The type of place to search for (e.g. 'gym', 'fitness_center', 'park').
        radius_meters: Search radius in meters (default: 3000 meters / ~1.8 miles).

    Returns:
        A dictionary containing a list of nearby places with name, address, and location coordinates.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    
    formatted_type = place_type.lower().strip().replace(" ", "_")
    
    body = json.dumps({
        "includedTypes": [formatted_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": float(radius_meters),
            }
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            places_raw = data.get("places", [])
            
            results = []
            for p in places_raw:
                results.append({
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress", "N/A"),
                    "location": {
                        "latitude": p.get("location", {}).get("latitude"),
                        "longitude": p.get("location", {}).get("longitude"),
                    },
                })
                
            return {
                "search_center": {"latitude": latitude, "longitude": longitude},
                "place_type": place_type,
                "places_found": results,
            }
    except Exception as e:
        return {"error": f"Places search failed: {str(e)}"}


def generate_fitness_image(
    prompt: str,
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Generate an exercise form illustration, workout graphic, or motivational visual using gemini-3.1-flash-lite-image model in global region.

    Args:
        prompt: Description of the fitness visual to generate (e.g. 'An illustration of proper dumbbell squat form in a modern gym').
        tool_context: ADK ToolContext injected automatically to save artifacts for the Playground.

    Returns:
        A dictionary containing the public Cloud Storage HTTPS image URL and filename.
    """
    genai_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )
    
    try:
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=f"Fitness artwork: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )
        
        image_bytes = None
        mime_type = "image/jpeg"
        
        for part in response.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break
                
        if not image_bytes:
            return {"error": "No image data was generated by the model."}

        object_name = f"fitness_visual_{uuid.uuid4().hex[:8]}.jpg"

        # 1. Save artifact to Playground via tool_context
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=object_name, artifact=artifact_part)

        # 2. Upload image bytes directly to public GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{object_name}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": object_name,
            "public_image_url": public_url,
        }
    except Exception as e:
        return {"error": f"Image generation or upload failed: {str(e)}"}


def generate_exercise_video(
    prompt: str,
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Generate a short exercise demonstration or workout video clip using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Args:
        prompt: Description of the exercise, movement, or workout clip to generate a video for.
        tool_context: ADK ToolContext injected automatically to save artifacts for the Playground.

    Returns:
        A dictionary containing the public Cloud Storage HTTPS video URL and filename.
    """
    genai_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    try:
        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=f"A short 5-second exercise video demonstrating: {prompt}. Professional fitness clip in a gym.",
        )

        video_bytes = None
        if hasattr(interaction, "output_video") and interaction.output_video:
            data = getattr(interaction.output_video, "data", None)
            if isinstance(data, str):
                video_bytes = base64.b64decode(data)
            elif isinstance(data, bytes):
                video_bytes = data

        if not video_bytes:
            return {"error": "No video data was generated by the model."}

        object_name = f"exercise_video_{uuid.uuid4().hex[:8]}.mp4"
        mime_type = "video/mp4"

        # 1. Save artifact to Playground via tool_context
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=object_name, artifact=artifact_part)

        # 2. Upload video bytes directly to public GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{object_name}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": object_name,
            "public_video_url": public_url,
        }
    except Exception as e:
        return {"error": f"Video generation or upload failed: {str(e)}"}

