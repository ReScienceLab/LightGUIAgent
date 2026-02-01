"""Task logging system (inspired by GELab-Zero design).

Records complete execution trace including:
- Actions at each step
- LLM reasoning process
- Screenshots
- Timestamps
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from PIL import Image


class TaskLogger:
    """Task execution logger."""

    def __init__(
        self, log_dir: Path, image_dir: Path, session_id: Optional[str] = None
    ):
        """Initialize task logger.

        Args:
            log_dir: Directory for log files (.jsonl files)
            image_dir: Directory for screenshots
            session_id: Session ID (auto-generated if None)
        """
        self.log_dir = Path(log_dir)
        self.image_dir = Path(image_dir)

        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)

        # Generate or use provided session_id
        self.session_id = session_id or str(uuid.uuid4())

        # Log file path
        self.log_file = self.log_dir / f"{self.session_id}.jsonl"

        print(f"📝 Logger initialized: {self.log_file}")

    def log_event(self, event_type: str, data: Dict[str, Any], is_print: bool = False):
        """Log an event to JSONL file.

        Args:
            event_type: Event type (e.g., "step_start", "action", "llm_response")
            data: Event data
            is_print: Whether to print to console
        """
        log_entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": event_type,
            "data": data,
        }

        # Write to JSONL file (one JSON object per line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        if is_print:
            print(json.dumps(log_entry, indent=2, ensure_ascii=False))

    def log_task_start(self, task: str, config: Dict[str, Any]):
        """记录任务开始"""
        self.log_event("task_start", {"task": task, "config": config})

    def log_step_start(self, step_num: int):
        """记录步骤开始"""
        self.log_event("step_start", {"step": step_num})

    def log_screenshot(self, step_num: int, screenshot_path: str):
        """记录截图信息"""
        self.log_event("screenshot", {"step": step_num, "path": screenshot_path})



    def log_llm_response(
        self,
        step_num: int,
        action: Dict[str, Any],
        inference_time: float,
        tokens: Dict[str, int],
    ):
        """记录LLM响应"""
        self.log_event(
            "llm_response",
            {
                "step": step_num,
                "action": action,
                "inference_time": inference_time,
                "tokens": tokens,
            },
        )

    def log_action_execution(
        self, step_num: int, action: Dict[str, Any], execution_time: float
    ):
        """记录动作执行"""
        self.log_event(
            "action_execution",
            {"step": step_num, "action": action, "execution_time": execution_time},
        )

    def log_step_complete(self, step_num: int, total_time: float):
        """记录步骤完成"""
        self.log_event("step_complete", {"step": step_num, "total_time": total_time})

    def log_task_complete(
        self, success: bool, total_steps: int, total_time: float, total_cost: float
    ):
        """记录任务完成"""
        self.log_event(
            "task_complete",
            {
                "success": success,
                "total_steps": total_steps,
                "total_time": total_time,
                "total_cost": total_cost,
            },
        )

    def log_error(self, step_num: int, error: str):
        """记录错误"""
        self.log_event("error", {"step": step_num, "error": str(error)})

    def save_image(
        self, image: Image.Image, step_num: int, image_type: str = "screenshot"
    ) -> str:
        """Save image to disk.

        Args:
            image: PIL Image object
            step_num: Step number
            image_type: Image type (screenshot, annotated, etc.)

        Returns:
            Path to saved image
        """
        # Compress as JPEG format
        image_rgb = image.convert("RGB")
        image_path = (
            self.image_dir / f"{self.session_id}_step{step_num:02d}_{image_type}.jpg"
        )

        image_rgb.save(image_path, format="JPEG", quality=85)

        return str(image_path)

    def read_logs(self) -> list:
        """Read log file.

        Returns:
            List of log entries
        """
        if not self.log_file.exists():
            return []

        logs = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))

        return logs

    def get_summary(self) -> Dict[str, Any]:
        """Get task summary.

        Returns:
            Task summary information
        """
        logs = self.read_logs()

        if not logs:
            return {"error": "No logs found"}

        # Extract key information
        task_start = next(
            (log for log in logs if log["event_type"] == "task_start"), None
        )
        task_complete = next(
            (log for log in logs if log["event_type"] == "task_complete"), None
        )

        step_completes = [log for log in logs if log["event_type"] == "step_complete"]
        llm_responses = [log for log in logs if log["event_type"] == "llm_response"]

        # Safely extract total tokens with fallback
        total_tokens = 0
        for log in llm_responses:
            if "tokens" in log["data"]:
                tokens_data = log["data"]["tokens"]
                if "total_tokens" in tokens_data:
                    total_tokens += tokens_data["total_tokens"]
                elif "input_tokens" in tokens_data and "output_tokens" in tokens_data:
                    # Calculate total from input + output if total_tokens is missing
                    total_tokens += (
                        tokens_data["input_tokens"] + tokens_data["output_tokens"]
                    )

        summary = {
            "session_id": self.session_id,
            "task": task_start["data"]["task"] if task_start else "Unknown",
            "total_steps": len(step_completes),
            "success": task_complete["data"]["success"] if task_complete else False,
            "total_time": task_complete["data"]["total_time"] if task_complete else 0,
            "total_cost": task_complete["data"]["total_cost"] if task_complete else 0,
            "avg_step_time": sum(log["data"]["total_time"] for log in step_completes)
            / len(step_completes)
            if step_completes
            else 0,
            "total_tokens": total_tokens,
        }

        return summary


# Convenience function
def create_logger(base_dir: Path = None) -> TaskLogger:
    """Create a new task logger.

    Args:
        base_dir: Base directory (defaults to debug/)

    Returns:
        TaskLogger instance
    """
    if base_dir is None:
        base_dir = Path("debug")

    log_dir = base_dir / "logs"
    image_dir = base_dir / "images"

    return TaskLogger(log_dir, image_dir)
