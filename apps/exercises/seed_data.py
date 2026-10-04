"""Seed data for grounding and breathing exercises (also loaded automatically by a migration)."""

GROUNDING_EXERCISES = [
    {
        "slug": "five-four-three-two-one",
        "title": "5-4-3-2-1 Grounding",
        "category": "grounding",
        "description": "Use your five senses to come back to the present moment.",
        "duration_minutes": 4,
        "steps": [
            {"title": "5 things you can SEE", "prompt": "Look around slowly and name five things you can see. Notice colours, shapes and light."},
            {"title": "4 things you can TOUCH", "prompt": "Notice four things you can feel: your clothes, the chair beneath you, the temperature of the air."},
            {"title": "3 things you can HEAR", "prompt": "Listen carefully. Name three sounds, near or far."},
            {"title": "2 things you can SMELL", "prompt": "Notice two scents around you, or recall two smells you enjoy."},
            {"title": "1 thing you can TASTE", "prompt": "Notice one taste in your mouth, or take a sip of water and notice how it tastes."},
        ],
    },
    {
        "slug": "body-scan-reset",
        "title": "Quick Body Scan",
        "category": "grounding",
        "description": "A short scan from head to toe to notice tension and let it soften.",
        "duration_minutes": 3,
        "steps": [
            {"title": "Settle", "prompt": "Sit or stand comfortably. Take one slow breath in and out."},
            {"title": "Head and shoulders", "prompt": "Notice your jaw, forehead and shoulders. If you can, let them drop a little."},
            {"title": "Arms and hands", "prompt": "Notice your arms and hands. Unclench your fists and let your fingers rest."},
            {"title": "Chest and belly", "prompt": "Notice your breathing without changing it. Feel your chest and belly move."},
            {"title": "Legs and feet", "prompt": "Press your feet gently into the floor. Notice the support beneath you."},
        ],
    },
    {
        "slug": "name-categories",
        "title": "Categories Game",
        "category": "grounding",
        "description": "A mental game that gently occupies your thinking mind.",
        "duration_minutes": 3,
        "steps": [
            {"title": "Pick a category", "prompt": "Choose a category, such as animals, countries or foods."},
            {"title": "Go through the alphabet", "prompt": "Name one item for as many letters as you can, from A onwards."},
            {"title": "Try another", "prompt": "Choose a second category and repeat, at your own pace."},
            {"title": "Check in", "prompt": "Pause and notice how you feel now compared to when you began."},
        ],
    },
]
