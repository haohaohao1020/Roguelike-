import pygame
import random
from .config import *

class DungeonRenderer:
    def __init__(self):
        self.tile_cache = {}
        self.generate_tiles()
    
    def generate_tiles(self):
        tile_size = TILE_SIZE
        
        floor_tiles = []
        for i in range(4):
            tile = pygame.Surface((tile_size, tile_size))
            base_color = (80 + i * 10, 60 + i * 8, 40 + i * 5)
            tile.fill(base_color)
            for _ in range(8):
                px = random.randint(0, tile_size - 1)
                py = random.randint(0, tile_size - 1)
                variation = random.randint(-15, 15)
                var_color = (
                    max(0, min(255, base_color[0] + variation)),
                    max(0, min(255, base_color[1] + variation)),
                    max(0, min(255, base_color[2] + variation))
                )
                pygame.draw.circle(tile, var_color, (px, py), 1)
            floor_tiles.append(tile)
        self.tile_cache['floor'] = floor_tiles
        
        wall_tile = pygame.Surface((tile_size, tile_size))
        wall_tile.fill((50, 50, 60))
        pygame.draw.rect(wall_tile, (70, 70, 85), (1, 1, tile_size - 2, tile_size - 2), 2)
        pygame.draw.line(wall_tile, (40, 40, 50), (0, tile_size // 3), (tile_size, tile_size // 3), 2)
        pygame.draw.line(wall_tile, (40, 40, 50), (0, tile_size * 2 // 3), (tile_size, tile_size * 2 // 3), 2)
        self.tile_cache['wall'] = wall_tile
        
        treasure_floor = pygame.Surface((tile_size, tile_size))
        treasure_floor.fill((100, 80, 30))
        for _ in range(3):
            px = random.randint(5, tile_size - 5)
            py = random.randint(5, tile_size - 5)
            pygame.draw.circle(treasure_floor, (200, 170, 0), (px, py), 2)
        self.tile_cache['treasure'] = treasure_floor
        
        shop_floor = pygame.Surface((tile_size, tile_size))
        shop_floor.fill((40, 70, 90))
        for i in range(3):
            pygame.draw.circle(shop_floor, (60, 110, 140), (8 + i * 10, 8 + i * 8), 3)
        self.tile_cache['shop'] = shop_floor
        
        rest_floor = pygame.Surface((tile_size, tile_size))
        rest_floor.fill((40, 90, 40))
        pygame.draw.circle(rest_floor, (60, 130, 60), (tile_size // 2, tile_size // 2), 8, 2)
        self.tile_cache['rest'] = rest_floor
        
        trap_floor = pygame.Surface((tile_size, tile_size))
        trap_floor.fill((90, 30, 30))
        pygame.draw.line(trap_floor, (130, 50, 50), (5, 5), (tile_size - 5, tile_size - 5), 3)
        pygame.draw.line(trap_floor, (130, 50, 50), (tile_size - 5, 5), (5, tile_size - 5), 3)
        self.tile_cache['trap'] = trap_floor
        
        boss_floor = pygame.Surface((tile_size, tile_size))
        boss_floor.fill((60, 20, 60))
        pygame.draw.circle(boss_floor, (100, 40, 100), (tile_size // 2, tile_size // 2), 10, 2)
        self.tile_cache['boss'] = boss_floor
        
        corridor = pygame.Surface((tile_size, tile_size))
        corridor.fill((60, 45, 30))
        pygame.draw.line(corridor, (70, 55, 40), (0, 0), (tile_size, tile_size), 1)
        self.tile_cache['corridor'] = corridor
        
        stairs = pygame.Surface((tile_size, tile_size))
        stairs.fill((100, 80, 30))
        for i in range(4):
            pygame.draw.rect(stairs, (70 + i * 20, 50 + i * 15, 20), (5 + i * 6, 5 + i * 6, tile_size - 10 - i * 12, tile_size - 10 - i * 12), 1)
        self.tile_cache['stairs'] = stairs
    
    def draw_floor(self, screen, x, y, camera_x, camera_y, room_type='normal', visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if room_type == 'normal':
            tile_variant = (x + y) % 4
            tile = self.tile_cache['floor'][tile_variant]
        elif room_type == 'treasure':
            tile = self.tile_cache['treasure']
        elif room_type == 'shop':
            tile = self.tile_cache['shop']
        elif room_type == 'rest':
            tile = self.tile_cache['rest']
        elif room_type == 'trap':
            tile = self.tile_cache['trap']
        elif room_type == 'boss':
            tile = self.tile_cache['boss']
        else:
            tile = self.tile_cache['corridor']
        
        if not visible:
            dark_tile = tile.copy()
            dark_tile.set_alpha(80)
            screen.blit(dark_tile, (screen_x, screen_y))
        else:
            screen.blit(tile, (screen_x, screen_y))
    
    def draw_wall(self, screen, x, y, camera_x, camera_y, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            dark_wall = self.tile_cache['wall'].copy()
            dark_wall.set_alpha(60)
            screen.blit(dark_wall, (screen_x, screen_y))
        else:
            screen.blit(self.tile_cache['wall'], (screen_x, screen_y))
    
    def draw_stairs(self, screen, x, y, camera_x, camera_y, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if visible:
            screen.blit(self.tile_cache['stairs'], (screen_x, screen_y))
            
            text = FONT_NORMAL.render('▼ 下一层', True, (255, 255, 100))
            text_rect = text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 15))
            screen.blit(text, text_rect)
        else:
            dark_stairs = self.tile_cache['stairs'].copy()
            dark_stairs.set_alpha(80)
            screen.blit(dark_stairs, (screen_x, screen_y))
    
    def draw_chest(self, screen, x, y, camera_x, camera_y, is_open=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        if is_open:
            pygame.draw.rect(screen, (100, 70, 30), (screen_x + 6, screen_y + 12, TILE_SIZE - 12, TILE_SIZE - 18))
            pygame.draw.rect(screen, (150, 100, 50), (screen_x + 6, screen_y + 5, TILE_SIZE - 12, 10))
            pygame.draw.rect(screen, (255, 215, 0), (screen_x + TILE_SIZE // 2 - 3, screen_y + 18, 6, 6))
        else:
            pygame.draw.rect(screen, (139, 90, 43), (screen_x + 6, screen_y + 8, TILE_SIZE - 12, TILE_SIZE - 14))
            pygame.draw.rect(screen, (180, 120, 60), (screen_x + 6, screen_y + 8, TILE_SIZE - 12, 8))
            pygame.draw.rect(screen, (255, 215, 0), (screen_x + TILE_SIZE // 2 - 3, screen_y + 14, 6, 6))
            
            glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 215, 0, 30), (TILE_SIZE // 2, TILE_SIZE // 2), 15)
            screen.blit(glow, (screen_x, screen_y))
    
    def draw_gold(self, screen, x, y, camera_x, camera_y, amount, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        pygame.draw.circle(screen, (255, 215, 0), (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), 8)
        pygame.draw.circle(screen, (200, 170, 0), (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), 5)
        pygame.draw.circle(screen, (255, 255, 150), (screen_x + TILE_SIZE // 2 - 2, screen_y + TILE_SIZE // 2 - 2), 2)


class MonsterRenderer:
    def __init__(self):
        pass
    
    def draw_goblin(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (80, 180, 80) if not is_hurt else (255, 255, 255)
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2 + 3), 12)
        
        pygame.draw.ellipse(screen, (60, 140, 60), (screen_x + 6, screen_y + 5, 20, 12))
        
        pygame.draw.circle(screen, (255, 50, 50), (screen_x + 11, screen_y + 9), 4)
        pygame.draw.circle(screen, (255, 50, 50), (screen_x + 21, screen_y + 9), 4)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 11, screen_y + 9), 2)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 21, screen_y + 9), 2)
        
        pygame.draw.polygon(screen, (50, 120, 50), [(screen_x + 4, screen_y + 5), (screen_x + 2, screen_y - 2), (screen_x + 8, screen_y + 4)])
        pygame.draw.polygon(screen, (50, 120, 50), [(screen_x + 28, screen_y + 5), (screen_x + 30, screen_y - 2), (screen_x + 24, screen_y + 4)])
        
        self.draw_health_bar(screen, screen_x, screen_y - 10, hp, max_hp)
        
        name_text = FONT_SMALL.render('哥布林', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 22))
        screen.blit(name_text, name_rect)
    
    def draw_orc(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (120, 80, 40) if not is_hurt else (255, 255, 255)
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2 + 2), 14)
        
        pygame.draw.rect(screen, (80, 50, 20), (screen_x + 5, screen_y + 3, 22, 18))
        
        pygame.draw.circle(screen, (255, 100, 100), (screen_x + 10, screen_y + 9), 4)
        pygame.draw.circle(screen, (255, 100, 100), (screen_x + 22, screen_y + 9), 4)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 10, screen_y + 9), 2)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 22, screen_y + 9), 2)
        
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 14, screen_y + 15), (screen_x + 16, screen_y + 20), (screen_x + 12, screen_y + 20)])
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 18, screen_y + 15), (screen_x + 20, screen_y + 20), (screen_x + 16, screen_y + 20)])
        
        self.draw_health_bar(screen, screen_x, screen_y - 10, hp, max_hp)
        
        name_text = FONT_SMALL.render('兽人', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 22))
        screen.blit(name_text, name_rect)
    
    def draw_skeleton(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (220, 220, 220) if not is_hurt else (255, 255, 255)
        
        pygame.draw.line(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + 10), (screen_x + TILE_SIZE // 2, screen_y + 28), 4)
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + 8), 8)
        
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 13, screen_y + 7), 3)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 19, screen_y + 7), 3)
        
        pygame.draw.line(screen, (0, 0, 0), (screen_x + 13, screen_y + 12), (screen_x + 19, screen_y + 12), 2)
        
        pygame.draw.line(screen, body_color, (screen_x + 8, screen_y + 14), (screen_x + 4, screen_y + 22), 3)
        pygame.draw.line(screen, body_color, (screen_x + 24, screen_y + 14), (screen_x + 28, screen_y + 22), 3)
        
        for i in range(3):
            pygame.draw.line(screen, body_color, (screen_x + 11, screen_y + 14 + i * 4), (screen_x + 21, screen_y + 14 + i * 4), 2)
        
        self.draw_health_bar(screen, screen_x, screen_y - 10, hp, max_hp)
        
        name_text = FONT_SMALL.render('骷髅', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 22))
        screen.blit(name_text, name_rect)
    
    def draw_mage(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (80, 40, 120) if not is_hurt else (255, 255, 255)
        
        pygame.draw.polygon(screen, (60, 20, 90), [
            (screen_x + TILE_SIZE // 2, screen_y + 2),
            (screen_x + 4, screen_y + 16),
            (screen_x + TILE_SIZE - 4, screen_y + 16)
        ])
        
        pygame.draw.circle(screen, (100, 60, 150), (screen_x + TILE_SIZE // 2, screen_y + 20), 10)
        
        pygame.draw.circle(screen, (180, 100, 255), (screen_x + 12, screen_y + 18), 3)
        pygame.draw.circle(screen, (180, 100, 255), (screen_x + 20, screen_y + 18), 3)
        
        pygame.draw.line(screen, (139, 90, 43), (screen_x + 28, screen_y + 10), (screen_x + 30, screen_y + 2), 3)
        pygame.draw.circle(screen, (100, 150, 255), (screen_x + 30, screen_y + 2), 4)
        
        magic_glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(magic_glow, (100, 100, 255, 50), (screen_x + 30 - screen_x, screen_y + 2 - screen_y), 8)
        screen.blit(magic_glow, (screen_x, screen_y))
        
        self.draw_health_bar(screen, screen_x, screen_y - 10, hp, max_hp)
        
        name_text = FONT_SMALL.render('黑暗法师', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 22))
        screen.blit(name_text, name_rect)
    
    def draw_elite_orc(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (180, 120, 40) if not is_hurt else (255, 255, 255)
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2 + 2), 16)
        
        pygame.draw.rect(screen, (140, 90, 30), (screen_x + 3, screen_y + 2, 26, 20))
        
        pygame.draw.circle(screen, (255, 150, 0), (screen_x + 9, screen_y + 8), 5)
        pygame.draw.circle(screen, (255, 150, 0), (screen_x + 23, screen_y + 8), 5)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 9, screen_y + 8), 2)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 23, screen_y + 8), 2)
        
        pygame.draw.rect(screen, (200, 50, 50), (screen_x + 8, screen_y - 4, 16, 6))
        
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 13, screen_y + 16), (screen_x + 16, screen_y + 23), (screen_x + 10, screen_y + 23)])
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 19, screen_y + 16), (screen_x + 22, screen_y + 23), (screen_x + 16, screen_y + 23)])
        
        elite_glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(elite_glow, (255, 150, 0, 40), (TILE_SIZE // 2, TILE_SIZE // 2), 18)
        screen.blit(elite_glow, (screen_x, screen_y))
        
        self.draw_health_bar(screen, screen_x, screen_y - 10, hp, max_hp)
        
        name_text = FONT_SMALL.render('★ 精英兽人', True, (255, 200, 100))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 22))
        screen.blit(name_text, name_rect)
    
    def draw_dragon(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (150, 50, 150) if not is_hurt else (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x + 2, screen_y + 8, 28, 20))
        
        pygame.draw.circle(screen, (180, 70, 180), (screen_x + TILE_SIZE // 2, screen_y + 10), 12)
        
        pygame.draw.polygon(screen, (120, 40, 120), [
            (screen_x + 6, screen_y + 2),
            (screen_x + 2, screen_y - 6),
            (screen_x + 10, screen_y + 4)
        ])
        pygame.draw.polygon(screen, (120, 40, 120), [
            (screen_x + 26, screen_y + 2),
            (screen_x + 30, screen_y - 6),
            (screen_x + 22, screen_y + 4)
        ])
        
        pygame.draw.circle(screen, (255, 100, 0), (screen_x + 11, screen_y + 8), 5)
        pygame.draw.circle(screen, (255, 100, 0), (screen_x + 21, screen_y + 8), 5)
        pygame.draw.circle(screen, (255, 255, 0), (screen_x + 11, screen_y + 8), 2)
        pygame.draw.circle(screen, (255, 255, 0), (screen_x + 21, screen_y + 8), 2)
        
        pygame.draw.polygon(screen, (180, 70, 180), [
            (screen_x + 2, screen_y + 18),
            (screen_x - 4, screen_y + 22),
            (screen_x + 2, screen_y + 26)
        ])
        pygame.draw.polygon(screen, (180, 70, 180), [
            (screen_x + 30, screen_y + 18),
            (screen_x + 36, screen_y + 22),
            (screen_x + 30, screen_y + 26)
        ])
        
        fire_glow = pygame.Surface((TILE_SIZE + 10, TILE_SIZE + 10), pygame.SRCALPHA)
        pygame.draw.circle(fire_glow, (255, 100, 0, 30), (TILE_SIZE // 2 + 5, TILE_SIZE // 2 + 5), 22)
        screen.blit(fire_glow, (screen_x - 5, screen_y - 5))
        
        self.draw_health_bar(screen, screen_x, screen_y - 15, hp, max_hp, True)
        
        name_text = FONT_NORMAL.render('🐉 远古巨龙', True, (255, 150, 255))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 30))
        screen.blit(name_text, name_rect)
    
    def draw_health_bar(self, screen, x, y, hp, max_hp, is_boss=False):
        bar_width = TILE_SIZE if not is_boss else TILE_SIZE + 10
        bar_height = 5 if not is_boss else 7
        
        bg_color = (80, 0, 0) if not is_boss else (100, 0, 100)
        fill_color = (0, 200, 0) if hp > max_hp * 0.3 else (255, 100, 0) if hp > max_hp * 0.1 else (255, 0, 0)
        
        if is_boss:
            fill_color = (200, 50, 200)
        
        bar_x = x + (TILE_SIZE - bar_width) // 2
        
        pygame.draw.rect(screen, bg_color, (bar_x, y, bar_width, bar_height))
        
        hp_ratio = hp / max_hp
        fill_width = int(bar_width * hp_ratio)
        pygame.draw.rect(screen, fill_color, (bar_x, y, fill_width, bar_height))
        
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, y, bar_width, bar_height), 1)


