# ICEY Training

## Environment

- Windows 10
- Python 3.8+
- Dependencies in `requirements.txt`
- ICEY game window must be visible in foreground

## Start Training Directly

1. Open ICEY and enter a repeatable combat scene.
2. Keep window title as `ICEY` (or set env `RL_GAME_WINDOW_TITLE`).
3. Run:
   - `python train.py`

Training now starts directly (no initial manual pause toggle required).

## Current Runtime Notes

- This repository is now ICEY-only runtime.
- `Tool/GetHP.py` currently uses fallback state values (no Hollow Knight memory offset logic).
- Episode has a max step cap to avoid hanging.
- Action/move space is defined in `Tool/GameProfile.py` (ICEY profile).

## Main Files

- `train.py`: training loop
- `Agent.py`: action sampling policy
- `Tool/Actions.py`: key mapping and restart behavior
- `Tool/GetHP.py`: state provider
- `Tool/Helper.py`: reward function
