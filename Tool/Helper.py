from Tool.WindowsAPI import key_check
from Tool.GameProfile import get_active_profile
import time


# check whether a game is end
def is_end(next_self_blood, min_hp, next_boss_blood, boss_blood):
    if next_self_blood ==9 and min_hp <= 3:    
        return True
    elif next_boss_blood - boss_blood > 200:   
        return True
    return False

# get mean score of a reward seq
def mean(d):
    t = 0
    for i in d:
        t += i
    return t / len(d)

# count play hp change, and give reward 
def count_self_reward(next_self_blood, self_hp):
    if next_self_blood - self_hp < 0:
        return 11 * (next_self_blood - self_hp)
    return 0

# count boss hp change, and give reward 
def count_boss_reward(next_boss_blood, boss_blood):
    if next_boss_blood -  boss_blood < 0:
        return int((boss_blood - next_boss_blood)/9)
    return 0

def direction_reward(move, player_x, hornet_x):
    dire = 0
    s = 0
    dis = 0
    base = 5
    if abs(player_x - hornet_x) < 2.5:
        dis = -1
    else:
        dis = 1
    if player_x - hornet_x > 0:
        s = -1
    else:
        s = 1
    if move == 0 or move == 2:
        dire = -1
    else:
        dire = 1

    return dire * s * dis * base


def distance_reward(move, next_player_x, next_hornet_x):
    if abs(next_player_x - next_hornet_x) < 2.5:
        return -6
    elif abs(next_player_x - next_hornet_x) < 4.8:
        return 4
    else:
        if move < 2:
            return 4
        else:
            return -2

def move_judge(self_blood, next_self_blood, player_x, next_player_x, enemy_x, next_enemy_x, move, enemy_skill1):
    hp_reward = count_self_reward(next_self_blood, self_blood)
    distance_now = abs(player_x - enemy_x)
    distance_next = abs(next_player_x - next_enemy_x)
    distance_delta = distance_now - distance_next
    reward = hp_reward + distance_delta * 2
    if move < 2 and distance_next > 8:
        reward += 1
    if move >= 2 and distance_next < 2:
        reward -= 1
    return reward







def act_skill_reward(hornet_skill1, action, next_hornet_x, next_hornet_y, next_player_x):
    skill_reward = 0
    if hornet_skill1:
        if action == 2 or action == 3:
            skill_reward -= 5
    elif  next_hornet_y >34 and abs(next_hornet_x - next_player_x) < 5:
        if action == 4:
            skill_reward += 2
    return skill_reward

def act_distance_reward(action, next_player_x, next_hornet_x, next_hornet_y):
    distance_reward = 0
    if abs(next_player_x - next_hornet_x) < 12:
        if abs(next_player_x - next_hornet_x) > 6:
            if action >= 2 and action <= 3:
                # distance_reward += 0.5
                pass
            elif next_hornet_y < 29 and action == 6:
                distance_reward -= 3
        else:
            if action >= 2 and action <= 3:
                distance_reward -= 0.5
    else:
        if action == 0 and action == 1:
            distance_reward -= 3
        elif action == 6:
            distance_reward += 1
    return distance_reward

# JUDGEMENT FUNCTION, write yourself
def action_judge(boss_blood, next_boss_blood, self_blood, next_self_blood, next_player_x, next_enemy_x,next_enemy_y, action, enemy_skill1):
    profile = get_active_profile()
    self_blood_reward = count_self_reward(next_self_blood, self_blood)
    boss_blood_reward = count_boss_reward(next_boss_blood, boss_blood)
    distance_reward = 0
    if abs(next_player_x - next_enemy_x) < profile.action_reward_close_distance and action in (0, 1):
        distance_reward += profile.action_reward_hit_bonus
    if abs(next_player_x - next_enemy_x) > profile.action_reward_far_distance and action in (0, 1):
        distance_reward += profile.action_reward_whiff_penalty

    time_penalty = profile.action_time_penalty
    reward = self_blood_reward + boss_blood_reward + distance_reward + time_penalty

    if next_self_blood <= 0 and self_blood != profile.max_self_hp:
        return reward - 40, 1
    if next_boss_blood <= 0:
        return reward + 60, 2
    return reward, 0

# Paused training
def pause_game(paused):
    op, d = key_check()
    if 'T' in op:
        if paused:
            paused = False
            print('start game')
            time.sleep(1)
        else:
            paused = True
            print('pause game')
            time.sleep(1)
    if paused:
        print('paused')
        while True:
            op, d = key_check()
            # pauses game and can get annoying.
            if 'T' in op:
                if paused:
                    paused = False
                    print('start game')
                    time.sleep(1)
                    break
                else:
                    paused = True
                    time.sleep(1)
    return paused
