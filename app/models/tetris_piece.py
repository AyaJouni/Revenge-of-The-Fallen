# app/models/tetris_piece.py
class TetrisPiece:
    """Represents a tetris piece in the programmable matter simulation."""
    
    # Tetris piece definitions - standard shapes
    SHAPES = {
        'I': [
            [(0, 0), (1, 0), (2, 0), (3, 0)],  # Horizontal
            [(0, 0), (0, 1), (0, 2), (0, 3)]   # Vertical
        ],
        'J': [
            [(0, 0), (0, 1), (1, 1), (2, 1)],  # ┌──
            [(1, 0), (2, 0), (1, 1), (1, 2)],  # │ bottom
            [(0, 1), (1, 1), (2, 1), (2, 2)],  # ──┘
            [(1, 0), (1, 1), (1, 2), (0, 2)]   # top │
        ],
        'L': [
            [(2, 0), (0, 1), (1, 1), (2, 1)],  # ──┐
            [(1, 0), (1, 1), (1, 2), (2, 2)],  # │ bottom
            [(0, 1), (1, 1), (2, 1), (0, 2)],  # └──
            [(0, 0), (1, 0), (1, 1), (1, 2)]   # top ┘
        ],
        'O': [
            [(0, 0), (1, 0), (0, 1), (1, 1)]   # Square (only one rotation)
        ],
        'S': [
            [(1, 0), (2, 0), (0, 1), (1, 1)],  # Horizontal
            [(1, 0), (1, 1), (2, 1), (2, 2)]   # Vertical
        ],
        'T': [
            [(1, 0), (0, 1), (1, 1), (2, 1)],  # Top
            [(1, 0), (1, 1), (2, 1), (1, 2)],  # Right
            [(0, 1), (1, 1), (2, 1), (1, 2)],  # Bottom
            [(1, 0), (0, 1), (1, 1), (1, 2)]   # Left
        ],
        'Z': [
            [(0, 0), (1, 0), (1, 1), (2, 1)],  # Horizontal
            [(2, 0), (1, 1), (2, 1), (1, 2)]   # Vertical
        ]
    }
    
    # Colors for each piece (matches the classic Tetris colors)
    COLORS = {
        'I': (0, 255, 255),   # Cyan
        'J': (0, 0, 255),     # Blue
        'L': (255, 127, 0),   # Orange
        'O': (255, 255, 0),   # Yellow
        'S': (0, 255, 0),     # Green
        'T': (170, 0, 255),   # Purple
        'Z': (255, 0, 0)      # Red
    }
    
    def __init__(self, shape_type, grid_width, x=None, y=None):
        """
        Initialize a new Tetris piece.
        
        Args:
            shape_type: Letter representing the shape ('I', 'J', 'L', 'O', 'S', 'T', 'Z')
            grid_width: Width of the game grid (to calculate default x position)
            x: Starting x coordinate (defaults to center top)
            y: Starting y coordinate (defaults to 0, top of grid)
        """
        if shape_type not in self.SHAPES:
            raise ValueError(f"Unknown Tetris shape: {shape_type}")
            
        self.shape_type = shape_type
        self.rotation = 0  # Current rotation index
        self.color = self.COLORS[shape_type]
        
        # Calculate piece width for centering
        first_shape = self.SHAPES[shape_type][0]
        min_x = min(x for x, y in first_shape)
        max_x = max(x for x, y in first_shape)
        piece_width = max_x - min_x + 1
        
        # Set position (center of grid if not specified)
        self.x = x if x is not None else ((grid_width - piece_width) // 2)
        self.y = y if y is not None else 0
        
        # Locked status (becomes locked when it lands)
        self.locked = False
    
    def get_current_shape(self):
        """Get the current shape configuration based on rotation."""
        return self.SHAPES[self.shape_type][self.rotation % len(self.SHAPES[self.shape_type])]
    
    def get_positions(self):
        """Get the absolute grid positions of all cells in the piece."""
        shape = self.get_current_shape()
        return [(self.x + dx, self.y + dy) for dx, dy in shape]
    
    def rotate(self, clockwise=True):
        """
        Rotate the piece clockwise or counterclockwise.
        
        Args:
            clockwise: True for clockwise rotation, False for counterclockwise
            
        Returns:
            The new positions after rotation
        """
        total_rotations = len(self.SHAPES[self.shape_type])
        
        if clockwise:
            self.rotation = (self.rotation + 1) % total_rotations
        else:
            self.rotation = (self.rotation - 1) % total_rotations
            
        return self.get_positions()
    
    def move(self, dx, dy):
        """
        Move the piece by the specified delta.
        
        Args:
            dx: Change in x-coordinate
            dy: Change in y-coordinate
            
        Returns:
            The new positions after movement
        """
        if self.locked:
            return self.get_positions()  # No movement if locked
            
        self.x += dx
        self.y += dy
        return self.get_positions()
    
    def lock(self):
        """Lock the piece in place (cannot be moved after locking)."""
        self.locked = True
        
    def get_shadow_positions(self, max_y):
        """
        Calculate the 'shadow' position (where piece would land if dropped).
        This is useful for showing players where the piece will land.
        
        Args:
            max_y: Maximum y-value to check (usually grid height)
            
        Returns:
            List of positions where the shadow would be
        """
        current_positions = self.get_positions()
        shadow_y = self.y
        
        # Drop the shadow down until it would hit something
        while shadow_y < max_y:
            shadow_positions = [(x, shadow_y + 1 + (y - self.y)) for x, y in current_positions]
            
            # This would need to check for collisions in the actual grid
            # For now, just use max_y as a boundary
            if any(y >= max_y for _, y in shadow_positions):
                break
                
            shadow_y += 1
            
        # Calculate the final shadow positions
        return [(x, shadow_y + (y - self.y)) for x, y in current_positions]
    
    def get_preview_positions(self):
        """Get the positions for piece preview (shown at the top of the game)."""
        shape = self.get_current_shape()
        
        # Normalize to start at 0,0
        min_x = min(x for x, y in shape)
        min_y = min(y for x, y in shape)
        
        return [(x - min_x, y - min_y) for x, y in shape]