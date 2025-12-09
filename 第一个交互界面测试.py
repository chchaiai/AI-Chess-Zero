import pygame
import sys
import os

# 初始化 Pygame
pygame.init()

# 窗口设置
WIDTH, HEIGHT = 800, 750  # 增加高度容纳颜色选择
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Chess Bot")

# 颜色定义
WHITE = (255, 255, 255)
BLUE = (0, 122, 255)
HOVER_BLUE = (0, 80, 200)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
HOVER_GREEN = (0, 150, 0)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)

# 字体设置
font = pygame.font.SysFont("Times New Roman", 24)
title_font = pygame.font.SysFont("Bodoni", 36, bold=True)
small_font = pygame.font.SysFont("Times New Roman", 18)

# 全局状态变量
selected_mode = None
selected_h2m_difficulty = None
selected_white_difficulty = None
selected_black_difficulty = None
selected_human_color = None  # 新增：存储人类选择的颜色

# 按钮类
class Button:
    def __init__(self, x, y, width, height, text, callback=None, color=BLUE, hover_color=HOVER_BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.current_color = self.color
        self.visible = True  # 新增：控制按钮可见性

    def draw(self, screen):
        if self.visible:
            pygame.draw.rect(screen, self.current_color, self.rect, border_radius=8)
            text_surface = font.render(self.text, True, WHITE)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)

    def update(self, mouse_pos, mouse_click):
        if self.visible and self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
            if mouse_click and self.callback:
                self.callback()
        else:
            self.current_color = self.color

# 回调函数
def on_easy():
    global selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty
    if selected_mode == "H2M":
        selected_h2m_difficulty = "Easy"
    elif selected_mode == "M2M":
        if selected_white_difficulty is None:
            selected_white_difficulty = "Easy"
        else:
            selected_black_difficulty = "Easy"

def on_medium():
    global selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty
    if selected_mode == "H2M":
        selected_h2m_difficulty = "Medium"
    elif selected_mode == "M2M":
        if selected_white_difficulty is None:
            selected_white_difficulty = "Medium"
        else:
            selected_black_difficulty = "Medium"

def on_hard():
    global selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty
    if selected_mode == "H2M":
        selected_h2m_difficulty = "Hard"
    elif selected_mode == "M2M":
        if selected_white_difficulty is None:
            selected_white_difficulty = "Hard"
        else:
            selected_black_difficulty = "Hard"

def on_neural():
    global selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty
    if selected_mode == "H2M":
        selected_h2m_difficulty = "Neural"
    elif selected_mode == "M2M":
        if selected_white_difficulty is None:
            selected_white_difficulty = "Neural"
        else:
            selected_black_difficulty = "Neural"






# 新增：选择人类颜色的回调
def on_white():
    global selected_human_color
    selected_human_color = "white"

def on_black():
    global selected_human_color
    selected_human_color = "black"

def on_h2m():
    global selected_mode, selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty, selected_human_color
    selected_mode = "H2M"
    # 重置相关选择
    selected_h2m_difficulty = None
    selected_white_difficulty = None
    selected_black_difficulty = None
    selected_human_color = None


def on_m2m():
    global selected_mode, selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty, selected_human_color
    selected_mode = "M2M"
    # 重置相关选择
    selected_h2m_difficulty = None
    selected_white_difficulty = None
    selected_black_difficulty = None
    selected_human_color = None


