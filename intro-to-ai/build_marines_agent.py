# build_marines_agent.py

### IMPORTS ###
import numpy as np
import random
from absl import app
from loop_helper import *
from pysc2.agents import base_agent as base_ag
from pysc2.env import sc2_env as base_env
from pysc2.lib import actions, features, units

### GLOBALS ###
# Simplifies code by putting actions.FUNCTIONS in ACTION_POOL
ACTION_POOL = actions.RAW_FUNCTIONS
ALLIANCE_LIST = features.PlayerRelative
RACE_UNITS = units.Terran

PROTOSS_UNITS = [
    units.Protoss.Adept,
    units.Protoss.Archon,
    units.Protoss.Carrier,
    units.Protoss.Colossus,
    units.Protoss.DarkTemplar,
    units.Protoss.Disruptor,
    units.Protoss.DisruptorPhased,
    units.Protoss.HighTemplar,
    units.Protoss.Immortal,
    units.Protoss.Interceptor,
    units.Protoss.Mothership,
    units.Protoss.MothershipCore,
    units.Protoss.Observer,
    units.Protoss.ObserverSurveillanceMode,
    units.Protoss.Oracle,
    units.Protoss.Phoenix,
    units.Protoss.Probe,
    units.Protoss.Sentry,
    units.Protoss.Stalker,
    units.Protoss.Tempest,
    units.Protoss.VoidRay,
    units.Protoss.WarpPrism,
    units.Protoss.WarpPrismPhasing,
    units.Protoss.Zealot
]
PROTOSS_BUILDINGS = [
    units.Protoss.Assimilator,
    units.Protoss.AssimilatorRich,
    units.Protoss.CyberneticsCore,
    units.Protoss.DarkShrine,
    units.Protoss.FleetBeacon,
    units.Protoss.Forge,
    units.Protoss.Gateway,
    units.Protoss.Nexus,
    units.Protoss.PhotonCannon,
    units.Protoss.Pylon,
    units.Protoss.PylonOvercharged,
    units.Protoss.RoboticsBay,
    units.Protoss.RoboticsFacility,
    units.Protoss.ShieldBattery,
    units.Protoss.Stargate,
    units.Protoss.StasisTrap,
    units.Protoss.TemplarArchive,
    units.Protoss.TwilightCouncil,
    units.Protoss.WarpGate
]
TERRAN_UNITS = [
    units.Terran.Banshee,
    units.Terran.Battlecruiser,
    units.Terran.Cyclone,
    units.Terran.Ghost,
    units.Terran.Hellbat,
    units.Terran.Hellion,
    units.Terran.Liberator,
    units.Terran.LiberatorAG,
    units.Terran.Marine,
    units.Terran.Marauder,
    units.Terran.Medivac,
    units.Terran.MULE,
    units.Terran.Raven,
    units.Terran.Reaper,
    units.Terran.RepairDrone,
    units.Terran.SCV,
    units.Terran.SiegeTank,
    units.Terran.Thor,
    units.Terran.ThorHighImpactMode,
    units.Terran.VikingAssault,
    units.Terran.VikingFighter
]
TERRAN_BUILDINGS = [
    units.Terran.Armory,
    units.Terran.Barracks,
    units.Terran.BarracksFlying,
    units.Terran.BarracksReactor,
    units.Terran.BarracksTechLab,
    units.Terran.Bunker,
    units.Terran.CommandCenter,
    units.Terran.CommandCenterFlying,
    units.Terran.EngineeringBay,
    units.Terran.Factory,
    units.Terran.FactoryFlying,
    units.Terran.FactoryReactor,
    units.Terran.FactoryTechLab,
    units.Terran.FusionCore,
    units.Terran.GhostAcademy,
    units.Terran.MissileTurret,
    units.Terran.OrbitalCommand,
    units.Terran.OrbitalCommandFlying,
    units.Terran.PlanetaryFortress,
    units.Terran.Reactor,
    units.Terran.Refinery,
    units.Terran.SensorTower,
    units.Terran.Starport,
    units.Terran.StarportFlying,
    units.Terran.StarportReactor,
    units.Terran.StarportTechLab,
    units.Terran.SupplyDepot,
    units.Terran.SupplyDepotLowered,
    units.Terran.TechLab
]
ZERG_UNITS = [
    units.Zerg.Baneling,
    units.Zerg.BanelingBurrowed,
    units.Zerg.BanelingCocoon,
    units.Zerg.Broodling,
    units.Zerg.BroodLord,
    units.Zerg.Changeling,
    units.Zerg.ChangelingMarine,
    units.Zerg.ChangelingMarineShield,
    units.Zerg.ChangelingZealot,
    units.Zerg.ChangelingZergling,
    units.Zerg.ChangelingZerglingWings,
    units.Zerg.Cocoon,
    units.Zerg.Corruptor,
    units.Zerg.Drone,
    units.Zerg.Hydralisk,
    units.Zerg.HydraliskBurrowed,
    units.Zerg.InfestedTerran,
    units.Zerg.Infestor,
    units.Zerg.InfestorBurrowed,
    units.Zerg.Larva,
    units.Zerg.Lurker,
    units.Zerg.LurkerBurrowed,
    units.Zerg.LurkerCocoon,
    units.Zerg.Mutalisk,
    units.Zerg.Overlord,
    units.Zerg.OverlordTransport,
    units.Zerg.OverlordTransportCocoon,
    units.Zerg.Overseer,
    units.Zerg.OverseerCocoon,
    units.Zerg.OverseerOversightMode,
    units.Zerg.ParasiticBombDummy,
    units.Zerg.Queen,
    units.Zerg.QueenBurrowed,
    units.Zerg.Ravager,
    units.Zerg.Roach,
    units.Zerg.SwarmHost,
    units.Zerg.Ultralisk,
    units.Zerg.Viper,
    units.Zerg.Zergling
]
ZERG_BUILDINGS = [
    units.Zerg.BanelingNest,
    units.Zerg.CreepTumor,
    units.Zerg.CreepTumorBurrowed,
    units.Zerg.EvolutionChamber,
    units.Zerg.Extractor,
    units.Zerg.GreaterSpire,
    units.Zerg.Hatchery,
    units.Zerg.Hive,
    units.Zerg.HydraliskDen,
    units.Zerg.InfestationPit,
    units.Zerg.Lair,
    units.Zerg.LurkerDen,
    units.Zerg.NydusCanal,
    units.Zerg.NydusNetwork,
    units.Zerg.RoachWarren,
    units.Zerg.SpawningPool,
    units.Zerg.SpineCrawler,
    units.Zerg.SpineCrawlerUprooted,
    units.Zerg.Spire,
    units.Zerg.SporeCrawler,
    units.Zerg.SporeCrawlerUprooted,
    units.Zerg.UltraliskCavern
]

