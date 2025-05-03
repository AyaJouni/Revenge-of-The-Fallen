# app/algorithms/greedy.py
import heapq

def manhattan_distance(x1, y1, x2, y2):
    """Calculate the Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)

def greedy_pathfind(grid, start_x, start_y, goal_x, goal_y, topology="vonNeumann"):
    """
    Find a path from start to goal using greedy best-first search with Manhattan distance.
    
    Args:
        grid: The Grid environment
        start_x, start_y: Starting position
        goal_x, goal_y: Goal position
        topology: Grid topology ("vonNeumann" or "moore")
    
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
    
    # Priority queue for greedy best-first search
    open_set = [(manhattan_distance(start_x, start_y, goal_x, goal_y), 0, (start_x, start_y))]
    
    # Counter for tie-breaking when distances are equal
    counter = 1
    
    # Set to keep track of visited positions
    closed_set = set()
    
    # Dictionary to store parent positions for path reconstruction
    came_from = {}
    
    nodes_explored = 0
    
    while open_set:
        # Get the position with the lowest heuristic value
        _, _, current = heapq.heappop(open_set)
        current_x, current_y = current
        nodes_explored += 1
        
        # If we've reached the goal, reconstruct and return the path
        if current_x == goal_x and current_y == goal_y:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()  # Reverse to get path from start to goal
            return path, nodes_explored
        
        # Mark current position as visited
        closed_set.add(current)
        
        # Explore neighbors based on topology
        for next_x, next_y in grid.get_neighbors(current_x, current_y, topology):
            neighbor = (next_x, next_y)
            
            # Skip if neighbor is not valid, is a wall, is occupied, or already visited
            if (neighbor in closed_set or
                grid.is_wall(next_x, next_y) or
                grid.is_element(next_x, next_y)):
                continue
            
            # Calculate heuristic for this neighbor
            h = manhattan_distance(next_x, next_y, goal_x, goal_y)
            
            # Check if this neighbor is already in the open set
            is_in_open_set = False
            for i, (_, _, pos) in enumerate(open_set):
                if pos == neighbor:
                    is_in_open_set = True
                    break
            
            # If this is a new position, update the open set
            if not is_in_open_set:
                came_from[neighbor] = current
                heapq.heappush(open_set, (h, counter, neighbor))
                counter += 1
    
    # If we've exhausted all possibilities without finding a path
    return None, nodes_explored