class PlayerRenderer:
    def __init__(self):
        pass
    
    def draw_warrior(self, screen, x, y, camera_x, camera_y, is_hurt=False):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        body_color = (80, 140, 220) if not is_hurt else (255, 255, 255)
        
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2 + 2), 12)
        
        pygame.draw.circle(screen, (255, 220, 180), (screen_x + TILE_SIZE // 2, screen_y + 8), 7)
        
        pygame.draw.circle(screen, (0, 0, 150), (screen_x + 13, screen_y + 7), 2)
        pygame.draw.circle(screen, (0, 0, 150), (screen_x + 19, screen_y + 7), 2)
        
        pygame.draw.rect(screen, (150, 0, 0), (screen_x + 8, screen_y + 3, 16, 4))
        
        pygame.draw.rect(screen, (139, 90, 43), (screen_x + 24, screen_y + 8, 4, 18))
        pygame.draw.rect(screen, (200, 200, 200), (screen_x + 22, screen_y + 5, 8, 6))
        
        pygame.draw.rect(screen, (80, 60, 40), (screen_x + 3, screen_y + 12, 6, 14))
        pygame.draw.rect(screen, (200, 150, 50), (screen_x + 3, screen_y + 12, 6, 3))
    
    def draw_mage(self, screen, x, y, camera_x, camera_y, is_hurt=False):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        body_color = (120, 80, 180) if not is_hurt else (255, 255, 255)
        
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2 + 2), 12)
        
        pygame.draw.polygon(screen, (80, 40, 140), [
            (screen_x + TILE_SIZE // 2, screen_y - 2),
            (screen_x + 6, screen_y + 10),
            (screen_x + TILE_SIZE - 6, screen_y + 10)
        ])
        
        pygame.draw.circle(screen, (255, 220, 180), (screen_x + TILE_SIZE // 2, screen_y + 10), 6)
        
        pygame.draw.circle(screen, (100, 50, 200), (screen_x + 14, screen_y + 9), 2)
        pygame.draw.circle(screen, (100, 50, 200), (screen_x + 18, screen_y + 9), 2)
        
        pygame.draw.line(screen, (139, 90, 43), (screen_x + 26, screen_y + 6), (screen_x + 30, screen_y - 4), 2)
        magic_ball = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(magic_ball, (100, 150, 255, 200), (30 - screen_x, -4 - screen_y), 5)
        pygame.draw.circle(magic_ball, (150, 200, 255, 100), (30 - screen_x, -4 - screen_y), 8)
        screen.blit(magic_ball, (screen_x, screen_y))
    
    def draw_rogue(self, screen, x, y, camera_x, camera_y, is_hurt=False):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        body_color = (60, 160, 100) if not is_hurt else (255, 255, 255)
        
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2 + 2), 11)
        
        pygame.draw.ellipse(screen, (40, 120, 70), (screen_x + 7, screen_y + 2, 18, 12))
        
        pygame.draw.circle(screen, (255, 220, 180), (screen_x + TILE_SIZE // 2, screen_y + 9), 5)
        
        pygame.draw.circle(screen, (0, 200, 100), (screen_x + 14, screen_y + 8), 2)
        pygame.draw.circle(screen, (0, 200, 100), (screen_x + 18, screen_y + 8), 2)
        
        pygame.draw.rect(screen, (80, 60, 40), (screen_x + 3, screen_y + 18, 5, 10))
        pygame.draw.rect(screen, (80, 60, 40), (screen_x + 24, screen_y + 18, 5, 10))
        
        pygame.draw.polygon(screen, (150, 150, 150), [
            (screen_x + 26, screen_y + 12),
            (screen_x + 32, screen_y + 18),
            (screen_x + 26, screen_y + 22)
        ])
