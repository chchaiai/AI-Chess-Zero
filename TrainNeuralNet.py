import tensorflow as tf
from keras import layers, models
import numpy as np
import os
import chess
import random
from ChessUtils import board_to_matrix, get_dataset_from_pgn

# 模型保存路径
MODEL_PATH = './AI-chess/model/chess_model.keras'

def create_model():
    """创建一个简单的卷积神经网络 (CNN)"""
    model = models.Sequential([
        # 输入层: 8x8x12
        layers.Input(shape=(8, 8, 12)),
        
        # 卷积层提取特征
        layers.Conv2D(64, kernel_size=(3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(64, kernel_size=(3, 3), activation='relu', padding='same'),
        layers.MaxPooling2D(pool_size=(2, 2)),
        
        layers.Conv2D(128, kernel_size=(3, 3), activation='relu', padding='same'),
        layers.Flatten(),
        
        # 全连接层进行评估
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        
        # 输出层: 1个数值，范围 -1 (黑胜) 到 1 (白胜)
        layers.Dense(1, activation='tanh') 
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def generate_random_data(num_samples=1000):
    """生成随机数据用于测试代码流程 (AI 会很笨)"""
    print("生成随机训练数据中...")
    inputs = []
    labels = []
    board = chess.Board()
    
    for _ in range(num_samples):
        if board.is_game_over():
            board.reset()
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            board.reset()
            continue
            
        move = random.choice(legal_moves)
        board.push(move)
        
        inputs.append(board_to_matrix(board))
        # 随机标签：仅仅为了让代码跑通
        labels.append(random.uniform(-1, 1))
        
    return np.array(inputs), np.array(labels)

if __name__ == "__main__":
    # === 配置区域 ===
    use_real_data = True  # 改为 True 并设置下方路径以训练真正的 AI
    pgn_path = "./AI-chess/training_data/Abdusattorov.pgn" 
    # ===============
    
    model = create_model()
    model.summary()
    
    if use_real_data and os.path.exists(pgn_path):
        print(f"从 {pgn_path} 加载数据...")
        x_train, y_train = get_dataset_from_pgn(pgn_path, max_games=500)
    else:
        print("未找到PGN文件或处于测试模式，使用随机数据生成演示...")
        x_train, y_train = generate_random_data(2000)
        
    print(f"开始训练，样本数: {len(x_train)}")
    model.fit(x_train, y_train, epochs=10, batch_size=32, validation_split=0.1)
    
    model.save(MODEL_PATH)
    print(f"模型已保存至 {MODEL_PATH}")