### IMPORTS ###
import matplotlib.pyplot as plt
import numpy as np
import random
import tensorflow as tf
import time
from keras import layers, models, Sequential
from keras.optimizers import Adam, SGD
from os import mkdir
from os.path import exists
from pysc2.lib import actions, units
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize

### CONSTANTS ###
IS_TRAINING = True

# Neural Network Constants
NUM_INPUTS = 23
HIDDEN_LAYERS = [32,64,128]
EPOCHS = 500
BATCH_SIZE = 32
L_RATE = 0.001

# Game Constants
NUM_EPISODES = 1
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
        self.model.add(layers.Dense(4, activation="softmax", name="output"))
        # self.model.compile(optimizer=Adam(), loss="categorical_crossentropy", metrics=["accuracy"]) # Adaptive learning rate
        self.model.compile(optimizer=SGD(learning_rate=L_RATE), loss="categorical_crossentropy", metrics=["accuracy"]) # Gradient descent
        self.model.summary()
        self.is_ready = True

    # Getting one hot encoding of action
    def one_hot(self, action, reward):
        encode = [0, 0, 0, 0]
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
            reward = 1 if reward == 1 else 0
            total_scenario = len(inputs)
            x_data = np.append(x_data, normalize(inputs))
            y_scenario = []
            [y_scenario.append(self.one_hot(action, reward)) for action in actions]
            y_scenario = np.array(y_scenario).astype("float32")
            y_data = np.append(y_data, y_scenario)
            total += total_scenario
        x_data = np.array(x_data).astype("float32").reshape(total, NUM_INPUTS)
        y_data = np.array(y_data).astype("float32").reshape(total, 4)

        x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.2)
        x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=0.2)

        history = self.model.fit(x_train, y_train, epochs=self.epochs, batch_size=self.batch_size, validation_data=(x_val, y_val), verbose=1)
        self.model.evaluate(x_test, y_test, verbose=1)

        loss_train = history.history['loss']
        loss_val = history.history['val_loss']
        epochs = range(1,EPOCHS + 1)
        plt.plot(epochs, loss_train, 'g', label='Training loss')
        plt.plot(epochs, loss_val, 'b', label='validation loss')
        plt.title('Training and Validation loss')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()
        plt.show()

        loss_train = history.history['accuracy']
        loss_val = history.history['val_accuracy']
        epochs = range(1,EPOCHS + 1)
        plt.plot(epochs, loss_train, 'g', label='Training accuracy')
        plt.plot(epochs, loss_val, 'b', label='validation accuracy')
        plt.title('Training and Validation accuracy')
        plt.xlabel('Epochs')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.show()

    def predict(self, inputs):
        print("Getting prediction")
        inputs = self.normalize(inputs, 1)
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


QUADRANT_COORD = [(19, 23), (40, 22), (16, 48), (38, 44)]
relative_quadrant = {
    "home": QUADRANT_COORD[0],
    "retreat_vertical": QUADRANT_COORD[1],
    "retreat_horizontal": QUADRANT_COORD[2],
    "enemy": QUADRANT_COORD[3]
}

scenario_hist0 = ScenarioRecord()
scenario_hist1 = ScenarioRecord()
scenario_hist2 = ScenarioRecord()
scenario_hist3 = ScenarioRecord()
game_hist = HistoryRecord()
[scenario_hist0.add_record(test[0:23], test[23]) for test in tests0]
[scenario_hist1.add_record(test[0:23], test[23]) for test in tests1]
[scenario_hist2.add_record(test[0:23], test[23]) for test in tests2]
[scenario_hist3.add_record(test[0:23], test[23]) for test in tests3]
scenario_hist0.add_reward(1)
scenario_hist1.add_reward(0)
scenario_hist2.add_reward(0)
scenario_hist3.add_reward(1)
game_hist.add_scenario(scenario_hist0)
game_hist.add_scenario(scenario_hist1)
game_hist.add_scenario(scenario_hist2)
game_hist.add_scenario(scenario_hist3)

neural_net = NeuralNetwork([32, 64, 128])
neural_net.load_model()
neural_net.define_model()
neural_net.model.summary()
neural_net.train_model(game_hist)