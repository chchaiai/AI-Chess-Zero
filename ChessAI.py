# 基类：提取公共方法和属性，减少重复代码
import chess
import sys
import random
import datetime

class ChessAI:
    def __init__(self, depth, is_white):
        self.depth = depth
        self.is_white = is_white  # 是否为白方
        self.nodes_visited = 0    # 搜索节点计数
        self.transposition_table = {}  # 置换表：缓存局面评估结果
        # 棋子位置价值表（基于国际象棋理论，中心位置更有价值）
        self.piece_position_scores = {
            'P': [  # 白兵
                [0, 0, 0, 0, 0, 0, 0, 0],
                [5, 10, 10, -20, -20, 10, 10, 5],
                [5, -5, -10, 0, 0, -10, -5, 5],
                [0, 0, 20, 30, 30, 20, 0, 0],
                [5, 5, 10, 25, 25, 10, 5, 5],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            'N': [  # 白马
                [-50, -40, -30, -30, -30, -30, -40, -50],
                [-40, -20, 0, 5, 5, 0, -20, -40],
                [-30, 5, 10, 15, 15, 10, 5, -30],
                [-30, 0, 15, 20, 20, 15, 0, -30],
                [-30, 5, 15, 20, 20, 15, 5, -30],
                [-30, 0, 10, 15, 15, 10, 0, -30],
                [-40, -20, 0, 0, 0, 0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]
            ],
            # 其他棋子的位置表（简化，实际可补充完整）
            'B': [[-20, -10, -10, -10, -10, -10, -10, -20],
                  [-10, 5, 0, 0, 0, 0, 5, -10],
                  [-10, 10, 10, 10, 10, 10, 10, -10],
                  [-10, 0, 10, 10, 10, 10, 0, -10],
                  [-10, 5, 5, 10, 10, 5, 5, -10],
                  [-10, 0, 5, 10, 10, 5, 0, -10],
                  [-10, 0, 0, 0, 0, 0, 0, -10],
                  [-20, -10, -10, -10, -10, -10, -10, -20]],
            'R': [[0, 0, 0, 5, 5, 0, 0, 0],
                  [-5, 0, 0, 0, 0, 0, 0, -5],
                  [-5, 0, 0, 0, 0, 0, 0, -5],
                  [-5, 0, 0, 0, 0, 0, 0, -5],
                  [-5, 0, 0, 0, 0, 0, 0, -5],
                  [-5, 0, 0, 0, 0, 0, 0, -5],
                  [5, 10, 10, 10, 10, 10, 10, 5],
                  [0, 0, 0, 0, 0, 0, 0, 0]],
            'Q': [[-20, -10, -10, -5, -5, -10, -10, -20],
                  [-10, 0, 0, 0, 0, 0, 0, -10],
                  [-10, 0, 5, 5, 5, 5, 0, -10],
                  [-5, 0, 5, 5, 5, 5, 0, -5],
                  [0, 0, 5, 5, 5, 5, 0, -5],
                  [-10, 5, 5, 5, 5, 5, 0, -10],
                  [-10, 0, 5, 0, 0, 0, 0, -10],
                  [-20, -10, -10, -5, -5, -10, -10, -20]],
            'K': [[20, 30, 10, 0, 0, 10, 30, 20],
                  [20, 20, 0, 0, 0, 0, 20, 20],
                  [-10, -20, -20, -20, -20, -20, -20, -10],
                  [-20, -30, -30, -40, -40, -30, -30, -20],
                  [-30, -40, -40, -50, -50, -40, -40, -30],
                  [-30, -40, -40, -50, -50, -40, -40, -30],
                  [-30, -40, -40, -50, -50, -40, -40, -30],
                  [-30, -40, -40, -50, -50, -40, -40, -30]]
        }

    def piece_score(self, piece):
        """计算棋子本身的价值"""
        if not piece:
            return 0
        piece_str = str(piece)
        # 基础子力价值
        base_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
        value = base_values.get(piece_str.upper(), 0)
        # 黑棋价值为负
        return value if piece_str.isupper() else -value

    def position_score(self, piece, square):
        """计算棋子位置价值（基于位置表）"""
        if not piece:
            return 0
        piece_str = str(piece)
        # 黑棋位置表使用反转的白棋表
        if piece_str.islower():
            table = self.piece_position_scores[piece_str.upper()][::-1]  # 反转行
            row, col = 7 - (square // 8), square % 8
        else:
            table = self.piece_position_scores[piece_str]
            row, col = square // 8, square % 8
        return table[row][col]

    def mobility_score(self, board):
        """计算棋子活动性分数（合法走法数量）"""
        mobility = len(list(board.legal_moves))
        # 白方加分，黑方减分
        return mobility if board.turn == chess.WHITE else -mobility

    def heuristic_eval(self, board):
        """增强版评估函数：综合子力、位置、活动性和将死情况"""
        # 检查将死（最高优先级）
        if board.is_checkmate():
            # 若当前回合是对方回合（说明己方造成将死）
            return 100000 if board.turn != self.is_white else -100000
        
        # 检查平局（ stalemate 等）
        if self.cuttoff_test(board):
            return 0

        total = 0
        # 子力价值
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            total += self.piece_score(piece)
            total += self.position_score(piece, square)
        
        # 活动性价值（权重较低）
        total += self.mobility_score(board) * 10
        return total

    def cuttoff_test(self, board):
        """检查是否终止搜索（平局情况）"""
        return (board.is_stalemate() or 
                board.is_fivefold_repetition() or 
                board.is_fifty_moves() or 
                board.is_seventyfive_moves() or 
                board.is_insufficient_material())

    def order_moves(self, board, moves):
        """移动排序：优先搜索更可能好的走法（提升剪枝效率）"""
        move_scores = []
        for move in moves:
            score = 0
            # 吃子加分（被吃子价值 - 吃子价值，避免用高价值子吃低价值子）
            captured = board.piece_at(move.to_square)
            if captured:
                score += self.piece_score(captured) - self.piece_score(board.piece_at(move.from_square)) * 0.1
            # 升变加分（升变为后优先级最高）
            if move.promotion == chess.QUEEN:
                score += 1000
            # 中心控制加分（e4, d4, e5, d5）
            if move.to_square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                score += 50
            move_scores.append((-score, move))  # 负号用于升序排序时优先高分
        
        # 按分数排序（分数高的先搜索）
        move_scores.sort()
        return [move for (_, move) in move_scores]