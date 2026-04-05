import cv2
import numpy as np
from Tool.GameProfile import get_active_profile
from Tool.WindowsAPI import grab_screen

class Hp_getter():
    def __init__(self):
        profile = get_active_profile()
        self.profile = profile
        # Used by training loop to indicate state comes from screen telemetry.
        self.has_realtime_telemetry = True
        self._fallback_state = dict(profile.state_fallback)
        self._last_enemy_hp = int(self._fallback_state["enemy_hp"])

        # Visual HP anchors (screen-space, full window capture based).
        self._player_hp_points = [(130 + i * 22, 50) for i in range(9)]
        self._boss_hp_y = 401
        self._boss_hp_start_x = 100
        self._boss_hp_end_x = 666
        self._boss_hp_max = 570
        self._player_blue_min = 60
        self._player_blue_delta = 20
        self._boss_red_min = 45
        self._boss_red_delta = 12
        self._boss_hp_sudden_drop_limit = -500
        self._boss_hp_stability_tolerance = 3
        self._actor_min_area = 80

        # Legacy grayscale fallback sentinels around top-left UI.
        self._legacy_player_hp_guard_value = 56
        self._legacy_player_hp_guard_min = 20
        self._legacy_player_hp_guard_points = ((40, 95), (300, 30), (200, 30), (400, 30))

    def _grab_frame(self):
        frame = grab_screen(self.profile.station_size)
        if frame is None or frame.size == 0:
            return None
        if len(frame.shape) == 3 and frame.shape[2] == 4:
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

    def _grab_gray(self, frame=None):
        if frame is None:
            frame = self._grab_frame()
        if frame is None or frame.size == 0:
            return None
        if len(frame.shape) == 2:
            return frame
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def _is_blue_pixel(self, pixel):
        b, g, r = int(pixel[0]), int(pixel[1]), int(pixel[2])
        return b >= self._player_blue_min and b > g + self._player_blue_delta and b > r + self._player_blue_delta

    def _is_red_pixel(self, pixel):
        b, g, r = int(pixel[0]), int(pixel[1]), int(pixel[2])
        return r >= self._boss_red_min and r > g + self._boss_red_delta and r > b + self._boss_red_delta

    def _stabilize_enemy_hp(self, boss_blood):
        if self._last_enemy_hp <= 0:
            return boss_blood
        if (boss_blood - self._last_enemy_hp) < self._boss_hp_sudden_drop_limit:
            return self._last_enemy_hp
        if abs(boss_blood - self._last_enemy_hp) < self._boss_hp_stability_tolerance:
            return self._last_enemy_hp
        return boss_blood

    def _detect_player_hp_color(self, frame):
        hp = 0
        h, w = frame.shape[:2]
        for idx, (x_, y_) in enumerate(self._player_hp_points):
            if y_ - 1 < 0 or y_ + 1 >= h or x_ - 1 < 0 or x_ + 1 >= w:
                continue
            blue_votes = 0
            for nx, ny in ((x_, y_), (x_ + 1, y_), (x_ - 1, y_), (x_, y_ + 1), (x_, y_ - 1)):
                if self._is_blue_pixel(frame[ny][nx]):
                    blue_votes += 1
            if blue_votes >= 3:
                hp = idx + 1
        return hp if hp > 0 else None

    def _detect_player_hp_gray(self, gray):
        hp = 0
        p0_y, p0_x = self._legacy_player_hp_guard_points[0]
        p1_y, p1_x = self._legacy_player_hp_guard_points[1]
        p2_y, p2_x = self._legacy_player_hp_guard_points[2]
        p3_y, p3_x = self._legacy_player_hp_guard_points[3]
        if (gray[p0_y][p0_x] != self._legacy_player_hp_guard_value and
            gray[p1_y][p1_x] > self._legacy_player_hp_guard_min and
            gray[p2_y][p2_x] > self._legacy_player_hp_guard_min and
            gray[p3_y][p3_x] > self._legacy_player_hp_guard_min):
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

    def _detect_enemy_hp_color(self, frame):
        h, w = frame.shape[:2]
        if self._boss_hp_y < 0 or self._boss_hp_y >= h:
            return None
        start_x = max(0, self._boss_hp_start_x)
        end_x = min(w, self._boss_hp_end_x)
        boss_blood = 0
        in_bar = False
        for i in range(start_x, end_x):
            if self._is_red_pixel(frame[self._boss_hp_y][i]):
                in_bar = True
                boss_blood += 1
            elif in_bar:
                break
        if boss_blood <= 0:
            return None
        return self._stabilize_enemy_hp(boss_blood)

    def _detect_enemy_hp_gray(self, gray):
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
        return self._stabilize_enemy_hp(boss_blood)

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
            if area < self._actor_min_area:
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

    def get_self_hp(self, gray=None, frame=None):
        if frame is None and gray is None:
            frame = self._grab_frame()
            gray = self._grab_gray(frame)
        elif frame is not None and gray is None:
            gray = self._grab_gray(frame)
        if gray is None:
            return self._fallback_state["self_hp"]
        try:
            if frame is not None:
                hp = self._detect_player_hp_color(frame)
                if hp is not None:
                    return hp
            return self._detect_player_hp_gray(gray)
        except Exception:
            return self._fallback_state["self_hp"]


    def get_boss_hp(self, gray=None, frame=None):
        if frame is None and gray is None:
            frame = self._grab_frame()
            gray = self._grab_gray(frame)
        elif frame is not None and gray is None:
            gray = self._grab_gray(frame)
        if gray is None:
            return self._fallback_state["enemy_hp"]
        try:
            hp = None
            if frame is not None:
                hp = self._detect_enemy_hp_color(frame)
            if hp is None:
                hp = self._detect_enemy_hp_gray(gray)
            self._last_enemy_hp = hp
            return hp
        except Exception:
            return self._fallback_state["enemy_hp"]

    def get_play_location(self, gray=None, frame=None):
        if gray is None:
            gray = self._grab_gray(frame)
        if gray is None:
            return self._fallback_state["self_x"], self._fallback_state["self_y"]
        try:
            px, py, _, _ = self._estimate_actor_positions(gray)
            return px, py
        except Exception:
            return self._fallback_state["self_x"], self._fallback_state["self_y"]

    def get_hornet_location(self, gray=None, frame=None):
        if gray is None:
            gray = self._grab_gray(frame)
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
        frame = self._grab_frame()
        gray = self._grab_gray(frame)
        self_hp = self.get_self_hp(gray=gray, frame=frame)
        enemy_hp = self.get_boss_hp(gray=gray, frame=frame)
        player_x, player_y = self.get_play_location(gray=gray, frame=frame)
        enemy_x, enemy_y = self.get_hornet_location(gray=gray, frame=frame)
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
