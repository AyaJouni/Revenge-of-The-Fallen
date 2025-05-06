# app/controllers/tetris_game.py
import random
import time
from app.models.tetris_piece import TetrisPiece

class TetrisGameController:
    """
    Controller for the Tetris-style programmable matter game.
    This manages the game state, piece generation, scoring, and
    coordinates with the programmable matter simulation.
    """
    
    def __init__(self, simulation, grid_width=10, grid_height=20, level=1):
        """
        Initialize the Tetris game controller.
        
        Args:
            simulation: Reference to the ProgrammableMatterSimulation
            grid_width: Width of the game grid
            grid_height: Height of the game grid
            level: Starting level (affects speed)
        """
        self.simulation = simulation
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.level = level
        
        # Game state
        self.score = 0
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.start_time = None
        self.elapsed_time = 0
        
        # Active pieces
        self.current_piece = None
        self.next_piece_type = None
        self.held_piece_type = None
        self.can_hold = True  # Whether player can hold a piece (once per drop)
        
        # Grid state for Tetris blocks (separate from programmable matter)
        # 0 = empty, other values represent locked pieces by color
        self.tetris_grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
        
        # Timing control
        self.last_drop_time = 0
        self.drop_interval = self._calculate_drop_interval()
        
        # Performance metrics for AI evaluation
        self.metrics = {
            'pieces_placed': 0,
            'tetris_clears': 0,  # Four lines cleared at once
            'total_moves': 0,
            'nodes_explored': 0,
            'deadlocks_resolved': 0,
            'ai_prediction_accuracy': 0
        }
        
        # Initialize the game
        self._generate_next_piece_type()
    
    def start_game(self):
        """Start a new Tetris game."""
        # Reset state
        self.score = 0
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.tetris_grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.metrics = {key: 0 for key in self.metrics}
        
        # Generate first pieces
        self._generate_next_piece_type()
        self._spawn_new_piece()
        
        # Set timing
        self.start_time = time.time()
        self.last_drop_time = time.time()
        
        return True
    
    def pause_game(self):
        """Pause or unpause the game."""
        if self.game_over:
            return False
            
        self.paused = not self.paused
        
        if self.paused:
            # Store elapsed time when pausing
            self.elapsed_time += time.time() - self.start_time
        else:
            # Reset start time when unpausing
            self.start_time = time.time()
            self.last_drop_time = time.time()
            
        return self.paused
    
    def update(self, current_time):
        """
        Update the game state. Should be called on each game loop iteration.
        
        Args:
            current_time: Current game time (from time.time())
            
        Returns:
            Dict with game state update information
        """
        if self.paused or self.game_over:
            return {'action': 'none'}
            
        # Check if it's time to drop the piece
        if current_time - self.last_drop_time >= self.drop_interval:
            self.last_drop_time = current_time
            return self._drop_piece()
            
        return {'action': 'none'}
    
    def _drop_piece(self):
        """
        Move the current piece down one row.
        
        Returns:
            Dict with result of the drop action
        """
        if not self.current_piece or self.game_over:
            return {'action': 'none'}
            
        # Try to move down
        new_positions = self.current_piece.move(0, 1)
        
        # Check for collision
        if self._check_collision(new_positions):
            # Move piece back up
            self.current_piece.move(0, -1)
            
            # Lock the piece in place
            self._lock_piece()
            
            # Check for line clears
            lines_cleared = self._check_lines()
            
            if lines_cleared > 0:
                self._update_score(lines_cleared)
                
            # Check if game is over (blocked at spawn)
            if not self._spawn_new_piece():
                self.game_over = True
                return {'action': 'game_over', 'score': self.score}
                
            return {
                'action': 'lock_piece',
                'lines_cleared': lines_cleared,
                'next_piece': self.next_piece_type
            }
        
        return {'action': 'drop'}
    
    def move_piece(self, direction):
        """
        Move the current piece left or right.
        
        Args:
            direction: -1 for left, 1 for right
            
        Returns:
            True if the move was successful, False otherwise
        """
        if not self.current_piece or self.paused or self.game_over:
            return False
            
        new_positions = self.current_piece.move(direction, 0)
        
        # Check for collision
        if self._check_collision(new_positions):
            # Move piece back
            self.current_piece.move(-direction, 0)
            return False
            
        return True
    
    def rotate_piece(self, clockwise=True):
        """
        Rotate the current piece.
        
        Args:
            clockwise: True for clockwise rotation, False for counterclockwise
            
        Returns:
            True if the rotation was successful, False otherwise
        """
        if not self.current_piece or self.paused or self.game_over:
            return False
            
        # Store original rotation to restore if needed
        original_rotation = self.current_piece.rotation
        
        # Try to rotate
        new_positions = self.current_piece.rotate(clockwise)
        
        # Check for collision
        if self._check_collision(new_positions):
            # Wall kick attempts - try to shift the piece to make rotation work
            kicks = [
                (1, 0),   # Right
                (-1, 0),  # Left 
                (0, -1),  # Up
                (1, -1),  # Up-right
                (-1, -1)  # Up-left
            ]
            
            success = False
            for dx, dy in kicks:
                # Move piece
                self.current_piece.move(dx, dy)
                
                # Check if this position works
                if not self._check_collision(self.current_piece.get_positions()):
                    success = True
                    break
                    
                # Move piece back
                self.current_piece.move(-dx, -dy)
                
            if not success:
                # Rotation failed, restore original rotation
                self.current_piece.rotation = original_rotation
                return False
                
        return True
    
    def hard_drop(self):
        """
        Drop the current piece all the way down.
        
        Returns:
            Number of rows the piece was dropped
        """
        if not self.current_piece or self.paused or self.game_over:
            return 0
            
        drop_distance = 0
        
        # Move down until collision
        while True:
            new_positions = self.current_piece.move(0, 1)
            
            if self._check_collision(new_positions):
                # Move piece back up
                self.current_piece.move(0, -1)
                break
                
            drop_distance += 1
            
        # Lock the piece
        self._lock_piece()
        
        # Check for line clears
        lines_cleared = self._check_lines()
        
        if lines_cleared > 0:
            self._update_score(lines_cleared)
            
        # Spawn new piece
        if not self._spawn_new_piece():
            self.game_over = True
            
        # Add bonus points for hard drop
        self.score += drop_distance * 2
        
        return drop_distance
    
    def hold_piece(self):
        """
        Hold the current piece and swap with previously held piece if any.
        
        Returns:
            True if the hold was successful, False otherwise
        """
        if not self.current_piece or not self.can_hold or self.paused or self.game_over:
            return False
            
        current_type = self.current_piece.shape_type
        
        if self.held_piece_type:
            # Swap with held piece
            self._spawn_new_piece(self.held_piece_type)
        else:
            # Just hold current piece and spawn next piece
            self._spawn_new_piece()
            
        self.held_piece_type = current_type
        self.can_hold = False  # Can only hold once per piece
        
        return True
    
    def _lock_piece(self):
        """Lock the current piece in place on the grid."""
        if not self.current_piece:
            return
            
        # Mark piece as locked
        self.current_piece.lock()
        
        # Add piece to grid
        for x, y in self.current_piece.get_positions():
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                self.tetris_grid[y][x] = self.current_piece.shape_type
        
        # Update metrics
        self.metrics['pieces_placed'] += 1
    
    def _check_lines(self):
        """
        Check for completed lines and clear them.
        
        Returns:
            Number of lines cleared
        """
        lines_cleared = 0
        
        # Check each row from bottom to top
        for y in range(self.grid_height - 1, -1, -1):
            # Check if row is full
            if all(cell != 0 for cell in self.tetris_grid[y]):
                lines_cleared += 1
                
                # Clear the row
                for row in range(y, 0, -1):
                    self.tetris_grid[row] = self.tetris_grid[row - 1].copy()
                    
                # Empty the top row
                self.tetris_grid[0] = [0 for _ in range(self.grid_width)]
        
        # Add to total lines cleared
        self.lines_cleared += lines_cleared
        
        # Update level (every 10 lines)
        old_level = self.level
        self.level = (self.lines_cleared // 10) + 1
        
        # Update drop interval if level changed
        if self.level != old_level:
            self.drop_interval = self._calculate_drop_interval()
            
        # Update tetris clear metric
        if lines_cleared == 4:
            self.metrics['tetris_clears'] += 1
            
        return lines_cleared
    
    def _update_score(self, lines_cleared):
        """
        Update score based on lines cleared and level.
        
        Args:
            lines_cleared: Number of lines cleared at once
        """
        # Classic NES Tetris scoring
        points_per_line = {
            1: 40,
            2: 100,
            3: 300,
            4: 1200  # Tetris!
        }
        
        if lines_cleared in points_per_line:
            self.score += points_per_line[lines_cleared] * self.level
    
    def _spawn_new_piece(self, piece_type=None):
        """
        Spawn a new piece at the top of the grid.
        
        Args:
            piece_type: Type of piece to spawn (uses next_piece_type if None)
            
        Returns:
            True if spawn was successful, False if blocked (game over)
        """
        # Use provided type or next piece type
        if piece_type is None:
            piece_type = self.next_piece_type
            self._generate_next_piece_type()
            
        # Create new piece
        self.current_piece = TetrisPiece(piece_type, self.grid_width)
        
        # Check if spawn position is already occupied (game over)
        if self._check_collision(self.current_piece.get_positions()):
            return False
            
        # Reset hold ability
        self.can_hold = True
        
        return True
    
    def _generate_next_piece_type(self):
        """Generate the next piece type randomly."""
        piece_types = list(TetrisPiece.SHAPES.keys())
        self.next_piece_type = random.choice(piece_types)
    
    def _check_collision(self, positions):
        """
        Check if the given positions collide with the grid boundaries or locked pieces.
        
        Args:
            positions: List of (x, y) positions to check
            
        Returns:
            True if collision detected, False otherwise
        """
        for x, y in positions:
            # Check grid boundaries
            if x < 0 or x >= self.grid_width or y >= self.grid_height:
                return True
                
            # Check collision with locked pieces (if position is within grid)
            if y >= 0 and self.tetris_grid[y][x] != 0:
                return True
                
        return False
    
    def _calculate_drop_interval(self):
        """
        Calculate the time interval between automatic drops based on level.
        
        Returns:
            Drop interval in seconds
        """
        # Classic Tetris drop speeds (frames per drop)
        # Converted to seconds (assuming 60 FPS)
        frames_per_level = [
            48, 43, 38, 33, 28, 23, 18, 13, 8, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1
        ]
        
        # Clamp level to valid index
        clamped_level = min(self.level, len(frames_per_level)) - 1
        
        # Convert frames to seconds
        return frames_per_level[clamped_level] / 60.0
    
    def get_game_state(self):
        """
        Get the current game state for rendering and AI planning.
        
        Returns:
            Dict with complete game state information
        """
        # Calculate elapsed time
        if self.paused:
            total_time = self.elapsed_time
        else:
            total_time = self.elapsed_time + (time.time() - self.start_time)
            
        state = {
            'grid': self.tetris_grid,
            'current_piece': self.current_piece.get_positions() if self.current_piece else None,
            'current_piece_type': self.current_piece.shape_type if self.current_piece else None,
            'next_piece': self.next_piece_type,
            'held_piece': self.held_piece_type,
            'level': self.level,
            'score': self.score,
            'lines_cleared': self.lines_cleared,
            'game_over': self.game_over,
            'paused': self.paused,
            'time': int(total_time),
            'metrics': self.metrics
        }
        
        # Add shadow position if there's a current piece
        if self.current_piece:
            state['shadow_positions'] = self.current_piece.get_shadow_positions(self.grid_height)
            
        return state