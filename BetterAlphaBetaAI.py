import sys
import chess
import chess.polyglot
import random
import time
from typing import Dict, List, Optional, Tuple

# --- 棋子位置价值表 (基于 PeSTO 的简化版) ---
MG_TABLES = {
    chess.PAWN: [
        0,   0,   0,   0,   0,   0,   0,   0,
        50,  50,  50,  50,  50,  50,  50,  50,
        10,  10,  20,  30,  30,  20,  10,  10,
        5,   5,  10,  25,  25,  10,   5,   5,
        0,   0,   0,  20,  20,   0,   0,   0,
        5,  -5, -10,   0,   0, -10,  -5,   5,
        5,  10,  10, -20, -20,  10,  10,   5,
        0,   0,   0,   0,   0,   0,   0,   0
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  15,  20,  20,  15,   0, -30,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    chess.ROOK: [
        0,   0,   0,   0,   0,   0,   0,   0,
        5,  10,  10,  10,  10,  10,  10,   5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        0,   0,   0,   5,   5,   0,   0,   0
    ],
    chess.QUEEN: [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10,   0,   0,  0,  0,   0,   0, -10,
        -10,   0,   5,  5,  5,   5,   0, -10,
        -5,    0,   5,  5,  5,   5,   0,  -5,
        0,     0,   5,  5,  5,   5,   0,  -5,
        -10,   5,   5,  5,  5,   5,   0, -10,
        -10,   0,   5,  0,  0,   0,   0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    chess.KING: [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20,   20,   0,   0,   0,   0,  20,  20,
        20,   30,  10,   0,   0,  10,  30,  20
    ]
}

# 残局王的位置价值表
EG_KING_TABLE = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

MG_VALUE = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}
EG_VALUE = {chess.PAWN: 120, chess.KNIGHT: 280, chess.BISHOP: 300, chess.ROOK: 550, chess.QUEEN: 950, chess.KING: 20000}

class BetterAlphaBetaAI:
    def __init__(self, depth: int, is_white: bool):
        self.depth = depth
        self.is_white = is_white
        self.nodes_visited = 0
        self.tt: Dict[int, Tuple[int, int, int, Optional[chess.Move]]] = {} # Hash -> (depth, flag, score, move)
        self.killer_moves: Dict[int, List[chess.Move]] = {}
        self.history_heuristic: Dict[int, int] = {}
        
        self.mg_tables = self._init_tables(MG_TABLES)
        self.eg_tables = self._init_tables(MG_TABLES)
        self.eg_tables[chess.KING] = list(EG_KING_TABLE)
        self.mg_tables_black = {k: self._flip_table(v) for k, v in self.mg_tables.items()}
        self.eg_tables_black = {k: self._flip_table(v) for k, v in self.eg_tables.items()}

    def _init_tables(self, base_tables):
        return {k: list(v) for k, v in base_tables.items()}

    def _flip_table(self, table):
        return [table[i^56] for i in range(64)]
        
    def get_board_hash(self, board: chess.Board) -> int:
        """安全地获取 Board 的 Zobrist 哈希"""
        return chess.polyglot.zobrist_hash(board)

    def choose_move(self, board: chess.Board) -> chess.Move:
        self.nodes_visited = 0
        best_move = None
        alpha = -sys.maxsize
        beta = sys.maxsize
        
        start_time = time.time()
        
        for current_depth in range(1, self.depth + 1):
            try:
                score = self.negamax(board, current_depth, alpha, beta, 1 if board.turn else -1, is_root=True)
                
                # 从置换表获取最佳移动
                tt_entry = self.tt.get(self.get_board_hash(board))
                if tt_entry and tt_entry[3]:
                    best_move = tt_entry[3]
                    print(f"Info: Depth {current_depth} score {score} move {best_move} nodes {self.nodes_visited}")
                
            except Exception as e:
                print(f"Error at depth {current_depth}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        if not best_move:
            best_move = random.choice(list(board.legal_moves))
            
        print(f"Stats: {self.nodes_visited} nodes in {time.time() - start_time:.2f}s")
        # 在AlphaBetaAI的choose_move方法末尾添加
        end_time = time.time()
        elapsed_time = end_time - start_time  # 需在方法开始处记录start_time
        nps = self.nodes_visited / elapsed_time if elapsed_time > 0 else 0
        print(f"AlphaBetaAI NPS: {nps:.2f}")
        # 可将结果存入日志或全局列表
        return best_move

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, turn_multiplier: int, is_root: bool = False) -> int:
        self.nodes_visited += 1
        
        # --- 平局/结束判断 ---
        
        # 1. 检查强制游戏结束 (杀棋, 逼和, 75步规则, 5次重复, 材质不足)
        if board.is_game_over():
            if board.is_checkmate():
                return -20000 + (self.depth - depth) # 负分表示当前走棋方输了
            return 0 # 其他情况都是平局

        # 2. 检查可声明的平局 (3次重复, 50步规则)
        # 引擎通常应当避免进入这些局面，除非它是唯一的生路
        if board.can_claim_draw():
            return 0

        # --- 置换表查询 ---
        board_hash = self.get_board_hash(board)
        tt_entry = self.tt.get(board_hash)
        tt_move = None
        
        if tt_entry:
            tt_depth, tt_flag, tt_score, tt_move = tt_entry
            if tt_depth >= depth and not is_root:
                if tt_flag == 0: # EXACT
                    return tt_score
                elif tt_flag == 1: # LOWERBOUND (Alpha)
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2: # UPPERBOUND (Beta)
                    beta = min(beta, tt_score)
                
                if alpha >= beta:
                    return tt_score

        # --- 静态搜索 (深度耗尽时) ---
        if depth <= 0:
            return self.quiescence(board, alpha, beta, turn_multiplier)

        # --- 空着裁剪 (Null Move Pruning) ---
        if depth >= 3 and not board.is_check() and not is_root:
            board.push(chess.Move.null())
            score = -self.negamax(board, depth - 1 - 2, -beta, -beta + 1, -turn_multiplier)
            board.pop()
            if score >= beta:
                return beta

        # --- 生成与排序移动 ---
        moves = self.order_moves(board, tt_move, depth)
        
        best_score = -sys.maxsize
        best_move_found = None
        tt_flag = 2 # 默认为 UPPERBOUND

        for move in moves:
            board.push(move)
            
            # 递归搜索
            score = -self.negamax(board, depth - 1, -beta, -alpha, -turn_multiplier)
            
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move_found = move
            
            if score > alpha:
                alpha = score
                tt_flag = 0 # EXACT
                
                if alpha >= beta:
                    # 剪枝发生
                    if not board.is_capture(move):
                        self.update_killers(move, depth)
                        self.update_history(move, depth)
                    tt_flag = 1 # LOWERBOUND
                    break
        
        # 保存到置换表
        self.tt[board_hash] = (depth, tt_flag, best_score, best_move_found)
        
        return best_score

    def quiescence(self, board: chess.Board, alpha: int, beta: int, turn_multiplier: int) -> int:
        self.nodes_visited += 1
        
        stand_pat = self.evaluate(board) * turn_multiplier
        
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
            
        moves = self.order_moves(board, None, 0, only_captures=True)
        
        for move in moves:
            board.push(move)
            score = -self.quiescence(board, -beta, -alpha, -turn_multiplier)
            board.pop()
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
                
        return alpha

    def evaluate(self, board: chess.Board) -> int:
        total_material = 0
        mg_score = 0
        eg_score = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
                
            pt = piece.piece_type
            color = piece.color
            
            if pt != chess.KING:
                total_material += MG_VALUE[pt]
            
            if color == chess.WHITE:
                mg_pos = self.mg_tables[pt][square]
                eg_pos = self.eg_tables[pt][square]
                mg_val = MG_VALUE[pt] + mg_pos
                eg_val = EG_VALUE[pt] + eg_pos
                
                mg_score += mg_val
                eg_score += eg_val
            else:
                mg_pos = self.mg_tables_black[pt][square]
                eg_pos = self.eg_tables_black[pt][square]
                mg_val = MG_VALUE[pt] + mg_pos
                eg_val = EG_VALUE[pt] + eg_pos
                
                mg_score -= mg_val
                eg_score -= eg_val

        phase = min(total_material, 6000) / 6000.0
        final_score = int((mg_score * phase) + (eg_score * (1 - phase)))
        
        # 简单奖励
        if board.turn == chess.WHITE:
            if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2: final_score += 30
            if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2: final_score -= 30
        else:
            if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2: final_score += 30
            if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2: final_score -= 30
            
        return final_score

    def order_moves(self, board: chess.Board, tt_move: Optional[chess.Move], depth: int, only_captures: bool = False) -> List[chess.Move]:
        moves = list(board.generate_legal_moves(chess.BB_ALL, board.occupied_co[not board.turn])) if only_captures else list(board.legal_moves)
        if not moves:
            return []
            
        scores = []
        for move in moves:
            score = 0
            
            if move == tt_move:
                score += 2000000
                
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                aggressor = board.piece_at(move.from_square)
                if victim:
                    val_victim = MG_VALUE.get(victim.piece_type, 0)
                    val_aggressor = MG_VALUE.get(aggressor.piece_type, 0)
                    score += 100000 + val_victim * 10 - val_aggressor
                if move.promotion:
                     score += MG_VALUE[move.promotion] * 10
            else:
                if depth in self.killer_moves and move in self.killer_moves[depth]:
                    score += 9000
                
                h_score = self.history_heuristic.get((move.from_square, move.to_square), 0)
                score += min(h_score, 8000)

            scores.append(score)
            
        sorted_moves = [x for _, x in sorted(zip(scores, moves), key=lambda pair: pair[0], reverse=True)]
        return sorted_moves

    def update_killers(self, move: chess.Move, depth: int):
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        if move not in self.killer_moves[depth]:
            self.killer_moves[depth].insert(0, move)
            self.killer_moves[depth] = self.killer_moves[depth][:2]

    def update_history(self, move: chess.Move, depth: int):
        key = (move.from_square, move.to_square)
        self.history_heuristic[key] = self.history_heuristic.get(key, 0) + depth * depth