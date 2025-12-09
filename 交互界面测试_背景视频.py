import pygame
import sys
import os
import cv2
import numpy as np

# 初始化 Pygame
pygame.init()

# 窗口设置
WIDTH, HEIGHT = 800, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Chess Bot - Premium Edition")

# --- 颜色定义 (高级配色) ---
# 基础色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TRANSPARENT_BLACK = (0, 0, 0, 180)  # 半透明遮罩
PANEL_BG = (30, 35, 40, 210)        # 卡片背景 (深蓝灰 + 透明)

# 主题色
THEME_CYAN = (0, 200, 255)          # 科技蓝 (用于模式)
THEME_AMBER = (255, 180, 50)        # 琥珀金 (用于难度)
THEME_RED = (255, 80, 80)           # 警告/重置
THEME_GREEN = (0, 230, 100)         # 启动

# 文本色
TEXT_PRIMARY = (240, 240, 240)
TEXT_SECONDARY = (160, 170, 180)

# --- 字体设置 ---
def get_font(size, bold=False):
    # 尝试加载系统现代字体，如果不行回退到默认
    font_name = "Segoe UI" if os.name == 'nt' else "Helvetica"
    try:
        return pygame.font.SysFont(font_name, size, bold=bold)
    except:
        return pygame.font.SysFont("Arial", size, bold=bold)

title_font = get_font(48, bold=True)
subtitle_font = get_font(24)
btn_font = get_font(20, bold=True)
status_font = get_font(18)

# --- 全局状态变量 ---
selected_mode = None
selected_h2m_difficulty = None
selected_white_difficulty = None
selected_black_difficulty = None
game_started = False # 新增：标记游戏是否正在进行
game_process = None  # 新增：用于存储游戏进程对象
# 状态提示文本
status_message = "Welcome via AI Chess System"

# --- 视频背景类 (保持原逻辑不变) ---
class VideoBackground:
    def __init__(self, video_path, target_size=(WIDTH, HEIGHT)):
        self.cap = None
        self.valid = False
        self.last_frame_time = pygame.time.get_ticks()
        self.target_size = target_size
        self.fps = 30
        self.frame_delay = 1000 / self.fps
        self.current_frame = None
        
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"Warning: Could not open video {video_path}")
            return
            
        self.valid = True
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0 or np.isnan(self.fps):
            self.fps = 30
        self.frame_delay = 1000 / self.fps
        self._read_first_frame()
        
    def _read_first_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self.target_size)
            self.current_frame = pygame.surfarray.make_surface(frame.transpose((1, 0, 2)))
        else:
            self.valid = False
            
    def get_frame(self):
        if not self.valid:
            return self.current_frame
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_time < self.frame_delay:
            return self.current_frame
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret: return self.current_frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
        frame = np.ascontiguousarray(frame)
        self.current_frame = pygame.surfarray.make_surface(frame.transpose((1, 0, 2)))
        self.last_frame_time = current_time
        return self.current_frame
    
    def stop(self):
        if self.valid and self.cap is not None:
            self.cap.release()

# 初始化视频
video_bg = VideoBackground("./AI-chess/video5.mp4")

