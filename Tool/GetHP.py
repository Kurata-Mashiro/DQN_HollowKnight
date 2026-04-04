import win32gui
from Tool.GameProfile import get_active_profile

class Hp_getter():
    def __init__(self):
        profile = get_active_profile()
        self.profile = profile
        self.has_realtime_telemetry = False
        self._fallback_state = dict(profile.state_fallback)
    
    def get_souls(self):
        return self._fallback_state["souls"]

    def get_self_hp(self):
        return self._fallback_state["self_hp"]


    def get_boss_hp(self):
        return self._fallback_state["enemy_hp"]

    def get_play_location(self):
        return self._fallback_state["self_x"], self._fallback_state["self_y"]

    def get_hornet_location(self):
        return self._fallback_state["enemy_x"], self._fallback_state["enemy_y"]

    def get_enemy_location(self):
        return self.get_hornet_location()

    def get_state(self):
        self_hp = self.get_self_hp()
        enemy_hp = self.get_boss_hp()
        player_x, player_y = self.get_play_location()
        enemy_x, enemy_y = self.get_enemy_location()
        souls = self.get_souls()
        return {
            "self_hp": self_hp,
            "enemy_hp": enemy_hp,
            "player_x": player_x,
            "player_y": player_y,
            "enemy_x": enemy_x,
            "enemy_y": enemy_y,
            "souls": souls,
        }
