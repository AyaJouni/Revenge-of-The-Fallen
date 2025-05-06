# app/algorithms/expectimax.py
import heapq
import math
import random

def expectimax_pathfind(grid, start_x, start_y, goal_x, goal_y, controller, element_id, topology="vonNeumann", max_depth=2):
    """
    Find a path using Expectimax search algorithm.
    Handles uncertainty in adversarial multi-agent environments.
    
    Args:
        grid: The Grid environment
        start_x, start_y: Starting position
        goal_x, goal_y: Goal position
        controller: ElementController that manages elements
        element_id: ID of the element being moved
        topology: Grid topology ("vonNeumann" or "moore")
        max_depth: Maximum search depth for Expectimax
    
    Returns:
        List of (x, y) positions forming a path from start to goal,
        and number of nodes explored
    """
    # Check if start and goal are valid positions
    if not grid.is_valid_position(start_x, start_y) or not grid.is_valid_position(goal_x, goal_y):
        return None, 0
    
    # Check if start or goal are walls
    if grid.is_wall(start_x, start_y) or grid.is_wall(goal_x, goal_y):
        return None, 0
    
    # If start is the goal, return a single-element path
    if start_x == goal_x and start_y == goal_y:
        return [(start_x, start_y)], 1
    
    # Get the element
    element = controller.elements.get(element_id)
    if not element:
        return None, 0
    
    # Adjust max_depth based on number of elements for computational efficiency
    num_elements = len(controller.elements)
    if num_elements > 15:
        max_depth = 1  # Very shallow search for many elements
    elif num_elements > 10:
        max_depth = 2  # Shallow search for many elements
    
    # Detect if element is in bottom row (needs special handling)
    is_bottom_row = element.y >= grid.height - 3
    
    # Find potential interfering elements
    interfering_elements = find_interfering_elements(
        grid, controller, element_id, start_x, start_y, goal_x, goal_y, is_bottom_row
    )
    
    # Store original position
    original_x, original_y = element.x, element.y
    
    # Get all possible first moves
    neighbors = grid.get_neighbors(start_x, start_y, topology)
    valid_moves = [(nx, ny) for nx, ny in neighbors 
                  if not grid.is_wall(nx, ny) and not grid.is_element(nx, ny)]
    
    # Special handling for bottom row elements - prioritize upward movements 
    if is_bottom_row and valid_moves:
        upward_moves = [(nx, ny) for nx, ny in valid_moves if ny < start_y]
        if upward_moves:
            # If element is stuck in bottom row, prioritize any upward movement
            # If there are multiple upward options, consider diagonal moves for Moore topology
            if topology == "moore" and len(upward_moves) > 1:
                # If element is far from target x-coordinate, prioritize diagonals that move toward target x
                target_dx = goal_x - start_x
                if abs(target_dx) > 1:
                    # Find upward diagonal moves that also move toward target x
                    diagonal_toward_target = [
                        (nx, ny) for nx, ny in upward_moves 
                        if (target_dx > 0 and nx > start_x) or (target_dx < 0 and nx < start_x)
                    ]
                    if diagonal_toward_target:
                        # Use a random diagonal toward target to break symmetry
                        return [(start_x, start_y), random.choice(diagonal_toward_target)], 1
                
                # If no good diagonal, use any upward move
                return [(start_x, start_y), upward_moves[0]], 1
            else:
                # For von Neumann, just move directly up if possible
                straight_up = (start_x, start_y - 1)
                if straight_up in upward_moves:
                    return [(start_x, start_y), straight_up], 1
                else:
                    return [(start_x, start_y), upward_moves[0]], 1
    
    # If no valid moves available, we're stuck - wait and see if situation changes
    if not valid_moves:
        # Check for elements blocking adjacent cells that might move
        adjacent_positions = [(start_x+dx, start_y+dy) 
                             for dx, dy in [(0, -1), (-1, 0), (1, 0), (0, 1)]]
        
        potentially_freeing = False
        for x, y in adjacent_positions:
            if grid.is_valid_position(x, y) and grid.is_element(x, y):
                # This position has an element that might move soon
                potentially_freeing = True
                break
        
        # Return current position with a note that we're waiting
        return [(start_x, start_y)], 1
    
    # Apply Expectimax to find the best first move
    best_move = None
    best_value = float('-inf')
    nodes_explored = 0
    
    # Value of each possible first move using Expectimax
    for nx, ny in valid_moves:
        # Temporarily move the element
        grid.remove_element(element)
        element.x, element.y = nx, ny
        grid.add_element(element)
        
        # Evaluate this move with Expectimax
        value = expectimax_value(
            grid, controller, element_id, interfering_elements, 
            1, max_depth, "max", topology, goal_x, goal_y, is_bottom_row
        )
        nodes_explored += 1
        
        # Special handling for bottom row elements - strong bonus for upward movement
        if is_bottom_row and ny < start_y:
            value += 100  # Significant bonus to escape bottom row
        
        # Restore the element's position
        grid.remove_element(element)
        element.x, element.y = original_x, original_y
        grid.add_element(element)
        
        # Update best move if this is better
        if value > best_value:
            best_value = value
            best_move = (nx, ny)
    
    if best_move is None:
        return None, nodes_explored
    
    # Now use A* to find a complete path starting with the best first move
    from app.algorithms.astar import astar_pathfind
    
    # Create a path starting with the initial position and best first move
    path = [(start_x, start_y), best_move]
    
    # For bottom row elements, we typically just want to take the first step
    # and then reevaluate, since the environment is highly dynamic
    if is_bottom_row:
        return path, nodes_explored
    
    # Find the rest of the path using A*
    grid.remove_element(element)  # Remove element temporarily
    sub_path, sub_nodes = astar_pathfind(grid, best_move[0], best_move[1], goal_x, goal_y, topology)
    grid.add_element(element)  # Put element back
    
    # If A* found a path, combine it with our first move
    if sub_path and len(sub_path) > 1:
        path.extend(sub_path[1:])  # Skip first position of sub_path (already in our path)
        return path, nodes_explored + sub_nodes
    else:
        # If A* couldn't find a path, just return the first move
        return path, nodes_explored

