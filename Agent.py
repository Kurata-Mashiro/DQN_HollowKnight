# -*- coding: utf-8 -*-
import numpy as np
from Tool.GameProfile import get_active_profile

class Agent:
    def __init__(self,act_dim,algorithm,e_greed=0.1,e_greed_decrement=0):
        self.act_dim = act_dim
        self.algorithm = algorithm
        self.e_greed = e_greed
        self.e_greed_decrement = e_greed_decrement


    def sample(self, station, soul, enemy_x, enemy_y, player_x, enemy_skill1):
        profile = get_active_profile()
        
        pred_move, pred_act = self.algorithm.model.predict(station)
        # print(pred_move)
        # print(self.e_greed)
        pred_move = pred_move.detach().cpu().numpy()
        pred_act = pred_act.detach().cpu().numpy()
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
                        pred_act[0][skill_idx] = profile.skill_block_penalty
            act = np.argmax(pred_act)

        self.e_greed = max(
            0.03, self.e_greed - self.e_greed_decrement)  
        return move, act
    
    def better_move(self, enemy_x, player_x, enemy_skill1, profile):
        dis = abs(player_x - enemy_x)
        dire = player_x - enemy_x

        if dis > 6:
            return 0 if dire > 0 else 1
        if dis < 2.5:
            return 1 if dire > 0 else 0
        return np.random.randint(profile.move_dim)

    def better_action(self, soul, enemy_x, enemy_y, player_x, enemy_skill1, profile):
        dis = abs(player_x - enemy_x)
        mid_range_action_indices = [
            idx for idx in profile.mid_range_action_indices if 0 <= idx < self.act_dim
        ]

        if dis < 2.5:
            return 0
        if dis < 6:
            # Prefer profile-defined mid-range subset for distance < 6.
            if mid_range_action_indices:
                return int(np.random.choice(mid_range_action_indices))
            return int(np.random.randint(self.act_dim))
        if 0 <= profile.far_range_action_index < self.act_dim:
            return int(profile.far_range_action_index)
        return max(0, self.act_dim - 1)
                
