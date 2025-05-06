# app/controllers/tetris_ai_integration.py
import time
import random
import numpy as np
from app.controllers.tetris_ai_controller import TetrisAIController

class TetrisAIIntegration:
    """
    Integration layer between AI-driven Tetris game and programmable matter simulation.
    Replaces manual controls with AI decision-making.
    """
    
    def __init__(self, tetris_game, simulation=None):
        """
        Initialize the AI integration.
        
        Args:
            tetris_game: The TetrisGameController instance
            simulation: Reference to the ProgrammableMatterSimulation (optional)
        """
        self.tetris_game = tetris_game
        self.simulation = simulation
        
        # Create AI controller
        self.ai_controller = TetrisAIController(tetris_game, self)
        
        # Programmable matter configuration
        self.pm_elements = []  # List of active PM elements
        self.target_positions = []  # Current target positions
        self.update_interval = 0.2  # Seconds between updates
        self.last_update_time = 0
        
        # AI parameters (can be adjusted through UI)
        self.planning_depth = 3
        self.use_expectimax = False
        self.learning_enabled = False
        
        # Performance metrics
        self.metrics = {
            'decisions_made': 0,
            'lines_cleared': 0,
            'pm_utilization': 0.0,
            'average_decision_time': 0.0,
            'total_score': 0
        }
        
        # Visualization data
        self.visualization_enabled = True
        self.decision_visualization = []
        self.pm_movement_visualization = []
        
        # Initialize the PM simulation if available
        if self.simulation:
            self._initialize_pm_elements()
    
    def update(self, current_time):
        """
        Update the integration layer. Should be called on each game loop iteration.
        
        Args:
            current_time: Current game time
            
        Returns:
            Dict with update information
        """
        if self.tetris_game.paused or self.tetris_game.gameOver:
            return {'action': 'none'}
        
        # Update AI parameters from game settings
        self._update_ai_parameters()
        
        # Only update at specified interval
        if current_time - self.last_update_time < self.update_interval:
            return {'action': 'none'}
        
        self.last_update_time = current_time
        
        # Start timing for performance metrics
        decision_start_time = time.time()
        
        # Let the AI controller make decisions
        self.ai_controller.update()
        
        # Update decision time metrics
        decision_time = time.time() - decision_start_time
        self._update_metrics('average_decision_time', decision_time)
        
        # Update PM target positions based on current game state
        self._update_target_positions()
        
        # Plan and execute PM movements
        move_result = self._plan_and_execute_pm_moves()
        
        # Gather visualization data
        if self.visualization_enabled:
            self._update_visualization()
        
        return {
            'action': 'ai_update',
            'decisions': self.ai_controller.get_visualization_data(),
            'pm_moves': move_result.get('moves', [])
        }
    
    def _update_ai_parameters(self):
        """Update AI controller parameters from game settings."""
        # Check if parameters have changed
        if self.planning_depth != self.ai_controller.search_depth:
            self.ai_controller.search_depth = self.planning_depth
            
        if self.use_expectimax != self.ai_controller.use_expectimax:
            self.ai_controller.use_expectimax = self.use_expectimax
            
        if self.learning_enabled != self.ai_controller.learning_enabled:
            self.ai_controller.learning_enabled = self.learning_enabled
    
    def _initialize_pm_elements(self):
        """Initialize programmable matter elements for the simulation."""
        if not self.simulation:
            return
            
        # Clear existing elements
        self.simulation.reset()
        
        # Create new elements (using 8 by default)
        num_elements = 8
        self.simulation.initialize_elements(num_elements)
        
        # Store reference to PM elements
        self.pm_elements = list(self.simulation.controller.elements.values())
        
        print(f"Initialized {len(self.pm_elements)} programmable matter elements")
    
    def _update_target_positions(self):
        """
        Update target positions for programmable matter elements
        based on the current Tetris game state.
        """
        if not self.simulation or not self.pm_elements:
            return
            
        # Clear previous targets
        self.target_positions = []
        
        # Get the current Tetris board state
        board = self.tetris_game.board
        
        # Strategy 1: Position under falling piece and fill gaps
        self._add_current_piece_targets()
        
        # Strategy 2: Fill holes in the structure
        self._add_hole_filling_targets()
        
        # Strategy 3: Create support structures
        self._add_support_structure_targets()
        
        # Set the targets in the simulation
        if self.target_positions:
            self.simulation.controller.set_target_positions(self.target_positions)
            self.simulation.controller.assign_targets()
            
            # Update metrics based on target assignment
            self._update_pm_metrics()
    
    def _add_current_piece_targets(self):
        """Add targets to position under the current falling piece."""
        current_piece = self.tetris_game.currentPiece
        shadow_positions = None
        
        # If visualization data is available, get shadow positions
        if hasattr(self.tetris_game, 'get_shadow_positions'):
            shadow_positions = self.tetris_game.get_shadow_positions()
        elif current_piece:
            # Approximate shadow positions based on current piece
            shadow_positions = []
            # Find the lowest possible position for the current piece
            max_y = len(self.tetris_game.board)
            
            # Clone the piece for simulation
            test_y = current_piece.y
            while test_y < max_y:
                # Test if piece can move down
                can_move_down = True
                blocks = [(current_piece.x + dx, test_y + 1 + dy) 
                        for dx, dy in current_piece.get_current_shape()]
                
                for x, y in blocks:
                    if (y >= max_y or 
                        (y >= 0 and x >= 0 and x < len(self.tetris_game.board[0]) and 
                         self.tetris_game.board[y][x] is not None)):
                        can_move_down = False
                        break
                
                if not can_move_down:
                    break
                    
                test_y += 1
            
            # Set shadow positions at the final test_y
            shadow_positions = [(current_piece.x + dx, test_y + dy) 
                            for dx, dy in current_piece.get_current_shape()]
        
        if shadow_positions:
            # Add positions below the shadow (landing) positions
            for x, y in shadow_positions:
                # Check if position below is empty and valid
                if (y + 1 < len(self.tetris_game.board) and 
                    x >= 0 and x < len(self.tetris_game.board[0]) and
                    self.tetris_game.board[y + 1][x] is None):
                    self.target_positions.append((x, y + 1))
    
    def _add_hole_filling_targets(self):
        """Add targets to fill holes in the Tetris structure."""
        board = self.tetris_game.board
        
        # Look for holes (empty cells with non-empty cells above)
        for y in range(len(board) - 2, 0, -1):  # Skip bottom row
            for x in range(len(board[y])):
                if board[y][x] is None:
                    # Check if there's any block above
                    has_block_above = False
                    for check_y in range(y - 1, -1, -1):
                        if board[check_y][x] is not None:
                            has_block_above = True
                            break
                    
                    # If there's a block above, this is a hole - target it
                    if has_block_above:
                        self.target_positions.append((x, y))
    
    def _add_support_structure_targets(self):
        """Add targets to create support structures for stability."""
        board = self.tetris_game.board
        
        # Find columns with high gaps that need support
        column_heights = []
        for x in range(len(board[0])):
            # Find the highest block in this column
            for y in range(len(board)):
                if board[y][x] is not None:
                    column_heights.append((x, len(board) - y))
                    break
            else:
                column_heights.append((x, 0))
        
        # Look for significant height differences between adjacent columns
        for i in range(len(column_heights) - 1):
            x1, h1 = column_heights[i]
            x2, h2 = column_heights[i + 1]
            
            # If height difference is more than 3, add support
            if abs(h1 - h2) > 3:
                # Target the higher column's bottom
                higher_col = x1 if h1 > h2 else x2
                higher_height = max(h1, h2)
                
                # Calculate the position to provide support
                support_y = len(board) - higher_height + 2  # +2 to be slightly below
                
                if 0 <= support_y < len(board) and board[support_y][higher_col] is None:
                    self.target_positions.append((higher_col, support_y))
    
    def _plan_and_execute_pm_moves(self):
        """
        Plan and execute movements for programmable matter elements.
        
        Returns:
            Dict with move results
        """
        if not self.simulation:
            return {'moves': []}
        
        # Execute a transformation using the appropriate algorithm
        algorithm = "astar"  # Default algorithm
        
        # Use more advanced algorithms when AI is using deeper search
        if self.planning_depth >= 3:
            algorithm = "minimax" if not self.use_expectimax else "expectimax"
        
        # Execute the transformation
        result = self.simulation.transform(
            algorithm=algorithm,
            topology="moore",  # Use Moore for more flexibility
            movement="parallel",  # Use parallel for faster adaptation
            control_mode="centralized"  # Use centralized for better coordination
        )
        
        # Update PM metrics based on the transformation
        self._update_pm_metrics()
        
        return result
    
    def _update_pm_metrics(self):
        """Update PM-related metrics."""
        if not self.simulation or not self.simulation.controller.elements:
            return
        
        # Calculate PM utilization (percentage of elements at targets)
        elements_with_targets = sum(1 for e in self.simulation.controller.elements.values() 
                              if e.has_target())
        
        elements_at_targets = sum(1 for e in self.simulation.controller.elements.values() 
                             if e.has_target() and e.x == e.target_x and e.y == e.target_y)
        
        if elements_with_targets > 0:
            pm_utilization = elements_at_targets / elements_with_targets
        else:
            pm_utilization = 0.0
            
        self._update_metrics('pm_utilization', pm_utilization)
    
    def _update_metrics(self, metric_name, value):
        """Update a specific metric, potentially with smoothing."""
        if metric_name == 'average_decision_time':
            # Use exponential moving average for time metrics
            alpha = 0.1  # Smoothing factor
            current_val = self.metrics[metric_name]
            self.metrics[metric_name] = (alpha * value) + ((1 - alpha) * current_val)
        else:
            # For other metrics, just set the value
            self.metrics[metric_name] = value
            
        # Track total lines cleared
        if metric_name == 'lines_cleared':
            self.metrics['total_lines_cleared'] = self.metrics.get('total_lines_cleared', 0) + value
            
        # Track decisions
        if metric_name == 'decisions_made':
            self.metrics['decisions_made'] = self.metrics.get('decisions_made', 0) + 1
    
    def _update_visualization(self):
        """Update visualization data for UI rendering."""
        # Get AI controller visualization data
        ai_viz_data = self.ai_controller.get_visualization_data()
        
        # Store for rendering
        self.decision_visualization = ai_viz_data
        
        # Update PM movement visualization
        if self.simulation:
            # Get current PM element positions
            pm_positions = [(e.id, e.x, e.y, e.has_target() and e.target_x == e.x and e.target_y == e.y) 
                         for e in self.simulation.controller.elements.values()]
            
            self.pm_movement_visualization = {
                'positions': pm_positions,
                'targets': [(e.id, e.target_x, e.target_y) 
                         for e in self.simulation.controller.elements.values() 
                         if e.has_target()]
            }
    
    def get_visualization_data(self):
        """
        Get data for visualization.
        
        Returns:
            Dict with visualization data
        """
        return {
            'ai_decisions': self.decision_visualization,
            'pm_movements': self.pm_movement_visualization,
            'metrics': self.metrics
        }
    
    def toggle_ai_mode(self, mode):
        """
        Toggle between different AI modes.
        
        Args:
            mode: AI mode ("minimax", "expectimax", "adaptive")
            
        Returns:
            Current mode after toggle
        """
        if mode == "expectimax":
            self.use_expectimax = True
            self.planning_depth = 3
        elif mode == "minimax":
            self.use_expectimax = False
            self.planning_depth = 3
        elif mode == "adaptive":
            # Adaptive mode switches between algorithms based on game state
            self.planning_depth = 2  # Lower depth for faster decisions
            # Will alternate between minimax and expectimax based on situation
            
        # Update the controller
        self._update_ai_parameters()
        
        return mode
    
    def set_planning_depth(self, depth):
        """Set the AI planning depth."""
        self.planning_depth = max(1, min(5, depth))  # Clamp between 1 and 5
        self._update_ai_parameters()
        return self.planning_depth
    
    def toggle_learning(self, enabled):
        """Toggle learning capability."""
        self.learning_enabled = enabled
        self._update_ai_parameters()
        return self.learning_enabled