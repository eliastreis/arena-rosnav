import os
import rospy
import rospkg
import json
import numpy as np
import time

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv, VecNormalize
from stable_baselines3.common.evaluation import evaluate_policy

from task_generator.task_generator.tasks import get_predefined_task
from arena_navigation.arena_local_planner.learning_based.arena_local_planner_drl.rl_agent.envs.flatland_gym_env import FlatlandEnv
from arena_navigation.arena_local_planner.learning_based.arena_local_planner_drl.tools.argsparser import parse_run_agent_args
from arena_navigation.arena_local_planner.learning_based.arena_local_planner_drl.tools.train_agent_utils import *

### HYPERPARAMETERS ###
max_steps_per_episode = 100000000

if __name__ == "__main__":
    args, _ = parse_run_agent_args()

    # get paths
    dir = rospkg.RosPack().get_path('arena_local_planner_drl')
    PATHS={
        'model': os.path.join(dir, 'agents', args.load),
        'robot_setting' : os.path.join(rospkg.RosPack().get_path('simulator_setup'), 'robot', 'myrobot.model.yaml'),
        'robot_as' : os.path.join(rospkg.RosPack().get_path('arena_local_planner_drl'), 'configs', 'default_settings.yaml'),
        'scenerios_json_path' : os.path.join(rospkg.RosPack().get_path('simulator_setup'), 'scenerios', args.scenario+'.json'),
        'curriculum': os.path.join(dir, 'configs', 'training_curriculum_map1small.yaml')
    }

    assert os.path.isfile(
        os.path.join(PATHS['model'], 'best_model.zip')), "No model file found in %s" % PATHS['model']
    assert os.path.isfile(
        PATHS['scenerios_json_path']), "No scenario file named %s" % PATHS['scenerios_json_path']

    # initialize hyperparams
    params = load_hyperparameters_json(PATHS)

    print("START RUNNING AGENT:    %s" % params['agent_name'])
    print_hyperparameters(params)

    # initialize task manager
    task_manager = get_predefined_task(ns='sim_1', mode='staged', start_stage=4, PATHS=PATHS)
    
    # initialize gym env
    env = DummyVecEnv(
        [lambda: FlatlandEnv(
            'sim_1', task_manager, PATHS.get('robot_setting'), PATHS.get('robot_as'), params['reward_fnc'], params['discrete_action_space'], 
            goal_radius=0.50, max_steps_per_episode=max_steps_per_episode, train_mode=False)
        ])
    if params['normalize']:
        env = VecNormalize(
            env, training=False, norm_obs=True, norm_reward=False, clip_reward=15)

    # load agent
    agent = PPO.load(os.path.join(PATHS['model'], "best_model.zip"), env)
    
    # evaluate_policy(
    #     model=agent,
    #     env=env,
    #     n_eval_episodes=1000,
    #     deterministic=True,
    # )

    env.reset()
    first_obs = True

    # iterate through each scenario max_repeat times
    while True:
        if first_obs:
            # send action 'stand still' in order to get first obs
            if params['discrete_action_space']:
                obs, rewards, dones, info = env.step([6])
            else:
                obs, rewards, dones, info = env.step([[0.0, 0.0]])
            first_obs = False
            cum_reward = 0.0

        # timer = time.time()
        action, _ = agent.predict(obs, deterministic=True)
        # print(f"Action predict time: {(time.time()-timer)*2.5} (sim time)")

        # clip action
        if not params['discrete_action_space']:
            action = np.maximum(
                np.minimum(agent.action_space.high, action), agent.action_space.low)
        
        # apply action
        obs, rewards, done, info = env.step(action)

        cum_reward += rewards
        
        if done:
            if args.verbose == '1':
                if info[0]['done_reason'] == 0:
                    done_reason = "exceeded max steps"
                elif info[0]['done_reason'] == 1:
                    done_reason = "collision"
                else:
                    done_reason = "goal reached"
                
                print("Episode finished with reward of %f (finish reason: %s)"% (cum_reward, done_reason))
            env.reset()
            first_obs = True

        time.sleep(0.001)
        if rospy.is_shutdown():
            print('shutdown')
            break
