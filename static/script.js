// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Hide intro after animation
    setTimeout(function() {
        document.getElementById('intro').style.opacity = 0;
        setTimeout(function() {
            document.getElementById('intro').style.display = 'none';
        }, 1000);
    }, 4000);
    
    // Initialize grid
    initializeGrid();
    
    // Set up agent slider
    const agentsSlider = document.getElementById('agents-slider');
    const agentsCount = document.getElementById('agents-count');
    
    agentsSlider.addEventListener('input', function() {
        agentsCount.textContent = this.value;
        updateGrid();
    });

    // Check if heart shape is selected and warn if necessary
    const activeShape = document.querySelector('.target-shape.active').id.split('-')[1];
    if (activeShape === 'heart' && parseInt(this.value) > 12) {
        // Trigger shape selection to show warning
        selectTargetShape('heart');
    }
    
    // Set up algorithm selection
    document.querySelectorAll('input[name="algorithm"]').forEach(radio => {
        radio.addEventListener('change', function() {
            logMessage(`Algorithm set to: ${this.value}`);
            
            // Show info message if Minimax is selected
            if (this.value === 'minimax') {
                logMessage("Minimax algorithm uses strategic planning to avoid collisions with other elements. Best for dense environments.", 'info');
            }
        });
    });
    
    // Set up topology selection
    document.querySelectorAll('input[name="topology"]').forEach(radio => {
        radio.addEventListener('change', function() {
            logMessage(`Topology set to: ${this.value}`);
        });
    });
    
    // Set up movement selection
    document.querySelectorAll('input[name="movement"]').forEach(radio => {
        radio.addEventListener('change', function() {
            logMessage(`Movement set to: ${this.value}`);
        });
    });
    
    // Set up control mode selection
    document.querySelectorAll('input[name="control-mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            logMessage(`Control mode set to: ${this.value}`);
        });
    });
    
    // Log startup
    logMessage('Programmable Matter interface initialized. Awaiting commands.', 'success');
    logMessage('Ready to begin transformation experiments.', 'normal');
});