def expectimax_value(grid, controller, element_id, interfering_elements, depth, max_depth, 
                    node_type, topology, goal_x, goal_y, is_bottom_row=False):
    """
    Recursive Expectimax function.
    
    Args:
        grid: The Grid environment
        controller: ElementController that manages elements
        element_id: ID of the element being moved
        interfering_elements: List of element IDs that could interfere
        depth: Current depth in the search tree
        max_depth: Maximum search depth
        node_type: "max" for our element, "chance" for other elements
        topology: Grid topology
        goal_x, goal_y: Goal position for our element
        is_bottom_row: Whether this element is in the bottom row and needs priority
    
    Returns:
        Expected utility value of this state
    """
    # Get our element
    element = controller.elements[element_id]
    
    # Terminal conditions
    if depth >= max_depth:
        return evaluate_state(grid, element, goal_x, goal_y, interfering_elements, controller, is_bottom_row)
    
    if element.x == goal_x and element.y == goal_y:
        return 1000  # High value for reaching the goal
    
    if node_type == "max":  # Our element's turn (maximize utility)
        value = float('-inf')
        
        # Get all possible moves
        neighbors = grid.get_neighbors(element.x, element.y, topology)
        valid_moves = [(nx, ny) for nx, ny in neighbors 
                      if not grid.is_wall(nx, ny) and not grid.is_element(nx, ny)]
        
        # If element is in bottom row, prioritize upward movement
        if is_bottom_row and valid_moves:
            upward_moves = [(nx, ny) for nx, ny in valid_moves if ny < element.y]
            if upward_moves and len(upward_moves) > 0:
                # Strongly prefer upward moves for bottom row elements
                valid_moves = upward_moves
        
        # If no valid moves, evaluate current state with a penalty
        if not valid_moves:
            # Apply a penalty for being stuck
            return evaluate_state(grid, element, goal_x, goal_y, interfering_elements, controller, is_bottom_row) - 20
        
        # Evaluate each possible move
        for nx, ny in valid_moves:
            # Simulate move
            old_x, old_y = element.x, element.y
            grid.remove_element(element)
            element.x, element.y = nx, ny
            grid.add_element(element)
            
            # Get first interfering element for chance node
            if interfering_elements:
                next_node_type = "chance"
                next_elements = interfering_elements[:]
            else:
                # If no interfering elements, skip chance nodes
                next_node_type = "max"
                next_elements = []
            
            # Recursive evaluation
            move_value = expectimax_value(
                grid, controller, element_id, next_elements, 
                depth + 1, max_depth, next_node_type, topology, goal_x, goal_y, is_bottom_row
            )
            
            # Restore position
            grid.remove_element(element)
            element.x, element.y = old_x, old_y
            grid.add_element(element)
            
            value = max(value, move_value)
                
        return value
        
    else:  # Chance node (interfering elements)
        # If no interfering elements left to process at this depth,
        # move to a max node for our element at next depth
        if not interfering_elements:
            return expectimax_value(
                grid, controller, element_id, [], 
                depth + 1, max_depth, "max", topology, goal_x, goal_y, is_bottom_row
            )
        
        # Process first interfering element
        other_id = interfering_elements[0]
        remaining_elements = interfering_elements[1:] if len(interfering_elements) > 1 else []
        
        # If this element doesn't exist, skip to next
        if other_id not in controller.elements:
            if remaining_elements:
                return expectimax_value(
                    grid, controller, element_id, remaining_elements, 
                    depth, max_depth, "chance", topology, goal_x, goal_y, is_bottom_row
                )
            else:
                return expectimax_value(
                    grid, controller, element_id, [], 
                    depth + 1, max_depth, "max", topology, goal_x, goal_y, is_bottom_row
                )
        
        # Get the interfering element
        other = controller.elements[other_id]
        
        # Get possible moves for this interfering element
        neighbors = grid.get_neighbors(other.x, other.y, topology)
        valid_moves = [(nx, ny) for nx, ny in neighbors 
                      if not grid.is_wall(nx, ny) and 
                      not (nx == element.x and ny == element.y) and
                      not grid.is_element(nx, ny)]
        
        # Include staying in place as an option
        valid_moves.append((other.x, other.y))
        
        # If no valid moves (shouldn't happen since staying in place is valid),
        # proceed to next interfering element
        if not valid_moves:
            if remaining_elements:
                return expectimax_value(
                    grid, controller, element_id, remaining_elements, 
                    depth, max_depth, "chance", topology, goal_x, goal_y, is_bottom_row
                )
            else:
                return expectimax_value(
                    grid, controller, element_id, [], 
                    depth + 1, max_depth, "max", topology, goal_x, goal_y, is_bottom_row
                )
        
        # Expectimax computes expected utility over all possible moves
        total_value = 0
        total_weight = 0
        
        # Weight staying in place higher for bottom row elements
        move_weights = {}
        for nx, ny in valid_moves:
            if nx == other.x and ny == other.y:  # staying in place
                # Higher probability of staying in place if in bottom row
                if other.y >= grid.height - 3:
                    move_weights[(nx, ny)] = 3.0  # High weight for staying in place
                else:
                    move_weights[(nx, ny)] = 1.5  # Moderate weight for staying in place
            else:
                move_weights[(nx, ny)] = 1.0  # Normal weight for moving
        
        # Calculate total weight for normalization
        total_weight = sum(move_weights.values())
        
        # Evaluate each possible move with appropriate weight
        for nx, ny in valid_moves:
            # Skip if probability is effectively zero (precision issues)
            probability = move_weights[(nx, ny)] / total_weight
            if probability < 0.01:
                continue
                
            # If staying in place, no need to modify grid
            if nx == other.x and ny == other.y:
                # Process next interfering element or move to max node
                if remaining_elements:
                    move_value = expectimax_value(
                        grid, controller, element_id, remaining_elements, 
                        depth, max_depth, "chance", topology, goal_x, goal_y, is_bottom_row
                    )
                else:
                    move_value = expectimax_value(
                        grid, controller, element_id, [], 
                        depth + 1, max_depth, "max", topology, goal_x, goal_y, is_bottom_row
                    )
            else:
                # Simulate the move
                old_x, old_y = other.x, other.y
                grid.remove_element(other)
                other.x, other.y = nx, ny
                grid.add_element(other)
                
                # Process next interfering element or move to max node
                if remaining_elements:
                    move_value = expectimax_value(
                        grid, controller, element_id, remaining_elements, 
                        depth, max_depth, "chance", topology, goal_x, goal_y, is_bottom_row
                    )
                else:
                    move_value = expectimax_value(
                        grid, controller, element_id, [], 
                        depth + 1, max_depth, "max", topology, goal_x, goal_y, is_bottom_row
                    )
                
                # Restore position
                grid.remove_element(other)
                other.x, other.y = old_x, old_y
                grid.add_element(other)
            
            # Add weighted value to total
            total_value += probability * move_value
        
        return total_value

