# -*- coding: utf-8 -*-
# Python 3.12 (pygame kurulu) ile çalıştır:
# C:\Users\PC\AppData\Local\Python\pythoncore-3.12-64\python.exe game.py
import pygame
import random
import copy
import math
import json
import os

pygame.init()
GAME_WIDTH = 700
GAME_HEIGHT = 500
screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
display_surface = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Sky Hopper - Premium Edition")
clock = pygame.time.Clock()
fullscreen = False

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
in_leaderboard = False
in_achievements = False

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

has_jetpack = False
max_jetpack_fuel = 120
jetpack_fuel = max_jetpack_fuel

# --- PAUSE ---
game_paused = False

# --- CAN SİSTEMİ ---
player_lives = 3
max_lives    = 3
death_anim_timer = 0
respawn_timer    = 0

# --- CHECKPOINT ---
checkpoint_rect     = None
checkpoint_reached  = False
checkpoint_player_x = 60
checkpoint_player_y = 260

# --- FREE PLAY ---
free_play_mode = False

# --- YILDIZ SİSTEMİ ---
level_stars = {}

def calc_stars(time_taken, coins_collected, total_coins, lives_left):
    stars = 1
    if lives_left == max_lives and not hazard_touched_this_level:
        stars = 2
    if stars == 2 and time_taken < get_time_limit(current_level) * 0.6:
        stars = 3
    return stars

# --- WALL JUMP ---
wall_jump_timer   = 0   # >0 iken duvardan itme aktif
touching_wall_dir = 0   # -1 sol duvar, +1 sağ duvar

# --- HAREKETLİ HAZARDLAR ---
moving_hazards = []   # [{'rect': Rect, 'dir': 1/-1, 'min': x, 'max': x, 'speed': n}]

# --- COIN TRAIL ---
coin_trail = []   # toplanan coinlerin uçma animasyonu

# --- SPEEDRUN MODU ---
speedrun_mode      = False
speedrun_time      = 0.0
speedrun_best      = {}   # {level_num: float}

# --- DAILY CHALLENGE ---
import datetime
daily_level    = (datetime.date.today().toordinal() % 40) + 1
daily_done     = False
daily_score    = 0
in_daily       = False

# --- TUTORIAL ---
tutorial_hints = {
    1: ["Arrow Keys = Move", "SPACE = Jump", "Collect all coins!"],
    2: ["SPACE again in air = Double Jump"],
    3: ["LSHIFT = Dash!"],
}
tutorial_shown = set()
tutorial_active_hint = ""
tutorial_hint_timer  = 0

# --- GRAVITY FLIP ---
gravity_flipped   = False
gravity_flip_timer = 0   # aktif süre (frame)

# --- ZAMAN LİMİTİ ---
def get_time_limit(lvl):
    base = 45
    if lvl >= 31: base = 25
    elif lvl >= 21: base = 30
    elif lvl >= 11: base = 35
    if lvl % 10 == 0: base -= 10
    return base

level_time_start = 0
level_time_paused_at = 0.0

# --- POWER-UPS ---
powerups = []
active_powerups = {}  # {'SHIELD': frames_left, 'SPEED': frames_left, 'EXTRA_JUMP': True}

# --- BOSS ---
boss_enemy = None
show_boss_warning = 0
boss_particles = []

# --- BAŞARILAR ---
achievement_notification = ""
achievement_notif_timer = 0

achievements = {
    'COIN MASTER':  {'unlocked': False, 'desc': 'Collect all coins in a level',       'bonus': 20},
    'SPEED RUNNER': {'unlocked': False, 'desc': 'Complete a level under 15 seconds',  'bonus': 15},
    'UNTOUCHABLE':  {'unlocked': False, 'desc': 'Finish without touching any hazard', 'bonus': 10},
    'LEVEL 10':     {'unlocked': False, 'desc': 'Complete level 10',                  'bonus': 25},
    'LEVEL 20':     {'unlocked': False, 'desc': 'Complete level 20',                  'bonus': 50},
    'SHOPAHOLIC':   {'unlocked': False, 'desc': 'Buy 3 different skins',              'bonus': 30},
}

# --- LEADERBOARD ---
highscores = []
skins_bought_count = 0
hazard_touched_this_level = False

# --- HIGHSCORE ---
def load_highscores():
    global highscores
    try:
        with open('highscores.json', 'r') as f:
            highscores = json.load(f)
    except:
        highscores = []

def save_highscores():
    try:
        with open('highscores.json', 'w') as f:
            json.dump(highscores, f)
    except:
        pass

def add_highscore(score_val, time_val, level_val):
    global highscores
    highscores.append({'score': score_val, 'time': round(time_val, 1), 'level': level_val})
    highscores.sort(key=lambda x: (-x['score'], x['time']))
    highscores = highscores[:5]
    save_highscores()

load_highscores()

# --- KAYIT SİSTEMİ ---
SAVE_FILE = 'savegame.json'

def save_game():
    data = {
        'total_score':     total_score,
        'unlocked_levels': unlocked_levels,
        'unlocked_skins':  unlocked_skins,
        'current_skin':    current_skin,
        'has_jetpack':     has_jetpack,
        'music_volume':    music_volume,
        'jump_volume':     jump_volume,
        'achievements':    {k: v['unlocked'] for k, v in achievements.items()},
        'skins_bought_count': skins_bought_count,
        'best_time':       best_time,
        'level_stars':     level_stars,
    }
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def load_game():
    global total_score, unlocked_levels, unlocked_skins, current_skin
    global has_jetpack, music_volume, jump_volume, skins_bought_count, best_time, level_stars
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
        total_score      = data.get('total_score', 0)
        unlocked_levels  = data.get('unlocked_levels', 1)
        unlocked_skins   = data.get('unlocked_skins', ['Default'])
        current_skin     = data.get('current_skin', 'Default')
        has_jetpack      = data.get('has_jetpack', False)
        music_volume     = data.get('music_volume', 1.0)
        jump_volume      = data.get('jump_volume', 0.5)
        skins_bought_count = data.get('skins_bought_count', 0)
        best_time        = data.get('best_time', 0)
        level_stars      = {int(k): v for k,v in data.get('level_stars', {}).items()}
        saved_ach        = data.get('achievements', {})
        for k, v in saved_ach.items():
            if k in achievements:
                achievements[k]['unlocked'] = v
    except:
        pass

# --- ACHIEVEMENT ---
def unlock_achievement(name):
    global total_score, achievement_notification, achievement_notif_timer
    if name in achievements and not achievements[name]['unlocked']:
        achievements[name]['unlocked'] = True
        bonus = achievements[name]['bonus']
        total_score += bonus
        achievement_notification = f"ACHIEVEMENT: {name}  +{bonus}!"
        achievement_notif_timer = 200

# --- UI RECTS ---
start_button_rect     = pygame.Rect(0, 0, 0, 0)
store_button_rect     = pygame.Rect(0, 0, 0, 0)
settings_button_rect  = pygame.Rect(0, 0, 0, 0)
exit_button_rect      = pygame.Rect(0, 0, 0, 0)
back_button_rect      = pygame.Rect(0, 0, 0, 0)
music_slider_rect     = pygame.Rect(0, 0, 0, 0)
jump_slider_rect      = pygame.Rect(0, 0, 0, 0)
play_again_btn_rect   = pygame.Rect(0, 0, 0, 0)
menu_btn_rect         = pygame.Rect(0, 0, 0, 0)
shop_skin_rects       = {}
level_rects           = {}
jetpack_rect          = pygame.Rect(0, 0, 0, 0)
leaderboard_btn_rect  = pygame.Rect(0, 0, 0, 0)
achievements_btn_rect = pygame.Rect(0, 0, 0, 0)
pause_resume_rect     = pygame.Rect(0, 0, 0, 0)
pause_restart_rect    = pygame.Rect(0, 0, 0, 0)
pause_menu_rect       = pygame.Rect(0, 0, 0, 0)

# --- SHOP & SKIN SYSTEM ---
current_skin   = "Default"
unlocked_skins = ["Default"]

skin_prices = {"Default": 0, "Purple": 10, "Blue": 20, "Red": 30, "Gray": 40, "Yellow": 50}
skins = {
    "Default": "player_sheet2-2.png", "Purple": "player_purple.png",
    "Blue": "player_blue.png",        "Red": "player_red.png",
    "Gray": "player_gray.png",        "Yellow": "player_yellow.png"
}
skin_colors = {
    "Default": (245, 197, 66), "Purple": (150, 50, 200),
    "Blue": (50, 150, 255),    "Red": (220, 50, 50),
    "Gray": (150, 150, 150),   "Yellow": (240, 220, 50)
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
    for i in range(4):
        frame_img = cropped_sheet.subsurface(pygame.Rect(i * frame_w, 0, frame_w, sheet_h)).copy()
        door_frames.append(pygame.transform.scale(frame_img, (80, 80)))
except:
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
vel_y = 0

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

def toggle_fullscreen():
    global fullscreen, display_surface
    fullscreen = not fullscreen
    if fullscreen:
        display_surface = pygame.display.set_mode((1680, 1050), pygame.FULLSCREEN)
    else:
        display_surface = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Sky Hopper - Premium Edition")

idle_frames = []
run_frames  = []
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
        cx_off = int(cell_w * 0.05); cy_off = int(cell_h * 0.05)
        cw = int(cell_w * 0.9);      ch = int(cell_h * 0.9)
        idle_frames = [get_clean_image(sprite_sheet, i*cell_w+cx_off, 0*cell_h+cy_off, cw, ch, target_w, target_h) for i in range(4)]
        run_frames = []
        for i in range(4):
            img = get_clean_image(sprite_sheet, i*cell_w+cx_off, 1*cell_h+cy_off, cw, ch, target_w, target_h)
            if i == 3: img = pygame.transform.flip(img, True, False)
            run_frames.append(img)
        back_frames = list(run_frames)
        jump_frames = [get_clean_image(sprite_sheet, i*cell_w+cx_off, 2*cell_h+cy_off, cw, ch, target_w, target_h) for i in range(4)]
        has_sprites = True
    except Exception as e:
        print(f"Could not load skin {skin_name}: {e}")
        has_sprites = False

load_player_sprites(current_skin)

# ============================================================
# LEVEL DATA (1-40)
# ============================================================
level_1_platforms  = [pygame.Rect(0,470,280,30),pygame.Rect(420,470,280,30),pygame.Rect(150,380,120,20),pygame.Rect(340,300,120,20),pygame.Rect(520,220,120,20),pygame.Rect(260,160,100,20)]
level_1_coins      = [pygame.Rect(200,345,16,16),pygame.Rect(390,265,16,16),pygame.Rect(560,185,16,16),pygame.Rect(300,130,16,16)]
level_1_hazards    = [pygame.Rect(280,460,140,14)]  # küçük tek engel ortada

level_2_platforms  = [pygame.Rect(0,470,150,30),pygame.Rect(250,400,120,20),pygame.Rect(500,330,120,20),pygame.Rect(220,250,100,20),pygame.Rect(20,180,120,20),pygame.Rect(400,120,200,20),pygame.Rect(425,470,375,30)]
level_2_coins      = [pygame.Rect(290,365,16,16),pygame.Rect(540,295,16,16),pygame.Rect(60,145,16,16),pygame.Rect(492,94,16,16)]
level_2_hazards    = [pygame.Rect(150,460,120,14)]  # zemin kenarında ateş

level_3_platforms  = [pygame.Rect(0,470,155,30),pygame.Rect(200,400,80,20),pygame.Rect(400,330,80,20),pygame.Rect(600,250,80,20),pygame.Rect(300,180,100,20),pygame.Rect(50,120,120,20),pygame.Rect(300,470,300,30)]
level_3_coins      = [pygame.Rect(230,365,16,16),pygame.Rect(430,295,16,16),pygame.Rect(630,215,16,16),pygame.Rect(102,94,16,16)]
level_3_hazards    = [pygame.Rect(155,460,145,14), pygame.Rect(600,460,100,14)]

level_4_platforms  = [pygame.Rect(0,470,150,30),pygame.Rect(150,380,80,20),pygame.Rect(300,380,80,20),pygame.Rect(550,300,80,20),pygame.Rect(350,200,80,20),pygame.Rect(100,100,100,20),pygame.Rect(354,470,200,30)]
level_4_coins      = [pygame.Rect(180,345,16,16),pygame.Rect(330,345,16,16),pygame.Rect(580,265,16,16),pygame.Rect(142,74,16,16)]
level_4_hazards    = [pygame.Rect(150,460,200,14), pygame.Rect(554,460,146,14)]

level_5_platforms  = [pygame.Rect(0,470,80,30),pygame.Rect(120,370,60,20),pygame.Rect(30,270,60,20),pygame.Rect(200,180,60,20),pygame.Rect(400,180,100,20),pygame.Rect(600,100,80,20),pygame.Rect(356,295,73,20)]
level_5_coins      = [pygame.Rect(140,335,16,16),pygame.Rect(50,235,16,16),pygame.Rect(220,145,16,16),pygame.Rect(632,74,16,16)]
level_5_hazards    = [pygame.Rect(80,460,240,14), pygame.Rect(500,460,100,14)]

level_6_platforms  = [pygame.Rect(0,470,173,16),pygame.Rect(150,400,50,20),pygame.Rect(300,330,110,20),pygame.Rect(550,260,50,20),pygame.Rect(300,160,119,20),pygame.Rect(35,100,95,20)]
level_6_coins      = [pygame.Rect(165,365,16,16),pygame.Rect(565,225,16,16),pygame.Rect(330,125,16,16),pygame.Rect(72,74,16,16)]
level_6_hazards    = [pygame.Rect(173,455,380,15), pygame.Rect(410,318,80,14)]  # platform kenarı + orta engel

level_7_platforms  = [pygame.Rect(0,470,120,30),pygame.Rect(180,400,60,20),pygame.Rect(350,330,60,20),pygame.Rect(520,260,60,20),pygame.Rect(350,180,60,20),pygame.Rect(152,100,100,20)]
level_7_coins      = [pygame.Rect(202,365,16,16),pygame.Rect(542,225,16,16),pygame.Rect(372,145,16,16),pygame.Rect(192,76,16,16)]
level_7_hazards    = [pygame.Rect(120,460,230,15), pygame.Rect(500,460,100,15), pygame.Rect(240,318,110,14)]

level_8_platforms  = [pygame.Rect(0,470,140,30),pygame.Rect(150,420,50,20),pygame.Rect(300,350,50,20),pygame.Rect(450,280,50,20),pygame.Rect(600,200,80,20),pygame.Rect(350,130,60,20),pygame.Rect(95,80,90,20)]
level_8_coins      = [pygame.Rect(167,385,16,16),pygame.Rect(317,315,16,16),pygame.Rect(467,245,16,16),pygame.Rect(132,56,16,16)]
level_8_hazards    = [pygame.Rect(140,458,160,15), pygame.Rect(350,458,250,15), pygame.Rect(200,338,100,14)]

level_9_platforms  = [pygame.Rect(0,470,140,30),pygame.Rect(150,380,40,20),pygame.Rect(300,380,40,20),pygame.Rect(480,300,40,20),pygame.Rect(600,220,60,20),pygame.Rect(400,150,40,20),pygame.Rect(200,100,40,20),pygame.Rect(37,63,90,20)]
level_9_coins      = [pygame.Rect(162,345,16,16),pygame.Rect(492,265,16,16),pygame.Rect(412,115,16,16),pygame.Rect(72,36,16,16)]
level_9_hazards    = [pygame.Rect(140,458,160,15), pygame.Rect(340,458,260,15), pygame.Rect(190,368,110,14), pygame.Rect(520,288,40,14)]

level_10_platforms = [pygame.Rect(0,470,140,30),pygame.Rect(150,400,40,20),pygame.Rect(350,350,40,20),pygame.Rect(550,280,40,20),pygame.Rect(350,200,40,20),pygame.Rect(485,95,90,20)]
level_10_coins     = [pygame.Rect(162,365,16,16),pygame.Rect(562,245,16,16),pygame.Rect(522,64,16,16)]
level_10_hazards   = [pygame.Rect(140,458,210,15), pygame.Rect(390,458,210,15), pygame.Rect(190,388,160,14), pygame.Rect(390,268,160,14)]

level_11_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(200,320,70,20),pygame.Rect(350,250,70,20),pygame.Rect(150,180,70,20),pygame.Rect(350,120,70,20),pygame.Rect(550,100,100,20)]
level_11_coins     = [pygame.Rect(220,290,16,16),pygame.Rect(370,220,16,16),pygame.Rect(170,150,16,16),pygame.Rect(580,70,16,16)]
level_11_hazards   = [pygame.Rect(150,340,200,14), pygame.Rect(420,340,230,14), pygame.Rect(270,238,80,14)]

