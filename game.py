import pygame
import random
import copy

pygame.init()
screen = pygame.display.set_mode((700, 500))
pygame.display.set_caption("Sky Hopper")
clock = pygame.time.Clock()

game_started = False  
is_running_sound_playing = False

transition_state = 0
transition_alpha = 0

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
    print("Kapı animasyonu yüklenemedi:", e)

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

try:
    sprite_sheet = pygame.image.load("player_sheet2-2.png").convert_alpha()
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
    has_sprites = False

level_1_platforms = [pygame.Rect(0, 470, 280, 30), pygame.Rect(420, 470, 280, 30), pygame.Rect(150, 380, 120, 20), pygame.Rect(340, 300, 120, 20), pygame.Rect(520, 220, 120, 20), pygame.Rect(260, 160, 100, 20)]
level_1_coins = [pygame.Rect(200, 345, 16, 16), pygame.Rect(390, 265, 16, 16), pygame.Rect(560, 185, 16, 16), pygame.Rect(300, 130, 16, 16)]

level_2_platforms = [pygame.Rect(0, 470, 150, 30), pygame.Rect(250, 400, 120, 20), pygame.Rect(500, 330, 120, 20), pygame.Rect(220, 250, 100, 20), pygame.Rect(20, 180, 120, 20), pygame.Rect(400, 120, 200, 20), pygame.Rect(425, 470, 375, 30)]
level_2_coins = [pygame.Rect(290, 365, 16, 16), pygame.Rect(540, 295, 16, 16), pygame.Rect(60, 145, 16, 16), pygame.Rect(492, 94, 16, 16)]

level_3_platforms = [pygame.Rect(0, 470, 155, 30), pygame.Rect(200, 400, 80, 20), pygame.Rect(400, 330, 80, 20), pygame.Rect(600, 250, 80, 20), pygame.Rect(300, 180, 100, 20), pygame.Rect(50, 120, 120, 20), pygame.Rect(300, 470, 300, 30)]
level_3_coins = [pygame.Rect(230, 365, 16, 16), pygame.Rect(430, 295, 16, 16), pygame.Rect(630, 215, 16, 16), pygame.Rect(102, 94, 16, 16)]

level_4_platforms = [pygame.Rect(0, 470, 150, 30), pygame.Rect(150, 380, 80, 20), pygame.Rect(300, 380, 80, 20), pygame.Rect(550, 300, 80, 20), pygame.Rect(350, 200, 80, 20), pygame.Rect(100, 100, 100, 20), pygame.Rect(354.5, 470, 200, 30)]
level_4_coins = [pygame.Rect(180, 345, 16, 16), pygame.Rect(330, 345, 16, 16), pygame.Rect(580, 265, 16, 16), pygame.Rect(142, 74, 16, 16)]

level_5_platforms = [pygame.Rect(0, 470, 80, 30), pygame.Rect(120, 370, 60, 20), pygame.Rect(30, 270, 60, 20), pygame.Rect(200, 180, 60, 20), pygame.Rect(400, 180, 100, 20), pygame.Rect(600, 100, 80, 20), pygame.Rect(356.5, 295, 73, 20)]
level_5_coins = [pygame.Rect(140, 335, 16, 16), pygame.Rect(50, 235, 16, 16), pygame.Rect(220, 145, 16, 16), pygame.Rect(632, 74, 16, 16)]

level_6_platforms = [pygame.Rect(0, 470, 173, 70), pygame.Rect(150, 400, 50, 20), pygame.Rect(300, 330, 110, 20), pygame.Rect(550, 260, 50, 20), pygame.Rect(300, 160, 119, 20), pygame.Rect(35.4, 100, 95, 20)]
level_6_coins = [pygame.Rect(165, 365, 16, 16), pygame.Rect(565, 225, 16, 16), pygame.Rect(330, 125, 16, 16), pygame.Rect(72, 74, 16, 16)]

level_7_platforms = [pygame.Rect(0, 470, 120, 30), pygame.Rect(180, 400, 60, 20), pygame.Rect(350, 330, 60, 20), pygame.Rect(520, 260, 60, 20), pygame.Rect(350, 180, 60, 20), pygame.Rect(152.5, 100, 100, 20)]
level_7_coins = [pygame.Rect(202, 365, 16, 16), pygame.Rect(542, 225, 16, 16), pygame.Rect(372, 145, 16, 16), pygame.Rect(192, 76, 16, 16)]

