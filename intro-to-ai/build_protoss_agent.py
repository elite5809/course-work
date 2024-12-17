# build_protoss_agent.py

### IMPORTS ###
from absl import app
from pysc2.agents import base_agent as base_ag
from pysc2.env import sc2_env as base_env
from pysc2.env import run_loop
from pysc2.lib import actions, features, units
import numpy as np
import random

class ProtoAgent(base_ag.BaseAgent):
    # Sets up the ProtoAgent object
    def __init__(self):
        # Set up basic variables needed from BaseAgent
        super(ProtoAgent, self).__init__()
        # Tracks base location
        self.base_top_left = None

    # Calculating distance
    def get_distances(self, obs, units, xy):
        # Getting unit coordinates
        units_xy = [(unit.x, unit.y) for unit in units]
        # Calculating distances for the units
        return np.linalg.norm(np.array(units_xy) - np.array(xy), axis = 1)

    # Returns the list of my units that corrispond to the unit type wanted
    def get_my_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.raw_units 
                if unit.unit_type == unit_type 
                and unit.alliance == features.PlayerRelative.SELF]

    # Checked for completed units
    def get_my_completed_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.raw_units
                if unit.unit_type == unit_type
                and unit.build_progress == 100
                and unit.alliance == features.PlayerRelative.SELF]

    # Order of priority for actions are based here
    def step(self, obs):
        # Need to call back to BaseAgent for setting up the step
        super(ProtoAgent, self).step(obs)
        # Simplifies code by putting actions.FUNCTIONS in action_pool
        action_pool = actions.RAW_FUNCTIONS
        
        # Checks if this is our first step
        # Sets up the attack coords by choosing coords opposite of our relative starting view
        if obs.first():
            # Determine base position for nexus
            nexus = self.get_my_units_by_type(obs, units.Protoss.Nexus)[0]
            self.base_top_left = (nexus.x < 32)

        # Getting Pylons
        pylons = self.get_my_units_by_type(obs, units.Protoss.Pylon)

        # Determine if there are pylons on the map
        if len(pylons) == 0 and obs.observation.player.minerals >= 100:
            # Getting probes
            probes = self.get_my_units_by_type(obs, units.Protoss.Probe)

            # Finding if there is at least 1 probe on the map
            if len(probes) > 0:
                # Builing pylon at certain location
                pylon_xy = (22, 20) if self.base_top_left else (35, 42)
                # Getting the distance between the probe and pylon
                distances = self.get_distances(obs, probes, pylon_xy)
                # Getting probe with shortest distance
                probe = probes[np.argmin(distances)]
                # Telling Probe to build pylon
                return actions.RAW_FUNCTIONS.Build_Pylon_pt("now", probe.tag, pylon_xy)

        # Getting completed pylons
        completed_pylons = self.get_my_completed_units_by_type(obs, units.Protoss.Pylon)
        # Getting gateways
        gateways = self.get_my_units_by_type(obs, units.Protoss.Gateway)

        # Check for pylons, no gateways, and enough minerals
        if (len(completed_pylons) > 0 and len(gateways) == 0 and 
            obs.observation.player.minerals >= 150):
            # Getting probes
            probes = self.get_my_units_by_type(obs, units.Protoss.Probe)
            if len(probes) > 0:
                # Determine gateway location
                gateway_xy = (22, 24) if self.base_top_left else (35, 45)
                # Calculate distance to gateway location
                distances = self.get_distances(obs, probes, gateway_xy)
                # Find closest probe
                probe = probes[np.argmin(distances)]
                # Build gateway
                return actions.RAW_FUNCTIONS.Build_Gateway_pt("now", probe.tag, gateway_xy)

        # Getting completed gateways
        completed_gateways = self.get_my_completed_units_by_type(obs, units.Protoss.Gateway)
        # Calculate free supplies
        free_supply = (obs.observation.player.food_cap - 
                        obs.observation.player.food_used)
        # Check if we have a gateway, enough minerals, and enough supplies
        if (len(completed_gateways) > 0 and obs.observation.player.minerals >= 100 
            and free_supply >= 2):
            # Select gateway
            gateway = gateways[0]
            if gateway.order_length < 5:
                return actions.RAW_FUNCTIONS.Train_Zealot_quick("now", gateway.tag)

        # Selecting all zealots
        zealots = self.get_my_units_by_type(obs, units.Protoss.Zealot)
        # Attack once no free supplies are left
        if free_supply < 2 and len(zealots) > 0:
            # Attack coordinates
            attack_xy = (38, 44) if self.base_top_left else (19, 23)
            # Calculating distance to target
            distances = self.get_distances(obs, zealots, attack_xy)
            # Choosing furthest zealot
            zealot = zealots[np.argmax(distances)]
            # Choosing random locations within 4 points of attack_xy
            x_offset = random.randint(-4, 4)
            y_offset = random.randint(-4, 4)
            return actions.RAW_FUNCTIONS.Attack_pt(
                "now", zealot.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset))

        return action_pool.no_op()

def main(argv):
    agent = ProtoAgent()
    # Allows quit via ctrl+c
    try:
        # Runs the game on loop
        while True:
            # Creates the game environment
            with base_env.SC2Env(
                map_name = "Simple64", # Map to play on
                players = [
                    base_env.Agent(base_env.Race.protoss), # Our agent
                    base_env.Bot(base_env.Race.protoss, # Enemy agent
                                 base_env.Difficulty.very_easy)
                ],
                agent_interface_format = features.AgentInterfaceFormat( # Sets up the screen and minimap
                    action_space = actions.ActionSpace.RAW, # Sets action space with RAW functions
                    use_raw_units = True, # Set units to RAW
                    raw_resolution = 64 # Convert RAW resolution from world space to 64
                )) as env:
                run_loop.run_loop([agent], env)         
    except KeyboardInterrupt:
        pass
  
if __name__ == "__main__":
    app.run(main)