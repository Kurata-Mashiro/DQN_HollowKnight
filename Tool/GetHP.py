import cv2
import numpy as np
from Tool.GameProfile import get_active_profile
from Tool.WindowsAPI import grab_screen

class Hp_getter():
    def __init__(self):
        profile = get_active_profile()
        self.profile = profile
        self.has_realtime_telemetry = True
        self._fallback_state = dict(profile.state_fallback)
        self._last_enemy_hp = int(self._fallback_state["enemy_hp"])

        # Visual HP anchors (screen-space, full window capture based).
        self._player_hp_points = [(130 + i * 22, 50) for i in range(9)]
        self._boss_hp_y = 401
        self._boss_hp_start_x = 100
        self._boss_hp_end_x = 666
        self._boss_hp_max = 570

    def _grab_gray(self):
        frame = grab_screen(self.profile.station_size)
        if frame is None or frame.size == 0:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

    def _detect_player_hp(self, gray):
        hp = 0
        if gray[40][95] != 56 and gray[300][30] > 20 and gray[200][30] > 20 and gray[400][30] > 20:
            return 9
        for idx, (x_, y_) in enumerate(self._player_hp_points):
            pixel = int(gray[y_][x_]) + int(gray[y_ + 1][x_]) + int(gray[y_ - 1][x_]) + int(gray[y_][x_ + 1]) + int(gray[y_][x_ - 1])
            if idx == 0:
                if pixel == 150:
                    break
                if 58 < pixel < 244:
                    hp = idx + 1
            else:
                if pixel == 150:
                    continue
                if (60 < pixel < 115) or (196 <= pixel <= 241) or (144 <= pixel <= 180):
                    hp = idx + 1
        return hp if hp > 0 else 1

    def _detect_enemy_hp(self, gray):
        if ((gray[self._boss_hp_y][98] != 0 and gray[self._boss_hp_y][98] != 62) or
            (gray[self._boss_hp_y][100] == 0 and gray[self._boss_hp_y][400] == 0 and gray[self._boss_hp_y][450] == 0)):
            return self._boss_hp_max
        boss_blood = 0
        for i in range(self._boss_hp_start_x, self._boss_hp_end_x):
            p = gray[self._boss_hp_y][i]
            if (25 < p < 31) or (44 < p < 50):
                boss_blood += 1
            else:
                break
        if boss_blood - self._last_enemy_hp < -500:
            return self._last_enemy_hp
        if abs(boss_blood - self._last_enemy_hp) < 3:
            return self._last_enemy_hp
        return boss_blood

    def _estimate_actor_positions(self, gray):
        # Simple vision estimator by bright-object centroids in lower half.
        h, w = gray.shape
        roi = gray[int(h * 0.35):, :]
        _, mask = cv2.threshold(roi, 180, 255, cv2.THRESH_BINARY)
        nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if nlabels <= 1:
            return self._fallback_state["self_x"], self._fallback_state["self_y"], self._fallback_state["enemy_x"], self._fallback_state["enemy_y"]

        candidates = []
        for i in range(1, nlabels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < 80:
                continue
            cx, cy = centroids[i]
            candidates.append((area, float(cx), float(cy)))

        if len(candidates) < 2:
            return self._fallback_state["self_x"], self._fallback_state["self_y"], self._fallback_state["enemy_x"], self._fallback_state["enemy_y"]

        candidates.sort(key=lambda x: x[0], reverse=True)
        _, x1, y1 = candidates[0]
        _, x2, y2 = candidates[1]
        # Assume player closer to screen center.
        center_x = w / 2.0
        if abs(x1 - center_x) <= abs(x2 - center_x):
            px, py, ex, ey = x1, y1, x2, y2
        else:
            px, py, ex, ey = x2, y2, x1, y1
        return px / 100.0, py / 100.0, ex / 100.0, ey / 100.0
    
    def get_souls(self):
        return self._fallback_state["souls"]

    def get_self_hp(self, gray=None):
        if gray is None:
            gray = self._grab_gray()
        if gray is None:
            return self._fallback_state["self_hp"]
        try:
            return self._detect_player_hp(gray)
        except Exception:
            return self._fallback_state["self_hp"]


    def get_boss_hp(self, gray=None):
        if gray is None:
            gray = self._grab_gray()
        if gray is None:
            return self._fallback_state["enemy_hp"]
        try:
            hp = self._detect_enemy_hp(gray)
            self._last_enemy_hp = hp
            return hp
        except Exception:
            return self._fallback_state["enemy_hp"]

    def get_play_location(self, gray=None):
        if gray is None:
            gray = self._grab_gray()
        if gray is None:
            return self._fallback_state["self_x"], self._fallback_state["self_y"]
        try:
            px, py, _, _ = self._estimate_actor_positions(gray)
            return px, py
        except Exception:
            return self._fallback_state["self_x"], self._fallback_state["self_y"]

    def get_hornet_location(self, gray=None):
        if gray is None:
            gray = self._grab_gray()
        if gray is None:
            return self._fallback_state["enemy_x"], self._fallback_state["enemy_y"]
        try:
            _, _, ex, ey = self._estimate_actor_positions(gray)
            return ex, ey
        except Exception:
            return self._fallback_state["enemy_x"], self._fallback_state["enemy_y"]

    def get_enemy_location(self):
        return self.get_hornet_location()

    def get_state(self):
        gray = self._grab_gray()
        self_hp = self.get_self_hp(gray)
        enemy_hp = self.get_boss_hp(gray)
        player_x, player_y = self.get_play_location(gray)
        enemy_x, enemy_y = self.get_hornet_location(gray)
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
