import chess
import numpy as np

# 棋子映射表：将棋子类型映射到 0-11 的索引
# 白棋: P=0, N=1, B=2, R=3, Q=4, K=5
# 黑棋: p=6, n=7, b=8, r=9, q=10, k=11
piece_idx = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
}

def board_to_matrix(board):
    """
    将 chess.Board 对象转换为 (8, 8, 12) 的 numpy 矩阵。
    """
    matrix = np.zeros((8, 8, 12), dtype=np.float32)
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # 获取棋子字符 (如 'P', 'k')
            symbol = piece.symbol()
            layer = piece_idx[symbol]
            
            # 计算行和列 (0-7)
            row = 7 - (square // 8) # 使得矩阵视觉上和棋盘方向一致
            col = square % 8
            
            matrix[row, col, layer] = 1.0
            
    return matrix

def get_dataset_from_pgn(pgn_file_path, max_games=100):
    """
    解析 PGN 文件生成训练数据 (这是一个简化的生成器)
    X: 棋盘矩阵
    Y: 结果 (1=白胜, -1=黑胜, 0=和棋)
    """
    import chess.pgn
    
    inputs = []
    labels = []
    
    with open(pgn_file_path) as f:
        count = 0
        while count < max_games:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            
            # 解析结果
            result = game.headers["Result"]
            if result == "1-0":
                y = 1.0
            elif result == "0-1":
                y = -1.0
            else:
                y = 0.0 # 平局
                
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                # 提取棋盘状态
                inputs.append(board_to_matrix(board))
                labels.append(y)
                
            count += 1
            print(f"Parsed game {count}", end='\r')
            
    return np.array(inputs), np.array(labels)