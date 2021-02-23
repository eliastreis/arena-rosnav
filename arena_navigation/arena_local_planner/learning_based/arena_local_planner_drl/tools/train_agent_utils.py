import os
import datetime
import json

from stable_baselines3 import PPO

""" 
Dict containing agent specific hyperparameter keys (for documentation and typing validation purposes)

:key agent_name: Precise agent name (as generated by get_agent_name())
:key robot: Robot name to load robot specific .yaml file containing settings
:key batch_size: Batch size (n_envs * n_steps)
:key gamma: Discount factor
:key n_steps: The number of steps to run for each environment per update
:key ent_coef: Entropy coefficient for the loss calculation
:key learning_rate: The learning rate, it can be a function
    of the current progress remaining (from 1 to 0)
    (i.e. batch size is n_steps * n_env where n_env is number of environment copies running in parallel)
:key vf_coef: Value function coefficient for the loss calculation
:key max_grad_norm: The maximum value for the gradient clipping
:key gae_lambda: Factor for trade-off of bias vs variance for Generalized Advantage Estimator
:key m_batch_size: Minibatch size
:key n_epochs: Number of epoch when optimizing the surrogate loss
:key clip_range: Clipping parameter, it can be a function of the current progress
    remaining (from 1 to 0).
:key train_max_steps_per_episode: Max timesteps per training episode
:key eval_max_steps_per_episode: Max timesteps per evaluation episode
:key goal_radius: Radius of the goal
:key reward_fnc: Number of the reward function (defined in ../rl_agent/utils/reward.py)
:key discrete_action_space: If robot uses discrete action space
:key normalize: If observations are normalized before fed to the network
:key task_mode: Mode tasks will be generated in (custom, random, staged).
:key curr_stage: In case of staged training which stage to start with.
:param n_timesteps: The number of timesteps trained on in total.
"""
hyperparams = {
    key: None for key in [
        'agent_name','robot', 'batch_size', 'gamma', 'n_steps', 'ent_coef', 'learning_rate', 'vf_coef', 'max_grad_norm', 'gae_lambda', 'm_batch_size', 
        'n_epochs', 'clip_range', 'reward_fnc', 'discrete_action_space', 'normalize', 'task_mode', 'curr_stage', 'train_max_steps_per_episode', 
        'eval_max_steps_per_episode', 'goal_radius'
    ]
}

def initialize_hyperparameters(PATHS: dict, load_target: str, config_name: str='default', n_envs: int=1):
    """
    Write hyperparameters to json file in case agent is new otherwise load existing hyperparameters

    :param PATHS: dictionary containing model specific paths
    :param load_target: unique agent name (when calling --load)
    :param config_name: name of the hyperparameter file in /configs/hyperparameters
    :param n_envs: number of envs
    """
    # when building new agent
    if load_target is None:
        hyperparams = load_hyperparameters_json(PATHS=PATHS, from_scratch=True, config_name=config_name)
        hyperparams['agent_name'] = PATHS['model'].split('/')[-1]
        hyperparams['n_timesteps'] = 0
    else:
        hyperparams = load_hyperparameters_json(PATHS=PATHS)
    
    # dynamically adapt n_steps according to batch size and n envs
    # then update .json
    check_batch_size(n_envs, hyperparams['batch_size'], hyperparams['m_batch_size'])
    hyperparams['n_steps'] = int(hyperparams['batch_size'] / n_envs)
    write_hyperparameters_json(hyperparams, PATHS)
    return hyperparams


def write_hyperparameters_json(hyperparams: dict, PATHS: dict):
    """
    Write hyperparameters.json to agent directory

    :param hyperparams: dict containing model specific hyperparameters
    :param PATHS: dictionary containing model specific paths
    """
    doc_location = os.path.join(PATHS.get('model'), "hyperparameters.json")

    with open(doc_location, "w", encoding='utf-8') as target:
        json.dump(hyperparams, target, ensure_ascii=False, indent=4)


def load_hyperparameters_json(PATHS: dict, from_scratch: bool=False, config_name: str='default'):
    """
    Load hyperparameters from model directory when loading - when training from scratch
    load from ../configs/hyperparameters

    :param PATHS: dictionary containing model specific paths
    :param from_scatch: if training from scratch
    :param config_name: file name of json file when training from scratch
    """
    if from_scratch:
        doc_location = os.path.join(PATHS.get('hyperparams'), config_name+'.json')
    else:
        doc_location = os.path.join(PATHS.get('model'), "hyperparameters.json")

    if os.path.isfile(doc_location):
        with open(doc_location, "r") as file:
            hyperparams = json.load(file)
        check_hyperparam_format(loaded_hyperparams=hyperparams, PATHS=PATHS)
        return hyperparams
    else:
        if from_scratch:
            raise FileNotFoundError("Found no '%s.json' in %s" % (config_name, PATHS.get('hyperparams')))
        else:
            raise FileNotFoundError("Found no 'hyperparameters.json' in %s" % PATHS.get('model'))


