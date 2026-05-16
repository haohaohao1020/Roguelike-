import pygame
import random
from .config import *
from .map import GameMap
from .entity import Character
from .monster import create_monster, create_elite, create_boss
from .items import Chest, create_random_item, Potion
from .combat import CombatSystem
from .save_manager import SaveManager, Shop
from .asset_loader import asset_loader

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
            if room.room_type == 'normal':
                num_monsters = random.randint(2, 4)
                for _ in range(num_monsters):
                    x, y = room.get_random_position()
                    if not any(e.x == x and e.y == y for e in self.monsters):
                        monster = create_monster(x, y, self.floor)
                        self.monsters.append(monster)
            elif room.room_type == 'treasure':
                x, y = room.center()
                self.items.append(Chest(x, y))
            elif room.room_type == 'trap':
                pass
        
        for room in self.game_map.rooms:
            if room.room_type != 'boss' and random.random() < 0.3:
                x, y = room.get_random_position()
                if not any(e.x == x and e.y == y for e in self.monsters + self.items):
                    item = create_random_item(x, y)
                    if item:
                        self.items.append(item)
        
        if self.game_map.rooms:
            boss_room = self.game_map.rooms[-1]
            if self.floor >= MAX_FLOOR:
                x, y = boss_room.center()
                boss = create_boss(x, y, self.floor)
                self.monsters.append(boss)
            else:
                if random.random() < 0.3:
                    x, y = boss_room.get_random_position()
                    elite = create_elite(x, y, self.floor)
                    self.monsters.append(elite)
        
        self.update_camera()
    
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
                elif item.item_type == 'gold':
                    self.player.gold += item.amount
                    self.items.remove(item)
                    self.add_message(f'拾取了 {item.amount} 金币！')
                else:
                    if self.player.add_item(item):
                        self.items.remove(item)
                        self.add_message(f'拾取了 {item.name}！')
        
        if self.game_map.is_walkable(new_x, new_y):
            self.player.move(dx, dy)
            self.update_camera()
        
        room = self.game_map.get_room_at(self.player.x, self.player.y)
        if room and room.room_type == 'shop':
            self.state = GameState.SHOP
            self.shop.refresh_items()
        elif room and room.room_type == 'rest':
            self.player.heal(30)
            self.player.restore_mp(20)
            self.add_message('在休息点恢复了生命和魔力！')
        
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
        self.camera_x = self.player.x * TILE_SIZE - SCREEN_WIDTH // 2
        self.camera_y = self.player.y * TILE_SIZE - SCREEN_HEIGHT // 2
        self.camera_x = max(0, min(self.camera_x, MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT))
    
    def render(self):
        self.screen.fill(BLACK)
        
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
        start_x = max(0, self.camera_x // TILE_SIZE)
        start_y = max(0, self.camera_y // TILE_SIZE)
        end_x = min(MAP_WIDTH, (self.camera_x + SCREEN_WIDTH) // TILE_SIZE + 1)
        end_y = min(MAP_HEIGHT, (self.camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                if self.game_map.explored[x][y]:
                    tile = self.game_map.tiles[x][y]
                    screen_x = x * TILE_SIZE - self.camera_x
                    screen_y = y * TILE_SIZE - self.camera_y
                    
                    if tile == 0:
                        color = (100, 80, 60) if self.game_map.visible[x][y] else (50, 40, 30)
                    else:
                        color = (50, 50, 50) if self.game_map.visible[x][y] else (30, 30, 30)
                    
                    pygame.draw.rect(self.screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        
        if self.game_map.stairs_pos:
            sx, sy = self.game_map.stairs_pos
            if self.game_map.explored[sx][sy]:
                screen_x = sx * TILE_SIZE - self.camera_x
                screen_y = sy * TILE_SIZE - self.camera_y
                pygame.draw.rect(self.screen, (200, 200, 0), (screen_x + 8, screen_y + 8, 16, 16))
        
        for item in self.items:
            if self.game_map.visible[item.x][item.y]:
                screen_x = item.x * TILE_SIZE - self.camera_x
                screen_y = item.y * TILE_SIZE - self.camera_y
                color = GOLD if hasattr(item, 'is_open') else item.color
                pygame.draw.circle(self.screen, color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), 8)
        
        for monster in self.monsters:
            if self.game_map.visible[monster.x][monster.y]:
                screen_x = monster.x * TILE_SIZE - self.camera_x
                screen_y = monster.y * TILE_SIZE - self.camera_y
                
                if monster.is_hurt:
                    pygame.draw.circle(self.screen, WHITE, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), 14)
                
                pygame.draw.circle(self.screen, monster.color, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), 12)
                
                hp_ratio = monster.hp / monster.max_hp
                hp_width = int(TILE_SIZE * hp_ratio)
                pygame.draw.rect(self.screen, RED, (screen_x, screen_y - 6, TILE_SIZE, 4))
                pygame.draw.rect(self.screen, GREEN, (screen_x, screen_y - 6, hp_width, 4))
        
        player_screen_x = self.player.x * TILE_SIZE - self.camera_x
        player_screen_y = self.player.y * TILE_SIZE - self.camera_y
        
        if self.player.is_hurt:
            pygame.draw.circle(self.screen, WHITE, (player_screen_x + TILE_SIZE // 2, player_screen_y + TILE_SIZE // 2), 16)
        
        pygame.draw.circle(self.screen, CYAN, (player_screen_x + TILE_SIZE // 2, player_screen_y + TILE_SIZE // 2), 14)
        
        for dn in self.combat.damage_numbers:
            screen_x = dn['x'] * TILE_SIZE - self.camera_x + TILE_SIZE // 2
            screen_y = dn['y'] * TILE_SIZE - self.camera_y + dn['offset_y']
            text = FONT_NORMAL.render(dn['text'], True, dn['color'])
            self.screen.blit(text, (screen_x - text.get_width() // 2, screen_y))
        
        self.render_ui()
    
    def render_ui(self):
        ui_bg = (30, 30, 30, 200)
        
        panel_rect = pygame.Rect(SCREEN_WIDTH - 250, 10, 240, 180)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2)
        
        y = panel_rect.y + 10
        
        class_name = CLASSES[self.player.class_type]['name']
        text = FONT_NORMAL.render(f'{class_name} Lv.{self.player.level}', True, WHITE)
        self.screen.blit(text, (panel_rect.x + 10, y))
        y += 25
        
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, (100, 0, 0), (panel_rect.x + 10, y, 220, 20))
        pygame.draw.rect(self.screen, RED, (panel_rect.x + 10, y, int(220 * hp_ratio), 20))
        text = FONT_SMALL.render(f'HP: {self.player.hp}/{self.player.max_hp}', True, WHITE)
        self.screen.blit(text, (panel_rect.x + 15, y + 2))
        y += 30
        
        mp_ratio = self.player.mp / self.player.max_mp
        pygame.draw.rect(self.screen, (0, 0, 100), (panel_rect.x + 10, y, 220, 20))
        pygame.draw.rect(self.screen, BLUE, (panel_rect.x + 10, y, int(220 * mp_ratio), 20))
        text = FONT_SMALL.render(f'MP: {self.player.mp}/{self.player.max_mp}', True, WHITE)
        self.screen.blit(text, (panel_rect.x + 15, y + 2))
        y += 30
        
        exp_ratio = self.player.exp / self.player.exp_to_next
        pygame.draw.rect(self.screen, (50, 50, 0), (panel_rect.x + 10, y, 220, 15))
        pygame.draw.rect(self.screen, YELLOW, (panel_rect.x + 10, y, int(220 * exp_ratio), 15))
        y += 25
        
        text = FONT_SMALL.render(f'金币: {self.player.gold}  层数: {self.floor}', True, GOLD)
        self.screen.blit(text, (panel_rect.x + 10, y))
        
        log_rect = pygame.Rect(10, SCREEN_HEIGHT - 120, SCREEN_WIDTH - 270, 110)
        pygame.draw.rect(self.screen, (40, 40, 40), log_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), log_rect, 2)
        
        y = log_rect.y + 10
        for msg in self.message_log[-5:]:
            text = FONT_SMALL.render(msg, True, WHITE)
            self.screen.blit(text, (log_rect.x + 10, y))
            y += 20
        
        help_text = '方向键移动 | 空格攻击 | I背包 | ESC暂停'
        text = FONT_SMALL.render(help_text, True, GRAY)
        self.screen.blit(text, (10, 10))
    
    def render_menu(self):
        title = FONT_TITLE.render('地牢探险', True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        
        menu_items = ['开始游戏', '继续游戏', '排行榜', '退出']
        for i, item in enumerate(menu_items):
            color = YELLOW if i == self.menu_selection else WHITE
            text = FONT_LARGE.render(item, True, color)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 300 + i * 60))
        
        pygame.display.flip()
    
    def render_class_select(self):
        title = FONT_LARGE.render('选择你的职业', True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        
        class_names = list(CLASSES.keys())
        for i, class_key in enumerate(class_names):
            class_data = CLASSES[class_key]
            color = YELLOW if i == self.menu_selection else WHITE
            
            x = 200 + i * 300
            pygame.draw.rect(self.screen, (50, 50, 50), (x - 50, 180, 250, 350))
            pygame.draw.rect(self.screen, color, (x - 50, 180, 250, 350), 3)
            
            text = FONT_LARGE.render(class_data['name'], True, color)
            self.screen.blit(text, (x, 200))
            
            y = 270
            stats = [
                f'生命: {class_data["hp"]}',
                f'魔力: {class_data["mp"]}',
                f'力量: {class_data["str"]}',
                f'敏捷: {class_data["dex"]}',
                f'智力: {class_data["int"]}',
                f'防御: {class_data["def"]}'
            ]
            for stat in stats:
                text = FONT_NORMAL.render(stat, True, WHITE)
                self.screen.blit(text, (x, y))
                y += 30
            
            text = FONT_SMALL.render(class_data['description'], True, GRAY)
            self.screen.blit(text, (x, y + 20))
        
        text = FONT_NORMAL.render('按回车确认', True, GRAY)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 580))
    
    def render_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        menu_items = ['继续游戏', '保存游戏', '返回主菜单']
        for i, item in enumerate(menu_items):
            color = YELLOW if i == self.menu_selection else WHITE
            text = FONT_LARGE.render(item, True, color)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 250 + i * 60))
    
    def render_inventory(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = FONT_LARGE.render('背包', True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 100, 600, 500)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2)
        
        y = 120
        for i, item in enumerate(self.player.inventory[:15]):
            color = YELLOW if i == self.inventory_selection else WHITE
            text = FONT_NORMAL.render(f'{i + 1}. {item.name}', True, color)
            self.screen.blit(text, (panel_rect.x + 20, y))
            y += 30
        
        if self.player.inventory:
            selected = self.player.inventory[self.inventory_selection]
            text = FONT_SMALL.render(f'价值: {selected.value} 金币', True, GRAY)
            self.screen.blit(text, (panel_rect.x + 300, 120))
            
            if hasattr(selected, 'stats'):
                y = 160
                for stat, value in selected.stats.items():
                    text = FONT_SMALL.render(f'{stat}: +{value}', True, GREEN)
                    self.screen.blit(text, (panel_rect.x + 300, y))
                    y += 25
        
        equip_text = FONT_SMALL.render('E-装备  U-使用  D-卸下', True, GRAY)
        self.screen.blit(equip_text, (panel_rect.x + 20, panel_rect.y + panel_rect.height - 40))
    
    def render_shop(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = FONT_LARGE.render('商店', True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 400, 100, 800, 500)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2)
        
        gold_text = FONT_NORMAL.render(f'金币: {self.player.gold}', True, GOLD)
        self.screen.blit(gold_text, (panel_rect.x + 20, panel_rect.y + 20))
        
        mode_text = '购买' if self.shop_mode == 'buy' else '出售'
        text = FONT_NORMAL.render(f'模式: {mode_text}', True, YELLOW)
        self.screen.blit(text, (panel_rect.x + 600, panel_rect.y + 20))
        
        items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
        
        y = 160
        for i, item in enumerate(items[:12]):
            color = YELLOW if i == self.shop_selection else WHITE
            price = item.value if self.shop_mode == 'buy' else item.value // 2
            text = FONT_NORMAL.render(f'{i + 1}. {item.name} - {price}G', True, color)
            self.screen.blit(text, (panel_rect.x + 20, y))
            y += 30
        
        help_text = 'TAB-切换模式  回车-交易  ESC-离开商店'
        text = FONT_SMALL.render(help_text, True, GRAY)
        self.screen.blit(text, (panel_rect.x + 20, panel_rect.y + panel_rect.height - 40))
    
    def render_game_over(self):
        self.screen.fill(BLACK)
        title = FONT_TITLE.render('游戏结束', True, RED)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        
        text = FONT_LARGE.render(f'到达层数: {self.floor}', True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 300))
        
        text = FONT_LARGE.render(f'最终等级: {self.player.level}', True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 360))
        
        text = FONT_NORMAL.render('按任意键返回主菜单', True, GRAY)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 500))
    
    def render_victory(self):
        self.screen.fill((20, 40, 20))
        title = FONT_TITLE.render('胜利！', True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        
        text = FONT_LARGE.render('恭喜你击败了远古巨龙！', True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 300))
        
        text = FONT_LARGE.render(f'最终等级: {self.player.level}', True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 360))
        
        text = FONT_NORMAL.render('按任意键返回主菜单', True, GRAY)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 500))
    
    def render_leaderboard(self):
        self.screen.fill(BLACK)
        title = FONT_TITLE.render('排行榜', True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
        
        leaderboard = self.save_manager.get_leaderboard()
        
        for i, entry in enumerate(leaderboard):
            text = FONT_LARGE.render(f'{i + 1}. {entry["name"]} - {entry["score"]}分 - 第{entry["floor"]}层', True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 180 + i * 45))
        
        text = FONT_NORMAL.render('按任意键返回', True, GRAY)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 600))
    
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
    
    def handle_menu_input(self, event):
        if event.key == pygame.K_UP:
            self.menu_selection = (self.menu_selection - 1) % 4
        elif event.key == pygame.K_DOWN:
            self.menu_selection = (self.menu_selection + 1) % 4
        elif event.key == pygame.K_RETURN:
            if self.menu_selection == 0:
                self.state = GameState.CLASS_SELECT
                self.menu_selection = 0
            elif self.menu_selection == 1:
                pass
            elif self.menu_selection == 2:
                self.state = GameState.LEADERBOARD
            elif self.menu_selection == 3:
                self.running = False
    
    def handle_class_select_input(self, event):
        if event.key == pygame.K_LEFT:
            self.menu_selection = (self.menu_selection - 1) % 3
        elif event.key == pygame.K_RIGHT:
            self.menu_selection = (self.menu_selection + 1) % 3
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
                    self.combat.attack(self.player, monster)
                    if not monster.is_alive():
                        self.monsters.remove(monster)
                    self.end_player_turn()
                    break
        elif event.key == pygame.K_i:
            self.state = GameState.INVENTORY
            self.inventory_selection = 0
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
            self.menu_selection = 0
    
    def handle_pause_input(self, event):
        if event.key == pygame.K_UP:
            self.menu_selection = (self.menu_selection - 1) % 3
        elif event.key == pygame.K_DOWN:
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
        if event.key == pygame.K_UP:
            if self.inventory_selection > 0:
                self.inventory_selection -= 1
        elif event.key == pygame.K_DOWN:
            if self.inventory_selection < len(self.player.inventory) - 1:
                self.inventory_selection += 1
        elif event.key == pygame.K_e:
            if self.player.inventory:
                item = self.player.inventory[self.inventory_selection]
                if hasattr(item, 'slot'):
                    self.player.equip_item(item)
                    self.add_message(f'装备了 {item.name}！')
        elif event.key == pygame.K_u:
            if self.player.inventory:
                item = self.player.inventory[self.inventory_selection]
                if hasattr(item, 'use'):
                    msg = item.use(self.player)
                    self.add_message(msg)
                    self.player.remove_item(item)
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def handle_shop_input(self, event):
        items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
        if event.key == pygame.K_UP:
            if self.shop_selection > 0:
                self.shop_selection -= 1
        elif event.key == pygame.K_DOWN:
            if self.shop_selection < len(items) - 1:
                self.shop_selection += 1
        elif event.key == pygame.K_TAB:
            self.shop_mode = 'sell' if self.shop_mode == 'buy' else 'buy'
            self.shop_selection = 0
        elif event.key == pygame.K_RETURN:
            if items:
                item = items[self.shop_selection]
                if self.shop_mode == 'buy':
                    success, msg = self.shop.buy(self.player, item)
                    self.add_message(msg)
                else:
                    success, msg = self.shop.sell(self.player, item)
                    self.add_message(msg)
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def run(self):
        while self.running:
            self.handle_input()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
