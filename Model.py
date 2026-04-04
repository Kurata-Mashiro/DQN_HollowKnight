import os
import numpy as np
import torch
import torch.nn as nn


class QNet(nn.Module):
    def __init__(self, out_dim: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(12, 32, kernel_size=5, stride=2, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.head = nn.Linear(128, out_dim)

    def forward(self, x):
        x = self.features(x)
        x = x.flatten(1)
        return self.head(x)


class Model:
    def __init__(self, input_shape, act_dim, move_dim=2):
        self.act_dim = act_dim
        self.move_dim = move_dim
        self.input_shape = input_shape
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.private_act_model = QNet(self.act_dim).to(self.device)
        self.private_move_model = QNet(self.move_dim).to(self.device)
        self.act_model = self.private_act_model
        self.move_model = self.private_move_model
        self.act_loss = []
        self.move_loss = []

    def _to_tensor(self, station):
        arr = np.asarray(station, dtype=np.float32)
        if arr.ndim == 4:
            # Single sample: (T, H, W, C) -> (1, T*C, H, W).
            # With default settings this is 4 * 3 = 12 channels.
            # We intentionally fold time into channels and use 2D convs for a lighter model.
            arr = np.transpose(arr, (0, 3, 1, 2))
            arr = arr.reshape(1, arr.shape[0] * arr.shape[1], arr.shape[2], arr.shape[3])
        elif arr.ndim == 5:
            # Batch sample: (N, T, H, W, C) -> (N, T*C, H, W), same temporal folding strategy.
            arr = np.transpose(arr, (0, 1, 4, 2, 3))
            arr = arr.reshape(arr.shape[0], arr.shape[1] * arr.shape[2], arr.shape[3], arr.shape[4])
        else:
            raise ValueError(f"Unsupported station shape: {arr.shape}")
        return torch.from_numpy(arr).to(self.device)

    def predict(self, station):
        self.private_move_model.eval()
        self.private_act_model.eval()
        with torch.no_grad():
            x = self._to_tensor(station)
            pred_move = self.private_move_model(x)
            pred_act = self.private_act_model(x)
        return pred_move, pred_act

    def load_model(self):
        os.makedirs("./model", exist_ok=True)
        act_path = "./model/act_part.pt"
        move_path = "./model/move_part.pt"
        if os.path.exists(act_path):
            print("load action model")
            self.private_act_model.load_state_dict(torch.load(act_path, map_location=self.device))
        if os.path.exists(move_path):
            print("load move model")
            self.private_move_model.load_state_dict(torch.load(move_path, map_location=self.device))

    def save_mode(self):
        os.makedirs("./model", exist_ok=True)
        print("save model")
        torch.save(self.private_act_model.state_dict(), "./model/act_part.pt")
        torch.save(self.private_move_model.state_dict(), "./model/move_part.pt")
