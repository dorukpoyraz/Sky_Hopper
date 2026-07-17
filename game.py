import pygame
import random
import copy
import math

pygame.init()
screen = pygame.display.set_mode((700, 500))
pygame.display.set_caption("Sky Hopper - Premium Edition")
clock = pygame.time.Clock()

# --- GLOBAL VARIABLES & STATES ---
cam_x = 0
cam_y = 0
game_started = False  
is_running_sound_playing = False
transition_state = 0
transition_alpha = 0
in_settings = False
in_shop = False
in_level_select = False 

unlocked_levels = 1 

music_volume = 1.0
jump_volume = 0.5  
dragging_music = False
dragging_jump = False
slider_x = 200
slider_width = 300

screen_shake = 0
particles = []
ghost_trails = []

dash_cooldown = 0
dash_duration = 0
is_dashing = False
dash_speed = 12

total_score = 0 
last_click_time = 0  

# --- UI RECTS ---
start_button_rect = pygame.Rect(0, 0, 0, 0)
store_button_rect = pygame.Rect(0, 0, 0, 0)
settings_button_rect = pygame.Rect(0, 0, 0, 0)
exit_button_rect = pygame.Rect(0, 0, 0, 0)       
back_button_rect = pygame.Rect(0, 0, 0, 0)
music_slider_rect = pygame.Rect(0, 0, 0, 0)
jump_slider_rect = pygame.Rect(0, 0, 0, 0)
play_again_btn_rect = pygame.Rect(0, 0, 0, 0)
menu_btn_rect = pygame.Rect(0, 0, 0, 0)
shop_skin_rects = {}
level_rects = {} 

# --- SHOP & SKIN SYSTEM ---
current_skin = "Default"
unlocked_skins = ["Default"] 

skin_prices = {
    "Default": 0,
    "Purple": 10,
    "Blue": 20,
    "Red": 30,
    "Gray": 40,
    "Yellow": 50
}

skins = {
    "Default": "player_sheet2-2.png",
    "Purple": "player_purple.png",
    "Blue": "player_blue.png",
    "Red": "player_red.png",
    "Gray": "player_gray.png",
    "Yellow": "player_yellow.png"
}
skin_colors = {
    "Default": (245, 197, 66),
    "Purple": (150, 50, 200),
    "Blue": (50, 150, 255),
    "Red": (220, 50, 50),
    "Gray": (150, 150, 150),
    "Yellow": (240, 220, 50)
}

try:
    raw_platform = pygame.image.load("platform.png").convert_alpha()
    plat_rect = raw_platform.get_bounding_rect() 
    platform_img = raw_platform.subsurface(plat_rect).copy() 
    
    raw_moving = pygame.image.load("platform2.png").convert()
    raw_moving.set_colorkey((0, 0, 0)) 
    moving_rect = raw_moving.get_bounding_rect() 
    moving_platform_img = raw_moving.subsurface(moving_rect).copy() 
except:
    platform_img = None
    moving_platform_img = None

try:
    door_img = pygame.image.load("door.png").convert_alpha()
    door_img = pygame.transform.scale(door_img, (80, 80)) 
except:
    door_img = None

door_frames = []
try:
    door_sheet = pygame.image.load("spacedoor3.png").convert_alpha()
    content_rect = door_sheet.get_bounding_rect() 
    cropped_sheet = door_sheet.subsurface(content_rect)
    sheet_w, sheet_h = cropped_sheet.get_size()
    frame_w = sheet_w // 4  
    frame_h = sheet_h
    for i in range(4):
        rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
        frame_img = cropped_sheet.subsurface(rect).copy()
        frame_img = pygame.transform.scale(frame_img, (80, 80))
        door_frames.append(frame_img)
except Exception as e:
    pass

target_w = 42
target_h = 46
player = pygame.Rect(60, 260, target_w, target_h)

speed = 5
gravity = 0.8
on_ground = False
platform_speed = 2
can_double_jump = False  
space_pressed = False    
facing_right = True
animation_frame = 0
animation_timer = 0

def get_clean_image(sheet, x, y, width, height, scale_w, scale_h):
    try:
        cropped = sheet.subsurface(pygame.Rect(x, y, width, height)).copy()
        clean_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for px in range(width):
            for py in range(height):
                color = cropped.get_at((px, py))
                if color[0] < 35 and color[1] < 35 and color[2] < 35:
                    clean_surface.set_at((px, py), (0, 0, 0, 0))
                else:
                    clean_surface.set_at((px, py), color)
        return pygame.transform.scale(clean_surface, (scale_w, scale_h))
    except:
        fallback = pygame.Surface((width, height), pygame.SRCALPHA)
        return pygame.transform.scale(fallback, (scale_w, scale_h))

idle_frames = []
run_frames = []
back_frames = []
jump_frames = []
has_sprites = False

def load_player_sprites(skin_name):
    global idle_frames, run_frames, back_frames, jump_frames, has_sprites
    try:
        filename = skins.get(skin_name, "player_sheet2-2.png")
        sprite_sheet = pygame.image.load(filename).convert_alpha()
        sheet_w, sheet_h = sprite_sheet.get_size()
        col_count, row_count = 4, 4
        cell_w, cell_h = sheet_w // col_count, sheet_h // row_count
        crop_x_offset, crop_y_offset = int(cell_w * 0.05), int(cell_h * 0.05)
        crop_w, crop_h = int(cell_w * 0.9), int(cell_h * 0.9)
        
        idle_frames = [get_clean_image(sprite_sheet, i * cell_w + crop_x_offset, 0 * cell_h + crop_y_offset, crop_w, crop_h, target_w, target_h) for i in range(4)]
        
        run_frames = []
        for i in range(4):
            img = get_clean_image(sprite_sheet, i * cell_w + crop_x_offset, 1 * cell_h + crop_y_offset, crop_w, crop_h, target_w, target_h)
            if i == 3: img = pygame.transform.flip(img, True, False)
            run_frames.append(img)
            
        back_frames = list(run_frames) 
        jump_frames = [get_clean_image(sprite_sheet, i * cell_w + crop_x_offset, 2 * cell_h + crop_y_offset, crop_w, crop_h, target_w, target_h) for i in range(4)]
        has_sprites = True
    except Exception as e:
        print(f"Could not load skin {skin_name}: {e}")
        has_sprites = False

load_player_sprites(current_skin)

# --- LEVEL DATA 1-10 ---
level_1_platforms = [pygame.Rect(0, 470, 280, 30), pygame.Rect(420, 470, 280, 30), pygame.Rect(150, 380, 120, 20), pygame.Rect(340, 300, 120, 20), pygame.Rect(520, 220, 120, 20), pygame.Rect(260, 160, 100, 20)]
level_1_coins = [pygame.Rect(200, 345, 16, 16), pygame.Rect(390, 265, 16, 16), pygame.Rect(560, 185, 16, 16), pygame.Rect(300, 130, 16, 16)]
level_1_hazards = [] 

level_2_platforms = [pygame.Rect(0, 470, 150, 30), pygame.Rect(250, 400, 120, 20), pygame.Rect(500, 330, 120, 20), pygame.Rect(220, 250, 100, 20), pygame.Rect(20, 180, 120, 20), pygame.Rect(400, 120, 200, 20), pygame.Rect(425, 470, 375, 30)]
level_2_coins = [pygame.Rect(290, 365, 16, 16), pygame.Rect(540, 295, 16, 16), pygame.Rect(60, 145, 16, 16), pygame.Rect(492, 94, 16, 16)]
level_2_hazards = []

