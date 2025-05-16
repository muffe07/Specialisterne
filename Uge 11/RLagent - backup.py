from pysc2.env import sc2_env
from pysc2.lib import features
from pysc2.lib import actions
from models import Agent
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

model_path = os.path.join(os.path.dirname(__file__), "mymodel")
value_path = os.path.join(os.path.dirname(__file__), "myvalue")

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

def extract_observations(observation):
    feature_screen = observation["feature_screen"]
    feature_map = observation["feature_minimap"]
    player = torch.from_numpy(observation["player"]).float()
    player/=200
    feature_screen = torch.from_numpy(np.stack([
        feature_screen["player_relative"],
        feature_screen["selected"],
    ])).float()
    feature_map = torch.from_numpy(np.stack([
        feature_map["player_relative"],
        feature_map["visibility_map"],
    ])).float()
    return ((feature_screen,feature_map,player))

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
    map_coord = [agent_actions[2].item()//32,agent_actions[2].item()%32]

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
        return (actions.FunctionCall(MOVE_CAMERA, [map_coord]), 0) 
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

def train(env):
    discount_factor = 0.99
    model = Agent()
    value_function = ValueFunction()
    timestep = env.reset()
    #optimizer = optim.Adam(list(model.parameters())+list(value_function.parameters()), lr = 0.001)
    optimizer = optim.Adam(list(model.parameters()), lr = 2e-2)# fix 
    value_optimizer = optim.Adam(value_function.parameters(), lr = 1e-5)
    BCE_logits_loss = nn.BCEWithLogitsLoss()
    Value_loss = nn.MSELoss()
    animation = Visual_interface([32,32])
    step_mul = 3 
    while(True):
        rewards = []
        value_prediction_logits = []
        actions_list = []
        screen_actions_list = []
        screen_dist_list = []
        dist_list = []
        #current_time = time.time()
        #step_time = []
        tick = 0
        while (True): #max length is 10000 ticks
            tick += 1
            time.sleep(1/22)

            obs = timestep[0].observation, timestep[1].observation

            inputs = (extract_observations(obs[0]), extract_observations(obs[1]))
            actor_action, (distribution, screen_dist, map_dist), logits = (model.forward(inputs[0]))

            actions_list.append(actor_action[0])
            screen_actions_list.append(actor_action[1])
            dist_list.append(distribution)
            screen_dist_list.append(screen_dist)
            #value_prediction_logits.append(torch.tensor([0]))
            value_prediction_logits.append(value_function.forward(inputs[0],inputs[1])) 

            #if(action_reward == -1): invalid_actions+=1
            #log_prob = distribution.log_prob(agent_actions[0])
            #screen_log_prob = screen_dist.log_prob(agent_actions[1])


            agent_action, action_reward = map_actions(obs[0], actor_action)
            timestep = env.step([
                actions.FunctionCall(actions.FUNCTIONS.no_op.id, []),
                agent_action, 
                #actions.FunctionCall(actions.FUNCTIONS.no_op.id, []),
            ], step_mul=step_mul)
            timestep = (timestep[1],timestep[0])
            reward = calculate_reward(timestep)
            rewards.append(reward[0])

            if (tick%(30) == 0):
                animation.update(
                    screen_dist.probs.view(32,32).detach().numpy(),
                    distribution.probs.detach().numpy()
                    #F.softmax(logits[1],dim=0).view(32,32).detach().numpy(),
                    #F.softmax(logits[0],dim=0).detach().numpy()
                )

            if(timestep[0].last()): 
                print("end game")
                break

            
            """ fix 
            if(tick > 1000/step_mul):
                print("ran out of time")
                timestep = env.reset()
                break
            """

            #policy_losses.append(-log_prob * action_reward + -screen_log_prob * action_reward)
            #old_time = current_time
            #current_time = time.time()
            #step_time.append(current_time-old_time)


        #make sure all data is available
        batch_size = len(rewards)
        assert len(value_prediction_logits) == batch_size
        assert len(actions_list) == batch_size
        assert len(screen_actions_list) == batch_size
        assert len(dist_list) == batch_size
        assert len(screen_dist_list) == batch_size
        print("\n\ntrain step")

        #batch lists
        #rewards
        #we overwrite the reward to make discounted future reward
        for i in reversed(range(len(rewards)-1)):
            rewards[i] = rewards[i+1]*discount_factor+rewards[i]*(1-discount_factor)
        rewards = torch.tensor(rewards)

        #value_prediction
        value_prediction_logits = torch.cat(value_prediction_logits)
        
        log_prob = torch.stack([dist_list[i].log_prob(actions_list[i]) for i in range(batch_size)])
        mean_dist = torch.mean(torch.stack([dist_list[i].probs for i in range(batch_size)]),dim=0)
        print(log_prob.requires_grad)
        #print(dist_list[0])
        print(actions_list[0].requires_grad)

        screen_log_prob = torch.stack([screen_dist_list[i].log_prob(screen_actions_list[i]) for i in range(batch_size)])
        advantage = rewards - F.sigmoid(value_prediction_logits.detach())

        entropy_loss = -torch.mean(torch.stack([dist_list[i].entropy() for i in range(batch_size)]))
        screen_entropy_loss = -torch.mean(torch.stack([screen_dist_list[i].entropy() for i in range(batch_size)]))
        policy_entropy_losses = (entropy_loss/np.log(6)+1+screen_entropy_loss/np.log(32*32)+1)
        #policy_entropy_losses = entropy_loss/np.log(6)+1

        prediction = F.sigmoid(value_prediction_logits)
        value_loss = Value_loss(prediction.to(dtype=torch.float32), rewards.to(dtype=torch.float32))
        #value_loss = BCE_logits_loss(value_prediction_logits.to(dtype=torch.float32), rewards.to(dtype=torch.float32))
        policy_loss = (-log_prob * advantage/2 + -screen_log_prob * advantage/10).mean()
        #_entropy_loss = -torch.mean(torch.cat(screen_dist.entropy()))
        #print(f"prediction: {F.sigmoid(value_prediction_logits).mean()}")
        #print(f"rewards: {rewards.mean()}")
        #print(np.average(step_time))
        #policy_losses = -log_prob * advantage.mean()
        #print(invalid_actions)
        #screen_loss = distributions
        print(f"average reward: {rewards.mean()}")
        print(f"average expected reward: {prediction.mean()}")
        print(f"policy loss: {policy_loss}")
        print(f"value loss: {value_loss}")
        print(f"entropy loss: {policy_entropy_losses}")
        print(f"")
        optimizer.zero_grad()
        value_optimizer.zero_grad()
        #(policy_entropy_losses/10 + policy_losses).backward()
        (policy_entropy_losses/1000).backward(retain_graph=True )
        policy_loss.backward()
        value_loss.backward()
        #torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.1)
        print(mean_dist)
        print(model.fc1.bias)
        print(model.fc1.bias.grad)
        optimizer.step()
        value_optimizer.step()
        animation.update_full(value_loss.detach().numpy(), policy_entropy_losses.detach().numpy(), policy_loss.detach().numpy())
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

class ValueFunction(nn.Module):
    def __init__(self):
        super(ValueFunction, self).__init__()
        self.fc1 = nn.Linear(32*32*4*2+11*2,100)
        self.fc2 = nn.Linear(100,1)

    def forward(self, features1, features2):
        screen1,map1,player1 = features1
        screen2,map2,player2 = features2
        player1 = np.clip(player1, 0, 1)
        player2 = np.clip(player2, 0, 1)
        x = torch.cat([screen1.view(-1), map1.view(-1), player1, screen2.view(-1), map2.view(-1), player2])
        x = self.fc1(x)
        x = nn.LeakyReLU(0.05)(x)
        x = self.fc2(x)
        return x


"""

class Agent(nn.Module):
    def __init__(self):
        super(Agent, self).__init__()
        self.fc1 = nn.Linear(11,6)
        self.fc_screen = nn.Linear(12,32*32)
        self.fc_map = nn.Linear(12,32*32)
        self.conv1 = nn.Conv2d(in_channels = 2, out_channels = 3, kernel_size = 1, stride = 1, padding = 0)
        self.conv2 = nn.Conv2d(in_channels = 3, out_channels = 1, kernel_size = 1, stride = 1, padding = 0)



    def forward(self, features):
        assert len(features)==3,"feature length"
        screen,map,player = features

        player = np.clip(player, 0, 1)

        action_logits = self.fc1(player)
        dist = torch.distributions.Categorical(logits=action_logits)
        action = dist.sample()

        after_action_data = torch.cat((action.unsqueeze(0),player))

        screen_gate = self.fc_screen(after_action_data)
        screen_x = self.conv1(screen)
        screen_x = nn.LeakyReLU(0.05)(screen_x)
        screen_x = self.conv2(screen_x)
        screen_x = nn.LeakyReLU(0.05)(screen_x)
        screen_logits = screen_gate.view(32, 32)*screen_x.squeeze(0)
        screen_logits = screen_logits.reshape(*screen_logits.shape[:-2], -1)
        screen_dist = torch.distributions.Categorical(logits = screen_logits)
        screen_action = screen_dist.sample()

        map_gate = self.fc_map(after_action_data)
        map_x = self.conv1(map)
        map_x = nn.LeakyReLU(0.05)(map_x)
        map_x = self.conv2(map_x)
        map_x = nn.LeakyReLU(0.05)(map_x)
        map_logits = map_gate.view(32, 32)*map_x.squeeze(0)
        map_logits = map_logits.reshape(*map_logits.shape[:-2], -1)
        map_dist = torch.distributions.Categorical(logits = map_logits)
        map_action = map_dist.sample()
        return((action,screen_action,map_action), (dist, screen_dist, map_dist), (action_logits, screen_logits, map_logits))
"""


def main(argv):
    flags.FLAGS.mark_as_parsed()
    open_game(argv)

if __name__ == "__main__":
    app.run(main)

