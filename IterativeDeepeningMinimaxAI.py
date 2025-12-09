import datetime
import sys
import random
import time
import chess
from typing import Dict, List, Optional, Tuple

class IterativeDeepeningMinimaxAI():
    def __init__(self, depth: int, is_white: bool):
        self.max_depth = depth
        self.is_white = is_white
        self.nodes_visited = 0
        self.best_move_history: List[chess.Move] = []
        
        # 时间管理（简单版本）
        self.start_time = None
        self.time_limit = 5.0  # 5秒时间限制
        
        # 增强的评估参数
        self.piece_values = {
            'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
            'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
        }

    def choose_move(self, board: chess.Board) -> chess.Move:
        """迭代加深搜索选择最佳移动"""
        start_time = time.time()
        self.start_time = datetime.datetime.now()
        self.nodes_visited = 0
        best_move = None
        best_value = -sys.maxsize if self.is_white else sys.maxsize
        
        print(f"Starting iterative deepening search to depth {self.max_depth}")
        
        # 迭代加深搜索
        for current_depth in range(1, self.max_depth + 1):
            if self.time_limit_reached():
                print(f"Time limit reached at depth {current_depth - 1}")
                break
                
            try:
                move, value = self.iterative_deepening_search(board, current_depth)
                
                if move:
                    best_move = move
                    best_value = value
                    self.best_move_history.append(move)
                    
                    print(f"Depth {current_depth}: {move} (eval: {value}, nodes: {self.nodes_visited})")
                    
                    # 如果找到必胜局面，提前终止
                    if abs(value) > 50000:  # 将死分数
                        print("Found winning move, stopping search")
                        break
                        
            except Exception as e:
                print(f"Search error at depth {current_depth}: {e}")
                break
        
        if not best_move:
            # 备用策略
            best_move = self.fallback_move(board)
        
        print(f"IterativeDeepening AI recommending move {best_move} after visiting {self.nodes_visited} nodes")
        end_time = time.time()
        elapsed_time = end_time - start_time  # 需在方法开始处记录start_time
        nps = self.nodes_visited / elapsed_time if elapsed_time > 0 else 0
        print(f"AlphaBetaAI NPS: {nps:.2f}")
        return best_move

    def iterative_deepening_search(self, board: chess.Board, max_depth: int) -> Tuple[Optional[chess.Move], int]:
        """迭代加深搜索核心"""
        best_move = None
        best_value = -sys.maxsize if self.is_white else sys.maxsize
        
        # 使用前一层的最佳移动作为这一层的第一个尝试
        moves = self.order_moves_with_history(board)
        
        for move in moves:
            if self.time_limit_reached():
                break
                
            board.push(move)
            value = self.minimax(board, max_depth - 1, not self.is_white, -sys.maxsize, sys.maxsize)
            board.pop()
            
            if (self.is_white and value > best_value) or (not self.is_white and value < best_value):
                best_value = value
                best_move = move
        
        return best_move, best_value

    def minimax(self, board: chess.Board, depth: int, maximizing: bool, alpha: int, beta: int) -> int:
        """带alpha-beta剪枝的minimax算法"""
        self.nodes_visited += 1
        
        # 终止条件
        if depth == 0 or board.is_game_over():
            return self.enhanced_evaluation(board)
        
        # 检查时间限制
        if self.time_limit_reached():
            return self.enhanced_evaluation(board)
        
        moves = list(board.legal_moves)
        if not moves:
            return self.enhanced_evaluation(board)
        
        if maximizing:
            max_eval = -sys.maxsize
            for move in moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, False, alpha, beta)
                board.pop()
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Beta剪枝
                    
            return max_eval
        else:
            min_eval = sys.maxsize
            for move in moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, True, alpha, beta)
                board.pop()
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha剪枝
                    
            return min_eval

    def order_moves_with_history(self, board: chess.Board) -> List[chess.Move]:
        """基于历史信息的移动排序"""
        moves = list(board.legal_moves)
        
        if not moves:
            return moves
        
        # 如果有历史最佳移动，优先尝试
        move_scores = []
        for move in moves:
            score = 0
            
            # 历史最佳移动优先
            if self.best_move_history and move == self.best_move_history[-1]:
                score += 1000
            
            # 吃子移动优先
            if board.is_capture(move):
                score += 500
                
            # 检查移动优先
            board.push(move)
            if board.is_check():
                score += 300
            board.pop()
            
            # 随机性避免重复模式
            score += random.randint(0, 50)
            
            move_scores.append((score, move))
        
        move_scores.sort(reverse=True, key=lambda x: x[0])
        return [move for _, move in move_scores]

    def enhanced_evaluation(self, board: chess.Board) -> int:
        """增强的评估函数"""
        # 游戏结束状态评估
        if board.is_checkmate():
            return -100000 if board.turn else 100000
        
        if board.is_stalemate():
            return 0
        
        # 基础子力评估
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                score += self.piece_values.get(str(piece), 0)
        
        # 移动性评估
        current_mobility = len(list(board.legal_moves))
        score += current_mobility * 10
        
        # 王的安全评估
        if board.is_check():
            score -= 50
        
        # 中心控制评估（简化）
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        for square in center_squares:
            piece = board.piece_at(square)
            if piece and piece.color == board.turn:
                score += 20
        
        return score if self.is_white else -score

    def time_limit_reached(self) -> bool:
        """检查时间限制"""
        if not self.start_time:
            return False
        
        elapsed = (datetime.datetime.now() - self.start_time).total_seconds()
        return elapsed >= self.time_limit

    def fallback_move(self, board: chess.Board) -> chess.Move:
        """备用移动选择策略"""
        moves = list(board.legal_moves)
        
        # 优先选择吃子移动
        captures = [move for move in moves if board.is_capture(move)]
        if captures:
            return random.choice(captures)
        
        # 优先选择检查移动
        checks = []
        for move in moves:
            board.push(move)
            if board.is_check():
                checks.append(move)
            board.pop()
        
        if checks:
            return random.choice(checks)
        
        # 随机选择
        return random.choice(moves) if moves else None

    def cuttoff_test(self, board: chess.Board) -> bool:
        """终止测试"""
        return board.is_game_over()