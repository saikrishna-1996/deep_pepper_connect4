import multiprocessing
import time

import numpy as np

from config import Config
from game.chess_env import ChessEnv
from game.features import board_to_feature
from network.policy_network import PolicyValNetwork_Giraffe
from network.value_network import Critic_Giraffe
from train.MCTS import MCTS, Node
from train.self_challenge import Champion


class GameGenerator(object):
    def __init__(self, champion: Champion, pool: multiprocessing.Pool, batch_size: int, workers: int):
        self.champion = champion
        self.pool = pool
        self.workers = workers
        self.batch_size = batch_size

    def generate_game(self, pol_model: PolicyValNetwork_Giraffe, val_model: Critic_Giraffe):
        np.random.seed()
        triplets = []
        step_game = 0
        temperature = 1
        # env = ChessEnv()
        # env.reset()
        game_over = False
        moves = 0
        #game_over, z = env.is_game_over(moves)
        env = ChessEnv()
        env.reset()
        root_node = Node(env,Config.EXPLORE_FACTOR)
        while not game_over:
            moves += 1
            step_game += 1
            if step_game == 50:
                temperature = 10e-6

            pi, successor, root_node = MCTS(temp=temperature, pol_network=pol_model, val_network = val_model, root=root_node)
            feature = board_to_feature(root_node.env.board)
            triplets.append([feature, pi])
            print('')
            print(root_node.env.board)
            print("Running on {} ".format(multiprocessing.current_process()))
            root_node = successor
            game_over, z = root_node.env.is_game_over(moves, res_check=True)
        for i in range(len(triplets) - step_game, len(triplets)):
            triplets[i].append(z)

        return triplets

    def play_game(self, _):
        return self.generate_game(self.champion.current_policy)

    def generate_games(self):
        start = time.time()
        games_per_worker = range(int(self.batch_size / self.workers + 1))
        games = self.pool.map(self.play_game, games_per_worker)
        print("Generated {} games in {}".format(len(games), time.time() - start))
        return games

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict
