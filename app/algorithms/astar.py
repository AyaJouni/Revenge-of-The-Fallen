import heapq

def manhattan_distance(x1, y1, x2, y2):
    """Calculate the Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)

def astar_pathfind(grid, start_x, start_y, goal_x, goal_y, topology="vonNeumann"):
    """
    Find a path from start to goal using A* search with Manhattan distance heuristic.
    
    Args:
        grid: The Grid environment
        start_x, start_y: Starting position
        goal_x, goal_y: Goal position
        topology: Grid topology ("vonNeumann" or "moore")
    
    Returns:
        List of (x, y) positions forming a path from start to goal,
        and number of nodes explored
    """
    print(f"Finding path from ({start_x}, {start_y}) to ({goal_x}, {goal_y}) using astar")
    
    # Check if start and goal are valid positions
    if not grid.is_valid_position(start_x, start_y) or not grid.is_valid_position(goal_x, goal_y):
        print(f"Invalid positions: start=({start_x}, {start_y}), goal=({goal_x}, {goal_y})")
        return None, 0
    
    # Check if start or goal are walls
    if grid.is_wall(start_x, start_y) or grid.is_wall(goal_x, goal_y):
        print(f"Start or goal is a wall: start=({start_x}, {start_y}), goal=({goal_x}, {goal_y})")
        return None, 0
    
    # If start is the goal, return a single-element path
    if start_x == goal_x and start_y == goal_y:
        print(f"Start is goal: ({start_x}, {start_y})")
        return [(start_x, start_y)], 1
    
    # Priority queue for A*
    open_set = []
    heapq.heappush(open_set, (0, 0, (start_x, start_y)))  # (f_score, tiebreaker, position)
    
    # Set to keep track of positions in the open set
    open_set_positions = {(start_x, start_y)}
    
    # Dictionary to store the g_score (cost from start) for each position
    g_score = {(start_x, start_y): 0}
    
    # Dictionary to store the parent of each position for path reconstruction
    parent = {}
    
    # Counter for tiebreaker
    counter = 1
    
    nodes_explored = 0
    
    while open_set:
        # Get the position with the lowest f_score
        _, _, (current_x, current_y) = heapq.heappop(open_set)
        current_pos = (current_x, current_y)
        open_set_positions.remove(current_pos)
        nodes_explored += 1
        
        # Check if we reached the goal
        if current_x == goal_x and current_y == goal_y:
            # Reconstruct path
            path = [(current_x, current_y)]
            current = current_pos
            
            # Trace back the path through parent pointers
            while current in parent:
                current = parent[current]
                path.append(current)
            
            path.reverse()  # Reverse to get path from start to goal
            print(f"Path found with {len(path)} steps")
            return path, nodes_explored
        
        # Check all neighboring cells based on topology
        neighbors = grid.get_neighbors(current_x, current_y, topology)
        
        for next_x, next_y in neighbors:
            next_pos = (next_x, next_y)
            
            # Skip if the position is occupied by another element
            if grid.is_element(next_x, next_y):
                continue
                
            # Calculate tentative g_score
            tentative_g_score = g_score[current_pos] + 1
            
            # If this path is better than any previous one
            if next_pos not in g_score or tentative_g_score < g_score[next_pos]:
                # Record the path
                parent[next_pos] = current_pos
                g_score[next_pos] = tentative_g_score
                
                # Calculate f_score = g_score + heuristic
                f_score = tentative_g_score + manhattan_distance(next_x, next_y, goal_x, goal_y)
                
                # Add to the open set if not already there
                if next_pos not in open_set_positions:
                    heapq.heappush(open_set, (f_score, counter, next_pos))
                    counter += 1
                    open_set_positions.add(next_pos)
    
    # If no path is found
    print(f"No path found from ({start_x}, {start_y}) to ({goal_x}, {goal_y}) after exploring {nodes_explored} nodes")
    return None, nodes_explored