# empty_agent.py

import random
import numpy as np
from absl import app
from pysc2.agents import base_agent
from pysc2.lib import actions, features, units
from pysc2.env import sc2_env, run_loop

class TestAgent(base_agent.BaseAgent):
  ''' This is just an agent that doesn't move.
      Just for testing the installation
      The boilerplate code is modeled after the second 
      tutorial you'll do, and creates a Terran center 
      that does nothing beyond the default mining of minerals.
  ''' 
  def step(self, obs):
    super(TestAgent, self).step(obs)


    return actions.RAW_FUNCTIONS.no_op()

def main(unused_argv):
  agent = TestAgent()
  try:
    while True:
      with sc2_env.SC2Env(
          # If this one doesn't work, you'll need to download the Melee maps.
          # In the meantime, you can switch to the AbyssalReef, which you should have.
          map_name="Simple64", 
#          map_name="AbyssalReef",
          players=[sc2_env.Agent(sc2_env.Race.terran), 
                   sc2_env.Bot(sc2_env.Race.zerg, 
                               sc2_env.Difficulty.very_easy)],
          agent_interface_format=features.AgentInterfaceFormat(
              action_space=actions.ActionSpace.RAW,
              use_raw_units=True,
              raw_resolution=64,
          ),
      ) as env:
        run_loop.run_loop([agent], env)
  except KeyboardInterrupt:
    pass


if __name__ == "__main__":
  app.run(main)
