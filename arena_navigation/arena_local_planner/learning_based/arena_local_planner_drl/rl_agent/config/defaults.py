from .config import CfgNode as CN
import os
import rospkg

arena_local_planner_drl_root= rospkg.RosPack().get_path('arena_local_planner_drl')


_C = CN()

_C.OUTPUT_DIR_ROOT = os.path.join(arena_local_planner_drl_root,'output')
#Robot's setting
_C.ROBOT = CN()
# setting's file for flatland
_C.ROBOT.FLATLAND_DEF =  os.path.join(
                rospkg.RosPack().get_path('simulator_setup'),
                'robot', 'myrobot.model.yaml')
# here defines robot's actions
_C.ROBOT.ACTIONS_DEF = os.path.join(arena_local_planner_drl_root,'configs','robot_actions.yaml')
_C.ROBOT.IS_ACTION_DISCRETE = True

_C.TASK = CN()
# _C.TASK.NAME = 'RandomTask'
_C.TASK.NAME = 'StagedRandomTask'


_C.ENV = CN()
_C.ENV.NAME='FlatlandEnvC3'
# in case robot gets stuck and can get out
# currently they are handled in env class
_C.ENV.MAX_STEPS_PER_EPISODE = 525


# rl MODELrithm's parameters which will be passed the curresponding MODELrithm's constructor
# 1. a list of possible parameters _C.MODELn be found here
#   https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html?highlight=ppo#stable_baselines3.ppo.PPO
# 2. a good blog show how to set the parameters properly
#   https://zhuanlan.zhihu.com/p/99901400
#


_C.REWARD = CN()       
_C.REWARD.RULE_NAME = "rule_01" 
# if none it will be set automatically 
_C.REWARD.SAFE_DIST = None
_C.REWARD.GOAL_RADIUS = 0.25

_C.INPUT = CN()
# where to normalize the inpute or not
_C.INPUT.NORM = True
_C.INPUT.NORM_SAVE_FILENAME="norm_env.nenv"

_C.NET_ARCH = CN()
_C.NET_ARCH.VF = [64,64]
_C.NET_ARCH.PI = [64,64]
_C.NET_ARCH.FEATURE_EXTRACTOR = CN()
_C.NET_ARCH.FEATURE_EXTRACTOR.NAME = 'CNN_NAVREPC3'
_C.NET_ARCH.FEATURE_EXTRACTOR.FEATURES_DIM = 128

_C.TRAINING = CN()
_C.TRAINING.N_TIMESTEPS = 4e7

# parameters meaning can be found here
# https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html?highlight=EvalCallback#stable_baselines3.common.callbacks.EvalCallback
_C.EVAL = CN()
_C.EVAL.N_EVAL_EPISODES = 40
_C.EVAL.EVAL_FREQ = 25000
# if None, disable the callback
_C.EVAL.STOP_TRAINING_ON_REWARD= True
_C.EVAL.STOP_TRAINING_ON_REWARD_THRESHOLD = 15
# only be active when the task is StagedRandomTask
_C.EVAL.CURRICULUM = CN()
# "rew" means "mean reward", "succ" means "success rate of episode "
_C.EVAL.CURRICULUM.TRESHHOLD_TYPE = "succ"
_C.EVAL.CURRICULUM.SUCC_THRESHOLD_RANGE = [0.6,0.8]
_C.EVAL.CURRICULUM.REW_THRESHOLD_RANGE  = [7,13]
_C.EVAL.CURRICULUM.STAGE_STATIC_OBSTACLE = [0,0,0,0,0,0,0]
_C.EVAL.CURRICULUM.STAGE_DYNAMIC_OBSTACLE = [0,2,4,6,8,10,12]
_C.EVAL.CURRICULUM.INIT_STAGE_IDX = 0

_C.MODEL = CN()
_C.MODEL.NAME= 'PPO'
_C.MODEL.LEARNING_RATE= 0.0003
_C.MODEL.BATCH_SIZE = 64
# stablebaseline requires that
_C.MODEL.N_STEPS = 1024//_C.MODEL.BATCH_SIZE*_C.MODEL.BATCH_SIZE
_C.MODEL.N_EPOCHS = 5
_C.MODEL.GAMMA = 0.99
_C.MODEL.GAE_LAMBDA = 0.95
_C.MODEL.CLIP_RANGE = 0.2
# this string will be treated as a callable object. we use this to schedule the the clip range 
_C.MODEL.CLIP_RANGE = f"res = 1-int(n_step/{_C.TRAINING.N_TIMESTEPS}*10)/10"
_C.MODEL.MAX_GRAD_NORM =  0.5
_C.MODEL.ENT_COEF = 0.02
_C.MODEL.VF_COEF = 0.5





