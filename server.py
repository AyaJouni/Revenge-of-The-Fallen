# server.py
from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import subprocess
import sys
import os
from app.controllers.simulation import ProgrammableMatterSimulation
import random
import time
import numpy as np
from stable_baselines3 import PPO
from pm_env_moore import ProgrammableMatterEnvMoore

app = Flask(__name__, static_folder='static')
simulation = ProgrammableMatterSimulation(width=12, height=12)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

def get_neighbors(pos, grid_size):
    """Return in‐bounds Moore neighbors of `pos` on a grid of size grid_size."""
    x, y = pos
    deltas = [(-1, -1), (-1, 0), (-1, 1),
              ( 0, -1),          ( 0, 1),
              ( 1, -1), ( 1, 0), ( 1, 1)]
    neighs = [(x + dx, y + dy) for dx, dy in deltas]
    return [(nx, ny) for nx, ny in neighs if 0 <= nx < grid_size and 0 <= ny < grid_size]



@app.route('/api/state', methods=['GET'])
def get_state():
    # Get the current state of the simulation
    state = simulation.get_state()
    return jsonify(state)

@app.route('/api/transform', methods=['POST'])
def transform():
    try:
        # Get request data
        data = request.json
        
        # Extract parameters
        algorithm = data.get('algorithm', 'astar')
        shape = data.get('shape', 'square')
        num_elements = data.get('num_elements', 8)
        topology = data.get('topology', 'vonNeumann')
        movement = data.get('movement', 'sequential')
        control_mode = data.get('control_mode', 'centralized')
        collision = data.get('collision', True)
        
        print("="*50)
        print(f"REQUEST PARAMETERS:")
        print(f"  Shape: {shape}")
        print(f"  Algorithm: {algorithm}")
        print(f"  Topology: {topology}")
        print(f"  Movement: {movement}")
        print(f"  Control Mode: {control_mode}")
        print(f"  Elements: {num_elements}")
        print("="*50)
        
        # Initialize the simulation with the specified number of elements
        elements = simulation.initialize_elements(num_elements)
        
        print("INITIAL ELEMENT POSITIONS:")
        for eid, element in simulation.controller.elements.items():
            print(f"  Element {eid}: ({element.x}, {element.y})")
        
        # Set the target shape
        targets = simulation.set_target_shape(shape, num_elements)
        
        print("TARGET POSITIONS:")
        for i, (tx, ty) in enumerate(targets):
            print(f"  Target {i}: ({tx}, {ty})")
        
        # Run the transformation - now supports minimax, expectimax, and adaptive
        result = simulation.transform(
            algorithm=algorithm,
            topology=topology,
            movement=movement,
            control_mode=control_mode
        )
        
        if not result["moves"]:
            print("WARNING: No moves were generated. The transformation may have failed.")
        else:
            print("TRANSFORMATION RESULT:")
            print(f"  Moves: {len(result['moves'])}")
            print(f"  Nodes explored: {result.get('nodes_explored', 0)}")
            
            # Detailed move logging
            print("MOVES (Backend format):")
            for i, move in enumerate(result['moves']):
                print(f"  Move {i}: Agent {move['agentId']} from {move['from']} to {move['to']}")
        
        # Format the moves for the frontend with explicit coordinate handling
        frontend_moves = []
        for move in result['moves']:
            # Create adjusted coordinates with both X and Y fixes
            # Move left by 1 column and up by 1 row
            frontend_move = {
                'agentId': move['agentId'],
                'from': {'x': move['from'][0] - 1, 'y': move['from'][1] - 1},  # Subtract 1 from both x and y
                'to': {'x': move['to'][0] - 1, 'y': move['to'][1] - 1}         # Subtract 1 from both x and y
            }
            frontend_moves.append(frontend_move)
        
        # Log frontend moves
        print("MOVES (Frontend format):")
        for i, move in enumerate(frontend_moves):
            print(f"  Move {i}: Agent {move['agentId']} from ({move['from']['x']},{move['from']['y']}) to ({move['to']['x']},{move['to']['y']})")
        
        # Final element positions
        print("FINAL ELEMENT POSITIONS:")
        for eid, element in simulation.controller.elements.items():
            if hasattr(element, 'target_x') and element.target_x is not None:
                at_target = element.x == element.target_x and element.y == element.target_y
                status = "AT TARGET" if at_target else "NOT AT TARGET"
                print(f"  Element {eid}: ({element.x}, {element.y}) -> Target: ({element.target_x}, {element.target_y}) {status}")
            else:
                print(f"  Element {eid}: ({element.x}, {element.y}) -> No target assigned")
        
        # Prepare the response
        response = {
            'success': True if frontend_moves else False,
            'moves': frontend_moves,
            'time': result['time'],
            'nodes': result.get('nodes_explored', 0),
            'message': 'Transformation completed successfully' if frontend_moves else 'No valid moves found',
            'algorithm_used': result.get('algorithm_used', algorithm)  # Include which algorithm was actually used
        }
        
        return jsonify(response)
    
    except Exception as e:
        import traceback
        print(f"ERROR during transformation: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'moves': [],
            'time': 0,
            'nodes': 0,
            'message': f'Error during transformation: {str(e)}'
        }), 500  # Return 500 status code for server errors
 
    
