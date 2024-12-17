import numpy as np
import random

actions_dict = {
    "stay": 0,
    "attack": 1,
    "retreat": 2
}

states_dict = {
    "home": 0,
    "retreat_vertical": 1,
    "retreat_horizontal": 2,
    "enemy": 3
}

def get_state_from_action(action, curr_state):
    match(action):
        case 0:
            return curr_state
        case 1:
            match(curr_state):
                case 0:
                    return random.choice([1, 2, 3])
                case 1:
                    return random.choice([2, 3])
                case 2:
                    return random.choice([1, 3])
                case 3:
                    return random.choice([1, 2])
        case 2:
            return 0
    return 0

def get_transition_matrix(old_state):
    match (old_state):
        case 0:
            return np.array([[1, 0, 0, 0],
                            [0, 1/3, 1/3, 1/3],
                            [1, 0, 0, 0]])
        case 1:
            return np.array([[0, 1, 0, 0],
                            [0, 0, 0.5, 0.5],
                            [1, 0, 0, 0]])
        case 2:
            return np.array([[0, 0, 1, 0],
                            [0, 0.5, 0, 0.5],
                            [1, 0, 0, 0]])
        case 3:
            return np.array([[0, 0, 0, 1],
                            [0, 0.5, 0.5, 0],
                            [1, 0, 0, 0]])
    return np.array([[0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0]])

def get_reward_matrix(old_state):
    match(old_state):
        case 0:
            return np.array([[-1, 0, 0, 0],
                            [0, 1, 1, 1],
                            [-1, 0, 0, 0]])
        case 1:
            return np.array([[0, 0, 0, 0],
                            [0, 0, 0.5, 1],
                            [-1, 0, 0, 0]])
        case 2:
            return np.array([[0, 0, 0, 0],
                            [0, 0.5, 0, 1],
                            [-1, 0, 0, 0]])
        case 3:
            return np.array([[0, 0, 0, 1],
                            [0, 0.5, 0.5, 0],
                            [-1, 0, 0, 0]])
    return np.array([[0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0]])

def get_next_qvalue(qvalues, new_state):
    return np.max([qvalues[new_state, action] for action in range(3)])

def do_qlearning(qvalues, old_state, action):
    qvalues[old_state, action] = sum([get_transition_matrix(old_state)[action][new_state]
                                 * (get_reward_matrix(old_state)[action][new_state]
                                 + 0.9 * get_next_qvalue(qvalues, new_state)) for new_state in range(4)])
    return qvalues

def compute_value_from_qvals(curr_state):
    max_value = -999
    for action in range(3):
        val = qvalues[curr_state, action]
        if val > max_value:
            max_value = val
    return max_value

def compute_action_from_qvals(curr_state):
    max_value = -999
    curr_actions = [random.choice([action for action in range(3)])]
    for action in range(3):
        val = qvalues[curr_state, action]
        if val == max_value:
            curr_actions.append(action)
        elif val > max_value:
            max_value = val
            curr_actions = [action]
    action = random.choice(curr_actions)

# Create Q-learning
qvalues = np.zeros((4, 3))
alpha = 0.1
discount = 0.9
curr_state = states_dict["home"]
for i in range(1000):
    for action in range(3):
        for new_state in range(4):
            curr_bias = (1 - alpha) * qvalues[curr_state][action]
            lrng_bias = alpha * (get_reward_matrix(curr_state)[action][new_state] + (discount * compute_value_from_qvals(new_state)))
            qvalues[curr_state][action] = curr_bias + lrng_bias
            curr_state = get_state_from_action(action, curr_state)
    for state in qvalues:
        print([val for val in state])
    print()