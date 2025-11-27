"""
Quiz configuration with smart evaluation questions.
"""

from typing import Dict, Any, List

QUIZ: List[Dict[str, Any]] = [
    {
        "id": "motivation",
        "type": "text",
        "q": "Write 3–4 sentences explaining why you want to work with us."
    },
    {
        "id": "conflict_resolution",
        "type": "text",
        "q": "Imagine you receive two conflicting instructions from two different team members. Describe step-by-step how you would resolve the conflict."
    },
    {
        "id": "logic_sequence",
        "type": "choice",
        "q": "What is the next number in the sequence: 2, 6, 12, 20, ?",
        "options": ["30", "24", "28", "32"]
    },
    {
        "id": "workflow_analysis",
        "type": "multi_choice",
        "q": "You are given a dataset with thousands of entries to improve a workflow. Which approaches would you consider first?",
        "options": [
            "Identify repeating patterns or bottlenecks",
            "Visualize the data to spot anomalies",
            "Automate repetitive actions",
            "Reduce dataset size randomly",
            "Build assumptions without checking the data"
        ]
    },
    {
        "id": "deadline_reaction",
        "type": "choice",
        "q": "You are under a tight deadline and a task takes much longer than expected. How do you react?",
        "options": [
            "Break the task into smaller measurable parts and reprioritize",
            "Inform the team early and propose alternatives",
            "Continue silently and deliver late",
            "Abandon the task and start a different one"
        ]
    },
]
