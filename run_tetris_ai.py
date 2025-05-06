# run_tetris_ai.py
from app.controllers.tetris_ai_game_controller import TetrisAIGameController
from app.controllers.simulation import ProgrammableMatterSimulation
import time

def main():
    """
    Run the AI-driven Tetris game with programmable matter integration.
    """
    print("Starting AI-driven Tetris game with programmable matter integration")
    
    # Create programmable matter simulation
    simulation = ProgrammableMatterSimulation(width=12, height=12)
    
    # Create AI Tetris game controller
    game = TetrisAIGameController(simulation)
    
    # Configure AI settings
    # Choose between minimax, expectimax, or adaptive
    algorithm = "minimax"  # Options: "minimax", "expectimax", "adaptive"
    planning_depth = 3     # How deep to search (1-5)
    
    print(f"AI Algorithm: {algorithm}")
    print(f"Planning Depth: {planning_depth}")
    
    # Configure the AI
    game.toggle_ai_mode(algorithm)
    game.set_planning_depth(planning_depth)
    
    # Start the game
    game.start_game()
    
    # Game loop
    try:
        print("Game started - AI is now playing")
        while game.active and not game.gameOver:
            # Get current time
            current_time = time.time()
            
            # Update game state
            update_result = game.update(current_time)
            
            # Print status updates periodically
            if game.metrics.get('pieces_placed', 0) % 5 == 0 and game.metrics.get('pieces_placed', 0) > 0:
                print_game_status(game)
            
            # Add a small delay to prevent CPU overuse
            time.sleep(0.05)
        
        # Game over
        print("\nGame Over!")
        print_game_status(game)
        
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        print_game_status(game)
    
    print("Thanks for using the AI-driven Tetris!")

def print_game_status(game):
    """Print the current status of the game."""
    print(f"\nScore: {game.score} | Level: {game.level} | Lines: {game.lines}")
    print(f"Pieces placed: {game.metrics.get('pieces_placed', 0)}")
    print(f"Tetris clears: {game.metrics.get('tetris_clears', 0)}")
    
    # Print AI metrics if available
    ai_metrics = game.ai_integration.metrics
    if ai_metrics:
        print(f"AI Decision time: {ai_metrics.get('average_decision_time', 0):.3f}s")
        print(f"PM Utilization: {ai_metrics.get('pm_utilization', 0)*100:.1f}%")

if __name__ == "__main__":
    main()