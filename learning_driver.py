# learning_driver.py
from app.controllers.simulation import ProgrammableMatterSimulation
from app.controllers.learned_transformation import LearnedTransformationController

def run_learning_experiment(num_elements=18, shape="square", algorithm="astar", 
                            save_model=True, load_model=None):
    """
    Run a complete learning experiment:
    1. Train a model on Moore topology
    2. Apply the learned model to Von Neumann topology
    3. Compare the results
    
    Args:
        num_elements: Number of elements to use
        shape: Target shape to form
        algorithm: Pathfinding algorithm to use
        save_model: Whether to save the trained model
        load_model: Path to a previously saved model to load
        
    Returns:
        Dictionary with experiment results
    """
    print("=" * 50)
    print(f"MOORE-TO-NEUMANN LEARNING EXPERIMENT")
    print(f"Elements: {num_elements}, Shape: {shape}, Algorithm: {algorithm}")
    print("=" * 50)
    
    # Create simulation
    simulation = ProgrammableMatterSimulation(width=12, height=12)
    
    # Create learned transformation controller
    controller = LearnedTransformationController(simulation)
    
    # If loading a model instead of training
    if load_model:
        print(f"Loading pre-trained model from: {load_model}")
        controller.load_model(load_model)
    else:
        # Train on Moore topology
        print("\nPHASE 1: Training on Moore topology")
        moore_success_rate = controller.train_from_moore(num_elements, shape, algorithm)
        print(f"Moore training complete. Success rate: {moore_success_rate*100:.1f}%")
        
        # Save the model if requested
        if save_model:
            model_file = controller.save_model()
            print(f"Model saved to: {model_file}")
    
    # Apply learned model to Von Neumann
    print("\nPHASE 2: Applying learned model to Von Neumann topology")
    vonneumann_result = controller.apply_learned_vonneumann(num_elements, shape, algorithm)
    
    # Run standard Von Neumann for comparison
    print("\nPHASE 3: Running standard Von Neumann for comparison")
    simulation.reset()
    simulation.initialize_elements(num_elements)
    simulation.set_target_shape(shape, num_elements)
    
    standard_result = simulation.transform(
        algorithm=algorithm,
        topology="vonNeumann",
        movement="parallel",
        control_mode="independent"
    )
    
    # Compile and print results
    learned_success = vonneumann_result.get('success_rate', 0)
    standard_success = standard_result.get('success_rate', 0)
    
    print("\n" + "=" * 50)
    print("EXPERIMENT RESULTS")
    print("=" * 50)
    print(f"Learned Von Neumann success rate: {learned_success*100:.1f}%")
    print(f"Standard Von Neumann success rate: {standard_success*100:.1f}%")
    print(f"Improvement: {(learned_success - standard_success)*100:.1f}%")
    print("=" * 50)
    
    return {
        "learned_success": learned_success,
        "standard_success": standard_success,
        "improvement": learned_success - standard_success,
        "learned_moves": len(vonneumann_result.get('moves', [])),
        "standard_moves": len(standard_result.get('moves', [])),
        "learned_result": vonneumann_result,
        "standard_result": standard_result
    }

def run_multiple_experiments(shapes=None, agents_list=None, iterations=3):
    """
    Run multiple learning experiments across different shapes and agent counts.
    
    Args:
        shapes: List of shapes to test
        agents_list: List of agent counts to test
        iterations: Number of iterations per configuration
        
    Returns:
        Dictionary with aggregated results
    """
    if shapes is None:
        shapes = ["square", "circle", "triangle"]
    
    if agents_list is None:
        agents_list = [10, 15, 18, 20]
    
    results = {}
    
    for shape in shapes:
        shape_results = {}
        
        for num_agents in agents_list:
            config_results = []
            
            print(f"\n{'-'*80}")
            print(f"TESTING: Shape={shape}, Agents={num_agents}")
            print(f"{'-'*80}")
            
            # Train once for this configuration
            experiment = run_learning_experiment(num_agents, shape)
            model_file = f"moore_to_neumann_{shape}_{num_agents}_elements.json"
            
            # Run additional iterations using the saved model
            for i in range(iterations - 1):
                print(f"\nIteration {i+2}/{iterations} for {shape} with {num_agents} agents")
                iter_experiment = run_learning_experiment(
                    num_agents, shape, load_model=model_file
                )
                config_results.append(iter_experiment)
            
            # Add initial experiment results
            config_results.append(experiment)
            
            # Calculate average results
            avg_improvement = sum(r["improvement"] for r in config_results) / len(config_results)
            avg_learned = sum(r["learned_success"] for r in config_results) / len(config_results)
            avg_standard = sum(r["standard_success"] for r in config_results) / len(config_results)
            
            shape_results[num_agents] = {
                "avg_improvement": avg_improvement,
                "avg_learned_success": avg_learned,
                "avg_standard_success": avg_standard,
                "raw_results": config_results
            }
            
            print(f"Average improvement: {avg_improvement*100:.1f}%")
        
        results[shape] = shape_results
    
    # Print summary of all experiments
    print("\n" + "=" * 80)
    print("EXPERIMENT SUMMARY")
    print("=" * 80)
    
    for shape in shapes:
        for num_agents in agents_list:
            shape_result = results[shape][num_agents]
            print(f"{shape.capitalize()} with {num_agents} agents: "
                  f"{shape_result['avg_improvement']*100:.1f}% improvement "
                  f"({shape_result['avg_learned_success']*100:.1f}% vs. "
                  f"{shape_result['avg_standard_success']*100:.1f}%)")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Moore-to-Neumann Learning Experiments")
    parser.add_argument("--agents", type=int, default=18, help="Number of agents")
    parser.add_argument("--shape", choices=["square", "circle", "triangle"], default="square", 
                      help="Target shape")
    parser.add_argument("--alg", choices=["astar", "bfs", "greedy"], default="astar", 
                      help="Pathfinding algorithm")
    parser.add_argument("--multi", action="store_true", help="Run multiple experiments")
    parser.add_argument("--load", type=str, help="Load a pre-trained model")
    
    args = parser.parse_args()
    
    if args.multi:
        run_multiple_experiments()
    else:
        run_learning_experiment(args.agents, args.shape, args.alg, load_model=args.load)