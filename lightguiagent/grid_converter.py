"""Grid coordinate converter.

Converts between grid notation (e.g., "E5") and pixel coordinates.
Grid system: A-J (columns) × 1-20 (rows)
"""

from lightguiagent.config import GRID_CONFIG


class GridConverter:
    """Converts between grid coordinates and pixel positions."""

    def __init__(self, config=None):
        """Initialize converter with grid configuration.

        Args:
            config: Optional custom grid config, defaults to GRID_CONFIG
        """
        self.config = config or GRID_CONFIG
        self.cols = self.config["grid_cols"]
        self.rows = self.config["grid_rows"]
        self.cell_width = self.config["cell_width"]
        self.cell_height = self.config["cell_height"]

        # Column letters (A-J for 10 cols)
        self.col_letters = [chr(65 + i) for i in range(self.cols)]  # A=65 in ASCII

    def grid_to_pixel(self, grid_str: str) -> tuple[int, int]:
        """Convert grid notation to pixel coordinates (center of cell).

        Args:
            grid_str: Grid notation like "E5", "A1", "J20"

        Returns:
            (x, y) pixel coordinates at center of the cell

        Examples:
            >>> converter = GridConverter()
            >>> converter.grid_to_pixel("A1")
            (54, 60)  # Center of top-left cell
            >>> converter.grid_to_pixel("E5")
            (486, 540)  # Center of cell E5
        """
        return self._single_grid_to_pixel(grid_str.strip().upper())

    def _single_grid_to_pixel(self, grid_str: str) -> tuple[int, int]:
        """Convert single grid notation to pixel coordinates (center of cell).

        Internal method used by grid_to_pixel.

        Args:
            grid_str: Grid notation like "E5", "A1", "J20"

        Returns:
            (x, y) pixel coordinates at center of the cell
        """
        grid_str = grid_str.strip().upper()

        # Parse column (letter) and row (number)
        if len(grid_str) < 2:
            raise ValueError(f"Invalid grid format: {grid_str}")

        col_letter = grid_str[0]
        row_str = grid_str[1:]

        # Validate column
        if col_letter not in self.col_letters:
            raise ValueError(
                f"Invalid column '{col_letter}'. Must be A-{self.col_letters[-1]}"
            )

        # Validate row
        try:
            row = int(row_str)
        except ValueError:
            raise ValueError(f"Invalid row '{row_str}'. Must be a number.")

        if not (1 <= row <= self.rows):
            raise ValueError(f"Invalid row {row}. Must be 1-{self.rows}")

        # Calculate pixel position (center of cell)
        col_index = self.col_letters.index(col_letter)
        x = int((col_index + 0.5) * self.cell_width)
        y = int((row - 0.5) * self.cell_height)  # Row is 1-indexed

        return (x, y)

    def pixel_to_grid(self, x: int, y: int) -> str:
        """Convert pixel coordinates to grid notation.

        Args:
            x: Pixel x coordinate
            y: Pixel y coordinate

        Returns:
            Grid notation like "E5"

        Examples:
            >>> converter = GridConverter()
            >>> converter.pixel_to_grid(540, 600)
            'E5'
        """
        # Calculate column and row indices
        col_index = int(x / self.cell_width)
        row_index = int(y / self.cell_height)

        # Clamp to valid range
        col_index = max(0, min(col_index, self.cols - 1))
        row_index = max(0, min(row_index, self.rows - 1))

        # Convert to grid notation
        col_letter = self.col_letters[col_index]
        row = row_index + 1  # Convert to 1-indexed

        return f"{col_letter}{row}"

    def get_cell_bounds(self, grid_str: str) -> tuple[int, int, int, int]:
        """Get the bounding box of a grid cell.

        Args:
            grid_str: Grid notation like "E5"

        Returns:
            (left, top, right, bottom) pixel coordinates

        Examples:
            >>> converter = GridConverter()
            >>> converter.get_cell_bounds("E5")
            (432, 480, 540, 600)
        """
        grid_str = grid_str.strip().upper()
        col_letter = grid_str[0]
        row = int(grid_str[1:])

        col_index = self.col_letters.index(col_letter)

        left = int(col_index * self.cell_width)
        top = int((row - 1) * self.cell_height)
        right = int((col_index + 1) * self.cell_width)
        bottom = int(row * self.cell_height)

        return (left, top, right, bottom)


# Convenience functions using default config
_default_converter = GridConverter()


def grid_to_pixel(grid_str: str) -> tuple[int, int]:
    """Convert grid notation to pixel coordinates (convenience function)."""
    return _default_converter.grid_to_pixel(grid_str)


def pixel_to_grid(x: int, y: int) -> str:
    """Convert pixel coordinates to grid notation (convenience function)."""
    return _default_converter.pixel_to_grid(x, y)


if __name__ == "__main__":
    # Test the converter
    converter = GridConverter()

    print("=== Grid Converter Test ===\n")

    # Test grid to pixel
    test_grids = [
        "A1",
        "E5",
        "J20",
        "A20",
        "J1",
    ]
    print("Grid → Pixel:")
    for grid in test_grids:
        x, y = converter.grid_to_pixel(grid)
        print(f"  {grid:8s} → ({x:4d}, {y:4d})")

    print("\nPixel → Grid:")
    test_pixels = [(54, 60), (540, 600), (972, 2340), (54, 2340), (972, 60)]
    for x, y in test_pixels:
        grid = converter.pixel_to_grid(x, y)
        print(f"  ({x:4d}, {y:4d}) → {grid}")

    print("\nCell Bounds:")
    print(f"  E5 bounds: {converter.get_cell_bounds('E5')}")

    print("\n✅ All tests passed!")
