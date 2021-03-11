import tracemalloc
import linecache
import argparse
from gym.envs.robotics import task_definitions
from panda_gym.gym_envs.utils import env_field
import os
from robosuite.controllers import load_controller_config
from robosuite.utils.input_utils import *
from rlkit.envs.wrappers import NormalizedBoxEnv

if os.environ['USER'] == 'hietalj4':
    print("Host paniikki")
    os.environ["FRANKA_TEMPLATE_PATH"] = '/m/home/home0/06/hietalj4/unix/robotics/panda-gym/panda_gym/franka_sim/templates'
    os.environ["FRANKA_MESH_PATH"] = '/m/home/home0/06/hietalj4/unix/robotics/panda-gym/panda_gym/franka_sim/meshes'
elif os.environ['USER'] == 'clothmanip':
    os.environ["FRANKA_TEMPLATE_PATH"] = '/home/clothmanip/robotics/panda-gym/panda_gym/franka_sim/templates'
    os.environ["FRANKA_MESH_PATH"] = '/home/clothmanip/robotics/panda-gym/panda_gym/franka_sim/meshes'
else:
    print("Host mac")
    os.environ["FRANKA_TEMPLATE_PATH"] = '/Users/juliushietala/robotics/panda-gym/panda_gym/franka_sim/templates'
    os.environ["FRANKA_MESH_PATH"] = '/Users/juliushietala/robotics/panda-gym/panda_gym/franka_sim/meshes'


def get_robosuite_env(variant):
    options = {}
    options["env_name"] = variant["env_name"]
    options["robots"] = "Panda"
    controller_name = variant['ctrl_kwargs']["ctrl_name"]
    options["controller_configs"] = load_controller_config(
        default_controller=controller_name)

    outp_override = variant["ctrl_kwargs"]["output_max"]
    options["controller_configs"]['output_max'][:3] = [
        outp_override for _ in range(3)]
    options["controller_configs"]['output_min'][:3] = [
        -outp_override for _ in range(3)]

    options["controller_configs"]['input_min'] = - \
        variant["ctrl_kwargs"]["input_max"]
    options["controller_configs"]['input_max'] = variant["ctrl_kwargs"]["input_max"]

    options["controller_configs"]["interpolation"] = variant["ctrl_kwargs"]["interpolator"]
    options["controller_configs"]["ramp_ratio"] = variant["ctrl_kwargs"]["ramp_ratio"]
    options["controller_configs"]["damping_ratio"] = variant["ctrl_kwargs"]["damping_ratio"]
    options["controller_configs"]["kp"] = variant["ctrl_kwargs"]["kp"]

    if variant["ctrl_kwargs"]["position_limits"] == "None":
        pos_limits = None
    else:
        pos_limits = variant["ctrl_kwargs"]["position_limits"]
    options["controller_configs"]["position_limits"] = pos_limits

    options["controller_configs"]["control_delta"] = variant["ctrl_kwargs"]["control_delta"]

    env = suite.make(
        **options,
        **variant['env_kwargs'],
        has_renderer=False,
        has_offscreen_renderer=variant['robosuite_kwargs']['offscreen_renderer'],
        ignore_done=False,
        use_camera_obs=False,
    )
    return NormalizedBoxEnv(env)