level_8_platforms = [pygame.Rect(0, 470, 140, 30), pygame.Rect(150, 420, 50, 20), pygame.Rect(300, 350, 50, 20), pygame.Rect(450, 280, 50, 20), pygame.Rect(600, 200, 80, 20), pygame.Rect(350, 130, 60, 20), pygame.Rect(95, 80, 90, 20)]
level_8_coins = [pygame.Rect(167, 385, 16, 16), pygame.Rect(317, 315, 16, 16), pygame.Rect(467, 245, 16, 16), pygame.Rect(132, 56, 16, 16)]

level_9_platforms = [pygame.Rect(0, 470, 140, 30), pygame.Rect(150, 380, 40, 20), pygame.Rect(300, 380, 40, 20), pygame.Rect(480, 300, 40, 20), pygame.Rect(600, 220, 60, 20), pygame.Rect(400, 150, 40, 20), pygame.Rect(200, 100, 40, 20), pygame.Rect(37, 63.5, 90, 20)]
level_9_coins = [pygame.Rect(162, 345, 16, 16), pygame.Rect(492, 265, 16, 16), pygame.Rect(412, 115, 16, 16), pygame.Rect(72, 36, 16, 16)]

level_10_platforms = [pygame.Rect(0, 470, 140, 30), pygame.Rect(150, 400, 40, 20), pygame.Rect(350, 350, 40, 20), pygame.Rect(550, 280, 40, 20), pygame.Rect(350, 200, 40, 20), pygame.Rect(485.5, 95, 90, 20)]
level_10_coins = [pygame.Rect(162, 365, 16, 16), pygame.Rect(562, 245, 16, 16), pygame.Rect(522, 64, 16, 16)]

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
    10: [{'idx': 1, 'dir': 1, 'min': 100, 'max': 250}, {'idx': 3, 'dir': -1, 'min': 450, 'max': 620}, {'idx': 5, 'dir': 1, 'min': 100, 'max': 250}]
}

current_level = 1
platforms = []
coins = []
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

def load_level(level_num):
    global platforms, coins, current_moving_data, player, vel_y, door_rect
    global is_door_opening, door_anim_index
    
    is_door_opening = False
    door_anim_index = 3  

    level_data = {
        1: (level_1_platforms, level_1_coins),
        2: (level_2_platforms, level_2_coins),
        3: (level_3_platforms, level_3_coins),
        4: (level_4_platforms, level_4_coins),
        5: (level_5_platforms, level_5_coins),
        6: (level_6_platforms, level_6_coins),
        7: (level_7_platforms, level_7_coins),
        8: (level_8_platforms, level_8_coins),
        9: (level_9_platforms, level_9_coins),
        10: (level_10_platforms, level_10_coins)
    }
    
    platforms = [pygame.Rect(p) for p in level_data[level_num][0]]
    coins = [pygame.Rect(c) for c in level_data[level_num][1]]
    current_moving_data = copy.deepcopy(level_moving_data[level_num])
    
    player.x = 60
    player.y = 260
    vel_y = 0

    if level_num == 10:
        door_rect.x = 520  
        door_rect.y = 200  
    elif coins:
        highest_coin = coins[-1] 
        door_rect.centerx = highest_coin.centerx
        door_rect.centery = highest_coin.centery - 4  

def reset_game():
    global current_level, score, start_time, game_won, game_over
    global is_running_sound_playing
    global transition_state, transition_alpha
    
    current_level = 1
    score = 0
    start_time = pygame.time.get_ticks()
    game_won = False
    game_over = False
    transition_state = 0
    transition_alpha = 0
    
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

try:
    font = pygame.font.SysFont("Impact", 30)
    title_font = pygame.font.SysFont("Impact", 60) 
except pygame.error:
    font = pygame.font.SysFont(None, 30)
    title_font = pygame.font.SysFont(None, 60)

stars = [(random.randint(0, 700), random.randint(0, 500), random.randint(1, 3)) for _ in range(60)]

try:
    pygame.mixer.init()  
    jump_sound = pygame.mixer.Sound("jumpsound.wav")
    jump_sound.set_volume(0.1)
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
    jump_sound = None
    coin_sound = None
    door_sound = None
    run_sound = None
    game_over_sound = None
    land_sound = None  

try:
    pygame.mixer.music.load("musicsound.mp3")
    pygame.mixer.music.set_volume(1.0)
except:
    pass

reset_game()

