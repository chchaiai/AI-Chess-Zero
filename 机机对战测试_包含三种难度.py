# Ari Chadda
# 9 October 2020
# Chess AI Assignment CS76 F20
import argparse
from PyQt5 import QtGui, QtSvg
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox  # 导入QMessageBox
import sys
import chess, chess.svg

from IterativeDeepeningMinimaxAI import IterativeDeepeningMinimaxAI
from RandomAI import RandomAI
from HumanPlayer import HumanPlayer
from AlphaBetaAI import AlphaBetaAI
from BetterAlphaBetaAI import BetterAlphaBetaAI
from ChessGame import ChessGame
from NeuralNetAI import NeuralNetAI

import random


class ChessGui:
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.game = ChessGame(player1, player2)
        self.app = QApplication(sys.argv)
        self.svgWidget = QtSvg.QSvgWidget()
        self.svgWidget.setGeometry(800, 300, 1000, 1000)
        self.svgWidget.show()
        self.timer = QTimer()  # 将timer设为实例变量，方便停止


    def start(self):
        self.timer.timeout.connect(self.make_move)
        self.timer.start(50)
        self.display_board()

    def display_board(self):
        svgboard = chess.svg.board(self.game.board)
        svgbytes = QByteArray()
        svgbytes.append(svgboard)
        self.svgWidget.load(svgbytes)

    def make_move(self):
        print("making move, white turn " + str(self.game.board.turn))

        if not self.game.exit_game():
            self.game.make_move()
            self.display_board()
            
            # 每次落子后检查游戏是否结束
            self.check_game_end()
        else:
            # 游戏已结束（可能是上一轮结束的），直接检查并弹窗
            self.check_game_end()

    def check_game_end(self):
        """检查游戏是否结束，若结束则弹窗提示并停止计时器"""
        board = self.game.board
        # 1. 检查将死（胜利条件）
        if board.is_checkmate():
            winner = "白方" if not board.turn else "黑方"  # 此时turn是输家的回合（因为刚结束）
            QMessageBox.information(self.svgWidget, "游戏结束", f"{winner}胜利！（将死）")
            self.timer.stop()  # 停止计时器，游戏终止
        # 2. 检查平局条件（可选，避免无限循环）
        elif board.is_stalemate():
            QMessageBox.information(self.svgWidget, "游戏结束", "平局！（困毙）")
            self.timer.stop()
        elif board.is_insufficient_material():
            QMessageBox.information(self.svgWidget, "游戏结束", "平局！（双方子力不足以将死）")
            self.timer.stop()
        elif board.is_seventyfive_moves():
            QMessageBox.information(self.svgWidget, "游戏结束", "平局！（75步规则）")
            self.timer.stop()
        elif board.is_fivefold_repetition():
            QMessageBox.information(self.svgWidget, "游戏结束", "平局！（五重重复）")
            self.timer.stop()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Chess Game Parameters")
    parser.add_argument("--white-difficulty", type=str, default="Easy",choices=["Easy", "Medium", "Hard","Neural"], help='White difficulty level')
    parser.add_argument("--black-difficulty", type=str, default="Easy",choices=["Easy", "Medium", "Hard","Neural"], help='Black difficulty level')
    return parser.parse_args()


if __name__ == "__main__":
    random.seed(1)
    args = parse_arguments()

    # 根据难度选择玩家
    if args.white_difficulty == "Easy":
        player1 = RandomAI()
    elif args.white_difficulty == "Medium":
        player1 = IterativeDeepeningMinimaxAI(2, True)
    elif args.white_difficulty == "Hard":
        player1 = BetterAlphaBetaAI(3, True)
    elif args.white_difficulty == "Neural":
        print("正在初始化神经网络AI")
        player1 = NeuralNetAI(2, True)
    
    if args.black_difficulty == "Easy":
        player2 = RandomAI()
    elif args.black_difficulty == "Medium":
        player2 = IterativeDeepeningMinimaxAI(2, False)
    elif args.black_difficulty == "Hard":
        player2 = BetterAlphaBetaAI(3, False)
    elif args.black_difficulty == "Neural":
        print("正在初始化神经网络AI")
        player2 = NeuralNetAI(2, True)

    # 初始化游戏和GUI
    gui = ChessGui(player1, player2)
    gui.start()
    sys.exit(gui.app.exec_())