def argsparser():
    parser = argparse.ArgumentParser("Parser")
    # Generic
    parser.add_argument('--run',  default=1, type=int)
    parser.add_argument('--title', default="notitle", type=str)
    parser.add_argument('--num_processes', type=int, default=1)
    parser.add_argument('--cprofile', type=int, default=0)

    # Train
    parser.add_argument('--train_steps', default=1000, type=int)
    parser.add_argument('--num_epochs', default=100, type=int)
    parser.add_argument('--save_policy_every_epoch', default=1, type=int)
    parser.add_argument('--num_cycles', default=20, type=int)
    parser.add_argument('--min_expl_steps', type=int, default=0)
    parser.add_argument('--num_eval_rollouts', type=int, default=1)
    parser.add_argument('--num_eval_param_buckets', type=int, default=1)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--debug_same_batch', type=int, default=0)

    # Replay buffer
    # HER 0.8 from paper
    parser.add_argument('--her_percent', default=0.8, type=float)
    parser.add_argument('--buffer_size', default=1E5, type=int)

    # Collection
    parser.add_argument('--max_path_length', default=50, type=int)

    # Env
    parser.add_argument('--env_name', type=str, default="Cloth")
    parser.add_argument('--env_type', type=str, default="robosuite")
    parser.add_argument('--domain_randomization', type=int, default=0)

    # {'kp': 800.0, 'ramp_ratio': 0.2, 'damping_ratio': 0.7, 'score': 0.05137783876823295}]
    # {'kp': 500.0, 'ramp_ratio': 0.1, 'damping_ratio': 1.5, 'score': 0.04553776563369524, 'ATE': 0.0030863284079210413}
    # Controller
    parser.add_argument('--control_delta', type=int, default=1)
    parser.add_argument('--output_max', type=float, default=0.02)
    parser.add_argument('--input_max', type=float, default=1.)
    parser.add_argument('--position_limits',
                        default=[[-0.12, -0.25, 0.12], [0.12, 0.05, 0.4]])
    parser.add_argument('--interpolator', type=str, default="linear")
    parser.add_argument('--ctrl_name', type=str, default="OSC_POSE")
    parser.add_argument('--ramp_ratio', type=float, default=0.1)
    parser.add_argument('--damping_ratio', type=float, default=1.5)
    parser.add_argument('--kp', type=float, default=500.0)

    # NOTE: only applies to some envs

    parser.add_argument('--offscreen_renderer', type=int, default=1)
    parser.add_argument('--constant_goal', type=int, default=0)
    parser.add_argument('--max_action', type=float, default=1.)
    parser.add_argument('--debug_render_success', type=int, default=0)
    parser.add_argument('--control_freq', type=int, default=10)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--task', type=str, default="sideways_franka_1")
    parser.add_argument('--velocity_in_obs', type=int, default=1)
    parser.add_argument('--image_training', default=0, type=int)
    parser.add_argument('--image_size', type=int, default=100)
    parser.add_argument('--randomize_params', type=int, default=0)
    parser.add_argument('--randomize_geoms', type=int, default=0)
    parser.add_argument('--uniform_jnt_tend', type=int, default=1)
    parser.add_argument('--sparse_dense', type=int, default=1)
    parser.add_argument('--goal_noise_range', type=tuple, default=(0, 0.02))
    parser.add_argument('--max_advance', type=float, default=0.05)

    # XML model / env TODO: merge these better with panda-gym
    parser.add_argument('--finger_type', type=str, default="3dprinted")
    parser.add_argument('--model_timestep', type=float, default=0.01)

    args = parser.parse_args()

    file = open("sample.txt", "w")
    file.write(str(args.__dict__))
    return args


def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))


