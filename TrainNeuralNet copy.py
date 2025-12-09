import tensorflow as tf
from keras import layers, models
import numpy as np
import os
import chess
import random
import matplotlib.pyplot as plt
from ChessUtils import board_to_matrix, get_dataset_from_pgn

# 模型保存路径
MODEL_PATH = './AI-chess/model/chess_model_2.keras'

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
    print("Generating random training data...")  # 替换中文
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

def plot_training_convergence(history):
    """绘制训练收敛曲线"""
    plt.figure(figsize=(12, 8))
    
    # 创建双Y轴
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # 左Y轴：损失值
    color = 'tab:red'
    ax1.set_xlabel('Epochs')  # 替换中文
    ax1.set_ylabel('Loss (MSE)', color=color)  # 替换中文
    line1 = ax1.plot(history.history['loss'], label='Training Loss', color='red', linewidth=2)
    line2 = ax1.plot(history.history['val_loss'], label='Validation Loss', color='orange', linewidth=2)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    
    # 右Y轴：准确率 (MAE)
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Accuracy (MAE)', color=color)  # 替换中文
    line3 = ax2.plot(history.history['mae'], label='Training MAE', color='blue', linewidth=2, linestyle='--')
    line4 = ax2.plot(history.history['val_mae'], label='Validation MAE', color='cyan', linewidth=2, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # 合并图例
    lines = line1 + line2 + line3 + line4
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')
    
    plt.title('Neural Network Training Convergence Curve')  # 替换中文
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('./AI-chess/training_convergence.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 打印最终指标
    final_train_loss = history.history['loss'][-1]
    final_val_loss = history.history['val_loss'][-1]
    final_train_mae = history.history['mae'][-1]
    final_val_mae = history.history['val_mae'][-1]
    
    print(f"\nFinal training metrics:")  # 替换中文
    print(f"Training Loss (MSE): {final_train_loss:.4f}")  # 替换中文
    print(f"Validation Loss (MSE): {final_val_loss:.4f}")  # 替换中文
    print(f"Training MAE: {final_train_mae:.4f}")  # 替换中文
    print(f"Validation MAE: {final_val_mae:.4f}")  # 替换中文
    
    # 证明模型学到了东西
    if final_val_loss < history.history['val_loss'][0] * 0.8:  # 损失减少超过20%
        print("\n✅ Model successfully learned useful features!")  # 替换中文
        print("   - Validation loss decreased significantly")  # 替换中文
        print("   - Model generalization ability improved")  # 替换中文
    else:
        print("\n⚠️ Model learning effect is limited, you may need to:")  # 替换中文
        print("   - More training data")  # 替换中文
        print("   - Adjust model architecture")  # 替换中文
        print("   - Increase training epochs")  # 替换中文

if __name__ == "__main__":
    # === 配置区域 ===
    use_real_data = True  # 改为 True 并设置下方路径以训练真正的 AI
    pgn_path = "./AI-chess/training_data/Abdusattorov.pgn" 
    epochs = 50  # 增加训练轮数以获得更好的收敛曲线
    # ===============
    
    # 创建模型目录
    os.makedirs('./AI-chess/model', exist_ok=True)
    
    model = create_model()
    model.summary()
    
    if use_real_data and os.path.exists(pgn_path):
        print(f"Loading data from {pgn_path}...")  # 替换中文
        x_train, y_train = get_dataset_from_pgn(pgn_path, max_games=500)
    else:
        print("PGN file not found or in test mode, generating demo data with random samples...")  # 替换中文
        x_train, y_train = generate_random_data(2000)
        
    print(f"Starting training, number of samples: {len(x_train)}")  # 替换中文
    
    # 训练模型并保存历史记录
    history = model.fit(
        x_train, y_train, 
        epochs=epochs, 
        batch_size=32, 
        validation_split=0.1,
        verbose=1
    )
    
    # 绘制训练收敛曲线
    plot_training_convergence(history)
    
    # 保存模型
    model.save(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")  # 替换中文