### CLASSES ###
# Agent class
class TerranAgent(base_ag.BaseAgent):

    # OVERRIDE METHODS
    # Sets up the TerranAgent object
    def __init__(self):
        # Set up basic variables needed from BaseAgent
        super(TerranAgent, self).__init__()

        # Agent constants
        self.NUM_BUILDERS = 2
        self.SETUP_DEPOTS = 4
        self.SETUP_BARRACKS = 2

        # Episode variables
        self.base_top_left = None
        self.is_setup = False
        self.is_random = True
        self.enemy_type = 0

        # Step variables
        self.curr_builders = []
        self.last_builder = -1
        self.last_barrack = -1

    # Need to reset variables when we reset the game
    def reset(self, do_random = True):
        super(TerranAgent, self).reset()
        self.steps = 0
        self.base_top_left = None
        self.is_setup = False
        self.is_random = do_random
        self.enemy_type = 0
        self.curr_builders = []
        self.last_builder = -1
        self.last_barrack = -1
    
    # HELPER FUNCTIONS
    # Calculating distance
    def get_distances(self, units, xy):
        # Getting unit coordinates
        units_xy = [(unit.x, unit.y) for unit in units]
        # Calculating distances for the units
        return np.linalg.norm(np.array(units_xy) - np.array(xy), axis = 1)

    # Returns the list of my units that corrispond to the unit type wanted
    def get_my_units_by_type(self, obs, unit_type, is_completed = False):
        units = []
        for unit in obs.observation.raw_units:
            if unit.unit_type == unit_type and unit.alliance == ALLIANCE_LIST.SELF:
                if not is_completed:
                    units.append(unit)
                elif unit.build_progress == 100: # Implication that we want completed units
                    units.append(unit)
        return units

    def get_enemy_units(self, obs, is_building = False):
        units = []
        for unit in obs.observation.raw_units:
            if unit.alliance == ALLIANCE_LIST.ENEMY:
                if self.enemy_type == 0:
                    if unit.unit_type in TERRAN_UNITS or unit.unit_type in TERRAN_BUILDINGS:
                        self.enemy_type = 1
                    elif unit.unit_type in PROTOSS_UNITS or unit.unit_type in PROTOSS_BUILDINGS:
                        self.enemy_type = 2
                    elif unit.unit_type in ZERG_UNITS or unit.unit_type in ZERG_BUILDINGS:
                        self.enemy_type = 3
                if (is_building and 
                   (unit.unit_type in TERRAN_BUILDINGS or 
                    unit.unit_type in PROTOSS_BUILDINGS or 
                    unit.unit_type in ZERG_BUILDINGS)):
                    units.append(unit)
                elif (unit.unit_type in TERRAN_UNITS or 
                      unit.unit_type in PROTOSS_UNITS or
                      unit.unit_type in ZERG_UNITS):
                    units.append(unit)
        return units

    # STEP FUNCTIONS
    # Scripted setup of the base
    def start_setup(self, obs):
        if self.is_setup:
            return None
        
        # Get current resources
        minerals = obs.observation.player.minerals
        # Calculate free supplies
        supply = (obs.observation.player.food_cap - obs.observation.player.food_used)
        # Getting depots
        depots = self.get_my_units_by_type(obs, RACE_UNITS.SupplyDepot)
        # Getting completed depots
        complete_depots = self.get_my_units_by_type(obs, RACE_UNITS.SupplyDepot, is_completed = True)
        # Getting barracks
        barracks = self.get_my_units_by_type(obs, RACE_UNITS.Barracks)
        # Getting completed barracks
        complete_barracks = self.get_my_units_by_type(obs, RACE_UNITS.Barracks, is_completed = True)

        num_all_buildings = len(depots) + len(barracks)
        num_complete_buildings = len(complete_depots) + len(complete_barracks)

        # Build first depot
        if len(depots) == 0 and minerals >= 100:
            # Determine depot location
            depots_xy = (16, 26) if self.base_top_left else (36, 42)
            return self.build_structure(obs, RACE_UNITS.SupplyDepot, depots_xy)

        # Check for 1+ depots, enough minerals, and not already building the second barrack
        if (len(barracks) < self.SETUP_BARRACKS and len(complete_depots) >= 1 and minerals >= 150 and
            not (num_all_buildings >= num_complete_buildings + self.NUM_BUILDERS)):
            # Determine barrack location
            barrack_xy = (24, 18 + (4 * len(barracks))) if self.base_top_left else (34, 46 + (4 * len(barracks)))
            return self.build_structure(obs, RACE_UNITS.Barracks, barrack_xy)

        # Set up supply depots to fufill requirement
        if (len(depots) < self.SETUP_DEPOTS and len(barracks) >= 1 and minerals >= 100 and 
            not (num_all_buildings >= num_complete_buildings + self.NUM_BUILDERS)):
            # Determine depot location
            depots_xy = (16 + (2 * len(depots)), 26) if self.base_top_left else (36 + (2 * len(depots)), 42)
            return self.build_structure(obs, RACE_UNITS.SupplyDepot, depots_xy)

        # Get builders back to work when done building
        if len(complete_depots) >= self.SETUP_DEPOTS and len(complete_barracks) >= self.SETUP_BARRACKS and len(self.curr_builders) > 0:
            # Clear current builders list
            tmp = self.curr_builders.copy()
            self.curr_builders.clear()

            # Grab closest mineral patch and send builders to it
            mineral_units = [unit for unit in obs.observation.raw_units
                        if unit.alliance == ALLIANCE_LIST.NEUTRAL]
            mineral_unit = mineral_units[np.argmin(self.get_distances(mineral_units, (tmp[0].x, tmp[0].y)))]
            return ACTION_POOL.Harvest_Gather_unit("now", [scv.tag for scv in tmp], mineral_unit.tag)

        # Build marines until we have no supply left
        if (len(complete_barracks) > 0 and minerals >= 100 and supply > 0):
            return self.train_unit(complete_barracks, RACE_UNITS.Marine)

        # Check if we have enough depots and barracks; if so, leave it to the agent
        if len(complete_depots) >= self.SETUP_DEPOTS and len(complete_barracks) >= self.SETUP_BARRACKS and supply == 0:
            self.is_setup = True
            return None

        # If we get here, we have no idea what to do
        return ACTION_POOL.no_op()

    # Order of priority for actions are based here
    def step(self, obs):
        # Need to call back to BaseAgent for setting up the step
        super(TerranAgent, self).step(obs)

        # Checks if this is our first step
        if obs.first():
            # Determine base position for Command Center
            base = self.get_my_units_by_type(obs, RACE_UNITS.CommandCenter)[0]
            self.base_top_left = (base.x < 32)

        # If we are in the setup phase, do that; if not, up to neural network
        return self.start_setup(obs)

    def export_inputs(self, obs):
        # Get my units
        my_marines = self.get_my_units_by_type(obs, RACE_UNITS.Marine)
        # Get enemy buildings
        enemy_buildings = self.get_enemy_units(obs, True)
        # Get enemy buildings in each quadrant
        quad_enemy_buildings = [[], [], [], []]
        for building in enemy_buildings:
            if building.x < 32 and building.y < 32:
                quad_enemy_buildings[0 if self.base_top_left else 3].append(building)
            elif building.x < 32 and building.y >= 32:
                quad_enemy_buildings[2 if self.base_top_left else 1].append(building)
            elif building.x >= 32 and building.y < 32:
                quad_enemy_buildings[1 if self.base_top_left else 2].append(building)
            elif building.x >= 32 and building.y >= 32:
                quad_enemy_buildings[3 if self.base_top_left else 0].append(building)

        inputs = {
            "num_my_army": len(my_marines),
            "num_enemy_buildings": len(enemy_buildings),
            "num_enemy_buildings_retreat_vertical": len(quad_enemy_buildings[1]),
            "num_enemy_buildings_retreat_horizontal": len(quad_enemy_buildings[2]),
            "num_enemy_buildings_enemy_base": len(quad_enemy_buildings[3]),
            "current_timestep": self.steps,
            "enemy_type": self.enemy_type # 0 - Dont know, 1 - Protoss, 2 - Terran, 3 - Zerg
        }
        return inputs

    # ACTION FUNCTIONS
    # Build a structure
    def build_structure(self, obs, structure_type, coords):
        # Getting SCVs
        scvs = self.get_my_units_by_type(obs, RACE_UNITS.SCV)
        # Finding if there is at least 1 SVC on the map
        if len(scvs) > 0:
            # Pre-selecting SCV to build
            while len(self.curr_builders) < min(self.NUM_BUILDERS, len(scvs)):
                # Getting the closet SVC to depot location
                closest_scv = scvs[np.argmin(self.get_distances(scvs, coords))]
                # Need unit tags to track units selected
                scv_tag_list = [scv.tag for scv in scvs]
                # De-select SVCs already assigned to build
                while closest_scv.tag in [builder.tag for builder in self.curr_builders]:
                    scvs.pop(scv_tag_list.index(closest_scv.tag))
                    scv_tag_list.remove(closest_scv.tag)
                    closest_scv = scvs[np.argmin(self.get_distances(scvs, coords))]
                self.curr_builders.append(closest_scv)

            match structure_type:
                # Building a depot
                case RACE_UNITS.SupplyDepot:
                    return ACTION_POOL.Build_SupplyDepot_pt("now", [builder.tag for builder in self.curr_builders], coords)
                case RACE_UNITS.Barracks:
                    return ACTION_POOL.Build_Barracks_pt("now", [builder.tag for builder in self.curr_builders], coords)
        return ACTION_POOL.no_op()

    def train_unit(self, barracks, unit_type):
        # Select barrack
        self.last_barrack = (self.last_barrack + 1) % len(barracks)
        barrack = barracks[self.last_barrack]
        # Train marines if queue is not full
        if barrack.order_length < 5:
            match unit_type:
                case RACE_UNITS.Marine:
                    return ACTION_POOL.Train_Marine_quick("now", barrack.tag)
        return ACTION_POOL.no_op()

    def attack_quadrant(self, obs, target_coords):
        # Selecting all marines
        marines = self.get_my_units_by_type(obs, RACE_UNITS.Marine)
        if len(marines) > 0:
            # Choosing random locations within 4 points of quadrant coordinates
            x_offset = random.randint(-6, 6)
            y_offset = random.randint(-6, 6)
            # Attack location
            return ACTION_POOL.Attack_pt("now", [marine.tag for marine in marines], (target_coords[0] + x_offset, target_coords[1] + y_offset))
        return ACTION_POOL.no_op()

