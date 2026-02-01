#!/usr/bin/env python3
"""Test script for grid system without requiring Claude API or ADB.

Tests:
1. Grid converter (grid ↔ pixel)
2. Grid overlay visualization
3. Basic component integration
"""

from pathlib import Path
from PIL import Image

from lightguiagent.grid_converter import GridConverter
from lightguiagent.grid_overlay import GridOverlay

# Use local debug dir to avoid config imports
DEBUG_DIR = Path(__file__).parent.parent / "artifacts" / "debug"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def test_grid_converter():
    """Test grid coordinate conversion with explicit config."""
    # Use explicit config to avoid config.yaml interference
    test_config = {
        "screen_width": 1080,
        "screen_height": 2400,
        "grid_cols": 10,
        "grid_rows": 20,
        "cell_width": 108,  # 1080 / 10
        "cell_height": 120,  # 2400 / 20
    }
    converter = GridConverter(config=test_config)

    # Test cases for 10×20 grid
    test_cases = [
        ("A1", (54, 60)),    # (0.5*108, 0.5*120)
        ("E5", (486, 540)),  # (4.5*108, 4.5*120)
        ("J20", (1026, 2340)),  # (9.5*108, 19.5*120)
        ("F10", (594, 1140)),  # (5.5*108, 9.5*120)
    ]

    # Grid → Pixel
    for grid, expected_pixel in test_cases:
        result = converter.grid_to_pixel(grid)
        assert result == expected_pixel, f"Grid {grid} → {result}, expected {expected_pixel}"

    # Pixel → Grid
    for grid, pixel in test_cases:
        result = converter.pixel_to_grid(*pixel)
        assert result == grid, f"Pixel {pixel} → {result}, expected {grid}"


def test_grid_overlay():
    """Test grid overlay on blank and sample images with explicit config."""
    # Use explicit config to avoid config.yaml interference
    test_config = {
        "screen_width": 1080,
        "screen_height": 2400,
        "grid_cols": 10,
        "grid_rows": 20,
        "cell_width": 108,
        "cell_height": 120,
        "line_color": (255, 0, 0),
        "line_width": 3,
        "label_size": 32,
        "label_color": (255, 255, 0),
        "label_bg_color": (0, 0, 0, 180),
        "target_size": 1568,
        "compression_quality": 85,
    }
    overlay = GridOverlay(config=test_config)

    # Test 1: Blank canvas
    blank_image = Image.new("RGB", (1080, 2400), color=(240, 240, 240))
    annotated = overlay.apply(blank_image)
    
    assert annotated is not None, "Annotated image should not be None"
    assert annotated.size == (1080, 2400), f"Expected size (1080, 2400), got {annotated.size}"

    output_path = DEBUG_DIR / "test_grid_blank.png"
    annotated.save(output_path)
    assert output_path.exists(), f"Output file not created: {output_path}"

    # Test 2: Compress and encode
    b64_string = overlay.compress_and_encode(annotated)
    assert len(b64_string) > 0, "Base64 string should not be empty"
    assert isinstance(b64_string, str), "Base64 should be a string"

    # Test 3: Full pipeline with mock screenshot
    mock_screenshot = create_mock_screenshot()
    mock_path = DEBUG_DIR / "mock_screenshot.png"
    mock_screenshot.save(mock_path)

    annotated, b64 = overlay.process_screenshot(
        mock_path, DEBUG_DIR / "test_grid_mock.png"
    )
    assert annotated.size == (1080, 2400), f"Expected size (1080, 2400), got {annotated.size}"
    assert len(b64) > 0, "Base64 should not be empty"
    assert (DEBUG_DIR / "test_grid_mock.png").exists(), "Mock grid file not created"


def create_mock_screenshot() -> Image.Image:
    """Create a mock screenshot with some UI elements."""
    from PIL import ImageDraw

    img = Image.new("RGB", (1080, 2400), color="white")
    draw = ImageDraw.Draw(img)

    # Mock header
    draw.rectangle([0, 0, 1080, 150], fill=(59, 130, 246))

    # Mock search bar
    draw.rectangle([50, 200, 1030, 320], fill=(229, 231, 235), outline="gray", width=3)

    # Mock buttons
    button_y = 500
    for i in range(3):
        x = 100 + i * 320
        draw.rectangle(
            [x, button_y, x + 280, button_y + 120],
            fill=(34, 197, 94),
            outline="green",
            width=2,
        )

    # Mock list items
    for i in range(5):
        y = 800 + i * 200
        draw.rectangle(
            [50, y, 1030, y + 150], fill=(243, 244, 246), outline="gray", width=2
        )

    # Mock bottom navigation
    draw.rectangle([0, 2250, 1080, 2400], fill=(243, 244, 246))

    return img


def main():
    """Run all tests (for manual execution)."""
    print("\n🧪 Grid-Claude-Agent Test Suite\n")

    try:
        print("Testing Grid Converter...")
        test_grid_converter()
        print("✅ Grid converter tests passed\n")

        print("Testing Grid Overlay...")
        test_grid_overlay()
        print("✅ Grid overlay tests passed\n")

        print("✅ All tests passed!")
        return 0
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
