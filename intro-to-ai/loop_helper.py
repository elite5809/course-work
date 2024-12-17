# loop_helper.py

### IMPORTS ###
import numpy as np
import random
import tensorflow as tf
import time
from keras import layers, models, Sequential
from keras.optimizers import Adam, SGD
from os import mkdir
from os.path import exists
from pysc2.lib import actions, units
from sklearn.preprocessing import normalize
from tensorflow import keras

### CONSTANTS ###
IS_TRAINING = True

# Neural Network Constants
NUM_INPUTS = 7
HIDDEN_LAYERS = [16]
EPOCHS = 100
BATCH_SIZE = 32
L_RATE = 0.001

# Game Constants
NUM_EPISODES = 10
STEP_CHANGE_QUAD = 144
ATTACK_INTERVAL = 16
QUADRANT_COORD = [(19, 23), (40, 22), (16, 48), (38, 44)]
ACTION_POOL = actions.RAW_FUNCTIONS
RACE_UNITS = units.Terran

### CLASSES ###
# History record
class HistoryRecord():
    def __init__(self):
        self.scenarios = []
    
    def add_scenario(self, scenario):
        self.scenarios.append(scenario)

    def clear(self):
        self.scenarios = []

    def get_history(self):
        return self.scenarios

# Scenario record
class ScenarioRecord():
    def __init__(self):
        self.inputs = []
        self.actions = []
        self.reward = None

    def add_record(self, inputs, action):
        # record = inputs + [action]
        # print(record)
        self.inputs.append(inputs)
        self.actions.append(action)
    
    def add_reward(self, reward):
        self.reward = reward

    def get_scenario(self):
        return self.inputs, self.actions, self.reward

# Neural Network
class NeuralNetwork():
    def __init__(self, hidden_layers=HIDDEN_LAYERS, epochs=EPOCHS, batch_size=BATCH_SIZE):
        # print("Initializing Neural Network")
        self.is_ready = False
        self.model = Sequential()
        self.hidden_layers = hidden_layers
        self.epochs = epochs
        self.batch_size = batch_size

    def define_model(self):
        print("Defining model")
        self.model.add(layers.BatchNormalization(input_shape=(NUM_INPUTS,), name="batch_norm_0"))
        for i in range(0, len(self.hidden_layers)):
            self.model.add(layers.Dense(self.hidden_layers[i], activation="relu", kernel_initializer="he_uniform", name=f"dense_{i}"))
            self.model.add(layers.BatchNormalization(name=f"batch_norm_{i+1}"))
        self.model.add(layers.Dense(3, activation="softmax", name="output"))
        # self.model.compile(optimizer=Adam(), loss="categorical_crossentropy", metrics=["accuracy"]) # Adaptive learning rate
        self.model.compile(optimizer=SGD(learning_rate=L_RATE, clipvalue=0.5), loss="categorical_crossentropy", metrics=["accuracy"]) # Gradient descent
        # self.model.summary()
        self.is_ready = True

    # Getting one hot encoding of action
    def one_hot(self, action, reward):
        encode = [0, 0, 0]
        encode[action] = reward
        return encode

    def train_model(self, history):
        print("Training model")
        hist = history.get_history()
        x_data = np.array([])
        y_data = np.array([])
        total = 0
        for scenario in hist:
            inputs, actions, reward = scenario.get_scenario()
            reward = 1 * (1 - (inputs[-1][NUM_INPUTS - 2] / 3600)) if reward == 1 else 0
            # reward = 1 if reward == 1 else 0
            total_scenario = len(inputs)
            x_data = np.append(x_data, normalize(inputs))
            y_scenario = []
            [y_scenario.append(self.one_hot(action, reward)) for action in actions]
            y_scenario = np.array(y_scenario).astype("float32")
            y_data = np.append(y_data, y_scenario)
            total += total_scenario
        x_data = np.array(x_data).astype("float32").reshape(total, NUM_INPUTS)
        y_data = np.array(y_data).astype("float32").reshape(total, 3)

        self.model.fit(x_data, y_data, epochs=self.epochs, batch_size=self.batch_size, verbose=0)

    def predict(self, inputs):
        print("Getting prediction")
        inputs = normalize(np.array(inputs).reshape(1, NUM_INPUTS))
        # inputs = np.array(inputs).astype("float32").reshape(1, NUM_INPUTS)
        predict = self.model.predict(inputs, verbose=0).flatten()
        # print(predict)
        max_indices = np.argwhere(predict == predict.max()).flatten().tolist()
        choice = random.choice(max_indices)
        return choice

    def save_model(self):
        print("Saving model")
        dir_name = "./saves/"
        if not exists(dir_name):
            mkdir(dir_name)
        for layer in self.hidden_layers:
            dir_name += str(layer) + "_"
        dir_name = dir_name[:-1] + "/"
        if not exists(dir_name):
            mkdir(dir_name)
        time_rtn = time.localtime()
        self.model.save(dir_name + f"save_{time_rtn.tm_year}_{time_rtn.tm_yday}_{time_rtn.tm_hour}_{time_rtn.tm_min}")
        self.model.save(dir_name + "latest")

    def load_model(self):
        print("Loading model")
        dir_name = "./saves/"
        for layer in self.hidden_layers:
            dir_name += str(layer) + "_"
        dir_name = dir_name[:-1] + "/"
        if exists(dir_name):
            print("Model found")
            self.model = models.load_model(dir_name + "latest")
            self.is_ready = True
        else:
            print("Model not found")