### RUNTIME LOOP ###
def main(argv):
    # Check number of arguments
    if len(argv) == 1:
        print("Using defaults")
    elif len(argv) != 2 and len(argv) != 4:
        print(f"Usage: python3 {argv[0]} <hidden layers>")
        print("hidden layers: int w/ comma separated ints")
        print(f"Example: python3 {argv[0]} 32,64")
        print(f"Usage: python3 {argv[0]} <hidden layers> <epochs> <batch size>")
        print("hidden layers: int w/ comma separated ints")
        print(f"Example: python3 {argv[0]} 32,64,128 100 32")
        return
    else:
        # Check if arguments are valid
        try:
            argv[1] = [int(layer) for layer in argv[1].split(",")]
            if (len(argv) == 4):
                argv[2] = int(argv[2])
                argv[3] = int(argv[3])
        except ValueError:
            print("Invalid arguments")
            return

    agent = TerranAgent()
    # Allows quit via ctrl+c
    try:
        # Runs the game on loop
        while True:
            # Creates the game environment
            with base_env.SC2Env(
                map_name = "Simple64", # Map to play on
                players = [
                    base_env.Agent(base_env.Race.terran), # Our agent
                    base_env.Bot(base_env.Race.random, # Enemy agent
                                 base_env.Difficulty.very_easy)
                ],
                agent_interface_format = features.AgentInterfaceFormat( # Sets up the screen and minimap
                    action_space = actions.ActionSpace.RAW, # Sets action space with RAW functions
                    use_raw_units = True, # Set units to RAW
                    raw_resolution = 64 # Convert RAW resolution from world space to 64
                )) as env:
                run_loop(argv, [agent], env)
    except KeyboardInterrupt:
        pass
  
if __name__ == "__main__":
    app.run(main)
