"""Grid overlay system for screenshots.

Adds grid lines and labels to screenshots to help Claude understand coordinates.
"""

import base64
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from lightguiagent.config import GRID_CONFIG


class GridOverlay:
    """Adds grid overlay to screenshots."""

    def __init__(self, config=None):
        """Initialize with grid configuration.

        Args:
            config: Optional custom grid config, defaults to GRID_CONFIG
        """
        self.config = config or GRID_CONFIG
        self.cols = self.config["grid_cols"]
        self.rows = self.config["grid_rows"]
        self.cell_width = self.config["cell_width"]
        self.cell_height = self.config["cell_height"]

        # Visual settings
        self.line_color = self.config["line_color"]
        self.line_width = self.config["line_width"]
        self.label_size = self.config["label_size"]
        self.label_color = self.config["label_color"]
        self.label_bg_color = self.config.get("label_bg_color", (0, 0, 0, 180))

        # Column letters
        self.col_letters = [chr(65 + i) for i in range(self.cols)]

        # Try to load font
        try:
            self.font = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", self.label_size
            )
        except Exception:
            # Fallback to default font
            self.font = ImageFont.load_default()

    def apply(self, image_input) -> Image.Image:
        """Apply grid overlay to an image.

        Args:
            image_input: Can be:
                - PIL Image object
                - Path to image file (str or Path)
                - File-like object

        Returns:
            PIL Image with grid overlay applied
        """
        # Load image if needed
        if isinstance(image_input, (str, Path)):
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input.copy()
        else:
            image = Image.open(image_input)

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Create drawing context
        draw = ImageDraw.Draw(image, "RGBA")

        # Draw vertical grid lines (columns)
        for i in range(self.cols + 1):
            x = int(i * self.cell_width)
            draw.line(
                [(x, 0), (x, self.config["screen_height"])],
                fill=self.line_color,
                width=self.line_width,
            )

        # Draw horizontal grid lines (rows)
        for i in range(self.rows + 1):
            y = int(i * self.cell_height)
            draw.line(
                [(0, y), (self.config["screen_width"], y)],
                fill=self.line_color,
                width=self.line_width,
            )

        # Draw column labels (A, B, C, ...)
        label_y_top = 10
        label_y_bottom = int(self.config["screen_height"] - self.label_size - 10)

        for i, letter in enumerate(self.col_letters):
            x = int((i + 0.5) * self.cell_width)

            # Top labels
            self._draw_label(draw, letter, x, label_y_top)
            # Bottom labels for easier reading
            self._draw_label(draw, letter, x, label_y_bottom)

        # Draw row labels (1, 2, 3, ...)
        label_x_left = 10
        label_x_right = int(self.config["screen_width"] - self.label_size - 10)

        for i in range(self.rows):
            row_num = str(i + 1)
            y = int((i + 0.5) * self.cell_height)

            # Left labels
            self._draw_label(draw, row_num, label_x_left, y)
            # Right labels for easier reading
            self._draw_label(draw, row_num, label_x_right, y)

        # Draw inner coordinate labels (optional)
        if self.config.get("show_inner_labels", True):
            self._draw_inner_labels(draw)

        return image

    def _draw_label(self, draw, text, x, y, opacity=None):
        """Draw a label with background for better visibility.

        Args:
            draw: ImageDraw object
            text: Label text
            x, y: Center position of the label
            opacity: Optional opacity override for label (0-255)
        """
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate background rectangle
        padding = 4
        bg_left = x - text_width // 2 - padding
        bg_top = y - text_height // 2 - padding
        bg_right = x + text_width // 2 + padding
        bg_bottom = y + text_height // 2 + padding

        # Apply custom opacity if provided
        if opacity is not None:
            bg_color = self.label_bg_color[:3] + (opacity,)
            text_color = self.label_color + (opacity,)
        else:
            bg_color = self.label_bg_color
            text_color = self.label_color

        # Draw background
        draw.rectangle([bg_left, bg_top, bg_right, bg_bottom], fill=bg_color)

        # Draw text
        text_x = x - text_width // 2
        text_y = y - text_height // 2
        draw.text((text_x, text_y), text, fill=text_color, font=self.font)

    def _draw_inner_labels(self, draw):
        """Draw coordinate labels inside grid cells for easier identification.
        
        Args:
            draw: ImageDraw object
        """
        interval = self.config.get("inner_label_interval", 3)
        opacity = self.config.get("inner_label_opacity", 128)
        
        # Draw labels at regular intervals (e.g., every 3 cells)
        for col_idx in range(interval - 1, self.cols, interval):
            for row_idx in range(interval - 1, self.rows, interval):
                # Calculate center position of cell
                x = int((col_idx + 0.5) * self.cell_width)
                y = int((row_idx + 0.5) * self.cell_height)
                
                # Create coordinate label (e.g., "E5")
                col_letter = self.col_letters[col_idx]
                row_num = str(row_idx + 1)
                label_text = f"{col_letter}{row_num}"
                
                # Draw semi-transparent label
                self._draw_label(draw, label_text, x, y, opacity=opacity)

    def compress_and_encode(
        self, image: Image.Image, target_size=None, quality=None
    ) -> str:
        """Compress image and encode to base64.

        Args:
            image: PIL Image
            target_size: Target size (will be square), defaults to config
            quality: JPEG quality 1-100, defaults to config

        Returns:
            Base64 encoded string suitable for Claude API
        """
        target_size = target_size or self.config["target_size"]
        quality = quality or self.config["compression_quality"]

        # Resize to target size (square)
        image_resized = image.resize(
            (target_size, target_size), Image.Resampling.LANCZOS
        )

        # Convert to JPEG and encode
        buffer = io.BytesIO()
        image_resized.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        # Encode to base64
        image_bytes = buffer.read()
        b64_string = base64.b64encode(image_bytes).decode("utf-8")

        return b64_string

    def process_screenshot(
        self, screenshot_path, save_path=None
    ) -> tuple[Image.Image, str]:
        """Complete pipeline: load screenshot, add grid, compress, encode.

        Args:
            screenshot_path: Path to original screenshot
            save_path: Optional path to save annotated image

        Returns:
            (annotated_image, base64_string)
        """
        # Apply grid overlay
        annotated_image = self.apply(screenshot_path)

        # Save if requested
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            annotated_image.save(save_path)

        # Compress and encode
        b64_string = self.compress_and_encode(annotated_image)

        return annotated_image, b64_string

    def mark_action(self, image: Image.Image, action: dict) -> Image.Image:
        """Mark the action location on the image with a visual indicator.

        Args:
            image: PIL Image with grid overlay
            action: Action dict with 'action' and 'grid' or 'value' fields

        Returns:
            Image with action marker
        """
        from lightguiagent.grid_converter import grid_to_pixel

        # Create a copy to avoid modifying original
        marked_image = image.copy()
        draw = ImageDraw.Draw(marked_image, "RGBA")

        action_type = action.get("action")

        if action_type == "CLICK":
            # Get click position
            grid = action.get("grid", "")
            if not grid:
                return marked_image

            try:
                x, y = grid_to_pixel(grid)

                # Draw a red circle at click position
                radius = 40
                draw.ellipse(
                    [(x - radius, y - radius), (x + radius, y + radius)],
                    outline=(255, 0, 0),
                    width=6,
                )

                # Draw crosshair
                line_len = 60
                draw.line(
                    [(x - line_len, y), (x + line_len, y)], fill=(255, 0, 0), width=4
                )
                draw.line(
                    [(x, y - line_len), (x, y + line_len)], fill=(255, 0, 0), width=4
                )

                # Add label
                label = f"CLICK {grid}"
                bbox = draw.textbbox((0, 0), label, font=self.font)
                label_width = bbox[2] - bbox[0]
                label_height = bbox[3] - bbox[1]

                label_x = x - label_width // 2
                label_y = y - radius - label_height - 10

                # Draw background for label
                draw.rectangle(
                    [
                        (label_x - 5, label_y - 5),
                        (label_x + label_width + 5, label_y + label_height + 5),
                    ],
                    fill=(255, 0, 0, 200),
                )
                draw.text(
                    (label_x, label_y), label, fill=(255, 255, 255), font=self.font
                )

            except Exception as e:
                print(f"  ⚠️  Failed to mark CLICK action: {e}")

        elif action_type == "TYPE":
            # For TYPE action, show text at top of screen
            text = action.get("value", "")
            if text:
                label = f'TYPE: "{text}"'
                bbox = draw.textbbox((0, 0), label, font=self.font)
                label_width = bbox[2] - bbox[0]
                label_height = bbox[3] - bbox[1]

                # Position at top center (use actual image width)
                label_x = (marked_image.width - label_width) // 2
                label_y = 20

                # Draw background
                draw.rectangle(
                    [
                        (label_x - 10, label_y - 5),
                        (label_x + label_width + 10, label_y + label_height + 5),
                    ],
                    fill=(0, 128, 255, 200),
                )
                draw.text(
                    (label_x, label_y), label, fill=(255, 255, 255), font=self.font
                )

        elif action_type == "AWAKE":
            # For AWAKE action, show package name at top
            package = action.get("value", "")
            if package:
                label = f"AWAKE: {package}"
                bbox = draw.textbbox((0, 0), label, font=self.font)
                label_width = bbox[2] - bbox[0]
                label_height = bbox[3] - bbox[1]

                # Position at top center (use actual image width)
                label_x = (marked_image.width - label_width) // 2
                label_y = 20

                draw.rectangle(
                    [
                        (label_x - 10, label_y - 5),
                        (label_x + label_width + 10, label_y + label_height + 5),
                    ],
                    fill=(0, 200, 0, 200),
                )
                draw.text(
                    (label_x, label_y), label, fill=(255, 255, 255), font=self.font
                )

        return marked_image


