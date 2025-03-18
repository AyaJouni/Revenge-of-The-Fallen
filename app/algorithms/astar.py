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
    print(f"A* pathfinding from ({start_x}, {start_y}) to ({goal_x}, {goal_y}) with topology {topology}")
    
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
    heapq.heappush(open_set, (0, (start_x, start_y)))  # (f_score, position)
    
    # Set to keep track of positions in the open set
    open_set_positions = {(start_x, start_y)}
    
    # Dictionary to store the g_score (cost from start) for each position
    g_score = {(start_x, start_y): 0}
    
    # Dictionary to store the f_score (g_score + heuristic) for each position
    f_score = {(start_x, start_y): manhattan_distance(start_x, start_y, goal_x, goal_y)}
    
    # Dictionary to store the parent of each position for path reconstruction
    parent = {}
    
    nodes_explored = 0
    
    while open_set:
        # Get the position with the lowest f_score
        current_f, (current_x, current_y) = heapq.heappop(open_set)
        open_set_positions.remove((current_x, current_y))
        nodes_explored += 1
        
        # Check if we reached the goal
        if current_x == goal_x and current_y == goal_y:
            # Reconstruct path
            path = [(current_x, current_y)]
            try:
                while (path[-1] != (start_x, start_y)):
                    if path[-1] not in parent:
                        print(f"ERROR: Path reconstruction failed. Position {path[-1]} has no parent.")
                        return None, nodes_explored
                    path.append(parent[path[-1]])
                path.reverse()
                print(f"Path found with {len(path)} steps: {path[:3]}...{path[-3:]}")
                return path, nodes_explored
            except Exception as e:
                print(f"ERROR in path reconstruction: {e}")
                return None, nodes_explored
        
        # Check all neighboring cells based on topology
        neighbors = grid.get_neighbors(current_x, current_y, topology)
        print(f"Node ({current_x}, {current_y}) has {len(neighbors)} neighbors")
        
        for next_x, next_y in neighbors:
            # Check if the next position is not a wall and not occupied by another element
            if not grid.is_wall(next_x, next_y) and not grid.is_element(next_x, next_y):
                # Calculate tentative g_score
                tentative_g_score = g_score[(current_x, current_y)] + 1
                
                # If this path is better than any previous one
                if (next_x, next_y) not in g_score or tentative_g_score < g_score[(next_x, next_y)]:
                    # Record the path
                    parent[(next_x, next_y)] = (current_x, current_y)
                    g_score[(next_x, next_y)] = tentative_g_score
                    
                    # Calculate f_score
                    next_f_score = tentative_g_score + manhattan_distance(next_x, next_y, goal_x, goal_y)
                    f_score[(next_x, next_y)] = next_f_score
                    
                    # Add to the open set if not already there
                    if (next_x, next_y) not in open_set_positions:
                        heapq.heappush(open_set, (next_f_score, (next_x, next_y)))
                        open_set_positions.add((next_x, next_y))
    
    # If no path is found
    print(f"No path found from ({start_x}, {start_y}) to ({goal_x}, {goal_y}) after exploring {nodes_explored} nodes")
    return None, nodes_explored