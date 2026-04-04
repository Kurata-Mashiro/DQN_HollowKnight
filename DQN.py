import torch
import torch.nn.functional as F


class DQN:
    def __init__(self, model, gamma=0.9, learnging_rate=0.0001):
        self.model = model
        self.act_dim = model.act_dim
        self.move_dim = model.move_dim
        self.act_model = model.act_model
        self.move_model = model.move_model
        self.gamma = gamma
        self.lr = learnging_rate
        self.act_optimizer = torch.optim.Adam(self.act_model.parameters(), lr=self.lr)
        self.move_optimizer = torch.optim.Adam(self.move_model.parameters(), lr=self.lr)
        self.act_global_step = 0
        self.move_global_step = 0

    def _to_tensor(self, obs):
        return self.model._to_tensor(obs)

    def act_train_step(self, action, features, labels):
        self.act_model.train()
        x = self._to_tensor(features)
        action = torch.as_tensor(action, dtype=torch.long, device=self.model.device)
        labels = torch.as_tensor(labels, dtype=torch.float32, device=self.model.device)
        predictions = self.act_model(x)
        pred_action_value = predictions.gather(1, action.view(-1, 1)).squeeze(1)
        loss = F.mse_loss(pred_action_value, labels)
        self.act_optimizer.zero_grad()
        loss.backward()
        self.act_optimizer.step()
        self.model.act_loss.append(float(loss.detach().cpu().item()))

    def act_train_model(self, action, features, labels, epochs=1):
        for _ in range(epochs):
            self.act_train_step(action, features, labels)

    def act_learn(self, obs, action, reward, next_obs, terminal):
        self.act_train_model(action, obs, reward, epochs=1)
        self.act_global_step += 1

    def move_train_step(self, action, features, labels):
        self.move_model.train()
        x = self._to_tensor(features)
        action = torch.as_tensor(action, dtype=torch.long, device=self.model.device)
        labels = torch.as_tensor(labels, dtype=torch.float32, device=self.model.device)
        predictions = self.move_model(x)
        pred_action_value = predictions.gather(1, action.view(-1, 1)).squeeze(1)
        loss = F.mse_loss(pred_action_value, labels)
        self.move_optimizer.zero_grad()
        loss.backward()
        self.move_optimizer.step()
        self.model.move_loss.append(float(loss.detach().cpu().item()))

    def move_train_model(self, action, features, labels, epochs=1):
        for _ in range(epochs):
            self.move_train_step(action, features, labels)

    def move_learn(self, obs, action, reward, next_obs, terminal):
        self.move_train_model(action, obs, reward, epochs=1)
        self.move_global_step += 1