level_12_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(200,380,100,20),pygame.Rect(400,350,100,20),pygame.Rect(550,250,100,20),pygame.Rect(350,180,100,20),pygame.Rect(150,100,100,20)]
level_12_coins     = [pygame.Rect(242,350,16,16),pygame.Rect(592,220,16,16),pygame.Rect(392,150,16,16),pygame.Rect(192,70,16,16)]
level_12_hazards   = [pygame.Rect(150,340,50,14), pygame.Rect(300,368,100,14), pygame.Rect(500,340,200,14), pygame.Rect(440,168,110,14)]

level_13_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(200,300,80,20),pygame.Rect(50,220,80,20),pygame.Rect(250,150,80,20),pygame.Rect(450,200,80,20),pygame.Rect(600,120,100,20)]
level_13_coins     = [pygame.Rect(230,270,16,16),pygame.Rect(80,190,16,16),pygame.Rect(280,120,16,16),pygame.Rect(640,90,16,16)]
level_13_hazards   = [pygame.Rect(150,340,50,14), pygame.Rect(280,288,170,14), pygame.Rect(130,208,120,14), pygame.Rect(530,188,70,14)]

level_14_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(220,380,100,20),pygame.Rect(420,320,100,20),pygame.Rect(600,250,100,20),pygame.Rect(400,180,100,20),pygame.Rect(200,100,100,20)]
level_14_coins     = [pygame.Rect(262,350,16,16),pygame.Rect(462,290,16,16),pygame.Rect(442,150,16,16),pygame.Rect(242,70,16,16)]
level_14_hazards   = [pygame.Rect(150,340,70,14), pygame.Rect(320,368,100,14), pygame.Rect(520,308,80,14), pygame.Rect(500,238,100,14), pygame.Rect(300,168,100,14)]

level_15_platforms = [pygame.Rect(0,350,120,30),pygame.Rect(180,320,100,20),pygame.Rect(380,320,100,20),pygame.Rect(580,250,100,20),pygame.Rect(380,180,100,20),pygame.Rect(180,120,100,20),pygame.Rect(380,60,100,20)]
level_15_coins     = [pygame.Rect(222,290,16,16),pygame.Rect(622,220,16,16),pygame.Rect(222,90,16,16),pygame.Rect(422,30,16,16)]
level_15_hazards   = [pygame.Rect(120,340,60,14), pygame.Rect(280,308,100,14), pygame.Rect(480,308,100,14), pygame.Rect(680,238,20,14), pygame.Rect(480,168,100,14), pygame.Rect(280,108,100,14)]

level_16_platforms = [pygame.Rect(0,350,120,30),pygame.Rect(180,300,70,20),pygame.Rect(380,250,70,20),pygame.Rect(580,200,70,20),pygame.Rect(350,150,60,20),pygame.Rect(150,100,80,20)]
level_16_coins     = [pygame.Rect(200,270,16,16),pygame.Rect(600,170,16,16),pygame.Rect(180,70,16,16)]
level_16_hazards   = [pygame.Rect(120,340,60,14), pygame.Rect(250,288,130,14), pygame.Rect(450,238,130,14), pygame.Rect(410,188,140,14), pygame.Rect(230,138,120,14)]

level_17_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(250,350,100,20),pygame.Rect(450,300,100,20),pygame.Rect(600,220,100,20),pygame.Rect(400,150,100,20),pygame.Rect(200,80,100,20)]
level_17_coins     = [pygame.Rect(292,320,16,16),pygame.Rect(642,190,16,16),pygame.Rect(442,120,16,16),pygame.Rect(242,50,16,16)]
level_17_hazards   = [pygame.Rect(150,340,100,14), pygame.Rect(350,338,100,14), pygame.Rect(550,288,50,14), pygame.Rect(700,208,0,14), pygame.Rect(500,138,100,14), pygame.Rect(300,68,100,14)]

level_18_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(200,400,120,20),pygame.Rect(420,340,100,20),pygame.Rect(600,260,100,20),pygame.Rect(400,180,100,20),pygame.Rect(200,100,100,20)]
level_18_coins     = [pygame.Rect(252,370,16,16),pygame.Rect(642,230,16,16),pygame.Rect(442,150,16,16),pygame.Rect(242,70,16,16)]
level_18_hazards   = [pygame.Rect(150,340,50,14), pygame.Rect(320,388,100,14), pygame.Rect(520,328,100,14), pygame.Rect(700,248,0,14), pygame.Rect(500,168,100,14), pygame.Rect(300,88,100,14)]

level_19_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(220,320,100,20),pygame.Rect(420,250,100,20),pygame.Rect(600,180,100,20),pygame.Rect(380,100,100,20)]
level_19_coins     = [pygame.Rect(262,290,16,16),pygame.Rect(642,150,16,16),pygame.Rect(422,70,16,16)]
level_19_hazards   = [pygame.Rect(150,338,70,14), pygame.Rect(320,308,100,14), pygame.Rect(520,238,80,14), pygame.Rect(480,168,120,14), pygame.Rect(250,88,130,14)]

level_20_platforms = [pygame.Rect(0,310,150,30),pygame.Rect(200,300,80,20),pygame.Rect(350,250,80,20),pygame.Rect(550,200,80,20),pygame.Rect(350,120,80,20),pygame.Rect(100,80,100,20)]
level_20_coins     = [pygame.Rect(230,270,16,16),pygame.Rect(580,170,16,16),pygame.Rect(140,50,16,16)]
level_20_hazards   = [pygame.Rect(150,300,50,14), pygame.Rect(280,288,70,14), pygame.Rect(430,238,120,14), pygame.Rect(630,188,70,14), pygame.Rect(430,108,120,14), pygame.Rect(200,68,100,14)]
level_21_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(200,380,60,20),pygame.Rect(400,320,50,20),pygame.Rect(600,250,60,20),pygame.Rect(350,150,50,20),pygame.Rect(150,90,80,20)]
level_21_coins     = [pygame.Rect(415,290,16,16),pygame.Rect(620,220,16,16),pygame.Rect(180,60,16,16)]
level_21_hazards   = [pygame.Rect(150,338,50,14),pygame.Rect(260,368,140,14),pygame.Rect(450,308,150,14),pygame.Rect(660,238,40,14),pygame.Rect(400,138,150,14),pygame.Rect(230,78,120,14)]

level_22_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(180,420,60,20),pygame.Rect(320,380,60,20),pygame.Rect(470,300,60,20),pygame.Rect(270,220,60,20),pygame.Rect(70,140,80,20),pygame.Rect(300,80,80,20)]
level_22_coins     = [pygame.Rect(340,350,16,16),pygame.Rect(290,190,16,16),pygame.Rect(330,50,16,16)]
level_22_hazards   = [pygame.Rect(150,338,30,14),pygame.Rect(240,408,80,14),pygame.Rect(380,368,90,14),pygame.Rect(530,288,90,14),pygame.Rect(330,208,90,14),pygame.Rect(150,128,120,14),pygame.Rect(380,68,80,14)]

level_23_platforms = [pygame.Rect(0,310,150,30),pygame.Rect(240,310,60,20),pygame.Rect(450,300,60,20),pygame.Rect(620,200,60,20),pygame.Rect(400,120,60,20),pygame.Rect(200,70,80,20)]
level_23_coins     = [pygame.Rect(260,320,16,16),pygame.Rect(640,170,16,16),pygame.Rect(230,40,16,16)]
level_23_hazards   = [pygame.Rect(150,298,90,14),pygame.Rect(300,298,150,14),pygame.Rect(510,288,110,14),pygame.Rect(680,188,20,14),pygame.Rect(460,108,140,14),pygame.Rect(280,58,120,14)]

level_24_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(220,350,80,20),pygame.Rect(420,280,80,20),pygame.Rect(600,200,80,20),pygame.Rect(300,120,80,20),pygame.Rect(100,60,80,20)]
level_24_coins     = [pygame.Rect(250,320,16,16),pygame.Rect(630,170,16,16),pygame.Rect(130,30,16,16)]
level_24_hazards   = [pygame.Rect(150,338,70,14),pygame.Rect(300,338,120,14),pygame.Rect(500,268,100,14),pygame.Rect(680,188,20,14),pygame.Rect(380,108,100,14),pygame.Rect(180,48,100,14),pygame.Rect(450,158,150,14)]

level_25_platforms = [pygame.Rect(0,310,150,30),pygame.Rect(200,280,50,20),pygame.Rect(50,200,50,20),pygame.Rect(200,130,50,20),pygame.Rect(350,100,50,20),pygame.Rect(550,80,80,20)]
level_25_coins     = [pygame.Rect(65,170,16,16),pygame.Rect(365,70,16,16),pygame.Rect(580,50,16,16)]
level_25_hazards   = [pygame.Rect(150,298,50,14),pygame.Rect(250,268,100,14),pygame.Rect(100,188,100,14),pygame.Rect(250,118,100,14),pygame.Rect(400,88,150,14),pygame.Rect(630,68,20,14),pygame.Rect(0,188,50,14)]

level_26_platforms = [pygame.Rect(0,310,150,30),pygame.Rect(200,270,80,20),pygame.Rect(350,220,80,20),pygame.Rect(500,170,80,20),pygame.Rect(350,120,80,20),pygame.Rect(150,70,80,20)]
level_26_coins     = [pygame.Rect(230,240,16,16),pygame.Rect(380,190,16,16),pygame.Rect(530,140,16,16),pygame.Rect(180,40,16,16)]
level_26_hazards   = [pygame.Rect(150,298,50,14),pygame.Rect(280,258,70,14),pygame.Rect(430,208,70,14),pygame.Rect(580,158,80,14),pygame.Rect(430,108,80,14),pygame.Rect(230,58,80,14),pygame.Rect(0,188,80,14)]

level_27_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(220,300,80,20),pygame.Rect(450,250,80,20),pygame.Rect(620,180,60,20),pygame.Rect(400,100,60,20),pygame.Rect(150,80,80,20)]
level_27_coins     = [pygame.Rect(250,270,16,16),pygame.Rect(640,150,16,16),pygame.Rect(180,50,16,16)]
level_27_hazards   = [pygame.Rect(150,338,70,14),pygame.Rect(300,288,150,14),pygame.Rect(530,238,90,14),pygame.Rect(680,168,20,14),pygame.Rect(460,88,140,14),pygame.Rect(230,68,80,14),pygame.Rect(0,238,80,14)]

level_28_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(200,400,60,20),pygame.Rect(380,320,60,20),pygame.Rect(520,250,60,20),pygame.Rect(350,160,60,20),pygame.Rect(150,100,80,20)]
level_28_coins     = [pygame.Rect(215,370,16,16),pygame.Rect(535,220,16,16),pygame.Rect(180,70,16,16)]
level_28_hazards   = [pygame.Rect(150,338,50,14),pygame.Rect(260,388,120,14),pygame.Rect(440,308,80,14),pygame.Rect(580,238,80,14),pygame.Rect(410,148,110,14),pygame.Rect(230,88,80,14),pygame.Rect(0,288,80,14),pygame.Rect(440,238,80,14)]

level_29_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(250,300,40,20),pygame.Rect(500,250,40,20),pygame.Rect(650,150,40,20),pygame.Rect(350,100,40,20),pygame.Rect(100,60,80,20)]
level_29_coins     = [pygame.Rect(260,270,16,16),pygame.Rect(660,120,16,16),pygame.Rect(360,70,16,16)]
level_29_hazards   = [pygame.Rect(150,338,100,14),pygame.Rect(290,288,210,14),pygame.Rect(540,238,110,14),pygame.Rect(690,138,10,14),pygame.Rect(390,88,110,14),pygame.Rect(180,48,80,14),pygame.Rect(0,238,100,14),pygame.Rect(300,148,200,14)]

level_30_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(180,380,50,20),pygame.Rect(380,350,50,20),pygame.Rect(580,280,50,20),pygame.Rect(350,200,50,20),pygame.Rect(150,140,50,20),pygame.Rect(300,70,80,20)]
level_30_coins     = [pygame.Rect(195,350,16,16),pygame.Rect(595,250,16,16),pygame.Rect(165,110,16,16)]
level_30_hazards   = [pygame.Rect(150,338,30,14),pygame.Rect(230,368,150,14),pygame.Rect(430,338,150,14),pygame.Rect(630,268,70,14),pygame.Rect(400,188,150,14),pygame.Rect(200,128,150,14),pygame.Rect(380,58,100,14),pygame.Rect(0,268,80,14)]
level_31_platforms = [pygame.Rect(0,350,150,30),pygame.Rect(200,320,80,20),pygame.Rect(380,260,80,20),pygame.Rect(560,200,80,20),pygame.Rect(350,130,80,20),pygame.Rect(140,70,80,20)]
level_31_coins     = [pygame.Rect(230,290,16,16),pygame.Rect(590,170,16,16),pygame.Rect(170,40,16,16)]
level_31_hazards   = [pygame.Rect(150,338,50,14),pygame.Rect(280,308,100,14),pygame.Rect(460,248,100,14),pygame.Rect(640,188,80,14),pygame.Rect(430,118,130,14),pygame.Rect(220,58,130,14),pygame.Rect(0,248,100,14),pygame.Rect(350,178,110,14)]

level_32_platforms = [pygame.Rect(0,350,120,30),pygame.Rect(180,290,60,20),pygame.Rect(360,240,60,20),pygame.Rect(540,180,60,20),pygame.Rect(260,140,80,20),pygame.Rect(430,80,80,20)]
level_32_coins     = [pygame.Rect(205,260,16,16),pygame.Rect(565,150,16,16),pygame.Rect(455,50,16,16)]
level_32_hazards   = [pygame.Rect(120,338,60,14),pygame.Rect(240,278,120,14),pygame.Rect(420,228,120,14),pygame.Rect(600,168,100,14),pygame.Rect(340,128,90,14),pygame.Rect(510,68,100,14),pygame.Rect(0,228,80,14),pygame.Rect(240,168,120,14)]

level_33_platforms = [pygame.Rect(0,360,160,30),pygame.Rect(220,310,70,20),pygame.Rect(420,280,70,20),pygame.Rect(610,220,70,20),pygame.Rect(330,150,70,20),pygame.Rect(150,90,80,20)]
level_33_coins     = [pygame.Rect(250,280,16,16),pygame.Rect(640,190,16,16),pygame.Rect(180,60,16,16)]
level_33_hazards   = [pygame.Rect(160,348,60,14),pygame.Rect(290,298,130,14),pygame.Rect(490,268,120,14),pygame.Rect(680,208,20,14),pygame.Rect(400,138,130,14),pygame.Rect(230,78,130,14),pygame.Rect(0,268,80,14),pygame.Rect(350,208,130,14),pygame.Rect(0,78,80,14)]

level_34_platforms = [pygame.Rect(0,330,140,30),pygame.Rect(180,300,60,20),pygame.Rect(360,250,60,20),pygame.Rect(540,200,60,20),pygame.Rect(260,150,60,20),pygame.Rect(100,100,80,20),pygame.Rect(430,80,80,20)]
level_34_coins     = [pygame.Rect(205,270,16,16),pygame.Rect(565,170,16,16),pygame.Rect(455,50,16,16)]
level_34_hazards   = [pygame.Rect(140,318,40,14),pygame.Rect(240,288,120,14),pygame.Rect(420,238,120,14),pygame.Rect(600,188,100,14),pygame.Rect(320,138,110,14),pygame.Rect(180,88,110,14),pygame.Rect(510,68,100,14),pygame.Rect(0,188,80,14),pygame.Rect(280,168,80,14)]

level_35_platforms = [pygame.Rect(0,340,130,30),pygame.Rect(200,300,70,20),pygame.Rect(390,260,70,20),pygame.Rect(580,210,70,20),pygame.Rect(320,140,70,20),pygame.Rect(110,80,80,20)]
level_35_coins     = [pygame.Rect(220,270,16,16),pygame.Rect(612,180,16,16),pygame.Rect(140,50,16,16)]
level_35_hazards   = [pygame.Rect(130,328,70,14),pygame.Rect(270,288,120,14),pygame.Rect(460,248,120,14),pygame.Rect(650,198,50,14),pygame.Rect(390,128,130,14),pygame.Rect(190,68,130,14),pygame.Rect(0,198,80,14),pygame.Rect(270,168,120,14),pygame.Rect(520,108,60,14)]

level_36_platforms = [pygame.Rect(0,320,150,30),pygame.Rect(220,290,80,20),pygame.Rect(420,260,80,20),pygame.Rect(600,220,80,20),pygame.Rect(320,140,80,20),pygame.Rect(130,80,80,20)]
level_36_coins     = [pygame.Rect(250,260,16,16),pygame.Rect(632,190,16,16),pygame.Rect(160,50,16,16)]
level_36_hazards   = [pygame.Rect(150,308,70,14),pygame.Rect(300,278,120,14),pygame.Rect(500,248,100,14),pygame.Rect(680,208,20,14),pygame.Rect(400,128,120,14),pygame.Rect(210,68,120,14),pygame.Rect(0,208,80,14),pygame.Rect(320,188,80,14),pygame.Rect(500,108,100,14),pygame.Rect(0,108,80,14)]

level_37_platforms = [pygame.Rect(0,340,120,30),pygame.Rect(180,300,60,20),pygame.Rect(360,250,60,20),pygame.Rect(540,190,60,20),pygame.Rect(250,150,60,20),pygame.Rect(90,90,80,20),pygame.Rect(430,70,80,20)]
level_37_coins     = [pygame.Rect(205,270,16,16),pygame.Rect(565,160,16,16),pygame.Rect(455,40,16,16)]
level_37_hazards   = [pygame.Rect(120,328,60,14),pygame.Rect(240,288,120,14),pygame.Rect(420,238,120,14),pygame.Rect(600,178,100,14),pygame.Rect(310,138,110,14),pygame.Rect(170,78,110,14),pygame.Rect(510,58,100,14),pygame.Rect(0,178,80,14),pygame.Rect(240,118,110,14),pygame.Rect(420,58,10,14)]

level_38_platforms = [pygame.Rect(0,360,140,30),pygame.Rect(200,320,70,20),pygame.Rect(380,280,70,20),pygame.Rect(560,240,70,20),pygame.Rect(320,180,70,20),pygame.Rect(140,120,80,20)]
level_38_coins     = [pygame.Rect(230,290,16,16),pygame.Rect(590,210,16,16),pygame.Rect(170,90,16,16)]
level_38_hazards   = [pygame.Rect(140,348,60,14),pygame.Rect(270,308,110,14),pygame.Rect(450,268,110,14),pygame.Rect(630,228,70,14),pygame.Rect(390,168,110,14),pygame.Rect(220,108,110,14),pygame.Rect(0,228,80,14),pygame.Rect(300,248,80,14),pygame.Rect(480,188,80,14),pygame.Rect(220,168,80,14)]

level_39_platforms = [pygame.Rect(0,330,150,30),pygame.Rect(220,290,80,20),pygame.Rect(420,240,80,20),pygame.Rect(610,180,70,20),pygame.Rect(330,120,70,20),pygame.Rect(140,70,80,20)]
level_39_coins     = [pygame.Rect(250,260,16,16),pygame.Rect(640,150,16,16),pygame.Rect(170,40,16,16)]
level_39_hazards   = [pygame.Rect(150,318,70,14),pygame.Rect(300,278,120,14),pygame.Rect(500,228,110,14),pygame.Rect(680,168,20,14),pygame.Rect(400,108,110,14),pygame.Rect(220,58,110,14),pygame.Rect(0,168,80,14),pygame.Rect(370,188,110,14),pygame.Rect(150,108,80,14),pygame.Rect(500,48,80,14)]

level_40_platforms = [pygame.Rect(0,350,160,30),pygame.Rect(220,310,80,20),pygame.Rect(430,270,80,20),pygame.Rect(610,220,80,20),pygame.Rect(330,150,80,20),pygame.Rect(130,80,80,20)]
level_40_coins     = [pygame.Rect(250,280,16,16),pygame.Rect(642,190,16,16),pygame.Rect(160,50,16,16)]
level_40_hazards   = [pygame.Rect(160,338,60,14),pygame.Rect(300,298,130,14),pygame.Rect(510,258,100,14),pygame.Rect(690,208,10,14),pygame.Rect(410,138,130,14),pygame.Rect(210,68,130,14),pygame.Rect(0,208,80,14),pygame.Rect(350,218,80,14),pygame.Rect(530,158,80,14),pygame.Rect(210,148,80,14),pygame.Rect(410,78,80,14)]

level_moving_data = {
    1:  [{'idx': 5, 'dir': 1, 'min': 150, 'max': 450}],
    2:  [{'idx': 3, 'dir': 1, 'min': 100, 'max': 400}],
    3:  [{'idx': 4, 'dir': 1, 'min': 200, 'max': 500}],
    4:  [{'idx': 2, 'dir': 1, 'min': 200, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 500}],
    5:  [{'idx': 4, 'dir': 1, 'min': 300, 'max': 500}],
    6:  [{'idx': 2, 'dir': 1, 'min': 200, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 150, 'max': 450}],
    7:  [{'idx': 1, 'dir': 1, 'min': 150, 'max': 300}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 650}],
    8:  [{'idx': 1, 'dir': 1, 'min': 120, 'max': 250}, {'idx': 2, 'dir': -1, 'min': 280, 'max': 420}, {'idx': 3, 'dir': 1, 'min': 420, 'max': 580}],
    9:  [{'idx': 2, 'dir': 1, 'min': 250, 'max': 400}, {'idx': 4, 'dir': -1, 'min': 550, 'max': 650}, {'idx': 5, 'dir': 1, 'min': 350, 'max': 500}],
    10: [{'idx': 1, 'dir': 1, 'min': 100, 'max': 250}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 620}, {'idx': 5, 'dir': 1, 'min': 100, 'max': 250}],
    11: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 500}],
    12: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 500}],
    13: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 500}],
    14: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 500}],
    15: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}],
    16: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}],
    17: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 550}],
    18: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 500}],
    19: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}],
    20: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}, {'idx': 4, 'dir': -1, 'min': 200, 'max': 450}],
    21: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 550}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 650}],
    22: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}, {'idx': 4, 'dir': -1, 'min': 150, 'max': 350}],
    23: [{'idx': 2, 'dir': 1, 'min': 350, 'max': 600}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 500}],
    24: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 550}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 650}],
    25: [{'idx': 2, 'dir': 1, 'min':  50, 'max': 250}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 450}],
    26: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}, {'idx': 5, 'dir': -1, 'min': 200, 'max': 500}],
    27: [{'idx': 1, 'dir': 1, 'min': 150, 'max': 350}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 650}],
    28: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 450}],
    29: [{'idx': 2, 'dir': 1, 'min': 450, 'max': 650}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 450}],
    30: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 550}, {'idx': 4, 'dir': -1, 'min': 250, 'max': 500}],
    31: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}],
    32: [{'idx': 3, 'dir': -1, 'min': 250, 'max': 500}],
    33: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}],
    34: [{'idx': 3, 'dir': -1, 'min': 250, 'max': 450}],
    35: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}],
    36: [{'idx': 3, 'dir': -1, 'min': 280, 'max': 500}],
    37: [{'idx': 2, 'dir': 1, 'min': 250, 'max': 450}],
    38: [{'idx': 3, 'dir': -1, 'min': 300, 'max': 500}],
    39: [{'idx': 2, 'dir': 1, 'min': 300, 'max': 500}],
    40: [{'idx': 3, 'dir': -1, 'min': 250, 'max': 450}],
}

current_level = 1
platforms = []
coins = []
hazards = []
current_moving_data = []
door_rect = pygame.Rect(0, 0, 80, 80)

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

# ============================================================
# PARTICLE SİSTEMİ
# ============================================================
class Particle:
    def __init__(self, x, y, color, size=4, spread=2):
        self.x = x
        self.y = y
        self.vx = random.uniform(-spread, spread)
        self.vy = random.uniform(-spread * 2, spread * 0.5)
        self.life = 255
        self.decay = random.randint(10, 20)
        self.color = color
        self.size = size

def spawn_particles(x, y, color, amount=10, size=4, spread=2):
    for _ in range(amount):
        particles.append(Particle(x, y, color, size, spread))

def spawn_explosion(x, y, color):
    for _ in range(25):
        p = Particle(x, y, color, random.randint(3, 7), 4)
        p.vy = random.uniform(-6, 2)
        particles.append(p)

def spawn_sparkle(x, y):
    colors = [(255, 220, 50), (255, 255, 150), (255, 180, 0)]
    for _ in range(12):
        p = Particle(x, y, random.choice(colors), random.randint(2, 5), 3)
        particles.append(p)