function initializeGrid() {
    const grid = document.getElementById('grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    // Create a 10x10 grid with proper data attributes
    for (let row = 0; row < 10; row++) {
        for (let col = 0; col < 10; col++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.row = row;
            cell.dataset.col = col;
            
            grid.appendChild(cell);
        }
    }
    
    // Add initial agents at the bottom
    updateGrid();
}

// Function to update grid to make targets clearer
function updateGrid() {
    const agentCount = parseInt(document.getElementById('agents-count').textContent);
    const faction = document.querySelector('.faction-choice.active').id.split('-')[1];
    const selectedShape = document.querySelector('.target-shape.active').id.split('-')[1];
    
    // Clear existing elements
    document.querySelectorAll('.matter-element').forEach(el => {
        el.remove();
    });
    
    // Clear target cell markers
    document.querySelectorAll('.target-cell').forEach(cell => {
        cell.classList.remove('target-cell');
    });
    
    // Add target cells based on shape
    highlightTargetCells(selectedShape, agentCount);
    
    // Add elements with proper spacing
    // Calculate how many elements per row
    const maxElementsPerRow = 10;
    const elementsPerRow = Math.min(maxElementsPerRow, agentCount);
    const rows = Math.ceil(agentCount / elementsPerRow);
    
    let elementCount = 0;
    
    // Start from the bottom rows
    for (let row = 9; row >= 10 - rows; row--) {
        const elementsInThisRow = Math.min(elementsPerRow, agentCount - elementCount);
        const startCol = Math.floor((10 - elementsInThisRow) / 2);
        
        for (let i = 0; i < elementsInThisRow; i++) {
            const col = startCol + i;
            const cell = document.querySelector(`.grid-cell[data-row="${row}"][data-col="${col}"]`);
            
            if (cell) {
                const element = document.createElement('div');
                element.className = `matter-element ${faction}`;
                element.dataset.id = `element-${elementCount}`;
                element.addEventListener('click', function(e) {
                    e.stopPropagation();
                    selectElement(this);
                });
                cell.appendChild(element);
                elementCount++;
            }
        }
    }
    
    logMessage(`Grid updated with ${agentCount} agents.`);
}


function generateTriangleFormation(numElements, gridSize) {
    const positions = [];
    
    // Calculate the number of rows needed for the triangle
    // Using the formula r(r+1) ≤ num_elements where r is the number of rows
    let r = Math.floor((-1 + Math.sqrt(1 + 4 * numElements)) / 2);
    
    // If we can't even fill the first row with 2 agents, adjust
    if (r < 1 && numElements >= 2) {
        r = 1;
    }
    
    // Calculate how many elements we'll use in complete rows
    const elementsInCompleteRows = r * (r + 1);
    
    // Remaining elements for the last partial row (if any)
    const remainingElements = numElements - elementsInCompleteRows;
    
    // Determine elements per row (starting from the TOP row with 2 elements, increasing as we go down)
    const elementsPerRow = [];
    for (let i = 0; i < r; i++) {
        elementsPerRow.push(2 * (i + 1));  // 2, 4, 6, 8, ...
    }
    
    // Add the last partial row if needed
    if (remainingElements > 0) {
        elementsPerRow.push(remainingElements);
    }
    
    // Generate positions for each row
    for (let row = 0; row < elementsPerRow.length; row++) {
        const numInRow = elementsPerRow[row];
        
        // Center the elements in this row
        const startCol = Math.floor((gridSize - numInRow) / 2);
        
        // Add positions for this row
        for (let col = 0; col < numInRow; col++) {
            positions.push([row, startCol + col]);  // Using [row, col] format
        }
    }
    
    // Adjust positions to be centered in the grid vertically
    const totalRows = elementsPerRow.length;
    const verticalOffset = Math.floor((gridSize - totalRows) / 2);
    
    // Apply vertical centering
    const centeredPositions = positions.map(([row, col]) => [row + verticalOffset, col]);
    
    return centeredPositions.slice(0, numElements);
}

function highlightTargetCells(shape, agentCount, gridSize = 10) {
    let positions = [];

    // Determine positions based on the shape
    switch (shape) {
        case 'circle':
            // Use the specialized circle formation logic to match backend
            positions = generateCircleFormation(agentCount, gridSize);
            break;
            
        case 'square':
            // Existing square code...
            const side = Math.ceil(Math.sqrt(agentCount));
            const startRow = Math.floor((gridSize - side) / 2);
            const startCol = Math.floor((gridSize - side) / 2);

            for (let r = 0; r < side; r++) {
                for (let c = 0; c < side; c++) {
                    positions.push([startRow + r, startCol + c]);
                    if (positions.length >= agentCount) break;
                }
                if (positions.length >= agentCount) break;
            }
            break;

        case 'triangle':
            // Use the specialized triangle formation logic to match backend
            positions = generateTriangleFormation(agentCount,gridSize);
            break;


        case 'heart':
            // Existing heart code...
            const heartPositions = [
                [2, 3], [2, 6],
                [3, 2], [3, 4], [3, 5], [3, 7],
                [4, 2], [4, 7],
                [5, 3], [5, 6],
                [6, 4], [6, 5]
            ];

            positions = heartPositions.map(([row, col]) => {
                return [row + Math.floor((gridSize - 10) / 2), col + Math.floor((gridSize - 10) / 2)];
            }).slice(0, agentCount);
            break;

        default:
            console.error('Invalid shape provided');
            return;
    }

    // Highlight target cells
    positions.forEach(([row, col]) => {
        const cell = document.querySelector(`.grid-cell[data-row="${row}"][data-col="${col}"]`);
        if (cell) {
            cell.classList.add('target-cell');
        }
    });
}

function generateCircleFormation(numAgents, gridSize) {
    const positions = [];
    let remaining = numAgents;
    
    // Base configuration for the circle shape
    const baseAgents = 20;
    
    // Define how many agents should be in each row for the base configuration
    let rowPattern = [2, 4, 4, 4, 4, 2];
    
    // Define which rows should have gaps in the middle
    const rowsWithGaps = [2, 3]; // Rows 2 and 3 (third and fourth rows, 0-indexed)
    
    // If we have additional agents beyond the base configuration, adjust the row pattern
    if (numAgents > baseAgents) {
        // Calculate additional agents beyond the base
        const additionalAgents = numAgents - baseAgents;
        
        // Each set of 12 additional agents adds 2 agents per row to the 6 rows
        const setsOf12 = Math.floor(additionalAgents / 12);
        const remainingExtra = additionalAgents % 12;
        
        // Modify row pattern to add 2 agents per row for each complete set of 12
        const modifiedRowPattern = [...rowPattern];
        for (let i = 0; i < modifiedRowPattern.length; i++) {
            modifiedRowPattern[i] += 2 * setsOf12;
        }
        
        // Distribute any remaining extra agents (less than 12) evenly starting from the middle rows
        const distributionOrder = [2, 3, 1, 4, 0, 5]; // Priority of rows to add extra agents
        
        for (let i = 0; i < Math.floor(remainingExtra / 2); i++) { // Add 2 agents at a time
            if (i < distributionOrder.length) {
                const rowIdx = distributionOrder[i];
                modifiedRowPattern[rowIdx] += 2;
            }
        }
        
        // Use the modified pattern
        rowPattern = modifiedRowPattern;
    }
    
    // Calculate vertical offset to center the pattern
    const verticalOffset = Math.floor((gridSize - rowPattern.length) / 2);
    
    // Place agents according to the pattern
    for (let rowIdx = 0; rowIdx < rowPattern.length; rowIdx++) {
        // If we've placed all agents, stop
        if (remaining <= 0) break;
        
        // Calculate actual row position with offset
        const actualRow = rowIdx + verticalOffset;
        
        // If we've reached the bottom of the grid, stop
        if (actualRow >= gridSize) break;
        
        // Calculate how many agents to place in this row
        const agentsInRow = rowPattern[rowIdx];
        const agentsToPlace = Math.min(agentsInRow, remaining);
        
        // For rows that need a gap in the middle
        if (rowsWithGaps.includes(rowIdx)) {
            // Calculate how many agents per side
            const agentsPerSide = Math.floor(agentsInRow / 2);
            
            // Calculate the size of the gap (always maintain 2 empty cells in the middle)
            const gapSize = 2;
            
            // Calculate the starting column for the left side
            const leftStart = Math.floor((gridSize - (agentsPerSide * 2 + gapSize)) / 2);
            
            // Left side agents
            for (let i = 0; i < agentsPerSide; i++) {
                if (remaining <= 0) break;
                positions.push([actualRow, leftStart + i]);
                remaining--;
            }
            
            // Right side agents (after the gap)
            const rightStart = leftStart + agentsPerSide + gapSize;
            for (let i = 0; i < agentsPerSide; i++) {
                if (remaining <= 0) break;
                positions.push([actualRow, rightStart + i]);
                remaining--;
            }
        } else {
            // For other rows, center the agents
            const startCol = Math.floor((gridSize - agentsToPlace) / 2);
            for (let i = 0; i < agentsToPlace; i++) {
                if (remaining <= 0) break;
                positions.push([actualRow, startCol + i]);
                remaining--;
            }
        }
    }
    
    // If we still have agents left to place, add them in rows below the pattern
    if (remaining > 0) {
        let currentRow = verticalOffset + rowPattern.length;
        
        while (remaining > 0 && currentRow < gridSize) {
            // Place up to grid width agents per row
            const agentsToPlace = Math.min(gridSize, remaining);
            const startCol = Math.floor((gridSize - agentsToPlace) / 2);
            
            for (let i = 0; i < agentsToPlace; i++) {
                positions.push([currentRow, startCol + i]);
                remaining--;
            }
            
            currentRow++;
        }
    }
    
    // Ensure we don't exceed the requested number of agents
    return positions.slice(0, numAgents);
}


// Select faction
function selectFaction(faction) {
    // Update UI
    document.querySelectorAll('.faction-choice').forEach(el => {
        el.classList.remove('active');
    });
    document.getElementById(`faction-${faction}`).classList.add('active');
    
    // Update elements
    document.querySelectorAll('.matter-element').forEach(el => {
        el.className = `matter-element ${faction}`;
        if (el.classList.contains('selected')) {
            el.classList.add('selected');
        }
    });
    
    logMessage(`Faction set to: ${faction}`);
}

// Select element
function selectElement(element) {
    document.querySelectorAll('.matter-element').forEach(el => {
        el.classList.remove('selected');
    });
    
    element.classList.add('selected');
    logMessage(`Element ${element.dataset.id} selected.`);
}

// Select target shape
function selectTargetShape(shape) {
    document.querySelectorAll('.target-shape').forEach(el => {
        el.classList.remove('active');
    });
    document.getElementById(`shape-${shape}`).classList.add('active');
    
    // Update target cells
    const agentCount = parseInt(document.getElementById('agents-count').textContent);

    // Clear existing warning message
    const existingWarning = document.querySelector('.shape-warning');
    if (existingWarning) {
        existingWarning.remove();
    }
    
    // Display warning if heart shape is selected with more than 12 agents
    if (shape === 'heart' && agentCount > 12) {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'shape-warning';
        warningDiv.innerHTML = `
            <svg class="warning-icon" viewBox="0 0 24 24" width="16" height="16">
                <path d="M12 2L1 21h22L12 2zm0 3.8L19.3 19H4.7L12 5.8z M11 10h2v5h-2z M11 16h2v2h-2z" fill="#ff9900" />
            </svg>
            Heart shape works best with exactly 12 agents. Your current selection will be limited to 12.
            <button class="adjust-agents-btn" onclick="adjustAgentsForHeart()">Set to 12</button>
        `;
        
        // Insert the warning after the target shapes container
        const targetContainer = document.querySelector('.target-container');
        targetContainer.insertAdjacentElement('afterend', warningDiv);
        
        // Only use 12 agents for highlighting
        highlightTargetCells(shape, 12);
        
        // Log the warning
        logMessage("Warning: Heart shape limited to 12 agents for optimal formation.", 'warning');
    } 
    else {
        // Clear existing target cells
        document.querySelectorAll('.target-cell').forEach(cell => {
            cell.classList.remove('target-cell');
        });
        
        // Add new target cells with actual agent count
        highlightTargetCells(shape, agentCount);
    }
    
    // Clear existing target cells
    document.querySelectorAll('.target-cell').forEach(cell => {
        cell.classList.remove('target-cell');
    });
    
    // Add new target cells
    highlightTargetCells(shape, agentCount);
    
    logMessage(`Target shape set to: ${shape}`);
}

// Helper function to adjust agent count to 12 for heart shape
function adjustAgentsForHeart() {
    const slider = document.getElementById('agents-slider');
    slider.value = 12;
    document.getElementById('agents-count').textContent = '12';
    
    // Update the grid with the new agent count
    updateGrid();
    
    // Remove the warning message
    const warningMsg = document.querySelector('.shape-warning');
    if (warningMsg) {
        warningMsg.remove();
    }
    
    logMessage("Agent count adjusted to 12 for optimal heart shape.", 'success');
}

// Fix move data formatting
function fixMoveData(moves) {
    // Check if the data looks correct already
    if (moves && moves.length > 0 && moves[0].to && typeof moves[0].to === 'object' && 'x' in moves[0].to) {
        console.log("Move data already in correct format");
        return moves;
    }
    
    // Fix data if coordinates are not in the expected format
    console.log("Reformatting move data");
    return moves.map(move => {
        // Check if "to" is an array [x,y] instead of {x:x, y:y}
        if (Array.isArray(move.to)) {
            return {
                agentId: move.agentId,
                from: Array.isArray(move.from) 
                    ? {x: move.from[0], y: move.from[1]} 
                    : move.from,
                to: {x: move.to[0], y: move.to[1]}
            };
        }
        return move;
    });
}

// Function to apply direct placement as fallback when needed
function applyDirectPlacement() {
    logMessage("Using direct placement as fallback...", 'warning');
    
    const selectedShape = document.querySelector('.target-shape.active').id.split('-')[1];
    const targetCells = document.querySelectorAll('.target-cell');
    const elements = document.querySelectorAll('.matter-element');
    
    if (targetCells.length === 0 || elements.length === 0) {
        logMessage("Cannot place elements: no targets or elements found", 'error');
        return;
    }
    
    // Remove elements from current positions
    elements.forEach(el => {
        if (el.parentNode) {
            el.parentNode.removeChild(el);
        }
    });
    
    // Place elements on targets
    const targetCellArray = Array.from(targetCells);
    elements.forEach((element, index) => {
        if (index < targetCellArray.length) {
            targetCellArray[index].appendChild(element);
        }
    });
    
    logMessage(`Elements directly placed into ${selectedShape} formation as fallback.`, 'success');
}

// Modify the startTransformation function to handle all combinations properly
function startTransformation() {
    const selectedShape = document.querySelector('.target-shape.active').id.split('-')[1];
    const algorithm = document.querySelector('input[name="algorithm"]:checked').value;
    const topology = document.querySelector('input[name="topology"]:checked').value;
    const movement = document.querySelector('input[name="movement"]:checked').value;
    const controlMode = document.querySelector('input[name="control-mode"]:checked').value;
    const agentCount = document.getElementById('agents-count').textContent;
    
    logMessage(`Starting transformation to ${selectedShape} shape...`, 'normal');
    
    // Show loading state
    document.getElementById('progress-fill').style.width = "5%";
    document.getElementById('completion-percentage').innerText = "5%";
    
    // Add lots of debug logging
    console.log("=== TRANSFORMATION REQUEST ===");
    console.log("Shape:", selectedShape);
    console.log("Algorithm:", algorithm);
    console.log("Topology:", topology);
    console.log("Movement:", movement);
    console.log("Control Mode:", controlMode);
    console.log("Agent Count:", agentCount);
    
    // Log the specific combination being used
    logMessage(`Using ${controlMode} control with ${movement} movement`, 'info');
    
    // Determine which endpoint to call
    const endpoint = algorithm === 'rl' ? '/api/transform_rl' : '/api/transform';
    
    // Call the backend API
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            algorithm: algorithm,
            shape: selectedShape,
            num_elements: parseInt(agentCount),
            topology: algorithm === 'rl' ? 'moore' : topology, // RL always uses Moore topology
            movement: movement, // Now we pass the actual movement mode selected
            control_mode: controlMode // Now we pass the actual control mode selected
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("=== SERVER RESPONSE ===", data);
        
        // Update metrics
        document.getElementById('moves-count').innerText = data.moves ? data.moves.length : 0;
        document.getElementById('time-elapsed').innerText = `${data.time.toFixed(1)}s`;
        document.getElementById('nodes-explored').innerText = data.nodes || 0;
        
        // Update progress
        document.getElementById('progress-fill').style.width = "50%";
        document.getElementById('completion-percentage').innerText = "50%";
        
        if (data.success) {
            if (data.moves && data.moves.length > 0) {
                console.log("Received moves array:", data.moves);
                
                // Fix move data if needed
                data.moves = fixMoveData(data.moves);
                
                logMessage(`Path calculated. Executing ${data.moves.length} moves...`, 'normal');
                
                // Choose animation method based on the algorithm and movement mode
                if (algorithm === 'rl') {
                    // For RL, use staggered animation
                    animateMovesWithDelay(data.moves);
                } else if (movement === 'sequential') {
                    // For sequential movement, use sequential animation
                    animateSequentialMoves(data.moves);
                } else {
                    // For parallel movement, use regular animation
                    animateMoves(data.moves);
                }
            } else {
                document.getElementById('progress-fill').style.width = "100%";
                document.getElementById('completion-percentage').innerText = "100%";
                logMessage("No moves received from server", 'warning');
            }
        } else {
            document.getElementById('progress-fill').style.width = "0%";
            document.getElementById('completion-percentage').innerText = "0%";
            logMessage(`Error: ${data.message || "Unknown error during transformation"}`, 'error');
        }
    })
    .catch(error => {
        console.error("API Error:", error);
        logMessage(`Connection error: ${error.message}`, 'error');
        document.getElementById('progress-fill').style.width = "0%";
        document.getElementById('completion-percentage').innerText = "0%";
    });
}