def find_interfering_elements(grid, controller, element_id, start_x, start_y, goal_x, goal_y, is_bottom_row=False):
    """
    Find elements that could potentially interfere with our path.
    
    Args:
        grid: The Grid environment
        controller: ElementController
        element_id: ID of our element
        start_x, start_y: Starting position
        goal_x, goal_y: Goal position
        is_bottom_row: Whether this element is in the bottom row and needs priority
    
    Returns:
        List of element IDs that could interfere
    """
    # Calculate bounding box of potential path with padding
    min_x = min(start_x, goal_x) - 2
    max_x = max(start_x, goal_x) + 2
    min_y = min(start_y, goal_y) - 2
    max_y = max(start_y, goal_y) + 2
    
    # For bottom row elements, especially look at elements directly above
    if is_bottom_row:
        min_y = min(start_y - 3, goal_y)  # Look more rows upward
        max_y = min(start_y + 1, goal_y + 1)  # Don't look too far down
    
    # Find elements within or near this bounding box
    potential_interference = []
    for other_id, other in controller.elements.items():
        if other_id == element_id:
            continue
            
        # Check if element is near our path
        if (min_x <= other.x <= max_x and min_y <= other.y <= max_y):
            # Only consider elements that might move (not at their targets)
            if other.has_target() and (other.x != other.target_x or other.y != other.target_y):
                # Calculate interference score based on proximity and position
                interference_score = calculate_interference_score(
                    start_x, start_y, goal_x, goal_y, 
                    other.x, other.y, 
                    other.target_x, other.target_y,
                    is_bottom_row
                )
                
                potential_interference.append((other_id, interference_score))
    
    # Sort by interference score and take top few elements
    if potential_interference:
        potential_interference.sort(key=lambda x: x[1], reverse=True)
        # Take more elements if in bottom row for better planning
        max_elements = 3 if is_bottom_row else 2
        return [e_id for e_id, _ in potential_interference[:max_elements]]
    
    return []

