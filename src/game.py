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
        
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        for monster in self.monsters:
            if monster.x == new_x and monster.y == new_y:
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
        
        self.last_room_type = current_room_type
        
        if self.game_map.stairs_pos:
            sx, sy = self.game_map.stairs_pos
            if self.player.x == sx and self.player.y == sy:
                self.go_downstairs()
        
        self.end_player_turn()
    
    def end_player_turn(self):
        self.player_turn = False
        self.turn += 1
        
        for monster in self.monsters:
            if monster.is_alive():
                monster.update_ai(self.game_map, self.player, self.monsters + [self.player])
                
                distance = monster.get_distance_to(self.player)
                if distance <= 1.5:
                    self.combat.attack(monster, self.player)
        
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
        elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.INVENTORY, GameState.SHOP]:
            self.render_game()
            if self.state == GameState.PAUSED:
                self.render_pause_menu()
            elif self.state == GameState.INVENTORY:
                self.render_inventory()
            elif self.state == GameState.SHOP:
                self.render_shop()
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
                        self.dungeon_renderer.draw_floor(self.screen, x, y, self.camera_x, self.camera_y, room_type, self.game_map.visible[x][y])
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
        
        self.render_ui()
    
    def render_ui(self):
        panel_rect = pygame.Rect(SCREEN_WIDTH - 260, 10, 250, 200)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, (80, 80, 100), panel_rect, 2)
        
        y = panel_rect.y + 15
        
        class_name = CLASSES[self.player.class_type]['name']
        title_text = FONT_LARGE.render(f'{class_name}', True, GOLD)
        level_text = FONT_NORMAL.render(f'Lv.{self.player.level}', True, WHITE)
        self.screen.blit(title_text, (panel_rect.x + 15, y))
        self.screen.blit(level_text, (panel_rect.x + 120, y + 5))
        y += 40
        
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, (80, 0, 0), (panel_rect.x + 15, y, 220, 18))
        pygame.draw.rect(self.screen, (220, 50, 50), (panel_rect.x + 15, y, int(220 * hp_ratio), 18))
        pygame.draw.rect(self.screen, (255, 100, 100), (panel_rect.x + 15, y, int(220 * hp_ratio), 6))
        hp_text = FONT_SMALL.render(f'生命值: {self.player.hp}/{self.player.max_hp}', True, WHITE)
        self.screen.blit(hp_text, (panel_rect.x + 20, y + 1))
        y += 28
        
        mp_ratio = self.player.mp / self.player.max_mp
        pygame.draw.rect(self.screen, (0, 0, 80), (panel_rect.x + 15, y, 220, 18))
        pygame.draw.rect(self.screen, (50, 100, 220), (panel_rect.x + 15, y, int(220 * mp_ratio), 18))
        pygame.draw.rect(self.screen, (100, 150, 255), (panel_rect.x + 15, y, int(220 * mp_ratio), 6))
        mp_text = FONT_SMALL.render(f'魔力值: {self.player.mp}/{self.player.max_mp}', True, WHITE)
        self.screen.blit(mp_text, (panel_rect.x + 20, y + 1))
        y += 28
        
        exp_ratio = self.player.exp / self.player.exp_to_next
        pygame.draw.rect(self.screen, (40, 40, 0), (panel_rect.x + 15, y, 220, 12))
        pygame.draw.rect(self.screen, (200, 200, 0), (panel_rect.x + 15, y, int(220 * exp_ratio), 12))
        y += 20
        
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        floor_text = FONT_NORMAL.render(f'第 {self.floor} 层', True, WHITE)
        self.screen.blit(gold_text, (panel_rect.x + 15, y))
        self.screen.blit(floor_text, (panel_rect.x + 130, y))
        
        stats_text = [
            f'力量: {self.player.get_total_str()}',
            f'敏捷: {self.player.get_total_dex()}',
            f'智力: {self.player.get_total_int()}',
            f'防御: {self.player.get_total_defense()}'
        ]
        y += 30
        for text in stats_text:
            stat_text = FONT_SMALL.render(text, True, (200, 200, 200))
            self.screen.blit(stat_text, (panel_rect.x + 15, y))
            y += 18
        
        log_rect = pygame.Rect(10, SCREEN_HEIGHT - 130, SCREEN_WIDTH - 280, 120)
        pygame.draw.rect(self.screen, (25, 25, 35), log_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), log_rect, 2)
        
        log_title = FONT_NORMAL.render('战斗日志', True, GRAY)
        self.screen.blit(log_title, (log_rect.x + 10, log_rect.y + 5))
        
        y = log_rect.y + 30
        for msg in self.message_log[-4:]:
            msg_text = FONT_SMALL.render(msg, True, (220, 220, 220))
            self.screen.blit(msg_text, (log_rect.x + 15, y))
            y += 22
        
        help_bg = pygame.Rect(10, 10, 300, 50)
        pygame.draw.rect(self.screen, (25, 25, 35), help_bg)
        pygame.draw.rect(self.screen, (60, 60, 80), help_bg, 2)
        
        help_lines = [
            '方向键/WASD:移动 | 空格:攻击 | I:背包 | ESC:暂停'
        ]
        y = help_bg.y + 8
        for line in help_lines:
            help_text = FONT_SMALL.render(line, True, GRAY)
            self.screen.blit(help_text, (help_bg.x + 10, y))
            y += 16
        
        minimap_size = 150
        minimap_rect = pygame.Rect(SCREEN_WIDTH - minimap_size - 10, 220, minimap_size, minimap_size)
        pygame.draw.rect(self.screen, (15, 15, 25), minimap_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), minimap_rect, 2)
        
        scale = minimap_size / MAP_WIDTH
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                if self.game_map.explored[x][y]:
                    if self.game_map.tiles[x][y] == 0:
                        color = (80, 60, 40) if not self.game_map.visible[x][y] else (120, 100, 70)
                    else:
                        color = (40, 40, 50)
                    px = int(minimap_rect.x + x * scale)
                    py = int(minimap_rect.y + y * scale)
                    pygame.draw.rect(self.screen, color, (px, py, max(1, int(scale)), max(1, int(scale))))
        
        for monster in self.monsters:
            if self.game_map.visible[monster.x][monster.y]:
                px = int(minimap_rect.x + monster.x * scale)
                py = int(minimap_rect.y + monster.y * scale)
                pygame.draw.circle(self.screen, RED, (px, py), 2)
        
        if self.game_map.stairs_pos:
            sx, sy = self.game_map.stairs_pos
            if self.game_map.explored[sx][sy]:
                px = int(minimap_rect.x + sx * scale)
                py = int(minimap_rect.y + sy * scale)
                pygame.draw.circle(self.screen, YELLOW, (px, py), 3)
        
        px = int(minimap_rect.x + self.player.x * scale)
        py = int(minimap_rect.y + self.player.y * scale)
        pygame.draw.circle(self.screen, CYAN, (px, py), 4)
        pygame.draw.circle(self.screen, WHITE, (px, py), 2)
    
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
            ('rogue', '盗贼', '敏捷灵活，背刺暴击', GREEN, ['HP: 100', 'MP: 50', '敏捷: 20', '闪避率高'])
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
        
        if self.player.inventory:
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
            self.menu_selection = (self.menu_selection - 1) % 3
        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
            self.menu_selection = (self.menu_selection + 1) % 3
        elif event.key == pygame.K_RETURN:
            classes = list(CLASSES.keys())
            self.new_game(classes[self.menu_selection])
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
    
    def handle_game_input(self, event):
        if event.key in [pygame.K_UP, pygame.K_w, pygame.K_W]:
            self.move_player(0, -1)
        elif event.key in [pygame.K_DOWN, pygame.K_s, pygame.K_S]:
            self.move_player(0, 1)
        elif event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_A]:
            self.move_player(-1, 0)
        elif event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_D]:
            self.move_player(1, 0)
        elif event.key == pygame.K_SPACE:
            for monster in self.monsters:
                if monster.get_distance_to(self.player) <= 1.5:
                    self.combat.attack(self.player, monster)
                    if not monster.is_alive():
                        self.monsters.remove(monster)
                    self.end_player_turn()
                    break
        elif event.key in [pygame.K_i, pygame.K_I]:
            self.state = GameState.INVENTORY
            self.inventory_selection = 0
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
            self.menu_selection = 0
    
    def handle_pause_input(self, event):
        if event.key in [pygame.K_UP, pygame.K_w, pygame.K_W]:
            self.menu_selection = (self.menu_selection - 1) % 3
        elif event.key in [pygame.K_DOWN, pygame.K_s, pygame.K_S]:
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
        if event.key in [pygame.K_UP, pygame.K_w, pygame.K_W]:
            if self.inventory_selection > 0:
                self.inventory_selection -= 1
        elif event.key in [pygame.K_DOWN, pygame.K_s, pygame.K_S]:
            if self.inventory_selection < len(self.player.inventory) - 1:
                self.inventory_selection += 1
        elif event.key in [pygame.K_e, pygame.K_E]:
            if self.player.inventory:
                item = self.player.inventory[self.inventory_selection]
                if hasattr(item, 'slot'):
                    if self.player.equip_item(item):
                        self.add_message(f'装备了 {item.name}！')
                    else:
                        self.add_message(f'无法装备 {item.name}！')
        elif event.key in [pygame.K_u, pygame.K_U]:
            if self.player.inventory:
                item = self.player.inventory[self.inventory_selection]
                if hasattr(item, 'use'):
                    msg = item.use(self.player)
                    self.add_message(msg)
                    self.player.remove_item(item)
                else:
                    self.add_message('这个物品无法使用！')
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def handle_shop_input(self, event):
        items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
        if event.key in [pygame.K_UP, pygame.K_w, pygame.K_W]:
            if self.shop_selection > 0:
                self.shop_selection -= 1
        elif event.key in [pygame.K_DOWN, pygame.K_s, pygame.K_S]:
            if self.shop_selection < len(items) - 1:
                self.shop_selection += 1
        elif event.key == pygame.K_TAB:
            self.shop_mode = 'sell' if self.shop_mode == 'buy' else 'buy'
            self.shop_selection = 0
        elif event.key == pygame.K_RETURN:
            if items:
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
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def run(self):
        while self.running:
            self.handle_input()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