// Add a function for sequential animation
function animateSequentialMoves(moves) {
    console.log("Starting sequential animation with", moves.length, "moves");
    
    // Use a longer delay for sequential to clearly show the step-by-step movement
    const moveDelay = 200; // milliseconds between sequential moves
    
    let moveCounter = 0;
    const totalMoves = moves.length;
    
    function executeNextMove() {
        if (moveCounter >= totalMoves) {
            document.getElementById('progress-fill').style.width = "100%";
            document.getElementById('completion-percentage').innerText = "100%";
            logMessage("Transformation complete!", 'success');
            return;
        }
        
        const move = moves[moveCounter];
        moveCounter++;
        
        // Calculate progress percentage
        const progress = 50 + Math.floor((moveCounter / totalMoves) * 50);
        document.getElementById('progress-fill').style.width = `${progress}%`;
        document.getElementById('completion-percentage').innerText = `${progress}%`;
        
        // Find the element
        const element = document.querySelector(`.matter-element[data-id="element-${move.agentId}"]`);
        
        if (element) {
            // Add movement effect
            element.classList.add('moving');
            
            // Get the target cell
            const cell = document.querySelector(`.grid-cell[data-row="${move.to.y}"][data-col="${move.to.x}"]`);
            
            if (cell) {
                // Remove from current location
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
                
                // Add to new cell
                cell.appendChild(element);
                
                // Remove animation class after animation completes
                setTimeout(() => {
                    element.classList.remove('moving');
                }, 300);
                
                console.log(`Moved element ${move.agentId} from (${move.from.x}, ${move.from.y}) to (${move.to.x}, ${move.to.y})`);
            } else {
                console.error(`Target cell not found: (${move.to.x}, ${move.to.y})`);
            }
        } else {
            console.error(`Element ${move.agentId} not found`);
        }
        
        // Schedule next move with delay
        setTimeout(executeNextMove, moveDelay);
    }
    
    // Start the animation
    executeNextMove();
}

// Add a function for RL staggered animation with better collision handling
function animateMovesWithDelay(moves) {
    console.log("Starting RL animation with", moves.length, "moves");
    
    // Use a shorter delay for RL to make the animation smoother
    const moveDelay = 30; // milliseconds between RL moves
    
    // Group moves by their step in the simulation
    // This handles the fact that RL agents make decisions in parallel
    const movesByStep = {};
    let currentStep = 0;
    
    moves.forEach(move => {
        // Simple heuristic to group moves into steps
        if (!movesByStep[currentStep]) {
            movesByStep[currentStep] = [];
        }
        
        movesByStep[currentStep].push(move);
        
        // Every 5 moves, increment the step to create groups
        if (movesByStep[currentStep].length >= 5) {
            currentStep++;
        }
    });
    
    let stepCounter = 0;
    const totalSteps = Object.keys(movesByStep).length;
    
    function executeNextStep() {
        if (stepCounter >= totalSteps) {
            document.getElementById('progress-fill').style.width = "100%";
            document.getElementById('completion-percentage').innerText = "100%";
            logMessage("Transformation complete!", 'success');
            return;
        }
        
        const stepMoves = movesByStep[stepCounter];
        stepCounter++;
        
        // Calculate progress percentage
        const progress = 50 + Math.floor((stepCounter / totalSteps) * 50);
        document.getElementById('progress-fill').style.width = `${progress}%`;
        document.getElementById('completion-percentage').innerText = `${progress}%`;
        
        // Create a set to track occupied cells for collision avoidance
        const occupiedCells = new Set();
        
        // First pass - find all current element positions
        document.querySelectorAll('.matter-element').forEach(element => {
            if (element.parentNode) {
                const row = element.parentNode.dataset.row;
                const col = element.parentNode.dataset.col;
                occupiedCells.add(`${row},${col}`);
            }
        });
        
        // Execute each move in this step, considering collisions
        stepMoves.forEach(move => {
            const element = document.querySelector(`.matter-element[data-id="element-${move.agentId}"]`);
            
            if (element) {
                // Add visual effect for movement
                element.classList.add('moving');
                
                // Get the target cell
                const cell = document.querySelector(`.grid-cell[data-row="${move.to.y}"][data-col="${move.to.x}"]`);
                
                if (cell) {
                    const targetCellKey = `${move.to.y},${move.to.x}`;
                    
                    // Check if the target cell is already marked as occupied by another element in this step
                    if (!occupiedCells.has(targetCellKey)) {
                        // Mark the new cell as occupied
                        occupiedCells.add(targetCellKey);
                        
                        // Remove the old position from occupied set
                        if (element.parentNode) {
                            const oldRow = element.parentNode.dataset.row;
                            const oldCol = element.parentNode.dataset.col;
                            occupiedCells.delete(`${oldRow},${oldCol}`);
                        }
                        
                        // Remove from current location
                        if (element.parentNode) {
                            element.parentNode.removeChild(element);
                        }
                        
                        // Add to new cell
                        cell.appendChild(element);
                        
                        console.log(`Moved element ${move.agentId} to (${move.to.x}, ${move.to.y})`);
                    } else {
                        console.warn(`Collision detected at (${move.to.x}, ${move.to.y}) - skipping move`);
                    }
                    
                    // Remove animation class after animation completes
                    setTimeout(() => {
                        element.classList.remove('moving');
                    }, 300);
                } else {
                    console.error(`Target cell not found: (${move.to.x}, ${move.to.y})`);
                }
            } else {
                console.error(`Element ${move.agentId} not found`);
            }
        });
        
        // Schedule next step with delay
        setTimeout(executeNextStep, moveDelay * 5); // Longer delay between steps
    }
    
    // Start the animation
    executeNextStep();
}

// Add this function to handle algorithm selection and update UI accordingly
function handleAlgorithmSelect() {
    const algorithm = document.querySelector('input[name="algorithm"]:checked').value;
    const topologyOptions = document.querySelectorAll('input[name="topology"]');
    const movementOptions = document.querySelectorAll('input[name="movement"]');
    const controlModeOptions = document.querySelectorAll('input[name="control-mode"]');
    
    if (algorithm === 'rl') {
        // For RL, force Moore topology
        document.querySelector('#topo-moore').checked = true;
        
        // Disable topology selection
        topologyOptions.forEach(option => {
            option.disabled = option.id !== 'topo-moore';
        });
        
        // Add information message
        logMessage("RL algorithm selected - using Moore topology", 'info');
        
        // For RL, recommend fewer agents if current count is high
        const agentCount = parseInt(document.getElementById('agents-count').textContent);
        if (agentCount > 20) {
            logMessage("RL works best with 20 or fewer agents - consider reducing agent count", 'warning');
        }
    } else {
        // Re-enable all options for other algorithms
        topologyOptions.forEach(option => {
            option.disabled = false;
        });
    }
}

// Update the event listener function to avoid duplicates
document.addEventListener('DOMContentLoaded', function() {
    // Initialize grid
    initializeGrid();
    
    // Set up agent slider
    const agentsSlider = document.getElementById('agents-slider');
    const agentsCount = document.getElementById('agents-count');
    
    agentsSlider.addEventListener('input', function() {
        agentsCount.textContent = this.value;
        updateGrid();
    });

    // Set up algorithm selection handlers - just ONE handler
    const algorithmRadios = document.querySelectorAll('input[name="algorithm"]');
    algorithmRadios.forEach(radio => {
        radio.addEventListener('change', handleAlgorithmSelect);
    });
    
    // Call once to set initial state
    handleAlgorithmSelect();
    
    // Add event listeners for movement and control mode changes
    document.querySelectorAll('input[name="movement"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const movement = this.value;
            const controlMode = document.querySelector('input[name="control-mode"]:checked').value;
            logMessage(`Movement set to: ${movement} with ${controlMode} control`, 'info');
        });
    });
    
    document.querySelectorAll('input[name="control-mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const controlMode = this.value;
            const movement = document.querySelector('input[name="movement"]:checked').value;
            logMessage(`Control mode set to: ${controlMode} with ${movement} movement`, 'info');
        });
    });
    
    // Log startup
    logMessage('Programmable Matter interface initialized. Awaiting commands.', 'success');
    logMessage('Ready to begin transformation experiments.', 'normal');
});

// Reset grid with improved logic
function resetGrid() {
    // Clear elements and target cells
    document.querySelectorAll('.matter-element').forEach(el => {
        el.remove();
    });
    
    document.querySelectorAll('.target-cell').forEach(cell => {
        cell.classList.remove('target-cell');
    });
    
    // Initialize grid
    updateGrid();
    
    // Reset metrics
    document.getElementById('moves-count').innerText = '0';
    document.getElementById('time-elapsed').innerText = '0.0s';
    document.getElementById('nodes-explored').innerText = '0';
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('completion-percentage').innerText = '0%';
    
    // Clear console except for initial message
    const console = document.getElementById('console');
    while (console.childElementCount > 2) {
        console.removeChild(console.lastChild);
    }
    
    logMessage('Grid reset. Ready for new transformation.', 'warning');
}