# 在on_start函数中确认参数传递正确
def on_start():
    global selected_mode, selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty, selected_human_color
    
    # 验证选择是否完整
    if selected_mode == "H2M":
        if selected_h2m_difficulty :
            print(f"Starting Human vs AI, Difficulty: {selected_h2m_difficulty}")
            # 根据难度设置文件路径
            if selected_h2m_difficulty == "Easy":
                file_path = "./AI-chess/人机对战测试_包含三种难度.py"
            elif selected_h2m_difficulty == "Medium":
                file_path = "./AI-chess/人机对战测试_包含三种难度.py"
            elif selected_h2m_difficulty == "Hard":
                file_path = "./AI-chess/人机对战测试_包含三种难度.py"
            elif selected_h2m_difficulty == "Neural":
                file_path = "./AI-chess/人机对战测试_包含三种难度.py"
            # 传递人类颜色参数
            status = os.system(f'python "{file_path}" --difficulty {selected_h2m_difficulty}')
            if status != 0:
                print("Error running Human vs AI mode")
        else:
            print("Please complete difficulty selection")
            
    elif selected_mode == "M2M" and selected_white_difficulty and selected_black_difficulty:
        print(f"Starting AI vs AI, White difficulty: {selected_white_difficulty}, Black difficulty: {selected_black_difficulty}")
        file_path = "./AI-chess/机机对战测试_包含三种难度.py"
        status = os.system(f'python "{file_path}" --white-difficulty {selected_white_difficulty} --black-difficulty {selected_black_difficulty}')
        if status != 0:
            print("Error running AI vs AI mode")
    else:
        print("Please complete all required selections")

# 创建按钮
easy_btn = Button(50, 300, 180, 60, "Easy", on_easy)
medium_btn = Button(235, 300, 180, 60, "Medium", on_medium)
hard_btn = Button(420, 300, 180, 60, "Hard", on_hard)
h2m_btn = Button(200, 150, 180, 60, "H2M", on_h2m)
m2m_btn = Button(400, 150, 180, 60, "M2M", on_m2m)
start_btn = Button(300, 600, 200, 60, "Start", on_start, GREEN, HOVER_GREEN)
neural_btn = Button(605, 300, 160, 60, "Neural", on_neural)



# 主循环
running = True
while running:
    screen.fill(WHITE)
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = False

    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_click = True

    # 绘制标题
    title_surface = title_font.render("AI Chess Bot", True, BLACK)
    title_rect = title_surface.get_rect(center=(WIDTH//2, 80))
    screen.blit(title_surface, title_rect)

    # 绘制状态文本（仅替换显示文本为英文）
    mode_text = f"Current Mode: {selected_mode if selected_mode else 'Not Selected'}"
    mode_surface = small_font.render(mode_text, True, BLACK)
    screen.blit(mode_surface, (50, 400))

    # 根据当前模式显示不同的状态信息（仅替换显示文本为英文）
    if selected_mode == "H2M":
        difficulty_text = f"Difficulty: {selected_h2m_difficulty if selected_h2m_difficulty else 'Not Selected'}"
        difficulty_surface = small_font.render(difficulty_text, True, BLACK)
        screen.blit(difficulty_surface, (300, 480))
        instruction = small_font.render("Please select difficulty .", True, BLACK)
        screen.blit(instruction, (300, 400))
        
    elif selected_mode == "M2M":
        white_text = f"White AI Difficulty: {selected_white_difficulty if selected_white_difficulty else 'Not Selected'}"
        black_text = f"Black AI Difficulty: {selected_black_difficulty if selected_black_difficulty else 'Not Selected'}"
        white_surface = small_font.render(white_text, True, BLACK)
        black_surface = small_font.render(black_text, True, BLACK)
        screen.blit(white_surface, (290, 440))
        screen.blit(black_surface, (290, 480))
        instruction = small_font.render("Please select White AI difficulty first, then Black AI", True, BLACK)
        screen.blit(instruction, (290, 400))
    else:
        instruction = small_font.render("Please select game mode first", True, BLACK)
        screen.blit(instruction, (400, 400))

    # 绘制并更新按钮
    easy_btn.draw(screen)
    easy_btn.update(mouse_pos, mouse_click)
    
    medium_btn.draw(screen)
    medium_btn.update(mouse_pos, mouse_click)
    
    hard_btn.draw(screen)
    hard_btn.update(mouse_pos, mouse_click)
    
    h2m_btn.draw(screen)
    h2m_btn.update(mouse_pos, mouse_click)
    
    m2m_btn.draw(screen)
    m2m_btn.update(mouse_pos, mouse_click)

    start_btn.draw(screen)
    start_btn.update(mouse_pos, mouse_click)

    neural_btn.draw(screen)
    neural_btn.update(mouse_pos, mouse_click)



    # 更新屏幕
    pygame.display.flip()

# 退出
pygame.quit()
sys.exit()