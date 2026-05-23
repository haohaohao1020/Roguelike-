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
        colors = [
            (100, 80, 60), (90, 70, 50), (110, 90, 70), (95, 75, 55)
        ]
        for i in range(4):
            tile = pygame.Surface((tile_size, tile_size))
            tile.fill(colors[i])
            for _ in range(5):
                px = random.randint(0, tile_size - 1)
                py = random.randint(0, tile_size - 1)
                var_color = (
                    max(0, min(255, colors[i][0] + random.randint(-15, 15))),
                    max(0, min(255, colors[i][1] + random.randint(-15, 15))),
                    max(0, min(255, colors[i][2] + random.randint(-15, 15)))
                )
                pygame.draw.circle(tile, var_color, (px, py), 1)
            floor_tiles.append(tile)
        self.tile_cache['floor'] = floor_tiles
        
        treasure = pygame.Surface((tile_size, tile_size))
        treasure.fill((120, 100, 30))
        for _ in range(3):
            px = random.randint(5, tile_size - 5)
            py = random.randint(5, tile_size - 5)
            pygame.draw.circle(treasure, (200, 170, 0), (px, py), 2)
        self.tile_cache['treasure'] = treasure
        
        shop = pygame.Surface((tile_size, tile_size))
        shop.fill((40, 70, 100))
        for i in range(3):
            pygame.draw.circle(shop, (80, 140, 180), (8 + i * 10, 8 + i * 8), 3)
        self.tile_cache['shop'] = shop
        
        rest = pygame.Surface((tile_size, tile_size))
        rest.fill((40, 100, 40))
        pygame.draw.circle(rest, (80, 160, 80), (tile_size // 2, tile_size // 2), 10, 2)
        self.tile_cache['rest'] = rest
        
        trap = pygame.Surface((tile_size, tile_size))
        trap.fill((100, 30, 30))
        pygame.draw.line(trap, (150, 70, 70), (5, 5), (tile_size - 5, tile_size - 5), 2)
        pygame.draw.line(trap, (150, 70, 70), (tile_size - 5, 5), (5, tile_size - 5), 2)
        self.tile_cache['trap'] = trap
        
        boss = pygame.Surface((tile_size, tile_size))
        boss.fill((70, 20, 70))
        pygame.draw.circle(boss, (120, 50, 120), (tile_size // 2, tile_size // 2), 12, 2)
        self.tile_cache['boss'] = boss
        
        corridor = pygame.Surface((tile_size, tile_size))
        corridor.fill((70, 50, 35))
        self.tile_cache['corridor'] = corridor
        
        wall = pygame.Surface((tile_size, tile_size))
        wall.fill((40, 40, 50))
        pygame.draw.rect(wall, (60, 60, 75), (1, 1, tile_size - 2, tile_size - 2), 2)
        pygame.draw.line(wall, (30, 30, 40), (0, tile_size // 3), (tile_size, tile_size // 3), 2)
        pygame.draw.line(wall, (30, 30, 40), (0, tile_size * 2 // 3), (tile_size, tile_size * 2 // 3), 2)
        self.tile_cache['wall'] = wall
        
        stairs = pygame.Surface((tile_size, tile_size))
        stairs.fill((100, 80, 30))
        for i in range(4):
            pygame.draw.rect(stairs, (70 + i * 25, 50 + i * 20, 20), (5 + i * 6, 5 + i * 6, tile_size - 10 - i * 12, tile_size - 10 - i * 12), 1)
        self.tile_cache['stairs'] = stairs
        
        ice = pygame.Surface((tile_size, tile_size))
        ice.fill((180, 220, 255))
        for i in range(5):
            pygame.draw.line(ice, (220, 240, 255), (random.randint(0, tile_size), random.randint(0, tile_size)), (random.randint(0, tile_size), random.randint(0, tile_size)), 1)
        self.tile_cache['ice'] = ice
        
        thorns = pygame.Surface((tile_size, tile_size))
        thorns.fill((50, 100, 50))
        for i in range(8):
            px = random.randint(5, tile_size - 5)
            py = random.randint(5, tile_size - 5)
            pygame.draw.polygon(thorns, (30, 70, 30), [(px, py - 4), (px - 3, py + 2), (px + 3, py + 2)])
        self.tile_cache['thorns'] = thorns
        
        poison = pygame.Surface((tile_size, tile_size))
        poison.fill((80, 130, 50))
        for i in range(4):
            px = random.randint(5, tile_size - 5)
            py = random.randint(5, tile_size - 5)
            pygame.draw.circle(poison, (100, 160, 60), (px, py), 3)
        self.tile_cache['poison'] = poison
        
        lava = pygame.Surface((tile_size, tile_size))
        lava.fill((200, 80, 30))
        for i in range(5):
            px = random.randint(5, tile_size - 5)
            py = random.randint(5, tile_size - 5)
            pygame.draw.circle(lava, (255, 150, 50), (px, py), 2)
        self.tile_cache['lava'] = lava
        
        speed = pygame.Surface((tile_size, tile_size))
        speed.fill((200, 180, 100))
        pygame.draw.polygon(speed, (255, 220, 150), [(tile_size // 2, 6), (tile_size // 2 - 6, tile_size // 2), (tile_size // 2 + 6, tile_size // 2)])
        pygame.draw.polygon(speed, (255, 220, 150), [(tile_size // 2, tile_size - 6), (tile_size // 2 - 6, tile_size // 2), (tile_size // 2 + 6, tile_size // 2)])
        self.tile_cache['speed'] = speed
        
        altar = pygame.Surface((tile_size, tile_size))
        altar.fill((60, 40, 80))
        pygame.draw.rect(altar, (100, 80, 120), (8, 16, 16, 12))
        pygame.draw.circle(altar, (150, 100, 200), (tile_size // 2, 12), 6)
        self.tile_cache['altar'] = altar
        
        blacksmith = pygame.Surface((tile_size, tile_size))
        blacksmith.fill((80, 60, 40))
        pygame.draw.rect(blacksmith, (150, 100, 50), (6, 20, 20, 8))
        pygame.draw.rect(blacksmith, (200, 150, 100), (10, 10, 12, 12))
        self.tile_cache['blacksmith'] = blacksmith
        
        library = pygame.Surface((tile_size, tile_size))
        library.fill((60, 50, 40))
        pygame.draw.rect(library, (100, 80, 60), (4, 8, 24, 20))
        for i in range(4):
            pygame.draw.line(library, (150, 120, 90), (8 + i * 6, 10), (8 + i * 6, 24), 2)
        self.tile_cache['library'] = library
        
        event = pygame.Surface((tile_size, tile_size))
        event.fill((50, 60, 70))
        pygame.draw.circle(event, (100, 150, 200), (tile_size // 2, tile_size // 2), 8)
        pygame.draw.circle(event, (150, 200, 255), (tile_size // 2, tile_size // 2), 4)
        self.tile_cache['event'] = event
    
    def draw_floor(self, screen, x, y, camera_x, camera_y, room_type='normal', terrain='normal', visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if terrain != 'normal':
            tile = self.tile_cache.get(terrain, self.tile_cache['floor'][0])
        elif room_type == 'normal':
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
        elif room_type == 'altar':
            tile = self.tile_cache['altar']
        elif room_type == 'blacksmith':
            tile = self.tile_cache['blacksmith']
        elif room_type == 'library':
            tile = self.tile_cache['library']
        elif room_type == 'event':
            tile = self.tile_cache['event']
        else:
            tile = self.tile_cache['corridor']
        
        if not visible:
            dark = tile.copy()
            dark.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(dark, (screen_x, screen_y))
        else:
            screen.blit(tile, (screen_x, screen_y))
    
    def draw_wall(self, screen, x, y, camera_x, camera_y, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            dark = self.tile_cache['wall'].copy()
            dark.fill((30, 30, 30), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(dark, (screen_x, screen_y))
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
            dark = self.tile_cache['stairs'].copy()
            dark.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(dark, (screen_x, screen_y))
    
    def draw_chest(self, screen, x, y, camera_x, camera_y, is_open=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        if is_open:
            pygame.draw.rect(screen, (100, 70, 30), (screen_x + 6, screen_y + 12, TILE_SIZE - 12, TILE_SIZE - 18))
            pygame.draw.rect(screen, (150, 100, 50), (screen_x + 6, screen_y + 5, TILE_SIZE - 12, 10))
        else:
            pygame.draw.rect(screen, (139, 90, 43), (screen_x + 6, screen_y + 8, TILE_SIZE - 12, TILE_SIZE - 14))
            pygame.draw.rect(screen, (180, 120, 60), (screen_x + 6, screen_y + 8, TILE_SIZE - 12, 8))
            pygame.draw.rect(screen, (255, 215, 0), (screen_x + TILE_SIZE // 2 - 3, screen_y + 12, 6, 6))
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


class MonsterRenderer:
    def __init__(self):
        pass
    
    def draw_goblin(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (80, 180, 80) if not is_hurt else (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x + 4, screen_y + 14, 24, 16))
        pygame.draw.ellipse(screen, (60, 140, 60), (screen_x + 6, screen_y + 6, 20, 14))
        
        pygame.draw.circle(screen, (255, 50, 50), (screen_x + 12, screen_y + 11), 4)
        pygame.draw.circle(screen, (255, 50, 50), (screen_x + 20, screen_y + 11), 4)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 12, screen_y + 11), 2)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 20, screen_y + 11), 2)
        
        pygame.draw.polygon(screen, (50, 120, 50), [(screen_x + 5, screen_y + 6), (screen_x + 2, screen_y - 2), (screen_x + 10, screen_y + 5)])
        pygame.draw.polygon(screen, (50, 120, 50), [(screen_x + 27, screen_y + 6), (screen_x + 30, screen_y - 2), (screen_x + 22, screen_y + 5)])
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('哥布林', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_orc(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (120, 80, 40) if not is_hurt else (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x + 2, screen_y + 12, 28, 18))
        pygame.draw.rect(screen, (80, 50, 20), (screen_x + 4, screen_y + 4, 24, 16))
        
        pygame.draw.circle(screen, (255, 100, 100), (screen_x + 10, screen_y + 10), 4)
        pygame.draw.circle(screen, (255, 100, 100), (screen_x + 22, screen_y + 10), 4)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 10, screen_y + 10), 2)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 22, screen_y + 10), 2)
        
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 13, screen_y + 16), (screen_x + 15, screen_y + 22), (screen_x + 11, screen_y + 22)])
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 19, screen_y + 16), (screen_x + 21, screen_y + 22), (screen_x + 17, screen_y + 22)])
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('兽人', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_skeleton(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (220, 220, 220) if not is_hurt else (255, 255, 255)
        
        pygame.draw.line(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + 12), (screen_x + TILE_SIZE // 2, screen_y + 28), 4)
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + 9), 8)
        
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 13, screen_y + 8), 3)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 19, screen_y + 8), 3)
        pygame.draw.line(screen, (0, 0, 0), (screen_x + 13, screen_y + 13), (screen_x + 19, screen_y + 13), 2)
        
        pygame.draw.line(screen, body_color, (screen_x + 8, screen_y + 16), (screen_x + 4, screen_y + 24), 3)
        pygame.draw.line(screen, body_color, (screen_x + 24, screen_y + 16), (screen_x + 28, screen_y + 24), 3)
        
        for i in range(3):
            pygame.draw.line(screen, body_color, (screen_x + 11, screen_y + 16 + i * 4), (screen_x + 21, screen_y + 16 + i * 4), 2)
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('骷髅', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_mage(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (80, 40, 120) if not is_hurt else (255, 255, 255)
        
        pygame.draw.polygon(screen, (60, 20, 90), [
            (screen_x + TILE_SIZE // 2, screen_y),
            (screen_x + 4, screen_y + 16),
            (screen_x + TILE_SIZE - 4, screen_y + 16)
        ])
        pygame.draw.circle(screen, (100, 60, 150), (screen_x + TILE_SIZE // 2, screen_y + 20), 10)
        
        pygame.draw.circle(screen, (180, 100, 255), (screen_x + 13, screen_y + 18), 3)
        pygame.draw.circle(screen, (180, 100, 255), (screen_x + 19, screen_y + 18), 3)
        
        pygame.draw.line(screen, (139, 90, 43), (screen_x + 26, screen_y + 8), (screen_x + 28, screen_y), 3)
        pygame.draw.circle(screen, (100, 150, 255), (screen_x + 28, screen_y), 4)
        
        magic_glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(magic_glow, (100, 100, 255, 40), (28, 0), 8)
        screen.blit(magic_glow, (screen_x, screen_y))
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('黑暗法师', True, (200, 200, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_elite_orc(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (180, 120, 40) if not is_hurt else (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x, screen_y + 10, 32, 20))
        pygame.draw.rect(screen, (140, 90, 30), (screen_x + 2, screen_y + 2, 28, 18))
        
        pygame.draw.circle(screen, (255, 150, 0), (screen_x + 9, screen_y + 8), 5)
        pygame.draw.circle(screen, (255, 150, 0), (screen_x + 23, screen_y + 8), 5)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 9, screen_y + 8), 2)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x + 23, screen_y + 8), 2)
        
        pygame.draw.rect(screen, (200, 50, 50), (screen_x + 7, screen_y - 2, 18, 5))
        
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 12, screen_y + 15), (screen_x + 14, screen_y + 22), (screen_x + 10, screen_y + 22)])
        pygame.draw.polygon(screen, (255, 255, 255), [(screen_x + 20, screen_y + 15), (screen_x + 22, screen_y + 22), (screen_x + 18, screen_y + 22)])
        
        elite_glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(elite_glow, (255, 150, 0, 40), (TILE_SIZE // 2, TILE_SIZE // 2), 18)
        screen.blit(elite_glow, (screen_x, screen_y))
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('★ 精英兽人', True, (255, 200, 100))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_dragon(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True, boss_name='远古巨龙', boss_color=None):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = boss_color if boss_color else (150, 50, 150)
        if is_hurt:
            body_color = (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x, screen_y + 6, 32, 22))
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + 8), 14)
        
        pygame.draw.polygon(screen, body_color, [
            (screen_x + 5, screen_y), (screen_x, screen_y - 8), (screen_x + 10, screen_y + 3)
        ])
        pygame.draw.polygon(screen, body_color, [
            (screen_x + 27, screen_y), (screen_x + 32, screen_y - 8), (screen_x + 22, screen_y + 3)
        ])
        
        eye_color = (255, 255, 0)
        pygame.draw.circle(screen, (255, 100, 0), (screen_x + 11, screen_y + 6), 5)
        pygame.draw.circle(screen, (255, 100, 0), (screen_x + 21, screen_y + 6), 5)
        pygame.draw.circle(screen, eye_color, (screen_x + 11, screen_y + 6), 2)
        pygame.draw.circle(screen, eye_color, (screen_x + 21, screen_y + 6), 2)
        
        pygame.draw.polygon(screen, body_color, [
            (screen_x, screen_y + 16), (screen_x - 6, screen_y + 20), (screen_x, screen_y + 24)
        ])
        pygame.draw.polygon(screen, body_color, [
            (screen_x + 32, screen_y + 16), (screen_x + 38, screen_y + 20), (screen_x + 32, screen_y + 24)
        ])
        
        fire_glow = pygame.Surface((TILE_SIZE + 12, TILE_SIZE + 12), pygame.SRCALPHA)
        pygame.draw.circle(fire_glow, (255, 100, 0, 30), (TILE_SIZE // 2 + 6, TILE_SIZE // 2 + 6), 24)
        screen.blit(fire_glow, (screen_x - 6, screen_y - 6))
        
        self.draw_health_bar(screen, screen_x, screen_y - 12, hp, max_hp, True)
        
        name_text = FONT_NORMAL.render(f'👑 {boss_name}', True, body_color)
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 26))
        screen.blit(name_text, name_rect)
    
    def draw_summoner(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (150, 50, 150) if not is_hurt else (255, 255, 255)
        
        pygame.draw.polygon(screen, (100, 30, 100), [
            (screen_x + TILE_SIZE // 2, screen_y - 4),
            (screen_x + 2, screen_y + 14),
            (screen_x + TILE_SIZE - 2, screen_y + 14)
        ])
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + 18), 10)
        
        pygame.draw.circle(screen, (200, 100, 255), (screen_x + 12, screen_y + 16), 3)
        pygame.draw.circle(screen, (200, 100, 255), (screen_x + 20, screen_y + 16), 3)
        
        pygame.draw.line(screen, (100, 50, 150), (screen_x + 26, screen_y + 4), (screen_x + 28, screen_y - 4), 3)
        pygame.draw.circle(screen, (200, 100, 255), (screen_x + 28, screen_y - 4), 5)
        
        summon_glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(summon_glow, (150, 50, 200, 50), (TILE_SIZE // 2, TILE_SIZE // 2), 16)
        screen.blit(summon_glow, (screen_x, screen_y))
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('召唤法师', True, (200, 150, 255))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_summon_minion(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        body_color = (100, 100, 150) if not is_hurt else (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x + 6, screen_y + 16, 20, 12))
        pygame.draw.ellipse(screen, (80, 80, 120), (screen_x + 8, screen_y + 8, 16, 12))
        
        pygame.draw.circle(screen, (200, 50, 50), (screen_x + 13, screen_y + 12), 2)
        pygame.draw.circle(screen, (200, 50, 50), (screen_x + 19, screen_y + 12), 2)
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('召唤小弟', True, (150, 150, 200))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_invisible_monster(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True, is_invisible=False):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        if is_invisible:
            invisible_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(invisible_surf, (100, 200, 255, 80), (TILE_SIZE // 2, TILE_SIZE // 2), 12)
            pygame.draw.circle(invisible_surf, (150, 220, 255, 50), (TILE_SIZE // 2, TILE_SIZE // 2), 16)
            screen.blit(invisible_surf, (screen_x, screen_y))
            
            status_text = FONT_SMALL.render('👻 隐身中', True, (100, 200, 255))
            status_rect = status_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 8))
            screen.blit(status_text, status_rect)
            return
        
        body_color = (100, 200, 255) if not is_hurt else (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x + 4, screen_y + 14, 24, 14))
        pygame.draw.ellipse(screen, (80, 180, 230), (screen_x + 6, screen_y + 6, 20, 14))
        
        pygame.draw.circle(screen, (200, 255, 255), (screen_x + 12, screen_y + 11), 3)
        pygame.draw.circle(screen, (200, 255, 255), (screen_x + 20, screen_y + 11), 3)
        
        pygame.draw.line(screen, (80, 180, 230), (screen_x + 26, screen_y + 10), (screen_x + 32, screen_y + 18), 2)
        
        ghost_trail = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(ghost_trail, (100, 200, 255, 30), (TILE_SIZE // 2, TILE_SIZE // 2), 18)
        screen.blit(ghost_trail, (screen_x, screen_y))
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render('幽灵刺客', True, (150, 220, 255))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_reviver(self, screen, x, y, camera_x, camera_y, hp, max_hp, is_hurt=False, visible=True, is_down=False, revive_count=0):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        if not visible:
            return
        
        if is_down:
            pygame.draw.ellipse(screen, (100, 80, 80), (screen_x + 2, screen_y + 20, 28, 10))
            pygame.draw.circle(screen, (80, 60, 60), (screen_x + 8, screen_y + 18), 6)
            
            revive_glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            alpha = int(100 + 50 * pygame.time.get_ticks() / 300 % 1)
            pygame.draw.circle(revive_glow, (150, 100, 100, alpha), (TILE_SIZE // 2, TILE_SIZE // 2), 20)
            screen.blit(revive_glow, (screen_x, screen_y))
            
            revive_text = FONT_SMALL.render(f'💀 复活中 {revive_count}/2', True, (200, 150, 150))
            revive_rect = revive_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 8))
            screen.blit(revive_text, revive_rect)
            return
        
        body_color = (150, 100, 100) if not is_hurt else (255, 255, 255)
        
        pygame.draw.ellipse(screen, body_color, (screen_x + 4, screen_y + 12, 24, 18))
        pygame.draw.rect(screen, (120, 80, 80), (screen_x + 6, screen_y + 4, 20, 14))
        
        pygame.draw.circle(screen, (180, 100, 100), (screen_x + 12, screen_y + 9), 3)
        pygame.draw.circle(screen, (180, 100, 100), (screen_x + 20, screen_y + 9), 3)
        
        pygame.draw.line(screen, (80, 50, 50), (screen_x + 10, screen_y + 15), (screen_x + 22, screen_y + 15), 2)
        
        self.draw_health_bar(screen, screen_x, screen_y - 8, hp, max_hp)
        
        name_text = FONT_SMALL.render(f'不死战士 ({2-revive_count})', True, (200, 150, 150))
        name_rect = name_text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y - 18))
        screen.blit(name_text, name_rect)
    
    def draw_health_bar(self, screen, x, y, hp, max_hp, is_boss=False):
        bar_width = TILE_SIZE if not is_boss else TILE_SIZE + 10
        bar_height = 5 if not is_boss else 7
        
        bar_x = x + (TILE_SIZE - bar_width) // 2
        
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, y, bar_width, bar_height))
        
        hp_ratio = max(0, hp / max_hp)
        fill_width = int(bar_width * hp_ratio)
        fill_color = (0, 200, 0) if hp_ratio > 0.3 else (255, 100, 0) if hp_ratio > 0.1 else (255, 0, 0)
        if is_boss:
            fill_color = (200, 50, 200)
        pygame.draw.rect(screen, fill_color, (bar_x, y, fill_width, bar_height))
        
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, y, bar_width, bar_height), 1)


class SkillEffectRenderer:
    def __init__(self):
        pass
    
    def draw_skill_effect(self, screen, effect, camera_x, camera_y):
        screen_x = effect['x'] * TILE_SIZE - int(camera_x)
        screen_y = effect['y'] * TILE_SIZE - int(camera_y)
        progress = 1 - effect['life'] / effect['max_life']
        
        effect_type = effect['type']
        radius = int(20 + progress * 40)
        alpha = int(200 * (1 - progress))
        
        if 'warrior' in effect_type:
            color = (255, 100, 50, alpha)
            if 'ultimate' in effect_type:
                radius = int(30 + progress * 60)
        elif 'mage' in effect_type:
            color = (255, 150, 0, alpha)
            if 'ultimate' in effect_type:
                radius = int(50 + progress * 100)
                color = (255, 100, 0, alpha)
        elif 'rogue' in effect_type:
            color = (100, 255, 100, alpha)
            if 'ultimate' in effect_type:
                color = (50, 200, 50, alpha)
        elif 'paladin' in effect_type:
            color = (255, 255, 150, alpha)
            if 'ultimate' in effect_type:
                radius = int(100 + progress * 200)
                color = (255, 255, 200, alpha)
        else:
            color = (255, 255, 255, alpha)
        
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (radius, radius), radius, 3)
        if 'ultimate' in effect_type:
            pygame.draw.circle(surf, (color[0], color[1], color[2], alpha // 2), (radius, radius), radius - 10)
        screen.blit(surf, (screen_x + TILE_SIZE // 2 - radius, screen_y + TILE_SIZE // 2 - radius))
    
    def draw_damage_numbers(self, screen, damage_numbers, camera_x, camera_y):
        for dn in damage_numbers:
            screen_x = dn.x * TILE_SIZE - int(camera_x) + TILE_SIZE // 2
            screen_y = dn.y * TILE_SIZE - int(camera_y) + TILE_SIZE // 2
            
            if dn.color:
                color = dn.color
            elif dn.is_heal:
                color = (100, 255, 100)
            elif dn.is_crit:
                color = (255, 50, 50)
            else:
                color = (255, 255, 255)
            
            font = FONT_LARGE if dn.is_crit else FONT_NORMAL
            text = font.render(f'+{dn.damage}' if dn.is_heal else f'{dn.damage}', True, color)
            text.set_alpha(dn.alpha)
            
            text_rect = text.get_rect(center=(screen_x, screen_y))
            screen.blit(text, text_rect)
            
            if dn.is_crit:
                crit_text = FONT_SMALL.render('暴击!', True, (255, 200, 0))
                crit_text.set_alpha(dn.alpha)
                crit_rect = crit_text.get_rect(center=(screen_x, screen_y - 25))
                screen.blit(crit_text, crit_rect)

class PlayerRenderer:
    def __init__(self):
        self.skill_effect_renderer = SkillEffectRenderer()
    
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
        
        pygame.draw.line(screen, (139, 90, 43), (screen_x + 26, screen_y + 6), (screen_x + 28, screen_y - 4), 2)
        magic_ball = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(magic_ball, (100, 150, 255, 200), (28, -4), 5)
        pygame.draw.circle(magic_ball, (150, 200, 255, 100), (28, -4), 8)
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
            (screen_x + 26, screen_y + 12), (screen_x + 32, screen_y + 18), (screen_x + 26, screen_y + 22)
        ])
    
    def draw_paladin(self, screen, x, y, camera_x, camera_y, is_hurt=False):
        screen_x = x * TILE_SIZE - int(camera_x)
        screen_y = y * TILE_SIZE - int(camera_y)
        
        body_color = (220, 200, 150) if not is_hurt else (255, 255, 255)
        
        pygame.draw.circle(screen, body_color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2 + 2), 12)
        
        pygame.draw.circle(screen, (255, 220, 180), (screen_x + TILE_SIZE // 2, screen_y + 8), 7)
        
        pygame.draw.circle(screen, (100, 50, 50), (screen_x + 13, screen_y + 7), 2)
        pygame.draw.circle(screen, (100, 50, 50), (screen_x + 19, screen_y + 7), 2)
        
        pygame.draw.rect(screen, (200, 180, 100), (screen_x + 6, screen_y + 2, 20, 5))
        
        pygame.draw.rect(screen, (200, 150, 50), (screen_x + 2, screen_y + 10, 6, 16))
        pygame.draw.rect(screen, (255, 220, 100), (screen_x + 2, screen_y + 10, 6, 3))
        
        pygame.draw.rect(screen, (180, 180, 200), (screen_x + 24, screen_y + 8, 5, 18))
        pygame.draw.rect(screen, (220, 220, 255), (screen_x + 22, screen_y + 6, 9, 5))
        
        aura = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(aura, (255, 255, 200, 30), (TILE_SIZE // 2, TILE_SIZE // 2), 16)
        screen.blit(aura, (screen_x, screen_y))