level_3_platforms = [pygame.Rect(0, 470, 155, 30), pygame.Rect(200, 400, 80, 20), pygame.Rect(400, 330, 80, 20), pygame.Rect(600, 250, 80, 20), pygame.Rect(300, 180, 100, 20), pygame.Rect(50, 120, 120, 20), pygame.Rect(300, 470, 300, 30)]
level_3_coins = [pygame.Rect(230, 365, 16, 16), pygame.Rect(430, 295, 16, 16), pygame.Rect(630, 215, 16, 16), pygame.Rect(102, 94, 16, 16)]
level_3_hazards = []

level_4_platforms = [pygame.Rect(0, 470, 150, 30), pygame.Rect(150, 380, 80, 20), pygame.Rect(300, 380, 80, 20), pygame.Rect(550, 300, 80, 20), pygame.Rect(350, 200, 80, 20), pygame.Rect(100, 100, 100, 20), pygame.Rect(354.5, 470, 200, 30)]
level_4_coins = [pygame.Rect(180, 345, 16, 16), pygame.Rect(330, 345, 16, 16), pygame.Rect(580, 265, 16, 16), pygame.Rect(142, 74, 16, 16)]
level_4_hazards = [] 

level_5_platforms = [pygame.Rect(0, 470, 80, 30), pygame.Rect(120, 370, 60, 20), pygame.Rect(30, 270, 60, 20), pygame.Rect(200, 180, 60, 20), pygame.Rect(400, 180, 100, 20), pygame.Rect(600, 100, 80, 20), pygame.Rect(356.5, 295, 73, 20)]
level_5_coins = [pygame.Rect(140, 335, 16, 16), pygame.Rect(50, 235, 16, 16), pygame.Rect(220, 145, 16, 16), pygame.Rect(632, 74, 16, 16)]
level_5_hazards = []

level_6_platforms = [pygame.Rect(0, 470, 173, 16.5), pygame.Rect(150, 400, 50, 20), pygame.Rect(300, 330, 110, 20), pygame.Rect(550, 260, 50, 20), pygame.Rect(300, 160, 119, 20), pygame.Rect(35.4, 100, 95, 20)]
level_6_coins = [pygame.Rect(165, 365, 16, 16), pygame.Rect(565, 225, 16, 16), pygame.Rect(330, 125, 16, 16), pygame.Rect(72, 74, 16, 16)]
level_6_hazards = []

level_7_platforms = [pygame.Rect(0, 470, 120, 30), pygame.Rect(180, 400, 60, 20), pygame.Rect(350, 330, 60, 20), pygame.Rect(520, 260, 60, 20), pygame.Rect(350, 180, 60, 20), pygame.Rect(152.5, 100, 100, 20)]
level_7_coins = [pygame.Rect(202, 365, 16, 16), pygame.Rect(542, 225, 16, 16), pygame.Rect(372, 145, 16, 16), pygame.Rect(192, 76, 16, 16)]
level_7_hazards = []

level_8_platforms = [pygame.Rect(0, 470, 140, 30), pygame.Rect(150, 420, 50, 20), pygame.Rect(300, 350, 50, 20), pygame.Rect(450, 280, 50, 20), pygame.Rect(600, 200, 80, 20), pygame.Rect(350, 130, 60, 20), pygame.Rect(95, 80, 90, 20)]
level_8_coins = [pygame.Rect(167, 385, 16, 16), pygame.Rect(317, 315, 16, 16), pygame.Rect(467, 245, 16, 16), pygame.Rect(132, 56, 16, 16)]
level_8_hazards = []

level_9_platforms = [pygame.Rect(0, 470, 140, 30), pygame.Rect(150, 380, 40, 20), pygame.Rect(300, 380, 40, 20), pygame.Rect(480, 300, 40, 20), pygame.Rect(600, 220, 60, 20), pygame.Rect(400, 150, 40, 20), pygame.Rect(200, 100, 40, 20), pygame.Rect(37, 63.5, 90, 20)]
level_9_coins = [pygame.Rect(162, 345, 16, 16), pygame.Rect(492, 265, 16, 16), pygame.Rect(412, 115, 16, 16), pygame.Rect(72, 36, 16, 16)]
level_9_hazards = []

level_10_platforms = [pygame.Rect(0, 470, 140, 30), pygame.Rect(150, 400, 40, 20), pygame.Rect(350, 350, 40, 20), pygame.Rect(550, 280, 40, 20), pygame.Rect(350, 200, 40, 20), pygame.Rect(485.5, 95, 90, 20)]
level_10_coins = [pygame.Rect(162, 365, 16, 16), pygame.Rect(562, 245, 16, 16), pygame.Rect(522, 64, 16, 16)]
level_10_hazards = []

# --- LEVEL DATA 11-20 ---
level_11_platforms = [pygame.Rect(0, 470, 120, 30), pygame.Rect(200, 400, 60, 20), pygame.Rect(400, 330, 60, 20), pygame.Rect(200, 250, 60, 20), pygame.Rect(400, 170, 60, 20), pygame.Rect(150, 80, 100, 20)]
level_11_coins = [pygame.Rect(220, 360, 16, 16), pygame.Rect(420, 290, 16, 16), pygame.Rect(220, 210, 16, 16), pygame.Rect(190, 40, 16, 16)]
level_11_hazards = []

level_12_platforms = [pygame.Rect(0, 470, 100, 30), pygame.Rect(150, 400, 60, 20), pygame.Rect(350, 350, 80, 20), pygame.Rect(550, 300, 60, 20), pygame.Rect(350, 200, 80, 20), pygame.Rect(150, 100, 100, 20)]
level_12_coins = [pygame.Rect(170, 360, 16, 16), pygame.Rect(570, 260, 16, 16), pygame.Rect(380, 160, 16, 16), pygame.Rect(190, 60, 16, 16)]
level_12_hazards = []

level_13_platforms = [pygame.Rect(0, 470, 100, 30), pygame.Rect(200, 420, 50, 20), pygame.Rect(400, 370, 50, 20), pygame.Rect(600, 320, 50, 20), pygame.Rect(400, 220, 50, 20), pygame.Rect(200, 120, 50, 20), pygame.Rect(50, 60, 80, 20)]
level_13_coins = [pygame.Rect(215, 380, 16, 16), pygame.Rect(615, 280, 16, 16), pygame.Rect(415, 180, 16, 16), pygame.Rect(80, 20, 16, 16)]
level_13_hazards = []

level_14_platforms = [pygame.Rect(0, 470, 100, 30), pygame.Rect(150, 380, 40, 20), pygame.Rect(300, 380, 40, 20), pygame.Rect(450, 300, 40, 20), pygame.Rect(600, 220, 40, 20), pygame.Rect(400, 140, 40, 20), pygame.Rect(200, 90, 80, 20)]
level_14_coins = [pygame.Rect(162, 340, 16, 16), pygame.Rect(462, 260, 16, 16), pygame.Rect(412, 100, 16, 16), pygame.Rect(230, 50, 16, 16)]
level_14_hazards = []

level_15_platforms = [pygame.Rect(0, 470, 80, 30), pygame.Rect(150, 400, 60, 20), pygame.Rect(350, 400, 60, 20), pygame.Rect(550, 350, 60, 20), pygame.Rect(350, 250, 60, 20), pygame.Rect(150, 150, 60, 20), pygame.Rect(350, 80, 80, 20)]
level_15_coins = [pygame.Rect(170, 360, 16, 16), pygame.Rect(570, 310, 16, 16), pygame.Rect(170, 110, 16, 16), pygame.Rect(380, 40, 16, 16)]
level_15_hazards = []