@app.route('/api/shapes', methods=['GET'])
def get_available_shapes():
    # Return available shape types
    shapes = ['square', 'circle', 'triangle', 'heart']
    return jsonify({'shapes': shapes})

@app.route('/api/algorithms', methods=['GET'])
def get_available_algorithms():
    # Return available algorithms with descriptions
    algorithms = {
        'astar': 'A* Search - Optimal pathfinding using Manhattan distance heuristic',
        'bfs': 'Breadth-First Search - Complete search guaranteeing shortest path',
        'greedy': 'Greedy Search - Fast but potentially suboptimal pathfinding',
        'minimax': 'Minimax - Adversarial search for complex environments',
        'expectimax': 'Expectimax - Probabilistic search handling uncertainty',
        'adaptive': 'Adaptive - Dynamic algorithm selection based on environment'
    }
    return jsonify({'algorithms': algorithms})

@app.route('/api/analyze', methods=['POST'])
def analyze_performance():
    """
    Analyze the performance of different algorithms for a specific shape and parameters.
    This endpoint runs multiple transformations with different algorithms and compares results.
    """
    try:
        # Get request data
        data = request.json
        
        # Extract parameters
        shape = data.get('shape', 'square')
        num_elements = data.get('num_elements', 8)
        topology = data.get('topology', 'vonNeumann')
        control_mode = data.get('control_mode', 'centralized')
        
        # Algorithms to compare
        algorithms = ['astar', 'bfs', 'greedy', 'minimax', 'expectimax', 'adaptive']
        
        results = {}
        
        # Run each algorithm
        for alg in algorithms:
            print(f"Testing algorithm: {alg}")
            
            # Reset simulation for clean comparison
            simulation.reset()
            simulation.initialize_elements(num_elements)
            simulation.set_target_shape(shape, num_elements)
            
            # Run transformation
            result = simulation.transform(
                algorithm=alg,
                topology=topology,
                movement='parallel',  # Use parallel for better comparison
                control_mode=control_mode
            )
            
            # Store results
            success_rate = 0
            # Calculate success rate
            total_elements = sum(1 for e in simulation.controller.elements.values() if e.has_target())
            at_target = sum(1 for e in simulation.controller.elements.values() 
                         if e.has_target() and e.x == e.target_x and e.y == e.target_y)
            
            if total_elements > 0:
                success_rate = at_target / total_elements
            
            results[alg] = {
                'success_rate': success_rate,
                'moves': len(result.get('moves', [])),
                'time': result.get('time', 0),
                'nodes_explored': result.get('nodes_explored', 0)
            }
            
            print(f"  Success rate: {success_rate*100:.1f}%")
            print(f"  Moves: {len(result.get('moves', []))}")
            print(f"  Time: {result.get('time', 0):.2f}s")
            
        return jsonify({
            'success': True,
            'results': results,
            'shape': shape,
            'elements': num_elements,
            'topology': topology,
            'control_mode': control_mode
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR during analysis: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error during analysis: {str(e)}'
        }), 500