# --- 高级按钮类 ---
class ModernButton:
    def __init__(self, x, y, width, height, text, callback, 
                 base_color=THEME_CYAN, group="default", check_active_func=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.base_color = base_color
        self.hovered = False
        self.group = group
        self.check_active_func = check_active_func # 函数：返回True如果该按钮应该处于选中状态

    def draw(self, surface):
        # 1. 确定状态颜色
        is_active = False
        if self.check_active_func:
            is_active = self.check_active_func()

        # 颜色计算
        if is_active:
            bg_color = self.base_color # 选中时完全显示主题色
            border_color = WHITE
            text_color = BLACK if sum(self.base_color) > 400 else WHITE
            alpha = 255
        elif self.hovered:
            bg_color = (self.base_color[0], self.base_color[1], self.base_color[2])
            border_color = self.base_color
            text_color = WHITE
            alpha = 150 # 悬停半透明
        else:
            bg_color = (40, 40, 40) # 默认深灰
            border_color = (80, 80, 80)
            text_color = (180, 180, 180)
            alpha = 200

        # 2. 绘制背景 (支持透明度)
        btn_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # 填充背景
        if is_active or self.hovered:
            r, g, b = bg_color
            pygame.draw.rect(btn_surface, (r, g, b, alpha), btn_surface.get_rect(), border_radius=10)
        else:
            # 默认状态：只有边框和淡背景
            pygame.draw.rect(btn_surface, (30, 30, 30, 180), btn_surface.get_rect(), border_radius=10)

        # 绘制边框
        if is_active:
            pygame.draw.rect(btn_surface, border_color, btn_surface.get_rect(), 2, border_radius=10)
        elif self.hovered:
            pygame.draw.rect(btn_surface, border_color, btn_surface.get_rect(), 1, border_radius=10)
        else:
            pygame.draw.rect(btn_surface, border_color, btn_surface.get_rect(), 1, border_radius=10)

        surface.blit(btn_surface, self.rect)

        # 3. 绘制文字
        txt_surf = btn_font.render(self.text, True, text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def update(self, mouse_pos, clicked):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and clicked and self.callback:
            self.callback()

# --- 逻辑回调函数 (更新状态文本) ---

def on_h2m():
    global selected_mode, status_message, selected_h2m_difficulty
    selected_mode = "H2M"
    selected_h2m_difficulty = None 
    status_message = "Mode: Human vs AI. Select Difficulty."

def on_m2m():
    global selected_mode, status_message, selected_white_difficulty, selected_black_difficulty
    selected_mode = "M2M"
    selected_white_difficulty = None
    selected_black_difficulty = None
    status_message = "Mode: AI vs AI. Select White AI Difficulty."

def set_difficulty(level):
    global selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty, status_message
    
    if selected_mode == "H2M":
        selected_h2m_difficulty = level
        status_message = f"Ready: Human vs AI ({level})"
    elif selected_mode == "M2M":
        if selected_white_difficulty is None:
            selected_white_difficulty = level
            status_message = f"White AI: {level}. Select Black AI Difficulty."
        else:
            selected_black_difficulty = level
            status_message = f"Ready: AI ({selected_white_difficulty}) vs AI ({level})"
    else:
        status_message = "Please select a Game Mode first."

def on_reset():
    global selected_mode, selected_h2m_difficulty, selected_white_difficulty, selected_black_difficulty, status_message
    selected_mode = None
    selected_h2m_difficulty = None
    selected_white_difficulty = None
    selected_black_difficulty = None
    status_message = "System Reset. Select Mode."

def on_start():
    global game_started, game_process, status_message
    can_start = False
    cmd = ""
    
    if selected_mode == "H2M" and selected_h2m_difficulty:
        can_start = True
        cmd = f'python "./AI-chess/人机对战测试_包含三种难度.py" --difficulty {selected_h2m_difficulty}'
    elif selected_mode == "M2M" and selected_white_difficulty and selected_black_difficulty:
        can_start = True
        cmd = f'python "./AI-chess/机机对战测试_包含三种难度.py" --white-difficulty {selected_white_difficulty} --black-difficulty {selected_black_difficulty}'
    
    if can_start:
        print(f"Executing: {cmd}")
        video_bg.stop() # 停止当前视频播放
        # 使用 subprocess.Popen 启动游戏，非阻塞
        import subprocess
        game_process = subprocess.Popen(cmd, shell=True)
        game_started = True
        status_message = "Game is running..."
    else:
        status_message = "Cannot Start: Setup incomplete."

# --- UI 布局构建 ---
center_x = WIDTH // 2
panel_w, panel_h = 500, 550
panel_x, panel_y = (WIDTH - panel_w) // 2, (HEIGHT - panel_h) // 2 + 30

buttons = []

# 1. 模式选择按钮 (Row 1)
btn_y_start = panel_y + 80
buttons.append(ModernButton(panel_x + 50, btn_y_start, 190, 50, "Human vs AI", on_h2m, THEME_CYAN, 
                            check_active_func=lambda: selected_mode == "H2M"))
buttons.append(ModernButton(panel_x + 260, btn_y_start, 190, 50, "AI vs AI", on_m2m, THEME_CYAN, 
                            check_active_func=lambda: selected_mode == "M2M"))

# 2. 难度选择按钮 (Grid)
diff_y_start = btn_y_start + 100
diff_levels = ["Easy", "Medium", "Hard", "Neural"]
for i, level in enumerate(diff_levels):
    # 简单的网格布局计算
    bx = panel_x + 50 + (i % 2) * 210
    by = diff_y_start + (i // 2) * 70
    
    # 检查函数：稍微复杂一点，需要根据当前模式判断是否高亮
    def check_diff_active(l=level):
        if selected_mode == "H2M":
            return selected_h2m_difficulty == l
        elif selected_mode == "M2M":
            # 在M2M模式下，如果在选白方，暂不高亮；如果选黑方，也许可以展示逻辑
            # 这里简化逻辑：如果是已选的白方或黑方，则高亮
            return l == selected_white_difficulty or l == selected_black_difficulty
        return False

    buttons.append(ModernButton(bx, by, 190, 50, level, lambda l=level: set_difficulty(l), THEME_AMBER, 
                                check_active_func=check_diff_active))

# 3. 功能按钮 (Reset & Start)
action_y = diff_y_start + 160
buttons.append(ModernButton(panel_x + 50, action_y, 120, 50, "Reset", on_reset, THEME_RED))

# Start按钮比较特殊，需要检查是否Ready
def check_start_ready():
    if selected_mode == "H2M" and selected_h2m_difficulty: return True
    if selected_mode == "M2M" and selected_white_difficulty and selected_black_difficulty: return True
    return False

start_btn = ModernButton(panel_x + 190, action_y, 260, 50, "START GAME", on_start, THEME_GREEN)
# 覆写 Start 按钮的绘制逻辑来做禁用态
original_draw = start_btn.draw
def draw_start_btn(surface):
    if check_start_ready():
        start_btn.base_color = THEME_GREEN
        start_btn.text = "START GAME"
    else:
        start_btn.base_color = (100, 100, 100) # Disabled gray
        start_btn.text = "LOCKED"
    original_draw(surface)
start_btn.draw = draw_start_btn
buttons.append(start_btn)


# --- 主绘制函数 ---
def draw_ui(screen):
    # 1. 绘制毛玻璃面板
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, PANEL_BG, panel_surf.get_rect(), border_radius=20)
    # 添加一个细边框
    pygame.draw.rect(panel_surf, (255, 255, 255, 30), panel_surf.get_rect(), 1, border_radius=20)
    screen.blit(panel_surf, (panel_x, panel_y))

    # 2. 绘制标题 (带阴影)
    title_text = "AI CHESS ZERO"
    shadow_surf = title_font.render(title_text, True, (0, 0, 0))
    main_surf = title_font.render(title_text, True, WHITE)
    screen.blit(shadow_surf, (center_x - main_surf.get_width()//2 + 2, 52))
    screen.blit(main_surf, (center_x - main_surf.get_width()//2, 50))

    # 3. 绘制分段标题
    mode_label = subtitle_font.render("SELECT MODE", True, TEXT_SECONDARY)
    screen.blit(mode_label, (panel_x + 50, panel_y + 40))

    diff_label = subtitle_font.render("SELECT DIFFICULTY", True, TEXT_SECONDARY)
    screen.blit(diff_label, (panel_x + 50, panel_y + 145))

    # 4. 绘制状态栏
    status_bg = pygame.Surface((panel_w - 40, 40), pygame.SRCALPHA)
    pygame.draw.rect(status_bg, (0, 0, 0, 100), status_bg.get_rect(), border_radius=5)
    screen.blit(status_bg, (panel_x + 20, panel_y + panel_h - 60))
    
    status_surf = status_font.render(status_message, True, THEME_CYAN)
    status_rect = status_surf.get_rect(center=(panel_x + panel_w // 2, panel_y + panel_h - 40))
    screen.blit(status_surf, status_rect)

# --- 主循环 ---
running = True
clock = pygame.time.Clock()

while running:
    clock.tick(60)
    
    # 检查游戏进程是否结束
    if game_started and game_process is not None:
        return_code = game_process.poll()
        if return_code is not None: # 游戏进程已结束
            print(f"Game finished with return code: {return_code}")
            game_started = False
            game_process = None
            # *** 关键步骤：重启视频背景 ***
            video_bg = VideoBackground("./AI-chess/video5.mp4") # 重新初始化
            status_message = "Game over. Select a new game or mode."

    # 原有的背景绘制、事件处理、UI绘制逻辑保持不变
    video_frame = video_bg.get_frame()
    # 1. 背景绘制
    video_frame = video_bg.get_frame()
    if video_frame is not None:
        screen.blit(pygame.transform.scale(video_frame, (WIDTH, HEIGHT)), (0, 0))
    else:
        screen.fill(BLACK)
    
    # 2. 绘制全屏遮罩 (让背景变暗，突出UI)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100)) # 整体压暗
    screen.blit(overlay, (0,0))

    # 3. 事件处理
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_click = True

    # 4. UI 绘制与更新
    draw_ui(screen)
    
    for btn in buttons:
        btn.update(mouse_pos, mouse_click)
        btn.draw(screen)

    pygame.display.flip()

video_bg.stop()
pygame.quit()
sys.exit()