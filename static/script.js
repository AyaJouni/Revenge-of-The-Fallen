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
    
    // // Set up collision toggle
    // const collisionToggle = document.getElementById('collision-toggle');
    
    // collisionToggle.addEventListener('change', function() {
    //     logMessage(`Collision detection ${this.checked ? 'enabled' : 'disabled'}`);
    // });
    
    // Set up algorithm selection
    document.querySelectorAll('input[name="algorithm"]').forEach(radio => {
        radio.addEventListener('change', function() {
            logMessage(`Algorithm set to: ${this.value}`);
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
    
    // Debug highlighted cells
    debugHighlightedCells();
    
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



data.moves = fixMoveData(data.moves);
if (data.moves && data.moves.length > 0) {
        logMessage(`Path calculated. Executing ${data.moves.length} moves...`, 'normal');
        animateMoves(data.moves);
       }





// Start transformation with debug logs
function startTransformation() {
    const selectedShape = document.querySelector('.target-shape.active').id.split('-')[1];
    const algorithm = document.querySelector('input[name="algorithm"]:checked').value;
    const topology = document.querySelector('input[name="topology"]:checked').value;
    const movement = document.querySelector('input[name="movement"]:checked').value;
    const controlMode = document.querySelector('input[name="control-mode"]:checked').value;
    const agentCount = document.getElementById('agents-count').textContent;
//    const collisionEnabled = document.getElementById('collision-toggle').checked;
    
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
  //  console.log("Collision Enabled:", collisionEnabled);
    
    // Call the backend API
    fetch('/api/transform', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            algorithm: algorithm,
            shape: selectedShape,
            num_elements: parseInt(agentCount),
            topology: topology,
            movement: movement,
            control_mode: controlMode,
      //      collision: collisionEnabled
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
                logMessage(`Path calculated. Executing ${data.moves.length} moves...`, 'normal');
                animateMoves(data.moves);
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

// Fix for animateMoves function
function animateMoves(moves) {
    console.log("Starting animation with", moves.length, "moves");
    
    // Validate move data - log the first few moves for debugging
    for (let i = 0; i < Math.min(5, moves.length); i++) {
        console.log(`Move ${i}:`, moves[i]);
    }
    
    let currentMove = 0;
    const totalMoves = moves.length;
    
    function executeNextMove() {
        if (currentMove >= totalMoves) {
            document.getElementById('progress-fill').style.width = "100%";
            document.getElementById('completion-percentage').innerText = "100%";
            logMessage("Transformation complete!", 'success');
            return;
        }
        
        const move = moves[currentMove];
        const elementId = move.agentId;
        
        // Debug information
        console.log(`Executing move ${currentMove}:`, move);
        
        // Find element
        const element = document.querySelector(`.matter-element[data-id="element-${elementId}"]`);
        
        if (element) {
            // Verify both the source and target positions
            console.log(`Element ${elementId} found at`, element.parentNode ? 
                       `row=${element.parentNode.dataset.row}, col=${element.parentNode.dataset.col}` : 
                       "no parent cell");
            
            // Get the target cell
            const cell = document.querySelector(`.grid-cell[data-row="${move.to.y}"][data-col="${move.to.x}"]`);
            
            if (cell) {
                console.log(`Target cell found at row=${move.to.y}, col=${move.to.x}`);
                
                // Remove from current location
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
                
                // Add to new cell
                cell.appendChild(element);
                console.log(`Moved element ${elementId} to row=${move.to.y}, col=${move.to.x}`);
            } else {
                console.error(`Target cell not found: row=${move.to.y}, col=${move.to.x}`);
                
                // Fallback: try to find a cell at x,y instead of y,x (in case coordinates are swapped)
                const altCell = document.querySelector(`.grid-cell[data-row="${move.to.x}"][data-col="${move.to.y}"]`);
                if (altCell) {
                    console.log(`Found cell with swapped coordinates. Using row=${move.to.x}, col=${move.to.y}`);
                    
                    // Remove from current location
                    if (element.parentNode) {
                        element.parentNode.removeChild(element);
                    }
                    
                    // Add to new cell with swapped coordinates
                    altCell.appendChild(element);
                }
            }
        } else {
            console.error(`Element ${elementId} not found`);
        }
        
        // Update progress
        currentMove++;
        const progress = 50 + Math.floor((currentMove / totalMoves) * 50);
        document.getElementById('progress-fill').style.width = `${progress}%`;
        document.getElementById('completion-percentage').innerText = `${progress}%`;
        
        // Continue animation
        setTimeout(executeNextMove, 100);  // Increase delay for easier visualization
    }
    
    // Start the animation
    if (moves.length > 0) {
        executeNextMove();
    } else {
        console.error("No moves to animate!");
        document.getElementById('progress-fill').style.width = "100%";
        document.getElementById('completion-percentage').innerText = "100%";
        logMessage("No movements needed or possible.", 'warning');
    }
}

// Fix for API call formatting - append this at the end of startTransformation function
// Add after the existing fetch call in startTransformation
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

// Move elements to form the selected shape
function moveElementsToShape(shape) {
    const grid = document.getElementById('grid');
    const elements = document.querySelectorAll('.matter-element');
    
    // Remove all elements from current positions
    elements.forEach(el => {
        if (el.parentNode) {
            el.parentNode.removeChild(el);
        }
    });
    
    let positions = [];
    
    // Determine positions based on the shape
    switch (shape) {
        case 'square':
            positions = [
                [3, 3], [3, 4], [3, 5], [3, 6],
                [4, 3], [4, 6],
                [5, 3], [5, 6],
                [6, 3], [6, 4], [6, 5], [6, 6]
            ];
            break;
        case 'circle':
            positions = [
                [2, 4], [2, 5],
                [3, 3], [3, 6],
                [4, 2], [4, 7],
                [5, 2], [5, 7],
                [6, 3], [6, 6],
                [7, 4], [7, 5]
            ];
            break;
        case 'triangle':
            positions = [
                [3, 5],
                [4, 4], [4, 6],
                [5, 3], [5, 7],
                [6, 2], [6, 4], [6, 5], [6, 6], [6, 8]
            ];
            break;
        case 'heart':
            positions = [
                [2, 3], [2, 6],
                [3, 2], [3, 4], [3, 5], [3, 7],
                [4, 2], [4, 7],
                [5, 3], [5, 6],
                [6, 4], [6, 5],
            ];
            break;
    }
    
    // Place elements at the new positions
    elements.forEach((el, index) => {
        if (index < positions.length) {
            const [row, col] = positions[index];
            const cell = document.querySelector(`.grid-cell[data-row="${row}"][data-col="${col}"]`);
            if (cell) {
                cell.appendChild(el);
                
                // Add animation effect
                el.classList.add('transform-animation');
                setTimeout(() => {
                    el.classList.remove('transform-animation');
                }, 800);
            }
        }
    });
    
    logMessage(`Elements rearranged into ${shape} formation.`);
}


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

// Helper function to select an element
function selectElement(element) {
    // Deselect any currently selected elements
    document.querySelectorAll('.matter-element').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Select the clicked element
    element.classList.add('selected');
    
    // Log the selection
    const elementId = element.dataset.id;
    const cell = element.parentNode;
    logMessage(`Element ${elementId} selected at position (${cell.dataset.col}, ${cell.dataset.row})`, 'normal');
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

// Add CSS for target cells
const style = document.createElement('style');
style.innerHTML = `
.target-cell {
    background: rgba(0, 184, 255, 0.1);
    box-shadow: inset 0 0 8px rgba(0, 184, 255, 0.3);
}
`;
document.head.appendChild(style);