level_16_platforms = [pygame.Rect(0, 470, 80, 30), pygame.Rect(120, 350, 50, 20), pygame.Rect(300, 280, 50, 20), pygame.Rect(500, 210, 50, 20), pygame.Rect(650, 140, 50, 20), pygame.Rect(400, 80, 80, 20)]
level_16_coins = [pygame.Rect(135, 310, 16, 16), pygame.Rect(515, 170, 16, 16), pygame.Rect(430, 40, 16, 16)]
level_16_hazards = []

level_17_platforms = [pygame.Rect(0, 470, 100, 30), pygame.Rect(200, 400, 40, 20), pygame.Rect(400, 350, 40, 20), pygame.Rect(600, 300, 40, 20), pygame.Rect(400, 200, 40, 20), pygame.Rect(200, 100, 40, 20), pygame.Rect(50, 50, 60, 20)]
level_17_coins = [pygame.Rect(212, 360, 16, 16), pygame.Rect(612, 260, 16, 16), pygame.Rect(212, 60, 16, 16), pygame.Rect(70, 10, 16, 16)]
level_17_hazards = []

level_18_platforms = [pygame.Rect(0, 470, 80, 30), pygame.Rect(150, 420, 60, 20), pygame.Rect(350, 360, 60, 20), pygame.Rect(550, 300, 60, 20), pygame.Rect(350, 220, 60, 20), pygame.Rect(150, 140, 60, 20), pygame.Rect(350, 60, 80, 20)]
level_18_coins = [pygame.Rect(170, 380, 16, 16), pygame.Rect(570, 260, 16, 16), pygame.Rect(170, 100, 16, 16), pygame.Rect(380, 20, 16, 16)]
level_18_hazards = []

level_19_platforms = [pygame.Rect(0, 470, 60, 30), pygame.Rect(150, 380, 40, 20), pygame.Rect(350, 300, 40, 20), pygame.Rect(550, 220, 40, 20), pygame.Rect(350, 140, 40, 20), pygame.Rect(150, 80, 80, 20)]
level_19_coins = [pygame.Rect(162, 340, 16, 16), pygame.Rect(562, 180, 16, 16), pygame.Rect(180, 40, 16, 16)]
level_19_hazards = []

level_20_platforms = [pygame.Rect(0, 470, 100, 30), pygame.Rect(150, 400, 50, 20), pygame.Rect(350, 350, 50, 20), pygame.Rect(550, 280, 50, 20), pygame.Rect(350, 200, 50, 20), pygame.Rect(500, 100, 90, 20)]
level_20_coins = [pygame.Rect(167, 360, 16, 16), pygame.Rect(567, 240, 16, 16), pygame.Rect(535, 60, 16, 16)]
level_20_hazards = []

level_moving_data = {
    1: [{'idx': 5, 'dir': 1, 'min': 150, 'max': 450}],
    2: [{'idx': 3, 'dir': 1, 'min': 100, 'max': 400}],
    3: [{'idx': 4, 'dir': 1, 'min': 200, 'max': 500}],
    4: [{'idx': 2, 'dir': 1, 'min': 200, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 500}],
    5: [{'idx': 4, 'dir': 1, 'min': 300, 'max': 500}],
    6: [{'idx': 2, 'dir': 1, 'min': 200, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 150, 'max': 450}],
    7: [{'idx': 1, 'dir': 1, 'min': 150, 'max': 300}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 650}],
    8: [{'idx': 1, 'dir': 1, 'min': 120, 'max': 250}, {'idx': 2, 'dir': -1, 'min': 280, 'max': 420}, {'idx': 3, 'dir': 1, 'min': 420, 'max': 580}],
    9: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 400}, {'idx': 4, 'dir': -1, 'min': 550, 'max': 650}, {'idx': 5, 'dir': 1, 'min': 350, 'max': 500}],
    10: [{'idx': 1, 'dir': 1, 'min': 100, 'max': 250}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 620}, {'idx': 5, 'dir': 1, 'min': 100, 'max': 250}],
    11: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}, {'idx': 4, 'dir': -1, 'min': 300, 'max': 500}],
    12: [{'idx': 2, 'dir': 1, 'min': 200, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 200, 'max': 450}],
    13: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}, {'idx': 4, 'dir': -1, 'min': 300, 'max': 500}],
    14: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 400}, {'idx': 4, 'dir': -1, 'min': 500, 'max': 650}],
    15: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 450}],
    16: [{'idx': 2, 'dir': 1, 'min': 200, 'max': 400}, {'idx': 3, 'dir': -1, 'min': 400, 'max': 600}],
    17: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}, {'idx': 4, 'dir': -1, 'min': 300, 'max': 500}],
    18: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 450}],
    19: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 450}],
    20: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 450}]
}

current_level = 1
platforms = []
coins = []
hazards = []
current_moving_data = []

door_rect = pygame.Rect(0, 0, 80, 80) 

vel_y = 0
score = 0
start_time = 0
best_time = 0 
finish_time = 0
current_time = 0
game_won = False
game_over = False

is_door_opening = False
door_anim_index = 3  
door_anim_timer = 0

class Particle:
    def __init__(self, x, y, color, size=4, spread=2):
        self.x = x
        self.y = y
        self.vx = random.uniform(-spread, spread)
        self.vy = random.uniform(-spread*2, spread*0.5)
        self.life = 255
        self.decay = random.randint(10, 20)
        self.color = color
        self.size = size

def spawn_particles(x, y, color, amount=10, size=4, spread=2):
    for _ in range(amount):
        particles.append(Particle(x, y, color, size, spread))

def load_level(level_num):
    global platforms, coins, hazards, current_moving_data, player, vel_y, door_rect
    global is_door_opening, door_anim_index, cam_x, cam_y, particles, ghost_trails
    
    is_door_opening = False
    door_anim_index = 3  
    particles.clear()
    ghost_trails.clear()
    
    level_data = {
        1: (level_1_platforms, level_1_coins, level_1_hazards), 2: (level_2_platforms, level_2_coins, level_2_hazards),
        3: (level_3_platforms, level_3_coins, level_3_hazards), 4: (level_4_platforms, level_4_coins, level_4_hazards),
        5: (level_5_platforms, level_5_coins, level_5_hazards), 6: (level_6_platforms, level_6_coins, level_6_hazards),
        7: (level_7_platforms, level_7_coins, level_7_hazards), 8: (level_8_platforms, level_8_coins, level_8_hazards),
        9: (level_9_platforms, level_9_coins, level_9_hazards), 10: (level_10_platforms, level_10_coins, level_10_hazards),
        11: (level_11_platforms, level_11_coins, level_11_hazards), 12: (level_12_platforms, level_12_coins, level_12_hazards),
        13: (level_13_platforms, level_13_coins, level_13_hazards), 14: (level_14_platforms, level_14_coins, level_14_hazards),
        15: (level_15_platforms, level_15_coins, level_15_hazards), 16: (level_16_platforms, level_16_coins, level_16_hazards),
        17: (level_17_platforms, level_17_coins, level_17_hazards), 18: (level_18_platforms, level_18_coins, level_18_hazards),
        19: (level_19_platforms, level_19_coins, level_19_hazards), 20: (level_20_platforms, level_20_coins, level_20_hazards)
    }
    platforms = [pygame.Rect(p) for p in level_data[level_num][0]]
    coins = [pygame.Rect(c) for c in level_data[level_num][1]]
    hazards = [pygame.Rect(h) for h in level_data[level_num][2]]
    current_moving_data = copy.deepcopy(level_moving_data[level_num])
    
    player.x = 60
    player.y = 260
    vel_y = 0
    cam_x = player.centerx - 350
    cam_y = player.centery - 250
    
    if level_num == 20:
        door_rect.x = 520  
        door_rect.y = 200  
    elif coins:
        highest_coin = coins[-1] 
        door_rect.centerx = highest_coin.centerx
        door_rect.centery = highest_coin.centery - 4  