// Compare algorithms function
function compareAlgorithms() {
    // Get selected shape type
    let shapeType = '';
    
    // Check regular shapes
    document.querySelectorAll('.target-shape').forEach(el => {
        if (el.classList.contains('active')) {
            shapeType = el.id.split('-')[1];
        }
    });
    
    if (!shapeType) {
        logMessage("Please select a target shape first", 'error');
        return;
    }
    
    const numElements = parseInt(document.getElementById('agents-count').textContent);
    const topology = document.querySelector('input[name="topology"]:checked').value;
    const movement = document.querySelector('input[name="movement"]:checked').value;
    const controlMode = document.querySelector('input[name="control-mode"]:checked').value;
    
    logMessage("Starting algorithm comparison...", 'normal');
    
    // Show loading state
    document.getElementById('progress-fill').style.width = "5%";
    document.getElementById('completion-percentage').innerText = "5%";
    
    // Create comparison metrics table
    const existingTable = document.querySelector('.comparison-metrics');
    if (existingTable) {
        existingTable.remove();
    }
    
    const metricsTable = document.createElement('div');
    metricsTable.className = 'comparison-metrics';
    metricsTable.innerHTML = `
        <h3>Algorithm Comparison</h3>
        <table id="comparison-table">
            <thead>
                <tr>
                    <th>Algorithm</th>
                    <th>Moves</th>
                    <th>Time (s)</th>
                    <th>Nodes</th>
                    <th>Success</th>
                </tr>
            </thead>
            <tbody>
                <tr id="astar-row">
                    <td>A*</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                <tr id="bfs-row">
                    <td>BFS</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                <tr id="greedy-row">
                    <td>Greedy</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                <tr id="minimax-row">
                    <td>Minimax</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td><tr id="minimax-row">
                    <td>Minimax</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
            </tbody>
        </table>
    `;
    
    // Add to the page
    const consoleElement = document.getElementById('console');
    consoleElement.parentNode.insertBefore(metricsTable, consoleElement);
    
    // Run each algorithm
    const algorithms = ['astar', 'bfs', 'greedy', 'minimax'];
    let currentAlgorithmIndex = 0;
    
    function runNextAlgorithm() {
        if (currentAlgorithmIndex >= algorithms.length) {
            // All done
            document.getElementById('progress-fill').style.width = "100%";
            document.getElementById('completion-percentage').innerText = "100%";
            logMessage("Algorithm comparison complete!", 'success');
            
            // Highlight the best algorithm based on moves
            highlightBestAlgorithm();
            return;
        }
        
        const algorithm = algorithms[currentAlgorithmIndex];
        logMessage(`Testing ${algorithm} algorithm...`, 'normal');
        
        // Update progress
        const progressPct = 5 + ((currentAlgorithmIndex / algorithms.length) * 95);
        document.getElementById('progress-fill').style.width = `${progressPct}%`;
        document.getElementById('completion-percentage').innerText = `${Math.round(progressPct)}%`;
        
        // Call the API
        fetch('/api/transform', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                algorithm: algorithm,
                shape: shapeType,
                num_elements: numElements,
                topology: topology,
                movement: movement,
                control_mode: controlMode
            })
        })
        .then(response => response.json())
        .then(data => {
            // Update metrics table
            const row = document.getElementById(`${algorithm}-row`);
            if (row) {
                row.cells[1].textContent = data.moves ? data.moves.length : 0;
                row.cells[2].textContent = data.time ? data.time.toFixed(2) : '-';
                row.cells[3].textContent = data.nodes || 0;
                row.cells[4].textContent = data.success ? 'Yes' : 'No';
                
                // Highlight successful algorithms
                if (data.success) {
                    row.classList.add('success');
                }
            }
            
            // Move to next algorithm
            currentAlgorithmIndex++;
            setTimeout(runNextAlgorithm, 500);
        })
        .catch(error => {
            logMessage(`Error testing ${algorithm}: ${error.message}`, 'error');
            
            // Update metrics table for the error
            const row = document.getElementById(`${algorithm}-row`);
            if (row) {
                row.cells[1].textContent = '-';
                row.cells[2].textContent = '-';
                row.cells[3].textContent = '-';
                row.cells[4].textContent = 'Error';
                row.classList.add('error');
            }
            
            currentAlgorithmIndex++;
            setTimeout(runNextAlgorithm, 500);
        });
    }
    
    // Function to highlight the best algorithm
    function highlightBestAlgorithm() {
        // Find all successful algorithms
        const successfulAlgorithms = [];
        
        for (const algorithm of algorithms) {
            const row = document.getElementById(`${algorithm}-row`);
            if (row && row.classList.contains('success')) {
                const moves = parseInt(row.cells[1].textContent);
                const time = parseFloat(row.cells[2].textContent);
                const nodes = parseInt(row.cells[3].textContent);
                
                if (!isNaN(moves) && !isNaN(time) && !isNaN(nodes)) {
                    successfulAlgorithms.push({
                        algorithm: algorithm,
                        moves: moves,
                        time: time,
                        nodes: nodes
                    });
                }
            }
        }
        
        // Find the best algorithm based on number of moves (primary) and time (secondary)
        if (successfulAlgorithms.length > 0) {
            // Sort by moves (ascending)
            successfulAlgorithms.sort((a, b) => a.moves - b.moves);
            
            // If multiple algorithms have the same minimum moves, sort by time
            const minMoves = successfulAlgorithms[0].moves;
            const sameMovesAlgs = successfulAlgorithms.filter(a => a.moves === minMoves);
            
            if (sameMovesAlgs.length > 1) {
                sameMovesAlgs.sort((a, b) => a.time - b.time);
            }
            
            const bestAlgorithm = sameMovesAlgs[0].algorithm;
            
            // Highlight the best algorithm
            for (const algorithm of algorithms) {
                const row = document.getElementById(`${algorithm}-row`);
                if (row) {
                    if (algorithm === bestAlgorithm) {
                        row.classList.add('best');
                    } else {
                        row.classList.remove('best');
                    }
                }
            }
            
            // Log the result
            logMessage(`${bestAlgorithm.toUpperCase()} is the most efficient algorithm for this configuration.`, 'success');
        }
    }
    
    // Start the comparison
    runNextAlgorithm();
}

// Highlight best moves for Minimax visualization
function highlightMinimaxStrategy() {
    // First check if Minimax is selected
    const algorithm = document.querySelector('input[name="algorithm"]:checked').value;
    if (algorithm !== 'minimax') {
        logMessage("Please select Minimax algorithm first to visualize strategic moves.", 'warning');
        return;
    }
    
    // Get all grid cells
    const cells = document.querySelectorAll('.grid-cell');
    
    // Clear any existing highlights
    cells.forEach(cell => {
        cell.classList.remove('strategic-path');
        cell.classList.remove('risk-zone');
    });
    
    // Get all elements
    const elements = document.querySelectorAll('.matter-element');
    
    // Check if we have elements to work with
    if (elements.length === 0) {
        logMessage("No elements to analyze.", 'warning');
        return;
    }
    
    // Select a random element to visualize strategy for
    const randomElement = elements[Math.floor(Math.random() * elements.length)];
    
    // Highlight the selected element
    document.querySelectorAll('.matter-element').forEach(el => {
        el.classList.remove('selected');
    });
    randomElement.classList.add('selected');
    
    // Get element's position
    const elementCell = randomElement.parentNode;
    const row = parseInt(elementCell.dataset.row);
    const col = parseInt(elementCell.dataset.col);
    
    // Get target cell (for demonstration, we'll use a target cell if available)
    const targetCell = document.querySelector('.target-cell');
    if (!targetCell) {
        logMessage("Please select a target shape first to visualize strategy.", 'warning');
        return;
    }
    
    const targetRow = parseInt(targetCell.dataset.row);
    const targetCol = parseInt(targetCell.dataset.col);
    
    // Highlight strategic path (in a real implementation, this would come from Minimax)
    highlightStrategicPath(row, col, targetRow, targetCol);
    
    // Highlight potential risk zones (areas where other elements might block)
    highlightRiskZones(row, col, targetRow, targetCol);
    
    logMessage("Minimax strategic visualization: Green shows optimal path, red shows potential conflict zones.", 'info');
}

// Helper function to highlight strategic path
function highlightStrategicPath(startRow, startCol, endRow, endCol) {
    // Simplified path (in a real implementation, this would be calculated by Minimax)
    const path = [];
    
    // Calculate horizontal distance
    const dx = endCol - startCol;
    const xSign = Math.sign(dx);
    
    // Calculate vertical distance
    const dy = endRow - startRow;
    const ySign = Math.sign(dy);
    
    // Build path (prioritize horizontal movement)
    let currentRow = startRow;
    let currentCol = startCol;
    
    // First move horizontally
    for (let i = 0; i < Math.abs(dx); i++) {
        currentCol += xSign;
        path.push([currentRow, currentCol]);
    }
    
    // Then move vertically
    for (let i = 0; i < Math.abs(dy); i++) {
        currentRow += ySign;
        path.push([currentRow, currentCol]);
    }
    
    // Highlight the path
    path.forEach(([row, col]) => {
        const cell = document.querySelector(`.grid-cell[data-row="${row}"][data-col="${col}"]`);
        if (cell) {
            cell.classList.add('strategic-path');
        }
    });
}

// Helper function to highlight risk zones
function highlightRiskZones(startRow, startCol, endRow, endCol) {
    // Calculate the bounding box of the path
    const minRow = Math.min(startRow, endRow);
    const maxRow = Math.max(startRow, endRow);
    const minCol = Math.min(startCol, endCol);
    const maxCol = Math.max(startCol, endCol);
    
    // Find other elements that might block the path
    document.querySelectorAll('.matter-element').forEach(el => {
        if (el.classList.contains('selected')) return; // Skip the selected element
        
        const cell = el.parentNode;
        const elRow = parseInt(cell.dataset.row);
        const elCol = parseInt(cell.dataset.col);
        
        // Check if this element is in or near the path
        if (elRow >= minRow - 1 && elRow <= maxRow + 1 && 
            elCol >= minCol - 1 && elCol <= maxCol + 1) {
            
            // Highlight potential conflict zones around this element
            const neighbors = [
                [elRow - 1, elCol], // Top
                [elRow + 1, elCol], // Bottom
                [elRow, elCol - 1], // Left
                [elRow, elCol + 1]  // Right
            ];
            
            neighbors.forEach(([row, col]) => {
                // Only highlight if in path bounding box
                if (row >= minRow && row <= maxRow && col >= minCol && col <= maxCol) {
                    const neighborCell = document.querySelector(`.grid-cell[data-row="${row}"][data-col="${col}"]`);
                    if (neighborCell) {
                        neighborCell.classList.add('risk-zone');
                    }
                }
            });
        }
    });
}

// Improved logging function
function logMessage(message, type = 'normal') {
    const console = document.getElementById('console');
    if (!console) return;
    
    const time = new Date().toTimeString().split(' ')[0];
    
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-time';
    timeSpan.innerText = `[${time}]`;
    
    entry.appendChild(timeSpan);
    entry.appendChild(document.createTextNode(` ${message}`));
    
    console.appendChild(entry);
    console.scrollTop = console.scrollHeight;
}

// Add CSS for visualization
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.innerHTML = `
    .target-cell {
        background: rgba(0, 184, 255, 0.1);
        box-shadow: inset 0 0 8px rgba(0, 184, 255, 0.3);
    }
    
    .strategic-path {
        background: rgba(0, 255, 0, 0.1);
        box-shadow: inset 0 0 8px rgba(0, 255, 0, 0.3);
    }
    
    .risk-zone {
        background: rgba(255, 0, 0, 0.1);
        box-shadow: inset 0 0 8px rgba(255, 0, 0, 0.3);
    }
    
    #comparison-table tr.best {
        background: rgba(0, 255, 0, 0.1);
    }
    
    #comparison-table tr.error {
        background: rgba(255, 0, 0, 0.1);
    }
    
    .log-entry.info {
        color: var(--energon-blue);
    }
    `;
    document.head.appendChild(style);
    
    // Add Minimax visualization button if needed
    const controlPanel = document.querySelector('.control-buttons');
    if (controlPanel) {
        const visualizeBtn = document.createElement('button');
        visualizeBtn.className = 'button transform';
        visualizeBtn.id = 'btn-visualize';
        visualizeBtn.innerHTML = `
            <svg class="button-icon" viewBox="0 0 24 24" width="16" height="16">
                <path d="M12 4V2M12 22v-2M4 12H2M22 12h-2M19.07 4.93l-1.41 1.41M6.34 17.66l-1.41 1.41M19.07 19.07l-1.41-1.41M6.34 6.34L4.93 4.93" 
                      stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/>
                <circle cx="12" cy="12" r="4" stroke="currentColor" fill="none" stroke-width="2"/>
            </svg>
            Visualize Strategy
        `;
        visualizeBtn.onclick = highlightMinimaxStrategy;
        controlPanel.appendChild(visualizeBtn);
    }
});

