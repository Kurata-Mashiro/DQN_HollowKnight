# Define the actions we may need during training
# You can define your actions here

from Tool.SendKey import PressKey, ReleaseKey
from Tool.WindowsAPI import grab_screen
import time
import cv2
import threading
from Tool.GameProfile import get_active_profile

# Hash code for key we may use: https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN
A = 0x41
D = 0x44
I = 0x49
J = 0x4A
O = 0x4F
SPACE = 0x20
ENTER = 0x0D

# Timings for ICEY first-boss retry flow.
ICEY_RETRY_DIALOG_SETTLE_SEC = 0.2
ICEY_ENTER_HOLD_SEC = 0.08
ICEY_POST_ENTER_WAIT_SEC = 1.0
ICEY_SCENE_TRAVEL_RIGHT_SEC = 5.0
ICEY_SCENE_SETTLE_SEC = 0.2
ICEY_POST_ROUTE_WAIT_SEC = 0.3

# move actions
# 0
def Nothing():
    ReleaseKey(A)
    ReleaseKey(D)
    pass

# Move
# 0
def Move_Left():
    PressKey(A)
    time.sleep(0.01)
# 1
def Move_Right():
    PressKey(D)
    time.sleep(0.01)

def Jump():
    PressKey(SPACE)
    time.sleep(0.08)
    ReleaseKey(SPACE)
    time.sleep(0.01)

def Dash():
    PressKey(O)
    time.sleep(0.08)
    ReleaseKey(O)
    time.sleep(0.01)

def Light_Attack():
    PressKey(J)
    time.sleep(0.12)
    ReleaseKey(J)
    time.sleep(0.01)

def Heavy_Attack():
    PressKey(I)
    time.sleep(0.16)
    ReleaseKey(I)
    time.sleep(0.01)

def restart():
    profile = get_active_profile()
    Nothing()
    if profile.restart_mode == "icey_first_boss_route":
        time.sleep(ICEY_RETRY_DIALOG_SETTLE_SEC)
        PressKey(ENTER)
        time.sleep(ICEY_ENTER_HOLD_SEC)
        ReleaseKey(ENTER)
        time.sleep(ICEY_POST_ENTER_WAIT_SEC)
        PressKey(D)
        time.sleep(ICEY_SCENE_TRAVEL_RIGHT_SEC)
        ReleaseKey(D)
        time.sleep(ICEY_SCENE_SETTLE_SEC)
        PressKey(D)
        time.sleep(ICEY_SCENE_TRAVEL_RIGHT_SEC)
        ReleaseKey(D)
        time.sleep(ICEY_POST_ROUTE_WAIT_SEC)
    else:
        # ICEY restart behavior: neutralize input and give a short settle delay before next episode.
        time.sleep(0.5)


ACTION_FUNC_MAP = {
    "Jump": Jump,
    "Dash": Dash,
    "Light_Attack": Light_Attack,
    "Heavy_Attack": Heavy_Attack,
}


def _resolve_actions():
    profile = get_active_profile()
    resolved = []
    for action_name in profile.action_names:
        action_func = ACTION_FUNC_MAP.get(action_name)
        if action_func is None:
            raise ValueError(f"Unsupported action configured in profile: {action_name}")
        resolved.append(action_func)
    return resolved


# List for action functions
Actions = _resolve_actions()
Directions = [Move_Left, Move_Right]
# Run the action
def take_action(action):
    Actions[action]()

def take_direction(direc):
    Directions[direc]()



class TackAction(threading.Thread):
    def __init__(self, threadID, name, direction, action):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.direction = direction
        self.action = action
        
    def run(self):
        take_direction(self.direction)
        take_action(self.action)