def spawn_fireworks(screen_w, screen_h):
    positions = [(screen_w // 4, screen_h // 3),
                 (screen_w // 2, screen_h // 4),
                 (3 * screen_w // 4, screen_h // 3)]
    colors = [(255, 80, 80), (80, 255, 80), (80, 150, 255)]
    for pos, col in zip(positions, colors):
        spawn_explosion(pos[0], pos[1], col)

# ============================================================
# POWER-UP & BOSS SPAWN
# ============================================================
POWERUP_COLORS = {
    'SHIELD':      (50, 150, 255),
    'SPEED':       (80, 255, 80),
    'EXTRA_JUMP':  (180, 80, 255),
    'MAGNET':      (255, 200, 0),
    'GRAVITY':     (150, 80, 255),
}

def spawn_level_powerups(level_num):
    global powerups
    powerups = []
    if platforms and level_num % 3 == 0:
        all_types = ['SHIELD', 'SPEED', 'EXTRA_JUMP', 'MAGNET', 'GRAVITY']
        pu_type = random.choice(all_types)
        candidates = [p for p in platforms if p.width >= 40]
        if candidates:
            plat = random.choice(candidates)
            pu_rect = pygame.Rect(plat.centerx - 10, plat.top - 26, 20, 20)
            powerups.append({'rect': pu_rect, 'type': pu_type, 'angle': 0.0})

def spawn_boss(level_num):
    global boss_enemy, show_boss_warning
    if level_num % 10 == 0:
        boss_enemy = {
            'rect': pygame.Rect(300, 200, 70, 70),
            'dir': 1,
            'min': 80,
            'max': 580,
            'speed': 2 + (level_num // 10),
        }
        show_boss_warning = 180  # 3 saniye
    else:
        boss_enemy = None
        show_boss_warning = 0

# ============================================================
# LOAD LEVEL
# ============================================================
def load_level(level_num):
    global platforms, coins, hazards, current_moving_data, player, vel_y, door_rect
    global is_door_opening, door_anim_index, cam_x, cam_y, particles, ghost_trails
    global jetpack_fuel, hazard_touched_this_level, level_time_start, active_powerups
    global boss_particles

    is_door_opening = False
    door_anim_index = 3
    particles.clear()
    ghost_trails.clear()
    boss_particles.clear()
    jetpack_fuel = max_jetpack_fuel
    hazard_touched_this_level = False
    active_powerups.clear()

    level_data = {
        1:  (level_1_platforms,  level_1_coins,  level_1_hazards),
        2:  (level_2_platforms,  level_2_coins,  level_2_hazards),
        3:  (level_3_platforms,  level_3_coins,  level_3_hazards),
        4:  (level_4_platforms,  level_4_coins,  level_4_hazards),
        5:  (level_5_platforms,  level_5_coins,  level_5_hazards),
        6:  (level_6_platforms,  level_6_coins,  level_6_hazards),
        7:  (level_7_platforms,  level_7_coins,  level_7_hazards),
        8:  (level_8_platforms,  level_8_coins,  level_8_hazards),
        9:  (level_9_platforms,  level_9_coins,  level_9_hazards),
        10: (level_10_platforms, level_10_coins, level_10_hazards),
        11: (level_11_platforms, level_11_coins, level_11_hazards),
        12: (level_12_platforms, level_12_coins, level_12_hazards),
        13: (level_13_platforms, level_13_coins, level_13_hazards),
        14: (level_14_platforms, level_14_coins, level_14_hazards),
        15: (level_15_platforms, level_15_coins, level_15_hazards),
        16: (level_16_platforms, level_16_coins, level_16_hazards),
        17: (level_17_platforms, level_17_coins, level_17_hazards),
        18: (level_18_platforms, level_18_coins, level_18_hazards),
        19: (level_19_platforms, level_19_coins, level_19_hazards),
        20: (level_20_platforms, level_20_coins, level_20_hazards),
        21: (level_21_platforms, level_21_coins, level_21_hazards),
        22: (level_22_platforms, level_22_coins, level_22_hazards),
        23: (level_23_platforms, level_23_coins, level_23_hazards),
        24: (level_24_platforms, level_24_coins, level_24_hazards),
        25: (level_25_platforms, level_25_coins, level_25_hazards),
        26: (level_26_platforms, level_26_coins, level_26_hazards),
        27: (level_27_platforms, level_27_coins, level_27_hazards),
        28: (level_28_platforms, level_28_coins, level_28_hazards),
        29: (level_29_platforms, level_29_coins, level_29_hazards),
        30: (level_30_platforms, level_30_coins, level_30_hazards),
        31: (level_31_platforms, level_31_coins, level_31_hazards),
        32: (level_32_platforms, level_32_coins, level_32_hazards),
        33: (level_33_platforms, level_33_coins, level_33_hazards),
        34: (level_34_platforms, level_34_coins, level_34_hazards),
        35: (level_35_platforms, level_35_coins, level_35_hazards),
        36: (level_36_platforms, level_36_coins, level_36_hazards),
        37: (level_37_platforms, level_37_coins, level_37_hazards),
        38: (level_38_platforms, level_38_coins, level_38_hazards),
        39: (level_39_platforms, level_39_coins, level_39_hazards),
        40: (level_40_platforms, level_40_coins, level_40_hazards),
    }
    platforms = [pygame.Rect(p) for p in level_data[level_num][0]]
    coins     = [pygame.Rect(c) for c in level_data[level_num][1]]
    hazards   = [pygame.Rect(h) for h in level_data[level_num][2]]
    current_moving_data = copy.deepcopy(level_moving_data[level_num])

    player.x = 60
    player.y = 260
    vel_y = 0
    cam_x = player.centerx - 350
    cam_y = player.centery - 250

    if level_num == 30:
        door_rect.x = 520
        door_rect.y = 200
    elif coins:
        door_rect.centerx = coins[-1].centerx
        door_rect.centery  = coins[-1].centery - 4

    spawn_level_powerups(level_num)
    spawn_boss(level_num)
    level_time_start = pygame.time.get_ticks()

    # --- HAREKETLİ HAZARDLAR ---
    global moving_hazards, coin_trail, tutorial_hint_timer, tutorial_active_hint
    moving_hazards = []
    coin_trail     = []
    tutorial_hint_timer   = 0
    tutorial_active_hint  = ""

    # Seviye 6+ → hazardların bazıları hareket eder
    if level_num >= 6 and hazards:
        count = min(len(hazards), 1 + level_num // 8)
        for h in hazards[:count]:
            spd = 1 + (level_num // 10)
            moving_hazards.append({
                'rect':  pygame.Rect(h),
                'dir':   1,
                'min':   max(0, h.x - 80),
                'max':   min(700, h.x + 80),
                'speed': spd,
            })

    # Checkpoint kur (7. platform varsa ortaya)
    global checkpoint_rect, checkpoint_reached, checkpoint_player_x, checkpoint_player_y
    checkpoint_reached = False
    if len(platforms) >= 4:
        mid_plat = platforms[len(platforms)//2]
        checkpoint_rect = pygame.Rect(mid_plat.centerx - 10, mid_plat.top - 30, 20, 30)
        checkpoint_player_x = mid_plat.centerx - target_w//2
        checkpoint_player_y = mid_plat.top - target_h
    else:
        checkpoint_rect = None

# ============================================================
# RESET GAME
# ============================================================
def reset_game(starting_level=None):
    global current_level, score, start_time, game_won, game_over
    global is_running_sound_playing, transition_state, transition_alpha
    global cam_x, cam_y, screen_shake, jetpack_fuel, game_paused
    global player_lives, death_anim_timer, respawn_timer
    global wall_jump_timer, touching_wall_dir, gravity_flipped, gravity_flip_timer, speedrun_time

    if starting_level is not None:
        current_level = starting_level

    score = 0
    start_time = pygame.time.get_ticks()
    game_won   = False
    game_over  = False
    game_paused = False
    transition_state = 0
    transition_alpha = 0
    cam_x = 0
    cam_y = 0
    screen_shake = 0
    jetpack_fuel = max_jetpack_fuel
    player_lives = max_lives
    death_anim_timer = 0
    respawn_timer = 0
    wall_jump_timer   = 0
    touching_wall_dir = 0
    gravity_flipped   = False
    gravity_flip_timer = 0
    speedrun_time     = 0.0

    if 'run_sound' in globals() and run_sound:
        run_sound.stop()
    is_running_sound_playing = False
    if 'game_over_sound' in globals() and game_over_sound:
        game_over_sound.stop()

    load_level(current_level)
    try:
        pygame.mixer.music.play(-1)
    except:
        pass

# ============================================================
# FONTS
# ============================================================
try:
    font       = pygame.font.SysFont("Impact", 30)
    small_font = pygame.font.SysFont("Impact", 20)
    hud_font   = pygame.font.SysFont("Impact", 22)
    title_font = pygame.font.SysFont("Impact", 60)
    big_font   = pygame.font.SysFont("Impact", 42)
except:
    font       = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 24)
    hud_font   = pygame.font.SysFont(None, 22)
    title_font = pygame.font.SysFont(None, 60)
    big_font   = pygame.font.SysFont(None, 42)

# ============================================================
# BACKGROUND
# ============================================================
shooting_stars = []
nebulas = [
    {"x": 150, "y": 150, "color": (100, 50, 150),  "radius": 180},
    {"x": 550, "y": 350, "color": (50, 100, 200),  "radius": 220},
    {"x": 350, "y": 100, "color": (150, 50, 100),  "radius": 150},
]
stars = [(random.randint(0, 700), random.randint(0, 500), random.randint(1, 3)) for _ in range(60)]
bg_planets = [
    {"x":  50, "y": 400, "r": 180, "color": (45, 50, 75),  "border": 2, "scroll": 0.2},
    {"x": 600, "y": 100, "r":  40, "color": (60, 45, 65),  "border": 1, "scroll": 0.5},
    {"x": 550, "y": 380, "r":  80, "color": (35, 45, 60),  "border": 1, "scroll": 0.3},
]
bg_orbits = [
    {"cx": 600, "cy": 100, "rx": 90,  "ry": 25, "color": (80, 80, 100, 100),  "scroll": 0.5},
    {"cx": 550, "cy": 380, "rx": 160, "ry": 40, "color": (70, 75, 90,  80),   "scroll": 0.3},
]

def draw_cosmic_background(surf, draw_ox=0, draw_oy=0, menu_mode=False):
    surf.fill((15, 18, 36))
    for neb in nebulas:
        sf = 0.05 if not menu_mode else 0.01
        nx = neb["x"] - draw_ox * sf
        ny = neb["y"] - draw_oy * sf
        ns = pygame.Surface((neb["radius"]*2, neb["radius"]*2), pygame.SRCALPHA)
        for r in range(neb["radius"], 0, -12):
            alpha = int((1 - r / neb["radius"]) * 35)
            pygame.draw.circle(ns, neb["color"] + (alpha,), (neb["radius"], neb["radius"]), r)
        surf.blit(ns, (int(nx - neb["radius"]), int(ny - neb["radius"])))

    bg_timer = pygame.time.get_ticks() * 0.005
    for i, star in enumerate(stars):
        sf = 0.1 if not menu_mode else 0.02
        sx = int(star[0] - draw_ox * sf) % 700
        sy = int(star[1] - draw_oy * sf) % 500
        r  = max(1, star[2] + math.sin(bg_timer + i) * 0.8)
        pygame.draw.circle(surf, (255, 255, 255), (sx, sy), int(r))

    if random.random() < 0.008:
        shooting_stars.append({"x": random.randint(-50,600), "y": random.randint(-50,200),
                                "speed_x": random.uniform(6,10), "speed_y": random.uniform(3,5),
                                "length": random.randint(30,60), "alpha": 255})
    for s in shooting_stars[:]:
        s["x"] += s["speed_x"]; s["y"] += s["speed_y"]; s["alpha"] -= 6
        if s["alpha"] <= 0 or s["x"] > 750 or s["y"] > 550:
            shooting_stars.remove(s); continue
        ss = pygame.Surface((700, 500), pygame.SRCALPHA)
        pygame.draw.line(ss, (255,255,200,s["alpha"]),
                         (int(s["x"]), int(s["y"])),
                         (int(s["x"]-s["length"]), int(s["y"]-s["length"]*0.5)), 2)
        surf.blit(ss, (0, 0))

    for orbit in bg_orbits:
        sf = orbit["scroll"] if not menu_mode else 0.02
        ox = int(orbit["cx"] - draw_ox * sf)
        oy = int(orbit["cy"] - draw_oy * sf)
        os = pygame.Surface((orbit["rx"]*2, orbit["ry"]*2), pygame.SRCALPHA)
        pygame.draw.ellipse(os, orbit["color"], (0, 0, orbit["rx"]*2, orbit["ry"]*2), 1)
        surf.blit(os, (ox - orbit["rx"], oy - orbit["ry"]))

    pt = pygame.time.get_ticks() * 0.001
    for i, planet in enumerate(bg_planets):
        sf = planet["scroll"] if not menu_mode else 0.03
        px = int((planet["x"] + math.sin(pt+i)*8)    - draw_ox * sf)
        py = int((planet["y"] + math.cos(pt*0.8+i)*6) - draw_oy * sf)
        pygame.draw.circle(surf, planet["color"], (px, py), planet["r"], planet["border"])

# ============================================================
# SES SİSTEMİ
# ============================================================
try:
    pygame.mixer.init()
    jump_sound      = pygame.mixer.Sound("jumpsound.wav");      jump_sound.set_volume(jump_volume * 0.3)
    coin_sound      = pygame.mixer.Sound("coinsound.mp3");      coin_sound.set_volume(0.7)
    door_sound      = pygame.mixer.Sound("spacedoor.wav");      door_sound.set_volume(0.8)
    run_sound       = pygame.mixer.Sound("runningmusic.wav");   run_sound.set_volume(0.85)
    game_over_sound = pygame.mixer.Sound("gameoversound.mp3");  game_over_sound.set_volume(0.67)
    land_sound      = pygame.mixer.Sound("landhit.mp3");        land_sound.set_volume(0.79)
except:
    jump_sound = coin_sound = door_sound = run_sound = game_over_sound = land_sound = None

try:
    pygame.mixer.music.load("musicsound.mp3")
    pygame.mixer.music.set_volume(music_volume)
except:
    pass

reset_game(1)
load_game()
load_player_sprites(current_skin)
try: pygame.mixer.music.set_volume(music_volume)
except: pass
try:
    if jump_sound: jump_sound.set_volume(jump_volume * 0.3)
except: pass

# ============================================================
# YARDIMCI ÇİZİM FONKSİYONLARI
# ============================================================
def draw_button(surf, rect, text, font_obj, base_color, hover_color, border_color, mouse_pos):
    color = hover_color if rect.collidepoint(mouse_pos) else base_color
    pygame.draw.rect(surf, border_color, (rect.x-3, rect.y-3, rect.w+6, rect.h+6), border_radius=10)
    pygame.draw.rect(surf, color, rect, border_radius=10)
    t = font_obj.render(text, True, (255,255,255))
    surf.blit(t, (rect.x + (rect.w - t.get_width())//2, rect.y + (rect.h - t.get_height())//2))

def draw_pause_menu(surf, mouse_pos):
    global pause_resume_rect, pause_restart_rect, pause_menu_rect
    overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    bw, bh = 240, 52
    bx = GAME_WIDTH//2 - bw//2
    pause_title = title_font.render("PAUSED", True, (245, 197, 66))
    surf.blit(pause_title, (GAME_WIDTH//2 - pause_title.get_width()//2, 130))
    pause_resume_rect  = pygame.Rect(bx, 210, bw, bh)
    pause_restart_rect = pygame.Rect(bx, 278, bw, bh)
    pause_menu_rect    = pygame.Rect(bx, 346, bw, bh)
    draw_button(surf, pause_resume_rect,  "RESUME",    font, (20,24,46), (60,180,120),  (245,197,66), mouse_pos)
    draw_button(surf, pause_restart_rect, "RESTART",   font, (20,24,46), (180,120,60),  (245,197,66), mouse_pos)
    draw_button(surf, pause_menu_rect,    "MAIN MENU", font, (20,24,46), (200,60,60),   (245,197,66), mouse_pos)
    hint = small_font.render("ESC - Resume", True, (160,160,160))
    surf.blit(hint, (GAME_WIDTH//2 - hint.get_width()//2, 410))

def draw_powerup_hud(surf):
    x = 10
    for pu_type, val in list(active_powerups.items()):
        col = POWERUP_COLORS.get(pu_type, (255,255,255))
        pygame.draw.rect(surf, col, (x, 62, 80, 14), border_radius=4)
        if isinstance(val, int):
            ratio = val / (5 * 60)
            pygame.draw.rect(surf, (255,255,255), (x, 62, int(80*ratio), 14), border_radius=4)
        label = small_font.render(pu_type[:3], True, (255,255,255))
        surf.blit(label, (x+2, 62))
        x += 88

# ============================================================
# ANA OYUN DÖNGÜSÜ
# ============================================================
running = True
draw_ox = 0
draw_oy = 0

while running:
    mouse_pos = pygame.mouse.get_pos()
    ticks     = pygame.time.get_ticks()

    # ---- EVENT HANDLING ----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Fullscreen
            if event.key == pygame.K_F11:
                toggle_fullscreen()
            elif event.key == pygame.K_f and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)):
                toggle_fullscreen()
            elif event.key == pygame.K_ESCAPE and fullscreen:
                toggle_fullscreen()
            # PAUSE (ESC, oyun içinde)
            elif event.key == pygame.K_ESCAPE and game_started and not game_won and not game_over:
                game_paused = not game_paused
                if game_paused:
                    if run_sound and is_running_sound_playing:
                        run_sound.stop(); is_running_sound_playing = False
                    try: pygame.mixer.music.pause()
                    except: pass
                else:
                    try: pygame.mixer.music.unpause()
                    except: pass

        if event.type == pygame.MOUSEBUTTONDOWN:
            click_time = ticks
            if click_time - last_click_time > 150:
                last_click_time = click_time
                mp = pygame.mouse.get_pos()

                # --- PAUSE MENU TIKLARI ---
                if game_paused:
                    if pause_resume_rect.collidepoint(mp):
                        game_paused = False
                        try: pygame.mixer.music.unpause()
                        except: pass
                    elif pause_restart_rect.collidepoint(mp):
                        game_paused = False
                        reset_game(current_level)
                    elif pause_menu_rect.collidepoint(mp):
                        game_paused = False
                        game_started = False
                        try: pygame.mixer.music.unpause()
                        except: pass

                elif not game_started:
                    if not in_settings and not in_shop and not in_level_select and not in_leaderboard and not in_achievements:
                        if start_button_rect.collidepoint(mp):
                            in_level_select = True
                        elif 'free_play_btn_rect' in dir() and free_play_btn_rect.collidepoint(mp):
                            free_play_mode = True
                            speedrun_mode  = False
                            game_started = True
                            in_level_select = False
                            reset_game(1)
                        elif 'speedrun_btn_rect' in dir() and speedrun_btn_rect.collidepoint(mp):
                            speedrun_mode  = True
                            free_play_mode = False
                            in_level_select = True
                        elif 'daily_btn_rect' in dir() and daily_btn_rect.collidepoint(mp):
                            free_play_mode = False
                            speedrun_mode  = False
                            game_started = True
                            reset_game(daily_level)
                        elif store_button_rect.collidepoint(mp):
                            in_shop = True
                        elif settings_button_rect.collidepoint(mp):
                            in_settings = True
                        elif leaderboard_btn_rect.collidepoint(mp):
                            in_leaderboard = True
                        elif achievements_btn_rect.collidepoint(mp):
                            in_achievements = True
                        elif exit_button_rect.collidepoint(mp):
                            running = False

                    elif in_level_select:
                        if back_button_rect.collidepoint(mp):
                            in_level_select = False
                        else:
                            for lvl, rect in level_rects.items():
                                if rect.collidepoint(mp) and lvl <= unlocked_levels:
                                    game_started = True
                                    in_level_select = False
                                    reset_game(lvl)

                    elif in_settings:
                        if back_button_rect.collidepoint(mp): in_settings = False
                        if music_slider_rect.collidepoint(mp): dragging_music = True
                        elif jump_slider_rect.collidepoint(mp): dragging_jump = True

                    elif in_leaderboard:
                        if back_button_rect.collidepoint(mp): in_leaderboard = False

                    elif in_achievements:
                        if back_button_rect.collidepoint(mp): in_achievements = False

                    elif in_shop:
                        if back_button_rect.collidepoint(mp): in_shop = False
                        if jetpack_rect.collidepoint(mp):
                            if not has_jetpack and total_score >= 100:
                                total_score -= 100; has_jetpack = True
                                if coin_sound: coin_sound.play()
                        for skin, rect in shop_skin_rects.items():
                            if rect.collidepoint(mp):
                                if skin in unlocked_skins:
                                    current_skin = skin; load_player_sprites(skin)
                                elif total_score >= skin_prices[skin]:
                                    total_score -= skin_prices[skin]
                                    unlocked_skins.append(skin)
                                    current_skin = skin; load_player_sprites(skin)
                                    if coin_sound: coin_sound.play()
                                    skins_bought_count += 1
                                    if skins_bought_count >= 3:
                                        unlock_achievement('SHOPAHOLIC')

                else:  # game_started
                    if game_won or game_over:
                        if play_again_btn_rect.collidepoint(mp):
                            reset_game(current_level)
                        elif menu_btn_rect.collidepoint(mp):
                            game_started = False

        if event.type == pygame.MOUSEBUTTONUP:
            dragging_music = dragging_jump = False

        if event.type == pygame.MOUSEMOTION:
            mp = pygame.mouse.get_pos()
            if dragging_music:
                music_volume = max(0.0, min(1.0, (mp[0] - slider_x) / slider_width))
                try: pygame.mixer.music.set_volume(music_volume)
                except: pass
            if dragging_jump:
                jump_volume = max(0.0, min(1.0, (mp[0] - slider_x) / slider_width))
                if jump_sound: jump_sound.set_volume(jump_volume * 0.3)

    # ============================================================
    # MENÜ ÇİZİMİ
    # ============================================================
    if not game_started:
        # ---- LEADERBOARD ----
        if in_leaderboard:
            draw_cosmic_background(screen, menu_mode=True)
            bx, by, bw, bh = 150, 40, 400, 420
            pygame.draw.rect(screen, (10,10,20),  (bx-5, by-5, bw+10, bh+10), border_radius=15)
            pygame.draw.rect(screen, (40,45,70),  (bx, by, bw, bh),           border_radius=15)
            t = title_font.render("LEADERBOARD", True, (245,197,66))
            screen.blit(t, (350 - t.get_width()//2, by+10))
            if not highscores:
                nt = font.render("No scores yet!", True, (180,180,180))
                screen.blit(nt, (350 - nt.get_width()//2, by+100))
            for i, hs in enumerate(highscores):
                row = font.render(f"#{i+1}  Score:{hs['score']}  Time:{hs['time']}s  Lv:{hs['level']}", True, (240,240,240))
                screen.blit(row, (bx+20, by+100 + i*52))
            back_button_rect = pygame.Rect(350-80, by+350, 160, 48)
            draw_button(screen, back_button_rect, "BACK", font, (20,24,46), (200,60,60), (245,197,66), mouse_pos)

        # ---- ACHIEVEMENTS ----
        elif in_achievements:
            draw_cosmic_background(screen, menu_mode=True)
            bx, by, bw, bh = 80, 20, 540, 455
            pygame.draw.rect(screen, (10,10,20), (bx-5, by-5, bw+10, bh+10), border_radius=15)
            pygame.draw.rect(screen, (40,45,70), (bx, by, bw, bh),           border_radius=15)
            t = title_font.render("ACHIEVEMENTS", True, (245,197,66))
            screen.blit(t, (350 - t.get_width()//2, by+10))
            for i, (name, data) in enumerate(achievements.items()):
                color  = (80,255,80) if data['unlocked'] else (120,120,120)
                prefix = "★" if data['unlocked'] else "○"
                row    = small_font.render(f"{prefix} {name}: {data['desc']}  +{data['bonus']}", True, color)
                screen.blit(row, (bx+20, by+80 + i*55))
            back_button_rect = pygame.Rect(350-80, by+395, 160, 48)
            draw_button(screen, back_button_rect, "BACK", font, (20,24,46), (200,60,60), (245,197,66), mouse_pos)

        # ---- LEVEL SELECT ----
        elif in_level_select:
            draw_cosmic_background(screen, menu_mode=True)
            box_w, box_h = 660, 520
            box_x = (700 - box_w)//2; box_y = (500 - box_h)//2
            pygame.draw.rect(screen, (10,10,20), (box_x-5, box_y-5, box_w+10, box_h+10), border_radius=15)
            pygame.draw.rect(screen, (40,45,70), (box_x, box_y, box_w, box_h),           border_radius=15)
            t = title_font.render("SELECT LEVEL", True, (245,197,66))
            screen.blit(t, (350 - t.get_width()//2, box_y-65))
            for txt, oy in [("SEC 1: THE NEBULA",10),("SEC 2: DEEP SPACE",140),("SEC 3: VOID'S EDGE",270),("SEC 4: STARFALL",400)]:
                screen.blit(small_font.render(txt, True, (255,255,255)), (box_x+30, box_y+oy))
            xs     = [50,110,170,230,290,350,410,470,530,590]
            y_bases= [50,180,310,440]
            level_coords = {}
            for sec in range(4):
                for i in range(10):
                    lvl = sec*10+i+1
                    if lvl > 40: break
                    level_coords[lvl] = (xs[i], y_bases[sec] + (25 if i%2==1 else 0))
            for i in range(1, 40):
                if i%10==0: continue
                x1,y1 = level_coords[i]; x2,y2 = level_coords[i+1]
                lc = (245,197,66) if i < unlocked_levels else (100,100,120)
                pygame.draw.line(screen, lc, (box_x+x1, box_y+y1), (box_x+x2, box_y+y2), 6)
            level_rects.clear()
            for i in range(1, 41):
                cx = box_x+level_coords[i][0]; cy = box_y+level_coords[i][1]
                r  = pygame.Rect(cx-20, cy-20, 40, 40)
                level_rects[i] = r
                is_hover     = r.collidepoint(mouse_pos)
                is_unlocked  = i <= unlocked_levels
                is_boss      = (i % 10 == 0)
                if is_unlocked:
                    if is_boss:
                        bg_col  = (220,60,60) if is_hover else (160,30,30)
                        bd_col  = (255,100,100)
                    elif i == unlocked_levels:
                        bg_col  = (245,197,66) if is_hover else (200,150,40)
                        bd_col  = (255,255,255)
                    else:
                        bg_col  = (60,180,120) if is_hover else (40,140,90)
                        bd_col  = (245,197,66)
                else:
                    bg_col = (60,60,75); bd_col = (40,40,50)
                pygame.draw.rect(screen, bd_col, (cx-23, cy-23, 46, 46), border_radius=23)
                pygame.draw.rect(screen, bg_col, r, border_radius=20)
                if is_unlocked:
                    lt = small_font.render(str(i), True, (255,255,255))
                    screen.blit(lt, (cx - lt.get_width()//2, cy - lt.get_height()//2))
                    if is_boss:
                        bt = small_font.render("B", True, (255,220,0))
                        screen.blit(bt, (cx+10, cy-22))
                    # Yıldızlar
                    stars_earned = level_stars.get(i, 0)
                    for si in range(3):
                        sc2 = (245,197,66) if si < stars_earned else (60,60,80)
                        pygame.draw.circle(screen, sc2, (cx-10+si*10, cy+18), 4)
                else:
                    pygame.draw.rect(screen, (200,200,200), (cx-8, cy-2, 16, 12), border_radius=3)
                    pygame.draw.circle(screen, (200,200,200), (cx, cy-2), 6, 2)
            bk_x = 350-80; bk_y = box_y+470
            back_button_rect = pygame.Rect(bk_x, bk_y, 160, 50)
            draw_button(screen, back_button_rect, "BACK", font, (20,24,46), (200,60,60), (245,197,66), mouse_pos)

        # ---- SETTINGS ----
        elif in_settings:
            draw_cosmic_background(screen, menu_mode=True)
            bx = (700-500)//2; by = (500-440)//2
            pygame.draw.rect(screen, (10,10,20), (bx-5, by-5, 510, 450), border_radius=15)
            pygame.draw.rect(screen, (40,45,70), (bx, by, 500, 440),     border_radius=15)
            t = title_font.render("SETTINGS", True, (245,197,66))
            screen.blit(t, (350 - t.get_width()//2, by+20))
            sh = 8
            # Müzik slider
            mt = font.render(f"MUSIC SOUND: %{int(music_volume*100)}", True, (240,240,240))
            screen.blit(mt, (350 - mt.get_width()//2, by+110))
            msy = by+160
            music_slider_rect = pygame.Rect(slider_x-10, msy-10, slider_width+20, sh+20)
            pygame.draw.rect(screen, (20,24,46),    (slider_x, msy, slider_width, sh), border_radius=4)
            pygame.draw.rect(screen, (245,197,66),  (slider_x, msy, int(slider_width*music_volume), sh), border_radius=4)
            pygame.draw.circle(screen, (255,255,255), (slider_x+int(slider_width*music_volume), msy+sh//2), 12)
            # Zıplama slider
            jt = font.render(f"JUMP SOUND: %{int(jump_volume*100)}", True, (240,240,240))
            screen.blit(jt, (350 - jt.get_width()//2, by+210))
            jsy = by+260
            jump_slider_rect = pygame.Rect(slider_x-10, jsy-10, slider_width+20, sh+20)
            pygame.draw.rect(screen, (20,24,46),   (slider_x, jsy, slider_width, sh), border_radius=4)
            pygame.draw.rect(screen, (60,180,120), (slider_x, jsy, int(slider_width*jump_volume), sh), border_radius=4)
            pygame.draw.circle(screen, (255,255,255), (slider_x+int(slider_width*jump_volume), jsy+sh//2), 12)
            # Kontroller bilgisi
            ctrl_y = by+310
            screen.blit(small_font.render("CONTROLS: ARROWS=Move  SPACE=Jump  LSHIFT=Dash  ESC=Pause", True, (180,220,255)), (bx+10, ctrl_y))
            back_button_rect = pygame.Rect(350-80, by+370, 160, 50)
            draw_button(screen, back_button_rect, "BACK", font, (20,24,46), (200,60,60), (245,197,66), mouse_pos)

        # ---- SHOP ----
        elif in_shop:
            draw_cosmic_background(screen, menu_mode=True)
            bx = (700-500)//2; by = (500-440)//2
            pygame.draw.rect(screen, (10,10,20), (bx-5, by-5, 510, 450), border_radius=15)
            pygame.draw.rect(screen, (40,45,70), (bx, by, 500, 440),     border_radius=15)
            t = title_font.render("STORE", True, (245,197,66))
            screen.blit(t, (350 - t.get_width()//2, by+15))
            ct = font.render(f"YOUR COINS: {total_score}", True, (255,255,255))
            screen.blit(ct, (350 - ct.get_width()//2, by+65))
            sy = by+105
            shop_skin_rects.clear()
            for i, (sn, color) in enumerate(skin_colors.items()):
                row = i//2; col = i%2
                sx  = bx+35+col*220; ssy = sy+row*60
                br  = pygame.Rect(sx, ssy, 200, 45)
                shop_skin_rects[sn] = br
                ih  = br.collidepoint(mouse_pos)
                bc  = color if ih else (30,34,56)
                tc  = (255,255,255) if ih else color
                pygame.draw.rect(screen, color, (sx-2, ssy-2, 204, 49), border_radius=8)
                pygame.draw.rect(screen, bc, br, border_radius=8)
                if current_skin == sn:
                    pygame.draw.rect(screen, (255,255,255), (sx-3, ssy-3, 206, 51), 3, border_radius=10)
                    st = "EQUIPPED"
                elif sn in unlocked_skins:
                    st = "OWNED"
                else:
                    st = f"{skin_prices[sn]} C"
                screen.blit(small_font.render(sn, True, tc), (sx+10, ssy+(45-small_font.get_height())//2))
                screen.blit(small_font.render(st, True, tc), (sx+190-small_font.size(st)[0], ssy+(45-small_font.get_height())//2))
            jy = sy+3*60
            jetpack_rect = pygame.Rect(bx+35, jy, 420, 45)
            jh  = jetpack_rect.collidepoint(mouse_pos)
            jc  = (255,120,30)
            jbc = jc if jh else (30,34,56)
            jtc = (255,255,255) if jh else jc
            pygame.draw.rect(screen, jc,  (bx+33, jy-2, 424, 49), border_radius=8)
            pygame.draw.rect(screen, jbc, jetpack_rect, border_radius=8)
            jst = "OWNED" if has_jetpack else "100 C"
            screen.blit(small_font.render("JETPACK (Hold SPACE to Fly)", True, jtc), (bx+45, jy+(45-small_font.get_height())//2))
            screen.blit(small_font.render(jst, True, jtc), (bx+445-small_font.size(jst)[0], jy+(45-small_font.get_height())//2))
            back_button_rect = pygame.Rect(350-80, by+365, 160, 50)
            draw_button(screen, back_button_rect, "BACK", font, (20,24,46), (200,60,60), (245,197,66), mouse_pos)

        # ---- ANA MENÜ ----
        else:
            draw_cosmic_background(screen, menu_mode=True)
            t = title_font.render("SKY HOPPER", True, (245,197,66))
            screen.blit(t, (350 - t.get_width()//2, 12))
            st = font.render(f"TOTAL SCORE: {total_score}", True, (255,255,255))
            screen.blit(st, (350 - st.get_width()//2, 75))

            # Today's Level - sağ üst köşe
            dc_corner = small_font.render(
                f"Today: Lv.{daily_level}" + (" ✓" if daily_done else ""),
                True, (80,255,80) if daily_done else (255,220,100))
            screen.blit(dc_corner, (GAME_WIDTH - dc_corner.get_width() - 8, 8))

            # --- 2 SÜTUN BUTON DÜZENİ ---
            bw, bh = 270, 42
            col1_x = 350 - bw - 14
            col2_x = 350 + 14
            start_y = 110
            gap     = 56

            # (label, renk, sütun 0=sol 1=sağ, satır)
            grid = [
                ("START GAME",      (60,180,120),  0, 0),
                ("FREE PLAY",       (50,180,180),  1, 0),
                ("SPEEDRUN",        (255,180,0),   0, 1),
                ("DAILY CHALLENGE", (200,80,200),  1, 1),
                ("STORE",           (150,50,200),  0, 2),
                ("SETTINGS",        (180,120,60),  1, 2),
                ("LEADERBOARD",     (50,100,200),  0, 3),
                ("ACHIEVEMENTS",    (80,180,80),   1, 3),
            ]

            btn_map = {}
            for label, color, col, row in grid:
                rx = col1_x if col == 0 else col2_x
                ry = start_y + row * gap
                r  = pygame.Rect(rx, ry, bw, bh)
                draw_button(screen, r, label, font, (20,24,46), color, (245,197,66), mouse_pos)
                btn_map[label] = r

            start_button_rect     = btn_map["START GAME"]
            free_play_btn_rect    = btn_map["FREE PLAY"]
            speedrun_btn_rect     = btn_map["SPEEDRUN"]
            daily_btn_rect        = btn_map["DAILY CHALLENGE"]
            store_button_rect     = btn_map["STORE"]
            settings_button_rect  = btn_map["SETTINGS"]
            leaderboard_btn_rect  = btn_map["LEADERBOARD"]
            achievements_btn_rect = btn_map["ACHIEVEMENTS"]

            # EXIT - ortada altta
            exit_button_rect = pygame.Rect(350-120, start_y + 4*gap + 6, 240, 42)
            draw_button(screen, exit_button_rect, "EXIT", font, (20,24,46), (200,60,60), (245,197,66), mouse_pos)

    # ============================================================
    # OYUN İÇİ (game_started)
    # ============================================================
    else:
        if not game_won and not game_over and not game_paused:
            # --- ZAMAN ---
            elapsed = (ticks - level_time_start) / 1000.0
            time_limit = get_time_limit(current_level)
            remaining  = max(0.0, time_limit - elapsed) if not free_play_mode else 999.0
            current_time = elapsed

            # Süre doldu → game over (free play'de değil)
            if not free_play_mode and remaining <= 0:
                game_over = True
                finish_time = elapsed
                screen_shake = 20
                try: pygame.mixer.music.stop()
                except: pass
                if run_sound: run_sound.stop(); is_running_sound_playing = False
                if game_over_sound: game_over_sound.play()

            # --- HAREKETLİ PLATFORMLAR ---
            for m_data in current_moving_data:
                mp_ = platforms[m_data['idx']]
                mv  = platform_speed * m_data['dir']
                mp_.x += mv
                if current_level == 1 and m_data['idx'] == 5:
                    door_rect.x += mv
                    if coins:
                        min(coins, key=lambda c: c.y).x += mv
                if mp_.right > m_data['max'] or mp_.left < m_data['min']:
                    m_data['dir'] *= -1
                    mp_.x += platform_speed * m_data['dir']
                    continue
                for oi, op in enumerate(platforms):
                    if oi != m_data['idx'] and mp_.colliderect(op):
                        m_data['dir'] *= -1
                        mp_.x += platform_speed * m_data['dir']
                        break

            # --- BOSS HAREKETİ ---
            if boss_enemy:
                be = boss_enemy
                be['rect'].x += be['speed'] * be['dir']
                if be['rect'].right > be['max'] or be['rect'].left < be['min']:
                    be['dir'] *= -1
                # Boss parçacıkları
                if random.random() < 0.3:
                    boss_particles.append(Particle(
                        be['rect'].centerx + random.randint(-30,30),
                        be['rect'].centery + random.randint(-20,20),
                        (220, 50+random.randint(0,50), 30), 3, 1))
                if show_boss_warning > 0:
                    show_boss_warning -= 1

            # --- POWER-UP ZAMANLAYICI ---
            for k in list(active_powerups.keys()):
                v = active_powerups[k]
                if isinstance(v, int):
                    active_powerups[k] -= 1
                    if active_powerups[k] <= 0:
                        del active_powerups[k]

            speed_now = int(speed * 1.5) if 'SPEED' in active_powerups else speed

            # --- GRAVITY FLIP ZAMANLAYICI ---
            real_gravity = -gravity if gravity_flipped else gravity
            if gravity_flip_timer > 0:
                gravity_flip_timer -= 1
                if gravity_flip_timer == 0:
                    gravity_flipped = False

            # --- HAREKETLİ HAZARDLAR ---
            for mh in moving_hazards:
                mh['rect'].x += mh['speed'] * mh['dir']
                if mh['rect'].right > mh['max'] or mh['rect'].left < mh['min']:
                    mh['dir'] *= -1

            # --- SPEEDRUN ZAMANLAYICI ---
            if speedrun_mode:
                speedrun_time = elapsed

            # --- TUTORIAL HİNT ---
            if current_level in tutorial_hints and current_level not in tutorial_shown:
                hints = tutorial_hints[current_level]
                hint_idx = min(int(elapsed * 0.5), len(hints)-1)
                tutorial_active_hint = hints[hint_idx]
                if elapsed > len(hints) * 2 + 2:
                    tutorial_shown.add(current_level)
                    tutorial_active_hint = ""

            # --- WALL JUMP ZAMANLAYICI ---
            if wall_jump_timer > 0:
                wall_jump_timer -= 1

            # --- KLAVYE / FİZİK ---
            is_moving = False; moving_backwards = False
            keys = pygame.key.get_pressed()
            can_move = not is_door_opening and transition_state == 0

            if dash_cooldown > 0: dash_cooldown -= 1
            if dash_duration > 0:
                is_dashing = True; dash_duration -= 1
                player.x += dash_speed if facing_right else -dash_speed
                vel_y = 0
                if has_sprites and dash_duration % 2 == 0:
                    ghost_trails.append({"x": player.x, "y": player.y, "frame": animation_frame, "facing": facing_right, "alpha": 150})
            else:
                is_dashing = False

            if can_move and not is_dashing:
                if has_jetpack and keys[pygame.K_SPACE] and jetpack_fuel > 0:
                    jetpack_fuel -= 1; vel_y -= 1.6
                    if vel_y < -7: vel_y = -7
                    on_ground = False
                    spawn_particles(player.centerx, player.bottom, (255,120,30), 2, 4, 3)
                    spawn_particles(player.centerx, player.bottom, (200,200,200), 1, 3, 1)
                if keys[pygame.K_LSHIFT] and dash_cooldown == 0:
                    dash_duration = 10; dash_cooldown = 40
                    if jump_sound: jump_sound.play()
                    spawn_particles(player.centerx, player.centery, (100,200,255), 15, 6, 4)
                if keys[pygame.K_LEFT]:
                    player.x -= speed_now; facing_right = False; is_moving = True; moving_backwards = True
                if keys[pygame.K_RIGHT]:
                    player.x += speed_now; facing_right = True;  is_moving = True
                if keys[pygame.K_SPACE]:
                    if not space_pressed:
                        if on_ground:
                            vel_y = -15
                            if jump_sound: jump_sound.play()
                            can_double_jump = True
                            spawn_particles(player.centerx, player.bottom, (255,255,255), 8)
                        elif touching_wall_dir != 0 and wall_jump_timer == 0:
                            # WALL JUMP
                            vel_y = -14
                            player.x += -touching_wall_dir * 60
                            wall_jump_timer = 20
                            if jump_sound: jump_sound.play()
                            spawn_particles(player.centerx, player.centery, (100,255,200), 12)
                        elif 'EXTRA_JUMP' in active_powerups:
                            vel_y = -22
                            del active_powerups['EXTRA_JUMP']
                            if jump_sound: jump_sound.play()
                            spawn_particles(player.centerx, player.bottom, (180,80,255), 15)
                        elif can_double_jump and not has_jetpack:
                            vel_y = -15
                            if jump_sound: jump_sound.play()
                            can_double_jump = False
                            spawn_particles(player.centerx, player.bottom, (150,200,255), 12)
                        space_pressed = True
                else:
                    space_pressed = False
            elif not can_move:
                space_pressed = False
                if not game_over and not game_won and (is_door_opening or transition_state == 1):
                    diff = door_rect.centerx - player.centerx
                    if abs(diff) > 2:
                        if diff > 0: player.x += 2; facing_right = True
                        else:        player.x -= 2; facing_right = False
                        is_moving = True
                    else:
                        player.centerx = door_rect.centerx

            if player.left < 0:   player.left = 0
            if player.right > 700: player.right = 700
            if player.top < 0:    player.top = 0; vel_y = 0

            if not is_dashing:
                vel_y += real_gravity
                player.y += vel_y

            was_on_ground = on_ground; on_ground = False
            player_on_moving = False; moving_dx = 0
            touching_wall_dir = 0

            for i, p in enumerate(platforms):
                if player.colliderect(p) and p.left < player.centerx < p.right:
                    if (vel_y > 0 and not gravity_flipped) or (vel_y < 0 and gravity_flipped):
                        if not is_dashing:
                            player.bottom = p.top; vel_y = 0; on_ground = True; can_double_jump = True
                            jetpack_fuel = max_jetpack_fuel
                            if not was_on_ground:
                                if land_sound: land_sound.play()
                                screen_shake = 5
                                spawn_particles(player.centerx, player.bottom, (200,200,200), 10, 3, 3)
                            for m in current_moving_data:
                                if i == m['idx']:
                                    player_on_moving = True; moving_dx = platform_speed * m['dir']
                    elif (vel_y < 0 and not gravity_flipped) or (vel_y > 0 and gravity_flipped):
                        if not is_dashing:
                            player.top = p.bottom; vel_y = 0
                # Yan çarpışma - wall jump için
                if not on_ground and not is_dashing:
                    if (player.right >= p.left and player.left < p.left and
                            player.bottom > p.top + 5 and player.top < p.bottom - 5):
                        touching_wall_dir = 1  # sağ duvar
                    elif (player.left <= p.right and player.right > p.right and
                            player.bottom > p.top + 5 and player.top < p.bottom - 5):
                        touching_wall_dir = -1  # sol duvar

            if player_on_moving: player.x += moving_dx

            # --- RUNNING SES ---
            if is_moving and on_ground:
                if run_sound and not is_running_sound_playing:
                    run_sound.play(-1); is_running_sound_playing = True
            else:
                if run_sound and is_running_sound_playing:
                    run_sound.stop(); is_running_sound_playing = False

            # --- COİN TOPLAMA ---
            initial_coin_count = len(coins)
            # MAGNET: yakındaki coinleri çek
            if 'MAGNET' in active_powerups:
                for coin in coins:
                    dx = player.centerx - coin.centerx
                    dy = player.centery  - coin.centery
                    dist = max(1, math.sqrt(dx*dx + dy*dy))
                    if dist < 180:
                        coin.x += int(dx / dist * 4)
                        coin.y += int(dy / dist * 4)
            for coin in coins[:]:
                if player.colliderect(coin):
                    coins.remove(coin); score += 1; total_score += 1
                    if coin_sound: coin_sound.play()
                    spawn_sparkle(coin.centerx, coin.centery)
                    # Coin trail animasyonu - coin ekrana uçar
                    coin_trail.append({
                        'x': float(coin.centerx), 'y': float(coin.centery),
                        'tx': 680.0, 'ty': 14.0,  # HUD'daki coins pozisyonu
                        'life': 30, 'size': 8
                    })
                    break

            # Coin trail güncelle
            for ct in coin_trail[:]:
                ct['x'] += (ct['tx'] - ct['x']) * 0.18
                ct['y'] += (ct['ty'] - ct['y']) * 0.18
                ct['life'] -= 1
                ct['size'] = max(2, ct['size'] - 0.2)
                if ct['life'] <= 0:
                    coin_trail.remove(ct)

            # --- HAZARD ÇARPIŞMA (sabit + hareketli) ---
            all_hazards = hazards + [mh['rect'] for mh in moving_hazards]
            for h in all_hazards:
                if player.colliderect(h):
                    if 'SHIELD' in active_powerups:
                        del active_powerups['SHIELD']
                        spawn_explosion(player.centerx, player.centery, (50,150,255))
                    elif respawn_timer == 0 and death_anim_timer == 0:
                        hazard_touched_this_level = True
                        player_lives -= 1
                        spawn_explosion(player.centerx, player.centery, (255,80,80))
                        screen_shake = 12
                        if player_lives <= 0:
                            game_over = True; finish_time = current_time
                            try: pygame.mixer.music.stop()
                            except: pass
                            if run_sound: run_sound.stop(); is_running_sound_playing = False
                            if game_over_sound: game_over_sound.play()
                        else:
                            death_anim_timer = 40
                    break

            # --- BOSS ÇARPIŞMA ---
            if boss_enemy and player.colliderect(boss_enemy['rect']):
                if 'SHIELD' in active_powerups:
                    del active_powerups['SHIELD']
                    spawn_explosion(player.centerx, player.centery, (50,150,255))
                elif respawn_timer == 0 and death_anim_timer == 0:
                    player_lives -= 1
                    spawn_explosion(boss_enemy['rect'].centerx, boss_enemy['rect'].centery, (255,40,40))
                    screen_shake = 15
                    if player_lives <= 0:
                        game_over = True; finish_time = current_time
                        try: pygame.mixer.music.stop()
                        except: pass
                        if run_sound: run_sound.stop(); is_running_sound_playing = False
                        if game_over_sound: game_over_sound.play()
                    else:
                        death_anim_timer = 40

            # --- ÖLÜM ANİMASYONU / RESPAWN ---
            if death_anim_timer > 0:
                death_anim_timer -= 1
                if death_anim_timer == 0:
                    # Checkpoint'e veya başlangıca respawn
                    if checkpoint_reached and checkpoint_rect:
                        player.x = checkpoint_player_x
                        player.y = checkpoint_player_y
                    else:
                        player.x = 60; player.y = 260
                    vel_y = 0
                    respawn_timer = 90  # 1.5 sn yanıp söner

            if respawn_timer > 0:
                respawn_timer -= 1

            # --- POWER-UP TOPLAMA ---
            for pu in powerups[:]:
                if player.colliderect(pu['rect']):
                    powerups.remove(pu)
                    pt = pu['type']
                    if pt == 'SHIELD':
                        active_powerups['SHIELD'] = 5 * 60
                    elif pt == 'SPEED':
                        active_powerups['SPEED'] = 5 * 60
                    elif pt == 'EXTRA_JUMP':
                        active_powerups['EXTRA_JUMP'] = True
                    elif pt == 'MAGNET':
                        active_powerups['MAGNET'] = 8 * 60
                    elif pt == 'GRAVITY':
                        gravity_flipped    = not gravity_flipped
                        gravity_flip_timer = 6 * 60
                    if coin_sound: coin_sound.play()
                    spawn_sparkle(pu['rect'].centerx, pu['rect'].centery)
                    break

            # --- CHECKPOINT TOPLAMA ---
            if checkpoint_rect and not checkpoint_reached and player.colliderect(checkpoint_rect):
                checkpoint_reached = True
                spawn_sparkle(checkpoint_rect.centerx, checkpoint_rect.centery)
                if coin_sound: coin_sound.play()

            # --- DÜŞME ---
            if player.top > 500:
                if 'SHIELD' in active_powerups:
                    del active_powerups['SHIELD']
                    player.x = 60; player.y = 260; vel_y = 0
                    spawn_explosion(player.centerx, player.centery, (50,150,255))
                elif respawn_timer == 0 and death_anim_timer == 0:
                    player_lives -= 1
                    screen_shake = 15
                    if player_lives <= 0:
                        game_over = True; finish_time = current_time
                        try: pygame.mixer.music.stop()
                        except: pass
                        if run_sound: run_sound.stop(); is_running_sound_playing = False
                        if game_over_sound: game_over_sound.play()
                    else:
                        death_anim_timer = 40

            # --- KAPI AÇILMA ---
            if len(coins) == 0 and player.colliderect(door_rect) and not is_door_opening and transition_state == 0:
                is_door_opening = True; door_anim_index = 3; door_anim_timer = 0
                if door_sound: door_sound.play()

            if is_door_opening:
                door_anim_timer += 1
                if door_anim_timer > 8:
                    door_anim_timer = 0
                    if door_anim_index > 0:
                        door_anim_index -= 1
                    else:
                        is_door_opening = False; door_anim_index = 3
                        # --- BAŞARI KONTROLLERI ---
                        if not hazard_touched_this_level:
                            unlock_achievement('UNTOUCHABLE')
                        if initial_coin_count > 0 and score >= initial_coin_count:
                            unlock_achievement('COIN MASTER')
                        if current_time < 15:
                            unlock_achievement('SPEED RUNNER')
                        if current_level == 10:
                            unlock_achievement('LEVEL 10')
                        if current_level == 20:
                            unlock_achievement('LEVEL 20')
                        # Yıldız hesapla ve kaydet
                        stars = calc_stars(current_time, score, initial_coin_count, player_lives)
                        if current_level not in level_stars or level_stars[current_level] < stars:
                            level_stars[current_level] = stars
                        # Speedrun best kaydet
                        if speedrun_mode:
                            if current_level not in speedrun_best or speedrun_time < speedrun_best[current_level]:
                                speedrun_best[current_level] = speedrun_time
                        # Daily tamamlandı mı?
                        if current_level == daily_level:
                            daily_done = True
                        # Zaman bonusu
                        time_bonus = int(remaining * 5) if not free_play_mode else 0
                        if time_bonus > 0:
                            total_score += time_bonus; score += time_bonus
                            spawn_sparkle(player.centerx, player.centery - 20)
                        # Leaderboard
                        add_highscore(total_score, current_time, current_level)

                        if current_level < 40:
                            transition_state = 1
                            spawn_fireworks(GAME_WIDTH, GAME_HEIGHT)
                        elif current_level == 40:
                            game_won = True; finish_time = current_time
                            if best_time == 0 or finish_time < best_time: best_time = finish_time
                            try: pygame.mixer.music.stop()
                            except: pass
                            if run_sound: run_sound.stop(); is_running_sound_playing = False

            # --- KAMERA ---
            tcx = max(-80, min(80, player.centerx - 350))
            tcy = max(-80, min(80, player.centery  - 250))
            cam_x += (tcx - cam_x) * 0.1
            cam_y += (tcy - cam_y) * 0.1
            shake_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
            shake_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
            draw_ox = int(cam_x) + shake_x
            draw_oy = int(cam_y) + shake_y
            if screen_shake > 0: screen_shake -= 1

        # ============================================================
        # ÇİZİM - GAME OVER / WIN
        # ============================================================
        if game_won or game_over:
            screen.fill((30, 34, 56))
            ebw, ebh = 400, 380
            ebx = (700-ebw)//2; eby = (500-ebh)//2
            pygame.draw.rect(screen, (10,10,20), (ebx-5, eby-5, ebw+10, ebh+10), border_radius=15)
            pygame.draw.rect(screen, (20,24,46), (ebx, eby, ebw, ebh),           border_radius=15)
            wlt = title_font.render('YOU WIN!' if game_won else 'GAME OVER!', True,
                                    (120,255,160) if game_won else (255,100,100))
            screen.blit(wlt, (ebx+(ebw-wlt.get_width())//2, eby+30))
            # Yıldızlar
            if game_won:
                finished_stars = level_stars.get(current_level, 0)
                for si in range(3):
                    sc3 = (245,197,66) if si < finished_stars else (60,60,80)
                    star_r = 18
                    sx3 = ebx + ebw//2 - 40 + si*40
                    sy3 = eby + 95
                    pygame.draw.circle(screen, sc3, (sx3, sy3), star_r)
                    st3 = font.render("★", True, (20,20,30) if si < finished_stars else (40,40,60))
                    screen.blit(st3, (sx3-st3.get_width()//2, sy3-st3.get_height()//2))
            ty = eby+125
            for txt in [f'Time: {round(finish_time,1)}s', f'Session Coins: {score}',
                        f'Best: {round(best_time,1)}s' if best_time > 0 else 'Best: --']:
                rt = font.render(txt, True, (240,240,240))
                screen.blit(rt, (ebx+(ebw-rt.get_width())//2, ty)); ty += 40
            bw2 = 220; bh2 = 50
            play_again_btn_rect = pygame.Rect(ebx+(ebw-bw2)//2, eby+240, bw2, bh2)
            menu_btn_rect       = pygame.Rect(ebx+(ebw-bw2)//2, eby+310, bw2, bh2)
            draw_button(screen, play_again_btn_rect, "PLAY AGAIN", font, (20,24,46), (60,180,120),  (245,197,66), mouse_pos)
            draw_button(screen, menu_btn_rect,       "MAIN MENU",  font, (20,24,46), (180,120,60),  (245,197,66), mouse_pos)
            # Fireworks
            for p in particles[:]:
                p.x += p.vx; p.y += p.vy; p.life -= p.decay
                if p.life <= 0: particles.remove(p); continue
                ps = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
                pygame.draw.circle(ps, p.color+(p.life,), (p.size//2,p.size//2), p.size//2)
                screen.blit(ps, (int(p.x), int(p.y)))

        # ============================================================
        # ÇİZİM - OYUN İÇİ
        # ============================================================
        else:
            draw_cosmic_background(screen, draw_ox, draw_oy, menu_mode=False)

            # KAPI
            if door_frames:
                screen.blit(door_frames[door_anim_index], (door_rect.x-draw_ox, door_rect.y-draw_oy))
            else:
                pygame.draw.rect(screen, (80,80,80), (door_rect.x-draw_ox, door_rect.y-draw_oy, 80, 80))

            # PLATFORMLAR
            moving_indices = [m['idx'] for m in current_moving_data]
            for i, p in enumerate(platforms):
                img = moving_platform_img if i in moving_indices else platform_img
                if img:
                    screen.blit(pygame.transform.scale(img, (p.width, p.height)), (p.x-draw_ox, p.y-draw_oy))
                else:
                    color = (140,90,140) if i in moving_indices else (90,120,90)
                    pygame.draw.rect(screen, color, (p.x-draw_ox, p.y-draw_oy, p.width, p.height))

            # HAZARDS (sabit - animasyonlu ateş rengi)
            ht  = ticks * 0.005
            for h in hazards:
                pulse = int(abs(math.sin(ht)) * 55)
                hc    = (min(255, 180+pulse), min(255, 30+pulse//4), 0)
                pygame.draw.rect(screen, hc, (h.x-draw_ox, h.y-draw_oy, h.width, h.height), border_radius=3)
                pygame.draw.rect(screen, (255, 180, 0), (h.x-draw_ox, h.y-draw_oy, h.width, h.height), 2, border_radius=3)
                if random.random() < 0.15:
                    spawn_particles(h.x+random.randint(0,max(1,h.width)),
                                    h.y+draw_oy-draw_oy, (255,120,0), 1, 2, 1)

            # HAREKETLİ HAZARDLAR (daha parlak, titreşimli)
            for mh in moving_hazards:
                r2 = mh['rect']
                pulse2 = int(abs(math.sin(ht * 1.5)) * 55)
                hc2 = (min(255, 200+pulse2), min(255, 60+pulse2//3), 0)
                pygame.draw.rect(screen, hc2, (r2.x-draw_ox, r2.y-draw_oy, r2.width, r2.height), border_radius=4)
                pygame.draw.rect(screen, (255, 230, 50), (r2.x-draw_ox, r2.y-draw_oy, r2.width, r2.height), 2, border_radius=4)
                # ok işareti
                ax = r2.centerx - draw_ox
                ay = r2.centery - draw_oy
                pygame.draw.polygon(screen, (255,255,100), [
                    (ax + mh['dir']*12, ay),
                    (ax + mh['dir']*4,  ay-5),
                    (ax + mh['dir']*4,  ay+5),
                ])

            # BOSS
            if boss_enemy:
                be = boss_enemy
                bex = be['rect'].x - draw_ox; bey = be['rect'].y - draw_oy
                bp  = int(abs(math.sin(ht*1.5)) * 60)
                pygame.draw.rect(screen, (160+bp, 20, 20), (bex, bey, be['rect'].w, be['rect'].h), border_radius=8)
                pygame.draw.rect(screen, (255, 80, 80),    (bex, bey, be['rect'].w, be['rect'].h), 3, border_radius=8)
                bl = small_font.render("BOSS", True, (255,220,0))
                screen.blit(bl, (bex + be['rect'].w//2 - bl.get_width()//2, bey - 22))
                if show_boss_warning > 0:
                    wt = big_font.render("⚠ BOSS LEVEL ⚠", True, (255,60,60))
                    screen.blit(wt, (350-wt.get_width()//2, 200))

            # BOSS PARÇACIKLARI
            for bp2 in boss_particles[:]:
                bp2.x += bp2.vx; bp2.y += bp2.vy; bp2.life -= bp2.decay
                if bp2.life <= 0: boss_particles.remove(bp2); continue
                bs = pygame.Surface((bp2.size, bp2.size), pygame.SRCALPHA)
                pygame.draw.circle(bs, bp2.color+(bp2.life,), (bp2.size//2, bp2.size//2), bp2.size//2)
                screen.blit(bs, (int(bp2.x)-draw_ox, int(bp2.y)-draw_oy))

            # COİNLER
            for coin in coins:
                ct2 = ticks * 0.004
                cr  = int(abs(math.sin(ct2 + coin.x * 0.01)) * 3)
                pygame.draw.ellipse(screen, (245,197,66),  (coin.x-draw_ox,   coin.y-draw_oy-cr,   coin.width,   coin.height+cr))
                pygame.draw.ellipse(screen, (255,255,150), (coin.x-draw_ox+4, coin.y-draw_oy+4-cr, coin.width-8, coin.height-8+cr))

            # POWER-UPLAR
            for pu in powerups:
                pu['angle'] = (pu['angle'] + 2) % 360
                pc    = POWERUP_COLORS.get(pu['type'], (255,255,255))
                pr    = pu['rect']
                alpha = 150 + int(abs(math.sin(ticks*0.005)) * 100)
                ps    = pygame.Surface((pr.w+10, pr.h+10), pygame.SRCALPHA)
                pygame.draw.circle(ps, pc+(alpha,), (pr.w//2+5, pr.h//2+5), pr.w//2+4)
                screen.blit(ps, (pr.x-draw_ox-5, pr.y-draw_oy-5))
                pygame.draw.circle(screen, pc, (pr.centerx-draw_ox, pr.centery-draw_oy), pr.w//2)
                lt = small_font.render(pu['type'][0], True, (255,255,255))
                screen.blit(lt, (pr.centerx-draw_ox-lt.get_width()//2, pr.centery-draw_oy-lt.get_height()//2))

            # GHOST TRAILS
            for trail in ghost_trails[:]:
                if has_sprites:
                    ts = run_frames[trail["frame"] % len(run_frames)]
                    if not trail["facing"]: ts = pygame.transform.flip(ts, True, False)
                    tc2 = ts.copy(); tc2.set_alpha(trail["alpha"])
                    screen.blit(tc2, (trail["x"]-draw_ox, trail["y"]+3-draw_oy))
                trail["alpha"] -= 15
                if trail["alpha"] <= 0: ghost_trails.remove(trail)

            # PLAYER ANİMASYON
            if has_sprites:
                animation_timer += 1
                if not on_ground:
                    current_set = jump_frames
                    animation_frame = (0 if vel_y < -5 else 1 if vel_y < 0 else 2 if vel_y < 5 else 3)
                elif is_moving:
                    current_set = back_frames if moving_backwards else run_frames
                    if animation_timer >= (4 if is_dashing else 6):
                        animation_frame = (animation_frame+1) % len(current_set); animation_timer = 0
                else:
                    current_set = idle_frames
                    if animation_timer >= 10:
                        animation_frame = (animation_frame+1) % len(current_set); animation_timer = 0
                    if animation_frame >= len(current_set): animation_frame = 0
                if not is_moving and on_ground: animation_frame = 0
                else: animation_frame = animation_frame % len(current_set)
                asp = current_set[animation_frame]
                if not facing_right: asp = pygame.transform.flip(asp, True, False)
                screen.blit(asp, (player.x-draw_ox, player.y+3-draw_oy))
            else:
                pygame.draw.rect(screen, (80,170,230), (player.x-draw_ox, player.y-draw_oy, player.width, player.height))

            # SHIELD HALKASI
            if 'SHIELD' in active_powerups:
                ss = pygame.Surface((80, 80), pygame.SRCALPHA)
                alpha_s = 100 + int(abs(math.sin(ticks*0.006)) * 100)
                pygame.draw.circle(ss, (50,150,255,alpha_s), (40,40), 38, 3)
                screen.blit(ss, (player.centerx-draw_ox-40, player.centery-draw_oy-40))

            # PARTİKÜLLER
            for p in particles[:]:
                p.x += p.vx; p.y += p.vy; p.life -= p.decay
                if p.life <= 0: particles.remove(p); continue
                ps = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
                pygame.draw.circle(ps, p.color+(p.life,), (p.size//2, p.size//2), p.size//2)
                screen.blit(ps, (int(p.x)-draw_ox, int(p.y)-draw_oy))

            # HUD
            screen.blit(hud_font.render(f'Coins: {score}',            True, (240,240,240)), (10,  10))
            screen.blit(hud_font.render(f'Level: {current_level}/40', True, (240,240,240)), (160, 10))
            if best_time > 0:
                screen.blit(hud_font.render(f'Best: {round(best_time,1)}s', True, (245,197,66)), (450, 10))
            # Geri sayım
            time_color = (255,80,80) if (not free_play_mode and remaining <= 10) else (240,240,240)
            time_txt = "FREE" if free_play_mode else f'Time: {int(remaining)}s'
            screen.blit(hud_font.render(time_txt, True, time_color), (300, 10))
            # CANLAR (kalp ikonu)
            for li in range(max_lives):
                hc2 = (220,50,50) if li < player_lives else (60,60,80)
                pygame.draw.circle(screen, hc2, (640 + li*22, 14), 8)
            # Jetpack fuel
            if has_jetpack:
                fr = jetpack_fuel / max_jetpack_fuel
                pygame.draw.rect(screen, (40,40,50),   (10, 45, 100, 10), border_radius=4)
                pygame.draw.rect(screen, (255,120,30), (10, 45, int(100*fr), 10), border_radius=4)
                pygame.draw.rect(screen, (255,255,255),(10, 45, 100, 10), 1, border_radius=4)
            # Power-up HUD
            draw_powerup_hud(screen)

            # CHECKPOINT çiz
            if checkpoint_rect and not checkpoint_reached:
                cp_col = (255, 220, 50)
                pygame.draw.rect(screen, cp_col,
                    (checkpoint_rect.x-draw_ox, checkpoint_rect.y-draw_oy, checkpoint_rect.w, checkpoint_rect.h), 2, border_radius=3)
                ct3 = small_font.render("CP", True, cp_col)
                screen.blit(ct3, (checkpoint_rect.x-draw_ox, checkpoint_rect.y-draw_oy-16))
            elif checkpoint_reached and checkpoint_rect:
                pygame.draw.rect(screen, (50,220,100),
                    (checkpoint_rect.x-draw_ox, checkpoint_rect.y-draw_oy, checkpoint_rect.w, checkpoint_rect.h), 2, border_radius=3)

            # RESPAWN yanıp sönme
            if respawn_timer > 0 and respawn_timer % 10 < 5:
                inv_surf = pygame.Surface((player.w+8, player.h+8), pygame.SRCALPHA)
                inv_surf.fill((255,255,255,80))
                screen.blit(inv_surf, (player.x-draw_ox-4, player.y-draw_oy-4))

            # ÖLÜM animasyonu
            if death_anim_timer > 0:
                da = int((death_anim_timer / 40) * 180)
                ds = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
                ds.fill((255, 0, 0, da))
                screen.blit(ds, (0,0))

            # PAUSE
            if game_paused:
                draw_pause_menu(screen, mouse_pos)

            # --- COİN TRAIL ÇİZİMİ ---
            for ct in coin_trail:
                alpha_ct = min(255, ct['life'] * 8)
                cs = pygame.Surface((int(ct['size'])*2+2, int(ct['size'])*2+2), pygame.SRCALPHA)
                pygame.draw.circle(cs, (245, 197, 66, alpha_ct),
                    (int(ct['size'])+1, int(ct['size'])+1), int(ct['size']))
                screen.blit(cs, (int(ct['x']) - int(ct['size']), int(ct['y']) - int(ct['size'])))

            # --- WALL JUMP GÖSTERGESI ---
            if touching_wall_dir != 0 and not on_ground:
                wj_col = (100, 255, 200)
                wj_x = player.x - draw_ox - 14 if touching_wall_dir == 1 else player.right - draw_ox + 2
                for wi in range(3):
                    pygame.draw.circle(screen, wj_col,
                        (wj_x, player.centery - draw_oy - 8 + wi*8), 3)

            # --- TUTORIAL HİNT ---
            if tutorial_active_hint:
                ths = pygame.Surface((400, 36), pygame.SRCALPHA)
                ths.fill((0, 0, 0, 140))
                screen.blit(ths, (150, GAME_HEIGHT - 50))
                ht2 = small_font.render(tutorial_active_hint, True, (255, 255, 150))
                screen.blit(ht2, (350 - ht2.get_width()//2, GAME_HEIGHT - 44))

            # --- SPEEDRUN TIMER ---
            if speedrun_mode:
                sp_best = speedrun_best.get(current_level, None)
                sp_col  = (80, 255, 80) if (sp_best and speedrun_time < sp_best) else (255, 220, 50)
                sp_txt  = font.render(f"SR: {speedrun_time:.2f}s", True, sp_col)
                screen.blit(sp_txt, (GAME_WIDTH//2 - sp_txt.get_width()//2, GAME_HEIGHT - 36))
                if sp_best:
                    sb_txt = small_font.render(f"Best: {sp_best:.2f}s", True, (180,180,180))
                    screen.blit(sb_txt, (GAME_WIDTH//2 - sb_txt.get_width()//2, GAME_HEIGHT - 18))

            # --- GRAVITY FLIP GÖSTERGESI ---
            if gravity_flipped:
                gf_surf = pygame.Surface((120, 22), pygame.SRCALPHA)
                gf_surf.fill((80, 50, 200, 160))
                screen.blit(gf_surf, (GAME_WIDTH//2 - 60, 28))
                gf_txt = small_font.render("↕ GRAVITY FLIP", True, (200, 180, 255))
                screen.blit(gf_txt, (GAME_WIDTH//2 - gf_txt.get_width()//2, 31))

        # Achievement bildirimi
        if achievement_notif_timer > 0:
            achievement_notif_timer -= 1
            alpha_n = min(255, achievement_notif_timer * 3)
            ns = pygame.Surface((500, 38), pygame.SRCALPHA)
            ns.fill((20, 20, 20, 180))
            screen.blit(ns, (100, 2))
            nt = small_font.render(f"★ {achievement_notification}", True, (245,197,66))
            screen.blit(nt, (350 - nt.get_width()//2, 10))

    # ============================================================
    # GEÇİŞ ANİMASYONU
    # ============================================================
    if transition_state > 0:
        fade = pygame.Surface((700, 500))
        fade.fill((0, 0, 0))
        fade.set_alpha(transition_alpha)
        screen.blit(fade, (0, 0))
        if transition_state == 1:
            transition_alpha += 15
            if transition_alpha >= 255:
                transition_alpha = 255; transition_state = 2
                current_level += 1
                if current_level > unlocked_levels: unlocked_levels = current_level
                load_level(current_level)
        elif transition_state == 2:
            transition_alpha -= 15
            if transition_alpha <= 0:
                transition_alpha = 0; transition_state = 0

    # ============================================================
    # EKRANA AKTAR
    # ============================================================
    if fullscreen:
        ww, wh = display_surface.get_size()
        scale   = min(ww / GAME_WIDTH, wh / GAME_HEIGHT)
        sw      = max(1, int(GAME_WIDTH  * scale))
        sh_     = max(1, int(GAME_HEIGHT * scale))
        ss_     = pygame.transform.smoothscale(screen, (sw, sh_))
        display_surface.fill((0, 0, 0))
        display_surface.blit(ss_, ((ww-sw)//2, (wh-sh_)//2))
    else:
        display_surface.blit(screen, (0, 0))

    pygame.display.flip()
    clock.tick(60)

save_game()
pygame.quit()
