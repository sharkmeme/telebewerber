"""
Question configuration for all job positions.
"""

from typing import Dict, Any, List

# Question config for all job positions
# Each position has:
# - name: display name
# - requires_portfolio: True/False
# - questions: list of {id, type, q, options?}

POSITIONS: Dict[str, Dict[str, Any]] = {

    "ai_video_creator": {
        "name": "AI Video Creator",
        "requires_portfolio": True,
        "questions": [
            {"id": "tools", "type": "multi_choice", "q": "Which AI video tools do you use?", "options": ["Sora", "Veo", "Pika", "Runway", "Kling", "Other"]},
            {"id": "experience", "type": "text", "q": "Describe your experience with AI video creation."},
            {"id": "workflow", "type": "text", "q": "Explain your typical video creation workflow."},
        ],
    },

    "ai_prompt_engineer": {
        "name": "AI Prompt Engineer",
        "requires_portfolio": False,
        "questions": [
            {"id": "llm_exp", "type": "text", "q": "What LLMs have you worked with (OpenAI, Claude, Gemini, etc.)?"},
            {"id": "prompt_samples", "type": "text", "q": "Share examples of prompts you have crafted."},
            {"id": "specialization", "type": "choice", "q": "What is your specialization?", "options": ["Video", "Image", "Automation", "Chatbots", "Coding", "Other"]},
        ],
    },

    "hr_manager": {
        "name": "HR Manager",
        "requires_portfolio": False,
        "questions": [
            {"id": "experience", "type": "text", "q": "Summarize your HR experience."},
            {"id": "tools", "type": "multi_choice", "q": "Which tools have you used?", "options": ["BambooHR", "Workable", "Notion", "Google Workspace", "Other"]},
            {"id": "policy", "type": "text", "q": "Describe a policy or workflow you implemented successfully."},
        ],
    },

    "social_media_manager": {
        "name": "Social Media Manager",
        "requires_portfolio": True,
        "questions": [
            {"id": "platforms", "type": "multi_choice", "q": "Which platforms do you manage?", "options": ["TikTok", "Instagram", "YouTube", "Facebook", "Twitter/X"]},
            {"id": "content_exp", "type": "text", "q": "Describe your experience with content creation."},
            {"id": "growth", "type": "text", "q": "Share an example of an account you've grown."},
        ],
    },

    "automation_specialist": {
        "name": "Automation Specialist (N8N)",
        "requires_portfolio": True,
        "questions": [
            {"id": "n8n_exp", "type": "text", "q": "Describe your experience with N8N."},
            {"id": "other_tools", "type": "multi_choice", "q": "Which automation tools do you know?", "options": ["Make.com", "Zapier", "Airflow", "Python", "Other"]},
            {"id": "complex_flow", "type": "text", "q": "Describe the most complex automation flow you built."},
        ],
    },

    "website_builder": {
        "name": "Website Builder (Webflow / Next.js)",
        "requires_portfolio": True,
        "questions": [
            {"id": "stack", "type": "multi_choice", "q": "Which stack do you use?", "options": ["Webflow", "Next.js", "React", "Tailwind", "Other"]},
            {"id": "projects", "type": "text", "q": "Describe websites or landing pages you've built."},
            {"id": "performance", "type": "text", "q": "What steps do you take to optimize page performance?"},
        ],
    },

    "sales_outreach": {
        "name": "Sales / Outreach Assistant",
        "requires_portfolio": False,
        "questions": [
            {"id": "experience", "type": "text", "q": "Describe your sales or outreach experience."},
            {"id": "tools", "type": "multi_choice", "q": "Which CRM/tools have you used?", "options": ["HubSpot", "Salesforce", "Notion", "Google Sheets", "Other"]},
            {"id": "closing", "type": "text", "q": "Describe your biggest success in outreach or sales."},
        ],
    },

    "ai_video_editor": {
        "name": "AI Video Editor",
        "requires_portfolio": True,
        "questions": [
            {"id": "tools", "type": "multi_choice", "q": "Which editing tools do you use?", "options": ["Premiere Pro", "DaVinci Resolve", "CapCut", "Final Cut", "Other"]},
            {"id": "experience", "type": "text", "q": "Describe your editing experience."},
            {"id": "showreel", "type": "text", "q": "Describe your best video or editing project."},
        ],
    },

    "developer": {
        "name": "Developer",
        "requires_portfolio": True,
        "questions": [
            {"id": "stack", "type": "multi_choice", "q": "Which languages/frameworks do you know?", "options": ["Python", "JavaScript", "TypeScript", "Node.js", "React", "SQL", "Other"]},
            {"id": "projects", "type": "text", "q": "Describe your most impressive coding projects."},
            {"id": "experience", "type": "text", "q": "How many years of coding experience do you have?"},
        ],
    },

    "other": {
        "name": "Other",
        "requires_portfolio": False,
        "questions": [],
    },
}
