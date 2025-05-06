# app/controllers/tetris_ai_game_controller.py
import time
import random
from app.models.tetris_piece import TetrisPiece
from app.controllers.tetris_ai_integration import TetrisAIIntegration

class TetrisAIGameController:
    """
    AI-driven Tetris game controller with programmable matter integration.
    This controller manages the game state and delegates decisions to an AI.
    """
    
    def __init__(self, simulation=None):
        """
        Initialize the AI-driven Tetris game.
        
        Args:
            simulation: Optional ProgrammableMatterSimulation instance
        """
        # Create the game board (10x20 grid)
        self.width = 10
        self.height = 20
        self.board = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        # Game state
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.gameOver = False
        self.start_time = None
        self.elapsed_time = 0
        
        # Pieces
        self.currentPiece = None
        self.nextPiece = None
        self.heldPiece = None
        self.holdUsed = False  # Can only hold once per piece
        
        # Timing control
        self.lastDropTime = 0
        self.dropInterval = self._calculate_drop_interval()
        self.lastFrameTime = 0
        self.active = False
        
        # Initialize AI integration
        self.ai_integration = TetrisAIIntegration(self, simulation)
        
        # Performance metrics
        self.metrics = {
            'pieces_placed': 0,
            'tetris_clears': 0,
            'total_moves': 0,
            'ai_decisions': 0,
            'pm_elements_utilized': 0
        }
        
        # Visualization options
        self.show_ai_thinking = True
        self.show_pm_targets = True
        self.ai_decision_history = []
        
        # Set to true when game is running
        self.active = False
    
    def start_game(self):
        """Start a new Tetris game."""
        # Reset game state
        self.board = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.gameOver = False
        
        # Reset metrics
        self.metrics = {key: 0 for key in self.metrics}
        
        # Generate first pieces
        self.nextPiece = self._generate_random_piece()
        self._spawn_piece()
        
        # Set timing
        self.start_time = time.time()
        self.lastDropTime = time.time()
        self.lastFrameTime = time.time()
        
        # Set active
        self.active = True
        
        return True
    
    def update(self, current_time):
        """
        Update the game state. Called on each game loop iteration.
        
        Args:
            current_time: Current time from time.time()
            
        Returns:
            Dict with game state update information
        """
        if not self.active or self.paused or self.gameOver:
            return {'action': 'none'}
        
        # Calculate delta time
        delta_time = current_time - self.lastFrameTime
        self.lastFrameTime = current_time
        
        # Update the AI integration
        ai_update = self.ai_integration.update(current_time)
        
        # Drop piece automatically based on level
        if current_time - self.lastDropTime >= self.dropInterval:
            self.lastDropTime = current_time
            drop_result = self._drop_piece()
            
            # If the piece was locked, update metrics
            if drop_result.get('action') == 'lock_piece':
                self.metrics['pieces_placed'] += 1
                
                # If lines were cleared, update metrics
                lines_cleared = drop_result.get('lines_cleared', 0)
                if lines_cleared > 0:
                    self.metrics['lines_cleared'] = self.metrics.get('lines_cleared', 0) + lines_cleared
                    
                    # If tetris (4 lines), update metric
                    if lines_cleared == 4:
                        self.metrics['tetris_clears'] += 1
        
        # Combine AI update with game state update
        return {
            'action': 'update',
            'game_state': self.get_game_state(),
            'ai_update': ai_update
        }
    
    def _drop_piece(self):
        """
        Move the current piece down one row.
        
        Returns:
            Dict with result of the drop action
        """
        if not self.currentPiece or self.gameOver:
            return {'action': 'none'}
        
        # Try to move down
        new_positions = self.currentPiece.move(0, 1)
        
        # Check for collision
        if self._check_collision(new_positions):
            # Move piece back up
            self.currentPiece.move(0, -1)
            
            # Lock the piece
            self._lock_piece()
            
            # Check for completed lines
            lines_cleared = self._check_lines()
            
            # Update score based on cleared lines
            if lines_cleared > 0:
                self._update_score(lines_cleared)
            
            # Spawn new piece
            if not self._spawn_piece():
                self.gameOver = True
                return {'action': 'game_over', 'score': self.score}
            
            return {
                'action': 'lock_piece',
                'lines_cleared': lines_cleared,
                'next_piece': self.nextPiece.shape_type if self.nextPiece else None
            }
        
        return {'action': 'drop'}
    
    def _lock_piece(self):
        """Lock the current piece into the board."""
        if not self.currentPiece:
            return
        
        # Get piece positions
        positions = self.currentPiece.get_positions()
        
        # Add to board
        for x, y in positions:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.board[y][x] = self.currentPiece.shape_type
        
        # Reset current piece
        self.currentPiece = None
        
        # Reset hold used flag
        self.holdUsed = False
    
    def _check_lines(self):
        """
        Check for and clear completed lines.
        
        Returns:
            Number of lines cleared
        """
        lines_cleared = 0
        
        # Check each row from bottom to top
        for y in range(self.height - 1, -1, -1):
            # Check if row is full
            if all(cell is not None for cell in self.board[y]):
                lines_cleared += 1
                
                # Clear this row and shift rows down
                for row in range(y, 0, -1):
                    self.board[row] = self.board[row - 1].copy()
                
                # Clear top row
                self.board[0] = [None for _ in range(self.width)]
        
        # Update lines count and level
        if lines_cleared > 0:
            self.lines += lines_cleared
            
            # Update level (every 10 lines)
            new_level = (self.lines // 10) + 1
            if new_level > self.level:
                self.level = new_level
                self.dropInterval = self._calculate_drop_interval()
        
        return lines_cleared
    
    def _update_score(self, lines_cleared):
        """
        Update score based on lines cleared and level.
        
        Args:
            lines_cleared: Number of lines cleared
        """
        # Classic NES Tetris scoring
        points = {
            1: 40,
            2: 100,
            3: 300,
            4: 1200  # Tetris!
        }
        
        if lines_cleared in points:
            self.score += points[lines_cleared] * self.level
    
    def _spawn_piece(self):
        """
        Spawn a new piece at the top of the board.
        
        Returns:
            Boolean indicating success
        """
        # Use next piece as current piece
        if not self.nextPiece:
            self.nextPiece = self._generate_random_piece()
        
        self.currentPiece = self.nextPiece
        
        # Generate new next piece
        self.nextPiece = self._generate_random_piece()
        
        # Check if spawn position is valid
        if self._check_collision(self.currentPiece.get_positions()):
            # Game over condition
            return False
        
        return True
    
    def _generate_random_piece(self):
        """
        Generate a random Tetris piece.
        
        Returns:
            TetrisPiece instance
        """
        shape_type = random.choice(list(TetrisPiece.SHAPES.keys()))
        return TetrisPiece(shape_type, self.width)
    
    def _check_collision(self, positions):
        """
        Check if positions collide with the board or existing pieces.
        
        Args:
            positions: List of (x, y) positions
            
        Returns:
            Boolean indicating collision
        """
        for x, y in positions:
            # Check boundaries
            if x < 0 or x >= self.width or y >= self.height:
                return True
            
            # Check collision with existing pieces (only if y is on board)
            if y >= 0 and self.board[y][x] is not None:
                return True
        
        return False
    
    def _calculate_drop_interval(self):
        """
        Calculate the drop interval based on the current level.
        
        Returns:
            Drop interval in milliseconds
        """
        # Classic Tetris formula (frames per drop)
        frames_per_drop = max(1, int(48 - ((self.level - 1) * 5)))
        
        # Convert to seconds (assuming 60 FPS)
        return frames_per_drop / 60.0
    
    def moveCurrentPiece(self, dx, dy):
        """Move the current piece (used by AI controller)."""
        if not self.currentPiece or self.gameOver or self.paused:
            return False
        
        # Get new positions
        new_positions = self.currentPiece.move(dx, dy)
        
        # Check collision
        if self._check_collision(new_positions):
            # Move back if collision
            self.currentPiece.move(-dx, -dy)
            return False
        
        return True
    
    def rotatePiece(self, clockwise=True):
        """Rotate the current piece (used by AI controller)."""
        if not self.currentPiece or self.gameOver or self.paused:
            return False
        
        # Store original rotation
        original_rotation = self.currentPiece.rotation
        
        # Rotate
        new_positions = self.currentPiece.rotate(clockwise)
        
        # Check collision
        if self._check_collision(new_positions):
            # Try wall kicks (simple implementation)
            kicks = [
                (1, 0),   # Right
                (-1, 0),  # Left
                (0, -1),  # Up
                (2, 0),   # Far right
                (-2, 0)   # Far left
            ]
            
            success = False
            for dx, dy in kicks:
                # Move piece
                self.currentPiece.move(dx, dy)
                
                # Check if this position works
                if not self._check_collision(self.currentPiece.get_positions()):
                    success = True
                    break
                
                # Move back
                self.currentPiece.move(-dx, -dy)
            
            if not success:
                # Rotation failed, restore original rotation
                self.currentPiece.rotation = original_rotation
                return False
        
        return True
    
    def hardDrop(self):
        """Hard drop the current piece (used by AI controller)."""
        if not self.currentPiece or self.gameOver or self.paused:
            return 0
        
        drop_distance = 0
        
        # Keep moving down until collision
        while True:
            new_positions = self.currentPiece.move(0, 1)
            
            if self._check_collision(new_positions):
                # Move piece back up
                self.currentPiece.move(0, -1)
                break
            
            drop_distance += 1
        
        # Lock the piece
        self._lock_piece()
        
        # Check for completed lines
        lines_cleared = self._check_lines()
        
        if lines_cleared > 0:
            self._update_score(lines_cleared)
        
        # Spawn new piece
        if not self._spawn_piece():
            self.gameOver = True
        
        # Add bonus points for hard drop
        self.score += drop_distance * 2
        
        return drop_distance
    
    def holdPiece(self):
        """Hold the current piece (used by AI controller)."""
        if not self.currentPiece or self.holdUsed or self.gameOver or self.paused:
            return False
        
        current_type = self.currentPiece.shape_type
        
        if self.heldPiece:
            # Swap with held piece
            self._spawn_piece(self.heldPiece)
        else:
            # Just hold current piece and spawn next piece
            self._spawn_piece()
        
        self.heldPiece = current_type
        self.holdUsed = True
        
        return True
    
    def get_game_state(self):
        """
        Get the current game state.
        
        Returns:
            Dict with game state
        """
        # Calculate elapsed time
        if self.paused:
            total_time = self.elapsed_time
        else:
            total_time = self.elapsed_time + (time.time() - self.start_time)
        
        state = {
            'board': self.board,
            'current_piece': self.currentPiece.get_positions() if self.currentPiece else None,
            'current_piece_type': self.currentPiece.shape_type if self.currentPiece else None,
            'next_piece': self.nextPiece.shape_type if self.nextPiece else None,
            'held_piece': self.heldPiece,
            'level': self.level,
            'score': self.score,
            'lines': self.lines,
            'gameOver': self.gameOver,
            'paused': self.paused,
            'time': int(total_time),
            'metrics': self.metrics
        }
        
        # Add shadow position if there's a current piece
        if self.currentPiece:
            state['shadow_positions'] = self.get_shadow_positions()
        
        # Add AI thinking data if enabled
        if self.show_ai_thinking:
            state['ai_thinking'] = self.ai_integration.get_visualization_data()
        
        return state
    
    def get_shadow_positions(self):
        """
        Get the shadow positions of the current piece.
        
        Returns:
            List of (x, y) positions where the shadow would be
        """
        if not self.currentPiece:
            return []
        
        # Clone the current piece
        shape_type = self.currentPiece.shape_type
        rotation = self.currentPiece.rotation
        x = self.currentPiece.x
        y = self.currentPiece.y
        
        # Drop the piece down
        shadow_y = y
        while shadow_y < self.height:
            # Get positions at this y
            positions = []
            shape = TetrisPiece.SHAPES[shape_type][rotation]
            for dx, dy in shape:
                positions.append((x + dx, shadow_y + 1 + dy))
            
            # Check for collision
            if self._check_collision(positions):
                break
            
            shadow_y += 1
        
        # Get final shadow positions
        shadow_positions = []
        shape = TetrisPiece.SHAPES[shape_type][rotation]
        for dx, dy in shape:
            shadow_positions.append((x + dx, shadow_y + dy))
        
        return shadow_positions
    
    def toggle_ai_mode(self, mode):
        """
        Toggle between different AI modes.
        
        Args:
            mode: AI mode ("minimax", "expectimax", "adaptive")
            
        Returns:
            Current mode after toggle
        """
        return self.ai_integration.toggle_ai_mode(mode)
    
    def set_planning_depth(self, depth):
        """Set the AI planning depth."""
        return self.ai_integration.set_planning_depth(depth)
    
    def toggle_visualization(self, enable):
        """Toggle AI visualization."""
        self.show_ai_thinking = enable
        return self.show_ai_thinking
    
    def set_pm_visualization(self, enable):
        """Toggle programmable matter visualization."""
        self.show_pm_targets = enable
        return self.show_pm_targets