"""Simplified auto-detecting settings with configurable grid."""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import yaml
from pydantic import BaseModel, Field


class AgentSettings(BaseModel):
    """Agent behavior settings."""

    max_steps: int = Field(default=20, ge=1, le=100)
    delay_after_action: float = Field(default=2.0, ge=0.0, le=10.0)
    verbose: bool = True
    save_screenshots: bool = True


class GridStyle(BaseModel):
    """Grid configuration (all optional)."""

    cols: Optional[int] = Field(default=None, ge=5, le=30)  # Optional: user-specified columns
    rows: Optional[int] = Field(default=None, ge=10, le=50)  # Optional: user-specified rows
    line_color: Tuple[int, int, int] = (255, 0, 0)
    line_width: int = Field(default=3, ge=1, le=10)
    label_size: int = 32
    label_color: Tuple[int, int, int] = (255, 255, 0)
    label_bg_color: Tuple[int, int, int, int] = (0, 0, 0, 180)
    
    # Inner coordinate labels (optional)
    show_inner_labels: bool = True  # Show coordinate labels inside grid cells
    inner_label_interval: int = Field(default=3, ge=1, le=10)  # Show label every N cells
    inner_label_opacity: int = Field(default=128, ge=50, le=255)  # Opacity for inner labels (0-255)


class ClaudeSettings(BaseModel):
    """Claude API settings (optional)."""

    model: str = "claude-opus-4-5-20251101"
    max_tokens: int = 2048
    temperature: float = 0.1


class Settings:
    """Main settings with full auto-detection."""

    def __init__(self, config_path: Optional[Path] = None, skip_auto_detect: bool = False):
        """Initialize with auto-detection and optional overrides.
        
        Args:
            config_path: Path to config.yaml file
            skip_auto_detect: If True, skip ADB auto-detection (for tests/CI)
        """

        # Load user config (optional)
        user_config = self._load_yaml(config_path)

        # 🤖 Auto-detect device info (unless skipped)
        if skip_auto_detect:
            self.device_name = "Test Device"
            self.screen_width, self.screen_height = 1080, 2400
        else:
            self.device_name = self._auto_detect_device()
            self.screen_width, self.screen_height = self._auto_detect_screen()

        # User settings
        agent_data = user_config.get("agent", {})
        self.agent = AgentSettings(**agent_data)

        grid_data = user_config.get("grid", {})
        self.grid_style = GridStyle(**grid_data)

        claude_data = user_config.get("claude", {})
        self.claude = ClaudeSettings(**claude_data)

        # Grid density: use user value OR auto-calculate
        if self.grid_style.cols is not None and self.grid_style.rows is not None:
            # User specified
            self.grid_cols = self.grid_style.cols
            self.grid_rows = self.grid_style.rows
            self.grid_source = "custom"
        else:
            # Auto-calculate
            self.grid_cols, self.grid_rows = self._calculate_grid()
            self.grid_source = "auto"

        # Calculate derived values
        self.cell_width = self.screen_width / self.grid_cols
        self.cell_height = self.screen_height / self.grid_rows

        # API key from environment
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

        # Print summary if verbose
        if self.agent.verbose:
            self._print_banner()

    def _load_yaml(self, config_path: Optional[Path]) -> dict:
        """Load YAML config file if exists."""
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config.yaml"

        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f) or {}

        return {}

    def _auto_detect_device(self) -> str:
        """Auto-detect device name via ADB."""
        try:
            manufacturer = subprocess.run(
                ["adb", "shell", "getprop", "ro.product.manufacturer"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()

            model = subprocess.run(
                ["adb", "shell", "getprop", "ro.product.model"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()

            device_name = f"{manufacturer} {model}".strip()
            return device_name if device_name else "Unknown Device"

        except Exception:
            return "Unknown Device"

    def _auto_detect_screen(self) -> Tuple[int, int]:
        """Auto-detect screen size via ADB."""
        try:
            result = subprocess.run(
                ["adb", "shell", "wm", "size"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            match = re.search(r"(\d+)x(\d+)", result.stdout)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                return width, height
        except Exception:
            pass

        # Fallback
        if self.agent.verbose:
            print("⚠️  Could not detect screen, using 1080×2400")
        return 1080, 2400

    def _calculate_grid(self) -> Tuple[int, int]:
        """Calculate optimal grid density based on screen.

        Target: ~108×120 pixels per cell
        """
        cols = round(self.screen_width / 108)
        rows = round(self.screen_height / 120)

        # Clamp to reasonable range
        cols = max(8, min(cols, 20))
        rows = max(15, min(rows, 35))

        return cols, rows

    def _print_banner(self):
        """Print configuration banner."""
        print("=" * 70)
        print("🚀 LightGUIAgent - Lightweight GUI Automation")
        print("=" * 70)
        print(f"📱 Device: {self.device_name}")
        print(f"📐 Screen: {self.screen_width}×{self.screen_height}")
        print(
            f"🎯 Grid: {self.grid_cols}×{self.grid_rows} ({self.grid_source}) "
            + f"- cell: {self.cell_width:.0f}×{self.cell_height:.0f}px"
        )
        print(f"🤖 Max steps: {self.agent.max_steps}")
        print(f"⏱️  Delay: {self.agent.delay_after_action}s")
        print("=" * 70)
        print()


# Singleton
_settings: Optional[Settings] = None


def get_settings(
    config_path: Optional[Path] = None, reload: bool = False, skip_auto_detect: bool = False
) -> Settings:
    """Get or create settings instance.
    
    Args:
        config_path: Path to config.yaml file
        reload: Force reload of settings
        skip_auto_detect: Skip ADB auto-detection (for tests/CI)
    """
    global _settings

    if _settings is None or reload:
        _settings = Settings(config_path, skip_auto_detect=skip_auto_detect)

    return _settings
