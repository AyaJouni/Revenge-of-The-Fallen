#last time done
import time
import heapq
import random
from app.models.grid import Grid
from app.models.shape import ShapeGenerator
from app.controllers.element_controller import ElementController
from app.algorithms.astar import astar_pathfind
from app.algorithms.bfs import bfs_pathfind
from app.algorithms.greedy import greedy_pathfind


class ProgrammableMatterSimulation:
    """Main simulation class for the programmable matter system."""

    def __init__(self, width=12, height=12):
        """
        Initialize the simulation with a grid of the specified width and height.
        """
        if width < 3 or height < 3:
            raise ValueError("Grid width and height must be at least 3 to account for walls.")
        self.grid = Grid(width, height)
        self.controller = ElementController(self.grid)
        self.shape_type = None  # Store the current shape type
        self.reset()

    def reset(self):
        """
        Reset the simulation to its initial state.
        """
        self.grid.clear_grid()
        self.controller.elements.clear()
        self.controller.target_positions = []

    def initialize_elements(self, num_elements):
        """
        Initialize the specified number of elements at the bottom of the grid.
        Ensures elements are placed within the grid boundaries and not on walls.
        """
        self.reset()

        boundary_size = 1  # Default boundary size
        safe_width = self.grid.width - (2 * boundary_size)
        safe_height = self.grid.height - (2 * boundary_size)

        # Calculate the maximum number of elements that can fit in the grid
        max_elements = safe_width * safe_height
        if num_elements > max_elements:
            raise ValueError(f"Cannot place {num_elements} elements. Maximum allowed is {max_elements}.")

        # Place elements in rows, starting from the bottom
        elements_placed = 0
        for row in range(safe_height):
            y = self.grid.height - (boundary_size + 1 + row)  # Move up one row at a time
            for col in range(safe_width):
                x = boundary_size + col
                if elements_placed >= num_elements:
                    break  # Stop if all elements are placed

                # Ensure the position is not a wall and is empty
                if not self.grid.is_wall(x, y) and self.grid.is_empty(x, y):
                    self.controller.add_element(elements_placed, x, y)
                    elements_placed += 1

            if elements_placed >= num_elements:
                break  # Stop if all elements are placed

        # Debug: Print the positions of the placed elements
        print(f"Initialized {elements_placed} elements:")
        for element_id, element in self.controller.elements.items():
            print(f"  Element {element_id}: ({element.x}, {element.y})")

        return self.controller.elements

    def set_target_shape(self, shape_type, num_elements):
        """
        Set the target shape for the elements.
        """
        self.shape_type = shape_type  # Store the shape type for later use
        
        target_positions = ShapeGenerator.generate_shape(
            shape_type, num_elements, self.grid.width, self.grid.height)
        
        # Validate target positions are within the grid and not on walls
        valid_targets = []
        for x, y in target_positions:
            if self.grid.is_valid_position(x, y) and not self.grid.is_wall(x, y):
                valid_targets.append((x, y))
            else:
                print(f"Warning: Target position ({x}, {y}) is invalid and will be ignored")
        
        self.controller.set_target_positions(valid_targets)
        return valid_targets

    def find_path(self, start_x, start_y, goal_x, goal_y, algorithm="astar", topology="vonNeumann"):
        """Find a path using the specified algorithm."""
        try:
            # Only check if goal is occupied by another element when it's not the element's current position
            if (start_x != goal_x or start_y != goal_y) and self.grid.is_element(goal_x, goal_y):
                print(f"Goal position ({goal_x}, {goal_y}) is blocked by another agent")
                return None, 0
            
            # Choose the appropriate algorithm
            if algorithm == "astar":
                return astar_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
            elif algorithm == "bfs":
                return bfs_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
            elif algorithm == "greedy":
                return greedy_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")
        
        except Exception as e:
            print(f"Error in find_path: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0
   
    def transform(self, algorithm="astar", topology="vonNeumann", movement="sequential", control_mode="centralized"):
        """Transform the elements to the target shape."""
        start_time = time.time()
        
        # Assign targets to elements
        self.controller.assign_targets()
        
        # Track results
        paths = {}
        total_moves = []
        total_nodes_explored = 0
        
        # Choose transformation strategy based on control mode
        if control_mode == "centralized":
            result = self._transform_centralized(algorithm, topology, movement, paths, total_moves, total_nodes_explored)
        else:
            result = self._transform_independent(algorithm, topology, movement, total_moves, total_nodes_explored)
        
        # Check if result is None (error occurred in the transformation)
        if result is None:
            # Create a default result dictionary
            result = {
                "paths": {},
                "moves": total_moves,
                "nodes_explored": total_nodes_explored,
                "success_rate": 0,
                "success": False,
                "message": "Transformation failed to complete"
            }
        else:
            # Add calculated paths to result
            result["paths"] = paths
        
        # Add elapsed time to result
        result["time"] = time.time() - start_time
        
        return result
    
    def _transform_centralized(self, algorithm, topology, movement, paths, total_moves, total_nodes_explored):
        """
        Centralized control transformation implementation.
        A central controller plans paths for all elements.
        """
        print("\nCentralized control mode")
        paths = {}
        # Sort elements by row (prioritize elements in the first row)
        sorted_elements = sorted(
            self.controller.elements.values(),
            key=lambda e: (e.y, e.distance_to_target())
        )
        
        for element in sorted_elements:
            if not element.has_target():
                continue
            
            # Temporarily remove the element from the grid for pathfinding
            self.grid.remove_element(element)
            
            # Find a path for this element
            path_result = self.find_path(
                element.x, element.y, 
                element.target_x, element.target_y,
                algorithm, topology
            )
            
            # Put the element back
            self.grid.add_element(element)
            
            if path_result and path_result[0]:  # Check if path exists
                path, nodes_explored = path_result
                paths[element.id] = path
                total_nodes_explored += nodes_explored
                
                # Execute the path for this element if using sequential movement
                if movement == "sequential":
                    for i in range(1, len(path)):
                        move = {"agentId": element.id, "from": (element.x, element.y), "to": path[i]}
                        total_moves.append(move)
                        success = self.grid.move_element(element, path[i][0], path[i][1])
                        if not success:
                            print(f"Failed to move element {element.id} to {path[i]}")
                            # Try to resolve deadlock
                            self._resolve_deadlocks(total_moves)
                            break
        
        # For parallel movement, execute all paths simultaneously
        if movement == "parallel":
            max_path_length = max([len(path) for path in paths.values()], default=0)
            
            for step in range(1, max_path_length):
                # Collect all moves for this step
                planned_moves = []
                for element_id, path in paths.items():
                    if step < len(path):
                        element = self.controller.elements[element_id]
                        planned_moves.append((element, path[step]))
                
                # Sort moves to prioritize elements closer to their targets
                planned_moves.sort(
                    key=lambda m: abs(m[0].target_x - m[1][0]) + abs(m[0].target_y - m[1][1])
                )
                
                # Execute moves with conflict resolution
                positions_taken = set()
                for element, pos in planned_moves:
                    # Skip if position already taken by another element this step
                    if pos in positions_taken:
                        continue
                        
                    # Try to move the element
                    success = self.grid.move_element(element, pos[0], pos[1])
                    if success:
                        move = {"agentId": element.id, "from": (element.x, element.y), "to": pos}
                        total_moves.append(move)
                        positions_taken.add(pos)
                
                # Check if we need to resolve deadlocks after each step
                if len(positions_taken) < len(planned_moves) / 2:  # If less than half of planned moves succeeded
                    self._resolve_deadlocks(total_moves)
        
        # Check if all elements have reached their targets
        all_at_target = all(
            (element.x == element.target_x and element.y == element.target_y) 
            for element in self.controller.elements.values() 
            if element.has_target()
        )
        
        # Calculate success metrics
        total_elements = sum(1 for element in self.controller.elements.values() if element.has_target())
        at_target_count = sum(1 for element in self.controller.elements.values() 
                             if element.has_target() and element.x == element.target_x and element.y == element.target_y)
        success_rate = at_target_count / total_elements if total_elements > 0 else 0
        
        print(f"\nCentralized transformation complete. Success rate: {success_rate:.2f}")
        
        return {
            "paths": paths,
            "moves": total_moves,
            "nodes_explored": total_nodes_explored,
            "success_rate": success_rate,
            "success": all_at_target
        }
    

    def _try_clear_target_path(self, element, total_moves):
        """
        Special handling for von Neumann topology. Tries to clear the path to an agent's target
        by temporarily moving a blocking element aside, letting the agent move to its target,
        and then returning the blocking element to its previous position if needed.
        
        Args:
            element: The element that needs to reach its target
            total_moves: List to record moves for visualization
            
        Returns:
            bool: True if the agent was successfully moved to its target, False otherwise
        """
        # Get the direction to the target
        dx = element.target_x - element.x
        dy = element.target_y - element.y
        
        # Calculate Manhattan distance to target
        manhattan_dist = abs(dx) + abs(dy)
        
        # Only proceed if the element is close to its target but not at it
        if manhattan_dist == 0:
            return False  # Already at target
        
        print(f"Trying to clear path for element {element.id} to reach target at ({element.target_x}, {element.target_y})")
        
        # Check if the target is directly occupied
        target_occupied = False
        blocking_element = None
        for other_id, other in self.controller.elements.items():
            if other_id != element.id and other.x == element.target_x and other.y == element.target_y:
                target_occupied = True
                blocking_element = other
                break
        
        if target_occupied:
            print(f"Target position ({element.target_x}, {element.target_y}) is occupied by element {blocking_element.id}")
            
            # Check if the blocking element is at its own target
            at_own_target = blocking_element.has_target() and blocking_element.x == blocking_element.target_x and blocking_element.y == blocking_element.target_y
            if at_own_target:
                print(f"Blocking element {blocking_element.id} is at its own target - can't move it")
                return False
            
            # Find a temporary position for the blocking element
            neighbors = self.grid.get_neighbors(blocking_element.x, blocking_element.y, "vonNeumann")
            valid_moves = [(nx, ny) for nx, ny in neighbors 
                        if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
            
            if not valid_moves:
                print(f"No available positions to move blocking element {blocking_element.id}")
                return False
            
            # Choose a temporary position that's not in the direction of element's movement
            if dx != 0:  # Moving horizontally
                side_moves = [pos for pos in valid_moves if pos[0] == blocking_element.x]  # Vertical moves
                if side_moves:
                    temp_pos = side_moves[0]
                else:
                    temp_pos = valid_moves[0]  # Any valid move
            else:  # Moving vertically
                side_moves = [pos for pos in valid_moves if pos[1] == blocking_element.y]  # Horizontal moves
                if side_moves:
                    temp_pos = side_moves[0]
                else:
                    temp_pos = valid_moves[0]  # Any valid move
            
            # STEP 1: Move the blocking element to the temporary position
            old_blocking_pos = (blocking_element.x, blocking_element.y)
            success1 = self.grid.move_element(blocking_element, temp_pos[0], temp_pos[1])
            
            if not success1:
                print(f"Failed to move blocking element {blocking_element.id} to temporary position")
                return False
            
            # Record the move
            move1 = {"agentId": blocking_element.id, "from": old_blocking_pos, "to": temp_pos}
            total_moves.append(move1)
            print(f"Moved blocking element {blocking_element.id} to temporary position {temp_pos}")
            
            # STEP 2: Move the original element to its target position
            old_element_pos = (element.x, element.y)
            success2 = self.grid.move_element(element, element.target_x, element.target_y)
            
            if not success2:
                # Something went wrong - move blocking element back and return
                self.grid.move_element(blocking_element, old_blocking_pos[0], old_blocking_pos[1])
                print(f"Failed to move element {element.id} to target position")
                return False
            
            # Record the move
            move2 = {"agentId": element.id, "from": old_element_pos, "to": (element.target_x, element.target_y)}
            total_moves.append(move2)
            print(f"Successfully moved element {element.id} to target position ({element.target_x}, {element.target_y})")
            
            # STEP 3: Check if the blocking element needs to return to its original position
            # This is only necessary if the blocking element was temporarily moved from its path to target
            if blocking_element.has_target():
                # Calculate if the temporary position is better or worse for the blocking element
                old_distance = abs(old_blocking_pos[0] - blocking_element.target_x) + abs(old_blocking_pos[1] - blocking_element.target_y)
                new_distance = abs(temp_pos[0] - blocking_element.target_x) + abs(temp_pos[1] - blocking_element.target_y)
                
                # Only move back if the temporary position is worse
                if new_distance > old_distance and old_element_pos != old_blocking_pos:
                    # Try to move back to original position if it's not now occupied by the moved element
                    if old_blocking_pos != (element.target_x, element.target_y):
                        success3 = self.grid.move_element(blocking_element, old_blocking_pos[0], old_blocking_pos[1])
                        if success3:
                            # Record the move back
                            move3 = {"agentId": blocking_element.id, "from": temp_pos, "to": old_blocking_pos}
                            total_moves.append(move3)
                            print(f"Moved blocking element {blocking_element.id} back to original position")
            
            return True
        
        # If the target isn't directly occupied, check if there are blocking elements in the path
        # (for von Neumann, this means checking the cardinal paths)
        if manhattan_dist > 1:
            # Check the path along X-axis
            if dx != 0:
                step_x = 1 if dx > 0 else -1
                for x in range(element.x + step_x, element.target_x + step_x, step_x):
                    # Check if this position is occupied by another element
                    for other_id, other in self.controller.elements.items():
                        if other_id != element.id and other.x == x and other.y == element.y:
                            print(f"Element {other.id} is blocking the horizontal path at ({x}, {element.y})")
                            
                            # Find a temporary position to move the blocking element
                            neighbors = self.grid.get_neighbors(other.x, other.y, "vonNeumann")
                            valid_moves = [(nx, ny) for nx, ny in neighbors 
                                        if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny) and ny != element.y]  # Avoid same row
                            
                            if valid_moves:
                                # Move the blocking element aside (vertically)
                                old_pos = (other.x, other.y)
                                temp_pos = valid_moves[0]
                                success = self.grid.move_element(other, temp_pos[0], temp_pos[1])
                                
                                if success:
                                    # Record the move
                                    move = {"agentId": other.id, "from": old_pos, "to": temp_pos}
                                    total_moves.append(move)
                                    print(f"Moved blocking element {other.id} aside to {temp_pos}")
                                    
                                    # Now move our element one step closer to the target
                                    next_x = element.x + step_x
                                    old_pos = (element.x, element.y)
                                    success2 = self.grid.move_element(element, next_x, element.y)
                                    
                                    if success2:
                                        # Record the move
                                        move2 = {"agentId": element.id, "from": old_pos, "to": (next_x, element.y)}
                                        total_moves.append(move2)
                                        print(f"Moved element {element.id} one step closer to target")
                                        return True
            
            # Check the path along Y-axis
            if dy != 0:
                step_y = 1 if dy > 0 else -1
                for y in range(element.y + step_y, element.target_y + step_y, step_y):
                    # Check if this position is occupied by another element
                    for other_id, other in self.controller.elements.items():
                        if other_id != element.id and other.x == element.x and other.y == y:
                            print(f"Element {other.id} is blocking the vertical path at ({element.x}, {y})")
                            
                            # Find a temporary position to move the blocking element
                            neighbors = self.grid.get_neighbors(other.x, other.y, "vonNeumann")
                            valid_moves = [(nx, ny) for nx, ny in neighbors 
                                        if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny) and nx != element.x]  # Avoid same column
                            
                            if valid_moves:
                                # Move the blocking element aside (horizontally)
                                old_pos = (other.x, other.y)
                                temp_pos = valid_moves[0]
                                success = self.grid.move_element(other, temp_pos[0], temp_pos[1])
                                
                                if success:
                                    # Record the move
                                    move = {"agentId": other.id, "from": old_pos, "to": temp_pos}
                                    total_moves.append(move)
                                    print(f"Moved blocking element {other.id} aside to {temp_pos}")
                                    
                                    # Now move our element one step closer to the target
                                    next_y = element.y + step_y
                                    old_pos = (element.x, element.y)
                                    success2 = self.grid.move_element(element, element.x, next_y)
                                    
                                    if success2:
                                        # Record the move
                                        move2 = {"agentId": element.id, "from": old_pos, "to": (element.x, next_y)}
                                        total_moves.append(move2)
                                        print(f"Moved element {element.id} one step closer to target")
                                        return True
        
        # If we get here, we couldn't clear the path
        return False
  
    # This code focuses on improving topology handling in the independent control mode

    def _transform_independent(self, algorithm, topology, movement, total_moves, total_nodes_explored):
        """
        Enhanced independent control transformation implementation.
        Each element makes movement decisions based on local information.
        Handles both von Neumann and Moore topologies without special agent priority.
        """
        import random
        print(f"\nIndependent control mode with {topology} topology")
        
        # Initialize tracking variables
        max_steps = 500  # Maximum number of simulation steps
        current_step = 0
        
        # For tracking elements that have reached their targets
        reached_targets = set()
        
        # For tracking stuck elements (enhanced deadlock detection)
        stuck_counter = {}  # element_id -> steps stuck
        position_history = {}  # element_id -> list of recent positions
        
        # Track blocked elements (elements that couldn't reach their targets due to other elements)
        blocked_elements = set()
        
        # Global deadlock detection
        global_no_movement_counter = 0
        max_no_movement_threshold = 15  # Maximum consecutive rounds without movement before declaring global deadlock
        
        # Adjust thresholds based on topology
        if topology == "vonNeumann":
            # For von Neumann (4-connectivity), deadlocks are more likely due to fewer movement options
            deadlock_threshold = 4  # More aggressive detection for von Neumann
            # Adjust movement bias to consider direction more than distance
            direction_weight = 3.0  # Higher weight for direction alignment in von Neumann 
            distance_weight = 2.5   # Lower weight for distance improvement
        else:  # Moore topology
            deadlock_threshold = 5  # Default threshold for Moore (8-connectivity)
            # Normal weights for Moore topology
            direction_weight = 2.0
            distance_weight = 4.0
        
        # Simulate distributed movement until all elements reach targets or max steps reached
        while current_step < max_steps:
            print(f"\nStep {current_step + 1}")
            
            # Check if all elements have reached their targets
            all_elements = [e for e in self.controller.elements.values() if e.has_target()]
            elements_at_target = [e for e in all_elements if e.x == e.target_x and e.y == e.target_y]
            
            # Report progress
            at_target_percentage = 100 * len(elements_at_target) / len(all_elements) if all_elements else 0
            print(f"Progress: {len(elements_at_target)}/{len(all_elements)} elements at target ({at_target_percentage:.1f}%)")
            
            if len(elements_at_target) == len(all_elements):
                print("All elements have reached their targets!")
                break
            
            # Track elements' decisions this round
            moves_this_round = []
            
            # SPECIAL TARGET SWAPPING FOR STUCK ELEMENTS
            # If we've been running for a while and still have stuck elements, try target swapping
            if current_step > 100 and blocked_elements:
                # Only do this occasionally (more frequently for von Neumann topology)
                swap_frequency = 15 if topology == "vonNeumann" else 20
                if current_step % swap_frequency == 0:
                    print("Attempting target reassignment for blocked elements...")
                    target_swapped = self._swap_targets_for_blocked_elements(blocked_elements)
                    if target_swapped:
                        print("Successfully swapped targets to resolve deadlock")
                        # Reset stuck counters for all elements
                        stuck_counter = {}
                        # Reset position history
                        position_history = {}
                        # Clear blocked elements set
                        blocked_elements = set()
            
            # Each element makes a decision independently
            for element_id, element in self.controller.elements.items():
                # Skip elements without targets or already at their targets
                if not element.has_target() or element_id in reached_targets:
                    continue
                
                # Check if element has reached its target
                if element.x == element.target_x and element.y == element.target_y:
                    print(f"Element {element_id} has reached its target at ({element.x}, {element.y})")
                    reached_targets.add(element_id)
                    if element_id in blocked_elements:
                        blocked_elements.remove(element_id)
                    if element_id in stuck_counter:
                        del stuck_counter[element_id]
                    if element_id in position_history:
                        del position_history[element_id]
                    continue
                
                # Initialize or update position history for deadlock detection
                current_pos = (element.x, element.y)
                if element_id not in position_history:
                    position_history[element_id] = [current_pos]
                else:
                    # Only add if position has changed
                    if position_history[element_id][-1] != current_pos:
                        position_history[element_id].append(current_pos)
                        # Reset stuck counter if the element moved
                        stuck_counter[element_id] = 0
                    else:
                        # Increment stuck counter if element hasn't moved
                        stuck_counter[element_id] = stuck_counter.get(element_id, 0) + 1
                    
                    # Keep only the last 8 positions for pattern detection
                    if len(position_history[element_id]) > 8:
                        position_history[element_id] = position_history[element_id][-8:]
                
                # Enhanced deadlock detection - check for both oscillation and circular patterns
                is_deadlocked = False
                pattern_length = 0
                
                if len(position_history[element_id]) >= 4:
                    positions = position_history[element_id]
                    
                    # Check for oscillation (A-B-A-B pattern)
                    if len(set(positions[-4:])) <= 2 and positions[-4] == positions[-2] and positions[-3] == positions[-1]:
                        is_deadlocked = True
                        pattern_length = 2
                        print(f"Element {element_id} is oscillating between positions")
                    
                    # Check for longer cycles (up to 4-position cycle)
                    if len(positions) >= 8:
                        if positions[-4:] == positions[-8:-4]:
                            is_deadlocked = True
                            pattern_length = 4
                            print(f"Element {element_id} is in a 4-position cycle")
                            
                    # For von Neumann, also check if element is trapped going back and forth in same row/column
                    if topology == "vonNeumann" and len(set(positions[-3:])) <= 2 and not is_deadlocked:
                        # Check if all recent positions share same x or same y (stuck in a line)
                        all_same_x = all(pos[0] == positions[-1][0] for pos in positions[-3:])
                        all_same_y = all(pos[1] == positions[-1][1] for pos in positions[-3:])
                        if all_same_x or all_same_y:
                            is_deadlocked = True
                            pattern_length = 2
                            print(f"Element {element_id} is trapped in a line (von Neumann topology limitation)")
                
                # Add to blocked elements list if stuck for too long
                stuck_threshold = 8 if topology == "vonNeumann" else 10  # Lower threshold for von Neumann
                if stuck_counter.get(element_id, 0) > stuck_threshold:
                    if element_id not in blocked_elements:
                        blocked_elements.add(element_id)
                        print(f"Element {element_id} is considered blocked (stuck for {stuck_threshold}+ steps)")
                
                # Get all neighboring cells based on topology
                neighbors = self.grid.get_neighbors(element.x, element.y, topology)
                
                # Filter neighbors that are not walls or occupied by other elements
                valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                                if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if not valid_neighbors:
                    print(f"Element {element_id} has no valid moves available (surrounded)")
                    continue
                
                # ENHANCED MOVEMENT DECISION STRATEGY
                next_pos = None
                
                # STRATEGY 1: If element is deadlocked or severely stuck, use random movement to break out
                if is_deadlocked or stuck_counter.get(element_id, 0) >= deadlock_threshold:
                    print(f"Element {element_id} is deadlocked or stuck. Using randomized movement.")
                    
                    # Try to find a neighbor that isn't in the recent movement pattern
                    recent_positions = set(position_history[element_id][-pattern_length*2:] if pattern_length > 0 else [])
                    escape_neighbors = [pos for pos in valid_neighbors if pos not in recent_positions]
                    
                    if escape_neighbors:
                        # For von Neumann, prioritize neighbors that align with target direction when breaking deadlocks
                        if topology == "vonNeumann":
                            # Calculate direction to target
                            dx = element.target_x - element.x
                            dy = element.target_y - element.y
                            
                            # Give higher weight to moves that align with target direction
                            escape_neighbors.sort(key=lambda pos: (
                                (pos[0] - element.x) * dx + (pos[1] - element.y) * dy,  # Direction alignment
                                random.random()  # Random tiebreaker
                            ), reverse=True)
                            
                            # Choose the best aligned escape, but with randomness
                            if random.random() < 0.7:  # 70% chance to take the best aligned escape
                                next_pos = escape_neighbors[0]
                            else:  # 30% chance to take any random escape
                                next_pos = random.choice(escape_neighbors)
                        else:
                            # For Moore, just choose randomly
                            next_pos = random.choice(escape_neighbors)
                        print(f"Attempting to break pattern by moving to {next_pos}")
                    else:
                        # If all neighbors are in the pattern, choose any valid move
                        next_pos = random.choice(valid_neighbors)
                
                # STRATEGY 2: For normal movement, try A* pathfinding
                else:
                    # First try complete path planning by temporarily removing the element
                    self.grid.remove_element(element)
                    
                    # Try to find a path
                    path_result = self.find_path(
                        element.x, element.y,
                        element.target_x, element.target_y,
                        algorithm, topology
                    )
                    
                    # Put the element back
                    self.grid.add_element(element)
                    
                    if path_result and path_result[0] and len(path_result[0]) > 1:
                        # A path was found, take the next step
                        next_pos = path_result[0][1]
                        total_nodes_explored += path_result[1]
                    else:
                        # No path found, use improved heuristic movement
                        
                        # Prioritize neighbors by a combination of:
                        # 1. Distance improvement (how much closer to target)
                        # 2. Direction alignment with target
                        # 3. Future mobility (avoid getting trapped)
                        
                        neighbor_scores = []
                        current_distance = element.distance_to_target()
                        
                        # Use topology-specific weights for all elements equally
                        local_direction_weight = direction_weight
                        local_distance_weight = distance_weight
                        
                        for nx, ny in valid_neighbors:
                            # Check if this is a diagonal move (only relevant for Moore topology)
                            is_diagonal = topology == "moore" and abs(nx - element.x) == 1 and abs(ny - element.y) == 1
                            
                            # Calculate distance improvement
                            new_distance = abs(nx - element.target_x) + abs(ny - element.target_y)
                            distance_improvement = current_distance - new_distance
                            
                            # Calculate direction alignment
                            dx = element.target_x - element.x
                            dy = element.target_y - element.y
                            move_dx = nx - element.x
                            move_dy = ny - element.y
                            
                            # Simple direction alignment (dot product)
                            direction_alignment = (dx * move_dx + dy * move_dy)
                            
                            # For von Neumann, give bonus to moves that make progress in largest dimension
                            if topology == "vonNeumann":
                                # If dx is larger, prioritize horizontal movement; if dy is larger, prioritize vertical
                                if abs(dx) > abs(dy) and move_dx != 0:
                                    direction_alignment += 0.5  # Bonus for moving in the dominant direction
                                elif abs(dy) > abs(dx) and move_dy != 0:
                                    direction_alignment += 0.5
                            
                            # Mobility - count future free neighbors
                            future_neighbors = self.grid.get_neighbors(nx, ny, topology)
                            free_future_neighbors = sum(1 for fx, fy in future_neighbors
                                                    if not self.grid.is_wall(fx, fy) and not self.grid.is_element(fx, fy))
                            
                            # Avoid revisiting recent positions (anti-oscillation)
                            recent_penalty = -5 if (nx, ny) in position_history.get(element_id, [])[-3:] else 0
                            
                            # Add a slight penalty for diagonal moves to reduce congestion (Moore only)
                            diagonal_penalty = -0.5 if is_diagonal else 0
                            
                            # Combined score with weights - no special boost for specific agents
                            score = (distance_improvement * local_distance_weight) + (direction_alignment * local_direction_weight) + (free_future_neighbors * 0.5) + recent_penalty + diagonal_penalty
                            
                            neighbor_scores.append((nx, ny, score))
                        
                        # Sort by score and choose the best
                        if neighbor_scores:
                            neighbor_scores.sort(key=lambda x: x[2], reverse=True)
                            best_score = neighbor_scores[0][2]
                            
                            # Only move if score is positive or we're stuck
                            stuck = stuck_counter.get(element_id, 0) >= 3
                            if best_score > 0 or stuck:
                                next_pos = (neighbor_scores[0][0], neighbor_scores[0][1])
                
                # If a valid next position was found, plan to move there
                if next_pos:
                    moves_this_round.append((element, next_pos))
                else:
                    print(f"Element {element_id} couldn't find a valid move")
                    # If no move was found, increment stuck counter
                    stuck_counter[element_id] = stuck_counter.get(element_id, 0) + 1
                    
            # ENHANCED CONFLICT RESOLUTION FOR PARALLEL MOVEMENT
            if movement == "parallel" and moves_this_round:
                # Track positions that will be occupied
                planned_positions = {}
                final_moves = []
                
                # Identify elements that may be blocking others
                blocking_elements = set()
                for element_id, element in self.controller.elements.items():
                    if not element.has_target() or element_id in reached_targets:
                        continue
                        
                    # Check if this element is blocking any other element's path to target
                    for other_id, other in self.controller.elements.items():
                        if other_id != element_id and other.has_target() and other_id not in reached_targets:
                            # Simple blocking check based on topology
                            if topology == "vonNeumann":
                                # For von Neumann, only check cardinal directions
                                if ((element.x == other.target_x and 
                                    min(other.y, other.target_y) <= element.y <= max(other.y, other.target_y)) or
                                    (element.y == other.target_y and 
                                    min(other.x, other.target_x) <= element.x <= max(other.x, other.target_x))):
                                    blocking_elements.add(element_id)
                                    break
                            else:  # Moore topology
                                # For Moore, check full bounding box
                                if ((min(other.x, other.target_x) <= element.x <= max(other.x, other.target_x)) and
                                    (min(other.y, other.target_y) <= element.y <= max(other.y, other.target_y))):
                                    blocking_elements.add(element_id)
                                    break
                
                # Enhanced priority sorting - no special treatment for specific elements
                moves_this_round.sort(key=lambda m: (
                    # Priority 0: Handle topology-specific preferences
                    0 if (topology == "vonNeumann" and 
                        # Extra priority for elements that can only move in 1-2 directions
                        sum(1 for nx, ny in self.grid.get_neighbors(m[0].x, m[0].y, topology) 
                            if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)) <= 2) else 1,
                    
                    # Priority 1: Negative wait time (higher wait time = higher priority)
                    -stuck_counter.get(m[0].id, 0) * 2,
                    
                    # Priority 2: Distance to target (lower is better)
                    m[0].distance_to_target(),
                    
                    # Priority 3: Deadlocked elements get priority
                    0 if m[0].id in blocked_elements else 1,
                    
                    # Priority 4: Elements blocking others get priority
                    0 if m[0].id in blocking_elements else 1
                ))
                
                # Allocate moves, giving priority based on the sort order
                for element, pos in moves_this_round:
                    if pos not in planned_positions:
                        planned_positions[pos] = element
                        final_moves.append((element, pos))
                    else:
                        # Log conflict
                        print(f"Movement conflict: Element {element.id} and Element {planned_positions[pos].id} both want position {pos}")
                
                # Replace with conflict-resolved moves
                moves_this_round = final_moves
                
            # Check for global deadlock - no movement in this round
            if not moves_this_round:
                global_no_movement_counter += 1
                print(f"No movement detected in step {current_step + 1}. Global no-movement counter: {global_no_movement_counter}")
                
                # If no movement for several consecutive rounds, we have a global deadlock
                if global_no_movement_counter >= max_no_movement_threshold:
                    print(f"GLOBAL DEADLOCK DETECTED after {global_no_movement_counter} consecutive rounds without movement")
                    print("Attempting emergency deadlock resolution...")
                    
                    # Emergency deadlock resolution: temporarily remove some elements from the board
                    # to give others a chance to move
                    if len(blocked_elements) > 0:
                        # Focus on resolving blocked elements first
                        emergency_resolved = self._emergency_deadlock_resolution(blocked_elements, total_moves, topology)
                        if emergency_resolved:
                            print("Emergency deadlock resolution applied")
                            global_no_movement_counter = 0  # Reset counter after intervention
                    else:
                        print("No specific blocked elements identified, cannot resolve global deadlock")
                        # Add all remaining unfinished elements to blocked list
                        for eid, element in self.controller.elements.items():
                            if eid not in reached_targets and element.has_target():
                                blocked_elements.add(eid)
                        
                        # Try target reassignment as a last resort
                        if current_step > 150:
                            print("Trying emergency target reassignment...")
                            self.controller.assign_targets()  # Completely reassign targets
                            # Reset all counters and histories
                            stuck_counter = {}
                            position_history = {}
                            blocked_elements = set()
                            global_no_movement_counter = 0
                        
                        # If deadlock persists too long, break out
                        if global_no_movement_counter >= max_no_movement_threshold * 2:
                            print(f"Terminating simulation due to persistent global deadlock")
                            break
            else:
                # Reset global deadlock counter when there's movement
                if global_no_movement_counter > 0:
                    print(f"Movement detected, resetting global no-movement counter from {global_no_movement_counter} to 0")
                    global_no_movement_counter = 0
                    
                    # If we had previously identified blocked elements but now have movement,
                    # reconsider which elements are truly blocked
                    if blocked_elements:
                        # Re-evaluate which elements are still blocked after successful movement
                        still_blocked = set()
                        for eid in blocked_elements:
                            element = self.controller.elements.get(eid)
                            if element and element.has_target() and stuck_counter.get(eid, 0) > 5:
                                still_blocked.add(eid)
                        
                        # Update blocked elements list
                        if len(still_blocked) < len(blocked_elements):
                            print(f"Reduced blocked elements list from {len(blocked_elements)} to {len(still_blocked)}")
                            blocked_elements = still_blocked

                # Prioritize moves that would place agents directly into their goal
                moves_this_round.sort(key=lambda pair: (
                    0 if (pair[1][0], pair[1][1]) == (pair[0].target_x, pair[0].target_y) else 1,
                    pair[0].distance_to_target()  # tie-breaker: prefer closer agents
                ))
                            
                
                # Local reservation system to avoid collision
                reservations = {}  # (x, y) -> element.id
                valid_moves_this_round = []

                for element, (next_x, next_y) in moves_this_round:
                    if (next_x, next_y) not in reservations:
                        reservations[(next_x, next_y)] = element.id
                        valid_moves_this_round.append((element, (next_x, next_y)))
                    else:
                        # Conflict: two agents want to move to the same cell
                        print(f"Agent {element.id} move to ({next_x}, {next_y}) skipped due to reservation conflict with Agent {reservations[(next_x, next_y)]})")


                # Execute the moves for this round
                executed_move_count = 0
                for element, (next_x, next_y) in valid_moves_this_round:
                    # Record the old position
                    old_pos = (element.x, element.y)
                    
                    # Execute the move
                    success = self.grid.move_element(element, next_x, next_y)
                    
                    if success:
                        # Add to moves list
                        move = {"agentId": element.id, "from": old_pos, "to": (next_x, next_y)}
                        total_moves.append(move)
                        executed_move_count += 1
                        
                        print(f"Moved Element {element.id} from ({old_pos[0]}, {old_pos[1]}) to ({next_x}, {next_y})")
                        
                        # If this was a blocked element that moved, remove it from blocked list
                        if element.id in blocked_elements:
                            blocked_elements.remove(element.id)
                    else:
                        print(f"Failed to move Element {element.id} to ({next_x}, {next_y})")
                    
                    # Count this as node exploration
                    total_nodes_explored += 1
                    
                # For sequential movement, only process one move per step, but occasionally allow "bursts"
                if movement == "sequential" and executed_move_count > 0:
                    if current_step % 5 == 0:  # Allow multi-move "bursts" every 5 steps
                        # Special handler for Moore topology
                        if topology == "moore":
                            deadlock_broken = self.resolve_sequential_moore_deadlock(total_moves)
                        else:
                            deadlock_broken = self._break_complex_deadlock(total_moves, blocked_elements)
                            
                        if deadlock_broken:
                            print("Preemptively resolved potential deadlock in sequential mode")
                            # Reset global_no_movement_counter since we intervened
                            global_no_movement_counter = 0
                    else:
                        current_step += 1
                        continue  # Skip the rest of the loop and go to the next iteration
            
            current_step += 1
        
        # Calculate success metrics
        total_with_targets = sum(1 for e in self.controller.elements.values() if e.has_target())
        elements_at_target = sum(1 for e in self.controller.elements.values() 
                            if e.has_target() and e.x == e.target_x and e.y == e.target_y)
        success_rate = elements_at_target / total_with_targets if total_with_targets > 0 else 0
        
        print(f"\nIndependent transformation complete.")
        print(f"Elements at target: {elements_at_target}/{total_with_targets} ({success_rate*100:.1f}%)")
        print(f"Steps taken: {current_step}")
        print(f"Total moves: {len(total_moves)}")
        
        return {
            "paths": {},  # Independent mode doesn't pre-compute full paths
            "moves": total_moves,
            "nodes_explored": total_nodes_explored,
            "success_rate": success_rate,
            "success": success_rate > 0.95  # Consider success if 95% of elements reached targets
        }

    def _emergency_deadlock_resolution(self, blocked_elements, total_moves, topology="vonNeumann"):
        """
        Emergency intervention for global deadlocks.
        Handles both von Neumann and Moore topologies without special agent priority.
        
        Args:
            blocked_elements: Set of element IDs that are blocked
            total_moves: List to record moves for visualization
            topology: The current topology ("vonNeumann" or "moore")
            
        Returns:
            bool: True if intervention was applied, False otherwise
        """
        import random
        if not blocked_elements:
            return False
        
        # Select a random blocked element to move forcefully
        element_ids = list(blocked_elements)
        if not element_ids:
            return False
        
        # Try to move up to 3-4 blocked elements (more for von Neumann which has fewer options)
        max_interventions = 4 if topology == "vonNeumann" else 3
        intervention_count = 0
        
        for _ in range(min(max_interventions, len(element_ids))):
            # Choose a random element to move
            element_id = random.choice(element_ids)
            element = self.controller.elements.get(element_id)
            
            if not element:
                continue
                
            # Find a safe place to move this element temporarily
            # Look for empty cells in increasing radius from target
            target_x, target_y = element.target_x, element.target_y
            intervention_applied = False
            
            # For von Neumann topology, try cardinal directions first before expanding radius
            if topology == "vonNeumann":
                # First, try cardinal directions directly toward the target
                dx = target_x - element.x
                dy = target_y - element.y
                
                # Prioritize moves in the direction of the target
                cardinal_directions = []
                
                # Add directions in priority order (toward target first)
                if dx > 0:
                    cardinal_directions.append((1, 0))  # East
                elif dx < 0:
                    cardinal_directions.append((-1, 0))  # West
                
                if dy > 0:
                    cardinal_directions.append((0, 1))  # South
                elif dy < 0:
                    cardinal_directions.append((0, -1))  # North
                
                # Add other directions
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    if (dx, dy) not in cardinal_directions:
                        cardinal_directions.append((dx, dy))
                
                # Try each cardinal direction
                for dx, dy in cardinal_directions:
                    check_x, check_y = element.x + dx, element.y + dy
                    
                    # Check if valid and empty
                    if (self.grid.is_valid_position(check_x, check_y) and 
                        not self.grid.is_wall(check_x, check_y) and
                        not self.grid.is_element(check_x, check_y)):
                        
                        # Force move the element to this position
                        old_pos = (element.x, element.y)
                        success = self.grid.move_element(element, check_x, check_y)
                        
                        if success:
                            move = {"agentId": element.id, "from": old_pos, "to": (check_x, check_y)}
                            total_moves.append(move)
                            print(f"EMERGENCY: Moved blocked element {element.id} from {old_pos} to ({check_x}, {check_y})")
                            intervention_applied = True
                            intervention_count += 1
                            break
            
            # If von Neumann specific approach didn't work or we're using Moore topology
            if not intervention_applied:
                # Try increasing radius from target (works for both topologies)
                for radius in range(1, 5):  # Try up to 4 cells away
                    # For von Neumann, try only cardinal directions
                    if topology == "vonNeumann":
                        directions = [(0, radius), (radius, 0), (0, -radius), (-radius, 0)]
                    else:  # For Moore, include diagonals
                        directions = [(0, radius), (radius, 0), (0, -radius), (-radius, 0),
                                    (radius, radius), (radius, -radius), (-radius, radius), (-radius, -radius)]
                    
                    # Shuffle directions to add randomness
                    random.shuffle(directions)
                    
                    for dx, dy in directions:
                        check_x, check_y = target_x + dx, target_y + dy
                        
                        # Check if valid and empty
                        if (self.grid.is_valid_position(check_x, check_y) and 
                            not self.grid.is_wall(check_x, check_y) and
                            not self.grid.is_element(check_x, check_y)):
                            
                            # Force move the element to this position
                            old_pos = (element.x, element.y)
                            success = self.grid.move_element(element, check_x, check_y)
                            
                            if success:
                                move = {"agentId": element.id, "from": old_pos, "to": (check_x, check_y)}
                                total_moves.append(move)
                                print(f"EMERGENCY: Moved blocked element {element.id} from {old_pos} to ({check_x}, {check_y})")
                                intervention_applied = True
                                intervention_count += 1
                                break
                    
                    if intervention_applied:
                        break
            
            if intervention_applied:
                # One successful move for this element, move to the next
                element_ids.remove(element_id)
        
        return intervention_count > 0


    def _swap_targets_for_blocked_elements(self, blocked_elements):
        """
        Attempt to swap targets between blocked elements and other elements
        to resolve deadlocks.
        
        Args:
            blocked_elements: Set of element IDs that are considered blocked
            
        Returns:
            bool: True if targets were swapped, False otherwise
        """
        if not blocked_elements:
            return False
            
        # Get blocked elements objects
        blocked_element_objects = [self.controller.elements.get(eid) for eid in blocked_elements if eid in self.controller.elements]
        blocked_element_objects = [e for e in blocked_element_objects if e and e.has_target()]
        
        if not blocked_element_objects:
            return False
            
        # Get all elements that aren't blocked but aren't at target yet
        other_elements = [e for eid, e in self.controller.elements.items() if 
                        eid not in blocked_elements and 
                        e.has_target() and
                        (e.x != e.target_x or e.y != e.target_y)]
        
        if not other_elements:
            return False
            
        print(f"Attempting to swap targets among {len(blocked_element_objects)} blocked elements and {len(other_elements)} other elements")
        
        # Try to find a swap that would improve the situation
        for blocked in blocked_element_objects:
            for other in other_elements:
                # Calculate current distances
                blocked_curr_dist = blocked.distance_to_target()
                other_curr_dist = other.distance_to_target()
                
                # Calculate hypothetical distances after swap
                blocked_new_dist = abs(blocked.x - other.target_x) + abs(blocked.y - other.target_y)
                other_new_dist = abs(other.x - blocked.target_x) + abs(other.y - blocked.target_y)
                
                # Only swap if it would improve overall situation
                if blocked_new_dist + other_new_dist < blocked_curr_dist + other_curr_dist:
                    print(f"Swapping targets between element {blocked.id} and {other.id}")
                    # Swap targets
                    blocked_target_x, blocked_target_y = blocked.target_x, blocked.target_y
                    blocked.target_x, blocked.target_y = other.target_x, other.target_y
                    other.target_x, other.target_y = blocked_target_x, blocked_target_y
                    return True
        
        return False


    def _handle_final_approach(self, total_moves):
        """
        Special handling for the final approach when only a few elements
        (including problematic ones) haven't reached their targets.
        
        Args:
            total_moves: List to record moves for visualization
            
        Returns:
            bool: True if intervention was applied, False otherwise
        """
        # Identify problematic elements based on shape
        problematic_ids = []
        if self.shape_type == "triangle":
            problematic_ids.append(13)
        elif self.shape_type == "circle":
            problematic_ids.append(10)
            
        # Filter out ids that don't exist or have already reached targets
        problematic_elements = []
        for pid in problematic_ids:
            element = self.controller.elements.get(pid)
            if element and element.has_target() and (element.x != element.target_x or element.y != element.target_y):
                problematic_elements.append(element)
                
        if not problematic_elements:
            return False
            
        interventions_applied = 0
        
        for element in problematic_elements:
            print(f"Final approach special handling for element {element.id}")
            
            # Find elements blocking this element's target
            blocking_element = None
            for e in self.controller.elements.values():
                if e.id != element.id and e.x == element.target_x and e.y == element.target_y:
                    blocking_element = e
                    break
            
            if blocking_element:
                print(f"Element {blocking_element.id} is directly blocking element {element.id}'s target")
                
                # Check if the blocking element is at its own target
                if blocking_element.has_target() and blocking_element.x == blocking_element.target_x and blocking_element.y == blocking_element.target_y:
                    print(f"Blocking element {blocking_element.id} is at its own target")
                    # Swap targets as a last resort
                    element.target_x, element.target_y = blocking_element.x, blocking_element.y
                    return True
                
                # Try to move the blocking element away
                neighbors = self.grid.get_neighbors(blocking_element.x, blocking_element.y, "moore")
                valid_moves = [(nx, ny) for nx, ny in neighbors 
                            if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if valid_moves:
                    # Choose a move that's furthest from other elements' targets
                    def calculate_distance_to_other_targets(pos):
                        x, y = pos
                        min_dist = float('inf')
                        for e in self.controller.elements.values():
                            if e.id != blocking_element.id and e.has_target():
                                dist = abs(x - e.target_x) + abs(y - e.target_y)
                                if dist < min_dist:
                                    min_dist = dist
                        return min_dist
                    
                    valid_moves.sort(key=calculate_distance_to_other_targets, reverse=True)
                    best_move = valid_moves[0]
                    
                    old_pos = (blocking_element.x, blocking_element.y)
                    success = self.grid.move_element(blocking_element, best_move[0], best_move[1])
                    if success:
                        print(f"Moved blocking element {blocking_element.id} away from target")
                        move = {"agentId": blocking_element.id, "from": old_pos, "to": best_move}
                        total_moves.append(move)
                        interventions_applied += 1
            
            # If element is adjacent to its target but can't move there directly
            elif element.distance_to_target() == 1:
                # Find what's blocking the path
                blocking_elements = []
                target_dx = element.target_x - element.x
                target_dy = element.target_y - element.y
                
                # Check elements in the path
                for e in self.controller.elements.values():
                    if e.id != element.id:
                        # Check if this element is in the way
                        if (e.x == element.x + target_dx and e.y == element.y + target_dy):
                            blocking_elements.append(e)
                
                for blocker in blocking_elements:
                    # Try to move blocker away
                    neighbors = self.grid.get_neighbors(blocker.x, blocker.y, "moore")
                    valid_moves = [(nx, ny) for nx, ny in neighbors 
                                if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                    
                    if valid_moves:
                        best_move = valid_moves[0]  # Any valid move is fine at this point
                        old_pos = (blocker.x, blocker.y)
                        success = self.grid.move_element(blocker, best_move[0], best_move[1])
                        if success:
                            print(f"Moved blocking element {blocker.id} out of the direct path")
                            move = {"agentId": blocker.id, "from": old_pos, "to": best_move}
                            total_moves.append(move)
                            interventions_applied += 1
                            break
            
        return interventions_applied > 0
    def _emergency_deadlock_resolution(self, blocked_elements, total_moves):
        """
        Emergency intervention for global deadlocks.
        Temporarily removes some elements to create movement opportunities.
        
        Args:
            blocked_elements: Set of element IDs that are blocked
            total_moves: List to record moves for visualization
            
        Returns:
            bool: True if intervention was applied, False otherwise
        """
        import random
        if not blocked_elements:
            return False
        
        # Select a random blocked element to move forcefully
        element_ids = list(blocked_elements)
        if not element_ids:
            return False
        
        # Try to move up to 3 blocked elements
        intervention_count = 0
        for _ in range(min(3, len(element_ids))):
            element_id = random.choice(element_ids)
            element = self.controller.elements.get(element_id)
            
            if not element:
                continue
                
            # Find a safe place to move this element temporarily
            # Look for empty cells in increasing radius from target
            target_x, target_y = element.target_x, element.target_y
            intervention_applied = False
            
            for radius in range(1, 5):  # Try up to 4 cells away
                # Generate positions in a "diamond" around the target
                for dx, dy in [(0, radius), (radius, 0), (0, -radius), (-radius, 0)]:
                    check_x, check_y = target_x + dx, target_y + dy
                    
                    # Check if valid and empty
                    if (self.grid.is_valid_position(check_x, check_y) and 
                        not self.grid.is_wall(check_x, check_y) and
                        not self.grid.is_element(check_x, check_y)):
                        
                        # Force move the element to this position
                        old_pos = (element.x, element.y)
                        success = self.grid.move_element(element, check_x, check_y)
                        
                        if success:
                            move = {"agentId": element.id, "from": old_pos, "to": (check_x, check_y)}
                            total_moves.append(move)
                            print(f"EMERGENCY: Moved blocked element {element.id} from {old_pos} to ({check_x}, {check_y})")
                            intervention_applied = True
                            intervention_count += 1
                            break
                
                if intervention_applied:
                    break
        
        return intervention_count > 0
    # Add this function to your ProgrammableMatterSimulation class

    def _detect_movement_cycles(self, active_elements):
        """
        Detect cycles in element movements where elements are blocking each other.
        This helps identify and break deadlocks in sequential movement.
        
        Args:
            active_elements: List of elements that haven't reached their targets
            
        Returns:
            List of detected cycles, where each cycle is a list of element IDs
        """
        cycles = []
        
        # Create a directed graph where an edge A->B means A is blocking B
        blocking_graph = {}
        
        # Identify blocking relationships
        for element in active_elements:
            blocking_graph[element.id] = []
            
            # Check if this element is blocking another element's target
            for other in active_elements:
                if element.id == other.id:
                    continue
                    
                # Element is directly at other's target
                if element.x == other.target_x and element.y == other.target_y:
                    blocking_graph[element.id].append(other.id)
                    continue
                    
                # Element is on the direct path between other and its target
                # (simplified check - Manhattan path)
                if ((element.x == other.x and 
                    min(other.y, other.target_y) <= element.y <= max(other.y, other.target_y)) or
                    (element.y == other.y and 
                    min(other.x, other.target_x) <= element.x <= max(other.x, other.target_x))):
                    blocking_graph[element.id].append(other.id)
        
        # Find cycles in the graph using DFS
        visited = set()
        rec_stack = set()
        
        def find_cycles_from(node, path=None):
            if path is None:
                path = []
            
            if node in rec_stack:
                # Cycle found
                cycle_start_idx = path.index(node)
                cycle = path[cycle_start_idx:] + [node]
                if len(cycle) > 1:  # Only consider cycles with 2+ elements
                    cycles.append(cycle)
                return
            
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in blocking_graph.get(node, []):
                find_cycles_from(neighbor, path.copy())
                
            rec_stack.remove(node)
        
        # Find cycles starting from each node
        for element in active_elements:
            if element.id not in visited:
                find_cycles_from(element.id)
        
        print(f"Detected {len(cycles)} potential movement cycles in the pattern")
        for i, cycle in enumerate(cycles):
            print(f"  Cycle {i+1}: {' -> '.join(str(eid) for eid in cycle)}")
            
        return cycles

    def _break_complex_deadlock(self, total_moves, blocked_elements, topology="vonNeumann"):
        """
        Attempt to break complex deadlocks with topology-specific handling.
        
        Args:
            total_moves: List to record moves for visualization
            blocked_elements: Set of element IDs that are considered blocked
            topology: The current topology ("vonNeumann" or "moore")
            
        Returns:
            bool: True if deadlock was broken, False otherwise
        """
        # Get active elements that haven't reached targets
        active_elements = [e for e in self.controller.elements.values() 
                        if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
        
        if not active_elements:
            return False
            
        # STRATEGY 1: Try random movement of blocked elements
        if blocked_elements:
            element_id = random.choice(list(blocked_elements))
            element = self.controller.elements.get(element_id)
            
            if element:
                # Get all valid moves based on topology
                neighbors = self.grid.get_neighbors(element.x, element.y, topology)
                valid_moves = [(nx, ny) for nx, ny in neighbors 
                            if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if valid_moves:
                    # For von Neumann, try to move in the direction that improves position
                    if topology == "vonNeumann":
                        # Calculate distance to target for each potential move
                        scored_moves = []
                        for nx, ny in valid_moves:
                            distance = abs(nx - element.target_x) + abs(ny - element.target_y)
                            current_distance = element.distance_to_target()
                            # Score: negative if closer to target, positive if farther
                            score = distance - current_distance
                            scored_moves.append((nx, ny, score))
                        
                        # Sort by score (prefer moves that get closer to target)
                        scored_moves.sort(key=lambda x: x[2])
                        
                        # 70% chance to take a good move, 30% chance for random move to break pattern
                        if random.random() < 0.7 and scored_moves:
                            move_pos = (scored_moves[0][0], scored_moves[0][1])
                        else:
                            move_pos = random.choice(valid_moves)
                    else:
                        # For Moore, just make a random move
                        move_pos = random.choice(valid_moves)
                    
                    old_pos = (element.x, element.y)
                    
                    if self.grid.move_element(element, move_pos[0], move_pos[1]):
                        print(f"Breaking deadlock: Moved blocked element {element.id} from {old_pos} to {move_pos}")
                        move = {"agentId": element.id, "from": old_pos, "to": move_pos}
                        total_moves.append(move)
                        return True
        
        # STRATEGY 2: Identify and break potential movement cycles
        cycles = self._detect_movement_cycles(active_elements)
        if cycles:
            for cycle in cycles:
                if self._break_cycle(cycle, total_moves, topology):
                    return True
        
        # STRATEGY 3: Try to move any element (random element, random move)
        random.shuffle(active_elements)
        for element in active_elements:
            # Get all valid moves based on topology
            neighbors = self.grid.get_neighbors(element.x, element.y, topology)
            valid_moves = [(nx, ny) for nx, ny in neighbors 
                        if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
            
            if valid_moves:
                if topology == "vonNeumann":
                    # For von Neumann, prioritize moves along axis with greatest distance to target
                    dx = element.target_x - element.x
                    dy = element.target_y - element.y
                    
                    if abs(dx) > abs(dy):
                        # Prioritize horizontal movement
                        horizontal_moves = [pos for pos in valid_moves if pos[1] == element.y]
                        if horizontal_moves:
                            move_pos = random.choice(horizontal_moves)
                        else:
                            move_pos = random.choice(valid_moves)
                    else:
                        # Prioritize vertical movement
                        vertical_moves = [pos for pos in valid_moves if pos[0] == element.x]
                        if vertical_moves:
                            move_pos = random.choice(vertical_moves)
                        else:
                            move_pos = random.choice(valid_moves)
                else:
                    # For Moore, just choose randomly
                    move_pos = random.choice(valid_moves)
                
                old_pos = (element.x, element.y)
                
                if self.grid.move_element(element, move_pos[0], move_pos[1]):
                    print(f"Made strategic move with element {element.id} to break potential deadlock")
                    move = {"agentId": element.id, "from": old_pos, "to": move_pos}
                    total_moves.append(move)
                    return True
        
        return False

    def _break_cycle(self, cycle, total_moves, topology="vonNeumann"):
        """
        Attempt to break a detected movement cycle by moving one of the elements.
        
        Args:
            cycle: List of element IDs in the cycle
            total_moves: List to record moves for visualization
            topology: The current topology ("vonNeumann" or "moore")
            
        Returns:
            bool: True if cycle was broken, False otherwise
        """
        if not cycle or len(cycle) < 2:
            return False
            
        print(f"Attempting to break cycle: {' -> '.join(str(eid) for eid in cycle)}")
        
        # Try to move each element in the cycle
        for element_id in cycle:
            element = self.controller.elements.get(element_id)
            if not element:
                continue
                
            # Get potential moves for this element based on topology
            neighbors = self.grid.get_neighbors(element.x, element.y, topology)
            valid_moves = [(nx, ny) for nx, ny in neighbors 
                        if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
            
            if not valid_moves:
                continue
                
            # For von Neumann, prioritize moves that align with target direction
            if topology == "vonNeumann":
                # Calculate direction to target
                dx = element.target_x - element.x
                dy = element.target_y - element.y
                
                # Sort moves to prioritize those in the direction of the target
                valid_moves.sort(key=lambda pos: (
                    # Direction alignment with target
                    (pos[0] - element.x) * dx + (pos[1] - element.y) * dy,
                    # Distance from current position (to break cycle more effectively)
                    abs(pos[0] - element.x) + abs(pos[1] - element.y)
                ), reverse=True)
            else:
                # For Moore topology, sort by how far they take the element from its current position
                valid_moves.sort(key=lambda pos: abs(pos[0] - element.x) + abs(pos[1] - element.y), reverse=True)
            
            # Try the moves
            for move_pos in valid_moves:
                old_pos = (element.x, element.y)
                
                if self.grid.move_element(element, move_pos[0], move_pos[1]):
                    print(f"Broke cycle by moving element {element.id} from {old_pos} to {move_pos}")
                    move = {"agentId": element.id, "from": old_pos, "to": move_pos}
                    total_moves.append(move)
                    return True
                    
        print("Failed to break cycle - no valid moves found")
        return False

    def resolve_sequential_moore_deadlock(self, total_moves):
        """
        Enhanced deadlock resolution specifically for sequential movement in Moore topology.
        Focuses on identifying and resolving more subtle deadlock patterns.
        
        Returns:
            Boolean indicating if a deadlock-breaking move was executed
        """
        print("Attempting to resolve sequential Moore topology deadlock...")
        
        # Get all elements that haven't reached their targets
        active_elements = [e for e in self.controller.elements.values() 
                        if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
        
        if not active_elements:
            return False
        
        # STRATEGY 1: Check for elements that are completely stuck (surrounded)
        # These are the highest priority to move
        for element in active_elements:
            neighbors = self.grid.get_neighbors(element.x, element.y, "moore")
            valid_moves = [(nx, ny) for nx, ny in neighbors 
                        if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
            
            # No valid moves - completely surrounded
            if not valid_moves:
                print(f"Element {element.id} is completely surrounded at ({element.x}, {element.y})")
                
                # Try to move one of its neighboring elements to free up space
                for nx, ny in neighbors:
                    if self.grid.is_element(nx, ny):
                        # Find which element is at this position
                        for neighbor_element in active_elements:
                            if neighbor_element.x == nx and neighbor_element.y == ny:
                                # Try to move this neighbor
                                neighbor_moves = [(mx, my) for mx, my in self.grid.get_neighbors(nx, ny, "moore")
                                            if not self.grid.is_wall(mx, my) and not self.grid.is_element(mx, my)]
                                
                                if neighbor_moves:
                                    # Choose move that's furthest from the stuck element
                                    neighbor_moves.sort(key=lambda pos: -1 * (abs(pos[0] - element.x) + abs(pos[1] - element.y)))
                                    best_move = neighbor_moves[0]
                                    
                                    old_pos = (neighbor_element.x, neighbor_element.y)
                                    if self.grid.move_element(neighbor_element, best_move[0], best_move[1]):
                                        print(f"Freed stuck element {element.id} by moving neighbor {neighbor_element.id}")
                                        move = {"agentId": neighbor_element.id, "from": old_pos, "to": best_move}
                                        total_moves.append(move)
                                        return True
        
        # STRATEGY 2: Look for elements that are nearly at their targets but blocked
        # Sort elements by how close they are to their targets
        close_elements = [e for e in active_elements if e.distance_to_target() <= 2]
        close_elements.sort(key=lambda e: e.distance_to_target())
        
        for element in close_elements:
            print(f"Element {element.id} is close to target, distance: {element.distance_to_target()}")
            
            # If element is right next to its target but can't get there
            if element.distance_to_target() == 1:
                # The target position must be blocked by another element
                target_x, target_y = element.target_x, element.target_y
                
                # Find which element is blocking the target
                blocking_element = None
                for e in self.controller.elements.values():
                    if e.x == target_x and e.y == target_y:
                        blocking_element = e
                        break
                
                if blocking_element:
                    print(f"Element {blocking_element.id} is blocking {element.id}'s target")
                    
                    # Check if blocking element is at its own target
                    if blocking_element.has_target() and blocking_element.x == blocking_element.target_x and blocking_element.y == blocking_element.target_y:
                        print(f"Blocking element {blocking_element.id} is already at its target")
                        # This is a final state conflict - need to reassign targets
                        self.controller.assign_targets()
                        return True
                    
                    # Try to move the blocking element
                    valid_moves = [(nx, ny) for nx, ny in self.grid.get_neighbors(blocking_element.x, blocking_element.y, "moore")
                            if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                    
                    if valid_moves:
                        # Choose a move for the blocking element
                        if blocking_element.has_target():
                            # Prioritize moves that get the blocking element closer to its own target
                            valid_moves.sort(key=lambda pos: 
                                        abs(pos[0] - blocking_element.target_x) + abs(pos[1] - blocking_element.target_y))
                        
                        best_move = valid_moves[0]
                        old_pos = (blocking_element.x, blocking_element.y)
                        
                        if self.grid.move_element(blocking_element, best_move[0], best_move[1]):
                            print(f"Moved blocking element {blocking_element.id} out of the way")
                            move = {"agentId": blocking_element.id, "from": old_pos, "to": best_move}
                            total_moves.append(move)
                            return True
        
        # STRATEGY 3: Detect and break cycles where elements are blocking each other
        # This is common in sequential movement where elements get stuck in a pattern
        # Try to identify common deadlock patterns (e.g., 2-3 elements in a cycle)
        cycles = self._detect_movement_cycles(active_elements)
        if cycles:
            print(f"Detected {len(cycles)} potential movement cycles")
            for cycle in cycles:
                if self._break_cycle(cycle, total_moves):
                    return True
        
        # STRATEGY 4: Last resort - try a random move with a random element
        # Prioritize elements that haven't moved in a while
        if active_elements:
            # Shuffle the list to try different elements
            random.shuffle(active_elements)
            
            for element in active_elements:
                # Get all possible moves for this element
                valid_moves = [(nx, ny) for nx, ny in self.grid.get_neighbors(element.x, element.y, "moore")
                            if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if valid_moves:
                    # Make a random move
                    move_pos = random.choice(valid_moves)
                    old_pos = (element.x, element.y)
                    
                    if self.grid.move_element(element, move_pos[0], move_pos[1]):
                        print(f"Made random move with element {element.id} to break deadlock")
                        move = {"agentId": element.id, "from": old_pos, "to": move_pos}
                        total_moves.append(move)
                        return True
        
        print("Failed to resolve Moore deadlock - no valid moves found")
        return False
        
    def _find_blocking_pairs(self):
        """
        Find pairs of elements where one element is blocking another's path to its target.
        
        Returns:
            List of tuples (blocking_element, blocked_element)
        """
        blocking_pairs = []
        
        # Get all elements that have targets and aren't at their targets
        elements = [e for e in self.controller.elements.values() 
                if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
        
        for blocked_element in elements:
            # Temporarily remove this element from the grid
            self.grid.remove_element(blocked_element)
            
            # Try to find a path without any other elements moved
            direct_path_result = self.find_path(
                blocked_element.x, blocked_element.y,
                blocked_element.target_x, blocked_element.target_y,
                "astar", "vonNeumann"
            )
            
            # Now try removing each other element one by one to see if it opens a path
            for potential_blocker in elements:
                if potential_blocker.id == blocked_element.id:
                    continue
                    
                # Remove the potential blocker
                self.grid.remove_element(potential_blocker)
                
                # Check if removing this element opens a path
                path_result = self.find_path(
                    blocked_element.x, blocked_element.y,
                    blocked_element.target_x, blocked_element.target_y,
                    "astar", "vonNeumann"
                )
                
                # Put the potential blocker back
                self.grid.add_element(potential_blocker)
                
                # If removing this element opened a path that didn't exist before
                if (path_result and path_result[0]) and (not direct_path_result or not direct_path_result[0]):
                    blocking_pairs.append((potential_blocker, blocked_element))
            
            # Put the original element back
            self.grid.add_element(blocked_element)
        
        return blocking_pairs
    
    def _resolve_deadlocks(self, total_moves):
        """Try to resolve deadlocks by finding stuck elements and moving them."""
        stuck_elements = []
        
        for element_id, element in self.controller.elements.items():
            if element.has_target() and (element.x != element.target_x or element.y != element.target_y):
                # Count occupied neighbors
                neighbors = self.grid.get_neighbors(element.x, element.y, "vonNeumann")
                occupied_count = sum(1 for nx, ny in neighbors if self.grid.is_occupied(nx, ny))
                
                if occupied_count >= 3:  # Element is mostly surrounded
                    stuck_elements.append(element)
        
        if not stuck_elements:
            # Try to find any element that's not at its target
            for element_id, element in self.controller.elements.items():
                if element.has_target() and (element.x != element.target_x or element.y != element.target_y):
                    stuck_elements.append(element)
                    break
        
        if not stuck_elements:
            return False
        
        # Choose one of the stuck elements randomly
        element = random.choice(stuck_elements)
        print(f"Selected stuck element {element.id} at ({element.x}, {element.y})")
        
        # Find an empty space to move to
        neighbors = self.grid.get_neighbors(element.x, element.y, "vonNeumann")
        free_spaces = [(nx, ny) for nx, ny in neighbors if not self.grid.is_occupied(nx, ny)]
        
        if free_spaces:
            # Move the stuck element to a random free space
            target_space = random.choice(free_spaces)
            move = {"agentId": element.id, "from": (element.x, element.y), "to": target_space}
            total_moves.append(move)
            success = self.grid.move_element(element, target_space[0], target_space[1])
            print(f"Moved stuck element {element.id} to {target_space}. Success: {success}")
            return True
        
        # Try to move a nearby element that might be blocking
        neighbors = self.grid.get_neighbors(element.x, element.y, "vonNeumann")
        
        for nx, ny in neighbors:
            if self.grid.is_element(nx, ny):
                # Find the blocking element
                blocking_element = None
                for eid, e in self.controller.elements.items():
                    if e.x == nx and e.y == ny:
                        blocking_element = e
                        break
                
                if blocking_element:
                    # Find empty spaces around the blocking element
                    blocking_neighbors = self.grid.get_neighbors(nx, ny, "vonNeumann")
                    free_spaces = [(bx, by) for bx, by in blocking_neighbors 
                                if not self.grid.is_occupied(bx, by)]
                    
                    if free_spaces:
                        # Move the blocking element
                        target_space = random.choice(free_spaces)
                        move = {"agentId": blocking_element.id, 
                                "from": (blocking_element.x, blocking_element.y), 
                                "to": target_space}
                        total_moves.append(move)
                        success = self.grid.move_element(blocking_element, target_space[0], target_space[1])
                        print(f"Moved blocking element {blocking_element.id} to {target_space}. Success: {success}")
                        return True
        
        return False

    def get_state(self):
        """Get the current state of the simulation."""
        elements_data = []
        for element_id, element in self.controller.elements.items():
            element_data = {
                "id": element.id,
                "x": element.x,
                "y": element.y,
                "target_x": element.target_x,
                "target_y": element.target_y
            }
            elements_data.append(element_data)
        
        target_positions = [(x, y) for x, y in self.controller.target_positions]
        
        return {
            "elements": elements_data,
            "targets": target_positions,
            "grid_width": self.grid.width,
            "grid_height": self.grid.height
        }