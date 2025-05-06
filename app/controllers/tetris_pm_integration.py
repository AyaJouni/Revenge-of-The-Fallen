# app/controllers/tetris_pm_integration.py
import time
import numpy as np

class TetrisPMIntegration:
    """
    Integration layer between the Tetris game and the programmable matter simulation.
    This class handles the interaction between falling Tetris pieces and
    the programmable matter elements.
    """
    
    def __init__(self, simulation, tetris_game):
        """
        Initialize the integration layer.
        
        Args:
            simulation: Reference to the ProgrammableMatterSimulation
            tetris_game: Reference to the TetrisGameController
        """
        self.simulation = simulation
        self.tetris_game = tetris_game
        self.grid = simulation.grid
        self.controller = simulation.controller
        
        # Configuration
        self.planning_depth = 3  # How many future pieces to consider
        self.update_interval = 0.1  # Seconds between PM updates
        self.last_update_time = 0
        
        # Tracking metrics
        self.target_positions = []  # Current target positions for PM elements
        self.planned_paths = {}  # Element ID -> planned path
        self.success_rate = 0.0  # Rate of successful target formations
        
        # AI parameters
        self.learning_enabled = False  # Whether learning is enabled
        self.use_expectimax = False  # Whether to use Expectimax for planning
        self.exploration_rate = 0.2  # Exploration rate for learning
        
    def update(self, current_time):
        """
        Update the integration layer. Should be called on each game loop iteration.
        
        Args:
            current_time: Current game time (from time.time())
            
        Returns:
            Dict with update information
        """
        if self.tetris_game.paused or self.tetris_game.game_over:
            return {'action': 'none'}
            
        # Only update PM at specified interval
        if current_time - self.last_update_time < self.update_interval:
            return {'action': 'none'}
            
        self.last_update_time = current_time
        
        # Get current Tetris game state
        game_state = self.tetris_game.get_game_state()
        
        # Update PM target positions based on current game state
        self._update_target_positions(game_state)
        
        # Plan and execute PM movements
        move_result = self._plan_and_execute_moves(game_state)
        
        # Check for successful formations
        formation_result = self._check_formations(game_state)
        
        return {
            'action': 'pm_update',
            'moves': move_result.get('moves', []),
            'formations': formation_result
        }
    
    def _update_target_positions(self, game_state):
        """
        Update the target positions for programmable matter elements
        based on the current game state.
        
        Args:
            game_state: Current Tetris game state
        """
        # Clear previous targets
        self.target_positions = []
        
        # Strategies for setting target positions:
        
        # 1. Prioritize completing rows that are nearly full
        self._add_near_complete_row_targets(game_state)
        
        # 2. Position under the current falling piece
        self._add_current_piece_targets(game_state)
        
        # 3. Add stability/support structure targets
        self._add_support_structure_targets(game_state)
        
        # 4. Position for future pieces (if planning ahead)
        if self.planning_depth > 0:
            self._add_future_piece_targets(game_state)
        
        # Finalize and assign target positions to elements
        self._assign_targets_to_elements()
    
    def _add_near_complete_row_targets(self, game_state):
        """
        Add targets to complete rows that are nearly full.
        
        Args:
            game_state: Current Tetris game state
        """
        grid = game_state['grid']
        
        # Check each row from bottom to top
        for y in range(len(grid) - 1, 0, -1):
            row = grid[y]
            
            # Count empty cells in this row
            empty_count = row.count(0)
            
            # If row is nearly complete (1-2 empty cells), add targets
            if 0 < empty_count <= 2:
                for x, cell in enumerate(row):
                    if cell == 0:
                        self.target_positions.append((x, y))
    
    def _add_current_piece_targets(self, game_state):
        """
        Add targets to position under the current falling piece.
        
        Args:
            game_state: Current Tetris game state
        """
        current_piece = game_state.get('current_piece')
        shadow_positions = game_state.get('shadow_positions')
        
        if shadow_positions:
            # Add positions below the shadow (landing) positions
            for x, y in shadow_positions:
                # Check if position below is empty and valid
                if (y + 1 < len(game_state['grid']) and 
                    game_state['grid'][y + 1][x] == 0):
                    self.target_positions.append((x, y + 1))
    
    def _add_support_structure_targets(self, game_state):
        """
        Add targets to create support structures for stability.
        
        Args:
            game_state: Current Tetris game state
        """
        grid = game_state['grid']
        
        # Look for patterns where support would be beneficial
        for y in range(len(grid) - 2, 0, -1):  # Skip bottom row
            for x in range(len(grid[y])):
                # Check for "holes" (empty cells with non-empty cells above)
                if grid[y][x] == 0:
                    # Check if there's a tetris block above
                    has_block_above = False
                    for check_y in range(y - 1, -1, -1):
                        if grid[check_y][x] != 0:
                            has_block_above = True
                            break
                    
                    if has_block_above:
                        # This is a hole, add a target here
                        self.target_positions.append((x, y))
    
    def _add_future_piece_targets(self, game_state):
        """
        Add targets based on planning for future pieces.
        More advanced - implements look-ahead planning.
        
        Args:
            game_state: Current Tetris game state
        """
        # This would implement more advanced planning algorithms
        # like Expectimax or Monte Carlo Tree Search
        
        if self.use_expectimax:
            # Example placeholder for Expectimax planning
            future_targets = self._expectimax_planning(game_state)
            self.target_positions.extend(future_targets)
        else:
            # Simpler heuristic planning
            future_targets = self._heuristic_planning(game_state)
            self.target_positions.extend(future_targets)
    
    def _expectimax_planning(self, game_state):
        """
        Implement Expectimax planning for future pieces.
        
        Args:
            game_state: Current Tetris game state
            
        Returns:
            List of target positions based on Expectimax planning
        """
        # This is a placeholder for actual Expectimax implementation
        # In a real implementation, this would model possible future
        # pieces and their optimal placements
        
        return []  # Placeholder
    
    def _heuristic_planning(self, game_state):
        """
        Implement simpler heuristic planning for future pieces.
        
        Args:
            game_state: Current Tetris game state
            
        Returns:
            List of target positions based on heuristic planning
        """
        # Simple heuristic: try to create flat surfaces
        grid = game_state['grid']
        targets = []
        
        # Find "valleys" (cells with higher columns on both sides)
        for x in range(1, len(grid[0]) - 1):
            height_left = 0
            height_right = 0
            height_current = 0
            
            # Calculate heights
            for y in range(len(grid)):
                if grid[y][x-1] != 0:
                    height_left = len(grid) - y
                    break
                    
            for y in range(len(grid)):
                if grid[y][x+1] != 0:
                    height_right = len(grid) - y
                    break
                    
            for y in range(len(grid)):
                if grid[y][x] != 0:
                    height_current = len(grid) - y
                    break
                    
            # If this is a valley, add target
            if height_current < min(height_left, height_right) - 1:
                target_y = len(grid) - max(1, height_current + 1)
                if target_y < len(grid) and grid[target_y][x] == 0:
                    targets.append((x, target_y))
                    
        return targets
    
    def _assign_targets_to_elements(self):
        """
        Assign target positions to PM elements.
        Uses a greedy algorithm to minimize total distance.
        """
        # Remove duplicates from target positions
        unique_targets = list(set(self.target_positions))
        
        # Get all available PM elements
        elements = list(self.controller.elements.values())
        
        # If no targets or elements, nothing to do
        if not unique_targets or not elements:
            return
            
        # Create a cost matrix for assignment
        cost_matrix = np.zeros((len(elements), len(unique_targets)))
        
        for i, element in enumerate(elements):
            for j, (tx, ty) in enumerate(unique_targets):
                # Manhattan distance as cost
                cost_matrix[i, j] = abs(element.x - tx) + abs(element.y - ty)
                
        # Use the Hungarian algorithm for optimal assignment
        try:
            from scipy.optimize import linear_sum_assignment
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            
            # Assign targets based on the solution
            for i, j in zip(row_ind, col_ind):
                if j < len(unique_targets):  # Safety check
                    tx, ty = unique_targets[j]
                    elements[i].set_target(tx, ty)
        except ImportError:
            # Fallback to greedy assignment if scipy not available
            self._greedy_target_assignment(elements, unique_targets)
    
    def _greedy_target_assignment(self, elements, targets):
        """
        Fallback greedy algorithm for target assignment.
        
        Args:
            elements: List of PM elements
            targets: List of target positions
        """
        # Sort elements by distance to closest target
        element_distances = []
        for element in elements:
            min_dist = float('inf')
            for tx, ty in targets:
                dist = abs(element.x - tx) + abs(element.y - ty)
                min_dist = min(min_dist, dist)
            element_distances.append((element, min_dist))
            
        # Sort by minimum distance (ascending)
        element_distances.sort(key=lambda x: x[1])
        
        # Assign targets
        remaining_targets = targets.copy()
        for element, _ in element_distances:
            if not remaining_targets:
                break
                
            # Find closest target
            closest_target = None
            min_dist = float('inf')
            for tx, ty in remaining_targets:
                dist = abs(element.x - tx) + abs(element.y - ty)
                if dist < min_dist:
                    min_dist = dist
                    closest_target = (tx, ty)
                    
            if closest_target:
                element.set_target(*closest_target)
                remaining_targets.remove(closest_target)
    
    def _plan_and_execute_moves(self, game_state):
        """
        Plan and execute movements for PM elements.
        
        Args:
            game_state: Current Tetris game state
            
        Returns:
            Dict with move results
        """
        # Update the simulation controller
        algorithm = "astar"  # Default algorithm
        topology = "vonNeumann"  # Default topology
        
        # Choose topology based on game mode
        if game_state.get('level', 1) > 5:
            # Higher levels use Moore topology for more movement options
            topology = "moore"
        
        # Execute the transformation
        result = self.simulation.transform(
            algorithm=algorithm,
            topology=topology,
            movement="parallel",  # Always use parallel for Tetris game
            control_mode="centralized"  # Use centralized for better coordination
        )
        
        # Update metrics
        if 'nodes_explored' in result:
            self.tetris_game.metrics['nodes_explored'] += result['nodes_explored']
            
        if 'moves' in result:
            self.tetris_game.metrics['total_moves'] += len(result['moves'])
            
        return result
    
    def _check_formations(self, game_state):
        """
        Check for successful target formations and update game state.
        
        Args:
            game_state: Current Tetris game state
            
        Returns:
            Dict with formation results
        """
        # Count how many elements reached their targets
        elements_at_target = 0
        elements_with_targets = 0
        
        for element in self.controller.elements.values():
            if element.has_target():
                elements_with_targets += 1
                if element.x == element.target_x and element.y == element.target_y:
                    elements_at_target += 1
        
        # Calculate success rate
        if elements_with_targets > 0:
            self.success_rate = elements_at_target / elements_with_targets
        else:
            self.success_rate = 0.0
            
        # Check for row clearing conditions
        # (Elements at targets that form a complete row)
        rows_formed = self._check_for_complete_rows(game_state)
        
        return {
            'success_rate': self.success_rate,
            'elements_at_target': elements_at_target,
            'elements_with_targets': elements_with_targets,
            'rows_formed': rows_formed
        }
    
    def _check_for_complete_rows(self, game_state):
        """
        Check if PM elements have formed complete rows.
        
        Args:
            game_state: Current Tetris game state
            
        Returns:
            List of row indices that are complete
        """
        tetris_grid = game_state['grid']
        grid_width = len(tetris_grid[0])
        grid_height = len(tetris_grid)
        
        # Create a copy of the Tetris grid with PM elements added
        combined_grid = [row.copy() for row in tetris_grid]
        
        # Add PM elements to the grid
        for element in self.controller.elements.values():
            if 0 <= element.x < grid_width and 0 <= element.y < grid_height:
                if combined_grid[element.y][element.x] == 0:  # Only if space is empty
                    combined_grid[element.y][element.x] = 'PM'  # Mark as PM element
        
        # Check for complete rows
        complete_rows = []
        for y in range(grid_height):
            if all(cell != 0 for cell in combined_grid[y]):
                complete_rows.append(y)
                
        # If there are complete rows, update the Tetris game
        if complete_rows:
            # Add score based on rows completed
            points_per_line = {
                1: 40,
                2: 100,
                3: 300,
                4: 1200  # Tetris!
            }
            
            if len(complete_rows) in points_per_line:
                self.tetris_game.score += points_per_line[len(complete_rows)] * self.tetris_game.level
                
            # Update lines cleared
            self.tetris_game.lines_cleared += len(complete_rows)
            
            # Clear the rows in the Tetris grid
            for y in sorted(complete_rows, reverse=True):
                # Move rows down
                for row in range(y, 0, -1):
                    self.tetris_game.tetris_grid[row] = self.tetris_game.tetris_grid[row - 1].copy()
                    
                # Empty the top row
                self.tetris_game.tetris_grid[0] = [0 for _ in range(grid_width)]
                
            # Special case: If 4 rows, count as a Tetris
            if len(complete_rows) == 4:
                self.tetris_game.metrics['tetris_clears'] += 1
                
        return complete_rows
    
    def set_learning_enabled(self, enabled):
        """Toggle learning mode."""
        self.learning_enabled = enabled
        return self.learning_enabled
    
    def set_use_expectimax(self, enabled):
        """Toggle Expectimax planning."""
        self.use_expectimax = enabled
        return self.use_expectimax
    
    def set_planning_depth(self, depth):
        """Set the planning depth."""
        self.planning_depth = max(0, min(5, depth))  # Clamp between 0 and 5
        return self.planning_depth
    
    def get_metrics(self):
        """
        Get performance metrics for the integration.
        
        Returns:
            Dict with performance metrics
        """
        return {
            'success_rate': self.success_rate,
            'planning_depth': self.planning_depth,
            'learning_enabled': self.learning_enabled,
            'use_expectimax': self.use_expectimax,
            'tetris_game_metrics': self.tetris_game.metrics
        }