def get_variant(args):
    variant = dict(
        algorithm="SAC",
        layer_size=256,
        trainer_kwargs=dict(
            discount=0.99,
            soft_target_tau=5e-3,
            target_update_period=1,
            policy_lr=3E-4,
            qf_lr=3E-4,
            reward_scale=1,
            use_automatic_entropy_tuning=True,
        ),
        path_collector_kwargs=dict(),
        policy_kwargs=dict(),
        replay_buffer_kwargs=dict(),
        algorithm_kwargs=dict()
    )

    variant['env_name'] = args.env_name
    variant['env_type'] = args.env_type
    variant['domain_randomization'] = bool(args.domain_randomization)
    variant['random_seed'] = args.seed
    variant['version'] = args.title
    variant['image_training'] = bool(args.image_training)
    variant['num_processes'] = int(args.num_processes)

    variant['algorithm_kwargs'] = dict(
        num_epochs=args.num_epochs,
        num_trains_per_train_loop=args.train_steps,
        num_expl_steps_per_train_loop=args.train_steps,
        num_train_loops_per_epoch=int(args.num_cycles),
        max_path_length=int(args.max_path_length),
        num_eval_rollouts_per_epoch=args.num_eval_rollouts,
        num_eval_param_buckets=args.num_eval_param_buckets,
        save_policy_every_epoch=args.save_policy_every_epoch,
        min_num_steps_before_training=args.min_expl_steps,
        batch_size=args.batch_size,
        debug_same_batch=bool(args.debug_same_batch)
    )

    variant['replay_buffer_kwargs'] = dict(
        max_size=int(args.buffer_size),
        fraction_goals_rollout_goals=1 - args.her_percent
    )

    if variant['env_type'] == 'panda_gym_reach':
        variant['env_kwargs'] = dict()
    elif variant['env_type'] == 'panda_gym_franka':
        variant['env_kwargs'] = dict(
            constraints=task_definitions.constraints[args.task],
            sparse_dense=bool(args.sparse_dense),
            pixels=bool(args.image_training),
            goal_noise_range=tuple(args.goal_noise_range),
            randomize_params=bool(args.randomize_params),
            randomize_geoms=bool(args.randomize_geoms),
            uniform_jnt_tend=bool(args.uniform_jnt_tend),
            image_size=args.image_size,
            random_seed=args.seed,
            velocity_in_obs=bool(args.velocity_in_obs)
        )
    elif variant['env_type'] == 'gym':
        n_substeps = int(1/(args.control_freq*args.model_timestep))
        variant['env_kwargs'] = dict(
            n_substeps=n_substeps,
            constraints=task_definitions.constraints[args.task],
            sparse_dense=bool(args.sparse_dense),
            pixels=bool(args.image_training),
            goal_noise_range=tuple(args.goal_noise_range),
            randomize_params=bool(args.randomize_params),
            randomize_geoms=bool(args.randomize_geoms),
            uniform_jnt_tend=bool(args.uniform_jnt_tend),
            image_size=args.image_size,
            random_seed=args.seed,
            velocity_in_obs=bool(args.velocity_in_obs),
            max_advance=float(args.max_advance)
        )
    elif variant['env_type'] == 'robosuite':
        variant['env_kwargs'] = dict(
            constant_goal=bool(args.constant_goal),
            sparse_dense=bool(args.sparse_dense),
            max_action=float(args.max_action),
            constraints=task_definitions.constraints[args.task],
            control_freq=int(args.control_freq),
            pixels=bool(args.image_training),
            goal_noise_range=tuple(args.goal_noise_range),
            randomize_params=bool(args.randomize_params),
            randomize_geoms=bool(args.randomize_geoms),
            uniform_jnt_tend=bool(args.uniform_jnt_tend),
            image_size=args.image_size,
            random_seed=args.seed,
            velocity_in_obs=bool(args.velocity_in_obs)
        )
        variant['robosuite_kwargs'] = dict(
            offscreen_renderer=bool(args.offscreen_renderer))
        variant['ctrl_kwargs'] = dict(ctrl_name=str(args.ctrl_name), output_max=args.output_max, input_max=args.input_max, position_limits=args.position_limits,
                                      interpolator=args.interpolator, ramp_ratio=args.ramp_ratio, damping_ratio=args.damping_ratio, kp=args.kp, control_delta=bool(args.control_delta))
    else:
        raise ValueError("Incorrect env_type provided")

    if args.image_training:
        channels = 1
        variant['policy_kwargs'] = dict(
            input_width=args.image_size,
            input_height=args.image_size,
            input_channels=channels,
            kernel_sizes=[3, 3, 3, 3],
            n_channels=[32, 32, 32, 32],
            strides=[2, 2, 2, 2],
            paddings=[0, 0, 0, 0],
            hidden_sizes=[256, 256, 256, 256],
            init_w=1e-4
        )
        variant['path_collector_kwargs']['additional_keys'] = [
            'robot_observation']
        if not args.env_type == 'panda_gym_reach':
            variant['replay_buffer_kwargs']['internal_keys'] = [
                'image', 'model_params', 'robot_observation']
        else:
            variant['replay_buffer_kwargs']['internal_keys'] = [
                'image', 'robot_observation']

    else:
        if not args.env_type == 'panda_gym_reach':
            variant['path_collector_kwargs']['additional_keys'] = [
                'robot_observation']
            variant['replay_buffer_kwargs']['internal_keys'] = [
                'model_params', 'robot_observation']
        else:
            variant['path_collector_kwargs']['additional_keys'] = []
            variant['replay_buffer_kwargs']['internal_keys'] = []

    return variant
