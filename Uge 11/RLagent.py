from pysc2.env import sc2_env
from pysc2.lib import features
from pysc2.lib import actions
from models import Agent, Critic
import torch
import torch.nn.functional as F
import torch.nn as nn
import torch.optim as optim
from absl import app
from absl import flags
import numpy as np
from visualization import Visual_interface
import time
import os
from types import SimpleNamespace

model_path = os.path.join(os.path.dirname(__file__), "Actor_Model.pt")
value_path = os.path.join(os.path.dirname(__file__), "Critic_Model.pt")

def softmax2d(input_tensor):
    shape = input_tensor.shape

    flattened_input = input_tensor.view(-1, shape[-2] * shape[-1])
    softmaxed = F.softmax(flattened_input, dim=-1)
    output_tensor = softmaxed.view(*shape[:-2], shape[-2], shape[-1])
    return output_tensor

def choose2dAction(logits):
    choice = np.random.choice(32*32, 1, p = torch.nn.functional.softmax(logits.view(-1),dim=0).detach().numpy())
    map_coord = [choice//32,choice%32]
    return (map_coord)

def random_valid_action(timestep):
    available_actions = timestep.observation.available_actions
    action_id = np.random.choice(available_actions)
    func = actions.FUNCTIONS[action_id]

    args = []
    for arg in func.args:
        if arg.name in ("screen", "minimap", "screen2"):
            coord = [np.random.randint(0, 32), np.random.randint(0, 32)]
            args.append(coord)
        else:
            args.append([np.random.randint(0, arg.sizes[0])])

    return actions.FunctionCall(action_id, args)

def extract_observation(observation):
    feature_screen = observation["feature_screen"]
    feature_map = observation["feature_minimap"]
    player = observation["player"]
    feature_screen = np.stack([
        feature_screen["player_relative"],
        feature_screen["selected"],
    ])
    feature_map = np.stack([
        feature_map["player_relative"],
        feature_map["visibility_map"],
    ])
    player = torch.tensor(player).float()
    feature_screen = torch.tensor(feature_screen).float()
    feature_map = torch.tensor(feature_map).float()
    return SimpleNamespace(screen = feature_screen,map = feature_map,player = player)



MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
ATTACK_SCREEN = actions.FUNCTIONS.Attack_screen.id
SELECT_SCREEN = actions.FUNCTIONS.select_point.id
MOVE_CAMERA = actions.FUNCTIONS.move_camera.id
TRAIN_SCV = actions.FUNCTIONS.Train_SCV_quick.id
TRAIN_MARINE = actions.FUNCTIONS.Train_Marine_quick.id
BUILD_SUPPLY = actions.FUNCTIONS.Build_SupplyDepot_screen.id
BUILD_BARRACKS = actions.FUNCTIONS.Build_Barracks_screen.id
NO_OP = actions.FUNCTIONS.no_op.id
available_actions = [MOVE_SCREEN,ATTACK_SCREEN,SELECT_SCREEN,MOVE_CAMERA,NO_OP,TRAIN_SCV]
def map_actions(obs, agent_actions):
    print_action = False
    action_id = available_actions[agent_actions[0]]
    if not action_id in obs['available_actions']:
        if (print_action): print("invalid command")
        return (actions.FunctionCall(NO_OP, []), -1)

    #choice = np.random.choice(32*32, 1, p = torch.nn.functional.softmax(screen_action.view(-1),dim=0).detach().numpy())
    screen_coord = [agent_actions[1].item()//32,agent_actions[1].item()%32]
    #choice = np.random.choice(32*32, 1, p = torch.nn.functional.softmax(map_action.view(-1),dim=0).detach().numpy())

    if action_id == TRAIN_SCV:
        if (print_action): print("train unit")
        return (actions.FunctionCall(TRAIN_SCV, [[0]]), 0)
    if action_id == SELECT_SCREEN:
        if (print_action): print("select")
        return (actions.FunctionCall(SELECT_SCREEN, [[0], screen_coord]), 0)
    elif action_id == MOVE_SCREEN:
        if (print_action): print("move")
        return (actions.FunctionCall(MOVE_SCREEN, [[0], screen_coord]), 0)
    elif action_id == ATTACK_SCREEN:
        if (print_action): print("attack")
        return (actions.FunctionCall(ATTACK_SCREEN, [[0], screen_coord]), 0)
    elif action_id == MOVE_CAMERA:
        if (print_action): print("camera")
        return (actions.FunctionCall(NO_OP, []), 0)
    elif action_id == NO_OP:
        if (print_action): print("noop")
        return (actions.FunctionCall(NO_OP, []), 0)
    else:
        raise Exception
        

def calculate_reward(timestep):

    obs = timestep[0].observation
    ai0_value = (
        obs["score_cumulative"]["total_value_units"] +
        obs["score_cumulative"]["total_value_structures"]
    )
    obs = timestep[1].observation
    ai1_value = (
        obs["score_cumulative"]["total_value_units"] +
        obs["score_cumulative"]["total_value_structures"]
    )
    denom = ai0_value+ai1_value
    reward = (ai0_value/denom, ai1_value/denom)
    return reward

def rollout(model, env, animation, step_mul):
    trajectories = []
    tick = 0
    timestep = env.reset()
    agent_obs = [None]*2
    agent_action = [None]*2
    policy = [None]*2
    action_reward = [None]*2
    while (True): #max length is 10000 ticks
        for i,observation in enumerate(timestep):
            obs = observation.observation
            agent_obs[i] = extract_observation(obs)
            policy[i] = model(agent_obs[i])
            agent_action[i], action_reward[i] = map_actions(obs, (policy[i].action, policy[i].screen_action))

        tick += step_mul
        timestep = env.step([
            actions.FunctionCall(actions.FUNCTIONS.no_op.id, []),
            agent_action[1],
        ], step_mul=step_mul)

        reward = list(calculate_reward(timestep))
        #reward[0] += action_reward[0]*1
        #reward[1] += action_reward[1]*1
        #for i, observation in enumerate(timestep):
        i = 1
        trajectories.append((agent_obs[0], agent_obs[1], policy[i].action, policy[i].screen_action, policy[i].dist, policy[i].screen_dist, reward[i]))

        if (tick%(30) == 0):
            animation.update(
                policy[0].screen_dist.probs.view(32,32).detach().numpy(),
                policy[0].dist.probs.detach().numpy()
            )

        if(timestep[0].last()): 
            print("end game")
            break

        if(tick > 1000):
            print("ran out of time")
            break

    return trajectories


    

def stack_namespaces(batched_namespace):
    assert len(batched_namespace)>0, "must have atleast 1 element in the batch"
    field_names = vars(batched_namespace[0]).keys()
    batched_fields = {
        field: torch.stack([getattr(c, field) for c in batched_namespace])
        for field in field_names
    }
    return(SimpleNamespace(**batched_fields))


def train(env):
    discount_factor = 0.95
    model = Agent()
    value_function = Critic()
    optimizer = optim.Adam(model.parameters(), lr = 1e-2)
    value_optimizer = optim.SGD(value_function.parameters(), lr = 1e-4)
    MSE_loss = nn.MSELoss()
    Value_loss = nn.BCEWithLogitsLoss()
    animation = Visual_interface([32,32])
    step_mul = 3 
    while(True):
        trajectories = rollout(model, env, animation, step_mul)
        obs0, obs1, action, screen_action, action_dist, screen_dist, rewards = zip(*trajectories)
        obs0 = stack_namespaces(obs0)
        obs1 = stack_namespaces(obs1)
        batch_size = len(trajectories)
        action = torch.stack(action)
        screen_action = torch.stack(screen_action)



        #rewards
        #we overwrite the reward to make discounted future reward
        rewards = list(rewards)
        for i in reversed(range(len(rewards)-1)):
            rewards[i] = rewards[i+1]*discount_factor+rewards[i]*(1-discount_factor)
        rewards = torch.tensor(rewards)

        #value_prediction

        log_prob = torch.stack([action_dist[i].log_prob(action[i]) for i in range(batch_size)]).detach()
        screen_log_prob = torch.stack([screen_dist[i].log_prob(screen_action[i]) for i in range(batch_size)]).detach()

        value_prediction_logits = value_function(obs0, obs1)
        prediction = F.sigmoid(value_prediction_logits)

        advantage = rewards - prediction.detach()
        #normalize advantage
        advantage -= advantage.mean()
        advantage /= advantage.std() + 1e-10

        for i in range(10):
            value_prediction_logits = value_function(obs0, obs1)

            model_output = model(obs0)
            model_screen_output = model.forward_screen(obs0, action)

            new_log_prob = model_output.dist.log_prob(action)
            new_screen_log_prob = model_screen_output[1].log_prob(screen_action)
            #new_screen_log_prob = torch.stack([model_screen_output[1].log_prob(screen_action[i]) for i in range(batch_size)])
            ratio = torch.exp(new_log_prob-log_prob)
            ratio = ratio.clamp(min = 1-0.1, max = 1+0.1)
            screen_ratio = torch.exp(new_screen_log_prob-screen_log_prob)
            screen_ratio = screen_ratio.clamp(min = 1-0.1, max = 1+0.1)
            actor_loss = -(ratio*advantage+screen_ratio*advantage).mean()
            #policy_loss = (-log_prob * advantage/2 + -screen_log_prob * advantage/10).mean()


            entropy_loss = -torch.mean(torch.stack([action_dist[i].entropy() for i in range(batch_size)]))
            screen_entropy_loss = -torch.mean(torch.stack([screen_dist[i].entropy() for i in range(batch_size)]))
            policy_entropy_loss = (entropy_loss/np.log(6)+1+screen_entropy_loss/np.log(32*32)+1)

            value_loss = MSE_loss(F.sigmoid(value_prediction_logits).flatten().to(dtype=torch.float32),rewards.flatten().to(dtype=torch.float32)).mean()
            #value_loss = Value_loss(value_prediction_logits.flatten().to(dtype=torch.float32), rewards.flatten().to(dtype=torch.float32))

            #print(f"average ratio: {ratio.mean()}")
            #print(f"actor loss: {actor_loss}")
            #print(f"value loss: {value_loss}")
            #print(f"entropy loss: {policy_entropy_losses}")
            #print(f"")
            #print(action)
            #print(advantage)
            #print(ratio)
            optimizer.zero_grad()
            entropy_loss.backward(retain_graph = True)
            actor_loss.backward()
            """
            for name, param in model.named_parameters():
                if(name == "fc1.bias"):

                    print(param)
                    print(param.grad)
            """
            optimizer.step()

            value_optimizer.zero_grad()
            value_loss.backward()
            value_optimizer.step()

        animation.update_full(value_loss.detach().numpy(), policy_entropy_loss.detach().numpy(), actor_loss.detach().numpy())
        torch.save(model, model_path)
        torch.save(value_function, value_path)

        
def open_game(argv):
    agent_interface_format = features.AgentInterfaceFormat(
        feature_dimensions=features.Dimensions(32, 32),
        use_feature_units=True,
        allow_cheating_layers=True
    )

    with sc2_env.SC2Env(
        map_name="Simple64",  
        players=[sc2_env.Agent(sc2_env.Race.terran), sc2_env.Agent(sc2_env.Race.terran)], 
        step_mul=8, 
        visualize=False,
        agent_interface_format=agent_interface_format
    ) as env:
        train(env)

def main(argv):
    flags.FLAGS.mark_as_parsed()
    open_game(argv)

if __name__ == "__main__":
    app.run(main)

