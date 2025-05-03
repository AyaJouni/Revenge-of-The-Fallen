# app/utils/moore_to_neumann_learner.py
import numpy as np
from collections import defaultdict, deque
import random

class MooreToNeumannLearner:
    """
    A learning algorithm that analyzes successful Moore navigation patterns
    and applies them to Von Neumann topology to improve success rates.
    """
    
    def __init__(self, grid, controller):
        """Initialize the learner with grid and controller references."""
        self.grid = grid
        self.controller = controller
        
        # Training data: successful paths from Moore topology
        self.moore_successful_paths = {}  # element_id -> list of positions
        
        # Extracted patterns and principles
        self.direction_preferences = {}  # situation -> direction preference
        self.target_approach_patterns = {}  # relative_position -> approach strategy
        self.deadlock_escape_patterns = {}  # pattern_type -> escape strategy
        
        # Situation classification
        self.situation_memory = {}  # (element_id, situation_hash) -> outcome
        
        # Pattern extraction
        self.position_history = {}  # element_id -> list of recent positions
        
        # Learning rate parameters
        self.learning_rate = 0.1
        self.exploration_rate = 0.2  # Start with 20% random exploration
        self.exploitation_threshold = 0.8  # When to switch from learning to exploitation
        
        # Training state
        self.is_trained = False
        self.training_iterations = 0
        
    def train_from_moore_paths(self, moore_paths, targets):
        """
        Train the model using successful paths from Moore topology.
        
        Args:
            moore_paths: Dict mapping element_ids to their successful Moore paths
            targets: Dict mapping element_ids to their target positions
        """
        print("Training Moore-to-Neumann model from successful paths...")
        self.moore_successful_paths = moore_paths
        
        # Reset learning state
        self.direction_preferences = {}
        self.target_approach_patterns = {}
        self.deadlock_escape_patterns = {}
        
        # Extract patterns from each successful path
        for element_id, path in moore_paths.items():
            if len(path) < 2:
                continue  # Skip paths that are too short
                
            target = targets.get(element_id)
            if not target:
                continue  # Skip elements without targets
                
            # Extract direction preferences
            self._extract_direction_preferences(path, target)
            
            # Extract target approach patterns
            self._extract_approach_patterns(path, target)
            
            # Extract deadlock escape patterns (if any)
            self._extract_escape_patterns(path)
        
        # Process and normalize learned patterns
        self._normalize_learned_patterns()
        
        # Mark as trained and ready for use
        self.is_trained = True
        self.training_iterations += 1
        
        print(f"Training complete. Extracted {len(self.direction_preferences)} direction preferences, "
              f"{len(self.target_approach_patterns)} approach patterns, and "
              f"{len(self.deadlock_escape_patterns)} escape patterns.")
        
    def _extract_direction_preferences(self, path, target):
        """
        Extract direction preferences from a successful path.
        Analyzes which directions were preferred in different situations.
        """
        for i in range(len(path) - 1):
            curr_pos = path[i]
            next_pos = path[i + 1]
            
            # Calculate the direction vector
            dx = next_pos[0] - curr_pos[0]
            dy = next_pos[1] - curr_pos[1]
            
            # Skip diagonal moves (can't be replicated in Von Neumann)
            if abs(dx) > 0 and abs(dy) > 0:
                continue
                
            # Calculate relative position to target
            target_dx = target[0] - curr_pos[0]
            target_dy = target[1] - curr_pos[1]
            
            # Normalize to get direction (-1, 0, 1)
            target_dx_dir = 0 if target_dx == 0 else (1 if target_dx > 0 else -1)
            target_dy_dir = 0 if target_dy == 0 else (1 if target_dy > 0 else -1)
            
            # Create a situation key
            situation = (target_dx_dir, target_dy_dir)
            
            # Record the chosen direction
            direction = (dx, dy)
            
            if situation not in self.direction_preferences:
                self.direction_preferences[situation] = defaultdict(int)
            
            self.direction_preferences[situation][direction] += 1
    
    def _extract_approach_patterns(self, path, target):
        """
        Extract patterns for approaching the target in the final steps.
        """
        # Focus on the last part of the path (approaching target)
        approach_segment = path[-min(len(path), 5):]
        
        if len(approach_segment) < 2:
            return
            
        # Calculate relative position at start of approach
        start_pos = approach_segment[0]
        rel_x = target[0] - start_pos[0]
        rel_y = target[1] - start_pos[1]
        
        # Create a key for this approach pattern
        approach_key = (
            1 if rel_x > 0 else (-1 if rel_x < 0 else 0),
            1 if rel_y > 0 else (-1 if rel_y < 0 else 0)
        )
        
        # Extract the sequence of moves
        moves = []
        for i in range(len(approach_segment) - 1):
            curr_pos = approach_segment[i]
            next_pos = approach_segment[i + 1]
            
            dx = next_pos[0] - curr_pos[0]
            dy = next_pos[1] - curr_pos[1]
            
            # Only include horizontal or vertical moves (Von Neumann compatible)
            if abs(dx) > 0 and abs(dy) > 0:
                continue
                
            moves.append((dx, dy))
        
        if moves:
            if approach_key not in self.target_approach_patterns:
                self.target_approach_patterns[approach_key] = []
            
            self.target_approach_patterns[approach_key].append(moves)
    
    def _extract_escape_patterns(self, path):
        """
        Extract patterns for escaping potential deadlock situations.
        Looks for sequences where an element appeared stuck then made progress.
        """
        # Look for oscillation patterns followed by progress
        oscillations = []
        
        for i in range(len(path) - 4):
            segment = path[i:i+4]
            
            # Check for A-B-A-B pattern
            if segment[0] == segment[2] and segment[1] == segment[3]:
                oscillations.append(i)
        
        # For each oscillation, find how it was eventually broken
        for osc_start in oscillations:
            # Find where the oscillation ends
            osc_end = osc_start + 4
            while (osc_end + 1 < len(path) and 
                   path[osc_end] == path[osc_end - 2] and 
                   path[osc_end - 1] == path[osc_end - 3]):
                osc_end += 2
            
            # If there's a path after the oscillation, record the escape
            if osc_end + 1 < len(path):
                # Get the oscillation pattern
                osc_pattern = (path[osc_start], path[osc_start + 1])
                
                # Get the escape move
                escape_pos = path[osc_end]
                escape_next = path[osc_end + 1]
                
                dx = escape_next[0] - escape_pos[0]
                dy = escape_next[1] - escape_pos[1]
                
                # Only consider horizontal or vertical escapes
                if abs(dx) > 0 and abs(dy) > 0:
                    continue
                    
                escape_dir = (dx, dy)
                
                # Create a pattern key
                pattern_key = f"oscillation_{hash(osc_pattern)}"
                
                if pattern_key not in self.deadlock_escape_patterns:
                    self.deadlock_escape_patterns[pattern_key] = defaultdict(int)
                
                self.deadlock_escape_patterns[pattern_key][escape_dir] += 1
    
    def _normalize_learned_patterns(self):
        """
        Process and normalize the learned patterns to create probability distributions.
        """
        # Normalize direction preferences
        for situation, directions in self.direction_preferences.items():
            total = sum(directions.values())
            for direction in directions:
                directions[direction] /= total
        
        # Process approach patterns
        for approach_key, pattern_list in self.target_approach_patterns.items():
            # Keep only the most common patterns
            if len(pattern_list) > 5:
                # Count pattern frequencies
                pattern_counts = defaultdict(int)
                for pattern in pattern_list:
                    pattern_tuple = tuple(pattern)
                    pattern_counts[pattern_tuple] += 1
                
                # Keep the top 5 most common patterns
                top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                self.target_approach_patterns[approach_key] = [list(p[0]) for p in top_patterns]
        
        # Normalize deadlock escape patterns
        for pattern, escapes in self.deadlock_escape_patterns.items():
            total = sum(escapes.values())
            for escape in escapes:
                escapes[escape] /= total
    
    def suggest_von_neumann_move(self, element, topology):
        """
        Suggest a move for Von Neumann topology based on learned patterns.
        
        Args:
            element: The element to generate a move for
            topology: The topology (should be "vonNeumann")
            
        Returns:
            Tuple (x, y) of the suggested next position or None if no suggestion
        """
        if not self.is_trained or topology != "vonNeumann":
            return None
        
        # Get available neighbors in Von Neumann topology
        neighbors = self.grid.get_neighbors(element.x, element.y, topology)
        valid_moves = [(nx, ny) for nx, ny in neighbors 
                     if not self.grid.is_wall(nx, ny) and not self.grid.is_element(nx, ny)]
        
        if not valid_moves:
            return None
        
        # Check if we should explore (random move)
        if random.random() < self.exploration_rate and self.training_iterations < 3:
            return random.choice(valid_moves)
        
        # Calculate relative position to target
        target_dx = element.target_x - element.x
        target_dy = element.target_y - element.y
        
        # Normalize to direction
        target_dx_dir = 0 if target_dx == 0 else (1 if target_dx > 0 else -1)
        target_dy_dir = 0 if target_dy == 0 else (1 if target_dy > 0 else -1)
        
        # Create a situation key
        situation = (target_dx_dir, target_dy_dir)
        
        # Store current position history
        if element.id not in self.position_history:
            self.position_history[element.id] = []
        
        current_pos = (element.x, element.y)
        self.position_history[element.id].append(current_pos)
        
        # Keep only recent history
        if len(self.position_history[element.id]) > 10:
            self.position_history[element.id] = self.position_history[element.id][-10:]
        
        # Check for oscillation or deadlock patterns
        is_deadlocked = self._check_deadlock_pattern(element.id)
        
        # STRATEGY 1: If near target, use approach patterns
        if abs(target_dx) <= 2 and abs(target_dy) <= 2:
            approach_key = (target_dx_dir, target_dy_dir)
            
            if approach_key in self.target_approach_patterns and self.target_approach_patterns[approach_key]:
                # Get a random approach pattern from the learned ones
                approach_pattern = random.choice(self.target_approach_patterns[approach_key])
                
                if approach_pattern:
                    next_dir = approach_pattern[0]  # Get the first move in the pattern
                    next_pos = (element.x + next_dir[0], element.y + next_dir[1])
                    
                    # Check if this move is valid
                    if next_pos in valid_moves:
                        return next_pos
        
        # STRATEGY 2: If in a deadlock, use escape patterns
        if is_deadlocked:
            pattern_key = f"oscillation_{hash(tuple(self.position_history[element.id][-4:]))}"
            
            if pattern_key in self.deadlock_escape_patterns:
                escapes = self.deadlock_escape_patterns[pattern_key]
                
                # Choose escape direction based on learned probabilities
                escape_dirs = list(escapes.keys())
                escape_probs = list(escapes.values())
                
                if escape_dirs and escape_probs:
                    escape_dir = random.choices(escape_dirs, weights=escape_probs)[0]
                    next_pos = (element.x + escape_dir[0], element.y + escape_dir[1])
                    
                    if next_pos in valid_moves:
                        return next_pos
            
            # If no learned escape or it's not valid, try any move that breaks pattern
            recent_positions = set(self.position_history[element.id][-4:])
            fresh_moves = [pos for pos in valid_moves if pos not in recent_positions]
            
            if fresh_moves:
                return random.choice(fresh_moves)
        
        # STRATEGY 3: Use direction preferences from learned data
        if situation in self.direction_preferences:
            directions = self.direction_preferences[situation]
            
            # Create a list of possible moves with their learned probabilities
            possible_moves = []
            probs = []
            
            for next_pos in valid_moves:
                dx = next_pos[0] - element.x
                dy = next_pos[1] - element.y
                direction = (dx, dy)
                
                if direction in directions:
                    possible_moves.append(next_pos)
                    probs.append(directions[direction])
            
            if possible_moves and probs:
                # Normalize probabilities
                total = sum(probs)
                if total > 0:
                    probs = [p/total for p in probs]
                    return random.choices(possible_moves, weights=probs)[0]
        
        # STRATEGY 4: Default to basic heuristic if no learned patterns apply
        # Prioritize moves that get closer to target
        move_scores = []
        for nx, ny in valid_moves:
            # Calculate Manhattan distance to target
            new_dist = abs(nx - element.target_x) + abs(ny - element.target_y)
            current_dist = abs(element.x - element.target_x) + abs(element.y - element.target_y)
            
            # Score based on distance improvement
            score = current_dist - new_dist
            
            # Penalize positions visited recently (avoid oscillation)
            if (nx, ny) in self.position_history.get(element.id, [])[-4:]:
                score -= 2
            
            move_scores.append((nx, ny, score))
        
        if move_scores:
            # Sort by score (highest first)
            move_scores.sort(key=lambda x: x[2], reverse=True)
            return move_scores[0][0], move_scores[0][1]
        
        # Fallback to random move
        return random.choice(valid_moves)
    
    def _check_deadlock_pattern(self, element_id):
        """
        Check if an element is in a deadlock pattern.
        
        Returns:
            Boolean indicating if a deadlock pattern is detected.
        """
        if element_id not in self.position_history:
            return False
            
        positions = self.position_history[element_id]
        
        # Need at least 4 positions to detect patterns
        if len(positions) < 4:
            return False
            
        # Check for oscillation (A-B-A-B pattern)
        if positions[-1] == positions[-3] and positions[-2] == positions[-4]:
            return True
        
        # Check for position repetition (A-B-C-A pattern)
        if positions[-1] == positions[-4]:
            return True
            
        # Check for lack of progress (same position multiple times)
        if positions[-1] == positions[-2] == positions[-3]:
            return True
            
        return False
    
    def update_from_outcome(self, element_id, move, success):
        """
        Update the model based on the outcome of a suggested move.
        Used during online learning to refine the model.
        
        Args:
            element_id: ID of the element that moved
            move: The move that was attempted (next_x, next_y)
            success: Boolean indicating if the move was successful
        """
        if not self.is_trained:
            return
            
        # Get the element
        if element_id not in self.controller.elements:
            return
            
        element = self.controller.elements[element_id]
        
        # Calculate the situation
        target_dx = element.target_x - element.x
        target_dy = element.target_y - element.y
        
        target_dx_dir = 0 if target_dx == 0 else (1 if target_dx > 0 else -1)
        target_dy_dir = 0 if target_dy == 0 else (1 if target_dy > 0 else -1)
        
        situation = (target_dx_dir, target_dy_dir)
        
        # Calculate the direction
        dx = move[0] - element.x
        dy = move[1] - element.y
        direction = (dx, dy)
        
        # Create a situation hash for memory
        situation_hash = hash((situation, direction))
        memory_key = (element_id, situation_hash)
        
        # Update memory with outcome
        if memory_key not in self.situation_memory:
            self.situation_memory[memory_key] = 0.5  # Initial neutral score
        
        # Update score based on success
        if success:
            # Successful move, increase score
            self.situation_memory[memory_key] += self.learning_rate * (1 - self.situation_memory[memory_key])
        else:
            # Failed move, decrease score
            self.situation_memory[memory_key] -= self.learning_rate * self.situation_memory[memory_key]
        
        # Update direction preferences if this situation exists
        if situation in self.direction_preferences and direction in self.direction_preferences[situation]:
            # Adjust the preference based on outcome
            if success:
                # Increase preference for this direction
                self.direction_preferences[situation][direction] *= (1 + self.learning_rate)
            else:
                # Decrease preference for this direction
                self.direction_preferences[situation][direction] *= (1 - self.learning_rate)
            
            # Renormalize
            total = sum(self.direction_preferences[situation].values())
            for d in self.direction_preferences[situation]:
                self.direction_preferences[situation][d] /= total
        
        # Reduce exploration rate as we learn
        self.exploration_rate *= 0.999
        self.exploration_rate = max(0.05, self.exploration_rate)  # Don't go below 5%
    
    def train_from_centralized_paths(self, centralized_results):
        """
        Extract training data from successful centralized algorithm runs.
        This is useful to learn from the centralized algorithm's success.
        
        Args:
            centralized_results: Results from centralized algorithm runs
        """
        if not centralized_results or "paths" not in centralized_results:
            return
            
        paths = centralized_results["paths"]
        targets = {}
        
        # Extract target positions
        for element_id, element in self.controller.elements.items():
            if element.has_target():
                targets[element_id] = (element.target_x, element.target_y)
        
        # Filter for successful paths and convert to the right format
        successful_paths = {}
        
        for element_id, path in paths.items():
            if not path:
                continue
                
            # Convert path to list of positions
            positions = [(pos[0], pos[1]) for pos in path]
            
            if len(positions) >= 2:  # Only consider non-trivial paths
                successful_paths[element_id] = positions
        
        # Train the model using these paths
        if successful_paths:
            self.train_from_moore_paths(successful_paths, targets)
    
    def save_model(self, filename="moore_to_neumann_model.json"):
        """
        Save the learned model to a file.
        """
        import json
        
        # Convert data to serializable format
        model_data = {
            "direction_preferences": {str(k): {str(dir): prob for dir, prob in v.items()} 
                                   for k, v in self.direction_preferences.items()},
            "target_approach_patterns": {str(k): v for k, v in self.target_approach_patterns.items()},
            "deadlock_escape_patterns": {k: {str(dir): prob for dir, prob in v.items()} 
                                      for k, v in self.deadlock_escape_patterns.items()},
            "training_iterations": self.training_iterations,
            "is_trained": self.is_trained
        }
        
        with open(filename, 'w') as f:
            json.dump(model_data, f, indent=2)
            
        print(f"Model saved to {filename}")
    
    def load_model(self, filename="moore_to_neumann_model.json"):
        """
        Load a previously saved model.
        """
        import json
        
        try:
            with open(filename, 'r') as f:
                model_data = json.load(f)
            
            # Parse direction preferences
            self.direction_preferences = {}
            for k_str, v in model_data["direction_preferences"].items():
                # Convert string tuple back to actual tuple
                k_parts = k_str.strip("()").split(", ")
                k_tuple = (int(k_parts[0]), int(k_parts[1]))
                
                self.direction_preferences[k_tuple] = defaultdict(int)
                for dir_str, prob in v.items():
                    # Convert string direction back to tuple
                    dir_parts = dir_str.strip("()").split(", ")
                    dir_tuple = (int(dir_parts[0]), int(dir_parts[1]))
                    
                    self.direction_preferences[k_tuple][dir_tuple] = float(prob)
            
            # Parse approach patterns
            self.target_approach_patterns = {}
            for k_str, v in model_data["target_approach_patterns"].items():
                k_parts = k_str.strip("()").split(", ")
                k_tuple = (int(k_parts[0]), int(k_parts[1]))
                
                self.target_approach_patterns[k_tuple] = v
            
            # Parse escape patterns
            self.deadlock_escape_patterns = {}
            for k, v in model_data["deadlock_escape_patterns"].items():
                self.deadlock_escape_patterns[k] = defaultdict(int)
                for dir_str, prob in v.items():
                    dir_parts = dir_str.strip("()").split(", ")
                    dir_tuple = (int(dir_parts[0]), int(dir_parts[1]))
                    
                    self.deadlock_escape_patterns[k][dir_tuple] = float(prob)
            
            # Set other attributes
            self.training_iterations = model_data.get("training_iterations", 0)
            self.is_trained = model_data.get("is_trained", False)
            
            print(f"Model loaded from {filename}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False