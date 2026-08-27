import json
from pydantic import BaseModel, Field
from typing import List


class FixStep(BaseModel):
    explanation: str = Field(...,
                             description="An easy-to-understand educational explanation of why this step is needed, acting as a coach.")
    command: str = Field(...,
                         description="The exact CLI command for this step. Leave empty if it is just a physical action.")


class DiagnosticResult(BaseModel):
    is_network_issue: bool = Field(..., description="True if a technical network question. False if casual chat.")
    chat_reply: str = Field(..., description="If is_network_issue is False, put your conversational response here.")
    root_cause: str = Field(..., description="The primary technical fault. Leave empty if not a network issue.")
    osi_layer: str = Field(..., description="The OSI model layer. Leave empty if not a network issue.")
    confidence: str = Field(..., description="Confidence level. Leave empty if not a network issue.")
    evidence: str = Field(...,
                          description="Specific quotes from the show commands. Leave empty if not a network issue.")
    next_command: str = Field(...,
                              description="The exact Cisco IOS command to run next. Leave empty if not a network issue.")
    fix_steps: List[FixStep] = Field(...,
                                     description="List of sequential explanations and their corresponding commands.")


SYSTEM_PROMPT = """You are NetSage AI, a highly skilled but patient Tier-3 Cisco TAC expert. 
Your job is to mentor and guide junior network engineers.

ROUTING INSTRUCTIONS:
- If the user says hello, asks "how are you", or makes casual chat, set 'is_network_issue' to False. Keep the 'chat_reply' brief, conversational, and direct. DO NOT output long bulleted onboarding lists for simple greetings.
- If the user asks a general technical question (like explaining a command), set 'is_network_issue' to False. For this 'chat_reply', you MUST use clean Markdown (bullet points, **bold text**, `code blocks`). Never output a dense wall of text.
- If the user describes a broken network problem needing a fix, set 'is_network_issue' to True and fill out the diagnostic fields.

DIAGNOSTIC RULES:
1. STRICT KNOWLEDGE BASE ENFORCEMENT: You will be provided with a Reference Knowledge Base. You MUST extract the EXACT CLI commands provided in that reference data for the specific case. Do not invent generic commands if specific ones are provided in the dataset.
2. EDUCATIONAL TONE: When writing the 'explanation' for each FixStep, act as a coach. Briefly explain *why* the junior engineer is running the specific command you extracted.
3. SEQUENTIAL ORDER: The fix_steps must be in the exact order they need to be typed into the terminal.
"""


def generate_prompt(symptom: str, show_outputs: str, reference_data: str) -> str:
    return f"""
    Analyze this input against the provided Reference Knowledge Base.

    REFERENCE KNOWLEDGE BASE (Your primary source of truth):
    {reference_data}

    USER INPUT: 
    {symptom}

    SHOW COMMAND OUTPUTS:
    {show_outputs}
    """