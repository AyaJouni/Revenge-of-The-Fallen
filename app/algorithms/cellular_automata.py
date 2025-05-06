import random

def decide_next_move(element, grid, topology):
    if not element.has_target() or element.at_target():
        return None

    # Get empty neighboring cells
    neighbors = grid.get_neighbors(element.x, element.y, topology)
    valid = [(x, y) for x, y in neighbors if grid.is_empty(x, y)]
    if not valid:
        return None

    # 1. Gradient: choose neighbor minimizing distance to target
    gradient = sorted(valid, key=lambda p: abs(p[0]-element.target_x)+abs(p[1]-element.target_y))
    move_grad = gradient[0]

    # 3. Direct step along major axis
    dx, dy = element.target_x-element.x, element.target_y-element.y
    step = (element.x + (1 if dx>0 else -1 if dx<0 else 0), element.y) if abs(dx)>abs(dy) else (element.x, element.y + (1 if dy>0 else -1 if dy<0 else 0))
    move_direct = step if step in valid else None

    # 4. Random
    move_rand = random.choice(valid)

    # Priority logic
    if move_grad==move_direct:
        return move_grad
    if random.random()<0.8:
        return move_grad
    if move_direct and random.random()<0.6:
        return move_direct
    return move_rand