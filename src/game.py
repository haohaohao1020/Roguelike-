import pygame
import random
from .config import *
from .map import GameMap
from .entity import Character
from .monster import create_monster, create_elite, create_boss
from .items import Chest, create_random_item, Potion, Gold
from .combat import CombatSystem
from .save_manager import SaveManager, Shop
from .asset_loader import asset_loader
from .renderer import DungeonRenderer, MonsterRenderer, PlayerRenderer

class GameState:
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    INVENTORY = 'inventory'
    SHOP = 'shop'
    GAME_OVER = 'game_over'
    VICTORY = 'victory'
    LEADERBOARD = 'leaderboard'
    CLASS_SELECT = 'class_select'
    TALENT = 'talent'

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('地牢探险 Roguelike')
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.save_manager = SaveManager()
        self.combat = CombatSystem()
        self.shop = Shop()
        
        self.dungeon_renderer = DungeonRenderer()
        self.monster_renderer = MonsterRenderer()
        self.player_renderer = PlayerRenderer()
        
        self.state = GameState.MENU
        self.floor = 1
        self.player = None
        self.game_map = None
        self.entities = []
        self.monsters = []
        self.items = []
        
        self.turn = 0
        self.player_turn = True
        
        self.camera_x = 0
        self.camera_y = 0
        
        self.selected_class = None
        self.menu_selection = 0
        self.inventory_selection = 0
        self.shop_selection = 0
        self.shop_mode = 'buy'
        self.talent_selection = 0
        
        self.message_log = []
        self.room_colors = {}
        self.last_room_type = None
    
    def add_message(self, text):
        self.message_log.append(text)
        if len(self.message_log) > 5:
            self.message_log.pop(0)
    
    def generate_floor(self):
        self.game_map = GameMap(MAP_WIDTH, MAP_HEIGHT, self.floor)
        self.game_map.generate_map()
        
        self.monsters = []
        self.items = []
        
        if self.game_map.rooms:
            start_room = self.game_map.rooms[0]
            self.player.x, self.player.y = start_room.center()
        
        for room in self.game_map.rooms:
            room_color = self.get_room_color(room.room_type)
            self.room_colors[(room.x1, room.y1, room.x2, room.y2)] = room_color
            
            if room.room_type == 'normal':
                num_monsters = random.randint(2, 4)
                for _ in range(num_monsters):
                    x, y = room.get_random_position()
                    if not any(m.x == x and m.y == y for m in self.monsters):
                        monster = create_monster(x, y, self.floor)
                        self.monsters.append(monster)
            elif room.room_type == 'treasure':
                x, y = room.center()
                self.items.append(Chest(x, y))
            elif room.room_type == 'boss':
                if self.floor >= MAX_FLOOR:
                    x, y = room.center()
                    boss = create_boss(x, y, self.floor)
                    self.monsters.append(boss)
                else:
                    if random.random() < 0.4:
                        x, y = room.get_random_position()
                        elite = create_elite(x, y, self.floor)
                        self.monsters.append(elite)
        
        for room in self.game_map.rooms:
            if room.room_type != 'boss' and random.random() < 0.3:
                x, y = room.get_random_position()
                if not any(e.x == x and e.y == y for e in self.monsters + self.items):
                    item_type = random.choice(['gold', 'potion', 'equipment'])
                    if item_type == 'gold':
                        self.items.append(Gold(x, y, random.randint(10, 50)))
                    elif item_type == 'potion':
                        potion_type = random.choice(['health', 'mana'])
                        self.items.append(Potion(x, y, potion_type))
                    else:
                        item = create_random_item(x, y)
                        if item:
                            self.items.append(item)
        
        self.game_map.update_fov(self.player.x, self.player.y, 15)
        self.update_camera()
    
    def get_room_color(self, room_type):
        colors = {
            'normal': (80, 60, 40),
            'treasure': (100, 80, 20),
            'shop': (40, 60, 80),
            'rest': (40, 80, 40),
            'trap': (80, 20, 20),
            'boss': (60, 20, 60)
        }
        return colors.get(room_type, (80, 60, 40))
    
    def new_game(self, class_type):
        self.player = Character(MAP_WIDTH // 2, MAP_HEIGHT // 2, '勇者', class_type)
        self.floor = 1
        self.turn = 0
        self.message_log = []
        self.generate_floor()
        self.state = GameState.PLAYING
        self.add_message('欢迎来到地牢！')
    
    def go_downstairs(self):
        if self.floor >= MAX_FLOOR:
            self.victory()
        else:
            self.floor += 1
            self.generate_floor()
            self.add_message(f'进入了第 {self.floor} 层！')
    
    def move_player(self, dx, dy):
        if not self.player_turn:
            return
        
        if self.player.has_status('stunned'):
            self.add_message('你被眩晕了，无法移动！')
            self.end_player_turn()
            return
        
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        for monster in self.monsters:
            if monster.x == new_x and monster.y == new_y:
                attack_count = self.player.get_total_attack_count()
                for i in range(attack_count):
                    if monster.is_alive():
                        self.combat.attack(self.player, monster)
                if not monster.is_alive():
                    self.monsters.remove(monster)
                self.end_player_turn()
                return
        
        for item in self.items[:]:
            if item.x == new_x and item.y == new_y:
                if hasattr(item, 'is_open') and not item.is_open:
                    msg = item.open(self.player)
                    self.add_message(msg)
                    self.items.remove(item)
                elif hasattr(item, 'amount'):
                    self.player.gold += item.amount
                    self.items.remove(item)
                    self.add_message(f'拾取了 {item.amount} 金币！')
                else:
                    if self.player.add_item(item):
                        self.items.remove(item)
                        self.add_message(f'拾取了 {item.name}！')
        
        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            if self.game_map.tiles[new_x][new_y] == 0:
                self.player.move(dx, dy)
                self.game_map.add_to_path(self.player.x, self.player.y)
                
                affected, msg = self.game_map.apply_terrain_effect(self.player, self.player.x, self.player.y)
                if affected and msg:
                    self.add_message(msg)
                
                self.game_map.update_fov(self.player.x, self.player.y, 15)
                self.update_camera()
        
        room = self.game_map.get_room_at(self.player.x, self.player.y)
        current_room_type = room.room_type if room else None
        
        if current_room_type == 'shop' and self.last_room_type != 'shop':
            self.state = GameState.SHOP
            self.shop.refresh_items()
            self.add_message('欢迎来到商店！')
        elif current_room_type == 'rest' and self.last_room_type != 'rest':
            heal_amount = int(self.player.max_hp * 0.3)
            mp_amount = int(self.player.max_mp * 0.3)
            self.player.heal(heal_amount)
            self.player.restore_mp(mp_amount)
            self.add_message(f'在休息点恢复了 {heal_amount} 生命和 {mp_amount} 魔力！')
        elif current_room_type == 'altar' and self.last_room_type != 'altar':
            self.add_message('你发现了一座神秘的祭坛！按 E 键献祭生命获得强化。')
        elif current_room_type == 'blacksmith' and self.last_room_type != 'blacksmith':
            self.add_message('你找到了铁匠铺！按 E 键强化装备。')
        elif current_room_type == 'library' and self.last_room_type != 'library':
            self.add_message('古老的图书馆！按 E 键阅读获得永久属性加成。')
        
        self.last_room_type = current_room_type
        
        if self.game_map.stairs_pos:
            sx, sy = self.game_map.stairs_pos
            if self.player.x == sx and self.player.y == sy:
                self.go_downstairs()
        
        self.end_player_turn()
    
    def end_player_turn(self):
        self.player_turn = False
        self.turn += 1
        
        status_messages = self.player.update_status_effects()
        for msg in status_messages:
            self.add_message(msg)
        
        self.player.apply_passive_effects()
        
        for monster in self.monsters:
            if monster.is_alive():
                monster.update_status_effects()
                monster.update_ai(self.game_map, self.player, self.monsters + [self.player])
                
                distance = monster.get_distance_to(self.player)
                if distance <= 1.5 and monster.attack_cooldown <= 0:
                    attack_count = 1 if random.random() < 0.7 else 2
                    for _ in range(attack_count):
                        if self.player.hp > 0:
                            self.combat.attack(monster, self.player)
                    monster.attack_cooldown = 2
                elif monster.attack_cooldown > 0:
                    monster.attack_cooldown -= 1
                
                self.game_map.apply_terrain_effect(monster, monster.x, monster.y)
        
        if self.player.hp <= 0:
            self.game_over()
        
        for buff in self.player.buffs[:]:
            buff['duration'] -= 1
            if buff['duration'] <= 0:
                if buff['type'] == 'strength':
                    self.player.str -= buff['value']
                elif buff['type'] == 'dexterity':
                    self.player.dex -= buff['value']
                self.player.buffs.remove(buff)
        
        self.combat.update()
        
        if self.player.level_up_animation > 0:
            self.player.level_up_animation -= 1
            if self.player.level_up_animation <= 0:
                self.player.is_leveling_up = False
        
        self.player_turn = True
    
    def update_camera(self):
        target_x = self.player.x * TILE_SIZE - SCREEN_WIDTH // 2
        target_y = self.player.y * TILE_SIZE - SCREEN_HEIGHT // 2
        
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        self.camera_x = max(0, min(self.camera_x, MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT))
    
    def render(self):
        self.screen.fill((10, 10, 15))
        
        if self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.CLASS_SELECT:
            self.render_class_select()
        elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.INVENTORY, GameState.SHOP, GameState.TALENT]:
            self.render_game()
            if self.state == GameState.PAUSED:
                self.render_pause_menu()
            elif self.state == GameState.INVENTORY:
                self.render_inventory()
            elif self.state == GameState.SHOP:
                self.render_shop()
            elif self.state == GameState.TALENT:
                self.render_talent()
        elif self.state == GameState.GAME_OVER:
            self.render_game_over()
        elif self.state == GameState.VICTORY:
            self.render_victory()
        elif self.state == GameState.LEADERBOARD:
            self.render_leaderboard()
        
        pygame.display.flip()
    
    def render_game(self):
        start_x = max(0, int(self.camera_x // TILE_SIZE) - 1)
        start_y = max(0, int(self.camera_y // TILE_SIZE) - 1)
        end_x = min(MAP_WIDTH, int((self.camera_x + SCREEN_WIDTH) // TILE_SIZE) + 2)
        end_y = min(MAP_HEIGHT, int((self.camera_y + SCREEN_HEIGHT) // TILE_SIZE) + 2)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                if self.game_map.explored[x][y]:
                    tile = self.game_map.tiles[x][y]
                    
                    if tile == 0:
                        room = self.game_map.get_room_at(x, y)
                        room_type = room.room_type if room else 'corridor'
                        terrain = self.game_map.terrain[x][y]
                        self.dungeon_renderer.draw_floor(self.screen, x, y, self.camera_x, self.camera_y, room_type, terrain, self.game_map.visible[x][y])
                    else:
                        self.dungeon_renderer.draw_wall(self.screen, x, y, self.camera_x, self.camera_y, self.game_map.visible[x][y])
                else:
                    screen_x = x * TILE_SIZE - int(self.camera_x)
                    screen_y = y * TILE_SIZE - int(self.camera_y)
                    pygame.draw.rect(self.screen, (5, 5, 8), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        
        if self.game_map.stairs_pos:
            sx, sy = self.game_map.stairs_pos
            if self.game_map.explored[sx][sy]:
                self.dungeon_renderer.draw_stairs(self.screen, sx, sy, self.camera_x, self.camera_y, self.game_map.visible[sx][sy])
        
        for item in self.items:
            if self.game_map.explored[item.x][item.y] and self.game_map.visible[item.x][item.y]:
                if hasattr(item, 'is_open'):
                    self.dungeon_renderer.draw_chest(self.screen, item.x, item.y, self.camera_x, self.camera_y, item.is_open, True)
                elif hasattr(item, 'amount'):
                    self.dungeon_renderer.draw_gold(self.screen, item.x, item.y, self.camera_x, self.camera_y, item.amount, True)
        
        for monster in self.monsters:
            if self.game_map.explored[monster.x][monster.y] and self.game_map.visible[monster.x][monster.y]:
                if monster.monster_type == 'boss':
                    self.monster_renderer.draw_dragon(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                elif monster.monster_type == 'elite':
                    self.monster_renderer.draw_elite_orc(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                else:
                    monster_name = monster.name
                    if '哥布林' in monster_name:
                        self.monster_renderer.draw_goblin(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '兽人' in monster_name:
                        self.monster_renderer.draw_orc(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '骷髅' in monster_name:
                        self.monster_renderer.draw_skeleton(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '法师' in monster_name:
                        self.monster_renderer.draw_mage(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    else:
                        self.monster_renderer.draw_goblin(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
        
        class_name = CLASSES[self.player.class_type]['name']
        if class_name == '战士':
            self.player_renderer.draw_warrior(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
        elif class_name == '法师':
            self.player_renderer.draw_mage(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
        elif class_name == '盗贼':
            self.player_renderer.draw_rogue(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
        elif class_name == '圣骑士':
            self.player_renderer.draw_paladin(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
        
        if self.player.is_leveling_up:
            px = self.player.x * TILE_SIZE - int(self.camera_x) + TILE_SIZE // 2
            py = self.player.y * TILE_SIZE - int(self.camera_y) + TILE_SIZE // 2
            
            progress = 1 - self.player.level_up_animation / 120
            radius = int(20 + progress * 40)
            alpha = int(255 * (1 - progress))
            
            level_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(level_surf, (255, 215, 0, alpha), (radius, radius), radius, 3)
            self.screen.blit(level_surf, (px - radius, py - radius))
            
            if self.player.level_up_animation > 60:
                text = FONT_LARGE.render(f'LV.{self.player.level}!', True, GOLD)
                text_rect = text.get_rect(center=(px, py - 30 - int((120 - self.player.level_up_animation) * 0.3)))
                self.screen.blit(text, text_rect)
        
        self.render_ui()
    
    def render_ui(self):
        top_panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 400, 10, 800, 100)
        pygame.draw.rect(self.screen, (30, 30, 40), top_panel_rect)
        pygame.draw.rect(self.screen, (80, 80, 100), top_panel_rect, 2)
        
        class_name = CLASSES[self.player.class_type]['name']
        title_text = FONT_LARGE.render(f'{class_name}', True, GOLD)
        level_text = FONT_NORMAL.render(f'Lv.{self.player.level}', True, WHITE)
        title_rect = title_text.get_rect(center=(top_panel_rect.centerx, top_panel_rect.y + 20))
        level_rect = level_text.get_rect(center=(top_panel_rect.centerx + 100, top_panel_rect.y + 25))
        self.screen.blit(title_text, title_rect)
        self.screen.blit(level_text, level_rect)
        
        bar_width = 350
        bar_x = top_panel_rect.centerx - bar_width // 2
        
        y = top_panel_rect.y + 50
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, (80, 0, 0), (bar_x, y, bar_width, 18))
        pygame.draw.rect(self.screen, (220, 50, 50), (bar_x, y, int(bar_width * hp_ratio), 18))
        pygame.draw.rect(self.screen, (255, 100, 100), (bar_x, y, int(bar_width * hp_ratio), 6))
        hp_text = FONT_SMALL.render(f'❤️ {self.player.hp}/{self.player.max_hp}', True, WHITE)
        hp_text_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, y + 9))
        self.screen.blit(hp_text, hp_text_rect)
        
        y += 22
        mp_ratio = self.player.mp / self.player.max_mp
        pygame.draw.rect(self.screen, (0, 0, 80), (bar_x, y, bar_width, 18))
        pygame.draw.rect(self.screen, (50, 100, 220), (bar_x, y, int(bar_width * mp_ratio), 18))
        pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, y, int(bar_width * mp_ratio), 6))
        mp_text = FONT_SMALL.render(f'💧 {self.player.mp}/{self.player.max_mp}', True, WHITE)
        mp_text_rect = mp_text.get_rect(center=(bar_x + bar_width // 2, y + 9))
        self.screen.blit(mp_text, mp_text_rect)
        
        left_panel_rect = pygame.Rect(10, 120, 200, 300)
        pygame.draw.rect(self.screen, (30, 30, 40), left_panel_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), left_panel_rect, 2)
        
        y = left_panel_rect.y + 15
        stats_title = FONT_NORMAL.render('属性', True, GOLD)
        self.screen.blit(stats_title, (left_panel_rect.x + 15, y))
        y += 30
        
        stats_text = [
            f'⚔️ 力量: {self.player.get_total_str()}',
            f'🏃 敏捷: {self.player.get_total_dex()}',
            f'✨ 智力: {self.player.get_total_int()}',
            f'🛡️ 防御: {self.player.get_total_defense()}'
        ]
        for text in stats_text:
            stat_text = FONT_SMALL.render(text, True, (200, 200, 200))
            self.screen.blit(stat_text, (left_panel_rect.x + 15, y))
            y += 25
        
        y += 10
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        self.screen.blit(gold_text, (left_panel_rect.x + 15, y))
        
        if self.player.status_effects:
            y += 30
            status_title = FONT_SMALL.render('状态效果:', True, GOLD)
            self.screen.blit(status_title, (left_panel_rect.x + 15, y))
            y += 20
            for status in self.player.status_effects[:4]:
                status_color = {
                    'poison': (100, 200, 100),
                    'burning': (255, 100, 50),
                    'frozen': (150, 200, 255),
                    'stunned': (200, 200, 100),
                    'haste': (255, 255, 100),
                    'shield': (100, 150, 255),
                    'invisible': (200, 200, 255)
                }.get(status['type'], WHITE)
                status_text = FONT_SMALL.render(f"  {status['type']} ({status['duration']})", True, status_color)
                self.screen.blit(status_text, (left_panel_rect.x + 15, y))
                y += 18
        
        right_panel_rect = pygame.Rect(SCREEN_WIDTH - 220, 120, 210, 350)
        pygame.draw.rect(self.screen, (30, 30, 40), right_panel_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), right_panel_rect, 2)
        
        minimap_size = 200
        minimap_rect = pygame.Rect(right_panel_rect.x + 5, right_panel_rect.y + 10, minimap_size, minimap_size)
        pygame.draw.rect(self.screen, (15, 15, 25), minimap_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), minimap_rect, 2)
        
        scale = minimap_size / MAP_WIDTH
        
        for (x, y_map) in self.game_map.walked_path:
            if self.game_map.explored[x][y_map]:
                px = int(minimap_rect.x + x * scale)
                py = int(minimap_rect.y + y_map * scale)
                pygame.draw.rect(self.screen, (60, 50, 35), (px, py, max(1, int(scale)), max(1, int(scale))))
        
        for x in range(MAP_WIDTH):
            for y_map in range(MAP_HEIGHT):
                if self.game_map.explored[x][y_map] and (x, y_map) not in self.game_map.walked_path:
                    if self.game_map.tiles[x][y_map] == 0:
                        color = (80, 60, 40) if not self.game_map.visible[x][y_map] else (120, 100, 70)
                    else:
                        color = (40, 40, 50)
                    px = int(minimap_rect.x + x * scale)
                    py = int(minimap_rect.y + y_map * scale)
                    pygame.draw.rect(self.screen, color, (px, py, max(1, int(scale)), max(1, int(scale))))
        
        for monster in self.monsters:
            if self.game_map.explored[monster.x][monster.y]:
                px = int(minimap_rect.x + monster.x * scale)
                py = int(minimap_rect.y + monster.y * scale)
                color = RED if self.game_map.visible[monster.x][monster.y] else (100, 0, 0)
                pygame.draw.circle(self.screen, color, (px, py), 3)
        
        for item in self.items:
            if self.game_map.explored[item.x][item.y]:
                px = int(minimap_rect.x + item.x * scale)
                py = int(minimap_rect.y + item.y * scale)
                if hasattr(item, 'is_open'):
                    color = YELLOW
                elif hasattr(item, 'amount'):
                    color = (255, 215, 0)
                else:
                    color = (180, 180, 255)
                pygame.draw.circle(self.screen, color, (px, py), 3)
        
        if self.game_map.stairs_pos:
            sx, sy = self.game_map.stairs_pos
            if self.game_map.explored[sx][sy]:
                px = int(minimap_rect.x + sx * scale)
                py = int(minimap_rect.y + sy * scale)
                pygame.draw.circle(self.screen, YELLOW, (px, py), 4)
        
        px = int(minimap_rect.x + self.player.x * scale)
        py = int(minimap_rect.y + self.player.y * scale)
        pygame.draw.circle(self.screen, CYAN, (px, py), 5)
        pygame.draw.circle(self.screen, WHITE, (px, py), 3)
        
        floor_text = FONT_NORMAL.render(f'第 {self.floor} 层', True, WHITE)
        floor_rect = floor_text.get_rect(center=(minimap_rect.centerx, minimap_rect.y + minimap_size + 15))
        self.screen.blit(floor_text, floor_rect)
        
        exp_bar_rect = pygame.Rect(right_panel_rect.x + 10, minimap_rect.y + minimap_size + 45, 190, 15)
        pygame.draw.rect(self.screen, (40, 40, 0), exp_bar_rect)
        exp_ratio = self.player.exp / self.player.exp_to_next
        pygame.draw.rect(self.screen, (200, 200, 0), (exp_bar_rect.x, exp_bar_rect.y, int(190 * exp_ratio), 15))
        exp_text = FONT_SMALL.render(f'EXP: {self.player.exp}/{self.player.exp_to_next}', True, WHITE)
        exp_rect = exp_text.get_rect(center=(exp_bar_rect.centerx, exp_bar_rect.y + 30))
        self.screen.blit(exp_text, exp_rect)
        
        log_rect = pygame.Rect(10, SCREEN_HEIGHT - 150, SCREEN_WIDTH - 240, 140)
        pygame.draw.rect(self.screen, (25, 25, 35), log_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), log_rect, 2)
        
        log_title = FONT_NORMAL.render('战斗日志', True, GRAY)
        self.screen.blit(log_title, (log_rect.x + 10, log_rect.y + 5))
        
        y_log = log_rect.y + 35
        for msg in self.message_log[-5:]:
            msg_text = FONT_SMALL.render(msg, True, (220, 220, 220))
            self.screen.blit(msg_text, (log_rect.x + 15, y_log))
            y_log += 22
        
        help_bg = pygame.Rect(10, SCREEN_HEIGHT - 55, 450, 45)
        pygame.draw.rect(self.screen, (25, 25, 35), help_bg)
        pygame.draw.rect(self.screen, (60, 60, 80), help_bg, 2)
        
        help_lines = [
            '方向键/WASD:移动 | 空格:攻击 | E:交互 | I:背包 | T:天赋 | ESC:暂停'
        ]
        y_help = help_bg.y + 12
        for line in help_lines:
            help_text = FONT_SMALL.render(line, True, GRAY)
            self.screen.blit(help_text, (help_bg.x + 10, y_help))
    
    def render_menu(self):
        title_bg = pygame.Rect(SCREEN_WIDTH // 2 - 300, 80, 600, 120)
        pygame.draw.rect(self.screen, (40, 40, 60), title_bg)
        pygame.draw.rect(self.screen, GOLD, title_bg, 3)
        
        title = FONT_TITLE.render('地牢探险', True, GOLD)
        subtitle = FONT_LARGE.render('Roguelike', True, (180, 180, 200))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 130))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 175))
        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)
        
        menu_items = ['开始游戏', '继续游戏', '排行榜', '退出游戏']
        for i, item in enumerate(menu_items):
            y = 280 + i * 70
            item_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, y, 400, 55)
            
            if i == self.menu_selection:
                pygame.draw.rect(self.screen, (60, 70, 90), item_rect)
                pygame.draw.rect(self.screen, GOLD, item_rect, 3)
                color = YELLOW
            else:
                pygame.draw.rect(self.screen, (35, 35, 50), item_rect)
                pygame.draw.rect(self.screen, (70, 70, 90), item_rect, 2)
                color = WHITE
            
            text = FONT_LARGE.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y + 28))
            self.screen.blit(text, text_rect)
        
        footer_text = FONT_SMALL.render('使用方向键选择，按回车确认', True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(footer_text, footer_rect)
    
    def render_class_select(self):
        title_bg = pygame.Rect(SCREEN_WIDTH // 2 - 300, 40, 600, 80)
        pygame.draw.rect(self.screen, (40, 40, 60), title_bg)
        pygame.draw.rect(self.screen, GOLD, title_bg, 3)
        
        title = FONT_LARGE.render('选择你的职业', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        class_data = [
            ('warrior', '战士', '血厚防高，近战强力', RED, ['HP: 150', 'MP: 30', '力量: 18', '防御: 15']),
            ('mage', '法师', '远程魔法，伤害爆炸', BLUE, ['HP: 80', 'MP: 120', '智力: 20', '魔法伤害高']),
            ('rogue', '盗贼', '敏捷灵活，背刺暴击', GREEN, ['HP: 100', 'MP: 50', '敏捷: 20', '闪避率高']),
            ('paladin', '圣骑士', '能奶能抗，神圣光环', (255, 215, 0), ['HP: 130', 'MP: 80', '防御: 18', '神圣光环'])
        ]
        
        for i, (key, name, desc, color, stats) in enumerate(class_data):
            x = 80 + i * 350
            panel_rect = pygame.Rect(x, 150, 300, 420)
            
            if i == self.menu_selection:
                bg_color = (50, 50, 70)
                border_color = GOLD
            else:
                bg_color = (30, 30, 45)
                border_color = (70, 70, 90)
            
            pygame.draw.rect(self.screen, bg_color, panel_rect)
            pygame.draw.rect(self.screen, border_color, panel_rect, 3)
            
            class_title = FONT_LARGE.render(name, True, color)
            self.screen.blit(class_title, (x + 30, 170))
            
            pygame.draw.circle(self.screen, color, (x + 150, 260), 40)
            pygame.draw.circle(self.screen, WHITE, (x + 150, 260), 40, 3)
            pygame.draw.circle(self.screen, WHITE, (x + 135, 250), 8)
            pygame.draw.circle(self.screen, WHITE, (x + 165, 250), 8)
            pygame.draw.circle(self.screen, BLACK, (x + 135, 250), 4)
            pygame.draw.circle(self.screen, BLACK, (x + 165, 250), 4)
            
            y = 320
            for stat in stats:
                stat_text = FONT_NORMAL.render(stat, True, WHITE)
                self.screen.blit(stat_text, (x + 30, y))
                y += 30
            
            desc_text = FONT_SMALL.render(desc, True, GRAY)
            self.screen.blit(desc_text, (x + 30, y + 20))
        
        footer_text = FONT_NORMAL.render('按 ← → 选择职业，按回车键开始游戏', True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(footer_text, footer_rect)
    
    def render_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 180, 500, 360)
        pygame.draw.rect(self.screen, (35, 35, 50), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        title = FONT_LARGE.render('游戏暂停', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140))
        self.screen.blit(title, title_rect)
        
        menu_items = ['继续游戏', '保存游戏', '返回主菜单']
        for i, item in enumerate(menu_items):
            y = SCREEN_HEIGHT // 2 - 60 + i * 70
            item_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, y, 360, 50)
            
            if i == self.menu_selection:
                pygame.draw.rect(self.screen, (60, 70, 90), item_rect)
                pygame.draw.rect(self.screen, GOLD, item_rect, 2)
                color = YELLOW
            else:
                pygame.draw.rect(self.screen, (50, 50, 70), item_rect)
                color = WHITE
            
            text = FONT_LARGE.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y + 25))
            self.screen.blit(text, text_rect)
    
    def render_inventory(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 400, 80, 800, 560)
        pygame.draw.rect(self.screen, (30, 30, 45), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        title = FONT_LARGE.render('背包', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 110))
        self.screen.blit(title, title_rect)
        
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        self.screen.blit(gold_text, (SCREEN_WIDTH // 2 + 300, 110))
        
        items_rect = pygame.Rect(panel_rect.x + 20, 150, 450, 400)
        pygame.draw.rect(self.screen, (25, 25, 35), items_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), items_rect, 2)
        
        y = 160
        for i, item in enumerate(self.player.inventory[:15]):
            if i == self.inventory_selection:
                bg_color = (60, 70, 90)
                text_color = YELLOW
            else:
                bg_color = (35, 35, 50)
                text_color = WHITE
            
            item_bg = pygame.Rect(items_rect.x + 10, y, 430, 25)
            pygame.draw.rect(self.screen, bg_color, item_bg)
            
            item_text = FONT_NORMAL.render(f'{i + 1}. {item.name}', True, text_color)
            self.screen.blit(item_text, (items_rect.x + 20, y + 2))
            y += 26
        
        if self.player.inventory and 0 <= self.inventory_selection < len(self.player.inventory):
            detail_rect = pygame.Rect(panel_rect.x + 490, 150, 290, 400)
            pygame.draw.rect(self.screen, (25, 25, 35), detail_rect)
            pygame.draw.rect(self.screen, (60, 60, 80), detail_rect, 2)
            
            selected = self.player.inventory[self.inventory_selection]
            
            name_text = FONT_NORMAL.render(selected.name, True, GOLD)
            self.screen.blit(name_text, (detail_rect.x + 15, 165))
            
            y = 200
            if hasattr(selected, 'slot'):
                slot_names = {
                    'weapon': '武器',
                    'armor': '盔甲',
                    'helmet': '头盔',
                    'boots': '靴子',
                    'accessory': '饰品'
                }
                type_text = FONT_SMALL.render(f'类型: {slot_names.get(selected.slot, "其他")}', True, WHITE)
                self.screen.blit(type_text, (detail_rect.x + 15, y))
                y += 25
                
                if hasattr(selected, 'stats'):
                    for stat, value in selected.stats.items():
                        stat_names = {
                            'damage': '伤害',
                            'defense': '防御',
                            'hp': '生命',
                            'mp': '魔力',
                            'str': '力量',
                            'dex': '敏捷',
                            'int': '智力'
                        }
                        stat_name = stat_names.get(stat, stat)
                        stat_text = FONT_SMALL.render(f'{stat_name}: +{value}', True, GREEN)
                        self.screen.blit(stat_text, (detail_rect.x + 15, y))
                        y += 22
            
            value_text = FONT_SMALL.render(f'价值: {selected.value} 金币', True, GRAY)
            self.screen.blit(value_text, (detail_rect.x + 15, y + 10))
        
        help_bg = pygame.Rect(panel_rect.x + 20, panel_rect.y + panel_rect.height - 60, 760, 45)
        pygame.draw.rect(self.screen, (25, 25, 35), help_bg)
        
        help_lines = [
            '↑↓: 选择物品 | E: 装备 | U: 使用 | ESC: 关闭背包'
        ]
        y = help_bg.y + 8
        for line in help_lines:
            help_text = FONT_NORMAL.render(line, True, GRAY)
            self.screen.blit(help_text, (help_bg.x + 20, y))
            y += 18
    
    def render_shop(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 450, 60, 900, 620)
        pygame.draw.rect(self.screen, (30, 30, 45), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        title = FONT_LARGE.render('商店', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 95))
        self.screen.blit(title, title_rect)
        
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        self.screen.blit(gold_text, (SCREEN_WIDTH // 2 + 350, 95))
        
        mode_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 95, 240, 35)
        if self.shop_mode == 'buy':
            pygame.draw.rect(self.screen, (40, 70, 100), mode_rect)
            mode_text = FONT_NORMAL.render('购买模式', True, CYAN)
        else:
            pygame.draw.rect(self.screen, (70, 70, 40), mode_rect)
            mode_text = FONT_NORMAL.render('出售模式', True, YELLOW)
        mode_rect_text = mode_text.get_rect(center=(SCREEN_WIDTH // 2, 112))
        self.screen.blit(mode_text, mode_rect_text)
        
        items_rect = pygame.Rect(panel_rect.x + 20, 150, 860, 420)
        pygame.draw.rect(self.screen, (25, 25, 35), items_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), items_rect, 2)
        
        items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
        
        y = 160
        for i, item in enumerate(items[:14]):
            if i == self.shop_selection:
                bg_color = (60, 70, 90)
                text_color = YELLOW
            else:
                bg_color = (35, 35, 50)
                text_color = WHITE
            
            item_bg = pygame.Rect(items_rect.x + 10, y, 840, 28)
            pygame.draw.rect(self.screen, bg_color, item_bg)
            
            price = item.value if self.shop_mode == 'buy' else max(1, item.value // 2)
            item_text = FONT_NORMAL.render(f'{i + 1}. {item.name} - {price} 金币', True, text_color)
            self.screen.blit(item_text, (items_rect.x + 20, y + 3))
            y += 30
        
        buy_btn_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + panel_rect.height - 60, 200, 45)
        sell_btn_rect = pygame.Rect(panel_rect.x + 240, panel_rect.y + panel_rect.height - 60, 200, 45)
        exit_btn_rect = pygame.Rect(panel_rect.x + panel_rect.width - 220, panel_rect.y + panel_rect.height - 60, 200, 45)
        
        if self.shop_mode == 'buy':
            pygame.draw.rect(self.screen, (40, 100, 60), buy_btn_rect)
            pygame.draw.rect(self.screen, (60, 60, 80), sell_btn_rect)
        else:
            pygame.draw.rect(self.screen, (60, 60, 80), buy_btn_rect)
            pygame.draw.rect(self.screen, (100, 80, 40), sell_btn_rect)
        
        pygame.draw.rect(self.screen, (100, 40, 40), exit_btn_rect)
        
        buy_text = FONT_NORMAL.render('购买', True, WHITE)
        sell_text = FONT_NORMAL.render('出售', True, WHITE)
        exit_text = FONT_NORMAL.render('离开商店', True, WHITE)
        
        buy_text_rect = buy_text.get_rect(center=buy_btn_rect.center)
        sell_text_rect = sell_text.get_rect(center=sell_btn_rect.center)
        exit_text_rect = exit_text.get_rect(center=exit_btn_rect.center)
        
        self.screen.blit(buy_text, buy_text_rect)
        self.screen.blit(sell_text, sell_text_rect)
        self.screen.blit(exit_text, exit_text_rect)
        
        self.shop_buy_btn = buy_btn_rect
        self.shop_sell_btn = sell_btn_rect
        self.shop_exit_btn = exit_btn_rect
    
    def render_talent(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 450, 50, 900, 650)
        pygame.draw.rect(self.screen, (25, 25, 35), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        title = FONT_LARGE.render('天赋树', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 85))
        self.screen.blit(title, title_rect)
        
        points_text = FONT_NORMAL.render(f'天赋点数: {self.player.skill_points}', True, WHITE)
        points_rect = points_text.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self.screen.blit(points_text, points_rect)
        
        talent_categories = [
            ('力量', 'strength', RED, 100),
            ('敏捷', 'dexterity', GREEN, 250),
            ('智力', 'intelligence', BLUE, 400),
            ('防御', 'defense', (150, 150, 200), 550),
            ('生命', 'hp', (255, 100, 100), 700),
            ('魔力', 'mp', (100, 150, 255), 850)
        ]
        
        talent_names = {
            'strength': ['蛮力 I', '蛮力 II', '蛮力 III'],
            'dexterity': ['灵动 I', '灵动 II', '灵动 III'],
            'intelligence': ['智慧 I', '智慧 II', '智慧 III'],
            'defense': ['坚韧 I', '坚韧 II', '坚韧 III'],
            'hp': ['体魄 I', '体魄 II', '体魄 III'],
            'mp': ['魔力 I', '魔力 II', '魔力 III']
        }
        
        talent_values = {
            'strength': ['+3 力量', '+5 力量', '+8 力量'],
            'dexterity': ['+3 敏捷', '+5 敏捷', '+8 敏捷'],
            'intelligence': ['+3 智力', '+5 智力', '+8 智力'],
            'defense': ['+3 防御', '+5 防御', '+8 防御'],
            'hp': ['+30 生命', '+50 生命', '+80 生命'],
            'mp': ['+20 魔力', '+35 魔力', '+50 魔力']
        }
        
        total_talents = len(talent_categories) * 3
        
        for cat_idx, (cat_name, cat_key, cat_color, x_pos) in enumerate(talent_categories):
            cat_text = FONT_NORMAL.render(cat_name, True, cat_color)
            self.screen.blit(cat_text, (panel_rect.x + x_pos, 160))
            
            for tier in range(3):
                talent_id = f'{cat_key}_{tier + 1}'
                talent_index = cat_idx * 3 + tier
                is_owned = self.player.talents.get(talent_id, False)
                can_unlock, message = self.player.can_unlock_talent(talent_id)
                is_selected = self.talent_selection == talent_index
                
                talent_rect = pygame.Rect(panel_rect.x + x_pos - 10, 200 + tier * 120, 140, 100)
                
                if is_owned:
                    bg_color = (50, 100, 50)
                    border_color = GOLD
                elif is_selected:
                    bg_color = (60, 70, 90)
                    border_color = YELLOW
                elif can_unlock:
                    bg_color = (40, 50, 60)
                    border_color = (100, 150, 200)
                else:
                    bg_color = (30, 30, 40)
                    border_color = (80, 80, 100)
                
                pygame.draw.rect(self.screen, bg_color, talent_rect)
                pygame.draw.rect(self.screen, border_color, talent_rect, 2)
                
                name_text = FONT_SMALL.render(talent_names[cat_key][tier], True, WHITE)
                name_rect = name_text.get_rect(center=(talent_rect.centerx, talent_rect.y + 25))
                self.screen.blit(name_text, name_rect)
                
                value_text = FONT_SMALL.render(talent_values[cat_key][tier], True, GREEN)
                value_rect = value_text.get_rect(center=(talent_rect.centerx, talent_rect.y + 50))
                self.screen.blit(value_text, value_rect)
                
                if is_owned:
                    status_text = FONT_SMALL.render('✓ 已学会', True, GOLD)
                elif not can_unlock:
                    status_text = FONT_SMALL.render(message, True, RED)
                else:
                    status_text = FONT_SMALL.render('按回车学习', True, YELLOW)
                status_rect = status_text.get_rect(center=(talent_rect.centerx, talent_rect.y + 78))
                self.screen.blit(status_text, status_rect)
        
        help_bg = pygame.Rect(panel_rect.x + 20, panel_rect.y + panel_rect.height - 50, 860, 35)
        pygame.draw.rect(self.screen, (25, 25, 35), help_bg)
        help_text = FONT_NORMAL.render('方向键:选择 | 回车:学习 | ESC:关闭', True, GRAY)
        help_rect = help_text.get_rect(center=help_bg.center)
        self.screen.blit(help_text, help_rect)
    
    def render_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((50, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        title = FONT_TITLE.render('游戏结束', True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        stats = [
            f'到达层数: 第 {self.floor} 层',
            f'最终等级: Lv.{self.player.level}',
            f'获得金币: {self.player.gold}',
            f'击败怪物数: {self.turn}'
        ]
        
        y = 300
        for stat in stats:
            stat_text = FONT_LARGE.render(stat, True, WHITE)
            stat_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(stat_text, stat_rect)
            y += 50
        
        footer_text = FONT_NORMAL.render('按任意键返回主菜单', True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(footer_text, footer_rect)
    
    def render_victory(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 50, 20, 200))
        self.screen.blit(overlay, (0, 0))
        
        for _ in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(self.screen, GOLD, (x, y), random.randint(3, 8))
        
        title = FONT_TITLE.render('🎉 胜利！🎉', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)
        
        subtitle = FONT_LARGE.render('恭喜你击败了远古巨龙！', True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(subtitle, subtitle_rect)
        
        stats = [
            f'通关层数: {self.floor} 层',
            f'最终等级: Lv.{self.player.level}',
            f'剩余生命: {self.player.hp}/{self.player.max_hp}',
            f'获得金币: {self.player.gold}'
        ]
        
        y = 320
        for stat in stats:
            stat_text = FONT_LARGE.render(stat, True, WHITE)
            stat_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(stat_text, stat_rect)
            y += 50
        
        footer_text = FONT_NORMAL.render('按任意键返回主菜单', True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(footer_text, footer_rect)
    
    def render_leaderboard(self):
        self.screen.fill((15, 15, 25))
        
        title_bg = pygame.Rect(SCREEN_WIDTH // 2 - 300, 50, 600, 80)
        pygame.draw.rect(self.screen, (40, 40, 60), title_bg)
        pygame.draw.rect(self.screen, GOLD, title_bg, 3)
        
        title = FONT_TITLE.render('🏆 排行榜 🏆', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(title, title_rect)
        
        board_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, 160, 700, 450)
        pygame.draw.rect(self.screen, (25, 25, 40), board_rect)
        pygame.draw.rect(self.screen, (70, 70, 90), board_rect, 2)
        
        leaderboard = self.save_manager.get_leaderboard()
        
        if not leaderboard:
            empty_text = FONT_LARGE.render('暂无记录，快去创造历史吧！', True, GRAY)
            empty_rect = empty_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(empty_text, empty_rect)
        else:
            header_text = FONT_LARGE.render('排名    玩家        分数        层数', True, GOLD)
            self.screen.blit(header_text, (board_rect.x + 40, 180))
            
            pygame.draw.line(self.screen, (80, 80, 100), (board_rect.x + 30, 220), (board_rect.x + board_rect.width - 30, 220), 2)
            
            y = 240
            for i, entry in enumerate(leaderboard[:10]):
                if i < 3:
                    medal_colors = [GOLD, (192, 192, 192), (205, 127, 50)]
                    color = medal_colors[i]
                    medal = f'🥇🥈🥉'[i] if i < 3 else f'  {i + 1}.'
                else:
                    color = WHITE
                    medal = f'  {i + 1}.'
                
                entry_text = FONT_LARGE.render(f'{medal}    {entry["name"]:8}  {entry["score"]:6}    第{entry["floor"]}层', True, color)
                self.screen.blit(entry_text, (board_rect.x + 40, y))
                y += 38
        
        footer_text = FONT_NORMAL.render('按任意键返回主菜单', True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(footer_text, footer_rect)
    
    def game_over(self):
        self.state = GameState.GAME_OVER
        score = self.player.level * 100 + self.floor * 500
        self.save_manager.save_score(self.player.name, score, self.floor)
        self.save_manager.delete_save()
    
    def victory(self):
        self.state = GameState.VICTORY
        score = self.player.level * 100 + self.floor * 1000
        self.save_manager.save_score(self.player.name, score, self.floor)
        self.save_manager.delete_save()
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_click(event.pos)
            
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    self.handle_menu_input(event)
                elif self.state == GameState.CLASS_SELECT:
                    self.handle_class_select_input(event)
                elif self.state == GameState.PLAYING:
                    self.handle_game_input(event)
                elif self.state == GameState.PAUSED:
                    self.handle_pause_input(event)
                elif self.state == GameState.INVENTORY:
                    self.handle_inventory_input(event)
                elif self.state == GameState.SHOP:
                    self.handle_shop_input(event)
                elif self.state == GameState.TALENT:
                    self.handle_talent_input(event)
                elif self.state in [GameState.GAME_OVER, GameState.VICTORY, GameState.LEADERBOARD]:
                    self.state = GameState.MENU
    
    def handle_mouse_click(self, pos):
        if self.state == GameState.SHOP:
            self.handle_shop_mouse_click(pos)
    
    def handle_shop_mouse_click(self, pos):
        mx, my = pos
        
        items_rect = pygame.Rect(SCREEN_WIDTH // 2 - 450 + 20, 150, 860, 420)
        items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
        
        if items_rect.collidepoint(mx, my):
            relative_y = my - items_rect.y
            index = relative_y // 30
            if 0 <= index < len(items) and index < 14:
                self.shop_selection = index
        
        mode_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 95, 240, 35)
        if mode_rect.collidepoint(mx, my):
            self.shop_mode = 'sell' if self.shop_mode == 'buy' else 'buy'
            self.shop_selection = 0
        
        if hasattr(self, 'shop_buy_btn') and self.shop_buy_btn.collidepoint(mx, my):
            self.shop_mode = 'buy'
            self.perform_shop_action()
        
        if hasattr(self, 'shop_sell_btn') and self.shop_sell_btn.collidepoint(mx, my):
            self.shop_mode = 'sell'
            self.perform_shop_action()
        
        if hasattr(self, 'shop_exit_btn') and self.shop_exit_btn.collidepoint(mx, my):
            self.state = GameState.PLAYING
    
    def perform_shop_action(self):
        items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
        if not items:
            return
        
        item = items[self.shop_selection]
        if self.shop_mode == 'buy':
            if self.player.gold >= item.value:
                if self.player.add_item(item):
                    self.player.gold -= item.value
                    self.shop.inventory.remove(item)
                    self.add_message(f'购买了 {item.name}！')
                else:
                    self.add_message('背包已满！')
            else:
                self.add_message('金币不足！')
        else:
            sell_price = max(1, item.value // 2)
            self.player.gold += sell_price
            self.player.remove_item(item)
            self.add_message(f'出售了 {item.name}，获得 {sell_price} 金币！')
    
    def handle_menu_input(self, event):
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.menu_selection = (self.menu_selection - 1) % 4
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.menu_selection = (self.menu_selection + 1) % 4
        elif event.key == pygame.K_RETURN:
            if self.menu_selection == 0:
                self.state = GameState.CLASS_SELECT
                self.menu_selection = 0
            elif self.menu_selection == 1:
                if self.save_manager.has_save():
                    pass
                else:
                    self.add_message('没有找到存档！')
            elif self.menu_selection == 2:
                self.state = GameState.LEADERBOARD
            elif self.menu_selection == 3:
                self.running = False
        elif event.key == pygame.K_ESCAPE:
            self.running = False
    
    def handle_class_select_input(self, event):
        if event.key in [pygame.K_LEFT, pygame.K_a]:
            self.menu_selection = (self.menu_selection - 1) % 4
        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
            self.menu_selection = (self.menu_selection + 1) % 4
        elif event.key == pygame.K_RETURN:
            classes = list(CLASSES.keys())
            self.new_game(classes[self.menu_selection])
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
    
    def handle_game_input(self, event):
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.move_player(0, -1)
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.move_player(0, 1)
        elif event.key in [pygame.K_LEFT, pygame.K_a]:
            self.move_player(-1, 0)
        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
            self.move_player(1, 0)
        elif event.key == pygame.K_SPACE:
            for monster in self.monsters:
                if monster.get_distance_to(self.player) <= 1.5:
                    attack_count = self.player.get_total_attack_count()
                    for _ in range(attack_count):
                        if monster.is_alive():
                            self.combat.attack(self.player, monster)
                    if not monster.is_alive():
                        self.monsters.remove(monster)
                    self.end_player_turn()
                    break
        elif event.key in [pygame.K_e]:
            self.handle_special_room_interaction()
        elif event.key in [pygame.K_i]:
            self.state = GameState.INVENTORY
            self.inventory_selection = 0
        elif event.key in [pygame.K_t]:
            self.state = GameState.TALENT
            self.talent_selection = 0
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
            self.menu_selection = 0
    
    def handle_special_room_interaction(self):
        room = self.game_map.get_room_at(self.player.x, self.player.y)
        if not room:
            self.add_message('这里没有可交互的对象！')
            return
        
        room_type = room.room_type
        interaction_happened = False
        
        if room_type == 'altar':
            interaction_happened = True
            if self.player.hp > 10:
                sacrifice = int(self.player.max_hp * 0.2)
                self.player.hp -= sacrifice
                self.player.str += 3
                self.player.defense += 2
                self.add_message(f'献祭了{sacrifice}点生命，获得力量提升！')
            else:
                self.add_message('生命值不足，无法献祭！')
        
        elif room_type == 'blacksmith':
            interaction_happened = True
            if self.player.gold >= 50:
                self.player.gold -= 50
                self.player.base_attack_count += 1
                self.add_message('花费50金币，铁匠强化了你的攻击！')
            else:
                self.add_message('金币不足，无法强化！')
        
        elif room_type == 'library':
            interaction_happened = True
            self.player.int += 5
            self.player.max_mp += 20
            self.player.mp = self.player.max_mp
            self.add_message('阅读古老典籍，智力与魔力永久提升！')
        
        elif room_type == 'event':
            interaction_happened = True
            event_roll = random.random()
            if event_roll < 0.3:
                heal_amount = int(self.player.max_hp * 0.5)
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                self.add_message(f'神秘泉水恢复了{heal_amount}点生命！')
            elif event_roll < 0.6:
                self.player.gold += random.randint(30, 80)
                self.add_message('发现了一个藏宝箱，获得金币！')
            elif event_roll < 0.8:
                self.player.add_status('poison', 5, 3)
                self.add_message('触发了古老诅咒，中毒了！')
            else:
                self.player.str += 2
                self.player.dex += 2
                self.add_message('获得了神秘的祝福！')
        else:
            self.add_message('这个房间没有特殊功能。')
        
        if interaction_happened:
            self.end_player_turn()
    
    def handle_pause_input(self, event):
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.menu_selection = (self.menu_selection - 1) % 3
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.menu_selection = (self.menu_selection + 1) % 3
        elif event.key == pygame.K_RETURN:
            if self.menu_selection == 0:
                self.state = GameState.PLAYING
            elif self.menu_selection == 1:
                self.save_manager.save_game({
                    'player': self.player,
                    'floor': self.floor,
                    'game_map': self.game_map,
                    'monsters': self.monsters,
                    'items': self.items
                })
                self.add_message('游戏已保存！')
                self.state = GameState.PLAYING
            elif self.menu_selection == 2:
                self.state = GameState.MENU
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def handle_inventory_input(self, event):
        if not self.player.inventory:
            self.inventory_selection = 0
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.PLAYING
            return
        
        self.inventory_selection = max(0, min(self.inventory_selection, len(self.player.inventory) - 1))
        
        if event.key in [pygame.K_UP, pygame.K_w]:
            if self.inventory_selection > 0:
                self.inventory_selection -= 1
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            if self.inventory_selection < len(self.player.inventory) - 1:
                self.inventory_selection += 1
        elif event.key in [pygame.K_e]:
            if 0 <= self.inventory_selection < len(self.player.inventory):
                item = self.player.inventory[self.inventory_selection]
                if hasattr(item, 'slot'):
                    if self.player.equip_item(item):
                        self.add_message(f'装备了 {item.name}！')
                    else:
                        self.add_message(f'无法装备 {item.name}！')
                else:
                    self.add_message('这个物品无法装备！')
        elif event.key in [pygame.K_u]:
            if 0 <= self.inventory_selection < len(self.player.inventory):
                item = self.player.inventory[self.inventory_selection]
                if hasattr(item, 'use'):
                    msg = item.use(self.player)
                    self.add_message(msg)
                    self.player.remove_item(item)
                    self.inventory_selection = min(self.inventory_selection, len(self.player.inventory) - 1)
                else:
                    self.add_message('这个物品无法使用！')
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def handle_shop_input(self, event):
        items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
        
        if not items:
            self.shop_selection = 0
            if event.key == pygame.K_TAB:
                self.shop_mode = 'sell' if self.shop_mode == 'buy' else 'buy'
                self.shop_selection = 0
            elif event.key == pygame.K_ESCAPE:
                self.state = GameState.PLAYING
            return
        
        self.shop_selection = max(0, min(self.shop_selection, len(items) - 1))
        
        if event.key in [pygame.K_UP, pygame.K_w]:
            if self.shop_selection > 0:
                self.shop_selection -= 1
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            if self.shop_selection < len(items) - 1:
                self.shop_selection += 1
        elif event.key == pygame.K_TAB:
            self.shop_mode = 'sell' if self.shop_mode == 'buy' else 'buy'
            self.shop_selection = 0
        elif event.key == pygame.K_RETURN:
            if items and 0 <= self.shop_selection < len(items):
                item = items[self.shop_selection]
                if self.shop_mode == 'buy':
                    if self.player.gold >= item.value:
                        if self.player.add_item(item):
                            self.player.gold -= item.value
                            self.shop.inventory.remove(item)
                            self.shop_selection = min(self.shop_selection, len(self.shop.inventory) - 1)
                            self.add_message(f'购买了 {item.name}！')
                        else:
                            self.add_message('背包已满！')
                    else:
                        self.add_message('金币不足！')
                else:
                    sell_price = max(1, item.value // 2)
                    self.player.gold += sell_price
                    self.player.remove_item(item)
                    self.shop_selection = min(self.shop_selection, len(self.player.inventory) - 1)
                    self.add_message(f'出售了 {item.name}，获得 {sell_price} 金币！')
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def handle_talent_input(self, event):
        talent_categories = ['strength', 'dexterity', 'intelligence', 'defense', 'hp', 'mp']
        total_talents = len(talent_categories) * 3
        
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.talent_selection = (self.talent_selection - 1) % total_talents
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.talent_selection = (self.talent_selection + 1) % total_talents
        elif event.key in [pygame.K_LEFT, pygame.K_a]:
            if self.talent_selection - 3 >= 0:
                self.talent_selection -= 3
        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
            if self.talent_selection + 3 < total_talents:
                self.talent_selection += 3
        elif event.key == pygame.K_RETURN:
            cat_idx = self.talent_selection // 3
            tier = self.talent_selection % 3
            talent_id = f'{talent_categories[cat_idx]}_{tier + 1}'
            success, message = self.player.unlock_talent(talent_id)
            self.add_message(f'{message}')
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def run(self):
        while self.running:
            self.handle_input()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
