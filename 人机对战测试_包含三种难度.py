import argparse
from ast import arg
from PyQt5 import QtGui, QtSvg
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import (QApplication, QWidget, QMessageBox, 
                             QLabel, QVBoxLayout, QInputDialog)  # 新增QInputDialog
import sys
import chess, chess.svg
import traceback
from NeuralNetAI import NeuralNetAI

# 假设这些AI和游戏类的实现正确（原代码已有）
from IterativeDeepeningMinimaxAI import IterativeDeepeningMinimaxAI
from RandomAI import RandomAI
from HumanPlayer import HumanPlayer
from AlphaBetaAI import AlphaBetaAI
from BetterAlphaBetaAI import BetterAlphaBetaAI
from ChessGame import ChessGame
import random


class ChessGui_h2m(QWidget):
    def __init__(self, app, human_player, ai_player):
        super().__init__()
        self.app = app
        self.human_player = human_player
        self.ai_player = ai_player
        self.game = ChessGame(human_player, ai_player)

        # 棋盘相关配置
        self.board_size = 800
        self.square_size = self.board_size // 8

        # 初始化布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 30)

        # 初始化SVG控件（启用抗锯齿，优化渲染）
        self.svgWidget = QtSvg.QSvgWidget()
        self.svgWidget.setFixedSize(self.board_size, self.board_size)
        self.layout.addWidget(self.svgWidget)

        # 状态提示标签
        self.status_label = QLabel("游戏开始：人类（白棋）先走", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; color: #333;")
        self.layout.addWidget(self.status_label)

        # 主窗口配置
        self.setGeometry(900, 400, self.board_size, self.board_size + 50)
        if args.difficulty == "Easy":
            self.setWindowTitle("AI-CHESS(EASY MODE)")
        elif args.difficulty == "Medium":
            self.setWindowTitle("AI-CHESS(MEDIUM MODE)")
        elif args.difficulty == "Hard":
            self.setWindowTitle("AI-CHESS(HARD MODE)")
        elif args.difficulty == "Neural":
            self.setWindowTitle("AI-CHESS(NEURAL MODE)")

        # 关键状态变量
        self.human_is_white = human_player.color if hasattr(human_player, 'color') else True
        self.selected_square = None
        self.legal_moves_for_selected = []
        self.is_ai_thinking = False
        self.ai_thread = None

        # 显示初始棋盘
        self.display_board()

    def start(self):
        self.show()

    def display_board(self, last_move=None):
        """生成SVG棋盘，强制实时渲染可走位置的X符号"""
        highlighted_squares = []  # 可走位置（X符号标记）
        check_square = None       # 选中棋子（红色标记）

        # 1. 处理选中棋子和可走位置
        if self.selected_square is not None:
            file, rank = self.selected_square
            selected_chess_square = chess.square(file, rank)
            check_square = selected_chess_square  # 选中棋子用红色标记（check参数）
            highlighted_squares = self.legal_moves_for_selected  # 可走位置用X标记（squares参数）

        # 2. 生成SVG（关键优化：明确区分选中棋子和可走位置，强制渲染X符号）
        svgboard = chess.svg.board(
            self.game.board,
            lastmove=last_move,          # 上一步走法（灰色高亮）
            squares=highlighted_squares, # 可走位置（X符号）
            check=check_square,          # 选中棋子（红色高亮）
            size=self.board_size,
            colors={
                'square light': '#f0d9b5',
                'square dark': '#b58863',
                'check': '#ffcccc'       # 选中棋子的红色高亮（浅红，不刺眼）
            }
        )

        # 3. 强制刷新SVG（解决渲染延迟问题）
        svgbytes = QByteArray(svgboard.encode('utf-8'))
        self.svgWidget.load(svgbytes)
        self.svgWidget.update()  # 强制控件刷新
        self.app.processEvents() # 处理未完成的GUI事件，确保实时显示

    def mousePressEvent(self, event):
        """监听鼠标点击事件"""
        if (self.game.board.turn != self.human_is_white) or self.is_ai_thinking:
            return

        x = event.x()
        y = event.y()
        if y >= self.board_size:
            return
        file = x // self.square_size
        rank = 7 - (y // self.square_size)
        square = (file, rank)

        if self.selected_square is None:
            self.select_piece(square)
        else:
            self.try_move(square)

    def select_piece(self, square):
        """选中棋子，实时计算并显示可走位置"""
        # 清空之前的状态（避免残留）
        self.selected_square = None
        self.legal_moves_for_selected = []

        file, rank = square
        chess_square = chess.square(file, rank)
        piece = self.game.board.piece_at(chess_square)

        if piece is not None:
            is_white_piece = (piece.color == chess.WHITE)
            if is_white_piece == self.human_is_white:
                self.selected_square = square
                # 计算当前棋子的所有合法走法（目标格子）
                self.legal_moves_for_selected = [
                    move.to_square
                    for move in self.game.board.legal_moves
                    if move.from_square == chess_square
                ]
                self.status_label.setText(f"选中棋子：{piece.symbol()} 在 {self.square_to_uci(square)}")
                print(f"选中棋子：{piece.symbol()} 在 {self.square_to_uci(square)}")
                print(f"合法走法：{[chess.square_name(m) for m in self.legal_moves_for_selected]}")
            else:
                self.status_label.setText("选中失败：这不是你的棋子！")
                QMessageBox.warning(self, "选中失败", "这不是你的棋子！")
        else:
            self.status_label.setText("选中失败：该格子上没有棋子！")
            QMessageBox.warning(self, "选中失败", "该格子上没有棋子！")

        # 强制刷新棋盘（关键：确保选中时立即显示X符号）
        self.display_board()

    def try_move(self, target_square):
        """尝试走棋，处理兵升变逻辑"""
        start_uci = self.square_to_uci(self.selected_square)
        target_uci = self.square_to_uci(target_square)
        move_uci = start_uci + target_uci

        # 关键步骤1：判断是否是兵的升变走法
        start_file, start_rank = self.selected_square
        start_chess_square = chess.square(start_file, start_rank)
        piece = self.game.board.piece_at(start_chess_square)
        is_pawn_promotion = False

        if piece and piece.symbol() in ['P', 'p']:  # 是兵
            target_file, target_rank = target_square
            # 白兵（P）到达8线（rank=7）、黑兵（p）到达1线（rank=0）→ 需要升变
            if (piece.color == chess.WHITE and target_rank == 7) or (piece.color == chess.BLACK and target_rank == 0):
                is_pawn_promotion = True

        # 关键步骤2：如果是升变，让人类选择升变棋子
        if is_pawn_promotion:
            # 弹出选择框：后（最强）、车、象、马
            promotion_piece, ok = QInputDialog.getItem(
                self,
                "兵升变",
                "选择要升变的棋子（默认后）：",
                ["后（Q）", "车（R）", "象（B）", "马（N）"],
                current=0,  # 默认选中“后”
                editable=False
            )
            if not ok:  # 用户取消选择，取消走棋
                self.status_label.setText("取消升变，走棋无效")
                self.selected_square = None
                self.legal_moves_for_selected = []
                self.display_board()
                return

            # 解析选择的棋子，生成UCI后缀（q=后，r=车，b=象，n=马）
            promotion_suffix = promotion_piece[-2]  # 取括号内的字符（Q/R/B/N）
            move_uci += promotion_suffix.lower()  # UCI后缀用小写（如e7e8q）

        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.game.board.legal_moves:
                # 执行人类走法（包含升变）
                self.game.board.push(move)
                if is_pawn_promotion:
                    self.status_label.setText(f"人类走法：{move_uci}（兵升变为{promotion_piece.split('（')[0]}）→ AI思考中...")
                    print(f"人类走法：{move_uci}（兵升变为{promotion_piece.split('（')[0]}）")
                else:
                    self.status_label.setText(f"人类走法：{move_uci} → AI思考中...")
                    print(f"人类走法：{move_uci}")
                
                # 清空选中状态和可走位置标记
                self.selected_square = None
                self.legal_moves_for_selected = []
                self.display_board(last_move=move)

                # 检查游戏是否结束
                if self.game.exit_game():
                    self.show_game_result()
                    return

                # 触发AI走棋
                self.is_ai_thinking = True
                QTimer.singleShot(500, self.ai_move)
            else:
                self.status_label.setText(f"走法无效：{move_uci}")
                QMessageBox.warning(self, "走法无效", f"从 {start_uci} 到 {target_uci} 是无效走法！")
                # 清空选中状态（但保留走法无效的提示）
                self.selected_square = None
                self.legal_moves_for_selected = []
                self.display_board()
        except ValueError:
            self.status_label.setText(f"格式错误：{move_uci}")
            QMessageBox.warning(self, "格式错误", f"走法 {move_uci} 格式无效！")
            self.selected_square = None
            self.legal_moves_for_selected = []
            self.display_board()

    def ai_move(self):
        """AI走棋（持有线程引用，避免被销毁）"""
        if self.game.exit_game():
            self.show_game_result()
            return

        # 确保之前的线程已结束
        if self.ai_thread is not None and self.ai_thread.isRunning():
            self.ai_thread.quit()
            self.ai_thread.wait()

        # 创建AI线程并持有引用
        self.ai_thread = AIThinkingThread(self.ai_player, self.game.board)
        self.ai_thread.finished.connect(self.clear_ai_thread)
        self.ai_thread.finished_signal.connect(self.on_ai_move_finished)
        self.ai_thread.start()

    def on_ai_move_finished(self, ai_move):
        """AI走棋完成回调，校验并补全AI的兵升变"""
        self.is_ai_thinking = False
        if not ai_move:
            self.status_label.setText("AI无法生成走法 → 人类回合")
            QMessageBox.warning(self, "AI错误", "AI无法生成有效走法，请你继续走棋！")
            return

        # 关键步骤：校验AI的走法是否需要升变（如果AI未处理，自动升变为后）
        ai_move_uci = ai_move.uci()
        start_square = ai_move.from_square
        target_square = ai_move.to_square
        piece = self.game.board.piece_at(start_square)
        need_promotion = False

        if piece and piece.symbol() in ['P', 'p']:  # AI的走法是兵
            target_rank = chess.square_rank(target_square)
            # 白兵（AI若为白）到8线，黑兵（AI若为黑）到1线 → 需要升变
            if (piece.color == chess.WHITE and target_rank == 7) or (piece.color == chess.BLACK and target_rank == 0):
                # 检查AI的走法是否包含升变后缀（q/r/b/n），没有则补全为后（q）
                if len(ai_move_uci) == 4:  # 标准走法是4个字符（如e7e8），无升变后缀
                    ai_move_uci += 'q'  # 自动升变为后（AI最优选择）
                    ai_move = chess.Move.from_uci(ai_move_uci)
                    need_promotion = True

        # 执行AI走法（包含补全的升变）
        self.game.board.push(ai_move)
        if need_promotion:
            self.status_label.setText(f"AI走法：{ai_move_uci}（兵升变为后）→ 人类回合")
            print(f"AI走法：{ai_move_uci}（兵升变为后）")
        else:
            self.status_label.setText(f"AI走法：{ai_move_uci} → 人类回合")
            print(f"AI走法：{ai_move_uci}")
        
        self.display_board(last_move=ai_move)

        # 检查游戏是否结束
        if self.game.exit_game():
            self.show_game_result()

    def clear_ai_thread(self):
        """线程结束后清理引用"""
        self.ai_thread = None

    def square_to_uci(self, square):
        """棋盘坐标→UCI格式"""
        file, rank = square
        file_char = chr(ord('a') + file)
        rank_num = rank + 1
        return f"{file_char}{rank_num}"

    def show_game_result(self):
        """显示游戏结果"""
        result = self.game.board.result()
        if result == "1-0":
            text = "白棋胜利！"
        elif result == "0-1":
            text = "黑棋胜利！"
        else:
            text = "和棋！"
        self.status_label.setText(f"游戏结束：{text}")
        QMessageBox.information(self, "游戏结束", text)
        QTimer.singleShot(2000, self.app.quit)

    def __del__(self):
        """析构函数：确保线程结束后再销毁对象"""
        if self.ai_thread is not None and self.ai_thread.isRunning():
            self.ai_thread.quit()
            self.ai_thread.wait()


class AIThinkingThread(QThread):
    """AI思考子线程"""
    finished_signal = pyqtSignal(chess.Move)

    def __init__(self, ai_player, board):
        super().__init__()
        self.ai_player = ai_player
        self.board = board.copy()
        self.setTerminationEnabled(True)  # 允许线程被终止

    def run(self):
        """线程执行：计算AI走法"""
        try:
            print(f"AI线程启动：当前回合{self.board.turn}（True=白，False=黑）")
            ai_move = self.ai_player.choose_move(self.board)
            print(f"AI计算完成：{ai_move.uci() if ai_move else '无有效走法'}")
            self.finished_signal.emit(ai_move)
        except Exception as e:
            print("\n=== AI计算异常详情 ===")
            traceback.print_exc()
            print("======================\n")
            self.finished_signal.emit(None)


def parse_arguments():
        parser = argparse.ArgumentParser(description="Chess Game Parameters")
        parser.add_argument("--difficulty", type=str, default="Easy",choices=["Easy", "Medium", "Hard","Neural"], help='Game difficulty level')
        return parser.parse_args()

if __name__ == "__main__":
    random.seed(1)
    args = parse_arguments()
    # 1. 创建QApplication
    app = QApplication(sys.argv)

    # 2. 配置人机对战
    human_player = HumanPlayer()
    human_player.color = True  # 人类=白棋
    if args.difficulty == "Easy":
        ai_player = RandomAI()  # AI=黑棋
    elif args.difficulty == "Medium":
        ai_player = IterativeDeepeningMinimaxAI(2, False)  # AI=黑棋
    elif args.difficulty == "Hard":
        ai_player = BetterAlphaBetaAI(3,False)  # AI=黑棋
    elif args.difficulty == "Neural":
        print("正在初始化神经网络AI")
        ai_player = NeuralNetAI(2, False)  # AI=黑棋
    # 3. 创建GUI实例
    gui = ChessGui_h2m(app, human_player, ai_player)
    gui.start()

    # 4. 启动事件循环
    sys.exit(app.exec_())