### RUNTIME ###
def run_loop(argv, agents, env, max_frames=0, max_episodes=0):
    """A run loop to have agents and an environment interact."""
    total_frames = 0
    total_episodes = 0
    total_rewards = [0, 0, 0]
    start_time = time.time()
    neural_net = NeuralNetwork()
    if (len(argv) == 2):
        neural_net = NeuralNetwork(argv[1])
    elif (len(argv) == 4):
        neural_net = NeuralNetwork(argv[1], argv[2], argv[3])
    neural_net.load_model()

    observation_spec = env.observation_spec()
    action_spec = env.action_spec()
    for agent, obs_spec, act_spec in zip(agents, observation_spec, action_spec):
        agent.setup(obs_spec, act_spec)

    game_history = HistoryRecord()
    episode_rewards = [0, 0, 0]
    try:
        while not max_episodes or total_episodes < max_episodes:
            total_episodes += 1
            timesteps = env.reset()

            for a in agents:
                a.reset(not neural_net.is_ready)

            relative_quadrant = {}
            quad_keys = []
            selected_area = ""
            scenario_history = ScenarioRecord()
            while True:
                # Standard SC2 loop
                total_frames += 1
                actions = [agent.step(timestep) for agent, timestep in zip(agents, timesteps)]
                # Quality of life variables
                my_agent = agents[0]
                my_obs = timesteps[0]
                minerals = my_obs.observation.player.minerals
                complete_barracks = my_agent.get_my_units_by_type(my_obs, RACE_UNITS.Barracks, True)
                # Setup relative quadrants dictionary
                if my_obs.first():
                    relative_quadrant = {
                        # "home": QUADRANT_COORD[0 if my_agent.base_top_left else 3],
                        "retreat_vertical": QUADRANT_COORD[1 if my_agent.base_top_left else 2],
                        "retreat_horizontal": QUADRANT_COORD[2 if my_agent.base_top_left else 1],
                        "enemy": QUADRANT_COORD[3 if my_agent.base_top_left else 0]
                    }
                    quad_keys = list(relative_quadrant.keys())

                # Take over if agent is setup
                if (my_agent.is_setup):
                    # Setup relative quadrant and select selected area
                    if selected_area == "" or my_agent.steps % STEP_CHANGE_QUAD == 0:
                        if my_agent.is_random:
                            selected_area = random.choice(quad_keys)
                        else:
                            inputs = list(my_agent.export_inputs(my_obs).values())
                            selected_area = quad_keys[neural_net.predict(inputs)]
                    # Attack, train, or do nothing
                    if (my_agent.steps % (STEP_CHANGE_QUAD / ATTACK_INTERVAL) == 0 and
                        len(my_agent.get_my_units_by_type(my_obs, RACE_UNITS.Marine)) >= 15):
                        # print("Change quad")
                        scenario_history.add_record(list(my_agent.export_inputs(my_obs).values()), 
                                                    quad_keys.index(selected_area))
                        actions[0] = my_agent.attack_quadrant(my_obs, relative_quadrant[selected_area])
                    elif (len(complete_barracks) > 0 and minerals >= 100):
                        # print("Train marine")
                        actions[0] = my_agent.train_unit(complete_barracks, RACE_UNITS.Marine)
                    else:
                        # print("No action")
                        actions[0] = ACTION_POOL.no_op()
                # Standard SC2 loop
                if max_frames and total_frames >= max_frames:
                    return
                if my_obs.last():
                    if my_obs.reward == 1:
                        scenario_history.add_record(list(my_agent.export_inputs(my_obs).values()), quad_keys.index(selected_area))
                    break
                
                timesteps = env.step(actions)
            # Get reward and add to history
            scenario_history.add_reward(timesteps[0].reward)
            game_history.add_scenario(scenario_history)
            match(timesteps[0].reward):
                case -1:
                    episode_rewards[0] += 1
                    total_rewards[0] += 1
                case 0:
                    episode_rewards[1] += 1
                    total_rewards[1] += 1
                case 1:
                    episode_rewards[2] += 1
                    total_rewards[2] += 1

            # Train neural network and save model
            if total_episodes % NUM_EPISODES == 0:
                if IS_TRAINING:
                    # Define AI model if not defined
                    if not neural_net.is_ready:
                        if not exists("./game_hists"):
                            mkdir("./game_hists")
                        with open(f"./game_hists/{int(time.time())}", "w") as f:
                            for scenario in game_history.get_history():
                                inputs, actions, reward = scenario.get_scenario()
                                f.writeline(f"{inputs}-{actions}-{reward}")
                        neural_net.define_model()
                    # Train AI model
                    neural_net.train_model(game_history)
                    # Save AI model
                    neural_net.save_model()

                print("EPISODE RESULTS: % - #")
                print(f"Win rate: {episode_rewards[2] / NUM_EPISODES} - {episode_rewards[2]}")
                print(f"Draw rate: {episode_rewards[1] / NUM_EPISODES} - {episode_rewards[1]}")
                print(f"Lose rate: {episode_rewards[0] / NUM_EPISODES} - {episode_rewards[0]}")
                print("TOTAL RESULTS: % - #")
                print(f"Win rate: {total_rewards[2] / total_episodes} - {total_rewards[2]}")
                print(f"Draw rate: {total_rewards[1] / total_episodes} - {total_rewards[1]}")
                print(f"Lose rate: {total_rewards[0] / total_episodes} - {total_rewards[0]}")
                episode_rewards = [0, 0, 0]
                game_history.clear()
    except KeyboardInterrupt:
        pass
    finally:
        elapsed_time = time.time() - start_time
        print("Took %.3f seconds for %s steps: %.3f fps" % (elapsed_time, total_frames, total_frames / elapsed_time))