@app.route('/api/deadlock-locations', methods=['POST'])
def analyze_deadlock_locations():
    """
    Identify locations on the grid where deadlocks commonly occur for specific shapes.
    This helps understand challenging areas in the formation process.
    """
    try:
        # Get request data
        data = request.json
        
        # Extract parameters
        shape = data.get('shape', 'square')
        num_elements = data.get('num_elements', 8)
        topology = data.get('topology', 'vonNeumann')
        
        # Number of test runs
        num_runs = data.get('runs', 5)
        
        # Create a grid to track deadlock locations
        deadlock_grid = [[0 for _ in range(simulation.grid.width)] for _ in range(simulation.grid.height)]
        
        # Run multiple transformations and track where elements get stuck
        for run in range(num_runs):
            print(f"Deadlock analysis run {run+1}/{num_runs}")
            
            # Reset simulation
            simulation.reset()
            simulation.initialize_elements(num_elements)
            simulation.set_target_shape(shape, num_elements)
            
            # Use non-adversarial algorithms to better identify natural deadlocks
            simulation.transform(
                algorithm='astar',
                topology=topology,
                movement='parallel',
                control_mode='independent'
            )
            
            # Check which elements didn't reach targets
            for eid, element in simulation.controller.elements.items():
                if element.has_target() and (element.x != element.target_x or element.y != element.target_y):
                    # Increment deadlock counter for this position
                    deadlock_grid[element.y][element.x] += 1
        
        # Prepare result with normalized heatmap
        max_value = max(max(row) for row in deadlock_grid)
        normalized_grid = []
        if max_value > 0:
            normalized_grid = [[cell/max_value for cell in row] for row in deadlock_grid]
        else:
            normalized_grid = deadlock_grid
        
        return jsonify({
            'success': True,
            'deadlock_grid': deadlock_grid,
            'normalized_grid': normalized_grid,
            'max_value': max_value,
            'runs': num_runs
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR during deadlock analysis: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error during deadlock analysis: {str(e)}'
        }), 500

# Add these endpoints to your server.py file

# Import the AI Tetris controller
from app.controllers.tetris_ai_game_controller import TetrisAIGameController

# Create an instance of the AI Tetris game
ai_tetris_game = None

@app.route('/api/tetris_ai/start', methods=['POST'])
def start_ai_tetris():
    """Start the AI-driven Tetris game."""
    global ai_tetris_game
    
    try:
        # Get configuration from request
        data = request.json
        algorithm = data.get('algorithm', 'minimax')
        planning_depth = data.get('planningDepth', 2)
        learning_enabled = data.get('learningEnabled', False)
        
        print("="*50)
        print(f"STARTING AI TETRIS GAME")
        print(f"Algorithm: {algorithm}")
        print(f"Planning Depth: {planning_depth}")
        print(f"Learning Enabled: {learning_enabled}")
        print("="*50)
        
        # Create a new AI Tetris game if not exists
        if ai_tetris_game is None:
            ai_tetris_game = TetrisAIGameController(simulation)
        
        # Configure the AI
        ai_tetris_game.toggle_ai_mode(algorithm)
        ai_tetris_game.set_planning_depth(planning_depth)
        
        # Start the game
        ai_tetris_game.start_game()
        
        return jsonify({
            'success': True,
            'message': 'AI Tetris game started'
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR starting AI Tetris: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error starting AI Tetris: {str(e)}'
        }), 500