def reset_game(starting_level=None):
    global current_level, score, start_time, game_won, game_over
    global is_running_sound_playing
    global transition_state, transition_alpha
    global cam_x, cam_y, screen_shake
    
    if starting_level is not None:
        current_level = starting_level

    score = 0
    start_time = pygame.time.get_ticks()
    game_won = False
    game_over = False
    transition_state = 0
    transition_alpha = 0
    cam_x = 0
    cam_y = 0
    screen_shake = 0
    
    if 'run_sound' in globals() and run_sound: run_sound.stop()
    is_running_sound_playing = False
    if 'game_over_sound' in globals() and game_over_sound: game_over_sound.stop()
    
    load_level(current_level)
    try: pygame.mixer.music.play(-1) 
    except: pass

try:
    font = pygame.font.SysFont("Impact", 30)
    small_font = pygame.font.SysFont("Impact", 20)
    title_font = pygame.font.SysFont("Impact", 60) 
except pygame.error:
    font = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 24)
    title_font = pygame.font.SysFont(None, 60)

shooting_stars = []
nebulas = [
    {"x": 150, "y": 150, "color": (100, 50, 150), "radius": 180},
    {"x": 550, "y": 350, "color": (50, 100, 200), "radius": 220},
    {"x": 350, "y": 100, "color": (150, 50, 100), "radius": 150}
]

stars = [(random.randint(0, 700), random.randint(0, 500), random.randint(1, 3)) for _ in range(60)]
bg_planets = [{"x": 50, "y": 400, "r": 180, "color": (45, 50, 75), "border": 2, "scroll": 0.2}, {"x": 600, "y": 100, "r": 40, "color": (60, 45, 65), "border": 1, "scroll": 0.5}, {"x": 550, "y": 380, "r": 80, "color": (35, 45, 60), "border": 1, "scroll": 0.3}]
bg_orbits = [{"cx": 600, "cy": 100, "rx": 90, "ry": 25, "color": (80, 80, 100, 100), "scroll": 0.5}, {"cx": 550, "cy": 380, "rx": 160, "ry": 40, "color": (70, 75, 90, 80), "scroll": 0.3}]

