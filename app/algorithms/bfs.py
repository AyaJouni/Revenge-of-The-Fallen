# app/algorithms/bfs.py
from collections import deque

def bfs_pathfind(grid, start_x, start_y, goal_x, goal_y, topology="vonNeumann"):
    """
    Find a path from start to goal using Breadth-First Search.
    
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
    
    # Queue for BFS
    queue = deque([(start_x, start_y)])
    
    # Set to keep track of visited positions
    visited = set([(start_x, start_y)])
    
    # Dictionary to store the parent of each position for path reconstruction
    parent = {}
    
    nodes_explored = 0
    
    while queue:
        current_x, current_y = queue.popleft()
        nodes_explored += 1
        
        # Check all neighboring cells based on topology
        for next_x, next_y in grid.get_neighbors(current_x, current_y, topology):
            # Check if the next position is not visited, not a wall, and not occupied by another element
            if (next_x, next_y) not in visited and not grid.is_wall(next_x, next_y) and not grid.is_element(next_x, next_y):
                # Add to the queue and mark as visited
                queue.append((next_x, next_y))
                visited.add((next_x, next_y))
                parent[(next_x, next_y)] = (current_x, current_y)
                
                # Check if we reached the goal
                if next_x == goal_x and next_y == goal_y:
                    # Reconstruct path
                    path = [(next_x, next_y)]
                    while (path[-1] != (start_x, start_y)):
                        path.append(parent[path[-1]])
                    path.reverse()
                    return path, nodes_explored
    
    # If no path is found
    return None, nodes_explored