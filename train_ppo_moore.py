# train_ppo_moore.py

import os
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback

from pm_env_moore import ProgrammableMatterEnvMoore
from app.controllers.simulation import ProgrammableMatterSimulation

def make_env():
    """
    Create a Gym environment that on each episode:
     - Randomly picks one agent from the simulation
     - Passes all the *other* agents' positions into the env as obstacles
     - Exposes the neighbor‐aware obs + collision penalty
    """
    sim = ProgrammableMatterSimulation(width=12, height=12)
    sim.initialize_elements(20)
    sim.set_target_shape('square', 20)
    sim.controller.assign_targets()

    class SingleAgentEnv(gym.Env):
        def __init__(self):
            super().__init__()
            self.sim = sim
            self.grid = sim.grid

            # These will be set in reset()
            self.eid      = None
            self.env      = None

            # Action & obs spaces are fixed
            self.action_space = spaces.Discrete(9)
            low  = np.array([0,0,0,0] + [0]*8, dtype=np.float32)
            high = np.array(
                [self.grid.width-1, self.grid.height-1,
                 self.grid.width-1, self.grid.height-1] + [1]*8,
                dtype=np.float32
            )
            self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        def reset(self, *, seed=None, options=None):
            # Pick a random agent
            rng_keys = list(self.sim.controller.elements.keys())
            self.eid = (np.random.RandomState(seed)
                        .choice(rng_keys)) if seed is not None else np.random.choice(rng_keys)
            elem = self.sim.controller.elements[self.eid]

            start  = (elem.x, elem.y)
            target = (elem.target_x, elem.target_y)

            # Compute the OTHER agents as obstacles
            obstacles = {
                (other.x, other.y)
                for oid, other in self.sim.controller.elements.items()
                if oid != self.eid
            }

            # Create the environment with dynamic obstacle set
            self.env = ProgrammableMatterEnvMoore(
                grid      = self.grid,
                start_pos = start,
                target_pos= target,
                obstacles = obstacles,       # <-- pass neighbors in
                max_steps = 200,
                collision_penalty = -5.0,
                success_reward    = 50.0
            )

            # Seed and reset
            obs, info = self.env.reset(seed=seed)
            return obs, info

        def step(self, action):
            return self.env.step(action)

    return SingleAgentEnv()


if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)

    env = make_env()
    checkpoint_cb = CheckpointCallback(
        save_freq  = 20_000,
        save_path  = "models/",
        name_prefix= "ppo_moore"
    )
   

    model = PPO(
        policy         = "MlpPolicy",  #feedforward policy
        env            = env,
        verbose        = 1,
        learning_rate  = 3e-4,
        batch_size     = 64,
        gamma          = 0.99,
    )

    # Train for 500k timesteps, saving intermediate checkpoints
    model.learn(total_timesteps=500_000, callback=checkpoint_cb)

    # Final save
    model.save("models/ppo_moore_final")
    print("Training complete, model saved to models/ppo_moore_final.zip")
