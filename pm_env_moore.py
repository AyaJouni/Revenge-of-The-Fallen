import gymnasium as gym
from gymnasium import spaces
import numpy as np

class ProgrammableMatterEnvMoore(gym.Env):
    """
    RL environment on a 2D grid using Moore (8-neighborhood) moves,
    with dynamic collision avoidance.
    Observation: [ax,ay,tx,ty] + 8 neighbor-blocked flags = 12 dims.
    """

    def __init__(
        self,
        grid,
        start_pos,
        target_pos,
        obstacles=None,
        max_steps: int = 200,
        collision_penalty: float = -5.0,
        success_reward: float = 50.0
    ):
        super().__init__()
        self.grid              = grid
        self.max_steps         = max_steps
        self.collision_penalty = collision_penalty
        self.success_reward    = success_reward

        # Dynamic set of other-agent obstacles
        # Should be updated externally via update_obstacles(...)
        self.obstacles = set(obstacles) if obstacles is not None else set()

        # Agent and goal positions
        self.agent_pos  = np.array(start_pos,  dtype=np.int32)
        self.target_pos = np.array(target_pos, dtype=np.int32)
        self.step_count = 0

        # Discrete 9-action Moore moves
        self.action_space = spaces.Discrete(9)

        # Observation: (ax,ay,tx,ty) + 8 neighbor flags
        low  = np.array([0,0,0,0] + [0]*8, dtype=np.float32)
        high = np.array(
            [grid.width-1, grid.height-1,
             grid.width-1, grid.height-1] + [1]*8,
            dtype=np.float32
        )
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

    def update_obstacles(self, obstacles):
        """
        Call this at each time step to let the env know
        where the other agents currently sit.
        """
        self.obstacles = set(obstacles)

    def reset(self, *, seed=None, options=None):
        """Resets step counter; positions stay as constructed."""
        self.step_count = 0
        return self._get_obs(), {}

    def _get_obs(self):
        """Return [ax,ay,tx,ty] plus binary flags for each of 8 neighbors."""
        ax, ay = self.agent_pos
        tx, ty = self.target_pos

        # Check all 8 Moore neighbors
        offsets = [(-1, -1), (-1, 0), (-1, 1),
                   ( 0, -1),          ( 0, 1),
                   ( 1, -1), ( 1, 0), ( 1, 1)]
        flags = []
        for dx, dy in offsets:
            nx, ny = ax + dx, ay + dy
            blocked = (
                nx < 0 or ny < 0 or
                nx >= self.grid.width or
                ny >= self.grid.height or
                self.grid.is_occupied(nx, ny) or
                (nx, ny) in self.obstacles
            )
            flags.append(1.0 if blocked else 0.0)

        return np.array([ax, ay, tx, ty] + flags, dtype=np.float32)

    def step(self, action):
        """Apply `action`, avoid collisions, and return (obs, reward, done, _, _)."""
        self.step_count += 1
        old_pos = self.agent_pos.copy()

        # Define Moore moves: stay + 8 directions
        moves = [
            ( 0,  0), ( 0, -1), ( 0,  1),
            (-1,  0), ( 1,  0),
            (-1, -1), ( 1, -1),
            (-1,  1), ( 1,  1)
        ]
        dx, dy = moves[action]

        # Compute new position and clip to grid bounds
        raw_new = old_pos + np.array([dx, dy], dtype=int)
        new_pos = np.clip(
            raw_new,
            [0, 0],
            [self.grid.width - 1, self.grid.height - 1]
        )

        new_tup = (int(new_pos[0]), int(new_pos[1]))

        # Collision check (static grid or dynamic obstacles)
        if self.grid.is_occupied(*new_pos) or new_tup in self.obstacles:
            # illegal: revert and heavy penalty
            self.agent_pos = old_pos
            reward = self.collision_penalty
        else:
            # valid move
            self.agent_pos = new_pos
            # shaped reward: closer → positive, big bonus on success
            dist_old = np.linalg.norm(old_pos - self.target_pos)
            dist_new = np.linalg.norm(new_pos - self.target_pos)
            reward   = (dist_old - dist_new) * 2.0
            if np.array_equal(new_pos, self.target_pos):
                reward += self.success_reward

        done = (
            np.array_equal(self.agent_pos, self.target_pos) or
            self.step_count >= self.max_steps
        )

        return self._get_obs(), float(reward), bool(done), False, {}

