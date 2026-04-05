# -*- coding: utf-8 -*-
import numpy as np
import os
import cv2
import time
import collections
import matplotlib.pyplot as plt

from Model import Model
from DQN import DQN
from Agent import Agent
from ReplayMemory import ReplayMemory


import Tool.Helper
import Tool.Actions
from Tool.Helper import mean, is_end
from Tool.Actions import take_action, restart,take_direction, TackAction, recover_and_enter_boss_if_needed, try_execute_from_text
from Tool.WindowsAPI import grab_screen
from Tool.GetHP import Hp_getter
from Tool.UserInput import User
from Tool.FrameBuffer import FrameBuffer
from Tool.GameProfile import get_active_profile

PROFILE = get_active_profile()
window_size = (0,0,1920,1017)
station_size = PROFILE.station_size

HP_WIDTH = 768
HP_HEIGHT = 407
WIDTH = PROFILE.frame_size[0]
HEIGHT = PROFILE.frame_size[1]
ACTION_DIM = PROFILE.action_dim
MOVE_DIM = PROFILE.move_dim
FRAMEBUFFERSIZE = 4
INPUT_SHAPE = (FRAMEBUFFERSIZE, HEIGHT, WIDTH, 3)

MEMORY_SIZE = 200  # replay memory的大小，越大越占用内存
MEMORY_WARMUP_SIZE = 24  # replay_memory 里需要预存一些经验数据，再从里面sample一个batch的经验让agent去learn
BATCH_SIZE = 10  # 每次给agent learn的数据数量，从replay memory随机里sample一批数据出来
LEARNING_RATE = 0.00001  # 学习率
GAMMA = 0

action_name = list(PROFILE.action_names)
move_name = list(PROFILE.move_names)

DELAY_REWARD = 1
# Safety limit to force episode rollover if no terminal signal is observed from state.
MAX_EPISODE_STEP = PROFILE.max_episode_step




