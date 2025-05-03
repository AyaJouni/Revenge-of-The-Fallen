# server.py
from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from app.controllers.simulation import ProgrammableMatterSimulation

app = Flask(__name__, static_folder='static')
simulation = ProgrammableMatterSimulation(width=12, height=12)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


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
        
        # Run the transformation
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
            print(f"  Nodes explored: {result['nodes_explored']}")
            
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
            'nodes': result['nodes_explored'],
            'message': 'Transformation completed successfully' if frontend_moves else 'No valid moves found'
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
 
    
@app.route('/api/reset', methods=['POST'])
def reset():
    # Reset the simulation
    simulation.reset()
    return jsonify({'success': True, 'message': 'Simulation reset'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)