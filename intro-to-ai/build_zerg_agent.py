# build_zerg_agent.py

### IMPORTS ###
from absl import app
from pysc2.agents import base_agent as base_ag
from pysc2.env import sc2_env as base_env
from pysc2.lib import actions, features, units
import random

class ZergAgent(base_ag.BaseAgent):
    # Sets up the ZergAgent object
    def __init__(self):
        # Set up basic variables needed from BaseAgent
        super(ZergAgent, self).__init__()
        # Set default value to coordinates that we want to attack
        self.attack_coordinates = None

    # Checks whether an action can be executed
    def can_do(self, obs, action):
        return action in obs.observation.available_actions

    # Returns the list of units that corrispond to the unit type wanted
    def get_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.feature_units if unit.unit_type == unit_type]

    # Step for the next set of frames (controlled by step_mul)
    # Order of priority for actions are based here
    def step(self, obs):
        # Need to call back to BaseAgent for setting up the step
        super(ZergAgent, self).step(obs)
        # Simplifies code by putting actions.FUNCTIONS in action_pool
        action_pool = actions.FUNCTIONS
        
        # Checks if this is our first step
        # Sets up the attack coords by choosing coords opposite of our relative starting view
        if obs.first():
            # Checks where our units are on the map
            # Uses numpy list == enum where SELF is 1 and produces are true/false list
            # nonzero function converts all trues in outputted list into parallel arrays of x's and y's
            player_y, player_x = (obs.observation.feature_minimap.player_relative == 
                                  features.PlayerRelative.SELF).nonzero()
            # Averages of the x-posisitions and y-positions of our units
            xmean = player_x.mean()
            ymean = player_y.mean()
            # Checks if we are on the top-left or bottom-right side of the map
            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16)

        # Gets the list of all zerglings
        zerglings = self.get_units_by_type(obs, units.Zerg.Zergling)
        # If there are enough zerglings, attack
        if len(zerglings) >= 10:
            # Checks if zerglings are selected
            if self.unit_type_is_selected(obs, units.Zerg.Zergling):
                # Checks if we can attack
                if self.can_do(obs, action_pool.Attack_minimap.id):
                    # Returns the action to attack the coordinates
                    return action_pool.Attack_minimap("now", self.attack_coordinates)
            # Checks if we can select zerglings
            if self.can_do(obs, action_pool.select_army.id):
                # Returns the action to select all zerglings
                return action_pool.select_army("select")

        # Gets the list of all spawning pools
        spawning_pools = self.get_units_by_type(obs, units.Zerg.SpawningPool)
        # If there are no spawning pools, build one
        if len(spawning_pools) <= 0:
            # Checks if drones are selected
            if self.unit_type_is_selected(obs, units.Zerg.Drone): 
                # Checks if we can build a spawning pool
                if self.can_do(obs, action_pool.Build_SpawningPool_screen.id):
                    # Randomly chooses a location to build the spawning pool
                    x = random.randint(0, 83)
                    y = random.randint(0, 83)
                    return action_pool.Build_SpawningPool_screen("now", (x, y))

            # Gets the list of all drones
            drones = self.get_units_by_type(obs, units.Zerg.Drone)
            # Checks if we can select drones
            if len(drones) > 0:
                # Randomly chooses a drone to select and all drones near it
                drone = random.choice(drones)
                return action_pool.select_point("select_all_type", (drone.x, drone.y))

        # Gets the list of all larvae
        if self.unit_type_is_selected(obs, units.Zerg.Larva):
            # Calculates the "free supply" of our base
            free_supply = (obs.observation.player.food_cap -
                           obs.observation.player.food_used)

            # If we dont have free supply, train a overlord if we can
            if free_supply == 0:
               if self.can_do(obs, action_pool.Train_Overlord_quick.id):
                   return action_pool.Train_Overlord_quick("now")
            
            # If we have free supply, train a zergling if we can
            if self.can_do(obs, action_pool.Train_Zergling_quick.id):
                return action_pool.Train_Zergling_quick("now")

        # Gets the list of all larvae
        larvae = self.get_units_by_type(obs, units.Zerg.Larva)
        # Checks if we can select larvae
        if len(larvae) > 0:
            # Randomly chooses a larva to select and all larvae near it
            larva = random.choice(larvae)
            return action_pool.select_point("select_all_type", (larva.x, larva.y))

        return action_pool.no_op()

    # Checks if the unit type is current selected
    def unit_type_is_selected(self, obs, unit_type):
        # Checks if the unit type is selected via single select
        if (len(obs.observation.single_select) > 0 and
            obs.observation.single_select[0].unit_type == unit_type):
            return True

        # Checks if the unit type is selected via multi select
        if (len(obs.observation.multi_select) > 0 and
            obs.observation.multi_select[0].unit_type == unit_type):
            return True
    
        return False

def main(argv):
    agent = ZergAgent()
    # Allows quit via ctrl+c
    try:
        # Runs the game on loop
        while True:
            # Creates the game environment
            with base_env.SC2Env(
                map_name = "Simple64", # Map to play on
                players = [
                    base_env.Agent(base_env.Race.zerg), # Our agent
                    base_env.Bot(base_env.Race.terran, # Enemy agent
                                 base_env.Difficulty.very_easy)
                ],
                agent_interface_format = features.AgentInterfaceFormat( # Sets up the screen and minimap
                    feature_dimensions = features.Dimensions(screen = 84, minimap = 64),
                    use_feature_units = True
                ),
                step_mul = 16, # How many game frames per agent step
                game_steps_per_episode = 0, # Not sure what this does
                visualize = True) as env: # Enables AI visualization screen
                # Grabs the features of the map and actions
                agent.setup(env.observation_spec(), env.action_spec())

                # Start the environment
                timesteps = env.reset()
                # Tracks number of episodes
                agent.reset()

                # Runs through the game
                while True:
                    # Gives agent the current state of the game
                    step_actions = [agent.step(timesteps[0])]
                    # Break if the game is over
                    if timesteps[0].last():
                        break
                    # Updates the game
                    timesteps = env.step(step_actions)
    except KeyboardInterrupt:
        pass
  
if __name__ == "__main__":
    app.run(main)