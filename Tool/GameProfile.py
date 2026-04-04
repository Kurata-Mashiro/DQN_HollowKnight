import os
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class GameProfile:
    name: str
    window_title: str
    station_size: Tuple[int, int, int, int]
    frame_size: Tuple[int, int]
    action_names: Tuple[str, ...]
    move_names: Tuple[str, ...]
    skill_action_indices: Tuple[int, ...]
    restart_mode: str = "generic"

    @property
    def action_dim(self) -> int:
        return len(self.action_names)


PROFILES: Dict[str, GameProfile] = {
    "hollow_knight": GameProfile(
        name="hollow_knight",
        window_title="Hollow Knight",
        station_size=(230, 230, 1670, 930),
        frame_size=(400, 200),
        action_names=(
            "Attack",
            "Attack_Up",
            "Short_Jump",
            "Mid_Jump",
            "Skill_Up",
            "Skill_Down",
            "Rush",
        ),
        move_names=("Move_Left", "Move_Right", "Turn_Left", "Turn_Right"),
        skill_action_indices=(4, 5),
        restart_mode="hollow_knight",
    ),
    "icey": GameProfile(
        name="icey",
        window_title="ICEY",
        station_size=(200, 160, 1720, 940),
        frame_size=(400, 200),
        action_names=(
            "Light_Attack",
            "Heavy_Attack",
            "Short_Jump",
            "Mid_Jump",
            "Dash",
            "Skill_Up",
            "Skill_Down",
        ),
        move_names=("Move_Left", "Move_Right", "Turn_Left", "Turn_Right"),
        skill_action_indices=(5, 6),
        restart_mode="generic",
    ),
}


def get_profile(profile_name: str = None) -> GameProfile:
    if profile_name is None:
        profile_name = os.getenv("RL_GAME_PROFILE", "hollow_knight")
    profile_name = profile_name.lower()
    if profile_name not in PROFILES:
        raise ValueError(f"Unknown RL game profile: {profile_name}")
    return PROFILES[profile_name]


def get_active_profile() -> GameProfile:
    return get_profile()