# Convenience functions
_default_overlay = GridOverlay()


def apply_grid(image_input) -> Image.Image:
    """Apply grid overlay (convenience function)."""
    return _default_overlay.apply(image_input)


def process_screenshot(screenshot_path, save_path=None) -> tuple[Image.Image, str]:
    """Process screenshot (convenience function)."""
    return _default_overlay.process_screenshot(screenshot_path, save_path)


if __name__ == "__main__":
    import sys

    print("=== Grid Overlay Test ===\n")

    # Test with a sample image
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        output_path = "debug/test_grid_overlay.png"

        print(f"Processing: {input_path}")
        overlay = GridOverlay()
        annotated, b64 = overlay.process_screenshot(input_path, output_path)

        print(f"✅ Saved annotated image: {output_path}")
        print(f"📊 Image size: {annotated.size}")
        print(f"📏 Base64 length: {len(b64)} characters")
    else:
        print("Usage: python grid_overlay.py <screenshot.png>")
        print("\nCreating test grid overlay with blank canvas...")

        # Create blank test image
        test_image = Image.new("RGB", (1080, 2400), color=(240, 240, 240))
        overlay = GridOverlay()
        annotated = overlay.apply(test_image)

        output_path = "debug/test_grid_blank.png"
        annotated.save(output_path)
        print(f"✅ Saved test grid: {output_path}")
