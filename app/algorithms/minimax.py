# app/algorithms/minimax.py
import heapq
import math
import random

def minimax_pathfind(grid, start_x, start_y, goal_x, goal_y, controller, element_id, topology="vonNeumann", max_depth=2):
    """
    Find a path using Minimax with Alpha-Beta pruning.
    
    Args:
        grid: The Grid environment
        start_x, start_y: Starting position
        goal_x, goal_y: Goal position
        controller: ElementController that manages elements
        element_id: ID of the element being moved
        topology: Grid topology ("vonNeumann" or "moore")
        max_depth: Maximum search depth for Minimax
    
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
        
    # Dynamically adjust max_depth based on number of elements
    # This reduces computational complexity for larger element counts
    num_elements = len(controller.elements)
    if num_elements > 10:
        max_depth = max(1, max_depth - 1)
    
    # Check if element is in bottom row - if so, prioritize upward movement
    bottom_row_priority = element.y >= 9
    
    # Store original position
    original_x, original_y = element.x, element.y
    
    # Find potential adversaries, with special handling for bottom row elements
    adversaries = find_potential_adversaries(grid, controller, element_id, start_x, start_y, goal_x, goal_y, bottom_row_priority)
    
    # Get all possible first moves
    neighbors = grid.get_neighbors(start_x, start_y, topology)
    valid_moves = [(nx, ny) for nx, ny in neighbors 
                  if not grid.is_wall(nx, ny) and not grid.is_element(nx, ny)]
    
    # If element is in bottom row and there's a valid upward move, prioritize it
    if bottom_row_priority and valid_moves:
        upward_moves = [(nx, ny) for nx, ny in valid_moves if ny < start_y]
        if upward_moves:
            # If direct vertical path is blocked, try diagonal upward moves
            vertical_blocked = any(grid.is_element(start_x, y) for y in range(start_y-1, goal_y-1, -1))
            if vertical_blocked and topology == "moore" and len(upward_moves) > 1:
                # Randomly choose an upward diagonal move to break symmetry
                return [(start_x, start_y), random.choice(upward_moves)], 1
            elif not vertical_blocked and upward_moves:
                return [(start_x, start_y), upward_moves[0]], 1
    
    if not valid_moves:
        # If no valid moves available, we're stuck
        # Try to identify if there's a position that might open up
        potential_future_moves = []
        for dx, dy in [(0, -1), (-1, 0), (1, 0), (0, 1)]:  # cardinal directions
            nx, ny = start_x + dx, start_y + dy
            if grid.is_valid_position(nx, ny) and not grid.is_wall(nx, ny) and grid.is_element(nx, ny):
                # This position has an element that might move
                potential_future_moves.append((nx, ny))
                
        if potential_future_moves:
            # Return current position but with a note that we're waiting
            return [(start_x, start_y)], 1
        return [(start_x, start_y)], 1
    
    # Apply Minimax to find the best first move
    best_move = None
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    nodes_explored = 0
    
    # If in bottom row, add a randomization factor to help break deadlocks
    random_choice = False
    if bottom_row_priority and random.random() < 0.3:  # 30% chance to make a random upward move
        upward_moves = [(nx, ny) for nx, ny in valid_moves if ny < start_y]
        if upward_moves:
            best_move = random.choice(upward_moves)
            random_choice = True
    
    # Normal minimax evaluation if not making a random choice
    if not random_choice:
        # Evaluate each possible first move
        for nx, ny in valid_moves:
            # Temporarily move the element
            grid.remove_element(element)
            element.x, element.y = nx, ny
            grid.add_element(element)
            
            # Evaluate this move with Minimax
            value = minimax_value(grid, controller, element_id, adversaries, 1, max_depth, 
                                False, alpha, beta, topology, goal_x, goal_y, bottom_row_priority)
            nodes_explored += 1
            
            # If element is in bottom row, add bonus for upward movement
            if bottom_row_priority and ny < start_y:
                value += 50  # Strong bonus for upward movement
                
            # Restore the grid
            grid.remove_element(element)
            element.x, element.y = original_x, original_y
            grid.add_element(element)
            
            # Update best move
            if value > best_value:
                best_value = value
                best_move = (nx, ny)
            
            # Update alpha
            alpha = max(alpha, best_value)
    
    if best_move is None:
        return None, nodes_explored
    
    # Now use A* to find a complete path starting with the best first move
    from app.algorithms.astar import astar_pathfind
    
    # Create a path starting with the initial position and best first move
    path = [(start_x, start_y), best_move]
    
    # For bottom row elements, we might want to just take the first step and reevaluate
    if bottom_row_priority:
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

def minimax_value(grid, controller, element_id, adversaries, depth, max_depth, 
                 is_max, alpha, beta, topology, goal_x, goal_y, bottom_row_priority=False):
    """
    Recursive Minimax function with Alpha-Beta pruning.
    
    Args:
        grid: The Grid environment
        controller: ElementController that manages elements
        element_id: ID of the element being moved
        adversaries: List of adversary element IDs
        depth: Current depth in the search tree
        max_depth: Maximum search depth
        is_max: True for maximizing player (our element), False for minimizing (adversaries)
        alpha, beta: Alpha-Beta pruning bounds
        topology: Grid topology
        goal_x, goal_y: Goal position for our element
        bottom_row_priority: Whether this element is in the bottom row and needs priority
    
    Returns:
        Utility value of this state
    """
    # Get our element
    element = controller.elements[element_id]
    
    # Terminal conditions
    if depth >= max_depth:
        return evaluate_state(grid, element, goal_x, goal_y, adversaries, controller, bottom_row_priority)
    
    if element.x == goal_x and element.y == goal_y:
        return 1000  # High value for reaching the goal
    
    if is_max:  # Maximizing player (our element)
        value = float('-inf')
        
        # Get all possible moves
        neighbors = grid.get_neighbors(element.x, element.y, topology)
        valid_moves = [(nx, ny) for nx, ny in neighbors 
                      if not grid.is_wall(nx, ny) and not grid.is_element(nx, ny)]
        
        # If element is in bottom row, prioritize upward movement
        if bottom_row_priority and valid_moves:
            upward_moves = [(nx, ny) for nx, ny in valid_moves if ny < element.y]
            if upward_moves and len(upward_moves) > 0:
                valid_moves = upward_moves  # Only consider upward moves
        
        if not valid_moves:
            # Still evaluate state even if stuck (important for fairness)
            penalty = evaluate_state(grid, element, goal_x, goal_y, adversaries, controller, bottom_row_priority)
            return penalty - 20  # Discourage being stuck but allow backpropagation
        
        for nx, ny in valid_moves:
            # Simulate move
            old_x, old_y = element.x, element.y
            grid.remove_element(element)
            element.x, element.y = nx, ny
            grid.add_element(element)
            
            # Recursive evaluation
            move_value = minimax_value(grid, controller, element_id, adversaries, depth + 1, 
                                     max_depth, False, alpha, beta, topology, goal_x, goal_y, bottom_row_priority)
            
            # Restore position
            grid.remove_element(element)
            element.x, element.y = old_x, old_y
            grid.add_element(element)
            
            value = max(value, move_value)
            alpha = max(alpha, value)
            
            if beta <= alpha:
                break  # Beta cutoff
                
        return value
        
    else:  # Minimizing player (adversaries)
        value = float('inf')
        
        # Skip if no adversaries
        if not adversaries:
            return minimax_value(grid, controller, element_id, adversaries, depth + 1, 
                               max_depth, True, alpha, beta, topology, goal_x, goal_y, bottom_row_priority)
        
        # Use only the first adversary for simplicity (can be extended to multiple)
        adversary_id = adversaries[0]
        remaining_adversaries = adversaries[1:] if len(adversaries) > 1 else []
        
        if adversary_id in controller.elements:
            adversary = controller.elements[adversary_id]
            
            # Get adversary's possible moves
            neighbors = grid.get_neighbors(adversary.x, adversary.y, topology)
            valid_moves = [(nx, ny) for nx, ny in neighbors 
                          if not grid.is_wall(nx, ny) and 
                          not (nx == element.x and ny == element.y) and
                          not grid.is_element(nx, ny)]
            
            # Include staying in place as an option with high probability
            valid_moves.append((adversary.x, adversary.y))
            
            # If adversary is also in bottom row, consider it might stay put more often
            if adversary.y >= 9 and bottom_row_priority:
                for _ in range(3):  # Add the staying put option multiple times to increase its probability
                    valid_moves.append((adversary.x, adversary.y))
            
            if not valid_moves:
                return minimax_value(grid, controller, element_id, remaining_adversaries, depth + 1, 
                                   max_depth, True, alpha, beta, topology, goal_x, goal_y, bottom_row_priority)
            
            for nx, ny in valid_moves:
                # Skip if staying in place
                if nx == adversary.x and ny == adversary.y:
                    move_value = minimax_value(grid, controller, element_id, remaining_adversaries, 
                                            depth + 1, max_depth, True, alpha, beta, 
                                            topology, goal_x, goal_y, bottom_row_priority)
                else:
                    # Simulate adversary move
                    old_x, old_y = adversary.x, adversary.y
                    grid.remove_element(adversary)
                    adversary.x, adversary.y = nx, ny
                    grid.add_element(adversary)
                    
                    # Recursive evaluation
                    move_value = minimax_value(grid, controller, element_id, remaining_adversaries, 
                                            depth + 1, max_depth, True, alpha, beta, 
                                            topology, goal_x, goal_y, bottom_row_priority)
                    
                    # Restore position
                    grid.remove_element(adversary)
                    adversary.x, adversary.y = old_x, old_y
                    grid.add_element(adversary)
                
                value = min(value, move_value)
                beta = min(beta, value)
                
                if beta <= alpha:
                    break  # Alpha cutoff
        
        return value

def find_potential_adversaries(grid, controller, element_id, start_x, start_y, goal_x, goal_y, bottom_row_priority=False):
    """
    Find elements that could potentially interfere with the path.
    
    Args:
        grid: The Grid environment
        controller: ElementController
        element_id: ID of our element
        start_x, start_y: Starting position
        goal_x, goal_y: Goal position
        bottom_row_priority: Whether this element is in the bottom row and needs priority
    
    Returns:
        List of element IDs that could interfere
    """
    # Calculate bounding box of potential path with some padding
    min_x = min(start_x, goal_x) - 2
    max_x = max(start_x, goal_x) + 2
    min_y = min(start_y, goal_y) - 2
    max_y = max(start_y, goal_y) + 2
    
    # For bottom row elements, look more at elements directly above
    if bottom_row_priority:
        min_y = min(start_y - 3, goal_y)  # Look more rows upward
        max_y = min(start_y + 1, goal_y + 1)  # Don't look too far down
    
    # Find elements within or near this bounding box
    adversaries = []
    for other_id, other in controller.elements.items():
        if other_id == element_id:
            continue
            
        # Check if element is near our path
        if (min_x <= other.x <= max_x and min_y <= other.y <= max_y):
            # Only consider elements that are not at their targets
            if other.has_target() and (other.x != other.target_x or other.y != other.target_y):
                # For bottom row, prioritize elements that block upward movement
                if bottom_row_priority and other.y < start_y and abs(other.x - start_x) <= 1:
                    threat_level = 100  # Very high threat for elements blocking upward movement
                    adversaries.append((other_id, threat_level))
                    continue
                
                # Check if their path might cross ours
                other_min_x = min(other.x, other.target_x if other.has_target() else other.x)
                other_max_x = max(other.x, other.target_x if other.has_target() else other.x)
                other_min_y = min(other.y, other.target_y if other.has_target() else other.y)
                other_max_y = max(other.y, other.target_y if other.has_target() else other.y)
                
                # Check for overlap in paths
                x_overlap = (min_x <= other_max_x and max_x >= other_min_x)
                y_overlap = (min_y <= other_max_y and max_y >= other_min_y)
                
                if x_overlap and y_overlap:
                    # Calculate threat level based on proximity and overlap with path
                    threat_level = calculate_threat_level(
                        start_x, start_y, goal_x, goal_y, 
                        other.x, other.y, 
                        other.target_x if other.has_target() else other.x, 
                        other.target_y if other.has_target() else other.y,
                        bottom_row_priority
                    )
                    
                    adversaries.append((other_id, threat_level))
    
    # Sort by threat level and take top adversaries
    if adversaries:
        adversaries.sort(key=lambda x: x[1], reverse=True)
        # Get more adversaries if in bottom row for better planning
        max_adversaries = 3 if bottom_row_priority else 2
        return [adv_id for adv_id, _ in adversaries[:max_adversaries]]
    
    return []

def calculate_threat_level(our_start_x, our_start_y, our_goal_x, our_goal_y, 
                         their_start_x, their_start_y, their_goal_x, their_goal_y,
                         bottom_row_priority=False):
    """
    Calculate how likely an element is to interfere with our path.
    Higher values indicate greater threat.
    """
    # Distance from their current position to our path
    distance_to_our_start = abs(their_start_x - our_start_x) + abs(their_start_y - our_start_y)
    distance_to_our_goal = abs(their_start_x - our_goal_x) + abs(their_start_y - our_goal_y)
    
    # Check if their path crosses our direct line
    our_dx = our_goal_x - our_start_x
    our_dy = our_goal_y - our_start_y
    their_dx = their_goal_x - their_start_x
    their_dy = their_goal_y - their_start_y
    
    # Simple cross-product check for path crossing
    cross_product = our_dx * their_dy - our_dy * their_dx
    
    # Threat level calculation
    threat = 0
    
    # Proximity threat (higher if closer to our path)
    proximity_threat = 20 - min(distance_to_our_start, distance_to_our_goal, 20)
    threat += proximity_threat
    
    # For bottom row, elements blocking upward movement are extremely threatening
    if bottom_row_priority and their_start_y < our_start_y and abs(their_start_x - our_start_x) <= 1:
        threat += 50
    
    # Path crossing threat
    if abs(cross_product) < 10:  # Paths are roughly parallel
        threat += 5
    else:  # Paths cross more directly
        threat += 15
    
    # Add threat if they're directly in our path
    if (min(our_start_x, our_goal_x) <= their_start_x <= max(our_start_x, our_goal_x) and
        min(our_start_y, our_goal_y) <= their_start_y <= max(our_start_y, our_goal_y)):
        threat += 20
    
    return threat

def evaluate_state(grid, element, goal_x, goal_y, adversaries, controller, bottom_row_priority=False):
    """
    Evaluate the current state from element's perspective.
    Args:
        grid: The Grid environment
        element: The element being evaluated
        goal_x, goal_y: Goal position
        adversaries: List of adversary element IDs
        controller: ElementController
        bottom_row_priority: Whether this element is in the bottom row and needs priority
    Returns:
        Utility value of this state
    """
    # Goal distance (closer is better)
    distance = abs(element.x - goal_x) + abs(element.y - goal_y)
    distance_score = -10 * distance

    # For bottom row elements, heavily prioritize moving upward toward goal
    if bottom_row_priority:
        # Strong bonus for making upward progress
        vertical_distance = element.y - goal_y
        vertical_score = vertical_distance * 20  # Higher bonus for vertical progress
        distance_score = -5 * distance + vertical_score
        
        # Even stronger penalty for staying in bottom rows
        if element.y >= 9:
            distance_score -= 100

    # Path clearness (penalize blocked paths)
    path_penalty = 0
    dx_sign = 1 if goal_x > element.x else -1 if goal_x < element.x else 0
    dy_sign = 1 if goal_y > element.y else -1 if goal_y < element.y else 0

    if dx_sign != 0:
        for x in range(element.x + dx_sign, goal_x + dx_sign, dx_sign):
            if grid.is_wall(x, element.y) or grid.is_element(x, element.y):
                path_penalty -= 15
                break

    if dy_sign != 0:
        for y in range(element.y + dy_sign, goal_y + dy_sign, dy_sign):
            if grid.is_wall(element.x, y) or grid.is_element(element.x, y):
                path_penalty -= 15
                # For bottom row, blocked upward path is extremely bad
                if bottom_row_priority and dy_sign < 0:
                    path_penalty -= 30  # Additional penalty
                break

    # Mobility (more free neighbors = better)
    neighbors = grid.get_neighbors(element.x, element.y, "vonNeumann")
    free_neighbors = sum(
        1 for nx, ny in neighbors if not grid.is_wall(nx, ny) and not grid.is_element(nx, ny)
    )
    mobility_score = 5 * free_neighbors

    # For bottom row, check if there's an upward path
    upward_path_score = 0
    if bottom_row_priority:
        for nx, ny in neighbors:
            if ny < element.y and not grid.is_wall(nx, ny) and not grid.is_element(nx, ny):
                upward_path_score += 50  # Big bonus for having an upward path
                break

    # Check adversary proximity
    adversary_penalty = 0
    for adv_id in adversaries:
        if adv_id in controller.elements:
            adv = controller.elements[adv_id]
            # Calculate Manhattan distance to adversary
            adv_distance = abs(element.x - adv.x) + abs(element.y - adv.y)
            # Penalize being close to adversaries
            if adv_distance <= 2:
                adversary_penalty -= (3 - adv_distance) * 10

    # Combined score with special handling for bottom row
    if bottom_row_priority:
        return distance_score + path_penalty + mobility_score + upward_path_score + adversary_penalty
    else:
        return distance_score + path_penalty + mobility_score + adversary_penalty