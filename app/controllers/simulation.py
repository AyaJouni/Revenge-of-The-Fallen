<<<<<<< HEAD
# app/controllers/simulation.py
import time
import heapq
from app.models.grid import Grid
from app.models.shape import ShapeGenerator
from app.controllers.element_controller import ElementController
from app.algorithms.astar import astar_pathfind
from app.algorithms.bfs import bfs_pathfind
from app.algorithms.greedy import greedy_pathfind

class ProgrammableMatterSimulation:
    """Main simulation class for the programmable matter system."""
    def __init__(self, width=12, height=12):
        self.grid = Grid(width, height)
        self.controller = ElementController(self.grid)
        self.reset()
    
    def reset(self):
        """Reset the simulation."""
        self.grid.clear_grid()
        self.controller.elements.clear()
        self.controller.target_positions = []
        
    def initialize_elements(self, num_elements):
        """Initialize the specified number of elements at the bottom of the grid."""
        self.reset()
        
        boundary_size = self.grid.boundary_size if hasattr(self.grid, 'boundary_size') else 1
        safe_width = self.grid.width - (2 * boundary_size)
        
        # Place elements at the bottom of the grid with a safe distance from walls
        for i in range(num_elements):
            x = boundary_size + (i % safe_width)
            y = self.grid.height - (boundary_size + 1)  # One row up from the bottom boundary
            self.controller.add_element(i, x, y)
        
        return self.controller.elements
    
    def set_target_shape(self, shape_type, num_elements):
        """Set the target shape for the elements."""
        target_positions = ShapeGenerator.generate_shape(
            shape_type, num_elements, self.grid.width, self.grid.height)
        self.controller.set_target_positions(target_positions)
        return target_positions
    
    def find_path(self, start_x, start_y, goal_x, goal_y, algorithm="astar", topology="vonNeumann"):
        """Find a path using the specified algorithm."""
        if algorithm == "astar":
            return astar_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
        elif algorithm == "bfs":
            return bfs_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
        elif algorithm == "greedy":
            return greedy_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
