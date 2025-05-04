import numpy as np

# Grid cell types
EMPTY = 0
WALL = 1
ELEMENT = 2
TARGET = 3

class Grid:
    """Represents the 2D grid environment."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Initialize grid with all empty cells
        self.grid = np.zeros((height, width), dtype=np.int8)
        # Set outer boundary as walls
        self.grid[0, :] = WALL
        self.grid[height-1, :] = WALL
        self.grid[:, 0] = WALL
        self.grid[:, width-1] = WALL
    
    def clear_grid(self):
        """Clear the grid, preserving walls."""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y, x] != WALL:
                    self.grid[y, x] = EMPTY
    
    def add_element(self, element):
        """Add an element to the grid."""
        if self.is_valid_position(element.x, element.y):
            # Safety check: make sure position is empty
            if self.is_element(element.x, element.y):
                print(f"WARNING: Attempted to add element at occupied position ({element.x}, {element.y})")
                return False
            if self.is_wall(element.x, element.y):
                print(f"WARNING: Attempted to add element at wall position ({element.x}, {element.y})")
                return False
                
            self.grid[element.y, element.x] = ELEMENT
            return True
        return False
    
    def remove_element(self, element):
        """Remove an element from the grid."""
        if self.is_valid_position(element.x, element.y):
            # Only clear the position if it actually contains an element
            if self.grid[element.y, element.x] == ELEMENT:
                self.grid[element.y, element.x] = EMPTY
                return True
            else:
                print(f"WARNING: Attempted to remove element from position that doesn't contain an element ({element.x}, {element.y})")
        return False
    
    def move_element(self, element, new_x, new_y):
        """Move an element to a new position with improved safety checks."""
        # Check if the new position is valid
        if not self.is_valid_position(new_x, new_y):
            print(f"ERROR: Invalid position: ({new_x}, {new_y})")
            return False
        
        # Check if the element is at a valid position
        if not self.is_valid_position(element.x, element.y):
            print(f"ERROR: Element at invalid position: ({element.x}, {element.y})")
            return False
        
        # Check if the new position is empty or at least not a wall
        if self.is_wall(new_x, new_y):
            print(f"ERROR: Cannot move to wall at ({new_x}, {new_y})")
            return False
        
        # Critical check: Ensure new position doesn't already have an element
        if self.is_element(new_x, new_y):
            print(f"ERROR: Cannot move to position with another element at ({new_x}, {new_y})")
            return False
        
        # Check that starting position actually has an element
        if not self.is_element(element.x, element.y):
            print(f"ERROR: No element at starting position ({element.x}, {element.y})")
            return False
        
        # Execute the move
        self.grid[element.y, element.x] = EMPTY
        self.grid[new_y, new_x] = ELEMENT
        
        # Update element coordinates
        element.x = new_x
        element.y = new_y
        
        return True
    
    def is_valid_position(self, x, y):
        """Check if a position is within grid boundaries."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_playable_position(self, x, y):
        """Check if a position is within the playable area (not on walls)."""
        return self.is_valid_position(x, y) and not self.is_wall(x, y)
    
    def is_wall(self, x, y):
        """Check if a position contains a wall."""
        if not self.is_valid_position(x, y):
            return False
        return self.grid[y, x] == WALL
    
    def is_element(self, x, y):
        """Check if a position contains an element."""
        if not self.is_valid_position(x, y):
            return False
        return self.grid[y, x] == ELEMENT
    
    def is_empty(self, x, y):
        """Check if a position is empty."""
        if not self.is_valid_position(x, y):
            return False
        return self.grid[y, x] == EMPTY
    
    def is_occupied(self, x, y):
        """Check if a position is occupied (wall or element)."""
        if not self.is_valid_position(x, y):
            return True  # Positions outside the grid are considered occupied
        return self.grid[y, x] in [WALL, ELEMENT]
    
    def set_target(self, x, y):
        """Mark a position as a target."""
        if self.is_playable_position(x, y):
            self.grid[y, x] = TARGET
            return True
        return False
    
    def get_neighbors(self, x, y, topology="vonNeumann"):
        """Get neighboring positions based on topology."""
        if not self.is_valid_position(x, y):
            return []
            
        neighbors = []
        
        # Von Neumann neighborhood (4 directions: N, E, S, W)
        if topology == "vonNeumann":
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:  # Up, Right, Down, Left
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny):
                    neighbors.append((nx, ny))
        
        # Moore neighborhood (8 directions including diagonals)
        elif topology == "moore":
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue  # Skip the center
                    nx, ny = x + dx, y + dy
                    if self.is_valid_position(nx, ny):
                        neighbors.append((nx, ny))
        
        return neighbors
    
    def visualize(self):
        """Return a string representation of the grid."""
        symbols = {EMPTY: ".", WALL: "#", ELEMENT: "O", TARGET: "X"}
        rows = []
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                row += symbols[self.grid[y, x]]
            rows.append(row)
        return "\n".join(rows)
    

    def get_element_at(self, x, y):
        """Return the element at the given coordinates, or None if none exists."""
        for element in self.controller.elements.values():
            if element.x == x and element.y == y:
                return element
        return None

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height