def update_total_timesteps_json(timesteps: int, PATHS:dict):
    """
    Update total number of timesteps in json file

    :param hyperparams_obj(object, agent_hyperparams): object containing containing model specific hyperparameters
    :param PATHS: dictionary containing model specific paths
    """
    doc_location = os.path.join(PATHS.get('model'), "hyperparameters.json")
    hyperparams = load_hyperparameters_json(PATHS=PATHS)
    
    try:
        curr_timesteps = int(hyperparams['n_timesteps']) + timesteps
        hyperparams['n_timesteps'] = curr_timesteps
    except Exception:
        raise Warning("Parameter 'total_timesteps' not found or not of type Integer in 'hyperparameter.json'!")
    else:
        with open(doc_location, "w", encoding='utf-8') as target:
            json.dump(hyperparams, target, ensure_ascii=False, indent=4)
    

def print_hyperparameters(hyperparams: dict):
    print("\n--------------------------------")
    print("         HYPERPARAMETERS         \n")
    for param, param_val in hyperparams.items():
        print("{:30s}{:<10s}".format((param+":"), str(param_val)))
    print("--------------------------------\n\n")


def check_hyperparam_format(loaded_hyperparams: dict, PATHS: dict):
    if not set(hyperparams.keys()) == set(loaded_hyperparams.keys()):
        missing_keys = set(hyperparams.keys()).difference(set(loaded_hyperparams.keys()))
        redundant_keys = set(loaded_hyperparams.keys()).difference(set(hyperparams.keys()))
        raise AssertionError(f"unmatching keys, following keys missing: {missing_keys} \n"
        f"following keys unused: {redundant_keys}")
    if not isinstance(loaded_hyperparams['discrete_action_space'], bool):
        raise TypeError("Parameter 'discrete_action_space' not of type bool")
    if not loaded_hyperparams['task_mode'] in ["custom", "random", "staged"]:
        raise TypeError("Parameter 'task_mode' has unknown value")


def update_hyperparam_model(model: PPO, PATHS: dict, params: dict, n_envs: int = 1):
    """
    Updates parameter of loaded PPO agent

    :param model(object, PPO): loaded PPO agent
    :param PATHS: program relevant paths
    :param params: dictionary containing loaded hyperparams
    :param n_envs: number of parallel environments
    """
    if model.batch_size != params['batch_size']:
        model.batch_size = params['batch_size']
    if model.gamma != params['gamma']:
        model.gamma = params['gamma']
    if model.n_steps != params['n_steps']:
        model.n_steps = params['n_steps']
    if model.ent_coef != params['ent_coef']:
        model.ent_coef = params['ent_coef']
    if model.learning_rate != params['learning_rate']:
        model.learning_rate = params['learning_rate']
    if model.vf_coef != params['vf_coef']:
        model.vf_coef = params['vf_coef']
    if model.max_grad_norm != params['max_grad_norm']:
        model.max_grad_norm = params['max_grad_norm']
    if model.gae_lambda != params['gae_lambda']:
        model.gae_lambda = params['gae_lambda']
    if model.n_epochs != params['n_epochs']:
        model.n_epochs = params['n_epochs']
    """
    if model.clip_range != params['clip_range']:
        model.clip_range = params['clip_range']
    """
    if model.n_envs != n_envs:
        model.update_n_envs()
    if model.rollout_buffer.buffer_size != params['n_steps']:
        model.rollout_buffer.buffer_size = params['n_steps']
    if model.tensorboard_log != PATHS['tb']:
        model.tensorboard_log = PATHS['tb']

def check_batch_size(n_envs: int, batch_size: int, mn_batch_size: int):
    assert (batch_size>mn_batch_size
    ), f"Mini batch size {mn_batch_size} is bigger than batch size {batch_size}"
    
    assert (batch_size%mn_batch_size == 0
    ), f"Batch size {batch_size} isn't divisible by mini batch size {mn_batch_size}"

    assert (batch_size%n_envs == 0
    ), f"Batch size {batch_size} isn't divisible by n_envs {n_envs}"

    assert (batch_size%mn_batch_size==0
    ), f"Batch size {batch_size} isn't divisible by mini batch size {mn_batch_size}"