// Add these to your static/script.js file

// Tetris Game Variables
let tetrisGame = {
    active: false,
    board: [],
    currentPiece: null,
    nextPiece: null,
    heldPiece: null,
    score: 0,
    level: 1,
    lines: 0,
    gameOver: false,
    paused: false,
    lastFrameTime: 0,
    dropInterval: 1000, // milliseconds
    lastDropTime: 0,
    keys: {
        left: false,
        right: false,
        down: false,
        up: false,
        space: false,
        shift: false
    },
    aiSettings: {
        learningEnabled: false,
        expectimaxEnabled: false,
        planningDepth: 3
    },
    metrics: {
        successRate: 0,
        elementsAtTarget: 0,
        elementsWithTargets: 0,
        rowsFormed: 0,
        nodesExplored: 0,
        tetrisClears: 0
    }
};

// Tetris piece definitions
const TETRIS_SHAPES = {
    'I': {
        color: 'rgba(0, 255, 255, 0.7)',
        rotations: [
            [[0, 0], [1, 0], [2, 0], [3, 0]],
            [[0, 0], [0, 1], [0, 2], [0, 3]]
        ]
    },
    'J': {
        color: 'rgba(0, 0, 255, 0.7)',
        rotations: [
            [[0, 0], [0, 1], [1, 1], [2, 1]],
            [[1, 0], [2, 0], [1, 1], [1, 2]],
            [[0, 1], [1, 1], [2, 1], [2, 2]],
            [[1, 0], [1, 1], [1, 2], [0, 2]]
        ]
    },
    'L': {
        color: 'rgba(255, 127, 0, 0.7)',
        rotations: [
            [[2, 0], [0, 1], [1, 1], [2, 1]],
            [[1, 0], [1, 1], [1, 2], [2, 2]],
            [[0, 1], [1, 1], [2, 1], [0, 2]],
            [[0, 0], [1, 0], [1, 1], [1, 2]]
        ]
    },
    'O': {
        color: 'rgba(255, 255, 0, 0.7)',
        rotations: [
            [[0, 0], [1, 0], [0, 1], [1, 1]]
        ]
    },
    'S': {
        color: 'rgba(0, 255, 0, 0.7)',
        rotations: [
            [[1, 0], [2, 0], [0, 1], [1, 1]],
            [[1, 0], [1, 1], [2, 1], [2, 2]]
        ]
    },
    'T': {
        color: 'rgba(170, 0, 255, 0.7)',
        rotations: [
            [[1, 0], [0, 1], [1, 1], [2, 1]],
            [[1, 0], [1, 1], [2, 1], [1, 2]],
            [[0, 1], [1, 1], [2, 1], [1, 2]],
            [[1, 0], [0, 1], [1, 1], [1, 2]]
        ]
    },
    'Z': {
        color: 'rgba(255, 0, 0, 0.7)',
        rotations: [
            [[0, 0], [1, 0], [1, 1], [2, 1]],
            [[2, 0], [1, 1], [2, 1], [1, 2]]
        ]
    }
};

// Initialize the Tetris game
function initTetrisGame() {
    // Create the board (10x20 grid)
    tetrisGame.board = [];
    for (let y = 0; y < 20; y++) {
        tetrisGame.board.push(Array(10).fill(null));
    }
    
    // Initialize the Tetris board UI
    const tetrisBoard = document.getElementById('tetris-board');
    if (tetrisBoard) {
        tetrisBoard.innerHTML = '';
        
        for (let y = 0; y < 20; y++) {
            for (let x = 0; x < 10; x++) {
                const cell = document.createElement('div');
                cell.className = 'tetris-cell';
                cell.dataset.x = x;
                cell.dataset.y = y;
                tetrisBoard.appendChild(cell);
            }
        }
    }
    
    // Initialize the preview displays
    initPreviewDisplays();
    
    // Initialize metrics display
    updateMetricsDisplay();
    
    // Initialize AI settings from UI
    updateAISettingsFromUI();
    
    // Hide the game over screen
    const gameOverScreen = document.getElementById('game-over-screen');
    if (gameOverScreen) gameOverScreen.classList.remove('active');
    
    // Reset game variables
    tetrisGame.score = 0;
    tetrisGame.level = 1;
    tetrisGame.lines = 0;
    tetrisGame.gameOver = false;
    tetrisGame.paused = false;
    tetrisGame.lastFrameTime = 0;
    tetrisGame.lastDropTime = 0;
    tetrisGame.dropInterval = calculateDropInterval(tetrisGame.level);
    tetrisGame.currentPiece = null;
    tetrisGame.nextPiece = generateRandomPiece();
    tetrisGame.heldPiece = null;
    
    // Update UI displays
    updateScoreDisplay();
    
    // Add keyboard event listeners
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
    
    // Start the game loop
    if (!tetrisGame.active) {
        tetrisGame.active = true;
        window.requestAnimationFrame(gameLoop);
    }
}

// Main game loop
function gameLoop(timestamp) {
    if (!tetrisGame.active) return;
    
    // Calculate delta time
    const deltaTime = timestamp - tetrisGame.lastFrameTime;
    tetrisGame.lastFrameTime = timestamp;
    
    // If game is paused or over, just keep looping
    if (tetrisGame.paused || tetrisGame.gameOver) {
        window.requestAnimationFrame(gameLoop);
        return;
    }
    
    // Spawn a new piece if needed
    if (!tetrisGame.currentPiece) {
        spawnPiece();
    }
    
    // Handle player input
    handleInput();
    
    // Handle automatic dropping
    if (timestamp - tetrisGame.lastDropTime > tetrisGame.dropInterval) {
        tetrisGame.lastDropTime = timestamp;
        moveCurrentPiece(0, 1); // Move down
    }
    
    // Update the game display
    updateGameDisplay();
    
    // Update AI status - simulate backend API call
    updateAIStatus();
    
    // Continue the game loop
    window.requestAnimationFrame(gameLoop);
}

// Handle keyboard input
function handleKeyDown(event) {
    if (!tetrisGame.active || tetrisGame.gameOver) return;
    
    switch (event.key) {
        case 'ArrowLeft':
            tetrisGame.keys.left = true;
            break;
        case 'ArrowRight':
            tetrisGame.keys.right = true;
            break;
        case 'ArrowDown':
            tetrisGame.keys.down = true;
            break;
        case 'ArrowUp':
            tetrisGame.keys.up = true;
            // Rotate immediately
            rotatePiece();
            break;
        case ' ':
            tetrisGame.keys.space = true;
            // Hard drop immediately
            hardDrop();
            break;
        case 'Shift':
        case 'c':
        case 'C':
            tetrisGame.keys.shift = true;
            // Hold piece immediately
            holdPiece();
            break;
        case 'p':
        case 'P':
            // Toggle pause
            pauseTetrisGame();
            break;
    }
}

function handleKeyUp(event) {
    if (!tetrisGame.active) return;
    
    switch (event.key) {
        case 'ArrowLeft':
            tetrisGame.keys.left = false;
            break;
        case 'ArrowRight':
            tetrisGame.keys.right = false;
            break;
        case 'ArrowDown':
            tetrisGame.keys.down = false;
            break;
        case 'ArrowUp':
            tetrisGame.keys.up = false;
            break;
        case ' ':
            tetrisGame.keys.space = false;
            break;
        case 'Shift':
        case 'c':
        case 'C':
            tetrisGame.keys.shift = false;
            break;
    }
}

// Fix for the handleInput function - add timestamp parameter and initialize movement timers
function handleInput(timestamp) {
    if (!tetrisGame.active || tetrisGame.gameOver || tetrisGame.paused) return;
    
    // Initialize movement timers if not already set
    if (!tetrisGame.lastLeftMove) tetrisGame.lastLeftMove = 0;
    if (!tetrisGame.lastRightMove) tetrisGame.lastRightMove = 0;
    if (!tetrisGame.lastDownMove) tetrisGame.lastDownMove = 0;
    
    // Only execute these moves once per interval for smooth movement
    if (tetrisGame.keys.left && (timestamp - tetrisGame.lastLeftMove > 100)) {
        tetrisGame.lastLeftMove = timestamp;
        moveCurrentPiece(-1, 0); // Left
    }
    
    if (tetrisGame.keys.right && (timestamp - tetrisGame.lastRightMove > 100)) {
        tetrisGame.lastRightMove = timestamp;
        moveCurrentPiece(1, 0); // Right
    }
    
    if (tetrisGame.keys.down && (timestamp - tetrisGame.lastDownMove > 50)) {
        tetrisGame.lastDownMove = timestamp;
        moveCurrentPiece(0, 1); // Down (soft drop)
    }
}

// Fix for the game loop function to correctly pass timestamp to handleInput
function gameLoop(timestamp) {
    if (!tetrisGame.active) return;
    
    // Calculate delta time
    const deltaTime = timestamp - tetrisGame.lastFrameTime;
    tetrisGame.lastFrameTime = timestamp;
    
    // If game is paused or over, just keep looping
    if (tetrisGame.paused || tetrisGame.gameOver) {
        window.requestAnimationFrame(gameLoop);
        return;
    }
    
    // Spawn a new piece if needed
    if (!tetrisGame.currentPiece) {
        spawnPiece();
    }
    
    // Handle player input - pass timestamp
    handleInput(timestamp);
    
    // Handle automatic dropping
    if (timestamp - tetrisGame.lastDropTime > tetrisGame.dropInterval) {
        tetrisGame.lastDropTime = timestamp;
        moveCurrentPiece(0, 1); // Move down
    }
    
    // Update the game display
    updateGameDisplay();
    
    // Update AI status - simulate backend API call
    updateAIStatus();
    
    // Continue the game loop
    window.requestAnimationFrame(gameLoop);
}