@app.route('/api/tetris_ai/stop', methods=['POST'])
def stop_ai_tetris():
    """Stop the AI-driven Tetris game."""
    global ai_tetris_game
    
    try:
        if ai_tetris_game is not None:
            ai_tetris_game.active = False
            
            print("AI Tetris game stopped")
            
            return jsonify({
                'success': True,
                'message': 'AI Tetris game stopped'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No AI Tetris game running'
            })
            
    except Exception as e:
        import traceback
        print(f"ERROR stopping AI Tetris: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error stopping AI Tetris: {str(e)}'
        }), 500

@app.route('/api/tetris_ai/state', methods=['GET'])
def get_ai_tetris_state():
    """Get the current state of the AI-driven Tetris game."""
    global ai_tetris_game
    
    try:
        if ai_tetris_game is not None and ai_tetris_game.active:
            # Update the game once
            current_time = time.time()
            ai_tetris_game.update(current_time)
            
            # Get the current game state
            game_state = ai_tetris_game.get_game_state()
            
            return jsonify({
                'success': True,
                'gameState': game_state
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No active AI Tetris game'
            })
            
    except Exception as e:
        import traceback
        print(f"ERROR getting AI Tetris state: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error getting AI Tetris state: {str(e)}'
        }), 500

@app.route('/api/tetris_ai/config', methods=['POST'])
def config_ai_tetris():
    """Configure the AI-driven Tetris game."""
    global ai_tetris_game
    
    try:
        if ai_tetris_game is not None:
            # Get configuration from request
            data = request.json
            
            # Update algorithm if provided
            if 'algorithm' in data:
                algorithm = data['algorithm']
                ai_tetris_game.toggle_ai_mode(algorithm)
                print(f"AI algorithm updated to {algorithm}")
            
            # Update planning depth if provided
            if 'planningDepth' in data:
                planning_depth = data['planningDepth']
                ai_tetris_game.set_planning_depth(planning_depth)
                print(f"AI planning depth updated to {planning_depth}")
            
            # Update learning enabled if provided
            if 'learningEnabled' in data:
                learning_enabled = data['learningEnabled']
                # Update learning mode if your AI controller supports it
                print(f"AI learning mode {'enabled' if learning_enabled else 'disabled'}")
            
            return jsonify({
                'success': True,
                'message': 'AI Tetris configuration updated'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No AI Tetris game running'
            })
            
    except Exception as e:
        import traceback
        print(f"ERROR configuring AI Tetris: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error configuring AI Tetris: {str(e)}'
        }), 500



@app.route('/api/launch-tetris-ai', methods=['POST'])
def launch_tetris_ai():
    """Launch the TetrisAI application in a separate process."""
    try:
        # Path to the Python interpreter
        python_executable = sys.executable
        
        # Path to TetrisAI folder
        tetris_ai_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TetrisAI")
        
        # Path to main.py within TetrisAI folder
        tetris_ai_main = os.path.join(tetris_ai_dir, "main.py")
        
        # Make sure the path exists
        if not os.path.exists(tetris_ai_main):
            return jsonify({
                'success': False,
                'message': f'TetrisAI not found at: {tetris_ai_main}'
            }), 404
        
        # Command to run
        command = [python_executable, tetris_ai_main, "--minimax", "0"]
        
        # Launch TetrisAI as a separate process in the TetrisAI directory
        # The key fix is setting the cwd parameter to the TetrisAI directory
        subprocess.Popen(command, cwd=tetris_ai_dir)
        
        return jsonify({
            'success': True,
            'message': 'TetrisAI launched successfully'
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR launching TetrisAI: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error launching TetrisAI: {str(e)}'
        }), 500

    