# Modified transform method with simplified distributed control
    def transform(self, algorithm="astar", topology="vonNeumann", movement="sequential", control_mode="centralized"):
        """Transform the elements to the target shape."""
        # Timing
        start_time = time.time()
        
        # Assign targets to elements
        self.controller.assign_targets()
        
        # Find paths for all elements
        paths = {}
        total_moves = []
        total_nodes_explored = 0
        
        if control_mode == "centralized":
            # Process elements one by one, keeping track of intermediate grid states
            sorted_elements = sorted(
                self.controller.elements.values(),
                key=lambda e: e.distance_to_target() if e.has_target() else float('inf')
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
                
                if path_result:
                    path, nodes_explored = path_result
                    paths[element.id] = path
                    total_nodes_explored += nodes_explored
                    
                    # Add debug info
                    print(f"Element {element.id}: Path found with {len(path)} steps")
                    
                    # Apply the moves sequentially if movement is sequential
                    if movement == "sequential":
                        # Execute the path for this element
                        for i in range(1, len(path)):
                            move = {"agentId": element.id, "from": (element.x, element.y), "to": path[i]}
                            total_moves.append(move)
                            self.grid.move_element(element, path[i][0], path[i][1])
        
        elif control_mode == "distributed":
            # Simplified distributed approach where each element makes its own decisions
            # based on its current position and target
            max_steps = 100
            current_step = 0
            moves_this_round = []
            all_at_target = False
            
            # For tracking elements that have reached their targets
            reached_targets = set()
            
            # Simulate distributed movement until all elements reach targets or max steps reached
            while current_step < max_steps and not all_at_target:
                moves_this_round = []
                
                # Each element makes a decision independently
                for element_id, element in self.controller.elements.items():
                    if not element.has_target() or element_id in reached_targets:
                        continue
                    
                    # Check if element has reached its target
                    if element.x == element.target_x and element.y == element.target_y:
                        reached_targets.add(element_id)
                        continue
                    
                    # Get neighboring cells
                    neighbors = self.grid.get_neighbors(element.x, element.y, topology)
                    
                    # Filter neighbors that are not walls or occupied by other elements
                    valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                                    if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                    
                    if not valid_neighbors:
                        continue  # No valid moves available
                    
                    # Simple distributed decision: choose the neighbor that minimizes 
                    # Manhattan distance to target
                    best_distance = element.distance_to_target()
                    best_pos = None
                    
                    for nx, ny in valid_neighbors:
                        # Calculate Manhattan distance from this neighbor to target
                        distance = abs(nx - element.target_x) + abs(ny - element.target_y)
                        if distance < best_distance:
                            best_distance = distance
                            best_pos = (nx, ny)
                    
                    # If a better position is found, plan to move there
                    if best_pos:
                        moves_this_round.append((element, best_pos))
                
                # For parallel movement, resolve conflicts (multiple elements wanting the same cell)
                if movement == "parallel":
                    # Track which positions will be occupied
                    planned_positions = {}
                    
                    # Sort moves by distance priority (elements closer to targets move first)
                    moves_this_round.sort(
                        key=lambda m: abs(m[0].target_x - m[1][0]) + abs(m[0].target_y - m[1][1])
                    )
                    
                    # Allocate moves, giving priority to elements closer to their targets
                    final_moves = []
                    for element, pos in moves_this_round:
                        if pos not in planned_positions:
                            planned_positions[pos] = element
                            final_moves.append((element, pos))
                    
                    moves_this_round = final_moves
                
                # Execute the moves for this round
                for element, (next_x, next_y) in moves_this_round:
                    move = {"agentId": element.id, "from": (element.x, element.y), "to": (next_x, next_y)}
                    total_moves.append(move)
                    self.grid.move_element(element, next_x, next_y)
                    total_nodes_explored += 1  # Count each move as a node exploration
                
                # Check if all elements have reached their targets
                all_at_target = all(
                    (element.x == element.target_x and element.y == element.target_y) 
                    for element in self.controller.elements.values() 
                    if element.has_target()
                )
                
                # If sequential movement and no moves were made this round, break out of the loop
                if movement == "sequential" and not moves_this_round:
                    break
                    
                current_step += 1
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Return the results
        return {
            "paths": paths,
            "moves": total_moves,
            "time": elapsed_time,
            "nodes_explored": total_nodes_explored,
            "success": True
        }
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
=======
# app/controllers/simulation.py
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
            # Check if the goal position is blocked by another agent
            if self.grid.is_element(goal_x, goal_y):
                print(f"Goal position ({goal_x}, {goal_y}) is blocked by another agent")
                return None, 0
            
            if algorithm == "astar":
                path_result = astar_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
            elif algorithm == "bfs":
                path_result = bfs_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
            elif algorithm == "greedy":
                path_result = greedy_pathfind(self.grid, start_x, start_y, goal_x, goal_y, topology)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")
            
            # Check if a valid path was found
            if path_result is None or path_result[0] is None:
                print(f"No path found from ({start_x}, {start_y}) to ({goal_x}, {goal_y})")
                return None, 0
            
            path, nodes_explored = path_result
            print(f"Path found with {len(path)} steps")
            return path_result
        except Exception as e:
            print(f"Error in find_path: {e}")
            return None, 0

   # 1. Add the resolve_moore_deadlock function shown above to your ProgrammableMatterSimulation class

    # 2. In your transform() method of ProgrammableMatterSimulation, find this section:
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
        
        # Add calculated paths and elapsed time to result
        result["paths"] = paths
        result["time"] = time.time() - start_time
        
        return result


    # 3. Modify the no_progress_counter section in your _transform_centralized or _transform_independent method:
    # Find the section that looks like this:
    
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
  
    def _transform_independent(self, algorithm, topology, movement, total_moves, total_nodes_explored):
        """
        Enhanced independent control transformation implementation.
        Each element makes movement decisions based on local information.
        
        Includes improved deadlock detection and resolution.
        """
        print("\nIndependent control mode")
        
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
                
                # Add to blocked elements list if stuck for too long
                if stuck_counter.get(element_id, 0) > 10:
                    if element_id not in blocked_elements:
                        blocked_elements.add(element_id)
                        print(f"Element {element_id} is considered blocked (stuck for 10+ steps)")
                
                # Get all neighboring cells
                neighbors = self.grid.get_neighbors(element.x, element.y, topology)
                
                # Filter neighbors that are not walls or occupied by other elements
                valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                                if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if not valid_neighbors:
                    print(f"Element {element_id} has no valid moves available (surrounded)")
                    continue
                
                # ENHANCED MOVEMENT DECISION STRATEGY
                next_pos = None
                
                # Adjust thresholds based on topology
                if topology == "moore":
                    # Be more aggressive with deadlock detection for Moore topology
                    deadlock_threshold = 5  # Lower threshold (default is 5)
                else:
                    deadlock_threshold = 5  # Normal threshold for von Neumann
                
                # STRATEGY 1: If element is deadlocked or severely stuck, use random movement to break out
                if is_deadlocked or stuck_counter.get(element_id, 0) >= deadlock_threshold:
                    print(f"Element {element_id} is deadlocked or stuck. Using randomized movement.")
                    
                    # Try to find a neighbor that isn't in the recent movement pattern
                    recent_positions = set(position_history[element_id][-pattern_length*2:] if pattern_length > 0 else [])
                    escape_neighbors = [pos for pos in valid_neighbors if pos not in recent_positions]
                    
                    if escape_neighbors:
                        # Choose a random neighbor that breaks the pattern
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
                        
                        for nx, ny in valid_neighbors:
                            # Check if this is a diagonal move (for Moore topology)
                            is_diagonal = abs(nx - element.x) == 1 and abs(ny - element.y) == 1
                            
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
                            
                            # Mobility - count future free neighbors
                            future_neighbors = self.grid.get_neighbors(nx, ny, topology)
                            free_future_neighbors = sum(1 for fx, fy in future_neighbors
                                                    if not self.grid.is_wall(fx, fy) and not self.grid.is_element(fx, fy))
                            
                            # Avoid revisiting recent positions (anti-oscillation)
                            recent_penalty = -5 if (nx, ny) in position_history.get(element_id, [])[-3:] else 0
                            
                            # Add a slight penalty for diagonal moves to reduce congestion (Moore only)
                            diagonal_penalty = -0.5 if is_diagonal and topology == "moore" else 0
                            
                            # Combined score with weights
                            score = (distance_improvement * 4) + (direction_alignment * 2) + \
                                    (free_future_neighbors * 0.5) + recent_penalty + diagonal_penalty
                            
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
                            # Simple blocking check: element is directly between other and its target
                            if ((element.x == other.target_x and 
                                min(other.y, other.target_y) <= element.y <= max(other.y, other.target_y)) or
                                (element.y == other.target_y and 
                                min(other.x, other.target_x) <= element.x <= max(other.x, other.target_x))):
                                blocking_elements.add(element_id)
                                break
                
                # Enhanced priority sorting
                moves_this_round.sort(key=lambda m: (
                    # Priority 1: Distance to target (lower is better)
                    m[0].distance_to_target(),
                    
                    # Priority 2: Negative wait time (higher wait time = higher priority)
                    -stuck_counter.get(m[0].id, 0),
                    
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
            
            # Execute the moves for this round
            executed_move_count = 0
            for element, (next_x, next_y) in moves_this_round:
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

    # Add this function to your ProgrammableMatterSimulation class

    def resolve_sequential_moore_deadlock(self, total_moves):
        """
        Advanced deadlock resolution for sequential movement in Moore topology.
        Sequential movement requires more aggressive deadlock resolution since
        only one element moves at a time.
        
        Returns:
            Boolean indicating if a deadlock-breaking move was executed
        """
        print("Attempting to resolve sequential Moore topology deadlock...")
        
        # Step 1: Identify all elements not at their targets
        active_elements = [e for e in self.controller.elements.values() 
                        if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
        
        if not active_elements:
            return False
        
        # Step 2: First attempt - find elements that can make progress toward target
        for element in active_elements:
            # Get all possible moves
            neighbors = self.grid.get_neighbors(element.x, element.y, "moore")
            valid_moves = [(nx, ny) for nx, ny in neighbors 
                        if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
            
            if not valid_moves:
                continue
                
            # Sort moves by distance to target
            valid_moves.sort(key=lambda pos: 
                        abs(pos[0] - element.target_x) + abs(pos[1] - element.target_y))
            
            # Is this move actually getting closer to the target?
            best_move = valid_moves[0]
            current_dist = abs(element.x - element.target_x) + abs(element.y - element.target_y)
            new_dist = abs(best_move[0] - element.target_x) + abs(best_move[1] - element.target_y)
            
            if new_dist < current_dist:
                # This move makes progress - execute it
                old_pos = (element.x, element.y)
                success = self.grid.move_element(element, best_move[0], best_move[1])
                
                if success:
                    print(f"Breaking deadlock: Moved element {element.id} closer to target")
                    move = {"agentId": element.id, "from": old_pos, "to": best_move}
                    total_moves.append(move)
                    return True
        
        # Step 3: Second attempt - find elements blocking others and move them
        # Detect simple blocking scenarios (one element directly in another's path)
        for blocked in active_elements:
            # Calculate direction to target
            dx = 1 if blocked.target_x > blocked.x else (-1 if blocked.target_x < blocked.x else 0)
            dy = 1 if blocked.target_y > blocked.y else (-1 if blocked.target_y < blocked.y else 0)
            
            # Check if there's an element in that direction
            next_x, next_y = blocked.x + dx, blocked.y + dy
            
            if self.grid.is_valid_position(next_x, next_y) and self.grid.is_element(next_x, next_y):
                # Find the blocking element
                blocker = None
                for e in active_elements:
                    if e.x == next_x and e.y == next_y:
                        blocker = e
                        break
                
                if blocker:
                    # Try to move the blocker
                    blocker_neighbors = self.grid.get_neighbors(blocker.x, blocker.y, "moore")
                    valid_moves = [(nx, ny) for nx, ny in blocker_neighbors 
                                if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                    
                    if valid_moves:
                        # Prioritize moves that don't block others and aren't diagonal
                        good_moves = []
                        
                        for nx, ny in valid_moves:
                            # Skip the position directly behind the blocked element (would cause swap deadlock)
                            if nx == blocked.x and ny == blocked.y:
                                continue
                                
                            # Prefer non-diagonal moves when possible
                            is_diagonal = abs(nx - blocker.x) == 1 and abs(ny - blocker.y) == 1
                            score = 0 if is_diagonal else 1
                            
                            # Also prefer moves toward blocker's own target
                            if blocker.has_target():
                                current_dist = abs(blocker.x - blocker.target_x) + abs(blocker.y - blocker.target_y)
                                new_dist = abs(nx - blocker.target_x) + abs(ny - blocker.target_y)
                                if new_dist < current_dist:
                                    score += 2
                            
                            good_moves.append((nx, ny, score))
                        
                        # Sort by score (higher is better)
                        if good_moves:
                            good_moves.sort(key=lambda m: m[2], reverse=True)
                            next_pos = (good_moves[0][0], good_moves[0][1])
                            
                            old_pos = (blocker.x, blocker.y)
                            success = self.grid.move_element(blocker, next_pos[0], next_pos[1])
                            
                            if success:
                                print(f"Breaking blocking deadlock: Moved blocker {blocker.id} from path of {blocked.id}")
                                move = {"agentId": blocker.id, "from": old_pos, "to": next_pos}
                                total_moves.append(move)
                                return True
        
        # Step 4: Check for elements that are severely stuck (surrounded by other elements)
        for element in active_elements:
            neighbors = self.grid.get_neighbors(element.x, element.y, "moore")
            occupied_count = sum(1 for nx, ny in neighbors 
                            if self.grid.is_wall(nx, ny) or self.grid.is_element(nx, ny))
            
            # If element is highly surrounded, it might be causing a deadlock
            # For Moore neighborhood (8 neighbors), being surrounded by 5+ neighbors is problematic
            if occupied_count >= 5:
                # Try to move a surrounding element to free up space
                for nx, ny in neighbors:
                    if self.grid.is_element(nx, ny):
                        # Find which element is at this position
                        adjacent = None
                        for e in active_elements:
                            if e.x == nx and e.y == ny:
                                adjacent = e
                                break
                        
                        if adjacent:
                            # Try to move this adjacent element
                            adj_neighbors = self.grid.get_neighbors(adjacent.x, adjacent.y, "moore")
                            valid_moves = [(ax, ay) for ax, ay in adj_neighbors 
                                        if not self.grid.is_wall(ax, ay) and not self.grid.is_element(ax, ay)]
                            
                            if valid_moves:
                                next_pos = valid_moves[0]  # Take any valid move
                                old_pos = (adjacent.x, adjacent.y)
                                success = self.grid.move_element(adjacent, next_pos[0], next_pos[1])
                                
                                if success:
                                    print(f"Breaking surrounding deadlock: Moved adjacent element {adjacent.id}")
                                    move = {"agentId": adjacent.id, "from": old_pos, "to": next_pos}
                                    total_moves.append(move)
                                    return True
        
        # Step 5: Last resort - Make a completely random move with any element
        # This is more aggressive for sequential mode since we need stronger interventions
        if active_elements:
            # Try multiple random elements before giving up
            for _ in range(min(5, len(active_elements))):
                element = random.choice(active_elements)
                
                neighbors = self.grid.get_neighbors(element.x, element.y, "moore")
                valid_moves = [(nx, ny) for nx, ny in neighbors 
                            if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if valid_moves:
                    # Make a completely random move
                    next_pos = random.choice(valid_moves)
                    old_pos = (element.x, element.y)
                    success = self.grid.move_element(element, next_pos[0], next_pos[1])
                    
                    if success:
                        print(f"Breaking deadlock with random move: Moved element {element.id}")
                        move = {"agentId": element.id, "from": old_pos, "to": next_pos}
                        total_moves.append(move)
                        return True
        
        # If all our strategies failed, it's a severe deadlock
        return False

    def _break_complex_deadlock(self, total_moves, blocked_elements=None):
            """
            Advanced method to break complex deadlocks by analyzing the current grid state
            and making strategic movement decisions.
            
            Args:
                total_moves: List to track all moves
                blocked_elements: Set of element IDs that are considered blocked
            
            Returns:
                bool: True if a deadlock-breaking move was executed, False otherwise
            """
            print("Attempting to break complex deadlock...")
            
            if blocked_elements is None:
                blocked_elements = set()
            
            # STRATEGY 1: Focus on moving elements that are blocking others
            blocking_pairs = self._find_blocking_pairs()
            if blocking_pairs:
                print(f"Found {len(blocking_pairs)} blocking pairs of elements")
                
                # Sort blocking pairs by priority
                # Priority: element A is blocking element B's path to target
                # Higher priority if B is close to its target
                blocking_pairs.sort(key=lambda pair: pair[1].distance_to_target())
                
                for blocking_element, blocked_element in blocking_pairs:
                    print(f"Element {blocking_element.id} is blocking Element {blocked_element.id}")
                    
                    # Try to find a move for the blocking element that doesn't block the path
                    neighbors = self.grid.get_neighbors(blocking_element.x, blocking_element.y, "vonNeumann")
                    valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                                    if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                    
                    if not valid_neighbors:
                        continue
                    
                    # Evaluate each potential move for the blocking element
                    neighbor_scores = []
                    for nx, ny in valid_neighbors:
                        # Temporarily move the blocking element
                        old_x, old_y = blocking_element.x, blocking_element.y
                        self.grid.remove_element(blocking_element)
                        
                        # Check if this opens a path for the blocked element
                        path_result = self.find_path(
                            blocked_element.x, blocked_element.y,
                            blocked_element.target_x, blocked_element.target_y,
                            "astar", "vonNeumann"
                        )
                        
                        # Put the blocking element back
                        self.grid.add_element(blocking_element)
                        
                        # Score based on whether this opens a path
                        path_score = 100 if path_result and path_result[0] else 0
                        
                        # Also consider how good this move is for the blocking element itself
                        blocking_dist_before = abs(old_x - blocking_element.target_x) + abs(old_y - blocking_element.target_y)
                        blocking_dist_after = abs(nx - blocking_element.target_x) + abs(ny - blocking_element.target_y)
                        dist_improvement = blocking_dist_before - blocking_dist_after
                        
                        # Combined score (heavily weighted toward opening the path)
                        total_score = path_score + (dist_improvement * 2)
                        neighbor_scores.append((nx, ny, total_score))
                    
                    if neighbor_scores:
                        # Sort by score and choose the best move
                        neighbor_scores.sort(key=lambda x: x[2], reverse=True)
                        best_move = neighbor_scores[0]
                        
                        # Execute the move if it has a positive score
                        if best_move[2] >= 0:
                            nx, ny = best_move[0], best_move[1]
                            old_pos = (blocking_element.x, blocking_element.y)
                            
                            success = self.grid.move_element(blocking_element, nx, ny)
                            if success:
                                print(f"Breaking deadlock: Moved Element {blocking_element.id} from {old_pos} to ({nx}, {ny})")
                                move = {"agentId": blocking_element.id, "from": old_pos, "to": (nx, ny)}
                                total_moves.append(move)
                                return True
            
            # STRATEGY 2: Focus specifically on the known blocked elements
            if blocked_elements:
                print(f"Focusing on {len(blocked_elements)} known blocked elements")
                
                for element_id in blocked_elements:
                    if element_id not in self.controller.elements:
                        continue
                        
                    element = self.controller.elements[element_id]
                    
                    # Try to find any possible move for the blocked element
                    neighbors = self.grid.get_neighbors(element.x, element.y, "vonNeumann")
                    valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                                    if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                    
                    if valid_neighbors:
                        # Calculate scores for each move
                        neighbor_scores = []
                        for nx, ny in valid_neighbors:
                            # Calculate how this move affects distance to target
                            current_dist = element.distance_to_target()
                            new_dist = abs(nx - element.target_x) + abs(ny - element.target_y)
                            dist_score = current_dist - new_dist  # Positive if getting closer
                            
                            # Check if this position has more open neighbors (mobility)
                            future_neighbors = self.grid.get_neighbors(nx, ny, "vonNeumann")
                            future_valid = [(fx, fy) for fx, fy in future_neighbors 
                                        if not self.grid.is_wall(fx, fy) and not self.grid.is_element(fx, fy)]
                            mobility_score = len(future_valid)
                            
                            # Combined score
                            score = (dist_score * 2) + mobility_score
                            neighbor_scores.append((nx, ny, score))
                        
                        # Select best move
                        if neighbor_scores:
                            neighbor_scores.sort(key=lambda x: x[2], reverse=True)
                            best_pos = neighbor_scores[0][0], neighbor_scores[0][1]
                            old_pos = (element.x, element.y)
                            
                            success = self.grid.move_element(element, best_pos[0], best_pos[1])
                            if success:
                                print(f"Moved blocked Element {element.id} from {old_pos} to {best_pos}")
                                move = {"agentId": element.id, "from": old_pos, "to": best_pos}
                                total_moves.append(move)
                                return True
            
            # STRATEGY 3: Random movement as last resort
            # Try moving any element that's not at its target to break the deadlock
            non_target_elements = [e for e in self.controller.elements.values() 
                                if e.has_target() and (e.x != e.target_x or e.y != e.target_y)]
            
            if non_target_elements:
                # Randomly select an element
                element = random.choice(non_target_elements)
                
                # Try to find any valid move
                neighbors = self.grid.get_neighbors(element.x, element.y, "vonNeumann")
                valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                                if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
                
                if valid_neighbors:
                    # Make a random move
                    next_pos = random.choice(valid_neighbors)
                    old_pos = (element.x, element.y)
                    
                    success = self.grid.move_element(element, next_pos[0], next_pos[1])
                    if success:
                        print(f"Random deadlock break: Moved Element {element.id} from {old_pos} to {next_pos}")
                        move = {"agentId": element.id, "from": old_pos, "to": next_pos}
                        total_moves.append(move)
                        return True
            
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
>>>>>>> 5fcb68a (Pushing latest updates)
        }