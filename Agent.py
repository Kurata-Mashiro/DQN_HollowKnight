# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf
from Tool.GameProfile import get_active_profile

class Agent:
    def __init__(self,act_dim,algorithm,e_greed=0.1,e_greed_decrement=0):
        self.act_dim = act_dim
        self.algorithm = algorithm
        self.e_greed = e_greed
        self.e_greed_decrement = e_greed_decrement
        self.skill_block_penalty = -30


    def sample(self, station, soul, enemy_x, enemy_y, player_x, enemy_skill1):
        profile = get_active_profile()
        
        pred_move, pred_act = self.algorithm.model.predict(station)
        # print(pred_move)
        # print(self.e_greed)
        pred_move = pred_move.numpy()
        pred_act = pred_act.numpy()
        sample = np.random.rand()  
        if sample < self.e_greed:
            move = self.better_move(enemy_x, player_x, enemy_skill1, profile)
        else:
            move = np.argmax(pred_move)
        self.e_greed = max(
            0.03, self.e_greed - self.e_greed_decrement)  

        sample = np.random.rand() 
        if sample < self.e_greed:
            act = self.better_action(soul, enemy_x, enemy_y, player_x, enemy_skill1, profile)
        else:
            act = np.argmax(pred_act)
            if soul < 33:
                for skill_idx in profile.skill_action_indices:
                    if skill_idx < pred_act.shape[1]:
                        pred_act[0][skill_idx] = self.skill_block_penalty
            act = np.argmax(pred_act)

        self.e_greed = max(
            0.03, self.e_greed - self.e_greed_decrement)  
        return move, act
    
    def better_move(self, enemy_x, player_x, enemy_skill1, profile):
        dis = abs(player_x - enemy_x)
        dire = player_x - enemy_x
        if profile.name == "hollow_knight":
            if enemy_skill1:
                if dis < 6:
                    return 1 if dire > 0 else 0
                return 2 if dire > 0 else 3
            if dis < 2.5:
                return 1 if dire > 0 else 0
            if dis < 5:
                return 2 if dire > 0 else 3
            return 0 if dire > 0 else 1

        if dis > 6:
            return 0 if dire > 0 else 1
        if dis < 2.5:
            return 1 if dire > 0 else 0
        return 2 if dire > 0 else 3

    def better_action(self, soul, enemy_x, enemy_y, player_x, enemy_skill1, profile):
        dis = abs(player_x - enemy_x)
        if profile.name == "hollow_knight":
            if enemy_skill1:
                if dis < 3:
                    return 6
                else:
                    return 1
            
            if enemy_y > 34 and dis < 5 and soul >= 33:
                return 4
            
            if dis < 1.5:
                return 6
            elif dis < 5:
                if enemy_y > 32:
                    return 6
                else:
                    act = np.random.randint(self.act_dim)
                    if soul < 33:
                        while act == 4 or act == 5:
                            act = np.random.randint(self.act_dim)
                    return act
            elif dis < 12:
                act = np.random.randint(2)
                return 2 + act
            else:
                return 6

        if dis < 2.5:
            return 0
        if dis < 6:
            act = np.random.randint(min(3, self.act_dim))
            return act
        if self.act_dim > 4:
            return 4
        return max(0, self.act_dim - 1)
                
