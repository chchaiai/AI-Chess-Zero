import datetime
import random
import sys
import chess
from typing import Dict, List, Optional, Tuple

class AlphaBetaAI():
    def __init__(self, depth: int, is_white: bool):
        self.depth = depth
        self.is_white = is_white
        self.nodes_visited = 0
        self.transposition_table: Dict[str, Tuple[int, int, chess.Move]] = {}  # 置换表
        self.killer_moves: Dict[int, List[chess.Move]] = {}  # 杀手启发
        
        # 增强的棋子价值表
        self.piece_values = {
            'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
            'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
        }
        
        # 棋子位置价值表（基于国际象棋理论）
        self.position_scores = {
            'P': [  # 兵
                [0, 0, 0, 0, 0, 0, 0, 0],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [5, 5, 10, 25, 25, 10, 5, 5],
                [0, 0, 0, 20, 20, 0, 0, 0],
                [5, -5, -10, 0, 0, -10, -5, 5],
                [5, 10, 10, -20, -20, 10, 10, 5],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            'N': [  # 马
                [-50, -40, -30, -30, -30, -30, -40, -50],
                [-40, -20, 0, 0, 0, 0, -20, -40],
                [-30, 0, 10, 15, 15, 10, 0, -30],
                [-30, 5, 15, 20, 20, 15, 5, -30],
                [-30, 0, 15, 20, 20, 15, 0, -30],
                [-30, 5, 10, 15, 15, 10, 5, -30],
                [-40, -20, 0, 5, 5, 0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]
            ]
        }

    def choose_move(self, board: chess.Board) -> chess.Move:
        """选择最佳移动"""
        self.nodes_visited = 0
        best_move = None
        best_value = -sys.maxsize
        
        # 迭代加深搜索
        for current_depth in range(1, self.depth + 1):
            try:
                move, value = self.alpha_beta_search(board, current_depth)
                if move:
                    best_move = move
                    best_value = value
                    print(f"Depth {current_depth}: {move} (eval: {value})")
            except Exception as e:
                print(f"Search error at depth {current_depth}: {e}")
                break
        
        if not best_move:
            # 备用：随机选择合法移动
            best_move = random.choice(list(board.legal_moves))
        
        print(f"AlphaBeta AI recommending move {best_move} at depth {self.depth}, nodes visited: {self.nodes_visited}")
        return best_move

    def alpha_beta_search(self, board: chess.Board, max_depth: int) -> Tuple[Optional[chess.Move], int]:
        """带alpha-beta剪枝的搜索"""
        best_move = None
        best_value = -sys.maxsize
        alpha = -sys.maxsize
        beta = sys.maxsize
        
        # 排序移动以提高剪枝效率
        moves = self.order_moves(board)
        
        for move in moves:
            board.push(move)
            value = -self.alpha_beta(board, max_depth - 1, -beta, -alpha, False)
            board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, best_value)
            if alpha >= beta:
                # 保存杀手移动
                self.store_killer_move(max_depth, move)
                break
        
        return best_move, best_value

    def alpha_beta(self, board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        """Alpha-beta剪枝核心算法"""
        self.nodes_visited += 1
        
        # 终止条件检查
        if depth == 0 or board.is_game_over():
            return self.advanced_evaluation(board)
        
        # 置换表查询
        board_key = board.fen()
        if board_key in self.transposition_table:
            tt_depth, tt_value, _ = self.transposition_table[board_key]
            if tt_depth >= depth:
                return tt_value
        
        moves = self.order_moves(board)
        best_value = -sys.maxsize if maximizing else sys.maxsize
        
        for move in moves:
            board.push(move)
            
            if maximizing:
                value = self.alpha_beta(board, depth - 1, alpha, beta, False)
                best_value = max(best_value, value)
                alpha = max(alpha, best_value)
            else:
                value = self.alpha_beta(board, depth - 1, alpha, beta, True)
                best_value = min(best_value, value)
                beta = min(beta, best_value)
            
            board.pop()
            
            # Alpha-beta剪枝
            if alpha >= beta:
                self.store_killer_move(depth, move)
                break
        
        # 保存到置换表
        self.transposition_table[board_key] = (depth, best_value, moves[0] if moves else None)
        
        return best_value

    def order_moves(self, board: chess.Board) -> List[chess.Move]:
        """移动排序：优先搜索好的移动"""
        moves = list(board.legal_moves)
        move_scores = []
        
        for move in moves:
            score = 0
            
            # 1. 杀手移动启发
            if self.is_killer_move(move, len(moves)):
                score += 1000
            
            # 2. 吃子移动启发（MVV-LVA）
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    # 被吃子价值 - 吃子价值（避免用高价值吃低价值）
                    attacker_value = abs(self.piece_values.get(str(board.piece_at(move.from_square)), 0))
                    victim_value = abs(self.piece_values.get(str(captured_piece), 0))
                    score += victim_value - attacker_value + 1000
            
            # 3. 升变启发
            if move.promotion:
                score += 900  # 升变价值
            
            # 4. 历史启发（简单版本）
            score += random.randint(0, 10)  # 添加随机性避免重复
            
            move_scores.append((score, move))
        
        # 按分数降序排序
        move_scores.sort(reverse=True, key=lambda x: x[0])
        return [move for _, move in move_scores]

    def advanced_evaluation(self, board: chess.Board) -> int:
        """增强的评估函数"""
        if board.is_checkmate():
            return -100000 if board.turn == self.is_white else 100000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        score = 0
        
        # 1. 子力价值
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_str = str(piece)
                score += self.piece_values.get(piece_str, 0)
                
                # 2. 位置价值
                if piece_str.upper() in ['P', 'N']:
                    score += self.get_position_score(piece_str, square)
        
        # 3. 活动性（移动数量）
        mobility = len(list(board.legal_moves))
        score += mobility * (10 if board.turn == self.is_white else -10)
        
        # 4. 王的安全（简单检查）
        if board.is_check():
            score += -50 if board.turn == self.is_white else 50
        
        return score if self.is_white else -score

    def get_position_score(self, piece: str, square: chess.Square) -> int:
        """获取棋子位置分数"""
        piece_type = piece.upper()
        if piece_type not in self.position_scores:
            return 0
        
        row = 7 - (square // 8) if piece.islower() else square // 8
        col = square % 8
        return self.position_scores[piece_type][row][col]

    def store_killer_move(self, depth: int, move: chess.Move):
        """保存杀手移动"""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        
        if move not in self.killer_moves[depth]:
            self.killer_moves[depth].insert(0, move)
            # 保持最多2个杀手移动
            if len(self.killer_moves[depth]) > 2:
                self.killer_moves[depth].pop()

    def is_killer_move(self, move: chess.Move, total_moves: int) -> bool:
        """检查是否是杀手移动"""
        for depth in self.killer_moves:
            if move in self.killer_moves[depth]:
                return True
        return False

    def cuttoff_test(self, board: chess.Board) -> bool:
        """终止测试"""
        return (board.is_stalemate() or 
                board.is_fivefold_repetition() or 
                board.is_fifty_moves() or 
                board.is_seventyfive_moves() or 
                board.is_insufficient_material())