def draw_cosmic_background(screen, draw_ox=0, draw_oy=0, menu_mode=False):
    screen.fill((15, 18, 36))
    for neb in nebulas:
        scroll_factor = 0.05 if not menu_mode else 0.01
        nx = neb["x"] - (draw_ox * scroll_factor)
        ny = neb["y"] - (draw_oy * scroll_factor)
        neb_surf = pygame.Surface((neb["radius"] * 2, neb["radius"] * 2), pygame.SRCALPHA)
        for r in range(neb["radius"], 0, -12):
            alpha = int((1 - r / neb["radius"]) * 35)
            color_with_alpha = neb["color"] + (alpha,)
            pygame.draw.circle(neb_surf, color_with_alpha, (neb["radius"], neb["radius"]), r)
        screen.blit(neb_surf, (int(nx - neb["radius"]), int(ny - neb["radius"])))

    bg_timer = pygame.time.get_ticks() * 0.005
    for i, star in enumerate(stars):
        scroll_factor = 0.1 if not menu_mode else 0.02
        s_draw_x = int(star[0] - (draw_ox * scroll_factor)) % 700
        s_draw_y = int(star[1] - (draw_oy * scroll_factor)) % 500
        twinkle = math.sin(bg_timer + i) * 0.8
        r = max(1, star[2] + twinkle)
        pygame.draw.circle(screen, (255, 255, 255), (s_draw_x, s_draw_y), int(r))

    if random.random() < 0.008:
        shooting_stars.append({"x": random.randint(-50, 600), "y": random.randint(-50, 200), "speed_x": random.uniform(6, 10), "speed_y": random.uniform(3, 5), "length": random.randint(30, 60), "alpha": 255})

    for s_star in shooting_stars[:]:
        s_star["x"] += s_star["speed_x"]
        s_star["y"] += s_star["speed_y"]
        s_star["alpha"] -= 6 
        if s_star["alpha"] <= 0 or s_star["x"] > 750 or s_star["y"] > 550:
            shooting_stars.remove(s_star)
            continue
        star_surf = pygame.Surface((700, 500), pygame.SRCALPHA)
        pygame.draw.line(star_surf, (255, 255, 200, s_star["alpha"]), (int(s_star["x"]), int(s_star["y"])), (int(s_star["x"] - s_star["length"]), int(s_star["y"] - s_star["length"] * 0.5)), 2)
        screen.blit(star_surf, (0, 0))

    for orbit in bg_orbits:
        scroll_factor = orbit["scroll"] if not menu_mode else 0.02
        o_draw_x = int(orbit["cx"] - (draw_ox * scroll_factor))
        o_draw_y = int(orbit["cy"] - (draw_oy * scroll_factor))
        orbit_surface = pygame.Surface((orbit["rx"] * 2, orbit["ry"] * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(orbit_surface, orbit["color"], (0, 0, orbit["rx"] * 2, orbit["ry"] * 2), 1)
        screen.blit(orbit_surface, (o_draw_x - orbit["rx"], o_draw_y - orbit["ry"]))

    planet_timer = pygame.time.get_ticks() * 0.001
    for i, planet in enumerate(bg_planets):
        scroll_factor = planet["scroll"] if not menu_mode else 0.03
        wave_x = math.sin(planet_timer + i) * 8
        wave_y = math.cos(planet_timer * 0.8 + i) * 6
        p_draw_x = int((planet["x"] + wave_x) - (draw_ox * scroll_factor))
        p_draw_y = int((planet["y"] + wave_y) - (draw_oy * scroll_factor))
        pygame.draw.circle(screen, planet["color"], (p_draw_x, p_draw_y), planet["r"], planet["border"])

try:
    pygame.mixer.init()  
    jump_sound = pygame.mixer.Sound("jumpsound.wav")
    jump_sound.set_volume(jump_volume * 0.3) 
    coin_sound = pygame.mixer.Sound("coinsound.mp3")
    coin_sound.set_volume(0.7)
    door_sound = pygame.mixer.Sound("spacedoor.wav")
    door_sound.set_volume(0.8)
    run_sound = pygame.mixer.Sound("runningmusic.wav")
    run_sound.set_volume(0.85)
    game_over_sound = pygame.mixer.Sound("gameoversound.mp3")
    game_over_sound.set_volume(0.67)
    land_sound = pygame.mixer.Sound("landhit.mp3")
    land_sound.set_volume(0.79)
except pygame.error:
    jump_sound = coin_sound = door_sound = run_sound = game_over_sound = land_sound = None  

try: pygame.mixer.music.load("musicsound.mp3"); pygame.mixer.music.set_volume(music_volume)
except: pass

reset_game(1)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    if not game_started:
        if not in_settings and not in_shop and not in_level_select:
            draw_cosmic_background(screen, menu_mode=True)
            title_text = title_font.render("SKY HOPPER", True, (245, 197, 66))
            screen.blit(title_text, (350 - title_text.get_width() // 2, 60))
            
            total_score_text = font.render(f"TOTAL SCORE: {total_score}", True, (255, 255, 255))
            screen.blit(total_score_text, (350 - total_score_text.get_width() // 2, 125))

            btn_width, btn_height = 240, 50 
            btn_x = 350 - btn_width // 2
            
            start_button_rect = pygame.Rect(btn_x, 170, btn_width, btn_height)
            button_color, text_color = ((60, 180, 120), (255, 255, 255)) if start_button_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (btn_x - 3, 170 - 3, btn_width + 6, btn_height + 6), border_radius=10) 
            pygame.draw.rect(screen, button_color, start_button_rect, border_radius=10)
            btn_text = font.render("START GAME", True, text_color)
            screen.blit(btn_text, (btn_x + (btn_width - btn_text.get_width()) // 2, 170 + (btn_height - btn_text.get_height()) // 2))

            store_button_rect = pygame.Rect(btn_x, 240, btn_width, btn_height)
            st_color, st_text_color = ((150, 50, 200), (255, 255, 255)) if store_button_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (btn_x - 3, 240 - 3, btn_width + 6, btn_height + 6), border_radius=10)
            pygame.draw.rect(screen, st_color, store_button_rect, border_radius=10)
            st_btn_text = font.render("STORE", True, st_text_color)
            screen.blit(st_btn_text, (btn_x + (btn_width - st_btn_text.get_width()) // 2, 240 + (btn_height - st_btn_text.get_height()) // 2))

            settings_button_rect = pygame.Rect(btn_x, 310, btn_width, btn_height)
            s_button_color, s_text_color = ((180, 120, 60), (255, 255, 255)) if settings_button_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (btn_x - 3, 310 - 3, btn_width + 6, btn_height + 6), border_radius=10) 
            pygame.draw.rect(screen, s_button_color, settings_button_rect, border_radius=10)
            s_btn_text = font.render("SETTINGS", True, s_text_color)
            screen.blit(s_btn_text, (btn_x + (btn_width - s_btn_text.get_width()) // 2, 310 + (btn_height - s_btn_text.get_height()) // 2))
            
            exit_button_rect = pygame.Rect(btn_x, 380, btn_width, btn_height)
            e_button_color, e_text_color = ((200, 60, 60), (255, 255, 255)) if exit_button_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (btn_x - 3, 380 - 3, btn_width + 6, btn_height + 6), border_radius=10)
            pygame.draw.rect(screen, e_button_color, exit_button_rect, border_radius=10)
            e_btn_text = font.render("EXIT", True, e_text_color)
            screen.blit(e_btn_text, (btn_x + (btn_width - e_btn_text.get_width()) // 2, 380 + (btn_height - e_btn_text.get_height()) // 2))
            
        elif in_level_select:
            draw_cosmic_background(screen, menu_mode=True)
            box_w, box_h = 620, 440; box_x, box_y = (700 - box_w) // 2, (500 - box_h) // 2
            
            title = title_font.render("SELECT LEVEL", True, (245, 197, 66))
            screen.blit(title, (350 - title.get_width() // 2, box_y - 65))

            pygame.draw.rect(screen, (10, 10, 20), (box_x - 5, box_y - 5, box_w + 10, box_h + 10), border_radius=15)
            pygame.draw.rect(screen, (40, 45, 70), (box_x, box_y, box_w, box_h), border_radius=15)

            sec1_title = small_font.render("SECTION 1: THE NEBULA", True, (255, 255, 255))
            screen.blit(sec1_title, (box_x + 30, box_y + 15))

            sec2_title = small_font.render("SECTION 2: DEEP SPACE", True, (255, 255, 255))
            screen.blit(sec2_title, (box_x + 30, box_y + 185))

            level_coords = {
                # Section 1
                1: (50, 70), 2: (140, 50), 3: (230, 70), 4: (320, 50), 5: (410, 70),
                6: (500, 50), 7: (560, 100), 8: (480, 130), 9: (390, 100), 10: (300, 130),
                
                # Section 2
                11: (50, 240), 12: (140, 220), 13: (230, 240), 14: (320, 220), 15: (410, 240),
                16: (500, 220), 17: (560, 270), 18: (480, 300), 19: (390, 270), 20: (300, 300)
            }

            for i in range(1, 20):
                if i == 10: continue 
                x1, y1 = level_coords[i]
                x2, y2 = level_coords[i+1]
                line_color = (245, 197, 66) if i < unlocked_levels else (100, 100, 120)
                pygame.draw.line(screen, line_color, (box_x + x1, box_y + y1), (box_x + x2, box_y + y2), 6)

            level_rects.clear()
            for i in range(1, 21):
                cx, cy = box_x + level_coords[i][0], box_y + level_coords[i][1]
                rect = pygame.Rect(cx - 26, cy - 26, 52, 52)
                level_rects[i] = rect

                is_hover = rect.collidepoint(mouse_pos)
                is_unlocked = i <= unlocked_levels

                if is_unlocked:
                    if i == unlocked_levels:
                        bg_color = (245, 197, 66) if is_hover else (200, 150, 40)
                        border_color = (255, 255, 255)
                    else:
                        bg_color = (60, 180, 120) if is_hover else (40, 140, 90)
                        border_color = (245, 197, 66)
                else:
                    bg_color = (60, 60, 75)
                    border_color = (40, 40, 50)

                pygame.draw.rect(screen, border_color, (cx - 29, cy - 29, 58, 58), border_radius=29) 
                pygame.draw.rect(screen, bg_color, rect, border_radius=26)

                if is_unlocked:
                    lvl_text = small_font.render(str(i), True, (255, 255, 255))
                    screen.blit(lvl_text, (cx - lvl_text.get_width()//2, cy - lvl_text.get_height()//2))
                else:
                    pygame.draw.rect(screen, (200, 200, 200), (cx - 10, cy - 2, 20, 16), border_radius=3)
                    pygame.draw.circle(screen, (200, 200, 200), (cx, cy - 2), 8, 3)

            back_w, back_h = 160, 50; back_x, back_y = 350 - back_w // 2, box_y + 360
            back_button_rect = pygame.Rect(back_x, back_y, back_w, back_h)
            b_color, b_text_color = ((200, 60, 60), (255, 255, 255)) if back_button_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (back_x - 3, back_y - 3, back_w + 6, back_h + 6), border_radius=10)
            pygame.draw.rect(screen, b_color, back_button_rect, border_radius=10)
            back_text = font.render("BACK", True, b_text_color)
            screen.blit(back_text, (back_x + (back_w - back_text.get_width()) // 2, back_y + (back_h - back_text.get_height()) // 2))

        elif in_settings:
            draw_cosmic_background(screen, menu_mode=True)
            box_w, box_h = 500, 420; box_x, box_y = (700 - box_w) // 2, (500 - box_h) // 2
            pygame.draw.rect(screen, (10, 10, 20), (box_x - 5, box_y - 5, box_w + 10, box_h + 10), border_radius=15)
            pygame.draw.rect(screen, (40, 45, 70), (box_x, box_y, box_w, box_h), border_radius=15)
            settings_title = title_font.render("SETTINGS", True, (245, 197, 66)); screen.blit(settings_title, (350 - settings_title.get_width() // 2, box_y + 20))

            slider_height = 8
            music_text = font.render(f"MUSIC SOUND: %{int(music_volume * 100)}", True, (240, 240, 240)); screen.blit(music_text, (350 - music_text.get_width() // 2, box_y + 110))
            music_slider_y = box_y + 160; music_slider_rect = pygame.Rect(slider_x - 10, music_slider_y - 10, slider_width + 20, slider_height + 20) 
            pygame.draw.rect(screen, (20, 24, 46), (slider_x, music_slider_y, slider_width, slider_height), border_radius=4)
            pygame.draw.rect(screen, (245, 197, 66), (slider_x, music_slider_y, int(slider_width * music_volume), slider_height), border_radius=4)
            pygame.draw.circle(screen, (255, 255, 255), (slider_x + int(slider_width * music_volume), music_slider_y + slider_height // 2), 12)

            jump_text = font.render(f"JUMP SOUND: %{int(jump_volume * 100)}", True, (240, 240, 240)); screen.blit(jump_text, (350 - jump_text.get_width() // 2, box_y + 210))
            jump_slider_y = box_y + 260; jump_slider_rect = pygame.Rect(slider_x - 10, jump_slider_y - 10, slider_width + 20, slider_height + 20) 
            pygame.draw.rect(screen, (20, 24, 46), (slider_x, jump_slider_y, slider_width, slider_height), border_radius=4)
            pygame.draw.rect(screen, (60, 180, 120), (slider_x, jump_slider_y, int(slider_width * jump_volume), slider_height), border_radius=4)
            pygame.draw.circle(screen, (255, 255, 255), (slider_x + int(slider_width * jump_volume), jump_slider_y + slider_height // 2), 12)

            back_w, back_h = 160, 50; back_x, back_y = 350 - back_w // 2, box_y + 340; back_button_rect = pygame.Rect(back_x, back_y, back_w, back_h)
            b_color, b_text_color = ((200, 60, 60), (255, 255, 255)) if back_button_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (back_x - 3, back_y - 3, back_w + 6, back_h + 6), border_radius=10) 
            pygame.draw.rect(screen, b_color, back_button_rect, border_radius=10)
            back_text = font.render("BACK", True, b_text_color); screen.blit(back_text, (back_x + (back_w - back_text.get_width()) // 2, back_y + (back_h - back_text.get_height()) // 2))

        elif in_shop:
            draw_cosmic_background(screen, menu_mode=True)
            box_w, box_h = 500, 420
            box_x, box_y = (700 - box_w) // 2, (500 - box_h) // 2
            pygame.draw.rect(screen, (10, 10, 20), (box_x - 5, box_y - 5, box_w + 10, box_h + 10), border_radius=15)
            pygame.draw.rect(screen, (40, 45, 70), (box_x, box_y, box_w, box_h), border_radius=15)
            
            shop_title = title_font.render("STORE - SKINS", True, (245, 197, 66))
            screen.blit(shop_title, (350 - shop_title.get_width() // 2, box_y + 15))

            coin_text = font.render(f"YOUR COINS: {total_score}", True, (255, 255, 255))
            screen.blit(coin_text, (350 - coin_text.get_width() // 2, box_y + 85))

            start_y = box_y + 130
            shop_skin_rects.clear()
            
            for i, (skin_name, color) in enumerate(skin_colors.items()):
                row = i // 2
                col = i % 2
                s_x = box_x + 35 + col * 220
                s_y = start_y + row * 70
                
                btn_rect = pygame.Rect(s_x, s_y, 200, 50)
                shop_skin_rects[skin_name] = btn_rect
                
                is_hover = btn_rect.collidepoint(mouse_pos)
                bg_color = color if is_hover else (30, 34, 56)
                text_color = (255, 255, 255) if is_hover else color
                
                pygame.draw.rect(screen, color, (s_x - 2, s_y - 2, 204, 54), border_radius=8)
                pygame.draw.rect(screen, bg_color, btn_rect, border_radius=8)
                
                if current_skin == skin_name:
                    pygame.draw.rect(screen, (255, 255, 255), (s_x - 4, s_y - 4, 208, 58), 3, border_radius=10)
                    status_text = "EQUIPPED"
                elif skin_name in unlocked_skins:
                    status_text = "OWNED"
                else:
                    status_text = f"{skin_prices[skin_name]} C"
                    
                skin_name_surf = small_font.render(skin_name, True, text_color)
                screen.blit(skin_name_surf, (s_x + 10, s_y + (50 - skin_name_surf.get_height()) // 2))

                status_surf = small_font.render(status_text, True, text_color)
                screen.blit(status_surf, (s_x + 190 - status_surf.get_width(), s_y + (50 - status_surf.get_height()) // 2))

            back_w, back_h = 160, 50; back_x, back_y = 350 - back_w // 2, box_y + 340
            back_button_rect = pygame.Rect(back_x, back_y, back_w, back_h)
            b_color, b_text_color = ((200, 60, 60), (255, 255, 255)) if back_button_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (back_x - 3, back_y - 3, back_w + 6, back_h + 6), border_radius=10) 
            pygame.draw.rect(screen, b_color, back_button_rect, border_radius=10)
            back_text = font.render("BACK", True, b_text_color)
            screen.blit(back_text, (back_x + (back_w - back_text.get_width()) // 2, back_y + (back_h - back_text.get_height()) // 2))

    else:
        if not game_won and not game_over:
            current_time = (pygame.time.get_ticks() - start_time) / 1000

            for m_data in current_moving_data:
                moving_plat = platforms[m_data['idx']]
                move_amount = platform_speed * m_data['dir']
                moving_plat.x += move_amount
                
                if current_level == 1 and m_data['idx'] == 5:
                    door_rect.x += move_amount
                    if len(coins) > 0:
                        highest_coin = min(coins, key=lambda c: c.y)
                        highest_coin.x += move_amount

                if moving_plat.right > m_data['max'] or moving_plat.left < m_data['min']:
                    m_data['dir'] *= -1
                    moving_plat.x += platform_speed * m_data['dir']
                    continue
                
                for other_idx, other_plat in enumerate(platforms):
                    if other_idx != m_data['idx'] and moving_plat.colliderect(other_plat):
                        m_data['dir'] *= -1
                        moving_plat.x += platform_speed * m_data['dir']
                        break

            is_moving = False
            moving_backwards = False
            keys = pygame.key.get_pressed()
            can_move = not is_door_opening and transition_state == 0
            
            if dash_cooldown > 0: dash_cooldown -= 1
            if dash_duration > 0:
                is_dashing = True
                dash_duration -= 1
                player.x += dash_speed if facing_right else -dash_speed
                vel_y = 0 
      
                if has_sprites and dash_duration % 2 == 0:
                    ghost_trails.append({"x": player.x, "y": player.y, "frame": animation_frame, "facing": facing_right, "alpha": 150})
            else:
                is_dashing = False
            
            if can_move and not is_dashing:
                if keys[pygame.K_LSHIFT] and dash_cooldown == 0:
                    dash_duration = 10
                    dash_cooldown = 40
                    if jump_sound: jump_sound.play() 
                    spawn_particles(player.centerx, player.centery, (100, 200, 255), 15, 6, 4)

                if keys[pygame.K_LEFT]: 
                    player.x -= speed
                    facing_right, is_moving, moving_backwards = False, True, True  
                if keys[pygame.K_RIGHT]: 
                    player.x += speed
                    facing_right, is_moving = True, True
                    
                if keys[pygame.K_SPACE]:
                    if not space_pressed: 
                        if on_ground:
                            vel_y = -15
                            if jump_sound: jump_sound.play()
                            can_double_jump = True
                            spawn_particles(player.centerx, player.bottom, (255, 255, 255), 8) 
                        elif can_double_jump:
                            vel_y = -15
                            if jump_sound: jump_sound.play()
                            can_double_jump = False
                            spawn_particles(player.centerx, player.bottom, (150, 200, 255), 12) 
                        space_pressed = True
                else:
                    space_pressed = False 
            elif not can_move:
                space_pressed = False 
                if not game_over and not game_won and (is_door_opening or transition_state == 1):
                    merkez_farki = door_rect.centerx - player.centerx
                    if abs(merkez_farki) > 2:
                        if merkez_farki > 0: player.x += 2; facing_right = True
                        else: player.x -= 2; facing_right = False
                        is_moving = True 
                    else: player.centerx = door_rect.centerx 
            
            if player.left < 0: player.left = 0
            if player.right > 700: player.right = 700
            if player.top < 0: player.top = 0; vel_y = 0  
            
            if not is_dashing:
                vel_y += gravity
                player.y += vel_y
            
            was_on_ground = on_ground
            on_ground = False
            player_on_moving = False
            moving_dx = 0

            for i, p in enumerate(platforms):
                if player.colliderect(p) and (player.centerx > p.left and player.centerx < p.right):
                    if vel_y > 0 and not is_dashing: 
                        player.bottom = p.top
                        vel_y = 0
                        on_ground = True
                        can_double_jump = True 
                        
                        if not was_on_ground:
                            if land_sound: land_sound.play()
                            screen_shake = 5 
                            spawn_particles(player.centerx, player.bottom, (200, 200, 200), 10, 3, 3) 
                            
                        for m_data in current_moving_data:
                            if i == m_data['idx']:
                                player_on_moving = True
                                moving_dx = platform_speed * m_data['dir']
                    elif vel_y < 0 and not is_dashing: 
                        player.top = p.bottom
                        vel_y = 0

            if player_on_moving: player.x += moving_dx

            if is_moving and on_ground:
                if run_sound and not is_running_sound_playing:
                    run_sound.play(-1); is_running_sound_playing = True
            else:
                if run_sound and is_running_sound_playing:
                    run_sound.stop(); is_running_sound_playing = False

            for coin in coins[:]:
                if player.colliderect(coin):
                    coins.remove(coin)
                    score += 1
                    total_score += 1 
                    if coin_sound: coin_sound.play()
                    spawn_particles(coin.centerx, coin.centery, (245, 197, 66), 15, 5, 4)
                    break

            if player.top > 500:
                game_over = True
                screen_shake = 20 
                finish_time = current_time
                try: pygame.mixer.music.stop()
                except: pass
                if run_sound: run_sound.stop(); is_running_sound_playing = False
                if game_over_sound: game_over_sound.play()

            if len(coins) == 0 and player.colliderect(door_rect) and not is_door_opening and transition_state == 0:
                is_door_opening = True  
                door_anim_index = 3  
                door_anim_timer = 0
                if door_sound: door_sound.play()
            
            if is_door_opening:
                door_anim_timer += 1
                if door_anim_timer > 8: 
                    door_anim_timer = 0
                    if door_anim_index > 0: door_anim_index -= 1
                    else:
                        is_door_opening = False
                        door_anim_index = 3  
                        if current_level < 20: transition_state = 1 
                        elif current_level == 20:
                            game_won = True
                            finish_time = current_time
                            if best_time == 0 or finish_time < best_time: best_time = finish_time
                            try: pygame.mixer.music.stop()
                            except: pass
                            if run_sound: run_sound.stop(); is_running_sound_playing = False

            target_cam_x = player.centerx - 350
            target_cam_y = player.centery - 250
            target_cam_x = max(-80, min(80, target_cam_x))
            target_cam_y = max(-80, min(80, target_cam_y))

            cam_x += (target_cam_x - cam_x) * 0.1
            cam_y += (target_cam_y - cam_y) * 0.1
            
            shake_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
            shake_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
            draw_ox = int(cam_x) + shake_x
            draw_oy = int(cam_y) + shake_y
            
            if screen_shake > 0: screen_shake -= 1

        if game_won or game_over:
            screen.fill((30, 34, 56))
            end_box_width, end_box_height = 400, 380 
            end_box_x, end_box_y = (700 - end_box_width) // 2, (500 - end_box_height) // 2
            
            pygame.draw.rect(screen, (10, 10, 20), (end_box_x - 5, end_box_y - 5, end_box_width + 10, end_box_height + 10), border_radius=15)
            pygame.draw.rect(screen, (20, 24, 46), (end_box_x, end_box_y, end_box_width, end_box_height), border_radius=15)

            win_lose_text = title_font.render('YOU WIN!' if game_won else 'GAME OVER!', True, (120, 255, 160) if game_won else (255, 100, 100))
            screen.blit(win_lose_text, (end_box_x + (end_box_width - win_lose_text.get_width()) // 2, end_box_y + 30))

            texts_to_show = [f'Time: {round(finish_time, 1)}s', f'Session Coins: {score}', f'Best: {round(best_time, 1)}s' if best_time > 0 else 'Best: --']

            text_y_offset = end_box_y + 110
            for info_text in texts_to_show:
                rendered_text = font.render(info_text, True, (240, 240, 240))
                screen.blit(rendered_text, (end_box_x + (end_box_width - rendered_text.get_width()) // 2, text_y_offset))
                text_y_offset += 40
            
            eb_btn_w, eb_btn_h = 220, 50
            play_again_x, play_again_y = end_box_x + (end_box_width - eb_btn_w) // 2, end_box_y + 240
            play_again_btn_rect = pygame.Rect(play_again_x, play_again_y, eb_btn_w, eb_btn_h)
            pa_color, pa_text_color = ((60, 180, 120), (255, 255, 255)) if play_again_btn_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (play_again_x - 3, play_again_y - 3, eb_btn_w + 6, eb_btn_h + 6), border_radius=10)
            pygame.draw.rect(screen, pa_color, play_again_btn_rect, border_radius=10)
            pa_text = font.render("PLAY AGAIN", True, pa_text_color)
            screen.blit(pa_text, (play_again_x + (eb_btn_w - pa_text.get_width()) // 2, play_again_y + (eb_btn_h - pa_text.get_height()) // 2))

            menu_x, menu_y = end_box_x + (end_box_width - eb_btn_w) // 2, end_box_y + 310
            menu_btn_rect = pygame.Rect(menu_x, menu_y, eb_btn_w, eb_btn_h)
            mm_color, mm_text_color = ((180, 120, 60), (255, 255, 255)) if menu_btn_rect.collidepoint(mouse_pos) else ((20, 24, 46), (240, 240, 240))
            pygame.draw.rect(screen, (245, 197, 66), (menu_x - 3, menu_y - 3, eb_btn_w + 6, eb_btn_h + 6), border_radius=10)
            pygame.draw.rect(screen, mm_color, menu_btn_rect, border_radius=10)
            mm_text = font.render("MAIN MENU", True, mm_text_color)
            screen.blit(mm_text, (menu_x + (eb_btn_w - mm_text.get_width()) // 2, menu_y + (eb_btn_h - mm_text.get_height()) // 2))

        else:
            draw_cosmic_background(screen, draw_ox, draw_oy, menu_mode=False)
            
            if door_frames: screen.blit(door_frames[door_anim_index], (door_rect.x - draw_ox, door_rect.y - draw_oy))
            else: pygame.draw.rect(screen, (80, 80, 80), (door_rect.x - draw_ox, door_rect.y - draw_oy, door_rect.width, door_rect.height))

            moving_indices = [m['idx'] for m in current_moving_data]
            for i, p in enumerate(platforms):
                if i in moving_indices:
                    if moving_platform_img: screen.blit(pygame.transform.scale(moving_platform_img, (p.width, p.height)), (p.x - draw_ox, p.y - draw_oy))
                    else: pygame.draw.rect(screen, (140, 90, 140), (p.x - draw_ox, p.y - draw_oy, p.width, p.height))
                else:
                    if platform_img: screen.blit(pygame.transform.scale(platform_img, (p.width, p.height)), (p.x - draw_ox, p.y - draw_oy))
                    else: pygame.draw.rect(screen, (90, 120, 90), (p.x - draw_ox, p.y - draw_oy, p.width, p.height))
                
            for coin in coins:
                pygame.draw.ellipse(screen, (245, 197, 66), (coin.x - draw_ox, coin.y - draw_oy, coin.width, coin.height))
                pygame.draw.ellipse(screen, (255, 255, 150), (coin.x - draw_ox + 4, coin.y - draw_oy + 4, coin.width - 8, coin.height - 8))
            
            for trail in ghost_trails[:]:
                if has_sprites:
                    trail_sprite = run_frames[trail["frame"]] if "run" in str(run_frames) else idle_frames[0]
                    if not trail["facing"]: trail_sprite = pygame.transform.flip(trail_sprite, True, False)
                    trail_surf = trail_sprite.copy()
                    trail_surf.set_alpha(trail["alpha"])
                    screen.blit(trail_surf, (trail["x"] - draw_ox, trail["y"] + 3 - draw_oy))
                trail["alpha"] -= 15
                if trail["alpha"] <= 0: ghost_trails.remove(trail)

            if has_sprites:
                animation_timer += 1
                if not on_ground:
                    current_set = jump_frames
                    if vel_y < -5: animation_frame = 0
                    elif vel_y < 0: animation_frame = 1
                    elif vel_y < 5: animation_frame = 2
                    else: animation_frame = 3
                elif is_moving:
                    current_set = back_frames if moving_backwards else run_frames
                    if animation_timer >= (4 if is_dashing else 6): 
                        animation_frame = (animation_frame + 1) % len(current_set)
                        animation_timer = 0
                else:
                    current_set = idle_frames
                    if animation_timer >= 10: 
                        animation_frame = (animation_frame + 1) % len(current_set)
                        animation_timer = 0
                    else:
                        if animation_frame >= len(current_set): animation_frame = 0
                
                if not is_moving and on_ground: animation_frame = 0
                else: animation_frame = animation_frame % len(current_set)
                    
                active_sprite = current_set[animation_frame]
                if not facing_right: active_sprite = pygame.transform.flip(active_sprite, True, False)
                screen.blit(active_sprite, (player.x - draw_ox, player.y + 3 - draw_oy))
            else:
                pygame.draw.rect(screen, (80, 170, 230), (player.x - draw_ox, player.y - draw_oy, player.width, player.height))
            
            for p in particles[:]:
                p.x += p.vx
                p.y += p.vy
                p.life -= p.decay
                if p.life <= 0:
                    particles.remove(p)
                else:
                    p_color = p.color + (p.life,)
                    surf = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
                    pygame.draw.circle(surf, p_color, (p.size//2, p.size//2), p.size//2)
                    screen.blit(surf, (int(p.x) - draw_ox, int(p.y) - draw_oy))

            top_bar_y = 10
            ui_text_color = (240, 240, 240)
     
            screen.blit(font.render(f'Coins: {score}', True, ui_text_color), (10, top_bar_y))
            screen.blit(font.render(f'Level: {current_level}/20', True, ui_text_color), (160, top_bar_y))
            screen.blit(font.render(f'Time: {round(current_time, 1)}s', True, ui_text_color), (300, top_bar_y))
            if best_time > 0: screen.blit(font.render(f'Best: {round(best_time, 1)}s', True, (245, 197, 66)), (450, top_bar_y))

    if transition_state > 0:
        fade_surface = pygame.Surface((700, 500))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(transition_alpha)
        screen.blit(fade_surface, (0, 0))
        
        if transition_state == 1: 
            transition_alpha += 15
            if transition_alpha >= 255:
                transition_alpha = 255
                transition_state = 2 
                current_level += 1
                
                if current_level > unlocked_levels:
                    unlocked_levels = current_level
                    
                load_level(current_level)
                
        elif transition_state == 2:
            transition_alpha -= 15
            if transition_alpha <= 0:
                transition_alpha = 0
                transition_state = 0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_time = pygame.time.get_ticks()
            if click_time - last_click_time > 150: 
                last_click_time = click_time
                mouse_pos = pygame.mouse.get_pos()
                
                if not game_started:
                    if not in_settings and not in_shop and not in_level_select:
                        if start_button_rect.collidepoint(mouse_pos): 
                            in_level_select = True
                        elif store_button_rect.collidepoint(mouse_pos): in_shop = True
                        elif settings_button_rect.collidepoint(mouse_pos): in_settings = True
                        elif exit_button_rect.collidepoint(mouse_pos): running = False
                    
                    elif in_level_select:
                        if back_button_rect.collidepoint(mouse_pos):
                            in_level_select = False
                        else:
                            for lvl, rect in level_rects.items():
                                if rect.collidepoint(mouse_pos) and lvl <= unlocked_levels:
                                    game_started = True
                                    in_level_select = False
                                    reset_game(lvl)

                    elif in_settings:
                        if back_button_rect.collidepoint(mouse_pos): in_settings = False
                        if music_slider_rect.collidepoint(mouse_pos): dragging_music = True
                        elif jump_slider_rect.collidepoint(mouse_pos): dragging_jump = True
                    elif in_shop:
                        if back_button_rect.collidepoint(mouse_pos): in_shop = False
                        for skin, rect in shop_skin_rects.items():
                            if rect.collidepoint(mouse_pos):
                                if skin in unlocked_skins:
                                    current_skin = skin
                                    load_player_sprites(skin)
                                else:
                                    if total_score >= skin_prices[skin]:
                                        total_score -= skin_prices[skin]
                                        unlocked_skins.append(skin)
                                        current_skin = skin
                                        load_player_sprites(skin)
                                        if coin_sound: coin_sound.play()
                else:
                    if game_won or game_over:
                        if play_again_btn_rect.collidepoint(mouse_pos): reset_game(current_level)
                        elif menu_btn_rect.collidepoint(mouse_pos): game_started = False

        if event.type == pygame.MOUSEBUTTONUP: dragging_music = dragging_jump = False
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            if dragging_music:
                music_volume = max(0.0, min(1.0, (mouse_pos[0] - slider_x) / slider_width))
                try: pygame.mixer.music.set_volume(music_volume)
                except: pass
            if dragging_jump:
                jump_volume = max(0.0, min(1.0, (mouse_pos[0] - slider_x) / slider_width))
                if jump_sound: jump_sound.set_volume(jump_volume * 0.3)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
