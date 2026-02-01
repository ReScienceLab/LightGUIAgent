"""
LightGUIAgent - Lightweight GUI Automation Agent with Grid-Based Visual Grounding

A lightweight Python framework for automating GUI interactions using:
- Grid-based coordinate system (10×20, like chess notation)
- Claude Opus 4.5 vision model for decision-making
- ADB for Android device control

Example usage:
    from lightguiagent import LightGUIAgent

    agent = LightGUIAgent()
    result = agent.run_task("Open Meituan and search for coffee")
"""

__version__ = "0.1.0"
__author__ = "LightGUIAgent Contributors"
__license__ = "MIT"

# Core agent
from lightguiagent.agent import LightGUIAgent

# Grid system components
from lightguiagent.grid_overlay import GridOverlay
from lightguiagent.grid_converter import GridConverter

# Claude client
from lightguiagent.claude_client import ClaudeClient

# Logging
from lightguiagent.logger import TaskLogger

# Configuration
from lightguiagent.config import (
    CLAUDE_CONFIG,
    GRID_CONFIG,
    AGENT_CONFIG,
    ADB_CONFIG,
)

__all__ = [
    # Core
    "LightGUIAgent",
    # Grid system
    "GridOverlay",
    "GridConverter",
    # Clients
    "ClaudeClient",
    # Logging
    "TaskLogger",
    # Config
    "CLAUDE_CONFIG",
    "GRID_CONFIG",
    "AGENT_CONFIG",
    "ADB_CONFIG",
    # Metadata
    "__version__",
]
