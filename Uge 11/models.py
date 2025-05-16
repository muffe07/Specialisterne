import torch
import torch.nn.functional as F
import torch.nn as nn
import numpy as np
from types import SimpleNamespace

class Agent(nn.Module):
    def __init__(self):
        super(Agent, self).__init__()
        self.fc1 = nn.Linear(11,6)
        self.fc_screen = nn.Linear(12,32*32)
        self.conv1 = nn.Conv2d(in_channels = 2, out_channels = 3, kernel_size = 1, stride = 1, padding = 0)
        self.conv2 = nn.Conv2d(in_channels = 3, out_channels = 1, kernel_size = 1, stride = 1, padding = 0)


    def forward_screen(self, features, action):
        screen = features.screen
        map = features.map 
        player = features.player
        if(action.dim() == 0):
            action = action.unsqueeze(0)
            player = player.unsqueeze(0)
            map = map.unsqueeze(0)
            screen = screen.unsqueeze(0)

        action = action.unsqueeze(1)
        player = np.clip(player, 0, 1)

        after_action_data = torch.cat((action,player), dim = 1)

        screen_gate = self.fc_screen(after_action_data)
        screen_x = self.conv1(screen)
        screen_x = nn.LeakyReLU(0.05)(screen_x)
        screen_x = self.conv2(screen_x)
        screen_x = nn.LeakyReLU(0.05)(screen_x)
        screen_logits = screen_gate.reshape(-1, 1, 32, 32)*screen_x
        #screen_logits = screen_logits.squeeze(#dim = 1)
        screen_logits = screen_logits.reshape(-1, 32*32)
        #screen_logits = screen_logits.reshape(*screen_logits.shape[:-2], -1)
        screen_dist = torch.distributions.Categorical(logits = screen_logits)
        screen_action = screen_dist.sample()
        return (screen_action,screen_dist)

    def forward(self, features):
        screen = features.screen
        map = features.map 
        player = features.player
        player = np.clip(player, 0, 1)
        action_logits = self.fc1(player)
        dist = torch.distributions.Categorical(logits=action_logits)
        action = dist.sample()


        screen_action, screen_dist = self.forward_screen(features, action)
        """
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
        """

        return(
            SimpleNamespace(
                action = action,
                screen_action = screen_action, 
                dist = dist, 
                screen_dist = screen_dist
            )
        )

def flatten_last_n_rows(x, n):
    return(x.view(*x.shape[:-n], -1))

class Critic(nn.Module):
    def __init__(self):
        super(Critic, self).__init__()
        self.fc1 = nn.Linear(32*32*4*2+11*2,100)
        self.fc2 = nn.Linear(100,1)

    def forward(self, features1, features2):
        screen1 = flatten_last_n_rows(features1.screen, 3)
        screen2 = flatten_last_n_rows(features2.screen, 3)
        map1 = flatten_last_n_rows(features1.map, 3)
        map2 = flatten_last_n_rows(features2.map, 3)
        player1 = np.clip(features1.player, 0, 1)
        player2 = np.clip(features2.player, 0, 1)
        print(screen1.shape)
        print(map1.shape)
        print(player1.shape)
        x = torch.cat([screen1, map1, player1, screen2, map2, player2], dim = 1)
        x = self.fc1(x)
        x = nn.LeakyReLU(0.05)(x)
        x = self.fc2(x)
        return x.squeeze(dim = 1)