# app/controllers/deadlock_resolver.py
import random
import math

class DeadlockResolver:
    """
    Advanced deadlock detection and resolution for programmable matter.
    Implements multiple strategies to detect and break deadlocks in both
    centralized and independent control modes.
    """
    
    def __init__(self, grid, controller):
        """Initialize the deadlock resolver."""
        self.grid = grid
        self.controller = controller
        self.position_history = {}  # element_id -> list of recent positions
        self.stuck_counters = {}    # element_id -> number of steps stuck
        self.blocked_elements = set()  # Set of element IDs that appear blocked
        self.deadlock_patterns = {} # element_id -> detected patterns
        
    def update_element_status(self, element_id):
        """Update tracking information for an element."""
        if element_id not in self.controller.elements:
            return False
            
        element = self.controller.elements[element_id]
        
        # Skip elements without targets or already at targets
        if not element.has_target() or (element.x == element.target_x and element.y == element.target_y):
            # Clean up tracking data for elements at target
            if element_id in self.position_history:
                del self.position_history[element_id]
            if element_id in self.stuck_counters:
                del self.stuck_counters[element_id]
            if element_id in self.blocked_elements:
                self.blocked_elements.remove(element_id)
            if element_id in self.deadlock_patterns:
                del self.deadlock_patterns[element_id]
            return False
        
        # Update position history
        current_pos = (element.x, element.y)
        if element_id not in self.position_history:
            self.position_history[element_id] = [current_pos]
            self.stuck_counters[element_id] = 0
        else:
            # Check if position has changed
            if self.position_history[element_id][-1] != current_pos:
                self.position_history[element_id].append(current_pos)
                self.stuck_counters[element_id] = 0
                
                # If the element moved, it's not blocked
                if element_id in self.blocked_elements:
                    self.blocked_elements.remove(element_id)
            else:
                # Increment stuck counter if position hasn't changed
                self.stuck_counters[element_id] += 1
                
                # Add to blocked elements list if stuck for too long
                if self.stuck_counters[element_id] > 10 and element_id not in self.blocked_elements:
                    self.blocked_elements.add(element_id)
            
            # Keep history limited to prevent memory issues
            if len(self.position_history[element_id]) > 16:
                self.position_history[element_id] = self.position_history[element_id][-16:]
        
        # Check for deadlock patterns
        return self.detect_deadlock_patterns(element_id)
    
    def detect_deadlock_patterns(self, element_id):
        """
        Detect common deadlock patterns for an element.
        Returns True if a deadlock pattern is detected.
        """
        if element_id not in self.position_history:
            return False
            
        positions = self.position_history[element_id]
        
        # Need at least 4 positions to detect patterns
        if len(positions) < 4:
            return False
            
        # Check for oscillation pattern (A-B-A-B)
        if len(positions) >= 4:
            last_four = positions[-4:]
            if len(set(last_four)) <= 2 and last_four[0] == last_four[2] and last_four[1] == last_four[3]:
                self.deadlock_patterns[element_id] = "oscillation"
                return True
        
        # Check for triangular deadlock (A-B-C-A)
        if len(positions) >= 4:
            last_four = positions[-4:]
            if len(set(last_four)) <= 3 and last_four[0] == last_four[3]:
                self.deadlock_patterns[element_id] = "triangular"
                return True
                
        # Check for circular patterns (A-B-C-D-A-B-C-D)
        if len(positions) >= 8:
            last_eight = positions[-8:]
            first_four = last_eight[:4]
            second_four = last_eight[4:]
            if first_four == second_four:
                self.deadlock_patterns[element_id] = "circular"
                return True
                
        # Check for long-term non-progress toward target
        if len(positions) >= 8 and self.stuck_counters[element_id] >= 5:
            element = self.controller.elements[element_id]
            if element.has_target():
                initial_distance = self._manhattan_distance(positions[0], (element.target_x, element.target_y))
                current_distance = element.distance_to_target()
                
                # If distance hasn't improved in the last 8 moves, consider it deadlocked
                if current_distance >= initial_distance:
                    self.deadlock_patterns[element_id] = "no_progress"
                    return True
        
        return False
    
    def break_element_deadlock(self, element_id, topology, total_moves=None):
        """
        Try to break a deadlock for a specific element.
        Returns True if a deadlock-breaking move was executed.
        """
        if element_id not in self.controller.elements:
            return False
            
        element = self.controller.elements[element_id]
        pattern_type = self.deadlock_patterns.get(element_id, None)
        
        # Get neighboring cells
        neighbors = self.grid.get_neighbors(element.x, element.y, topology)
        valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                           if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
        
        if not valid_neighbors:
            return False
            
        # Different breaking strategies based on pattern type
        if pattern_type == "oscillation":
            # For oscillation, avoid the last 2 positions
            recent_positions = set(self.position_history[element_id][-4:])
            escape_neighbors = [pos for pos in valid_neighbors if pos not in recent_positions]
            
            if escape_neighbors:
                next_pos = random.choice(escape_neighbors)
            else:
                next_pos = random.choice(valid_neighbors)
                
        elif pattern_type == "triangular" or pattern_type == "circular":
            # For cyclic patterns, try to move toward the target through a new path
            recent_positions = set(self.position_history[element_id][-min(8, len(self.position_history[element_id])):])
            escape_neighbors = [pos for pos in valid_neighbors if pos not in recent_positions]
            
            if escape_neighbors:
                # Choose the neighbor that gets closest to target
                escape_neighbors.sort(key=lambda pos: self._manhattan_distance(pos, (element.target_x, element.target_y)))
                next_pos = escape_neighbors[0]
            else:
                # If all neighbors are in the pattern, choose any valid move
                next_pos = random.choice(valid_neighbors)
                
        elif pattern_type == "no_progress" or pattern_type is None:
            # For general deadlocks, try a more randomized approach
            if random.random() < 0.7:  # 70% chance to try a move away from the target to break the deadlock
                valid_neighbors.sort(key=lambda pos: -self._manhattan_distance(pos, (element.target_x, element.target_y)))
                next_pos = valid_neighbors[0]
            else:
                next_pos = random.choice(valid_neighbors)
        else:
            # Default to random movement
            next_pos = random.choice(valid_neighbors)
        
        # Execute the move
        old_pos = (element.x, element.y)
        success = self.grid.move_element(element, next_pos[0], next_pos[1])
        
        if success and total_moves is not None:
            move = {"agentId": element.id, "from": old_pos, "to": next_pos}
            total_moves.append(move)
            
            # Clear pattern detection for this element
            if element_id in self.deadlock_patterns:
                del self.deadlock_patterns[element_id]
                
            return True
            
        return False
    
    def break_global_deadlock(self, topology, total_moves=None):
        """
        Attempt to break a global deadlock by identifying and moving key elements.
        Returns True if any deadlock-breaking move was executed.
        """
        # Strategy 1: Focus on elements with detected patterns
        for element_id in list(self.deadlock_patterns.keys()):
            if self.break_element_deadlock(element_id, topology, total_moves):
                return True
        
        # Strategy 2: Find blocking elements
        blocking_pairs = self.find_blocking_pairs(topology)
        if blocking_pairs:
            # Sort to prioritize elements blocking others that are close to their targets
            blocking_pairs.sort(key=lambda pair: pair[1].distance_to_target())
            
            for blocking_element, blocked_element in blocking_pairs:
                # Find alternate positions for blocker
                neighbors = self.grid.get_neighbors(blocking_element.x, blocking_element.y, topology)
                valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                               if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if valid_neighbors:
                    # Sort by how good the move is for the blocker
                    valid_neighbors.sort(key=lambda pos: 
                                     self._manhattan_distance(pos, (blocking_element.target_x, blocking_element.target_y)))
                    
                    # Try to move the blocker
                    next_pos = valid_neighbors[0]
                    old_pos = (blocking_element.x, blocking_element.y)
                    success = self.grid.move_element(blocking_element, next_pos[0], next_pos[1])
                    
                    if success and total_moves is not None:
                        move = {"agentId": blocking_element.id, "from": old_pos, "to": next_pos}
                        total_moves.append(move)
                        return True
        
        # Strategy 3: Try to move any element that's stuck but not at its target
        stuck_elements = [(e_id, self.stuck_counters.get(e_id, 0)) 
                       for e_id, e in self.controller.elements.items()
                       if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
        
        if stuck_elements:
            # Sort by stuck time (descending)
            stuck_elements.sort(key=lambda x: x[1], reverse=True)
            
            # Try the most stuck elements first
            for element_id, _ in stuck_elements[:3]:  # Try the top 3 most stuck
                element = self.controller.elements[element_id]
                
                neighbors = self.grid.get_neighbors(element.x, element.y, topology)
                valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                               if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if valid_neighbors:
                    # Make a move that maximizes future mobility
                    best_pos = None
                    max_mobility = -1
                    
                    for nx, ny in valid_neighbors:
                        future_neighbors = self.grid.get_neighbors(nx, ny, topology)
                        mobility = sum(1 for fx, fy in future_neighbors 
                                   if not self.grid.is_wall(fx, fy) and not self.grid.is_element(fx, fy))
                        
                        if mobility > max_mobility:
                            max_mobility = mobility
                            best_pos = (nx, ny)
                    
                    if best_pos:
                        old_pos = (element.x, element.y)
                        success = self.grid.move_element(element, best_pos[0], best_pos[1])
                        
                        if success and total_moves is not None:
                            move = {"agentId": element.id, "from": old_pos, "to": best_pos}
                            total_moves.append(move)
                            return True
        
        # Strategy 4: Last resort - try a random move for a random element
        non_target_elements = [e for e in self.controller.elements.values() 
                           if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
        
        if non_target_elements:
            element = random.choice(non_target_elements)
            neighbors = self.grid.get_neighbors(element.x, element.y, topology)
            valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                           if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
            
            if valid_neighbors:
                next_pos = random.choice(valid_neighbors)
                old_pos = (element.x, element.y)
                success = self.grid.move_element(element, next_pos[0], next_pos[1])
                
                if success and total_moves is not None:
                    move = {"agentId": element.id, "from": old_pos, "to": next_pos}
                    total_moves.append(move)
                    return True
        
        return False
    
    def find_blocking_pairs(self, topology):
        """
        Find pairs of elements where one element is blocking another's path to its target.
        
        Returns:
            List of tuples (blocking_element, blocked_element)
        """
        blocking_pairs = []
        
        # Get elements that are not at their targets
        non_target_elements = [e for e in self.controller.elements.values() 
                           if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
        
        for blocked_element in non_target_elements:
            # Start with a simple blocking check: is there an element directly between this and target?
            dx = 1 if blocked_element.target_x > blocked_element.x else (-1 if blocked_element.target_x < blocked_element.x else 0)
            dy = 1 if blocked_element.target_y > blocked_element.y else (-1 if blocked_element.target_y < blocked_element.y else 0)
            
            # Check the immediate next step position
            next_x, next_y = blocked_element.x + dx, blocked_element.y + dy
            
            if self.grid.is_valid_position(next_x, next_y) and self.grid.is_element(next_x, next_y):
                # Find which element is in this position
                for potential_blocker in non_target_elements:
                    if potential_blocker.id != blocked_element.id and potential_blocker.x == next_x and potential_blocker.y == next_y:
                        blocking_pairs.append((potential_blocker, blocked_element))
                        break
            
            # More advanced detection: temporarily remove this element, then try removing each other
            # element to see if that opens a path
            if topology == "vonNeumann" and blocked_element.id in self.blocked_elements:
                # Only do this expensive check for von Neumann topology and elements we think are blocked
                self.grid.remove_element(blocked_element)
                
                # Try to find a direct path with no elements removed
                direct_path_exists = False
                try:
                    # Use simple BFS for speed
                    from collections import deque
                    
                    # Simple BFS implementation
                    start = (blocked_element.x, blocked_element.y)
                    target = (blocked_element.target_x, blocked_element.target_y)
                    
                    queue = deque([start])
                    visited = {start}
                    
                    while queue and not direct_path_exists:
                        x, y = queue.popleft()
                        
                        if (x, y) == target:
                            direct_path_exists = True
                            break
                            
                        # Check neighbors
                        for nx, ny in self.grid.get_neighbors(x, y, topology):
                            if (nx, ny) not in visited and not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny):
                                queue.append((nx, ny))
                                visited.add((nx, ny))
                except Exception:
                    # Fall back if BFS fails
                    direct_path_exists = False
                
                # For each potential blocker
                for potential_blocker in non_target_elements:
                    if potential_blocker.id == blocked_element.id:
                        continue
                        
                    # Skip if already found as a blocker
                    if any(pb.id == potential_blocker.id and be.id == blocked_element.id for pb, be in blocking_pairs):
                        continue
                        
                    # Remove the potential blocker
                    self.grid.remove_element(potential_blocker)
                    
                    # Check if removing this opens a path
                    path_opens = False
                    try:
                        # Use simple BFS for speed
                        from collections import deque
                        
                        # Simple BFS implementation
                        start = (blocked_element.x, blocked_element.y)
                        target = (blocked_element.target_x, blocked_element.target_y)
                        
                        queue = deque([start])
                        visited = {start}
                        
                        while queue and not path_opens:
                            x, y = queue.popleft()
                            
                            if (x, y) == target:
                                path_opens = True
                                break
                                
                            # Check neighbors
                            for nx, ny in self.grid.get_neighbors(x, y, topology):
                                if (nx, ny) not in visited and not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny):
                                    queue.append((nx, ny))
                                    visited.add((nx, ny))
                    except Exception:
                        # Fall back if BFS fails
                        path_opens = False
                    
                    # Add blocker if removing it opened a path
                    if path_opens and not direct_path_exists:
                        blocking_pairs.append((potential_blocker, blocked_element))
                    
                    # Put the potential blocker back
                    self.grid.add_element(potential_blocker)
                
                # Put the original element back
                self.grid.add_element(blocked_element)
        
        return blocking_pairs
    
    def _manhattan_distance(self, pos1, pos2):
        """Calculate Manhattan distance between two points."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])