// Fix for checking lines to properly handle animation and timing
function checkLines() {
    if (!tetrisGame.board) return 0;
    
    let completedLines = 0;
    let linesToClear = [];
    
    // Check each row from bottom to top for completed lines
    for (let y = tetrisGame.board.length - 1; y >= 0; y--) {
        if (tetrisGame.board[y].every(cell => cell !== null)) {
            // This row is complete
            completedLines++;
            linesToClear.push(y);
        }
    }
    
    if (linesToClear.length > 0) {
        // Add animation to the lines being cleared
        linesToClear.forEach(y => {
            const cells = document.querySelectorAll(`.tetris-cell[data-y="${y}"]`);
            cells.forEach(cell => {
                cell.classList.add('clearing');
            });
        });
        
        // Delay the actual clearing and shifting to allow for animation
        setTimeout(() => {
            // Clear the rows (in reverse order to avoid index shifting issues)
            linesToClear.sort((a, b) => b - a); // Sort in descending order
            
            linesToClear.forEach(y => {
                // Remove the animation class
                const cells = document.querySelectorAll(`.tetris-cell[data-y="${y}"]`);
                cells.forEach(cell => {
                    cell.classList.remove('clearing');
                });
                
                // Shift rows down
                for (let row = y; row > 0; row--) {
                    tetrisGame.board[row] = [...tetrisGame.board[row - 1]];
                }
                
                // Empty the top row
                tetrisGame.board[0] = Array(tetrisGame.board[0].length).fill(null);
            });
            
            // Update the game display
            updateGameDisplay();
        }, 300); // shorter animation time for better game feel
    }
    
    return completedLines;
}

// Fix for the lockPiece function to ensure a new piece is spawned
function lockPiece() {
    if (!tetrisGame.currentPiece) return;
    
    console.log("Locking piece", tetrisGame.currentPiece.type);
    
    // Get the piece's blocks
    const blocks = getPieceBlocks(tetrisGame.currentPiece);
    
    // Add the blocks to the board
    for (const [x, y] of blocks) {
        if (y >= 0 && y < tetrisGame.board.length && x >= 0 && x < tetrisGame.board[0].length) {
            tetrisGame.board[y][x] = tetrisGame.currentPiece.type;
        }
    }
    
    // Check for completed lines
    const completedLines = checkLines();
    
    // Update score based on completed lines
    if (completedLines > 0) {
        tetrisGame.lines += completedLines;
        
        // Calculate points (original Nintendo scoring)
        const linePoints = [0, 40, 100, 300, 1200];
        tetrisGame.score += linePoints[Math.min(completedLines, 4)] * tetrisGame.level;
        
        // Update level (every 10 lines)
        const newLevel = Math.floor(tetrisGame.lines / 10) + 1;
        if (newLevel > tetrisGame.level) {
            tetrisGame.level = newLevel;
            tetrisGame.dropInterval = calculateDropInterval(tetrisGame.level);
        }
        
        // Update the lines display
        updateScoreDisplay();
        
        // Update metrics
        if (completedLines === 4) {
            tetrisGame.metrics.tetrisClears++;
        }
    }
    
    // Reset the current piece and allow a new hold
    tetrisGame.currentPiece = null;
    tetrisGame.holdUsed = false;
    
    // Spawn a new piece with a small delay to make the game feel smoother
    setTimeout(() => {
        spawnPiece();
    }, 50);
}

// Fix for the spawnPiece function with better debugging
function spawnPiece(pieceType = null) {
    console.log("Spawning new piece", pieceType || "from next piece");
    
    // If no specific piece type is provided, use the next piece
    if (!pieceType) {
        if (!tetrisGame.nextPiece) {
            tetrisGame.nextPiece = generateRandomPiece();
        }
        pieceType = tetrisGame.nextPiece;
        // Generate a new next piece
        tetrisGame.nextPiece = generateRandomPiece();
        updateNextPieceDisplay();
    }
    
    // Create the new piece
    tetrisGame.currentPiece = {
        type: pieceType,
        x: 3, // Start in the middle of the board
        y: 0, // Start at the top
        rotation: 0
    };
    
    // Check if the spawn position is valid
    if (!isValidPosition(tetrisGame.currentPiece)) {
        // Game over - piece can't spawn
        tetrisGame.gameOver = true;
        showGameOver();
        console.log("Game over - can't spawn piece");
        return false;
    }
    
    console.log("New piece spawned:", tetrisGame.currentPiece.type);
    return true;
}

// Additional function to help with debugging movement issues
function debugMovement(direction, fromX, fromY, toX, toY, success) {
    console.log(`Movement ${direction}: from (${fromX},${fromY}) to (${toX},${toY}) - ${success ? 'SUCCESS' : 'FAILED'}`);
}

// Fix for the moveCurrentPiece function with better validation and debugging
function moveCurrentPiece(dx, dy) {
    if (!tetrisGame.currentPiece || tetrisGame.gameOver || tetrisGame.paused) {
        console.log("Can't move: no piece, game over, or paused");
        return false;
    }
    
    // Create a copy of the current piece
    const piece = {...tetrisGame.currentPiece};
    const oldX = piece.x;
    const oldY = piece.y;
    
    piece.x += dx;
    piece.y += dy;
    
    // Check if the new position is valid
    if (!isValidPosition(piece)) {
        debugMovement(`${dx},${dy}`, oldX, oldY, piece.x, piece.y, false);
        
        // If moving down and invalid, lock the piece
        if (dy > 0) {
            lockPiece();
        }
        return false;
    }
    
    // Update the current piece position
    tetrisGame.currentPiece.x = piece.x;
    tetrisGame.currentPiece.y = piece.y;
    
    debugMovement(`${dx},${dy}`, oldX, oldY, piece.x, piece.y, true);
    return true;
}
// Rotate the current piece
function rotatePiece() {
    if (!tetrisGame.currentPiece || tetrisGame.gameOver || tetrisGame.paused) return false;
    
    // Create a copy of the current piece
    const piece = {...tetrisGame.currentPiece};
    
    // Get the next rotation index
    const rotations = TETRIS_SHAPES[piece.type].rotations;
    piece.rotation = (piece.rotation + 1) % rotations.length;
    
    // Check if the rotated position is valid
    if (!isValidPosition(piece)) {
        // Try wall kicks (standard SRS wall kick)
        const kicks = [
            [1, 0],   // Right
            [-1, 0],  // Left
            [0, -1],  // Up
            [2, 0],   // 2 Right
            [-2, 0],  // 2 Left
            [0, 1]    // Down
        ];
        
        let validKick = false;
        
        // Try each kick offset
        for (const [kickX, kickY] of kicks) {
            const kickedPiece = {
                ...piece,
                x: piece.x + kickX,
                y: piece.y + kickY
            };
            
            if (isValidPosition(kickedPiece)) {
                // Update with the valid kick
                tetrisGame.currentPiece.x = kickedPiece.x;
                tetrisGame.currentPiece.y = kickedPiece.y;
                tetrisGame.currentPiece.rotation = piece.rotation;
                validKick = true;
                break;
            }
        }
        
        // If no valid kick, rotation fails
        if (!validKick) return false;
    } else {
        // Update with the simple rotation
        tetrisGame.currentPiece.rotation = piece.rotation;
    }
    
    return true;
}

// Hard drop the current piece
function hardDrop() {
    if (!tetrisGame.currentPiece || tetrisGame.gameOver || tetrisGame.paused) return;
    
    let dropDistance = 0;
    
    // Keep moving down until collision
    while (moveCurrentPiece(0, 1)) {
        dropDistance++;
    }
    
    // Add bonus points for hard drop
    tetrisGame.score += dropDistance * 2;
    
    // Lock the piece
    lockPiece();
    
    // Update the score display
    updateScoreDisplay();
}

// Hold the current piece
function holdPiece() {
    if (!tetrisGame.currentPiece || tetrisGame.gameOver || tetrisGame.paused || tetrisGame.holdUsed) return;
    
    // Get the current piece type
    const currentType = tetrisGame.currentPiece.type;
    
    // If there's already a held piece, swap them
    if (tetrisGame.heldPiece) {
        const heldType = tetrisGame.heldPiece;
        tetrisGame.heldPiece = currentType;
        // Spawn the previously held piece
        spawnPiece(heldType);
    } else {
        // No held piece yet, just hold the current one
        tetrisGame.heldPiece = currentType;
        // Spawn the next piece
        spawnPiece();
    }
    
    // Mark hold as used for this turn
    tetrisGame.holdUsed = true;
    
    // Update the hold display
    updateHoldDisplay();
}

// Lock the current piece in place
function lockPiece() {
    if (!tetrisGame.currentPiece) return;
    
    // Get the piece's blocks
    const blocks = getPieceBlocks(tetrisGame.currentPiece);
    
    // Add the blocks to the board
    for (const [x, y] of blocks) {
        if (y >= 0 && y < tetrisGame.board.length && x >= 0 && x < tetrisGame.board[0].length) {
            tetrisGame.board[y][x] = tetrisGame.currentPiece.type;
        }
    }
    
    // Check for completed lines
    const completedLines = checkLines();
    
    // Update score based on completed lines
    if (completedLines > 0) {
        tetrisGame.lines += completedLines;
        
        // Calculate points (original Nintendo scoring)
        const linePoints = [0, 40, 100, 300, 1200];
        tetrisGame.score += linePoints[completedLines] * tetrisGame.level;
        
        // Update level (every 10 lines)
        const newLevel = Math.floor(tetrisGame.lines / 10) + 1;
        if (newLevel > tetrisGame.level) {
            tetrisGame.level = newLevel;
            tetrisGame.dropInterval = calculateDropInterval(tetrisGame.level);
        }
        
        // Update the lines display
        updateScoreDisplay();
        
        // Update metrics
        if (completedLines === 4) {
            tetrisGame.metrics.tetrisClears++;
        }
    }
    
    // Reset the current piece and allow a new hold
    tetrisGame.currentPiece = null;
    tetrisGame.holdUsed = false;
    
    // Spawn a new piece
    spawnPiece();
}

// Check for completed lines
function checkLines() {
    if (!tetrisGame.board) return 0;
    
    let completedLines = 0;
    
    // Check each row from bottom to top
    for (let y = tetrisGame.board.length - 1; y >= 0; y--) {
        if (tetrisGame.board[y].every(cell => cell !== null)) {
            // This row is complete
            completedLines++;
            
            // Clear this row with animation
            const cells = document.querySelectorAll(`.tetris-cell[data-y="${y}"]`);
            cells.forEach(cell => {
                cell.classList.add('clearing');
            });
            
            // Delay the actual clearing and shifting to allow for animation
            setTimeout(() => {
                // Remove the animation class
                cells.forEach(cell => {
                    cell.classList.remove('clearing');
                });
                
                // Shift rows down
                for (let row = y; row > 0; row--) {
                    tetrisGame.board[row] = [...tetrisGame.board[row - 1]];
                }
                
                // Empty the top row
                tetrisGame.board[0] = Array(tetrisGame.board[0].length).fill(null);
                
                // Update the game display
                updateGameDisplay();
            }, 500); // match the animation duration
            
            // Since we remove a row, we need to check the same row index again
            y++;
        }
    }
    
    return completedLines;
}

