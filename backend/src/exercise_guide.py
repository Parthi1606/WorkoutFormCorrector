"""
Exercise Form Guide
Provides instructions and visual guides for each exercise
"""

EXERCISE_GUIDES = {
    "bicep_curl": {
        "name": "Bicep Curl",
        "instructions": [
            "Stand with feet shoulder-width apart",
            "Keep elbows tucked at your sides",
            "Curl weights up towards shoulders",
            "Lower slowly with control",
            "Keep wrists straight throughout"
        ],
        "common_mistakes": [
            "Swinging the weights",
            "Moving shoulders",
            "Elbows drifting forward",
            "Incomplete range of motion"
        ],
        "target_muscles": ["Biceps Brachii", "Brachialis", "Brachioradialis"]
    },
    "squat": {
        "name": "Squat",
        "instructions": [
            "Stand with feet shoulder-width apart",
            "Keep chest up and back straight",
            "Sit back as if into a chair",
            "Go down until thighs are parallel to ground",
            "Drive through heels to stand up"
        ],
        "common_mistakes": [
            "Knees caving inward",
            "Rounded back",
            "Heels lifting off ground",
            "Not going deep enough"
        ],
        "target_muscles": ["Quadriceps", "Glutes", "Hamstrings", "Core"]
    },
    "plank": {
        "name": "Plank",
        "instructions": [
            "Lie face down, prop up on forearms",
            "Lift body forming a straight line",
            "Tighten core and glutes",
            "Keep neck neutral, look at floor",
            "Hold position without sagging"
        ],
        "common_mistakes": [
            "Hips sagging down",
            "Hips too high (piking)",
            "Head looking up",
            "Holding breath"
        ],
        "target_muscles": ["Core", "Shoulders", "Glutes", "Back"]
    },
    "lunge": {
        "name": "Lunge",
        "instructions": [
            "Stand tall with feet together",
            "Step forward with one leg",
            "Lower hips until both knees are at 90°",
            "Front knee aligned with ankle",
            "Push back to starting position"
        ],
        "common_mistakes": [
            "Front knee past toes",
            "Leaning forward too much",
            "Back knee bent",
            "Losing balance"
        ],
        "target_muscles": ["Quadriceps", "Glutes", "Hamstrings", "Calves"]
    },
    "pushup": {
        "name": "Push-up",
        "instructions": [
            "Start in high plank position",
            "Hands shoulder-width apart",
            "Lower body until chest nearly touches floor",
            "Keep elbows at 45° angle",
            "Push back up explosively"
        ],
        "common_mistakes": [
            "Elbows flaring out",
            "Hips sagging",
            "Incomplete range of motion",
            "Head position wrong"
        ],
        "target_muscles": ["Chest", "Triceps", "Shoulders", "Core"]
    },
    "shoulder_press": {
        "name": "Shoulder Press",
        "instructions": [
            "Hold weights at shoulder height",
            "Keep core tight, back straight",
            "Press weights overhead",
            "Extend arms fully at top",
            "Lower with control"
        ],
        "common_mistakes": [
            "Arching back",
            "Elbows flaring out",
            "Using momentum",
            "Partial range of motion"
        ],
        "target_muscles": ["Deltoids", "Triceps", "Trapezius"]
    }
}

def get_guide(exercise_name):
    """Get form guide for exercise"""
    return EXERCISE_GUIDES.get(exercise_name, None)

def print_guide(exercise_name):
    """Print form guide to console"""
    guide = get_guide(exercise_name)
    if not guide:
        print(f"No guide available for {exercise_name}")
        return
    
    print(f"\n{'='*50}")
    print(f"FORM GUIDE: {guide['name']}")
    print(f"{'='*50}")
    print("\nINSTRUCTIONS:")
    for i, inst in enumerate(guide['instructions'], 1):
        print(f"  {i}. {inst}")
    
    print("\nCOMMON MISTAKES TO AVOID:")
    for mistake in guide['common_mistakes']:
        print(f"  • {mistake}")
    
    print("\nTARGET MUSCLES:")
    print(f"  {', '.join(guide['target_muscles'])}")
    print(f"{'='*50}\n")