import sys
import os
import chess
import time
from typing import Tuple

# 引入现有的 AI 类
from RandomAI import RandomAI
from IterativeDeepeningMinimaxAI import IterativeDeepeningMinimaxAI
from BetterAlphaBetaAI import BetterAlphaBetaAI
from NeuralNetAI import NeuralNetAI

# --- 工具类：用于隐藏 AI 思考时的控制台输出 ---
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

# --- AI 工厂函数 ---
def create_ai(ai_name: str, is_white: bool):
    """根据名称创建 AI 实例，设定默认难度深度"""
    if ai_name == "RandomAI":
        return RandomAI()
    elif ai_name == "ID-Minimax":
        # 默认深度 2，与你原本的 GUI 设置一致
        return IterativeDeepeningMinimaxAI(2, is_white)
    elif ai_name == "BetterAlphaBeta":
        # 默认深度 3
        return BetterAlphaBetaAI(3, is_white)
    elif ai_name == "NeuralNetAI":
        # 默认深度 2
        return NeuralNetAI(2, is_white)
    else:
        raise ValueError(f"Unknown AI: {ai_name}")

# --- 单局游戏逻辑 ---
def play_single_game(white_ai_name, black_ai_name, max_moves=200) -> str:
    """
    运行一局游戏。
    返回: "1-0" (白胜), "0-1" (黑胜), "1/2-1/2" (平局)
    """
    board = chess.Board()
    
    # 实例化 AI (每次必须重新实例化以清空置换表/缓存)
    white_player = create_ai(white_ai_name, True)
    black_player = create_ai(black_ai_name, False)
    
    move_count = 0
    
    while not board.is_game_over() and move_count < max_moves:
        # 轮流走棋
        player = white_player if board.turn else black_player
        
        try:
            # 使用上下文管理器隐藏 AI 内部的 print 输出
            with HiddenPrints():
                move = player.choose_move(board)
            
            board.push(move)
            move_count += 1
        except Exception as e:
            # 如果 AI 出错（例如超时或崩溃），判负
            # print(f"Error in game: {e}")
            return "0-1" if board.turn else "1-0"

    # 游戏结束判定
    result = board.result()
    
    # 如果达到最大步数强制平局（防止 Random vs Random 死循环）
    if move_count >= max_moves and result == "*":
        return "1/2-1/2"
        
    return result

# --- 评测逻辑 ---
def evaluate_matchup(matchup_name, white_name, black_name, num_games):
    print(f"正在进行测试: {matchup_name} [{white_name} vs {black_name}] (共 {num_games} 局)...")
    
    white_wins = 0
    black_wins = 0
    draws = 0
    
    # 进度条效果
    for i in range(num_games):
        print(f"\r  进度: {i+1}/{num_games}", end="", flush=True)
        result = play_single_game(white_name, black_name)
        
        if result == "1-0":
            white_wins += 1
        elif result == "0-1":
            black_wins += 1
        else:
            draws += 1
            
    print(f" -> 完成")
    
    return {
        "Matchup": matchup_name,
        "White": white_name,
        "Black": black_name,
        "A_Win_Pct": (white_wins / num_games) * 100,
        "Draw_Pct": (draws / num_games) * 100,
        "B_Win_Pct": (black_wins / num_games) * 100
    }

# --- 主程序 ---
if __name__ == "__main__":
    # 定义测试配置
    test_cases = [
        ("Test 1", "RandomAI", "RandomAI"),
        ("Test 2", "ID-Minimax", "RandomAI"),
        ("Test 3", "BetterAlphaBeta", "ID-Minimax"),
        ("Test 4", "NeuralNetAI", "RandomAI")
    ]
    
    TOTAL_GAMES_PER_MATCH = 50  # 每组对决的局数
    results = []

    print("=== 开始自动化对战测试 ===")
    print(f"每组对决局数: {TOTAL_GAMES_PER_MATCH}")
    print("注意: 复杂的 AI (如 AlphaBeta) 思考时间较长，请耐心等待。\n")

    start_time = time.time()

    for test_name, white, black in test_cases:
        stats = evaluate_matchup(test_name, white, black, TOTAL_GAMES_PER_MATCH)
        results.append(stats)

    total_time = time.time() - start_time
    
    # --- 打印表格 ---
    print("\n\n" + "="*90)
    print(f"Table 1: Head-to-Head Win Rates (50 Games)")
    print("="*90)
    
    # 表头
    header = f"{'Matchup':<10} | {'White (Player A)':<20} | {'Black (Player B)':<20} | {'A Win %':<8} | {'Draw %':<8} | {'B Win %':<8}"
    print(header)
    print("-" * len(header))
    
    # 数据行
    for row in results:
        print(f"{row['Matchup']:<10} | "
              f"{row['White']:<20} | "
              f"{row['Black']:<20} | "
              f"{row['A_Win_Pct']:>6.1f}% | "
              f"{row['Draw_Pct']:>6.1f}% | "
              f"{row['B_Win_Pct']:>6.1f}%")
              
    print("="*90)
    print(f"总耗时: {total_time:.2f} 秒")