"""Grid-Claude-Agent main orchestrator.

Coordinates screenshot capture, grid overlay, Claude API calls, and action execution.
"""

import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from lightguiagent.config import AGENT_CONFIG, ADB_CONFIG, LOGS_DIR, GRID_CONFIG
from lightguiagent.grid_overlay import GridOverlay
from lightguiagent.grid_converter import GridConverter
from lightguiagent.claude_client import ClaudeClient
from lightguiagent.logger import TaskLogger


class LightGUIAgent:
    """Main agent that orchestrates the entire automation pipeline."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        device_serial: Optional[str] = None,
        verbose: bool = None,
    ):
        """Initialize agent with components.

        Args:
            api_key: Claude API key
            device_serial: ADB device serial (None = auto-detect)
            verbose: Print detailed logs
        """
        self.verbose = verbose if verbose is not None else AGENT_CONFIG["verbose"]

        # Initialize components
        self.claude = ClaudeClient(api_key=api_key)
        self.grid_overlay = GridOverlay()
        self.grid_converter = GridConverter()

        # ADB configuration
        self.device_serial = device_serial or ADB_CONFIG["device_serial"]
        self.screenshot_path = ADB_CONFIG["screenshot_path"]

        # Execution state
        self.history = []
        self.step_count = 0
        self.step_times = []  # Track timing for each step

        # Logger (initialized per task)
        self.logger = None

        # yadb availability flag
        self.yadb_available = False

        # Verify ADB connection
        self._verify_adb_connection()

        # Setup yadb for Chinese input
        self._setup_yadb()

    def _verify_adb_connection(self):
        """Verify ADB is installed and device is connected."""
        try:
            # Check ADB installed
            subprocess.run(
                ["adb", "version"], capture_output=True, check=True, timeout=5
            )

            # Check device connected
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )

            devices = [
                line.split()[0]
                for line in result.stdout.split("\n")[1:]
                if line.strip() and "device" in line
            ]

            if not devices:
                print("⚠️  Warning: No ADB devices connected")
                print("   Connect your device and enable USB debugging")
            elif self.verbose:
                print(f"✅ ADB connected: {devices[0]}")

        except FileNotFoundError:
            raise Exception("ADB not found. Please install Android SDK Platform Tools.")
        except subprocess.TimeoutExpired:
            raise Exception("ADB command timed out. Check ADB server.")

    def _adb_command(self, *args, timeout=10) -> subprocess.CompletedProcess:
        """Execute ADB command.

        Args:
            *args: ADB command arguments
            timeout: Command timeout in seconds

        Returns:
            subprocess.CompletedProcess result
        """
        cmd = ["adb"]
        if self.device_serial:
            cmd.extend(["-s", self.device_serial])
        cmd.extend(args)

        if self.verbose:
            print(f"  🔧 ADB: {' '.join(cmd)}")

        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def capture_screenshot(self) -> Path:
        """Capture screenshot from device.

        Returns:
            Path to local screenshot file
        """
        # Capture screenshot on device
        self._adb_command("shell", "screencap", "-p", self.screenshot_path)

        # Pull to local
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = ADB_CONFIG["local_screenshot_dir"] / f"screenshot_{timestamp}.png"

        self._adb_command("pull", self.screenshot_path, str(local_path))

        if not local_path.exists():
            raise Exception(f"Failed to pull screenshot to {local_path}")

        return local_path

    def _clear_text_field(self):
        """Clear current focused text field using Ctrl+A + Delete.

        This is useful when there's existing text in the input field.
        """
        try:
            # Ctrl+A (Select All): KEYCODE_CTRL_LEFT (113) + KEYCODE_A (29)
            print("  Clearing text field: Ctrl+A + Delete")

            # Method 1: Use keycombination (most reliable)
            self._adb_command(
                "shell", "input", "keycombination", "113", "29", timeout=2
            )

            # Small delay
            time.sleep(0.2)

            # Delete selected text: KEYCODE_DEL (67)
            self._adb_command("shell", "input", "keyevent", "67", timeout=2)

            time.sleep(0.2)

        except Exception as e:
            if self.verbose:
                print(f"  ⚠️  Clear text failed: {e}")

    def execute_action(self, action: dict, retry_on_failure: bool = True):
        """Execute an action on the device.

        Args:
            action: Action dict from Claude
            retry_on_failure: Whether to retry on failure
        """
        action_type = action["action"]

        max_retries = 2 if retry_on_failure else 1

        for attempt in range(max_retries):
            try:
                if action_type == "CLICK":
                    grid = action["grid"]
                    x, y = self.grid_converter.grid_to_pixel(grid)

                    print(
                        f"Executing command: adb -s {self.device_serial or 'default'} shell input tap {x} {y}"
                    )
                    self._adb_command("shell", "input", "tap", str(x), str(y))

                elif action_type == "TYPE":
                    value = action["value"]
                    clear_first = action.get("clear_first", False)

                    # Clear existing text if requested
                    if clear_first:
                        self._clear_text_field()

                    # Use yadb for better Chinese input support
                    if self.yadb_available:
                        # Preprocess text: replace newlines and tabs with spaces
                        processed_text = value.replace("\n", " ").replace("\t", " ")

                        cmd_parts = [
                            "shell",
                            "app_process",
                            "-Djava.class.path=/data/local/tmp/yadb",
                            "/data/local/tmp",
                            "com.ysbing.yadb.Main",
                            "-keyboard",
                            f'"{processed_text}"',
                        ]

                        print(
                            f"Executing command (yadb): adb shell app_process ... -keyboard '{value}'"
                        )
                        self._adb_command(*cmd_parts)
                    else:
                        # Fallback to basic input text (doesn't support Chinese well)
                        # Escape special characters and spaces
                        escaped_value = value.replace(" ", "%s").replace("'", "\\'")

                        print(f"Executing command: adb shell input text '{value}'")
                        self._adb_command("shell", "input", "text", escaped_value)

                elif action_type == "SCROLL":
                    direction = action["value"]  # "up" or "down"

                    # Calculate swipe coordinates (middle of screen horizontally)
                    screen_width = GRID_CONFIG["screen_width"]
                    screen_height = GRID_CONFIG["screen_height"]
                    x = screen_width // 2

                    if direction == "down":
                        # Swipe from top to bottom (scroll down)
                        y1 = int(screen_height * 0.7)  # Start at 70% down
                        y2 = int(screen_height * 0.3)  # End at 30% down
                    else:  # "up"
                        # Swipe from bottom to top (scroll up)
                        y1 = int(screen_height * 0.3)  # Start at 30% down
                        y2 = int(screen_height * 0.7)  # End at 70% down

                    duration = 300  # milliseconds

                    print(
                        f"Executing command: adb shell input swipe {x} {y1} {x} {y2} {duration}"
                    )
                    self._adb_command(
                        "shell",
                        "input",
                        "swipe",
                        str(x),
                        str(y1),
                        str(x),
                        str(y2),
                        str(duration),
                    )

                elif action_type == "AWAKE":
                    package = action["value"]

                    # First force stop the app
                    print(f"Executing command: adb shell am force-stop {package}")
                    self._adb_command("shell", "am", "force-stop", package)
                    time.sleep(0.5)

                    # Then launch it
                    print(
                        f"Executing command: adb shell monkey -p {package} -c android.intent.category.LAUNCHER 1"
                    )
                    self._adb_command(
                        "shell",
                        "monkey",
                        "-p",
                        package,
                        "-c",
                        "android.intent.category.LAUNCHER",
                        "1",
                    )

                elif action_type == "COMPLETE":
                    if self.verbose:
                        print("✅ Task marked as complete")

                else:
                    print(f"⚠️  Unknown action type: {action_type}")

                # Success - break retry loop
                break

            except Exception as e:
                if attempt < max_retries - 1:
                    print(
                        f"⚠️  Action failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(1)
                else:
                    print(f"❌ Action failed after {max_retries} attempts: {e}")
                    raise

    def _setup_yadb(self):
        """Setup yadb tool for Chinese input support."""
        try:
            # Check if yadb already exists on device
            result = self._adb_command(
                "shell", "md5sum", "/data/local/tmp/yadb", timeout=5
            )

            if result.returncode == 0:
                if self.verbose:
                    print("✅ yadb already installed on device")
                self.yadb_available = True
                return

            # Push yadb to device
            yadb_path = Path(__file__).parent / "yadb"
            if not yadb_path.exists():
                print("⚠️  yadb file not found, will use basic input method")
                self.yadb_available = False
                return

            if self.verbose:
                print("📦 Installing yadb to device...")

            result = self._adb_command(
                "push", str(yadb_path), "/data/local/tmp/", timeout=10
            )

            if result.returncode == 0:
                if self.verbose:
                    print("✅ yadb installed successfully")
                self.yadb_available = True
            else:
                print("⚠️  Failed to install yadb, will use basic input method")
                self.yadb_available = False

        except Exception as e:
            print(f"⚠️  yadb setup error: {e}, will use basic input method")
            self.yadb_available = False

    def run_task(
        self, task: str, max_steps: Optional[int] = None, save_screenshots: bool = None
    ) -> dict:
        """Run a complete task.

        Args:
            task: User's goal (e.g., "在美团点一杯瑞幸拿铁")
            max_steps: Maximum steps (defaults to config)
            save_screenshots: Save annotated screenshots (defaults to config)

        Returns:
            Result dict with success status, steps, and cost
        """
        max_steps = max_steps or AGENT_CONFIG["max_steps"]
        save_screenshots = (
            save_screenshots
            if save_screenshots is not None
            else AGENT_CONFIG["save_debug_images"]
        )

        # Initialize logger with proper directory structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = LOGS_DIR / f"task_{timestamp}"
        image_dir = log_dir / "images"

        self.logger = TaskLogger(log_dir=log_dir, image_dir=image_dir)

        print("=" * 60)
        print("🚀 Grid-Claude-Agent Starting")
        print("=" * 60)
        print(f"📋 Task: {task}")
        print(f"🎯 Max steps: {max_steps}")
        print(f"📁 Log: {self.logger.log_file}")
        print()

        # Clean up old temporary screenshots
        screenshot_dir = ADB_CONFIG["local_screenshot_dir"]
        if screenshot_dir.exists():
            for old_screenshot in screenshot_dir.glob("screenshot_*.png"):
                try:
                    old_screenshot.unlink()
                except Exception:
                    pass

        # Reset state
        self.history = []
        self.step_count = 0
        self.step_times = []
        start_time = time.time()

        # Log task start
        self.logger.log_task_start(task, {"max_steps": max_steps})

        try:
            for step in range(1, max_steps + 1):
                step_start = time.time()
                self.step_count = step

                # Log step start
                self.logger.log_step_start(step)

                # 1. Capture screenshot
                screenshot_path = self.capture_screenshot()

                # 2. Add grid overlay (don't save to DEBUG_DIR, only save via logger)
                annotated_image, grid_image_b64 = self.grid_overlay.process_screenshot(
                    screenshot_path, save_path=None
                )

                # Log screenshot path
                self.logger.log_screenshot(step, str(screenshot_path))

                # Save annotated image to logger's image directory (only location)
                if save_screenshots and annotated_image:
                    saved_path = self.logger.save_image(
                        annotated_image, step, "annotated"
                    )
                    if self.verbose:
                        print(f"  💾 Saved: {saved_path}")

                # Clean up temporary original screenshot (not needed after processing)
                try:
                    screenshot_path.unlink()
                except Exception:
                    pass  # Ignore cleanup errors

                # 3. Get action from Claude
                llm_start = time.time()
                action = self.claude.get_action(
                    task=task, grid_image_b64=grid_image_b64, history=self.history
                )
                llm_time = time.time() - llm_start

                print(f"LLM Claude Opus 4.5 inference time: {llm_time:.2f} seconds")

                # Log LLM response
                tokens = {
                    "input": self.claude.total_input_tokens,
                    "output": self.claude.total_output_tokens,
                }
                self.logger.log_llm_response(step, action, llm_time, tokens)

                # 4. Execute action
                try:
                    action_start = time.time()
                    self.execute_action(action)
                    action_time = time.time() - action_start

                    # Log successful action
                    self.logger.log_action_execution(step, action, action_time)

                    # Create and save marked image showing the action
                    marked_image_b64 = None
                    if save_screenshots and annotated_image and action["action"] in [
                        "CLICK",
                        "TYPE",
                        "AWAKE",
                    ]:
                        marked_image = self.grid_overlay.mark_action(
                            annotated_image, action
                        )
                        marked_path = self.logger.save_image(
                            marked_image, step, "action_marked"
                        )
                        if self.verbose:
                            print(f"  ✓ Action marked: {marked_path}")

                        # Compress and encode marked image for history
                        marked_image_b64 = self.grid_overlay.compress_and_encode(
                            marked_image
                        )

                except Exception as e:
                    # Log error
                    self.logger.log_error(step, str(e))
                    raise

                # 5. Calculate step time
                step_time = time.time() - step_start
                self.step_times.append(step_time)
                print(f"Step {step} took: {step_time:.2f} seconds")

                # Log step completion
                self.logger.log_step_complete(step, step_time)

                # 6. Print step summary
                self._print_step_summary(step, max_steps, action)

                # 7. Record in history with marked screenshot
                history_entry = action.copy()
                if marked_image_b64:
                    history_entry["marked_screenshot_b64"] = marked_image_b64

                self.history.append(history_entry)

                # 8. Check if complete
                if action["action"] == "COMPLETE":
                    print(f"\n{'═' * 60}")
                    print("✅ Task Completed Successfully!")
                    print(f"{'═' * 60}")
                    break

                # 9. Wait before next step
                delay = AGENT_CONFIG["delay_after_action"]
                time.sleep(delay)

            else:
                # Max steps reached
                print(f"\n{'═' * 60}")
                print("⚠️  Reached maximum steps without completion")
                print(f"{'═' * 60}")

        except KeyboardInterrupt:
            print("\n\n⚠️  Task interrupted by user")
            self.logger.log_event("task_interrupted", {"reason": "user_interrupt"})

        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback

            error_traceback = traceback.format_exc()
            print(error_traceback)

            # Log error
            self.logger.log_event(
                "task_error", {"error": str(e), "traceback": error_traceback}
            )

        finally:
            # Print summary
            elapsed_time = time.time() - start_time
            self._print_summary(elapsed_time)

            # Log task completion
            cost = self.claude.get_cost()
            success = len(self.history) > 0 and self.history[-1]["action"] == "COMPLETE"

            self.logger.log_task_complete(
                success=success,
                total_steps=self.step_count,
                total_time=elapsed_time,
                total_cost=cost,
            )

            # Print logger summary
            if self.verbose:
                summary = self.logger.get_summary()
                print("\n📊 Logger Summary:")
                print(f"   Session ID: {summary.get('session_id', 'N/A')}")
                print(f"   Total steps: {summary.get('total_steps', 0)}")
                print(f"   Log file: {self.logger.log_file}")

        # Return results
        return {
            "success": len(self.history) > 0
            and self.history[-1]["action"] == "COMPLETE",
            "steps": self.step_count,
            "elapsed_time": elapsed_time,
            "cost": self.claude.get_cost(),
            "history": self.history,
            "log_file": str(self.logger.log_file) if self.logger else None,
        }

    def _print_step_summary(self, step: int, max_steps: int, action: dict):
        """Print summary after each step (similar to GELab-Zero format)."""
        action_type = action["action"]
        explain = action.get("explain", "")

        # Format action details based on type
        if action_type == "CLICK":
            grid = action.get("grid", "")
            x, y = self.grid_converter.grid_to_pixel(grid)
            action_detail = f"CLICK {grid} → ({x}, {y})"
        elif action_type == "TYPE":
            value = action.get("value", "")
            action_detail = f'TYPE "{value}"'
        elif action_type == "SCROLL":
            direction = action.get("value", "")
            action_detail = f"SCROLL {direction}"
        elif action_type == "AWAKE":
            value = action.get("value", "")
            action_detail = f"AWAKE {value}"
        else:
            action_detail = action_type

        print(f"Step {step}/{max_steps} done. Action: {action_detail}")
        print(f"  ➤ {explain}")

        # Print summary if available
        if "summary" in action:
            print(f"  📝 Summary: {action['summary']}")

    def _print_summary(self, elapsed_time: float):
        """Print execution summary."""
        print("\n" + "=" * 60)
        print("📊 Execution Summary")
        print("=" * 60)
        print(f"Steps completed: {self.step_count}")
        print(f"Time elapsed:    {elapsed_time:.1f}s")

        if self.step_count > 0:
            avg_time = elapsed_time / self.step_count
            print(f"Avg per step:    {avg_time:.1f}s")

            # Show step time breakdown
            if self.step_times:
                min_time = min(self.step_times)
                max_time = max(self.step_times)
                print(f"Fastest step:    {min_time:.1f}s")
                print(f"Slowest step:    {max_time:.1f}s")

        print(f"Total execution time: {elapsed_time:.1f}s")

        # Print cost summary
        self.claude.print_cost_summary()


# Note: Main entry point is in main.py, not here.
# This agent.py module provides the LightGUIAgent class only.