@app.route('/api/transform_rl', methods=['POST'])
def transform_rl():
    try:
        data = request.json
        shape        = data.get('shape',        'square')
        num_elements = data.get('num_elements', 20)
        control_mode = data.get('control_mode', 'centralized')

        # 1) Initialize & assign targets
        simulation.initialize_elements(num_elements)
        simulation.set_target_shape(shape, num_elements)
        simulation.controller.assign_targets()

        # 2) Load PPO model & grid size
        grid_size = simulation.grid.width
        model     = PPO.load(os.path.join(os.getcwd(), "models", "ppo_moore_final"))

        # 3) Build one env + obs per agent
        agents = {}
        for eid, elem in simulation.controller.elements.items():
            if not elem.has_target():
                continue
            start = (elem.x, elem.y)
            tgt   = (elem.target_x, elem.target_y)
            env   = ProgrammableMatterEnvMoore(simulation.grid, start, tgt)
            obs, _= env.reset()
            agents[eid] = {"env": env, "obs": obs, "done": False}

        frontend_moves = []
        start_time     = time.time()
        max_steps      = 200

        # 4) Pre-build list of agent IDs
        agent_ids = list(agents.keys())

        # 5) Interleaved, randomized RL stepping
        for _ in range(max_steps):
            any_moved = False

            # Compute occupied cells
            occupied = {
                tuple(a["env"].agent_pos)
                for a in agents.values() if not a["done"]
            }

            # Shuffle turn order each tick
            random.shuffle(agent_ids)

            for eid in agent_ids:
                a = agents[eid]
                if a["done"]:
                    continue

                env, obs = a["env"], a["obs"]
                pos = tuple(env.agent_pos)

                # Tell env about other agents
                env.update_obstacles(occupied - {pos})

                # If fully blocked, skip
                neighs = get_neighbors(pos, grid_size)
                if all(n in occupied for n in neighs):
                    continue

                # PPO step
                action, _        = model.predict(obs)
                obs2, _, done, _, _ = env.step(action)
                new = tuple(env.agent_pos)

                if new != pos:
                    # record move
                    frontend_moves.append({
                        "agentId": eid,
                        "from":   {"x": pos[0] - 1, "y": pos[1] - 1},
                        "to":     {"x": new[0] - 1, "y": new[1] - 1}
                    })
                    any_moved = True

                    # update main simulation grid
                    simulation.controller.move_element(eid, new[0], new[1])

                    occupied.remove(pos)
                    occupied.add(new)

                a["obs"]  = obs2
                if done:
                    a["done"] = True

            if not any_moved:
                break

        # 6) A* fallback for any agents still not at target
        for eid, a in agents.items():
            if a["done"]:
                continue

            elem = simulation.controller.elements[eid]
            sx, sy = elem.x, elem.y
            tx, ty = elem.target_x, elem.target_y

            path, _ = simulation.find_path(
                sx, sy,
                tx, ty,
                algorithm="astar",
                topology="moore"
            )
            if not path or len(path) < 2:
                continue

            prev = (sx, sy)
            for nx, ny in path[1:]:
                # move in main sim
                simulation.controller.move_element(eid, nx, ny)
                # record for front-end
                frontend_moves.append({
                    "agentId": eid,
                    "from":   {"x": prev[0] - 1, "y": prev[1] - 1},
                    "to":     {"x": nx     - 1, "y": ny     - 1}
                })
                prev = (nx, ny)

        # 7) Sanitize moves: convert any numpy ints to Python ints
        safe_moves = []
        for m in frontend_moves:
            safe_moves.append({
                "agentId": int(m["agentId"]),
                "from": {
                    "x": int(m["from"]["x"]),
                    "y": int(m["from"]["y"])
                },
                "to": {
                    "x": int(m["to"]["x"]),
                    "y": int(m["to"]["y"])
                }
            })

        # 8) Return JSON-safe response
        return jsonify({
            "success": True,
            "moves":   safe_moves,
            "time":    float(round(time.time() - start_time, 2)),
            "nodes":   0,
            "message": f"RL+ASTAR movement completed ({control_mode})"
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({
            "success": False,
            "moves":   [],
            "time":    0,
            "nodes":   0,
            "message": f"Error during RL movement: {e}"
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    simulation.reset()
    return jsonify({'success': True, 'message': 'Simulation reset'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
