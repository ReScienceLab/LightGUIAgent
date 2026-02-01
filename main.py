#!/usr/bin/env python3
"""
LightGUIAgent - Main Entry Point

Usage:
    python main.py "Open Meituan app"
    python main.py "Search for Luckin Coffee"
"""

import sys
import os
from lightguiagent.agent import LightGUIAgent


def main():
    """Main entry point for LightGUIAgent."""

    # Check for task argument
    if len(sys.argv) < 2:
        print("❌ Error: No task provided!")
        print("\n📝 Usage:")
        print(f"   python {sys.argv[0]} 'your task description'")
        print("\n💡 Examples:")
        print('   python main.py "Open Meituan"')
        print('   python main.py "Search for Luckin Coffee and add to cart"')
        sys.exit(1)

    # Get task description
    task = " ".join(sys.argv[1:])

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print("\n📝 Please set your API key:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("\nOr create a .env file:")
        print("   cp .env.example .env")
        print("   # Edit .env and add your API key")
        sys.exit(1)

    # Print banner
    print("=" * 70)
    print("🚀 LightGUIAgent - Lightweight GUI Automation")
    print("=" * 70)
    print(f"📋 Task: {task}")
    print("🤖 Model: Claude Opus 4.5")
    print("🎯 Grid: 10×20 (A-J, 1-20)")
    print("=" * 70)
    print()

    # Run agent
    try:
        agent = LightGUIAgent(verbose=True)
        # Use 50 steps for complex tasks
        result = agent.run_task(task=task, max_steps=50, save_screenshots=True)

        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  User interrupted")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