def calculate_interference_score(our_start_x, our_start_y, our_goal_x, our_goal_y, 
                               their_x, their_y, their_target_x, their_target_y,
                               is_bottom_row=False):
    """
    Calculate how likely an element is to interfere with our path.
    Higher scores indicate greater interference potential.
    """
    # Distance to our current position and goal
    distance_to_our_pos = abs(their_x - our_start_x) + abs(their_y - our_start_y)
    distance_to_our_goal = abs(their_x - our_goal_x) + abs(their_y - our_goal_y)
    
    # Check if they're directly in our planned path
    on_our_path = False
    if our_start_x == our_goal_x:  # Vertical path
        if their_x == our_start_x and min(our_start_y, our_goal_y) <= their_y <= max(our_start_y, our_goal_y):
            on_our_path = True
    elif our_start_y == our_goal_y:  # Horizontal path
        if their_y == our_start_y and min(our_start_x, our_goal_x) <= their_x <= max(our_start_x, our_goal_x):
            on_our_path = True
    else:  # Diagonal or irregular path
        # Check if they're within our path's bounding box
        in_box = (min(our_start_x, our_goal_x) <= their_x <= max(our_start_x, our_goal_x) and
                  min(our_start_y, our_goal_y) <= their_y <= max(our_start_y, our_goal_y))
        
        # More precise check for path intersection
        if in_box:
            # Simple approximation - if they're close to the direct line
            dx = our_goal_x - our_start_x
            dy = our_goal_y - our_start_y
            
            # Project their position onto our path line
            t = max(0, min(1, ((their_x - our_start_x) * dx + (their_y - our_start_y) * dy) / (dx*dx + dy*dy)))
            proj_x = our_start_x + t * dx
            proj_y = our_start_y + t * dy
            
            # Check distance to projection
            dist_to_line = abs(their_x - proj_x) + abs(their_y - proj_y)
            if dist_to_line <= 1:  # Very close to our path
                on_our_path = True
    
    # Calculate their path's potential intersection with ours
    path_intersection = 0
    if their_target_x is not None and their_target_y is not None:
        # Check if their path crosses ours
        our_dx = our_goal_x - our_start_x
        our_dy = our_goal_y - our_start_y
        their_dx = their_target_x - their_x
        their_dy = their_target_y - their_y
        
        # Simple cross product approximation
        cross_mag = abs(our_dx * their_dy - our_dy * their_dx)
        dot_product = our_dx * their_dx + our_dy * their_dy
        
        if cross_mag > 5:  # Paths likely cross at a significant angle
            path_intersection = 20
        elif dot_product < 0:  # Paths in opposite directions
            path_intersection = 10
        else:  # Paths roughly parallel
            path_intersection = 5
    
    # Special case for bottom row elements
    bottom_row_factor = 0
    if is_bottom_row:
        # Elements directly above us are highly interfering
        if their_y < our_start_y and abs(their_x - our_start_x) <= 1:
            bottom_row_factor = 50
        # Elements blocking the path upward
        elif their_y < our_start_y and their_x == our_start_x:
            bottom_row_factor = 40
    
    # Base score from proximity
    proximity_score = max(0, 10 - min(distance_to_our_pos, distance_to_our_goal))
    
    # Calculate final interference score
    interference_score = (
        proximity_score * 2 +  # Proximity is important
        (30 if on_our_path else 0) +  # Big bonus if directly on our path
        path_intersection +  # Add path intersection score
        bottom_row_factor  # Add bottom row factor
    )
    
    return interference_score