// Spawn a new piece
function spawnPiece(pieceType = null) {
    // If no specific piece type is provided, use the next piece
    if (!pieceType) {
        if (!tetrisGame.nextPiece) {
            tetrisGame.nextPiece = generateRandomPiece();
        }
        pieceType = tetrisGame.nextPiece;
        // Generate a new next piece
        tetrisGame.nextPiece = generateRandomPiece();
        updateNextPieceDisplay();
    }
    
    // Create the new piece
    tetrisGame.currentPiece = {
        type: pieceType,
        x: 3, // Start in the middle of the board
        y: 0, // Start at the top
        rotation: 0
    };
    
    // Check if the spawn position is valid
    if (!isValidPosition(tetrisGame.currentPiece)) {
        // Game over - piece can't spawn
        tetrisGame.gameOver = true;
        showGameOver();
        return false;
    }
    
    return true;
}

// Generate a random piece
function generateRandomPiece() {
    const pieceTypes = Object.keys(TETRIS_SHAPES);
    const randomIndex = Math.floor(Math.random() * pieceTypes.length);
    return pieceTypes[randomIndex];
}

// Check if piece position is valid
function isValidPosition(piece) {
    const blocks = getPieceBlocks(piece);
    
    for (const [x, y] of blocks) {
        // Check if out of bounds
        if (x < 0 || x >= tetrisGame.board[0].length || y >= tetrisGame.board.length) {
            return false;
        }
        
        // Check if overlaps with existing blocks (ignore if above the board)
        if (y >= 0 && tetrisGame.board[y][x] !== null) {
            return false;
        }
    }
    
    return true;
}

// Get the block positions for a piece
function getPieceBlocks(piece) {
    const { type, rotation, x, y } = piece;
    const shape = TETRIS_SHAPES[type].rotations[rotation];
    
    // Apply position offset to get the actual grid positions
    return shape.map(([blockX, blockY]) => [blockX + x, blockY + y]);
}

// Calculate drop interval based on level
function calculateDropInterval(level) {
    // Classic Tetris formula (frames per drop)
    const framesPerDrop = Math.max(1, 48 - (level - 1) * 5);
    // Convert frames to milliseconds (assuming 60fps)
    return framesPerDrop * 16.67;
}

// Update the game display
function updateGameDisplay() {
    // Clear the board display
    const cells = document.querySelectorAll('.tetris-cell');
    cells.forEach(cell => {
        cell.className = 'tetris-cell';
    });
    
    // Draw the locked blocks
    for (let y = 0; y < tetrisGame.board.length; y++) {
        for (let x = 0; x < tetrisGame.board[y].length; x++) {
            const cellType = tetrisGame.board[y][x];
            if (cellType) {
                const cell = document.querySelector(`.tetris-cell[data-x="${x}"][data-y="${y}"]`);
                if (cell) {
                    cell.classList.add(cellType);
                }
            }
        }
    }
    
    // Draw the shadow (where the piece would land)
    if (tetrisGame.currentPiece) {
        const shadowPiece = {...tetrisGame.currentPiece};
        
        // Drop the shadow down
        while (true) {
            shadowPiece.y++;
            if (!isValidPosition(shadowPiece)) {
                shadowPiece.y--; // Move back up to last valid position
                break;
            }
        }
        
        // Draw the shadow
        const shadowBlocks = getPieceBlocks(shadowPiece);
        for (const [x, y] of shadowBlocks) {
            if (y >= 0) { // Only draw if on the board
                const cell = document.querySelector(`.tetris-cell[data-x="${x}"][data-y="${y}"]`);
                if (cell && !cell.classList.contains('tetris-cell')) {
                    cell.classList.add('shadow');
                }
            }
        }
        
        // Draw the current piece
        const blocks = getPieceBlocks(tetrisGame.currentPiece);
        for (const [x, y] of blocks) {
            if (y >= 0) { // Only draw if on the board
                const cell = document.querySelector(`.tetris-cell[data-x="${x}"][data-y="${y}"]`);
                if (cell) {
                    cell.classList.add(tetrisGame.currentPiece.type);
                }
            }
        }
    }
    
    // Draw programmable matter elements (simulated for this demo)
    simulateProgrammableMatterElements();
}

// Simulate programmable matter elements (for the demo)
function simulateProgrammableMatterElements() {
    // This is a simplified simulation
    // In a real implementation, this would be based on the actual PM simulation backend
    
    const numElements = 8; // Number of PM elements to simulate
    const boardHeight = tetrisGame.board.length;
    const boardWidth = tetrisGame.board[0].length;
    
    // Clear previous PM elements
    document.querySelectorAll('.pm-element').forEach(el => {
        el.classList.remove('pm-element');
    });
    
    // Deploy PM elements strategically
    let elementsPlaced = 0;
    
    // Strategy 1: Fill gaps in rows that are nearly complete
    for (let y = boardHeight - 1; y >= 0 && elementsPlaced < numElements; y--) {
        const row = tetrisGame.board[y];
        const emptyCells = [];
        
        // Find empty cells in this row
        for (let x = 0; x < row.length; x++) {
            if (row[x] === null) {
                emptyCells.push([x, y]);
            }
        }
        
        // If the row is nearly complete (1-2 empty cells), fill it
        if (emptyCells.length > 0 && emptyCells.length <= 2) {
            for (const [x, y] of emptyCells) {
                if (elementsPlaced < numElements) {
                    const cell = document.querySelector(`.tetris-cell[data-x="${x}"][data-y="${y}"]`);
                    if (cell) {
                        cell.classList.add('pm-element');
                        elementsPlaced++;
                    }
                }
            }
        }
    }
    
    // Strategy 2: Support the current piece
    if (tetrisGame.currentPiece && elementsPlaced < numElements) {
        const shadowPiece = {...tetrisGame.currentPiece};
        
        // Drop the shadow down
        while (true) {
            shadowPiece.y++;
            if (!isValidPosition(shadowPiece)) {
                shadowPiece.y--; // Move back up to last valid position
                break;
            }
        }
        
        // Position under the shadow
        const shadowBlocks = getPieceBlocks(shadowPiece);
        for (const [x, y] of shadowBlocks) {
            if (elementsPlaced < numElements && y < boardHeight - 1) {
                const supportY = y + 1;
                
                // Check if the cell below is empty
                if (supportY < boardHeight && tetrisGame.board[supportY][x] === null) {
                    const cell = document.querySelector(`.tetris-cell[data-x="${x}"][data-y="${supportY}"]`);
                    if (cell && !cell.classList.contains('pm-element')) {
                        cell.classList.add('pm-element');
                        elementsPlaced++;
                    }
                }
            }
        }
    }
    
    // Strategy 3: Fill holes (empty cells with non-empty cells above)
    for (let y = boardHeight - 2; y >= 0 && elementsPlaced < numElements; y--) {
        for (let x = 0; x < boardWidth; x++) {
            if (tetrisGame.board[y][x] === null) {
                // Check if there's a non-empty cell above
                let hasBlockAbove = false;
                for (let checkY = y - 1; checkY >= 0; checkY--) {
                    if (tetrisGame.board[checkY][x] !== null) {
                        hasBlockAbove = true;
                        break;
                    }
                }
                
                if (hasBlockAbove) {
                    const cell = document.querySelector(`.tetris-cell[data-x="${x}"][data-y="${y}"]`);
                    if (cell && !cell.classList.contains('pm-element')) {
                        cell.classList.add('pm-element');
                        elementsPlaced++;
                        
                        if (elementsPlaced >= numElements) {
                            break;
                        }
                    }
                }
            }
        }
    }
    
    // Update metrics based on PM element placement
    updatePMMetrics(elementsPlaced);
}

// Update the preview displays
function initPreviewDisplays() {
    // Initialize next piece preview
    const nextPieceContainer = document.getElementById('next-piece-preview');
    if (nextPieceContainer) {
        nextPieceContainer.innerHTML = '';
        
        // Create a 4x4 grid for the preview
        for (let y = 0; y < 4; y++) {
            for (let x = 0; x < 4; x++) {
                const cell = document.createElement('div');
                cell.className = 'preview-cell';
                cell.dataset.x = x;
                cell.dataset.y = y;
                nextPieceContainer.appendChild(cell);
            }
        }
    }
    
    // Initialize hold piece preview
    const holdPieceContainer = document.getElementById('hold-piece-preview');
    if (holdPieceContainer) {
        holdPieceContainer.innerHTML = '';
        
        // Create a 4x4 grid for the preview
        for (let y = 0; y < 4; y++) {
            for (let x = 0; x < 4; x++) {
                const cell = document.createElement('div');
                cell.className = 'preview-cell';
                cell.dataset.x = x;
                cell.dataset.y = y;
                holdPieceContainer.appendChild(cell);
            }
        }
    }
}

// Update the next piece preview
function updateNextPieceDisplay() {
    if (!tetrisGame.nextPiece) return;
    
    // Clear previous display
    const cells = document.querySelectorAll('#next-piece-preview .preview-cell');
    cells.forEach(cell => {
        cell.classList.remove('filled');
    });
    
    // Create a dummy piece for the preview
    const previewPiece = {
        type: tetrisGame.nextPiece,
        x: 0,
        y: 0,
        rotation: 0
    };
    
    // Center the piece in the preview
    const blocks = getPieceBlocks(previewPiece);
    
    // Find the bounds
    let minX = 3, minY = 3, maxX = 0, maxY = 0;
    for (const [x, y] of blocks) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
    }
    
    const offsetX = Math.floor((4 - (maxX - minX + 1)) / 2) - minX;
    const offsetY = Math.floor((4 - (maxY - minY + 1)) / 2) - minY;
    
    // Draw the piece
    for (const [x, y] of blocks) {
        const cell = document.querySelector(`#next-piece-preview .preview-cell[data-x="${x + offsetX}"][data-y="${y + offsetY}"]`);
        if (cell) {
            cell.classList.add('filled');
            cell.style.backgroundColor = TETRIS_SHAPES[tetrisGame.nextPiece].color;
        }
    }
}

