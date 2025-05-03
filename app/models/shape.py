import numpy as np
import math 
class ShapeGenerator:
    """Generates target positions for different shapes."""
    @staticmethod
    def generate_shape(shape_type, num_elements, grid_width, grid_height):
        """Generate target positions for the specified shape."""
        if shape_type == "square":
            return ShapeGenerator.generate_square(num_elements, grid_width, grid_height)
        elif shape_type == "circle":
            return ShapeGenerator.generate_circle(num_elements, grid_width, grid_height)
        elif shape_type == "triangle":
            return ShapeGenerator.generate_triangle(num_elements, grid_width, grid_height)
        elif shape_type == "heart":
            return ShapeGenerator.generate_heart(num_elements, grid_width, grid_height)
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")
        
    @staticmethod
    def generate_square(num_elements, grid_width, grid_height):
        """Generate a square shape with positions matching frontend expectations."""
        # Calculate the side length of the square
        side_length = math.ceil(math.sqrt(num_elements))
        
        # Center the square in the grid
        start_x = (grid_width - side_length) // 2
        start_y = (grid_height - side_length) // 2
        
        # Generate positions in (x,y) format but in a way that matches
        # the frontend's [row, col] visual layout
        positions = []
        for y in range(start_y, start_y + side_length):
            for x in range(start_x, start_x + side_length):
                # Note: We store coordinates as (x,y) where x=col, y=row
                positions.append((x, y))
                if len(positions) >= num_elements:
                    break
            if len(positions) >= num_elements:
                break

        # Debug output to see generated positions
        print(f"SQUARE POSITIONS GENERATED (x,y format):")
        for i, (x, y) in enumerate(positions):
            print(f"  Position {i}: ({x},{y})")
            
        return positions
    
    @staticmethod
    def generate_circle(num_elements, grid_width, grid_height):
        """Generate a circle shape using a predefined pattern of agents per row."""
        positions = []
        remaining = num_elements
        
        # Base configuration for the circle shape
        base_agents = 20
        
        # Define how many agents should be in each row for the base configuration
        row_pattern = [2, 4, 4, 4, 4, 2]
        
        # Define which rows should have gaps in the middle
        rows_with_gaps = [2, 3]
        
        # If we have additional agents beyond the base configuration,
        # adjust the row pattern to add 2 agents per row
        if num_elements > base_agents:
            # Calculate additional agents beyond the base
            additional_agents = num_elements - base_agents
            
            # Each set of 12 additional agents adds 2 agents per row to the 6 rows
            sets_of_12 = additional_agents // 12
            remaining_extra = additional_agents % 12
            
            # Modify row pattern to add 2 agents per row for each complete set of 12
            modified_row_pattern = row_pattern.copy()
            for i in range(len(modified_row_pattern)):
                modified_row_pattern[i] += 2 * sets_of_12
            
            # Distribute any remaining extra agents (less than 12) evenly
            # starting from the middle rows
            distribution_order = [2, 3, 1, 4, 0, 5]  # Priority of rows to add extra agents
            
            for i in range(remaining_extra // 2):  # Add 2 agents at a time
                if i < len(distribution_order):
                    row_idx = distribution_order[i]
                    modified_row_pattern[row_idx] += 2
            
            # Use the modified pattern
            row_pattern = modified_row_pattern
        
        # Calculate vertical offset to center the pattern
        vertical_offset = (grid_height - len(row_pattern)) // 2
        
        # Place agents according to the pattern
        for row_idx, agents_in_row in enumerate(row_pattern):
            # If we've placed all agents, stop
            if remaining <= 0:
                break
                
            # Calculate actual row position with offset
            actual_row = row_idx + vertical_offset
                
            # If we've reached the bottom of the grid, stop
            if actual_row >= grid_height:
                break
                
            # Calculate how many agents to place in this row
            agents_to_place = min(agents_in_row, remaining)
            
            # For rows that need a gap in the middle
            if row_idx in rows_with_gaps:
                # Calculate how many agents to place on each side of the gap
                agents_per_side = agents_in_row // 2
                
                # Calculate the size of the gap (always maintain 2 empty cells in the middle)
                gap_size = 2
                
                # Calculate the starting column for the left side
                left_start = (grid_width - (agents_per_side * 2 + gap_size)) // 2
                
                # Left side agents
                for i in range(agents_per_side):
                    if remaining <= 0:
                        break
                    positions.append((left_start + i, actual_row))
                    remaining -= 1
                
                # Right side agents (after the gap)
                right_start = left_start + agents_per_side + gap_size
                for i in range(agents_per_side):
                    if remaining <= 0:
                        break
                    positions.append((right_start + i, actual_row))
                    remaining -= 1
            else:
                # For other rows, center the agents
                start_col = (grid_width - agents_in_row) // 2
                for i in range(agents_to_place):
                    if remaining <= 0:
                        break
                    positions.append((start_col + i, actual_row))
                    remaining -= 1
        
        # If we still have agents left to place, add them in rows below the pattern
        if remaining > 0:
            current_row = vertical_offset + len(row_pattern)
            
            while remaining > 0 and current_row < grid_height:
                # Place up to grid_width agents per row
                agents_to_place = min(grid_width, remaining)
                start_col = (grid_width - agents_to_place) // 2
                
                for i in range(agents_to_place):
                    positions.append((start_col + i, current_row))
                    remaining -= 1
                    
                current_row += 1
        
        # Ensure we don't exceed the requested number of elements
        return positions[:num_elements]
    

    @staticmethod
    def calculate_min_grid_size(num_agents):
        """
        Calculate the minimum required grid size for a triangle formation
        where each row has 2 more agents than the previous row.
        Formula: r(r + 1) ≤ num_agents, where r is the number of rows.
        """
        r = 0
        while r * (r + 1) < num_agents:
            r += 1
        return r + 1  # Add 1 for buffer    

    @staticmethod
    def generate_triangle(num_elements, grid_width, grid_height):
        """
        Generate a triangle shape where each row has 2 more elements than the previous row.
        The top row starts with 2 elements.
        """
        positions = []
        
        # Calculate the number of rows needed for the triangle
        # Using the formula r(r+1) ≤ num_agents where r is the number of rows
        r = int((-1 + math.sqrt(1 + 4 * num_elements)) / 2)
        
        # If we can't even fill the first row with 2 agents, adjust
        if r < 1 and num_elements >= 2:
            r = 1
        
        # Calculate how many elements we'll use in complete rows
        elements_in_complete_rows = r * (r + 1)
        
        # Remaining elements for the last partial row (if any)
        remaining_elements = num_elements - elements_in_complete_rows
        
        # Determine elements per row (starting from the top with 2 elements)
        elements_per_row = []
        for i in range(r):
            elements_per_row.append(2 * (i + 1))  # 2, 4, 6, 8, ...
        
        # Add the last partial row if needed
        if remaining_elements > 0:
            elements_per_row.append(remaining_elements)
        
        # Generate positions for each row
        for row, num_in_row in enumerate(elements_per_row):
            # Center the elements in this row
            start_col = (grid_width - num_in_row) // 2
            
            # Add positions for this row
            for col in range(num_in_row):
                positions.append((start_col + col, row))
        
        # Adjust positions to be centered in the grid vertically
        total_rows = len(elements_per_row)
        vertical_offset = (grid_height - total_rows) // 2
        
        # Apply vertical centering
        centered_positions = [(x, y + vertical_offset) for x, y in positions]
        
        return centered_positions[:num_elements]
        
    @staticmethod
    def generate_heart(num_elements, grid_width, grid_height):
        """
        Generate a heart shape that works best with exactly 12 blocks.
        If more than 12 blocks are requested, still return 12 positions
        and print a warning that the heart shape works best with 12 elements.
        """
        # Define the fixed heart positions (12 blocks) exactly as in the JavaScript code
        heart_template = [
            (2, 3), (2, 6),                  # Top curves (2)
            (3, 2), (3, 4), (3, 5), (3, 7),  # Upper middle row (4)
            (4, 2), (4, 7),                  # Middle section (2)
            (5, 3), (5, 6),                  # Bottom curves start (2)
            (6, 4), (6, 5),                  # Bottom middle (2)
        ]
        
        # Check if more than 12 elements are requested
        if num_elements > 12:
            print(f"WARNING: Heart shape works best with exactly 12 elements. Currently using {num_elements} elements.")
            print("Please set the number of agents to 12 for the best heart shape.")
            # Still proceed with 12 elements
            actual_num = 12
        else:
            actual_num = num_elements
        
        # Calculate the offset to center the heart in the grid
        row_offset = (grid_height - 10) // 2
        col_offset = (grid_width - 10) // 2
        
        # Apply the offset to center the heart - convert from [row,col] to (x,y) format
        centered_positions = [(col + col_offset, row + row_offset) for row, col in heart_template]
        
        # Take only as many positions as needed (up to 12)
        result_positions = centered_positions[:actual_num]
        
        # Debug output
        print(f"HEART POSITIONS GENERATED (x,y format):")
        for i, (x, y) in enumerate(result_positions):
            print(f"  Position {i}: ({x},{y})")
        
        return result_positions

    @staticmethod
    def validate_positions(positions, grid):
        """Filter out positions that would be invalid in the grid."""
        valid_positions = []
        for x, y in positions:
            if grid.is_valid_position(x, y) and not grid.is_wall(x, y):
                valid_positions.append((x, y))
        return valid_positions