# ICEY Training

## Environment

- Windows 10
- Python 3.8+
- Dependencies in `requirements.txt`
- PyTorch runtime (`torch`)
- ICEY game window must be visible in foreground

## Start Training Directly

1. Open ICEY and enter a repeatable combat scene.
2. Keep window title as `ICEY` (or set env `RL_GAME_WINDOW_TITLE`).
   - Example:
     - PowerShell: `$env:RL_GAME_WINDOW_TITLE="ICEY"`
     - CMD: `set RL_GAME_WINDOW_TITLE=ICEY`
3. Run:
   - `python train.py`

Training now starts directly (no initial manual pause toggle required).

## ICEY Action Mapping (current)

- Move left: `A`
- Move right: `D`
- Jump: `Space`
- Dash: `O`
- Light attack: `J`
- Heavy attack: `I`

Other actions are removed from the runtime action space.

## Current Runtime Notes

- This repository is now ICEY-only runtime.
- `Tool/GetHP.py` now uses a vision-based telemetry path first (HP/position estimated from screen), with per-field fallback values when detection is unavailable.
- Episode has a max step cap to avoid hanging.
- Action/move space is defined in `Tool/GameProfile.py` (ICEY profile).

## Main Files

- `train.py`: training loop
- `Agent.py`: action sampling policy
- `Tool/Actions.py`: key mapping and restart behavior
- `Tool/GetHP.py`: state provider
- `Tool/Helper.py`: reward function
