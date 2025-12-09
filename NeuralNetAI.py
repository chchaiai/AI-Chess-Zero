import tensorflow as tf
import numpy as np
import chess
import sys
import os
from AlphaBetaAI import AlphaBetaAI
from ChessUtils import board_to_matrix

class NeuralNetAI(AlphaBetaAI):
    def __init__(self, depth: int, is_white: bool):
        # 初始化父类
        super().__init__(depth, is_white)
        self.model = None
        self.load_model()
        
    def load_model(self):
        """加载训练好的模型"""
        model_path = './AI-chess/model/chess_model.keras'
        if os.path.exists(model_path):
            try:
                self.model = tf.keras.models.load_model(model_path)
                print("Neural Network model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print("Warning: 'chess_model.h5' not found. NeuralAI will behave randomly.")

    def advanced_evaluation(self, board: chess.Board) -> int:
        """
        重写父类的评估函数。
        使用神经网络来评估局面，而不是手动计算分值。
        """
        # 1. 处理终局情况 (这是规则，神经网络不需要学)
        if board.is_checkmate():
            return -100000 if board.turn == self.is_white else 100000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
            
        # 2. 如果模型未加载，回退到父类的评估
        if self.model is None:
            return super().advanced_evaluation(board)

        # 3. 神经网络评估
        # 转换数据格式
        matrix = board_to_matrix(board)
        # 增加 batch 维度 (1, 8, 8, 12)
        input_data = np.expand_dims(matrix, axis=0)
        
        # 预测 (返回 -1 到 1 之间的浮点数)
        # 注意：在循环中调用 predict 会比较慢，但这对于作业演示是可以接受的
        prediction = self.model(input_data, training=False).numpy()[0][0]
        
        # 4. 将 -1~1 的浮点数映射回 AlphaBeta 需要的大整数分值 (如 -10000 到 10000)
        score = int(prediction * 10000)
        
        # AlphaBeta 算法通常期望返回相对于白棋的分数，
        # 或者相对于当前走棋方的分数。
        # 这里我们的模型设计是：1代表白优，-1代表黑优。
        # 如果 self.is_white 为 True，我们想要分越高越好。
        # 如果 self.is_white 为 False，我们通过父类逻辑处理，
        # 但通常 AlphaBeta 实现中，如果 advanced_evaluation 返回的是绝对分数（白正黑负），
        # 那么需要在外部根据 turn 调整。
        # 查看你的 AlphaBetaAI 代码，最后返回的是: return score if self.is_white else -score
        # 这意味着 advanced_evaluation 应该返回 "对该 AI 有利程度" 的绝对值，或者标准白正黑负值。
        
        # 假设你的 AlphaBetaAI 逻辑是标准的 "Evaluate for White"，然后根据 is_white 翻转：
        return score