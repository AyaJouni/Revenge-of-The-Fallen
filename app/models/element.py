class Element:
    """Represents a programmable matter element with enhanced capabilities for distributed control."""
    def __init__(self, element_id, x, y):
        self.id = element_id
        self.x = x
        self.y = y
        self.target_x = None
        self.target_y = None
        
        # Attributes for distributed control and deadlock detection
        self.failed_attempts = 0
        self.last_positions = []
        self.last_distances = []
        self.stuck_count = 0
        self.priority = 0.0
        self.temp_target = None
        self.is_in_deadlock_resolution = False
    
    def set_target(self, x, y):
        """Set the target position for this element."""
        self.target_x = x
        self.target_y = y
    
    def has_target(self):
        """Check if the element has a target assigned."""
        return self.target_x is not None and self.target_y is not None
    
    def distance_to_target(self):
        """Calculate the Manhattan distance to the target."""
        if not self.has_target():
            return float('inf')
        return abs(self.x - self.target_x) + abs(self.y - self.target_y)
    
    def at_target(self):
        """Check if the element is at its target position."""
        return self.has_target() and self.x == self.target_x and self.y == self.target_y
    
    def update_history(self):
        """Update the element's position and distance history."""
        # Update position history
        self.last_positions.append((self.x, self.y))
        if len(self.last_positions) > 10:
            self.last_positions.pop(0)
        
        # Update distance history
        if self.has_target():
            self.last_distances.append(self.distance_to_target())
            if len(self.last_distances) > 10:
                self.last_distances.pop(0)
    
    def is_making_progress(self):
        """Check if the element is making progress toward its target."""
        if len(self.last_distances) < 3:
            return True
        
        # Check if distance has decreased
        return min(self.last_distances[-3:]) < self.last_distances[0]
    
    def is_cycling(self):
        """Check if the element is cycling between positions."""
        if len(self.last_positions) < 6:
            return False
        
        # Check for repeating patterns in recent history
        recent = self.last_positions[-6:]
        unique_positions = set(recent)
        
        # If cycling between 1-2 positions
        if len(unique_positions) <= 2:
            return True
            
        # Check for repeating sequence
        for i in range(2, 4):  # Check for cycles of length 2-3
            pattern = tuple(recent[-i:])
            if pattern in [tuple(recent[j:j+i]) for j in range(len(recent)-2*i+1)]:
                return True
        
        return False
    
    def reset_deadlock_state(self):
        """Reset the element's deadlock-related state."""
        self.failed_attempts = 0
        self.stuck_count = 0
        self.is_in_deadlock_resolution = False
        self.last_positions = []
        self.last_distances = []
    
    def __repr__(self):
        """String representation for debugging."""
        status = "AT_TARGET" if self.at_target() else f"DISTANCE={self.distance_to_target()}"
        return f"Element(id={self.id}, pos=({self.x},{self.y}), target=({self.target_x},{self.target_y}), {status})"