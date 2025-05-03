# app/controllers/learned_transformation.py
from app.utils.moore_to_neumann_learner import MooreToNeumannLearner

class LearnedTransformationController:
    """
    Controller for learned transformation strategies, integrating Moore-to-Neumann learning
    to improve von Neumann performance by learning from Moore's successes.
    """
    
    def __init__(self, simulation):
        """Initialize with reference to the simulation."""
        self.simulation = simulation
        self.learner = MooreToNeumannLearner(simulation.grid, simulation.controller)
        self.is_trained = False
        self.training_data = {}
    
    def train_from_moore(self, num_elements, shape, algorithm="astar"):
        """
        Train the model by running Moore topology transformations
        and learning from their success patterns.
        
        Args:
            num_elements: Number of elements to initialize
            shape: Target shape to form
            algorithm: Pathfinding algorithm to use
        
        Returns:
            Success rate of the training runs
        """
        print(f"Training Moore-to-Neumann model with {num_elements} elements, shape: {shape}")
        
        # Initialize elements
        self.simulation.initialize_elements(num_elements)
        
        # Set target shape
        self.simulation.set_target_shape(shape, num_elements)
        
        # Run Moore topology transformation to gather training data
        result = self.simulation.transform(
            algorithm=algorithm,
            topology="moore",  # Use Moore for training
            movement="parallel",
            control_mode="centralized"  # Centralized provides cleaner paths for learning
        )
        
        # Store training data
        self.training_data = {
            'num_elements': num_elements,
            'shape': shape,
            'algorithm': algorithm,
            'result': result
        }
        
        # Extract paths from result
        paths = {}
        targets = {}
        
        # Convert paths to the format expected by the learner
        for element_id, path in result.get('paths', {}).items():
            if not path:
                continue
            paths[element_id] = [(pos[0], pos[1]) for pos in path]
        
        # Get target positions
        for element_id, element in self.simulation.controller.elements.items():
            if element.has_target():
                targets[element_id] = (element.target_x, element.target_y)
        
        # Train the learner
        self.learner.train_from_moore_paths(paths, targets)
        self.is_trained = True
        
        # Return the success rate
        return result.get('success_rate', 0)
    
    def apply_learned_vonneumann(self, num_elements, shape, algorithm="astar"):
        """
        Apply the learned model to transform using Von Neumann topology.
        
        Args:
            num_elements: Number of elements to initialize
            shape: Target shape to form
            algorithm: Pathfinding algorithm to use
            
        Returns:
            Results of the transformation
        """
        if not self.is_trained:
            print("WARNING: Model not trained. Results may be suboptimal.")
        
        print(f"Applying learned Von Neumann transformation for {num_elements} elements, shape: {shape}")
        
        # Initialize elements
        self.simulation.initialize_elements(num_elements)
        
        # Set target shape
        self.simulation.set_target_shape(shape, num_elements)
        
        # Run Von Neumann transformation with learned strategies
        result = self._transform_learned_independent(
            algorithm=algorithm,
            topology="vonNeumann",
            movement="parallel"
        )
        
        return result
    
    def _transform_learned_independent(self, algorithm, topology, movement):
        """
        Execute transformation using learned strategies for Von Neumann topology.
        This is a custom transformation method that applies learned patterns.
        
        Args:
            algorithm: Base pathfinding algorithm
            topology: Should be "vonNeumann"
            movement: Movement type (sequential or parallel)
            
        Returns:
            Transformation results
        """
        import time
        
        if topology != "vonNeumann":
            print("WARNING: Learned transformation only applies to Von Neumann topology.")
        
        start_time = time.time()
        
        # Initialize tracking
        total_moves = []
        total_nodes_explored = 0
        
        # Maximum steps
        max_steps = 500
        current_step = 0
        
        # Element tracking
        reached_targets = set()
        stuck_counters = {}
        
        # Real-time learning variables
        attempted_moves = {}  # element_id -> (move, success)
        movement_outcomes = {}  # element_id -> list of (move, success) pairs
        
        # Online learning enabled flag - continue learning during execution
        online_learning = True
        
        # While we have elements not at target and haven't exceeded max steps
        while current_step < max_steps:
            # Get all elements with targets that haven't reached them yet
            active_elements = [e for e in self.simulation.controller.elements.values() 
                           if e.has_target() and e.id not in reached_targets]
            
            # If all elements have reached their targets, we're done
            if not active_elements:
                break
            
            # Progress report
            all_elements = [e for e in self.simulation.controller.elements.values() if e.has_target()]
            at_target = len(all_elements) - len(active_elements)
            print(f"Step {current_step}: {at_target}/{len(all_elements)} elements at target "
                  f"({at_target/len(all_elements)*100:.1f}%)")
            
            # Track pending moves for this round
            moves_this_round = []
            
            # Process each element
            for element in active_elements:
                # Check if element has reached its target
                if element.x == element.target_x and element.y == element.target_y:
                    reached_targets.add(element.id)
                    continue
                
                # Track stuck count
                if element.id not in stuck_counters:
                    stuck_counters[element.id] = 0
                
                # Get the learned suggestion
                suggested_pos = self.learner.suggest_von_neumann_move(element, topology)
                
                if suggested_pos:
                    # Validate the suggested position
                    nx, ny = suggested_pos
                    
                    # Check if the suggested position is valid
                    if (self.simulation.grid.is_valid_position(nx, ny) and 
                        not self.simulation.grid.is_wall(nx, ny) and 
                        not self.simulation.grid.is_element(nx, ny)):
                        
                        # Valid move, add to this round's moves
                        moves_this_round.append((element, suggested_pos))
                    else:
                        # Invalid suggestion, fall back to basic algorithm
                        self.simulation.grid.remove_element(element)
                        path_result = self.simulation.find_path(
                            element.x, element.y,
                            element.target_x, element.target_y,
                            algorithm, topology
                        )
                        self.simulation.grid.add_element(element)
                        
                        if path_result and path_result[0] and len(path_result[0]) > 1:
                            next_pos = path_result[0][1]
                            total_nodes_explored += path_result[1]
                            moves_this_round.append((element, next_pos))
                else:
                    # No suggestion, fall back to basic algorithm
                    self.simulation.grid.remove_element(element)
                    path_result = self.simulation.find_path(
                        element.x, element.y,
                        element.target_x, element.target_y,
                        algorithm, topology
                    )
                    self.simulation.grid.add_element(element)
                    
                    if path_result and path_result[0] and len(path_result[0]) > 1:
                        next_pos = path_result[0][1]
                        total_nodes_explored += path_result[1]
                        moves_this_round.append((element, next_pos))
            
            # Handle parallel vs sequential movement
            if movement == "sequential" and moves_this_round:
                # For sequential, take only the first move
                moves_this_round = [moves_this_round[0]]
            elif movement == "parallel" and moves_this_round:
                # For parallel, resolve conflicts
                planned_positions = {}
                final_moves = []
                
                for element, pos in moves_this_round:
                    if pos not in planned_positions:
                        planned_positions[pos] = element
                        final_moves.append((element, pos))
                    else:
                        # Position conflict - find alternative
                        neighbors = self.simulation.grid.get_neighbors(element.x, element.y, topology)
                        alt_positions = [(nx, ny) for nx, ny in neighbors 
                                      if not self.simulation.grid.is_wall(nx, ny) and 
                                      not self.simulation.grid.is_element(nx, ny) and 
                                      (nx, ny) not in planned_positions]
                        
                        if alt_positions:
                            # Choose alternative closest to target
                            alt_positions.sort(key=lambda p: 
                                          abs(p[0] - element.target_x) + abs(p[1] - element.target_y))
                            alt_pos = alt_positions[0]
                            planned_positions[alt_pos] = element
                            final_moves.append((element, alt_pos))
                
                moves_this_round = final_moves
            
            # Execute moves
            execution_results = []
            for element, (next_x, next_y) in moves_this_round:
                # Record old position
                old_pos = (element.x, element.y)
                
                # Execute the move
                success = self.simulation.grid.move_element(element, next_x, next_y)
                
                if success:
                    # Add to total moves
                    move = {"agentId": element.id, "from": old_pos, "to": (next_x, next_y)}
                    total_moves.append(move)
                    
                    # Reset stuck counter
                    stuck_counters[element.id] = 0
                    
                    # If online learning is enabled, update the model based on the outcome
                    if online_learning:
                        self.learner.update_from_outcome(element.id, (next_x, next_y), True)
                    
                    # Add to execution results
                    execution_results.append((element.id, (next_x, next_y), True))
                    
                    print(f"Moved Element {element.id} from {old_pos} to ({next_x}, {next_y})")
                else:
                    # Increment stuck counter
                    stuck_counters[element.id] += 1
                    
                    # If online learning is enabled, update the model based on the outcome
                    if online_learning:
                        self.learner.update_from_outcome(element.id, (next_x, next_y), False)
                    
                    # Add to execution results
                    execution_results.append((element.id, (next_x, next_y), False))
                    
                    print(f"Failed to move Element {element.id} to ({next_x}, {next_y})")
                
                # Count as node exploration
                total_nodes_explored += 1
            
            # Handle stuck elements and deadlocks
            stuck_elements = [e_id for e_id, count in stuck_counters.items() if count >= 5]
            if stuck_elements:
                print(f"Detected {len(stuck_elements)} stuck elements: {stuck_elements}")
                
                for e_id in stuck_elements:
                    if e_id in self.simulation.controller.elements:
                        element = self.simulation.controller.elements[e_id]
                        
                        # Try to find an alternative move
                        neighbors = self.simulation.grid.get_neighbors(element.x, element.y, topology)
                        valid_neighbors = [(nx, ny) for nx, ny in neighbors 
                                        if not self.simulation.grid.is_wall(nx, ny) and 
                                        not self.simulation.grid.is_element(nx, ny)]
                        
                        if valid_neighbors:
                            # Choose random neighbor to break deadlock
                            import random
                            next_pos = random.choice(valid_neighbors)
                            old_pos = (element.x, element.y)
                            
                            success = self.simulation.grid.move_element(element, next_pos[0], next_pos[1])
                            
                            if success:
                                print(f"Deadlock resolution: Moved Element {e_id} to {next_pos}")
                                move = {"agentId": e_id, "from": old_pos, "to": next_pos}
                                total_moves.append(move)
                                stuck_counters[e_id] = 0
            
            # Next step
            current_step += 1
        
        # Calculate results
        elements_with_targets = [e for e in self.simulation.controller.elements.values() if e.has_target()]
        elements_at_target = [e for e in elements_with_targets if e.at_target()]
        
        success_rate = len(elements_at_target) / len(elements_with_targets) if elements_with_targets else 0
        
        print(f"\nLearned transformation complete.")
        print(f"Elements at target: {len(elements_at_target)}/{len(elements_with_targets)} ({success_rate*100:.1f}%)")
        print(f"Steps taken: {current_step}")
        print(f"Total moves: {len(total_moves)}")
        
        # Return results
        return {
            "moves": total_moves,
            "nodes_explored": total_nodes_explored,
            "success_rate": success_rate,
            "time": time.time() - start_time,
            "success": success_rate > 0.95  # Consider success if 95% of elements reached targets
        }
    
    def save_model(self, filename=None):
        """Save the learned model to a file."""
        if not filename:
            # Generate filename based on training data
            shape = self.training_data.get('shape', 'unknown')
            elements = self.training_data.get('num_elements', 0)
            filename = f"moore_to_neumann_{shape}_{elements}_elements.json"
        
        self.learner.save_model(filename)
        return filename
    
    def load_model(self, filename):
        """Load a previously saved model."""
        success = self.learner.load_model(filename)
        if success:
            self.is_trained = True
        return success