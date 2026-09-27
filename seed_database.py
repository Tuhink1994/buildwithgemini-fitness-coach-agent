"""Seed script for fitness-coach-agent Firestore database."""
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-1e2398f3750c"
COLLECTION_NAME = "exercises"

SEED_EXERCISES = [
    {
        "id": "push_ups",
        "name": "Push-Ups",
        "category": "strength",
        "muscle_group": "chest",
        "difficulty": "beginner",
        "calories_per_minute": 7.0,
        "instructions": "Keep your body in a straight line from head to heels. Lower your chest to the floor and push back up.",
    },
    {
        "id": "barbell_squats",
        "name": "Barbell Squats",
        "category": "strength",
        "muscle_group": "legs",
        "difficulty": "intermediate",
        "calories_per_minute": 9.5,
        "instructions": "Place barbell across upper back. Hinge hips back, bend knees until thighs are parallel to ground, then drive back up.",
    },
    {
        "id": "plank",
        "name": "Forearm Plank",
        "category": "core",
        "muscle_group": "abs",
        "difficulty": "beginner",
        "calories_per_minute": 4.0,
        "instructions": "Rest on forearms and toes. Keep core engaged and spine neutral without letting hips sag.",
    },
    {
        "id": "dumbbell_bicep_curls",
        "name": "Dumbbell Bicep Curls",
        "category": "strength",
        "muscle_group": "biceps",
        "difficulty": "beginner",
        "calories_per_minute": 5.5,
        "instructions": "Hold dumbbells at sides with palms facing forward. Curl weights toward shoulders while keeping elbows pinned to sides.",
    },
    {
        "id": "hiit_sprints",
        "name": "High-Intensity Interval Sprints",
        "category": "cardio",
        "muscle_group": "full_body",
        "difficulty": "advanced",
        "calories_per_minute": 14.0,
        "instructions": "Alternate 30 seconds of maximum effort sprinting with 60 seconds of walking recovery.",
    },
]


def seed():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)
    print(f"Seeding '{COLLECTION_NAME}' collection in Firestore project '{PROJECT_ID}'...")
    for item in SEED_EXERCISES:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"  ✓ Added exercise: {item['name']} ({doc_id})")
    print("Database seeding complete!")


if __name__ == "__main__":
    seed()
