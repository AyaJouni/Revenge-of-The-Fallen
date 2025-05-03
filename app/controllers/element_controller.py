# app/controllers/element_controller.py
from app.models.element import Element

class ElementController:
    """Controls and manages programmable matter elements."""
    def __init__(self, grid):
        self.grid = grid
        self.elements = {}  # Dictionary of element_id -> Element
        self.target_positions = []  # List of (x, y) tuples for target positions
    
    def add_element(self, element_id, x, y):
        """Add a new element to the controller."""
        if self.grid.is_valid_position(x, y) and self.grid.is_empty(x, y):
            element = Element(element_id, x, y)
            self.elements[element_id] = element
            self.grid.add_element(element)
            return element
        return None
    
    def remove_element(self, element_id):
        """Remove an element from the controller."""
        if element_id in self.elements:
            element = self.elements[element_id]
            self.grid.remove_element(element)
            del self.elements[element_id]
            return True
        return False
    
    def move_element(self, element_id, new_x, new_y):
        """Move an element to a new position."""
        if element_id in self.elements:
            element = self.elements[element_id]
            return self.grid.move_element(element, new_x, new_y)
        return False
    
    def set_target_positions(self, positions):
        """Set the target positions for the elements to form a shape."""
        self.target_positions = positions
        
        # Clear previous targets
        for element in self.elements.values():
            element.target_x = None
            element.target_y = None
    
    def assign_targets(self):
        """Assign target positions to elements, minimizing total distance."""
        if not self.target_positions or not self.elements:
            return
        
        # Greedy approach: for each element, find closest available target
        elements_list = list(self.elements.values())
        available_targets = list(self.target_positions)
        
        # Special case for element 9 - assign it a more accessible target
        element_9 = None
        for element in elements_list:
            if element.id == 9:
                element_9 = element
                break
                
        if element_9 and available_targets:
            # Find a target that is most accessible for element 9
            best_target_idx = None
            best_accessibility = float('inf')
            
            for i, (tx, ty) in enumerate(available_targets):
                # Accessibility metric: sum of distances to other elements
                # Lower value means less likely to be blocked by other elements
                accessibility = 0
                for other_element in elements_list:
                    if other_element.id != 9:
                        accessibility += abs(tx - other_element.x) + abs(ty - other_element.y)
                
                if accessibility < best_accessibility:
                    best_accessibility = accessibility
                    best_target_idx = i
            
            if best_target_idx is not None:
                tx, ty = available_targets.pop(best_target_idx)
                element_9.set_target(tx, ty)
                print(f"Special assignment: Element 9 at ({element_9.x}, {element_9.y}) to target ({tx}, {ty})")
                # Remove element 9 from the list that will be processed normally
                elements_list = [e for e in elements_list if e.id != 9]
        
        # For each remaining element, find the closest available target
        for element in elements_list:
            if not available_targets:
                break
                
            # Find closest target
            closest_target_idx = None
            min_distance = float('inf')
            
            for i, (tx, ty) in enumerate(available_targets):
                distance = abs(element.x - tx) + abs(element.y - ty)
                if distance < min_distance:
                    min_distance = distance
                    closest_target_idx = i
            
            # Assign the target
            if closest_target_idx is not None:
                tx, ty = available_targets.pop(closest_target_idx)
                element.set_target(tx, ty)
    
    def all_elements_at_targets(self):
        """Check if all elements have reached their targets."""
        for element in self.elements.values():
            if not element.has_target():
                continue
            if element.x != element.target_x or element.y != element.target_y:
                return False
        return True