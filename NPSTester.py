import chess
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# 导入所有AI类
from RandomAI import RandomAI
from AlphaBetaAI import AlphaBetaAI
from BetterAlphaBetaAI import BetterAlphaBetaAI
from IterativeDeepeningMinimaxAI import IterativeDeepeningMinimaxAI
from NeuralNetAI import NeuralNetAI

class NPSTester:
    def __init__(self, num_tests=5, depth=3):
        self.num_tests = num_tests  # 每个AI测试次数
        self.depth = depth          # 统一搜索深度
        self.results = defaultdict(list)  # 存储结果: {AI名称: [nps1, nps2...]}
        self.initial_board = chess.Board()  # 统一初始棋盘状态

    def test_ai(self, ai_class, name, is_white=True):
        """测试单个AI的NPS性能"""
        print(f"开始测试 {name}...")
        
        for i in range(self.num_tests):
            # 每次测试使用相同初始状态
            board = chess.Board()
            board.set_fen(self.initial_board.fen())
            
            # 创建AI实例
            if ai_class in [ AlphaBetaAI, BetterAlphaBetaAI, 
                           IterativeDeepeningMinimaxAI, NeuralNetAI]:
                ai = ai_class(self.depth, is_white)
            else:
                ai = ai_class()  # RandomAI不需要参数
            
            # 记录开始时间和初始节点数
            start_time = time.time()
            if hasattr(ai, 'nodes_visited'):
                ai.nodes_visited = 0  # 重置节点计数
            
            # 执行走棋决策
            try:
                ai.choose_move(board)
            except Exception as e:
                print(f"{name} 测试失败: {e}")
                continue
            
            # 计算耗时和NPS
            end_time = time.time()
            elapsed = end_time - start_time
            
            if hasattr(ai, 'nodes_visited') and ai.nodes_visited > 0 and elapsed > 0:
                nps = ai.nodes_visited / elapsed
                self.results[name].append(nps)
                print(f"  测试 {i+1}/{self.num_tests}: {ai.nodes_visited} 节点, "
                      f"{elapsed:.3f}秒, {nps:.0f} NPS")
            else:
                # 无节点计数的AI（如RandomAI）
                self.results[name].append(0)
                print(f"  测试 {i+1}/{self.num_tests}: 无节点计数")

    def run_all_tests(self):
        """测试所有AI模型"""
        # 定义要测试的AI列表 (类, 名称)
        ai_list = [
            (RandomAI, "RandomAI"),
            (AlphaBetaAI, "AlphaBetaAI"),
            (BetterAlphaBetaAI, "BetterAlphaBetaAI"),
            (IterativeDeepeningMinimaxAI, "IterativeMinimaxAI"),
            (NeuralNetAI, "NeuralNetAI")
        ]
        
        # 依次测试每个AI
        for ai_class, name in ai_list:
            self.test_ai(ai_class, name)

    def generate_chart(self, output_path="nps_analysis.png"):
        """生成柱状图"""
        if not self.results:
            print("没有测试结果可生成图表")
            return
        
        # 计算每个AI的平均NPS
        avg_nps = []
        labels = []
        for name, nps_list in self.results.items():
            labels.append(name)
            avg_nps.append(np.mean(nps_list))
        
        # 创建柱状图
        plt.figure(figsize=(12, 6))
        x = np.arange(len(labels))
        bars = plt.bar(x, avg_nps, color=[ 'green', 'red', 'cyan', 'magenta', 'orange'])
        
        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}',
                    ha='center', va='bottom', rotation=0)
        
        # 设置图表属性
        plt.xlabel('AI Algorithms', fontsize=12)
        plt.ylabel('Nodes Per Second (NPS)', fontsize=12)
        plt.title('Different Algorithms Cost of Searching', fontsize=14)
        plt.xticks(x, labels, fontsize=10,ha='right')
        plt.yscale('log')  # 使用对数刻度，便于查看差异大的数据
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(output_path, dpi=300)
        print(f"图表已保存至 {output_path}")
        plt.show()

if __name__ == "__main__":
    # 初始化测试器（5次测试，搜索深度3）
    tester = NPSTester(num_tests=5, depth=3)
    # 运行所有测试
    tester.run_all_tests()
    # 生成图表
    tester.generate_chart()