def evaluate_state(grid, element, goal_x, goal_y, interfering_elements, controller, is_bottom_row=False):
    """
    Evaluate the current state from element's perspective.
    
    Args:
        grid: The Grid environment
        element: The element being evaluated
        goal_x, goal_y: Goal position
        interfering_elements: List of interfering element IDs
        controller: ElementController
        is_bottom_row: Whether this element is in the bottom row and needs priority
        
    Returns:
        Utility value of this state
    """
    # Calculate distance to goal (Manhattan distance)
    distance = abs(element.x - goal_x) + abs(element.y - goal_y)
    
    # Base distance score - closer to goal is better
    distance_score = -10 * distance
    
    # For bottom row elements, heavily prioritize upward movement
    if is_bottom_row:
        # Strong bonus for vertical progress (higher is better)
        vertical_progress = start_y - element.y
        vertical_score = 20 * vertical_progress  # High value for upward progress
        
        # Even stronger penalty for staying in bottom rows
        if element.y >= 9:  # Very bottom rows
            distance_score -= 100
        
        # Modify distance score
        distance_score = distance_score + vertical_score
    
    # Path clearness - check if path to goal is clear
    path_clearness = 0
    
    # Check horizontal path component
    dx_sign = 1 if goal_x > element.x else -1 if goal_x < element.x else 0
    if dx_sign != 0:
        horizontal_blocked = False
        for x in range(element.x + dx_sign, goal_x + dx_sign, dx_sign):
            if grid.is_wall(x, element.y) or grid.is_element(x, element.y):
                horizontal_blocked = True
                path_clearness -= 15
                break
    
    # Check vertical path component
    dy_sign = 1 if goal_y > element.y else -1 if goal_y < element.y else 0
    if dy_sign != 0:
        vertical_blocked = False
        for y in range(element.y + dy_sign, goal_y + dy_sign, dy_sign):
            if grid.is_wall(element.x, y) or grid.is_element(element.x, y):
                vertical_blocked = True
                path_clearness -= 15
                # Extra penalty for blocked upward path in bottom row
                if is_bottom_row and dy_sign < 0:
                    path_clearness -= 25
                break
    
    # Mobility - more free neighbors is better
    neighbors = grid.get_neighbors(element.x, element.y, "vonNeumann")
    free_neighbors = sum(1 for nx, ny in neighbors
                       if not grid.is_wall(nx, ny) and not grid.is_element(nx, ny))
    mobility_score = 5 * free_neighbors
    
    # Special handling for bottom row - check for upward mobility
    upward_path_score = 0
    if is_bottom_row:
        # Check for any upward movement option
        for nx, ny in neighbors:
            if ny < element.y and not grid.is_wall(nx, ny) and not grid.is_element(nx, ny):
                upward_path_score += 40  # Big bonus for having an upward escape
                break
    
    # Check for interference from other elements
    interference_penalty = 0
    for other_id in interfering_elements:
        if other_id in controller.elements:
            other = controller.elements[other_id]
            # Calculate Manhattan distance to this element
            other_distance = abs(element.x - other.x) + abs(element.y - other.y)
            
            # Penalize being close to interfering elements
            if other_distance <= 2:
                interference_penalty -= (3 - other_distance) * 10
            
            # Extra penalty for elements blocking upward path in bottom row
            if is_bottom_row and other.y < element.y and abs(other.x - element.x) <= 1:
                interference_penalty -= 20
    
    # Calculate combined utility score
    # Bottom row elements get special scoring
    if is_bottom_row:
        # Emphasize upward mobility and path clearness
        return distance_score + path_clearness * 1.5 + mobility_score + upward_path_score + interference_penalty
    else:
        # Standard scoring for normal elements
        return distance_score + path_clearness + mobility_score + interference_penalty