// Update the hold piece preview
function updateHoldDisplay() {
    if (!tetrisGame.heldPiece) return;
    
    // Clear previous display
    const cells = document.querySelectorAll('#hold-piece-preview .preview-cell');
    cells.forEach(cell => {
        cell.classList.remove('filled');
    });
    
    // Create a dummy piece for the preview
    const previewPiece = {
        type: tetrisGame.heldPiece,
        x: 0,
        y: 0,
        rotation: 0
    };
    
    // Center the piece in the preview
    const blocks = getPieceBlocks(previewPiece);
    
    // Find the bounds
    let minX = 3, minY = 3, maxX = 0, maxY = 0;
    for (const [x, y] of blocks) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
    }
    
    const offsetX = Math.floor((4 - (maxX - minX + 1)) / 2) - minX;
    const offsetY = Math.floor((4 - (maxY - minY + 1)) / 2) - minY;
    
    // Draw the piece
    for (const [x, y] of blocks) {
        const cell = document.querySelector(`#hold-piece-preview .preview-cell[data-x="${x + offsetX}"][data-y="${y + offsetY}"]`);
        if (cell) {
            cell.classList.add('filled');
            cell.style.backgroundColor = TETRIS_SHAPES[tetrisGame.heldPiece].color;
        }
    }
}

// Update score display
function updateScoreDisplay() {
    document.getElementById('tetris-score').textContent = tetrisGame.score;
    document.getElementById('tetris-lines').textContent = tetrisGame.lines;
    document.getElementById('tetris-level').textContent = tetrisGame.level;
}

// Update performance metrics
function updatePMMetrics(elementsPlaced) {
    // Calculate success rate (elements placed / target locations)
    const targetLocations = 10; // This would be the actual count from the backend
    
    tetrisGame.metrics.elementsWithTargets = targetLocations;
    tetrisGame.metrics.elementsAtTarget = elementsPlaced;
    tetrisGame.metrics.successRate = targetLocations > 0 ? elementsPlaced / targetLocations : 0;
    
    // Increment nodes explored
    tetrisGame.metrics.nodesExplored += Math.floor(Math.random() * 10) + 1;
    
    // Update UI
    updateMetricsDisplay();
}

// Update metrics display
function updateMetricsDisplay() {
    const successRateBar = document.getElementById('success-rate-bar');
    const successRateText = document.getElementById('success-rate');
    const elementsAtTargetText = document.getElementById('elements-at-target');
    const tetrisBlocksText = document.getElementById('tetris-blocks');
    const tetrisNodesText = document.getElementById('tetris-nodes');
    
    if (successRateBar && successRateText) {
        const rate = tetrisGame.metrics.successRate * 100;
        successRateBar.style.width = `${rate}%`;
        successRateText.textContent = `${Math.round(rate)}%`;
    }
    
    if (elementsAtTargetText) {
        elementsAtTargetText.textContent = `${tetrisGame.metrics.elementsAtTarget}/${tetrisGame.metrics.elementsWithTargets}`;
    }
    
    if (tetrisBlocksText) {
        tetrisBlocksText.textContent = tetrisGame.metrics.tetrisClears;
    }
    
    if (tetrisNodesText) {
        tetrisNodesText.textContent = tetrisGame.metrics.nodesExplored;
    }
}

// Show game over screen
function showGameOver() {
    const gameOverScreen = document.getElementById('game-over-screen');
    const finalScoreElement = document.getElementById('final-score');
    
    if (gameOverScreen && finalScoreElement) {
        gameOverScreen.classList.add('active');
        finalScoreElement.textContent = tetrisGame.score;
    }
}

// Start the Tetris game
function startTetrisGame() {
    if (tetrisGame.active && !tetrisGame.gameOver && !tetrisGame.paused) return;
    
    if (tetrisGame.gameOver) {
        // Reset the game
        resetTetrisGame();
    } else if (tetrisGame.paused) {
        // Unpause the game
        pauseTetrisGame();
    } else {
        // Initialize and start
        initTetrisGame();
        
        // Show the game container
        const gameContainer = document.querySelector('.tetris-game-container');
        if (gameContainer) {
            gameContainer.style.display = 'block';
        }
        
        // Hide the main container
        const mainContainer = document.querySelector('.main-container');
        if (mainContainer) {
            mainContainer.style.display = 'none';
        }
        
        // Log game start
        console.log("Tetris game started");
    }
}

// Pause the Tetris game
function pauseTetrisGame() {
    if (!tetrisGame.active || tetrisGame.gameOver) return;
    
    tetrisGame.paused = !tetrisGame.paused;
    
    // Update pause button text
    const pauseButton = document.getElementById('btn-pause-game');
    if (pauseButton) {
        pauseButton.textContent = tetrisGame.paused ? 'Resume' : 'Pause';
    }
    
    // Log pause state
    console.log(`Tetris game ${tetrisGame.paused ? 'paused' : 'resumed'}`);
}

// Reset the Tetris game
function resetTetrisGame() {
    // Stop the current game
    tetrisGame.active = false;
    
    // Re-initialize the game
    initTetrisGame();
    
    // Log reset
    console.log("Tetris game reset");
}

// Simulate API calls to the backend for AI status updates
function updateAIStatus() {
    // In a real implementation, this would call the backend API
    // For this demo, we'll just simulate some AI behavior
    
    // Randomly improve metrics to simulate AI learning
    if (tetrisGame.aiSettings.learningEnabled) {
        tetrisGame.metrics.successRate = Math.min(1.0, tetrisGame.metrics.successRate + 0.001);
    }
    
    // Simulate backend processing
    if (Math.random() < 0.01) {
        // Simulate PM elements moving to optimal positions
        simulateProgrammableMatterElements();
    }
}

// Update AI settings from UI controls
function updateAISettingsFromUI() {
    const learningToggle = document.getElementById('learning-toggle');
    const expectimaxToggle = document.getElementById('expectimax-toggle');
    const planningDepthDisplay = document.getElementById('planning-depth');
    
    if (learningToggle) {
        tetrisGame.aiSettings.learningEnabled = learningToggle.checked;
    }
    
    if (expectimaxToggle) {
        tetrisGame.aiSettings.expectimaxEnabled = expectimaxToggle.checked;
    }
    
    if (planningDepthDisplay) {
        tetrisGame.aiSettings.planningDepth = parseInt(planningDepthDisplay.textContent);
    }
}

// Decrease planning depth
function decreasePlanningDepth() {
    const planningDepthDisplay = document.getElementById('planning-depth');
    if (planningDepthDisplay) {
        const currentDepth = parseInt(planningDepthDisplay.textContent);
        if (currentDepth > 1) {
            planningDepthDisplay.textContent = currentDepth - 1;
            tetrisGame.aiSettings.planningDepth = currentDepth - 1;
        }
    }
}

// Increase planning depth
function increasePlanningDepth() {
    const planningDepthDisplay = document.getElementById('planning-depth');
    if (planningDepthDisplay) {
        const currentDepth = parseInt(planningDepthDisplay.textContent);
        if (currentDepth < 5) {
            planningDepthDisplay.textContent = currentDepth + 1;
            tetrisGame.aiSettings.planningDepth = currentDepth + 1;
        }
    }
}

// Toggle between main simulation and Tetris game
function toggleGameMode() {
    const mainContainer = document.querySelector('.main-container');
    const tetrisContainer = document.querySelector('.tetris-game-container');
    
    if (mainContainer && tetrisContainer) {
        if (mainContainer.style.display === 'none') {
            // Switch back to main mode
            mainContainer.style.display = 'block';
            tetrisContainer.style.display = 'none';
            
            // Pause the Tetris game
            if (tetrisGame.active && !tetrisGame.paused) {
                pauseTetrisGame();
            }
        } else {
            // Switch to Tetris mode
            mainContainer.style.display = 'none';
            tetrisContainer.style.display = 'block';
            
            // Start Tetris if not already running
            if (!tetrisGame.active) {
                startTetrisGame();
            } else if (tetrisGame.paused) {
                pauseTetrisGame();
            }
        }
    }
}

// Add a toggle button to the main interface
function addGameModeToggle() {
    const modeToggleContainer = document.createElement('div');
    modeToggleContainer.className = 'mode-toggle-container';
    
    const toggleButton = document.createElement('button');
    toggleButton.className = 'mode-toggle pulsing';
    toggleButton.innerHTML = `
        <svg viewBox="0 0 24 24" width="16" height="16">
            <path d="M14 5h8v2h-8zM14 9h8v2h-8zM14 13h8v2h-8zM14 17h8v2h-8zM2 5h10v14H2zM2 5h10v2H2zM2 17h10v2H2z"></path>
        </svg>
        Play Tetris Mode
    `;
    toggleButton.onclick = toggleGameMode;
    
    modeToggleContainer.appendChild(toggleButton);
    
    // Insert before the faction selector
    const factionSelector = document.querySelector('.faction-selector');
    if (factionSelector && factionSelector.parentNode) {
        factionSelector.parentNode.insertBefore(modeToggleContainer, factionSelector);
    }
}

// Initialize the game mode toggle when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add the game mode toggle button
    addGameModeToggle();
    
    // Initialize the Tetris game
    initTetrisGame();
});


// Add this to your existing script.js file
document.addEventListener('DOMContentLoaded', function() {
    // Add the TetrisAI button click handler
    setTimeout(function() {
        const tetrisAiButton = document.getElementById('tetris-ai-button');
        if (tetrisAiButton) {
            tetrisAiButton.addEventListener('click', launchTetrisAI);
        } else {
            // If the button doesn't exist yet, create it
            addTetrisAiButton();
        }
    }, 1000); // Give the page time to fully load
});

// Function to launch TetrisAI
function launchTetrisAI() {
    logMessage("Launching TetrisAI...", 'normal');
    
    // Call the backend API to launch TetrisAI
    fetch('/api/launch-tetris-ai', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            logMessage("TetrisAI launched successfully! Check your taskbar for the new window.", 'success');
        } else {
            logMessage(`Failed to launch TetrisAI: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("API Error:", error);
        logMessage(`Error launching TetrisAI: ${error.message}`, 'error');
    });
}

// Function to launch TetrisAI
function launchTetrisAI() {
    logMessage("Launching TetrisAI...", 'normal');
    
    // Call the backend API to launch TetrisAI
    fetch('/api/launch-tetris-ai', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            logMessage("TetrisAI launched successfully! Check for the new window.", 'success');
        } else {
            logMessage(`Failed to launch TetrisAI: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("API Error:", error);
        logMessage(`Error launching TetrisAI: ${error.message}`, 'error');
    });
}