def run_episode(hp, algorithm,agent,act_rmp_correct, move_rmp_correct,PASS_COUNT,paused):
    recover_and_enter_boss_if_needed()
    restart()
    # learn while load game
    for i in range(8):
        if (len(move_rmp_correct) > MEMORY_WARMUP_SIZE):
            # print("move learning")
            batch_station,batch_actions,batch_reward,batch_next_station,batch_done = move_rmp_correct.sample(BATCH_SIZE)
            algorithm.move_learn(batch_station,batch_actions,batch_reward,batch_next_station,batch_done)   

        if (len(act_rmp_correct) > MEMORY_WARMUP_SIZE):
            # print("action learning")
            batch_station,batch_actions,batch_reward,batch_next_station,batch_done = act_rmp_correct.sample(BATCH_SIZE)
            algorithm.act_learn(batch_station,batch_actions,batch_reward,batch_next_station,batch_done)

    
    step = 0
    done = 0
    total_reward = 0

    start_time = time.time()
    # Delay Reward
    DelayMoveReward = collections.deque(maxlen=DELAY_REWARD)
    DelayActReward = collections.deque(maxlen=DELAY_REWARD)
    DelayStation = collections.deque(maxlen=DELAY_REWARD + 1) # 1 more for next_station
    DelayActions = collections.deque(maxlen=DELAY_REWARD)
    DelayDirection = collections.deque(maxlen=DELAY_REWARD)
    
    start_wait_time = time.time()
    if hp.has_realtime_telemetry:
        while True:
            state = hp.get_state()
            boss_hp_value = state["enemy_hp"]
            self_hp = state["self_hp"]
            if boss_hp_value >= 0 and self_hp >= 0:
                break
            if time.time() - start_wait_time > PROFILE.episode_start_timeout_sec:
                break
            time.sleep(0.1)
    else:
        time.sleep(0.2)
        

    thread1 = FrameBuffer(1, "FrameBuffer", WIDTH, HEIGHT, maxlen=FRAMEBUFFERSIZE, station_size=station_size, window_title=PROFILE.window_title)
    thread1.start()

    while True:
        step += 1
        # last_time = time.time()
        # no more than 10 mins
        # if time.time() - start_time > 600:
        #     break

        # in case of do not collect enough frames
        
        while(len(thread1.buffer) < FRAMEBUFFERSIZE):
            time.sleep(0.1)
        
        stations = thread1.get_buffer()
        state = hp.get_state()
        boss_hp_value = state["enemy_hp"]
        self_hp = state["self_hp"]
        player_x, player_y = state["player_x"], state["player_y"]
        enemy_x, enemy_y = state["enemy_x"], state["enemy_y"]
        soul = state["souls"]
        print(f"[Recognized] self_hp={self_hp}, boss_hp={boss_hp_value}, player=({player_x:.2f},{player_y:.2f}), enemy=({enemy_x:.2f},{enemy_y:.2f}), souls={soul}")

        # ICEY runtime currently does not provide an enemy-skill detector.
        move, action = agent.sample(stations, soul, enemy_x, enemy_y, player_x, False)

        
        # action = 0
        take_direction(move)
        take_action(action)
        if try_execute_from_text():
            print("[Recognized] execution prompt detected: pressed L")
        
        # print(time.time() - start_time, " action: ", action_name[action])
        # start_time = time.time()
        
        next_station = thread1.get_buffer()
        next_state = hp.get_state()
        next_boss_hp_value = next_state["enemy_hp"]
        next_self_hp = next_state["self_hp"]
        next_player_x, next_player_y = next_state["player_x"], next_state["player_y"]
        next_enemy_x, next_enemy_y = next_state["enemy_x"], next_state["enemy_y"]

        # get reward
        move_reward = Tool.Helper.move_judge(self_hp, next_self_hp, player_x, next_player_x, enemy_x, next_enemy_x, move, False)
        # print(move_reward)
        act_reward, done = Tool.Helper.action_judge(
            boss_hp_value,
            next_boss_hp_value,
            self_hp,
            next_self_hp,
            next_player_x,
            next_enemy_x,
            next_enemy_y,
            action,
            False,
        )
            # print(reward)
        # print( action_name[action], ", ", move_name[d], ", ", reward)
        
        DelayMoveReward.append(move_reward)
        DelayActReward.append(act_reward)
        DelayStation.append(stations)
        DelayActions.append(action)
        DelayDirection.append(move)

        if len(DelayStation) >= DELAY_REWARD + 1:
            if DelayMoveReward[0] != 0:
                move_rmp_correct.append((DelayStation[0],DelayDirection[0],DelayMoveReward[0],DelayStation[1],done))
            # if DelayMoveReward[0] <= 0:
            #     move_rmp_wrong.append((DelayStation[0],DelayDirection[0],DelayMoveReward[0],DelayStation[1],done))

        if len(DelayStation) >= DELAY_REWARD + 1:
            if mean(DelayActReward) != 0:
                act_rmp_correct.append((DelayStation[0],DelayActions[0],mean(DelayActReward),DelayStation[1],done))
            # if mean(DelayActReward) <= 0:
            #     act_rmp_wrong.append((DelayStation[0],DelayActions[0],mean(DelayActReward),DelayStation[1],done))

        station = next_station
        self_hp = next_self_hp
        boss_hp_value = next_boss_hp_value
            

        # if (len(act_rmp) > MEMORY_WARMUP_SIZE and int(step/ACTION_SEQ) % LEARN_FREQ == 0):
        #     print("action learning")
        #     batch_station,batch_actions,batch_reward,batch_next_station,batch_done = act_rmp.sample(BATCH_SIZE)
        #     algorithm.act_learn(batch_station,batch_actions,batch_reward,batch_next_station,batch_done)

        total_reward += act_reward
        if step >= MAX_EPISODE_STEP:
            done = 1
        paused = Tool.Helper.pause_game(paused)

        if done == 1:
            Tool.Actions.Nothing()
            break
        elif done == 2:
            PASS_COUNT += 1
            Tool.Actions.Nothing()
            time.sleep(3)
            break
        

    thread1.stop()

    for i in range(8):
        if (len(move_rmp_correct) > MEMORY_WARMUP_SIZE):
            # print("move learning")
            batch_station,batch_actions,batch_reward,batch_next_station,batch_done = move_rmp_correct.sample(BATCH_SIZE)
            algorithm.move_learn(batch_station,batch_actions,batch_reward,batch_next_station,batch_done)   

        if (len(act_rmp_correct) > MEMORY_WARMUP_SIZE):
            # print("action learning")
            batch_station,batch_actions,batch_reward,batch_next_station,batch_done = act_rmp_correct.sample(BATCH_SIZE)
            algorithm.act_learn(batch_station,batch_actions,batch_reward,batch_next_station,batch_done)
    # if (len(move_rmp_wrong) > MEMORY_WARMUP_SIZE):
    #     # print("move learning")
    #     batch_station,batch_actions,batch_reward,batch_next_station,batch_done = move_rmp_wrong.sample(1)
    #     algorithm.move_learn(batch_station,batch_actions,batch_reward,batch_next_station,batch_done)   

    # if (len(act_rmp_wrong) > MEMORY_WARMUP_SIZE):
    #     # print("action learning")
    #     batch_station,batch_actions,batch_reward,batch_next_station,batch_done = act_rmp_wrong.sample(1)
    #     algorithm.act_learn(batch_station,batch_actions,batch_reward,batch_next_station,batch_done)

    return total_reward, step, PASS_COUNT, self_hp


if __name__ == '__main__':

    total_remind_hp = 0

    act_rmp_correct = ReplayMemory(MEMORY_SIZE, file_name='./act_memory')         # experience pool
    move_rmp_correct = ReplayMemory(MEMORY_SIZE,file_name='./move_memory')         # experience pool
    
    # new model, if exit save file, load it
    model = Model(INPUT_SHAPE, ACTION_DIM, MOVE_DIM)

    # Hp counter
    hp = Hp_getter()


    model.load_model()
    algorithm = DQN(model, gamma=GAMMA, learnging_rate=LEARNING_RATE)
    agent = Agent(ACTION_DIM,algorithm,e_greed=0.12,e_greed_decrement=1e-6)
    
    # get user input, no need anymore
    # user = User()

    # paused at the begining
    paused = False

    max_episode = 30000
    # 开始训练
    episode = 0
    PASS_COUNT = 0                                       # pass count
    while episode < max_episode:    # 训练max_episode个回合，test部分不计算入episode数量
        # 训练
        episode += 1     
        # if episode % 20 == 1:
        #     algorithm.replace_target()

        total_reward, total_step, PASS_COUNT, remind_hp = run_episode(hp, algorithm,agent,act_rmp_correct, move_rmp_correct, PASS_COUNT, paused)
        if episode % 10 == 1:
            model.save_mode()
        if episode % 5 == 0:
            move_rmp_correct.save(move_rmp_correct.file_name)
        if episode % 5 == 0:
            act_rmp_correct.save(act_rmp_correct.file_name)
        total_remind_hp += remind_hp
        print("Episode: ", episode, ", pass_count: " , PASS_COUNT, ", hp:", total_remind_hp / episode)
