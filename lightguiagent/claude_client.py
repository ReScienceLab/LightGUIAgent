"""Claude API client for GUI automation.

Handles communication with Claude Opus 4.5 API for vision-based action decisions.
"""

import json
import time
from typing import Optional

from anthropic import Anthropic
from lightguiagent.config import CLAUDE_CONFIG, ACTION_TYPES, PRICING


class ClaudeClient:
    """Client for Claude API with structured output for GUI automation."""

    SYSTEM_PROMPT = """You are an Android GUI automation expert using a grid-based coordinate system.

**Grid System:**
- Screen divided into 10×20 grid
- Columns: A-J (left to right)  
- Rows: 1-20 (top to bottom)
- Each cell labeled on the screenshot (e.g., "E5", "A1", "J20")

**Your Task:**
Analyze the screenshot and decide the next action to accomplish the user's goal.

**Available Actions:**

1. **CLICK** - Click on a grid position
   
   Examples (Chinese task):
   ```json
   {
     "action": "CLICK",
     "grid": "E5",
     "explain": "点击搜索框以输入关键词",
     "summary": "任务目标是在美团点咖啡。当前在主页，下一步是搜索。"
   }
   ```
   
   Examples (English task):
   ```json
   {
     "action": "CLICK",
     "grid": "E5",
     "explain": "Click the search box to enter keywords",
     "summary": "Goal is to order coffee on Meituan. Currently on home page, next step is to search."
   }
   ```

2. **TYPE** - Type text into current input field
   
   Examples (Chinese task):
   ```json
   {
     "action": "TYPE", 
     "value": "瑞幸咖啡",
     "explain": "在搜索框中输入'瑞幸咖啡'来查找店铺",
     "summary": "已打开美团并激活搜索框，正在输入搜索关键词。"
   }
   ```
   
   Examples (English task):
   ```json
   {
     "action": "TYPE",
     "value": "Luckin Coffee",
     "explain": "Type 'Luckin Coffee' in search box to find the store",
     "summary": "Opened Meituan and activated search box, entering search keywords."
   }
   ```
   
   **Optional parameter**:
   - `"clear_first": true` → Clear existing text before typing (uses Ctrl+A + Delete)
   - Use this when the input field already contains text that needs to be replaced
   
   Example with clear:
   ```json
   {
     "action": "TYPE",
     "value": "瑞幸咖啡", 
     "clear_first": true,
     "explain": "清空搜索框并输入新关键词"
   }
   ```

3. **SCROLL** - Scroll screen up or down
   ```json
   {
     "action": "SCROLL",
     "value": "down",
     "explain": "向下滚动查找生椰拿铁",
     "summary": "已进入菜单页面，正在滚动寻找目标商品。"
   }
   ```
   Note: value must be "up" or "down"

4. **AWAKE** - Launch app by package name
   ```json
   {
     "action": "AWAKE",
     "value": "com.sankuai.meituan",
     "explain": "启动美团应用开始任务",
     "summary": "任务目标是在美团点咖啡。第一步：启动美团应用。"
   }
   ```

5. **COMPLETE** - Task successfully finished
   ```json
   {
     "action": "COMPLETE",
     "explain": "已成功完成订单并选择支付方式",
     "summary": "任务完成：已在美团下单咖啡并选择微信支付。"
   }
   ```

**Output Format Requirements:**

You MUST include these fields in your JSON response:

- **action**: Action type (CLICK/TYPE/SCROLL/AWAKE/COMPLETE)
- **explain**: Concise explanation of why this action (1 sentence, use the same language as user's task)
- **summary**: One-sentence progress summary of overall task (use the same language as user's task)
- **grid**: Required for CLICK (e.g., "E5")
- **value**: Required for TYPE, SCROLL, and AWAKE (text, "up"/"down", or package name)

**Language Matching Rule:**
IMPORTANT: Your "explain" and "summary" fields MUST match the language of the user's task:
- If user's task is in Chinese (e.g., "在美团点咖啡"), respond in Chinese
- If user's task is in English (e.g., "Order coffee on Meituan"), respond in English
- If user's task is in another language, respond in that language

**Important Guidelines:**

1. **Observe carefully**: Study the current UI state before deciding
2. **Grid precision**: Use the labeled grid coordinates visible on the screenshot
3. **Context awareness**: Remember the overall goal and what's been done
4. **Visual context**: If you see a previous step's screenshot (with action markers), use it to:
   - Verify the previous action was executed correctly
   - Understand the UI transition (before → after)
   - Detect if you're stuck or making progress
   - Identify what changed after the action
5. **Progress tracking**: Update the summary field to show task progress
6. **JSON only**: Output ONLY valid JSON, no markdown code blocks
7. **Language consistency**: Explain each action's purpose clearly in the user's language

**Navigation & Recovery:**

7. **Back button**: If you're on wrong page, look for back button (usually top-left, like ← or 返回)
8. **Stuck detection**: If you see the same page multiple times, try:
   - Click back button (top-left corner, often in grid A1-B3)
   - Click home button
   - Search again from main page
9. **Common back button locations**: Grid positions A1, A2, A3, B2 (top-left corner)
10. **Don't repeat failed actions**: If previous action didn't work, try different approach

**Common Package Names:**
- 美团: com.sankuai.meituan
- 淘宝: com.taobao.taobao
- 微信: com.tencent.mm
- 支付宝: com.eg.android.AlipayGphone
"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize Claude client.

        Args:
            api_key: Claude API key, defaults to config
            model: Model name, defaults to config
        """
        self.api_key = api_key or CLAUDE_CONFIG["api_key"]
        self.model = model or CLAUDE_CONFIG["model"]

        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.max_tokens = CLAUDE_CONFIG["max_tokens"]
        self.temperature = CLAUDE_CONFIG["temperature"]

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def get_action(
        self,
        task: str,
        grid_image_b64: str,
        history: Optional[list] = None,
        max_retries: int = 3,
    ) -> dict:
        """Get next action from Claude based on current screenshot.

        Args:
            task: User's goal (e.g., "在美团点一杯瑞幸拿铁")
            grid_image_b64: Base64-encoded screenshot with grid overlay
            history: List of previous actions (for context)
            max_retries: Max retry attempts on API errors

        Returns:
            Action dict like {"action":"CLICK","grid":"E5","explain":"..."}

        Raises:
            ValueError: If API returns invalid JSON
            Exception: If API call fails after retries
        """
        # Build message with context
        user_message = self._build_user_message(task, history)

        # Prepare content array
        content = []

        # Include previous step's marked screenshot if available
        if history and len(history) > 0:
            last_action = history[-1]
            if "marked_screenshot_b64" in last_action:
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": last_action["marked_screenshot_b64"],
                        },
                    }
                )
                content.append(
                    {
                        "type": "text",
                        "text": "**Previous step screenshot** (showing the action that was just executed):\n\n",
                    }
                )

        # Add current screenshot
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": grid_image_b64,
                },
            }
        )

        # Add user message
        content.append(
            {
                "type": "text",
                "text": user_message,
            }
        )

        # Prepare API request
        messages = [
            {
                "role": "user",
                "content": content,
            }
        ]

        # Call API with retries
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=self.SYSTEM_PROMPT,
                    messages=messages,
                )

                # Track usage
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

                # Parse response
                action = self._parse_response(response)
                return action

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  API error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(1)
                else:
                    raise Exception(
                        f"API call failed after {max_retries} attempts: {e}"
                    )

    def _build_user_message(self, task: str, history: Optional[list] = None) -> str:
        """Build user message with task and history context."""
        message = f"**User Goal:** {task}\n\n"

        if history and len(history) > 0:
            message += "**Previous Actions:**\n"
            for i, action in enumerate(history[-5:], 1):  # Show last 5 actions
                action_type = action.get("action", "UNKNOWN")
                explain = action.get("explain", "")

                if action_type == "CLICK":
                    grid = action.get("grid", "")
                    message += f"{i}. CLICK {grid} - {explain}\n"
                elif action_type == "TYPE":
                    value = action.get("value", "")
                    message += f'{i}. TYPE "{value}" - {explain}\n'
                elif action_type == "SCROLL":
                    value = action.get("value", "")
                    message += f"{i}. SCROLL {value} - {explain}\n"
                elif action_type == "AWAKE":
                    value = action.get("value", "")
                    message += f"{i}. AWAKE {value} - {explain}\n"
                else:
                    message += f"{i}. {action_type} - {explain}\n"

            message += "\n"

            # Add stuck detection warning
            if len(history) >= 2:
                # Check for repeated clicks on same grid position
                recent_actions = history[-2:]
                if all(a.get("action") == "CLICK" for a in recent_actions):
                    recent_grids = [a.get("grid", "") for a in recent_actions]
                    if len(set(recent_grids)) == 1 and recent_grids[0]:
                        message += f"⚠️ **Warning**: Last 2 CLICK actions targeted the same grid position '{recent_grids[0]}'!\n"
                        message += "The UI likely changed after the first click. Analyze the current screenshot carefully.\n"
                        message += "Do NOT repeat the same click unless you're certain it's needed.\n\n"
                
                # Check for repeated explains (original logic, but with 2 instead of 3)
                if len(history) >= 3:
                    recent_explains = [h.get("explain", "") for h in history[-3:]]
                    if len(set(recent_explains)) == 1:
                        message += "⚠️ **Warning**: Last 3 actions had same explanation. You might be stuck!\n"
                        message += "Consider: Click back button (top-left, grid A1-B3) or try different approach.\n\n"

        message += "**What is the next action?** (Output JSON only)"
        return message

    def _parse_response(self, response) -> dict:
        """Parse Claude's response into action dict."""
        # Extract text content
        text_content = None
        for block in response.content:
            if block.type == "text":
                text_content = block.text
                break

        if not text_content:
            raise ValueError("No text content in response")

        # Remove markdown code blocks if present
        text_content = text_content.strip()
        if text_content.startswith("```"):
            # Remove ```json and ``` markers
            lines = text_content.split("\n")
            text_content = "\n".join(lines[1:-1])

        # Parse JSON
        try:
            action = json.loads(text_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {text_content}\nError: {e}")

        # Validate action structure
        if "action" not in action:
            raise ValueError(f"Missing 'action' field in response: {action}")

        action_type = action["action"]
        if action_type not in ACTION_TYPES:
            raise ValueError(
                f"Invalid action type '{action_type}'. Must be one of: {ACTION_TYPES}"
            )

        # Validate required fields based on action type
        if action_type == "CLICK":
            if "grid" not in action:
                raise ValueError(f"CLICK action requires 'grid' field: {action}")
        elif action_type in ["TYPE", "SCROLL", "AWAKE"]:
            if "value" not in action:
                raise ValueError(
                    f"{action_type} action requires 'value' field: {action}"
                )
            # Validate SCROLL direction
            if action_type == "SCROLL" and action["value"] not in ["up", "down"]:
                raise ValueError(
                    f"SCROLL value must be 'up' or 'down', got: {action['value']}"
                )

        return action

    def get_cost(self) -> dict:
        """Calculate current session costs.

        Returns:
            Dict with token counts and costs in USD
        """
        input_cost = (self.total_input_tokens / 1_000_000) * PRICING[
            "input_per_million"
        ]
        output_cost = (self.total_output_tokens / 1_000_000) * PRICING[
            "output_per_million"
        ]
        total_cost = input_cost + output_cost

        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": total_cost,
        }

    def print_cost_summary(self):
        """Print cost summary to console."""
        cost = self.get_cost()
        print("\n" + "=" * 50)
        print("💰 Cost Summary")
        print("=" * 50)
        print(f"Input tokens:  {cost['input_tokens']:,}")
        print(f"Output tokens: {cost['output_tokens']:,}")
        print(f"Total tokens:  {cost['total_tokens']:,}")
        print("-" * 50)
        print(f"Input cost:    ${cost['input_cost_usd']:.4f}")
        print(f"Output cost:   ${cost['output_cost_usd']:.4f}")
        print(f"Total cost:    ${cost['total_cost_usd']:.4f}")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    print("=== Claude Client Test ===\n")
    print("This is a placeholder test.")
    print("Real testing requires:")
    print("  1. CLAUDE_API_KEY environment variable")
    print("  2. A screenshot with grid overlay")
    print("\nSee agent.py for full integration testing.")
