# app/controllers/tetris_ai_controller.py
import random
import math
import numpy as np
from app.models.tetris_piece import TetrisPiece

class TetrisAIController:
    """
    AI controller for Tetris game using Minimax algorithm.
    Controls both Tetris pieces and programmable matter elements.
    """
    
    def __init__(self, game_controller, pm_integration=None):
        """
        Initialize the AI controller.
        
        Args:
            game_controller: The TetrisGameController instance
            pm_integration: Optional TetrisPMIntegration instance for programmable matter
        """
        self.game = game_controller
        self.pm_integration = pm_integration
        
        # AI parameters
        self.search_depth = 3  # Default depth for minimax search
        self.use_expectimax = False  # Whether to use expectimax instead of minimax
        self.learning_enabled = False  # Whether to use learning to improve decisions
        
        # Evaluation weights
        self.weights = {
            'height': -0.510066,  # Weight for cumulative height
            'lines': 0.760666,    # Weight for completed lines
            'holes': -0.35663,    # Weight for holes in the grid
            'bumpiness': -0.184483, # Weight for bumpiness/contour
            'clear_potential': 0.4, # Weight for potential line clears
            'pm_support': 0.6,    # Weight for programmable matter support
            'well_depth': 0.25,   # Weight for well formations
            'blockage': -0.5      # Weight for blockage of PM access to rows
        }
        
        # Decision history for learning
        self.decision_history = []
        self.feature_history = []
        self.result_history = []
        
        # For visualization and debugging
        self.evaluated_states = []
        self.decision_tree = {}
        self.current_decision_path = []
        
        # Log for decisions
        self.log = []
    
    def update(self):
        """Update the AI controller, make decisions and execute them."""
        if not self.game.active or self.game.gameOver or self.game.paused:
            return
        
        # If no current piece, wait for next update
        if not self.game.currentPiece:
            return
        
        # Clear previous state tracking
        self.evaluated_states = []
        self.current_decision_path = []
        
        # Make a decision with the current piece
        self.make_decision()
        
        # If programmable matter integration is enabled, update it
        if self.pm_integration:
            self.update_programmable_matter()
    
    def make_decision(self):
        """Make a decision for the current piece using minimax."""
        current_piece = self.game.currentPiece
        if not current_piece:
            return
        
        # Get all possible placements for the current piece
        possible_placements = self.get_possible_placements(current_piece)
        
        # Calculate the best placement
        best_placement = self.find_best_placement(possible_placements)
        
        if best_placement:
            # Extract the target position and rotation
            target_x, target_rotation = best_placement
            
            # Execute the move
            self.execute_move(target_x, target_rotation)
            
            # Log the decision
            self.log.append(f"Placed {current_piece.shape_type} at x={target_x}, rotation={target_rotation}")
    
    def get_possible_placements(self, piece):
        """
        Get all possible valid placements for a piece.
        
        Returns:
            List of tuples (x, rotation) representing valid placements
        """
        valid_placements = []
        
        # For each rotation
        for rotation in range(len(TetrisPiece.SHAPES[piece.shape_type])):
            # Test all possible x positions
            # Fix: Use len() instead of .length property
            for x in range(-2, len(self.game.board[0]) + 2):  # Allow some overhang
                # Create a test piece with this rotation and position
                test_piece = {
                    'type': piece.shape_type,
                    'rotation': rotation,
                    'x': x,
                    'y': 0  # Start at top
                }
                
                # Drop the piece to find the final y position
                drop_result = self.simulate_drop(test_piece)
                
                if drop_result['valid']:
                    # Valid placement found
                    valid_placements.append((x, rotation))
        
        return valid_placements
    
    def simulate_drop(self, piece):
        """
        Simulate dropping a piece to find its final position.
        
        Args:
            piece: Dictionary with piece parameters (type, rotation, x, y)
            
        Returns:
            Dictionary with drop result information
        """
        # Get the shape for this piece and rotation
        shape = TetrisPiece.SHAPES[piece['type']][piece['rotation']]
        
        # Start from current y and drop down
        y = piece['y']
        valid = True
        landed = False
        
        while not landed and valid:
            # Check if the piece can move down one more row
            new_y = y + 1
            
            # Get block positions at new position
            blocks = [(piece['x'] + block[0], new_y + block[1]) for block in shape]
            
            # Check for collisions
            if self.check_collision(blocks):
                landed = True  # Piece has landed
            else:
                y = new_y  # Continue dropping
        
        # Final position blocks
        final_blocks = [(piece['x'] + block[0], y + block[1]) for block in shape]
        
        # Check if this is a valid final position
        valid = not self.check_collision(final_blocks)
        
        return {
            'valid': valid,
            'y': y,
            'blocks': final_blocks if valid else None
        }
    
    def check_collision(self, blocks):
        """
        Check if the blocks collide with the board boundaries or existing blocks.
        
        Args:
            blocks: List of (x, y) positions to check
            
        Returns:
            True if there is a collision, False otherwise
        """
        for x, y in blocks:
            # Check boundaries
            if x < 0 or x >= len(self.game.board[0]) or y >= len(self.game.board):
                return True
                
            # Check collision with existing blocks (only if y is valid)
            if y >= 0 and self.game.board[y][x] is not None:
                return True
                
        return False
    
    def find_best_placement(self, possible_placements):
        """
        Find the best placement using minimax or expectimax algorithm.
        
        Args:
            possible_placements: List of valid (x, rotation) placements
            
        Returns:
            Tuple (x, rotation) of the best placement
        """
        if not possible_placements:
            return None
            
        best_placement = None
        best_score = float('-inf')
        
        for placement in possible_placements:
            x, rotation = placement
            
            # Create a copy of the game state for simulation
            test_state = self.clone_game_state()
            
            # Simulate placing the piece
            piece_result = self.simulate_placement(test_state, x, rotation)
            
            if not piece_result['valid']:
                continue
            
            # If using expectimax with search_depth > 1, look ahead
            if self.use_expectimax and self.search_depth > 1:
                # Calculate score using expectimax
                score = self.expectimax(test_state, self.search_depth - 1, False)
            elif self.search_depth > 1:
                # Calculate score using minimax
                score = self.minimax(test_state, self.search_depth - 1, float('-inf'), float('inf'), False)
            else:
                # Just evaluate the immediate result
                score = self.evaluate_state(test_state)
            
            # Add state to evaluated states for visualization
            self.evaluated_states.append({
                'placement': placement,
                'score': score,
                'state': test_state
            })
            
            # Update best placement if this is better
            if score > best_score:
                best_score = score
                best_placement = placement
        
        return best_placement
    
    def minimax(self, state, depth, alpha, beta, is_maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            state: The game state to evaluate
            depth: Current search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            is_maximizing: Whether this is a maximizing node
            
        Returns:
            Score of the best move
        """
        # Terminal conditions
        if depth == 0 or state['game_over']:
            return self.evaluate_state(state)
        
        if is_maximizing:
            # Maximizing player (AI placing pieces optimally)
            max_eval = float('-inf')
            current_piece = state['current_piece']
            
            # Get all possible placements
            placements = self.get_possible_placements_for_state(state, current_piece)
            
            for placement in placements:
                x, rotation = placement
                
                # Clone state and simulate placement
                next_state = self.clone_state(state)
                placement_result = self.simulate_placement(next_state, x, rotation)
                
                if not placement_result['valid']:
                    continue
                
                # Recursive evaluation
                eval = self.minimax(next_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                
                # Alpha-beta pruning
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
                    
            return max_eval
            
        else:
            # Minimizing player (worst case next pieces)
            min_eval = float('inf')
            
            # Get potential next pieces (all possible piece types)
            next_pieces = list(TetrisPiece.SHAPES.keys())
            
            for piece_type in next_pieces:
                # Clone state and set next piece
                next_state = self.clone_state(state)
                next_state['next_piece'] = piece_type
                next_state['current_piece'] = piece_type
                
                # Recursive evaluation
                eval = self.minimax(next_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                
                # Alpha-beta pruning
                beta = min(beta, eval)
                if beta <= alpha:
                    break
                    
            return min_eval
    
    def expectimax(self, state, depth, is_maximizing):
        """
        Expectimax algorithm for handling uncertainty.
        
        Args:
            state: The game state to evaluate
            depth: Current search depth
            is_maximizing: Whether this is a maximizing node
            
        Returns:
            Score of the best move
        """
        # Terminal conditions
        if depth == 0 or state['game_over']:
            return self.evaluate_state(state)
        
        if is_maximizing:
            # Maximizing player (AI placing pieces optimally)
            max_eval = float('-inf')
            current_piece = state['current_piece']
            
            # Get all possible placements
            placements = self.get_possible_placements_for_state(state, current_piece)
            
            for placement in placements:
                x, rotation = placement
                
                # Clone state and simulate placement
                next_state = self.clone_state(state)
                placement_result = self.simulate_placement(next_state, x, rotation)
                
                if not placement_result['valid']:
                    continue
                
                # Recursive evaluation
                eval = self.expectimax(next_state, depth - 1, False)
                max_eval = max(max_eval, eval)
                    
            return max_eval
            
        else:
            # Chance node (random next pieces)
            next_pieces = list(TetrisPiece.SHAPES.keys())
            expected_value = 0
            
            # All piece types are equally likely
            probability = 1.0 / len(next_pieces)
            
            for piece_type in next_pieces:
                # Clone state and set next piece
                next_state = self.clone_state(state)
                next_state['next_piece'] = piece_type
                next_state['current_piece'] = piece_type
                
                # Recursive evaluation
                eval = self.expectimax(next_state, depth - 1, True)
                expected_value += probability * eval
                    
            return expected_value
    
    def evaluate_state(self, state):
        """
        Evaluate a game state based on multiple features.
        
        Args:
            state: The game state to evaluate
            
        Returns:
            Numerical score representing the quality of the state
        """
        # Extract the board from the state
        board = state['board']
        
        # Calculate features
        features = {}
        
        # Aggregate height - sum of heights of each column
        heights = self.get_column_heights(board)
        features['height'] = sum(heights)
        
        # Number of complete lines
        features['lines'] = self.count_complete_lines(board)
        
        # Number of holes (empty cells with a block above them)
        features['holes'] = self.count_holes(board, heights)
        
        # Bumpiness - sum of differences between adjacent column heights
        features['bumpiness'] = sum(abs(heights[i] - heights[i+1]) for i in range(len(heights)-1))
        
        # Potential for line clears
        features['clear_potential'] = self.calculate_clear_potential(board)
        
        # Programmable matter support - check for PM elements supporting structure
        features['pm_support'] = self.evaluate_pm_support(state)
        
        # Well formation - encourages formations that enable Tetris clears
        features['well_depth'] = self.calculate_well_depth(heights)
        
        # Blockage - penalizes configurations that block PM access to rows
        features['blockage'] = self.calculate_pm_blockage(board)
        
        # Calculate weighted sum
        score = sum(self.weights[feature] * value for feature, value in features.items())
        
        # Store features for learning
        self.feature_history.append(features)
        
        return score
    
    def get_column_heights(self, board):
        """Calculate the height of each column."""
        heights = []
        for x in range(len(board[0])):
            for y in range(len(board)):
                if board[y][x] is not None:
                    heights.append(len(board) - y)
                    break
            else:
                heights.append(0)  # Empty column
        return heights
    
    def count_complete_lines(self, board):
        """Count the number of complete lines."""
        return sum(1 for row in board if all(cell is not None for cell in row))
    
    def count_holes(self, board, heights):
        """Count the number of holes in the board."""
        holes = 0
        for x in range(len(board[0])):
            top = len(board) - heights[x]  # Convert height to board index
            for y in range(top + 1, len(board)):
                if board[y][x] is None:
                    holes += 1
        return holes
    
    def calculate_clear_potential(self, board):
        """Calculate the potential for clearing lines."""
        potential = 0
        for y in range(len(board)):
            filled_cells = sum(1 for cell in board[y] if cell is not None)
            # More points for rows that are nearly complete
            if filled_cells >= len(board[0]) - 2:
                potential += filled_cells / len(board[0])
        return potential
    
    def evaluate_pm_support(self, state):
        """
        Evaluate how well programmable matter elements are supporting the structure.
        """
        if not self.pm_integration:
            return 0
            
        # This would be implemented based on the specifics of PM integration
        # For now, return a placeholder value
        return 0
    
    def calculate_well_depth(self, heights):
        """
        Calculate the depth of wells in the board.
        A well is a column with adjacent columns much higher.
        """
        well_depth = 0
        for i in range(len(heights)):
            # Check left and right neighbors
            left = heights[i-1] if i > 0 else 0
            right = heights[i+1] if i < len(heights)-1 else 0
            
            # If both neighbors are higher by at least 3, consider it a well
            if left >= heights[i] + 3 and right >= heights[i] + 3:
                well_depth += (left + right) / 2 - heights[i]
                
        return well_depth
    
    def calculate_pm_blockage(self, board):
        """
        Calculate how much the current board configuration blocks
        programmable matter elements from accessing rows.
        """
        blockage = 0
        
        # If there's no PM integration, return 0
        if not self.pm_integration:
            return blockage
            
        # Count the number of holes that are inaccessible to PM
        # This would be implemented based on PM integration
        
        return blockage
    
    def execute_move(self, target_x, target_rotation):
        """
        Execute the move to place the current piece at the target position and rotation.
        
        Args:
            target_x: Target x-coordinate
            target_rotation: Target rotation
        """
        if not self.game.currentPiece:
            return
            
        # Get current piece state
        current_x = self.game.currentPiece.x
        current_rotation = self.game.currentPiece.rotation
        
        # First, rotate to the target rotation
        while current_rotation != target_rotation:
            self.game.rotatePiece()
            current_rotation = (current_rotation + 1) % len(TetrisPiece.SHAPES[self.game.currentPiece.shape_type])
        
        # Then, move to the target x position
        dx = target_x - current_x
        if dx < 0:
            # Move left
            for _ in range(-dx):
                self.game.moveCurrentPiece(-1, 0)
        elif dx > 0:
            # Move right
            for _ in range(dx):
                self.game.moveCurrentPiece(1, 0)
        
        # Finally, hard drop the piece
        self.game.hardDrop()
    
    def update_programmable_matter(self):
        """Update programmable matter elements based on the current game state."""
        if not self.pm_integration:
            return
            
        # This would interact with the PM integration system
        # For example, calculating target positions for PM elements
    
    def clone_game_state(self):
        """Create a copy of the current game state for simulation."""
        # Clone the board
        board_copy = []
        for row in self.game.board:
            board_copy.append(row.copy())
            
        # Create state dictionary
        state = {
            'board': board_copy,
            'current_piece': self.game.currentPiece.shape_type if self.game.currentPiece else None,
            'next_piece': self.game.nextPiece,
            'score': self.game.score,
            'lines': self.game.lines,
            'level': self.game.level,
            'game_over': self.game.gameOver
        }
        
        return state
    
    def clone_state(self, state):
        """Create a deep copy of a game state."""
        # Clone the board
        board_copy = []
        for row in state['board']:
            board_copy.append(row.copy())
            
        # Create new state dictionary
        new_state = {
            'board': board_copy,
            'current_piece': state['current_piece'],
            'next_piece': state['next_piece'],
            'score': state['score'],
            'lines': state['lines'],
            'level': state['level'],
            'game_over': state['game_over']
        }
        
        return new_state
    
    def get_possible_placements_for_state(self, state, piece_type):
        """Get possible placements for a state and piece type."""
        # This is a simplified version for the state-based minimax
        possible_placements = []
        
        # For each rotation
        for rotation in range(len(TetrisPiece.SHAPES[piece_type])):
            # Try each x position
            for x in range(-2, len(state['board'][0]) + 2):
                possible_placements.append((x, rotation))
                
        return possible_placements
    
    def simulate_placement(self, state, x, rotation):
        """
        Simulate placing a piece in the given state.
        
        Args:
            state: Game state to modify
            x: Target x-coordinate
            rotation: Target rotation
            
        Returns:
            Dictionary with placement result
        """
        # This is a simplified version for the state-based minimax
        # In a real implementation, this would simulate the piece drop
        # and update the state accordingly
        
        # For now, just return a placeholder result
        return {
            'valid': True,
            'lines_cleared': 0,
            'score_increase': 0
        }
    
    def update_weights_from_learning(self):
        """Update evaluation weights based on learning from previous games."""
        if not self.learning_enabled or len(self.result_history) < 10:
            return
            
        # This would implement a learning algorithm to adjust weights
        # based on the history of decisions and their outcomes
        
        # For example, simple gradient descent based on game scores
        learning_rate = 0.01
        
        # Calculate weight adjustments based on correlations with results
        for feature, weight in self.weights.items():
            # Calculate correlation between feature values and results
            feature_values = [features[feature] for features in self.feature_history]
            correlation = self.calculate_correlation(feature_values, self.result_history)
            
            # Adjust weight based on correlation
            self.weights[feature] += learning_rate * correlation
    
    def calculate_correlation(self, x, y):
        """Calculate correlation between two lists of values."""
        if len(x) != len(y):
            return 0
            
        n = len(x)
        if n == 0:
            return 0
            
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        variance_x = sum((xi - mean_x) ** 2 for xi in x) / n
        variance_y = sum((yi - mean_y) ** 2 for yi in y) / n
        
        if variance_x == 0 or variance_y == 0:
            return 0
            
        covariance = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
        
        return covariance / (math.sqrt(variance_x) * math.sqrt(variance_y))
    
    def get_visualization_data(self):
        """
        Get data for visualizing the AI's decision-making process.
        
        Returns:
            Dictionary with visualization data
        """
        return {
            'evaluated_states': self.evaluated_states,
            'decision_path': self.current_decision_path,
            'log': self.log[-10:] if len(self.log) > 10 else self.log
        }