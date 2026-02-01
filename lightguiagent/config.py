"""Configuration for LightGUIAgent.

Backward compatibility wrapper around new settings system.
"""

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Lazy initialization to avoid ADB detection during import
_settings = None


def _get_settings():
    """Lazy load settings to avoid ADB auto-detection during import."""
    global _settings
    if _settings is None:
        from lightguiagent.settings import get_settings
        _settings = get_settings()
    return _settings

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DEBUG_DIR = ARTIFACTS_DIR / "debug"
LOGS_DIR = ARTIFACTS_DIR / "logs"

# Ensure directories exist
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Claude API Configuration (lazy-loaded)
# ============================================================================

def _get_claude_config():
    """Lazy load Claude config."""
    settings = _get_settings()
    return {
        "api_key": settings.api_key,
        "model": settings.claude.model,
        "max_tokens": settings.claude.max_tokens,
        "temperature": settings.claude.temperature,
    }

# Create property-like access
class _ConfigProxy:
    """Proxy for lazy config loading."""
    def __getitem__(self, key):
        return _get_claude_config()[key]
    
    def __contains__(self, key):
        return key in _get_claude_config()
    
    def get(self, key, default=None):
        return _get_claude_config().get(key, default)

CLAUDE_CONFIG = _ConfigProxy()

# Validate API key
if not CLAUDE_CONFIG["api_key"]:
    print("⚠️  Warning: ANTHROPIC_API_KEY not set. Please set it via:")
    print("   export ANTHROPIC_API_KEY='your-key-here'")

# ============================================================================
# Grid System Configuration (lazy-loaded)
# ============================================================================

def _get_grid_config():
    """Lazy load grid config."""
    settings = _get_settings()
    return {
        "screen_width": settings.screen_width,
        "screen_height": settings.screen_height,
        "grid_cols": settings.grid_cols,
        "grid_rows": settings.grid_rows,
        "cell_width": settings.cell_width,
        "cell_height": settings.cell_height,
        "line_color": settings.grid_style.line_color,
        "line_width": settings.grid_style.line_width,
        "label_size": settings.grid_style.label_size,
        "label_color": settings.grid_style.label_color,
        "label_bg_color": settings.grid_style.label_bg_color,
        "show_inner_labels": settings.grid_style.show_inner_labels,
        "inner_label_interval": settings.grid_style.inner_label_interval,
        "inner_label_opacity": settings.grid_style.inner_label_opacity,
        "target_size": 1568,  # Claude optimal image size
        "compression_quality": 85,  # JPEG quality
    }

class _GridConfigProxy(_ConfigProxy):
    """Proxy for lazy grid config loading."""
    def __getitem__(self, key):
        return _get_grid_config()[key]
    
    def __contains__(self, key):
        return key in _get_grid_config()
    
    def get(self, key, default=None):
        return _get_grid_config().get(key, default)

GRID_CONFIG = _GridConfigProxy()

# ============================================================================
# Agent Behavior Configuration (lazy-loaded)
# ============================================================================

def _get_agent_config():
    """Lazy load agent config."""
    settings = _get_settings()
    return {
        "max_steps": settings.agent.max_steps,
        "delay_after_action": settings.agent.delay_after_action,
        "save_debug_images": settings.agent.save_screenshots,
        "verbose": settings.agent.verbose,
    }

class _AgentConfigProxy(_ConfigProxy):
    """Proxy for lazy agent config loading."""
    def __getitem__(self, key):
        return _get_agent_config()[key]
    
    def __contains__(self, key):
        return key in _get_agent_config()
    
    def get(self, key, default=None):
        return _get_agent_config().get(key, default)

AGENT_CONFIG = _AgentConfigProxy()

# ============================================================================
# ADB Configuration
# ============================================================================

ADB_CONFIG = {
    "device_serial": None,  # None = use first connected device
    "screenshot_path": "/sdcard/screenshot.png",  # Temp path on device
    "local_screenshot_dir": DEBUG_DIR / "screenshots",
}

ADB_CONFIG["local_screenshot_dir"].mkdir(exist_ok=True)

# ============================================================================
# Action Definitions
# ============================================================================

ACTION_TYPES = [
    "CLICK",  # Click on grid cell
    "TYPE",  # Type text
    "SCROLL",  # Scroll screen (up/down)
    "AWAKE",  # Launch app by package name
    "COMPLETE",  # Task completed
]

# ============================================================================
# Cost Tracking
# ============================================================================

PRICING = {
    "input_per_million": 5.00,  # $5 per million input tokens
    "output_per_million": 25.00,  # $25 per million output tokens
}