running = True
while running:
    if not game_started:
        screen.fill((30, 34, 56)) 
        for star in stars:
            pygame.draw.circle(screen, (255, 255, 255), (star[0], star[1]), star[2])
            
        title_text = title_font.render("SKY HOPPER", True, (245, 197, 66))
        screen.blit(title_text, (350 - title_text.get_width() // 2, 120))
        
        btn_width, btn_height = 240, 60
        btn_x, btn_y = 350 - btn_width // 2, 260
        start_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        mouse_pos = pygame.mouse.get_pos()
        
        if start_button_rect.collidepoint(mouse_pos):
            button_color, text_color = (60, 180, 120), (255, 255, 255)
        else:
            button_color, text_color = (20, 24, 46), (240, 240, 240)
            
        pygame.draw.rect(screen, (245, 197, 66), (btn_x - 3, btn_y - 3, btn_width + 6, btn_height + 6), border_radius=10) 
        pygame.draw.rect(screen, button_color, start_button_rect, border_radius=10)
        
        btn_text = font.render("START GAME", True, text_color)
        screen.blit(btn_text, (btn_x + (btn_width - btn_text.get_width()) // 2, btn_y + (btn_height - btn_text.get_height()) // 2))

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
                    if current_level == 1 and m_data['idx'] == 5:
                        door_rect.x += platform_speed * m_data['dir']
                        if len(coins) > 0:
                            highest_coin = min(coins, key=lambda c: c.y)
                            highest_coin.x += platform_speed * m_data['dir']
                    continue
                
                for other_idx, other_plat in enumerate(platforms):
                    if other_idx != m_data['idx']:
                        if moving_plat.colliderect(other_plat):
                            m_data['dir'] *= -1
                            moving_plat.x += platform_speed * m_data['dir']
                            if current_level == 1 and m_data['idx'] == 5:
                                door_rect.x += platform_speed * m_data['dir']
                                if len(coins) > 0:
                                    highest_coin = min(coins, key=lambda c: c.y)
                                    highest_coin.x += platform_speed * m_data['dir']
                            break

            is_moving = False
            moving_backwards = False
            keys = pygame.key.get_pressed()
            
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
                    elif can_double_jump:
                        vel_y = -15
                        if jump_sound: jump_sound.play()
                        can_double_jump = False
                    space_pressed = True
            else:
                space_pressed = False 
                    
            if player.left < 0: player.left = 0
            if player.right > 700: player.right = 700
            
            if player.top < 0:
                player.top = 0
                vel_y = 0  
            
            vel_y += gravity
            player.y += vel_y
            
            was_on_ground = on_ground
            on_ground = False
            
            player_on_moving = False
            moving_dx = 0

            for i, p in enumerate(platforms):
                if player.colliderect(p) and (player.centerx > p.left and player.centerx < p.right):
                    if vel_y > 0: 
                        player.bottom = p.top
                        vel_y = 0
                        on_ground = True
                        can_double_jump = True 
                        
                        if not was_on_ground:
                            if land_sound: land_sound.play()
                            
                        for m_data in current_moving_data:
                            if i == m_data['idx']:
                                player_on_moving = True
                                moving_dx = platform_speed * m_data['dir']
                    elif vel_y < 0: 
                        player.top = p.bottom
                        vel_y = 0

            if player_on_moving:
                player.x += moving_dx

            if is_moving and on_ground:
                if run_sound and not is_running_sound_playing:
                    run_sound.play(-1) 
                    is_running_sound_playing = True
            else:
                if run_sound and is_running_sound_playing:
                    run_sound.stop()
                    is_running_sound_playing = False

            for coin in coins[:]:
                if player.colliderect(coin):
                    coins.remove(coin)
                    score += 1
                    if coin_sound: coin_sound.play()
                    break

            if player.top > 500:
                game_over = True
                finish_time = current_time
                try: pygame.mixer.music.stop()
                except: pass
                if run_sound:
                    run_sound.stop()
                    is_running_sound_playing = False
                
                if game_over_sound:
                    game_over_sound.play()

            if len(coins) == 0 and player.colliderect(door_rect) and not is_door_opening and transition_state == 0:
                is_door_opening = True  
                door_anim_index = 3  
                door_anim_timer = 0
                if door_sound: door_sound.play()
            
            if is_door_opening:
                door_anim_timer += 1
                if door_anim_timer > 8: 
                    door_anim_timer = 0
                    if door_anim_index > 0:  
                        door_anim_index -= 1
                    else:
                        is_door_opening = False
                        door_anim_index = 3  
                        if current_level < 10:
                            transition_state = 1 
                        elif current_level == 10:
                            game_won = True
                            finish_time = current_time
                            if best_time == 0 or finish_time < best_time:
                                best_time = finish_time
                            try: pygame.mixer.music.stop()
                            except: pass
                            if run_sound:
                                run_sound.stop()
                                is_running_sound_playing = False

        if game_won or game_over:
            screen.fill((30, 34, 56))
            end_box_width, end_box_height = 400, 320
            end_box_x, end_box_y = (700 - end_box_width) // 2, (500 - end_box_height) // 2
            
            pygame.draw.rect(screen, (10, 10, 20), (end_box_x - 5, end_box_y - 5, end_box_width + 10, end_box_height + 10))
            pygame.draw.rect(screen, (20, 24, 46), (end_box_x, end_box_y, end_box_width, end_box_height))

            win_lose_text = title_font.render('YOU WIN!' if game_won else 'GAME OVER!', True, (120, 255, 160) if game_won else (255, 100, 100))
            screen.blit(win_lose_text, (end_box_x + (end_box_width - win_lose_text.get_width()) // 2, end_box_y + 40))

            texts_to_show = [
                f'Time: {round(finish_time, 1)}s',
                f'Total Coins: {score}',
                f'Best: {round(best_time, 1)}s' if best_time > 0 else 'Best: --'
            ]

            text_y_offset = end_box_y + 120
            for info_text in texts_to_show:
                rendered_text = font.render(info_text, True, (240, 240, 240))
                screen.blit(rendered_text, (end_box_x + (end_box_width - rendered_text.get_width()) // 2, text_y_offset))
                text_y_offset += 45
            
            play_again_text = font.render('Press "R" to Play Again', True, (245, 197, 66))
            screen.blit(play_again_text, (end_box_x + (end_box_width - play_again_text.get_width()) // 2, end_box_y + 250))

        else:
            screen.fill((30, 34, 56))
            for star in stars:
                pygame.draw.circle(screen, (255, 255, 255), (star[0], star[1]), star[2])
            
            if door_frames:
                screen.blit(door_frames[door_anim_index], (door_rect.x, door_rect.y))
            else:
                if door_img:
                    screen.blit(door_img, (door_rect.x, door_rect.y))
                else:
                    pygame.draw.rect(screen, (80, 80, 80), door_rect)

            moving_indices = [m['idx'] for m in current_moving_data]
            for i, p in enumerate(platforms):
                if i in moving_indices:
                    if moving_platform_img:
                        scaled_img = pygame.transform.scale(moving_platform_img, (p.width, p.height))
                        screen.blit(scaled_img, (p.x, p.y))
                    else:
                        pygame.draw.rect(screen, (140, 90, 140), p)
                else:
                    if platform_img:
                        scaled_img = pygame.transform.scale(platform_img, (p.width, p.height))
                        screen.blit(scaled_img, (p.x, p.y))
                    else:
                        pygame.draw.rect(screen, (90, 120, 90), p)
                
            for coin in coins:
                pygame.draw.ellipse(screen, (245, 197, 66), coin)
                
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
                    if animation_timer >= 6: 
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
                screen.blit(active_sprite, (player.x, player.y + 3))
                
            else:
                pygame.draw.rect(screen, (80, 170, 230), player)
            
            top_bar_y = 10
            ui_text_color = (240, 240, 240)
            screen.blit(font.render(f'Coins: {score}', True, ui_text_color), (10, top_bar_y))
            screen.blit(font.render(f'Level: {current_level}/10', True, ui_text_color), (140, top_bar_y))
            screen.blit(font.render(f'Time: {round(current_time, 1)}s', True, ui_text_color), (280, top_bar_y))
            if best_time > 0:
                screen.blit(font.render(f'Best: {round(best_time, 1)}s', True, (245, 197, 66)), (450, top_bar_y))

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
                load_level(current_level)
                
        elif transition_state == 2:
            transition_alpha -= 15
            if transition_alpha <= 0:
                transition_alpha = 0
                transition_state = 0 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                if not game_started and start_button_rect.collidepoint(event.pos):
                    game_started = True
                    reset_game() 
        if event.type == pygame.KEYDOWN:
            if (game_won or game_over) and event.key == pygame.K_r:
                reset_game()

    pygame.display.flip()
    clock.tick(60) 

pygame.quit()