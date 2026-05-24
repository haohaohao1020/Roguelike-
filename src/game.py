import pygame
import random
from .config import *
from .map import GameMap
from .entity import Character
from .monster import create_monster, create_elite, create_boss, FinalBoss
from .items import Chest, create_random_item, Potion, Gold
from .combat import CombatSystem
from .save_manager import SaveManager, Shop
from .asset_loader import asset_loader
from .renderer import DungeonRenderer, MonsterRenderer, PlayerRenderer
from .items import SynthesisSystem
from .npc import create_random_npc, QuestManager, DeliveryLetter
from .behavior_tracker import BehaviorTracker, EndingSystem

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
    MODE_SELECT = 'mode_select'
    SYNTHESIS = 'synthesis'
    QUEST_PANEL = 'quest_panel'
    NPC_INTERACT = 'npc_interact'
    ENDING = 'ending'

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
        self.synthesis = SynthesisSystem()
        
        self.dungeon_renderer = DungeonRenderer()
        self.monster_renderer = MonsterRenderer()
        self.player_renderer = PlayerRenderer()
        
        self.map_reveal_duration = 0
        self.synthesis_selection = 0
        self.synthesis_quality = 'common'
        self.shop_tab = 0
        self.gamble_selection = 0
        
        self.state = GameState.MENU
        self.game_mode = 'single'
        self.floor = 1
        self.player = None
        self.player2 = None
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
        self.used_rooms = set()
        
        self.quest_manager = QuestManager()
        self.behavior_tracker = BehaviorTracker()
        self.ending_system = EndingSystem()
        self.npcs = []
        self.current_npc = None
        self.quest_selection = 0
        self.npc_selection = 0
        self.current_ending = None
        self.ending_data = None
        self.final_boss_damage_taken = 0
        self.is_fighting_final_boss = False
    
    def add_message(self, text):
        self.message_log.append(text)
        if len(self.message_log) > 5:
            self.message_log.pop(0)
    
    def load_saved_game(self):
        try:
            save_data = self.save_manager.load_game()
            if save_data:
                self.player = save_data.get('player')
                self.floor = save_data.get('floor', 1)
                self.game_map = save_data.get('game_map')
                self.monsters = save_data.get('monsters', [])
                self.items = save_data.get('items', [])
                self.game_mode = 'single'
                self.player2 = None
                self.state = GameState.PLAYING
                self.menu_selection = 0
                self.add_message(f'成功加载存档！当前第{self.floor}层')
            else:
                self.add_message('存档数据损坏！')
        except Exception as e:
            print(f'加载存档失败: {e}')
            self.add_message('加载存档失败！')
    
    def generate_floor(self):
        self.game_map = GameMap(MAP_WIDTH, MAP_HEIGHT, self.floor)
        self.game_map.generate_map()
        
        self.monsters = []
        self.items = []
        self.npcs = []
        self.used_rooms = set()
        
        self.dungeon_renderer.set_floor_theme(self.floor)
        
        monster_multiplier = 1.5 if self.game_mode == 'coop' else 1.0
        floor_difficulty_multiplier = 1 + (self.floor - 1) * 0.15
        
        if self.game_map.rooms:
            start_room = self.game_map.rooms[0]
            cx, cy = start_room.center()
            self.player.x, self.player.y = cx, cy
            if self.game_mode == 'coop' and self.player2:
                self.player2.x, self.player2.y = cx + 1, cy
        
        for room in self.game_map.rooms:
            room_color = self.get_room_color(room.room_type)
            self.room_colors[(room.x1, room.y1, room.x2, room.y2)] = room_color
            
            if room.room_type == 'normal':
                base_monsters = random.randint(2, 4 + self.floor // 3)
                num_monsters = int(base_monsters * monster_multiplier * floor_difficulty_multiplier)
                for _ in range(num_monsters):
                    x, y = room.get_random_position()
                    if not any(m.x == x and m.y == y for m in self.monsters):
                        monster = create_monster(x, y, self.floor)
                        self.monsters.append(monster)
                
                elite_chance = 0.1 + self.floor * 0.05
                if random.random() < elite_chance:
                    ex, ey = room.get_random_position()
                    if not any(m.x == ex and m.y == ey for m in self.monsters):
                        elite = create_elite(ex, ey, self.floor)
                        self.monsters.append(elite)
                
                if random.random() < 0.2:
                    nx, ny = room.get_random_position()
                    if not any(e.x == nx and e.y == ny for e in self.monsters + self.items + self.npcs):
                        npc = create_random_npc(nx, ny, self.floor)
                        self.npcs.append(npc)
            
            elif room.room_type == 'treasure':
                x, y = room.center()
                self.items.append(Chest(x, y, self.floor))
            elif room.room_type == 'boss':
                x, y = room.center()
                if self.floor == 10:
                    boss = FinalBoss(x, y)
                    self.is_fighting_final_boss = True
                    self.final_boss_damage_taken = 0
                else:
                    boss = create_boss(x, y, self.floor)
                self.monsters.append(boss)
                if random.random() < 0.4:
                    ex, ey = room.get_random_position()
                    if (ex, ey) != (x, y):
                        elite = create_elite(ex, ey, self.floor)
                        self.monsters.append(elite)
                        if self.game_mode == 'coop' and random.random() < 0.5:
                            elite2 = create_elite(ex + 2, ey, self.floor)
                            self.monsters.append(elite2)
        
        for room in self.game_map.rooms:
            if room.room_type != 'boss' and random.random() < 0.3:
                x, y = room.get_random_position()
                if not any(e.x == x and e.y == y for e in self.monsters + self.items):
                    item_type = random.choice(['gold', 'potion', 'equipment'])
                    if item_type == 'gold':
                        amount = int(random.randint(10, 50) * self.floor * (1.2 if self.game_mode == 'coop' else 1))
                        self.items.append(Gold(x, y, amount))
                    elif item_type == 'potion':
                        potion_type = random.choice(['health', 'mana'])
                        self.items.append(Potion(x, y, potion_type))
                        if self.game_mode == 'coop':
                            self.items.append(Potion(x + 1, y, potion_type))
                    else:
                        item = create_random_item(x, y, self.floor)
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
    
    def new_game(self, class_type, class_type2=None):
        self.player = Character(MAP_WIDTH // 2, MAP_HEIGHT // 2, '勇者1', class_type)
        self.player.is_player1 = True
        self.player.teleport_anchors = []
        self.player2 = None
        if self.game_mode == 'coop' and class_type2:
            self.player2 = Character(MAP_WIDTH // 2 + 1, MAP_HEIGHT // 2, '勇者2', class_type2)
            self.player2.is_player2 = True
            self.player2.teleport_anchors = []
        self.shop.refresh_items(self.game_mode)
        self.floor = 1
        self.turn = 0
        self.message_log = []
        self.map_reveal_duration = 0
        
        self.quest_manager = QuestManager()
        self.behavior_tracker = BehaviorTracker()
        self.npcs = []
        self.current_npc = None
        self.quest_selection = 0
        self.npc_selection = 0
        self.current_ending = None
        self.ending_data = None
        self.final_boss_damage_taken = 0
        self.is_fighting_final_boss = False
        
        self.generate_floor()
        self.state = GameState.PLAYING
        if self.game_mode == 'coop':
            self.add_message('双人模式开始！并肩作战吧！')
        else:
            self.add_message('欢迎来到地牢！')
        
        theme_name = FLOOR_THEMES[self.floor]['name']
        self.add_message(f'进入了{theme_name}！')
    
    def get_nearest_monster(self, player):
        nearest = None
        min_dist = 999
        for monster in self.monsters:
            if monster.is_alive():
                dist = monster.get_distance_to(player)
                if dist < min_dist:
                    min_dist = dist
                    nearest = monster
        return nearest
    
    def use_player_skill(self, player, skill_type, allies=None):
        target = self.get_nearest_monster(player)
        all_enemies = [m for m in self.monsters if m.is_alive()]
        
        if skill_type == 'basic':
            success = self.combat.use_basic_skill(player, target, all_enemies, allies)
        else:
            success = self.combat.use_ultimate_skill(player, target, all_enemies, allies)
        
        if success:
            for msg in self.combat.log[-3:]:
                self.add_message(msg)
            self.monsters = [m for m in self.monsters if m.is_alive()]
        
        return success
    
    def go_downstairs(self):
        if self.floor >= MAX_FLOOR:
            self.victory()
        else:
            failed_quests = self.quest_manager.fail_floor_locked_quests(self.floor + 1)
            for quest in failed_quests:
                self.add_message(f'任务失败：{quest.name}（本层任务未完成）')
            
            for item in self.player.inventory[:]:
                if hasattr(item, 'item_type') and item.item_type == 'delivery_letter':
                    self.player.inventory.remove(item)
            
            self.floor += 1
            self.generate_floor()
            
            theme_name = FLOOR_THEMES[self.floor]['name']
            self.add_message(f'进入了{theme_name}（第 {self.floor} 层）！')
    
    def move_single_player(self, player, dx, dy, player_num=1):
        if not self.player_turn:
            return False
        
        if player.has_status('stunned') or player.has_status('frozen'):
            self.add_message(f'{player.name}被控制了，无法移动！')
            return False
        
        new_x = player.x + dx
        new_y = player.y + dy
        
        other_player = self.player2 if player_num == 1 else self.player
        if other_player and other_player.x == new_x and other_player.y == new_y:
            return False
        
        for monster in self.monsters:
            if monster.x == new_x and monster.y == new_y:
                if hasattr(monster, 'is_summon') and monster.is_summon:
                    self.add_message('不能攻击自己的召唤物！')
                    return True
                attack_count = player.get_total_attack_count()
                for i in range(attack_count):
                    if monster.is_alive():
                        self.combat.attack(player, monster)
                if not monster.is_alive() and monster in self.monsters:
                    self.monsters.remove(monster)
                return True
        
        for item in self.items[:]:
            if item.x == new_x and item.y == new_y:
                if hasattr(item, 'is_open') and not item.is_open:
                    msg = item.open(player)
                    self.add_message(msg)
                    self.items.remove(item)
                elif hasattr(item, 'amount'):
                    player.gold += item.amount
                    self.items.remove(item)
                    self.add_message(f'{player.name}拾取了 {item.amount} 金币！')
                else:
                    if hasattr(item, 'item_type') and item.item_type == 'quest_item':
                        self.quest_manager.update_collect_progress(item)
                        self.items.remove(item)
                        self.add_message(f'{player.name}收集了任务物品：{item.name}！')
                    elif player.add_item(item):
                        self.items.remove(item)
                        self.add_message(f'{player.name}拾取了 {item.name}！')
        
        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            if self.game_map.tiles[new_x][new_y] == 0:
                player.move(dx, dy)
                self.game_map.add_to_path(player.x, player.y)
                
                affected, msg = self.game_map.apply_terrain_effect(player, player.x, player.y)
                if affected and msg:
                    self.add_message(msg)
                
                if self.game_mode == 'coop' and self.player2:
                    if self.player.is_alive():
                        self.game_map.update_fov(self.player.x, self.player.y, 15)
                    elif self.player2.is_alive():
                        self.game_map.update_fov(self.player2.x, self.player2.y, 15)
                else:
                    self.game_map.update_fov(player.x, player.y, 15)
                
                if self.map_reveal_duration > 0:
                    self.game_map.reveal_all()
                
                self.update_camera()
        
        room = self.game_map.get_room_at(player.x, player.y)
        current_room_type = room.room_type if room else None
        
        if current_room_type == 'shop' and self.last_room_type != 'shop':
            self.state = GameState.SHOP
            
            self.shop.is_mysterious = random.random() < 0.15
            self.shop.refresh_items(self.game_mode, self.floor)
            
            if self.shop.is_mysterious:
                self.add_message('🎭 遇到了神秘商人！有稀有物品出售！')
            else:
                self.add_message('欢迎来到商店！')
            
            if self.game_mode == 'coop':
                has_dead_teammate = False
                if self.player2 and not self.player2.is_alive():
                    has_dead_teammate = True
                elif not self.player.is_alive():
                    has_dead_teammate = True
                
                if has_dead_teammate:
                    from .items import ReviveScroll
                    has_revive = False
                    for item in self.shop.inventory:
                        if hasattr(item, 'item_type') and item.item_type == 'revive_scroll':
                            has_revive = True
                            break
                    if not has_revive:
                        self.shop.inventory.append(ReviveScroll(0, 0))
                        self.add_message('老板拿出了一张复活符！')
        elif current_room_type == 'rest' and self.last_room_type != 'rest':
            self.add_message('休息点！按 E 键恢复生命和魔力。')
        
        self.last_room_type = current_room_type
        
        if self.game_map.stairs_pos:
            sx, sy = self.game_map.stairs_pos
            if player.x == sx and player.y == sy:
                boss_alive = any(hasattr(m, 'monster_type') and m.monster_type == 'boss' and m.is_alive() for m in self.monsters)
                if boss_alive:
                    self.add_message('必须先击杀Boss才能前往下一层！')
                else:
                    self.go_downstairs()
        
        return True
    
    def move_player(self, dx, dy):
        moved = self.move_single_player(self.player, dx, dy, 1)
        if moved:
            self.end_player_turn()
    
    def move_player2(self, dx, dy):
        if self.game_mode != 'coop' or not self.player2:
            return
        moved = self.move_single_player(self.player2, dx, dy, 2)
        if moved:
            self.end_player_turn()
    
    def end_player_turn(self):
        self.player_turn = False
        self.turn += 1
        
        all_players = [self.player]
        if self.game_mode == 'coop' and self.player2:
            all_players.append(self.player2)
        
        alive_players = [p for p in all_players if p.is_alive()]
        
        for player in all_players:
            if player.is_alive():
                status_messages = player.update_status_effects()
                for msg in status_messages:
                    self.add_message(msg)
                player.apply_passive_effects()
                player.update_skill_cooldowns()
                player.update_buff_durations()
        
        if self.map_reveal_duration > 0:
            self.map_reveal_duration -= 1
            if self.map_reveal_duration <= 0:
                self.game_map.hide_reveal()
                self.game_map.update_fov(self.player.x, self.player.y, 15)
                self.add_message('地图透视效果消失了')
        
        for monster in self.monsters[:]:
            if hasattr(monster, 'is_summon') and monster.is_summon:
                if hasattr(monster, 'summon_duration'):
                    monster.summon_duration -= 1
                    if monster.summon_duration <= 0:
                        self.add_message(f'{monster.name} 消失了！')
                        self.monsters.remove(monster)
                        continue
        
        new_summons = []
        for monster in self.monsters:
            if hasattr(monster, 'summons') and monster.summons:
                for summon in monster.summons:
                    if summon not in self.monsters:
                        new_summons.append(summon)
                monster.summons = []
        self.monsters.extend(new_summons)
        
        monsters_to_process = [m for m in self.monsters if m.is_alive()]
        
        for monster in monsters_to_process:
            if not monster.is_alive():
                continue
                
            monster.update_status_effects()
            
            if hasattr(monster, 'is_summon') and monster.is_summon:
                monster.update_ai(self.game_map, self.player, self.monsters + alive_players, alive_players)
                continue
            
            monster.update_ai(self.game_map, self.player, self.monsters + alive_players, alive_players)
            
            target = None
            if alive_players:
                target = min(alive_players, key=lambda p: monster.get_distance_to(p))
            
            if target and monster.is_aggro:
                distance = monster.get_distance_to(target)
                
                if hasattr(monster, 'monster_type') and monster.monster_type == 'elite':
                    if distance <= 2 and hasattr(monster, 'use_knockback'):
                        if random.random() < 0.3:
                            success = monster.use_knockback(target, self.game_map)
                            if success:
                                self.add_message(f'{monster.name} 发动了击退攻击！')
                                self.combat.add_skill_effect('knockback', monster.x, monster.y, 20)
                
                if distance <= 1.5 and monster.attack_cooldown <= 0:
                    if not hasattr(monster, 'is_invisible') or not monster.is_invisible:
                        attack_count = 1 if random.random() < 0.7 else 2
                        if hasattr(monster, 'monster_type') and monster.monster_type == 'boss':
                            attack_count = 2 if random.random() < 0.5 else 3
                        
                        for _ in range(attack_count):
                            if target.is_alive():
                                self.combat.attack(monster, target)
                                if target.hp <= 0:
                                    target.is_dead = True
                                    self.add_message(f'{target.name} 倒下了！使用复活符复活！')
                                    alive_players = [p for p in all_players if p.is_alive()]
                        
                        monster.attack_cooldown = 2 if monster.monster_type != 'boss' else 1
                else:
                    if monster.attack_cooldown > 0:
                        monster.attack_cooldown -= 1
            
            self.game_map.apply_terrain_effect(monster, monster.x, monster.y)
        
        dead_monsters = []
        for monster in self.monsters:
            if hasattr(monster, 'should_remove'):
                if monster.should_remove():
                    dead_monsters.append(monster)
            elif not monster.is_alive():
                if not hasattr(monster, 'is_down') or not monster.is_down:
                    dead_monsters.append(monster)
        
        for monster in dead_monsters:
            if hasattr(monster, 'master') and monster.master:
                if hasattr(monster.master, 'summons'):
                    if monster in monster.master.summons:
                        monster.master.summons.remove(monster)
            
            if hasattr(monster, 'summons'):
                for summon in monster.summons:
                    if summon in self.monsters:
                        self.monsters.remove(summon)
            
            if hasattr(monster, 'monster_type') and monster.monster_type != 'summon':
                self.quest_manager.update_hunt_progress(
                    getattr(monster, 'monster_type', 'normal'),
                    getattr(monster, 'name', '')
                )
                self.behavior_tracker.record_monster_killed(
                    getattr(monster, 'monster_type', 'normal')
                )
            
            if hasattr(monster, 'drop_loot') and monster.monster_type in ['elite', 'boss', 'normal']:
                drops = monster.drop_loot()
                for drop in drops:
                    if self.player.add_item(drop):
                        quality_name = QUALITY_NAMES.get(drop.quality, '普通')
                        self.add_message(f'💎 {monster.name} 掉落了 {quality_name} {drop.name}！已存入背包！')
                    else:
                        drop.x = monster.x
                        drop.y = monster.y
                        self.items.append(drop)
                        quality_name = QUALITY_NAMES.get(drop.quality, '普通')
                        self.add_message(f'{monster.name} 掉落了 {quality_name} {drop.name}！背包已满，掉落在地上！')
            
            if monster in self.monsters:
                self.monsters.remove(monster)
            
            if hasattr(monster, 'exp'):
                self.player.gain_exp(monster.exp)
                self.add_message(f'获得了 {monster.exp} 经验！')
            if hasattr(monster, 'gold'):
                self.player.gold += monster.gold
                self.add_message(f'获得了 {monster.gold} 金币！')
        
        all_dead = True
        for player in all_players:
            if player.is_alive():
                all_dead = False
                break
        if all_dead:
            self.game_over()
        
        for player in all_players:
            for buff in player.buffs[:]:
                buff['duration'] -= 1
                if buff['duration'] <= 0:
                    if buff['type'] == 'strength':
                        player.str -= buff['value']
                    elif buff['type'] == 'dexterity':
                        player.dex -= buff['value']
                    player.buffs.remove(buff)
        
        self.combat.update()
        
        for player in all_players:
            if player.level_up_animation > 0:
                player.level_up_animation -= 1
                if player.level_up_animation <= 0:
                    player.is_leveling_up = False
        
        self.behavior_tracker.update_play_time()
        
        self.player_turn = True
    
    def render_player_status(self, player, x, y, label=None):
        status_rect = pygame.Rect(x, y, 300, 90)
        self.draw_transparent_rect(status_rect, (25, 25, 38))
        self.draw_transparent_border(status_rect, (80, 80, 100))
        
        class_name = CLASSES[player.class_type]['name']
        title_text = FONT_LARGE.render(f'{class_name}', True, GOLD)
        title_text.set_alpha(UI_ALPHA)
        level_text = FONT_NORMAL.render(f'Lv.{player.level}', True, WHITE)
        level_text.set_alpha(UI_ALPHA)
        
        if label:
            label_text = FONT_NORMAL.render(label, True, CYAN)
            label_text.set_alpha(UI_ALPHA)
            label_rect = label_text.get_rect(center=(status_rect.x + 25, status_rect.y + 20))
            self.screen.blit(label_text, label_rect)
            title_rect = title_text.get_rect(center=(status_rect.centerx + 15, status_rect.y + 20))
        else:
            title_rect = title_text.get_rect(center=(status_rect.centerx, status_rect.y + 20))
        level_rect = level_text.get_rect(center=(status_rect.centerx + 100, status_rect.y + 25))
        self.screen.blit(title_text, title_rect)
        self.screen.blit(level_text, level_rect)
        
        bar_width = 260
        bar_x = status_rect.centerx - bar_width // 2
        
        y_pos = status_rect.y + 48
        max_hp = player.get_total_max_hp()
        hp_ratio = max(0, player.hp / max_hp)
        pygame.draw.rect(self.screen, (80, 0, 0), (bar_x, y_pos, bar_width, 16))
        pygame.draw.rect(self.screen, (220, 50, 50), (bar_x, y_pos, int(bar_width * hp_ratio), 16))
        pygame.draw.rect(self.screen, (255, 100, 100), (bar_x, y_pos, int(bar_width * hp_ratio), 5))
        hp_text = FONT_SMALL.render(f'❤️ {player.hp}/{max_hp}', True, WHITE)
        hp_text.set_alpha(UI_ALPHA)
        hp_text_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, y_pos + 8))
        self.screen.blit(hp_text, hp_text_rect)
        
        y_pos += 18
        max_mp = player.get_total_max_mp()
        mp_ratio = max(0, player.mp / max_mp)
        pygame.draw.rect(self.screen, (0, 0, 80), (bar_x, y_pos, bar_width, 16))
        pygame.draw.rect(self.screen, (50, 100, 220), (bar_x, y_pos, int(bar_width * mp_ratio), 16))
        pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, y_pos, int(bar_width * mp_ratio), 5))
        mp_text = FONT_SMALL.render(f'💧 {player.mp}/{max_mp}', True, WHITE)
        mp_text.set_alpha(UI_ALPHA)
        mp_text_rect = mp_text.get_rect(center=(bar_x + bar_width // 2, y_pos + 8))
        self.screen.blit(mp_text, mp_text_rect)
    
    def update_camera(self):
        camera_target = self.player
        if self.game_mode == 'coop' and self.player2:
            if not self.player.is_alive() and self.player2.is_alive():
                camera_target = self.player2
        
        target_x = camera_target.x * TILE_SIZE - SCREEN_WIDTH // 2
        target_y = camera_target.y * TILE_SIZE - SCREEN_HEIGHT // 2
        
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        self.camera_x = max(0, min(self.camera_x, MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT))
    
    def render(self):
        self.screen.fill((10, 10, 15))
        
        if self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.MODE_SELECT:
            self.render_mode_select()
        elif self.state == GameState.CLASS_SELECT:
            self.render_class_select()
        elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.INVENTORY, GameState.SHOP, GameState.TALENT, GameState.SYNTHESIS, GameState.QUEST_PANEL, GameState.NPC_INTERACT]:
            self.render_game()
            if self.state == GameState.PAUSED:
                self.render_pause_menu()
            elif self.state == GameState.INVENTORY:
                self.render_inventory()
            elif self.state == GameState.SHOP:
                self.render_shop()
            elif self.state == GameState.TALENT:
                self.render_talent()
            elif self.state == GameState.SYNTHESIS:
                self.render_synthesis()
            elif self.state == GameState.QUEST_PANEL:
                self.render_quest_panel()
            elif self.state == GameState.NPC_INTERACT:
                self.render_npc_interact()
        elif self.state == GameState.GAME_OVER:
            self.render_game_over()
        elif self.state == GameState.VICTORY:
            self.render_victory()
        elif self.state == GameState.ENDING:
            self.render_ending()
        elif self.state == GameState.LEADERBOARD:
            self.render_leaderboard()
        
        pygame.display.flip()
    
    def render_mode_select(self):
        title_bg = pygame.Rect(SCREEN_WIDTH // 2 - 300, 80, 600, 100)
        pygame.draw.rect(self.screen, (40, 40, 60), title_bg)
        pygame.draw.rect(self.screen, GOLD, title_bg, 3)
        
        title = FONT_LARGE.render('选择游戏模式', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self.screen.blit(title, title_rect)
        
        mode_items = ['单人模式', '双人模式 (Co-op)']
        mode_descriptions = ['独自冒险探索地牢', '与朋友并肩作战，怪物更多！']
        for i, (item, desc) in enumerate(zip(mode_items, mode_descriptions)):
            y = 280 + i * 100
            item_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, y, 500, 80)
            
            if i == self.menu_selection:
                pygame.draw.rect(self.screen, (60, 70, 90), item_rect)
                pygame.draw.rect(self.screen, GOLD, item_rect, 3)
                color = YELLOW
            else:
                pygame.draw.rect(self.screen, (35, 35, 50), item_rect)
                pygame.draw.rect(self.screen, (70, 70, 90), item_rect, 2)
                color = WHITE
            
            text = FONT_LARGE.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y + 30))
            self.screen.blit(text, text_rect)
            
            desc_text = FONT_SMALL.render(desc, True, GRAY)
            desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, y + 58))
            self.screen.blit(desc_text, desc_rect)
        
        footer_text = FONT_SMALL.render('使用方向键选择，按回车确认，ESC返回', True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(footer_text, footer_rect)
    
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
                elif hasattr(item, 'amount') and hasattr(item, 'item_type') and item.item_type == 'gold':
                    self.dungeon_renderer.draw_gold(self.screen, item.x, item.y, self.camera_x, self.camera_y, item.amount, True)
                elif hasattr(item, 'item_type') and item.item_type == 'equipment':
                    screen_x = item.x * TILE_SIZE - int(self.camera_x)
                    screen_y = item.y * TILE_SIZE - int(self.camera_y)
                    quality_color = QUALITY_BORDER_COLORS.get(item.quality, GRAY)
                    pygame.draw.rect(self.screen, quality_color, (screen_x + 8, screen_y + 8, 16, 16))
                    pygame.draw.rect(self.screen, (255, 255, 255), (screen_x + 8, screen_y + 8, 16, 16), 1)
                elif hasattr(item, 'item_type') and item.item_type == 'potion':
                    screen_x = item.x * TILE_SIZE - int(self.camera_x)
                    screen_y = item.y * TILE_SIZE - int(self.camera_y)
                    pygame.draw.circle(self.screen, (255, 100, 100), (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), 8)
                    pygame.draw.circle(self.screen, (200, 50, 50), (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2), 5)
                elif hasattr(item, 'item_type') and item.item_type == 'scroll':
                    screen_x = item.x * TILE_SIZE - int(self.camera_x)
                    screen_y = item.y * TILE_SIZE - int(self.camera_y)
                    pygame.draw.rect(self.screen, (200, 200, 200), (screen_x + 8, screen_y + 6, 16, 20))
                    pygame.draw.rect(self.screen, (150, 150, 150), (screen_x + 8, screen_y + 6, 16, 20), 1)
        
        for monster in self.monsters:
            if self.game_map.explored[monster.x][monster.y] and self.game_map.visible[monster.x][monster.y]:
                if monster.monster_type == 'boss':
                    boss_name = monster.name
                    boss_color = monster.color
                    self.monster_renderer.draw_dragon(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True, boss_name, boss_color)
                elif monster.monster_type == 'elite':
                    self.monster_renderer.draw_elite_orc(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                else:
                    monster_name = monster.name
                    if '哥布林' in monster_name:
                        self.monster_renderer.draw_goblin(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '兽人' in monster_name and '精英' not in monster_name:
                        self.monster_renderer.draw_orc(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '骷髅' in monster_name:
                        self.monster_renderer.draw_skeleton(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '黑暗法师' in monster_name:
                        self.monster_renderer.draw_mage(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '召唤法师' in monster_name:
                        self.monster_renderer.draw_summoner(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '召唤小弟' in monster_name:
                        self.monster_renderer.draw_summon_minion(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
                    elif '幽灵刺客' in monster_name:
                        is_invisible = hasattr(monster, 'is_invisible') and monster.is_invisible
                        self.monster_renderer.draw_invisible_monster(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True, is_invisible)
                    elif '不死战士' in monster_name:
                        is_down = hasattr(monster, 'is_down') and monster.is_down
                        revive_count = monster.revive_count if hasattr(monster, 'revive_count') else 0
                        self.monster_renderer.draw_reviver(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True, is_down, revive_count)
                    else:
                        self.monster_renderer.draw_goblin(self.screen, monster.x, monster.y, self.camera_x, self.camera_y, monster.hp, monster.max_hp, monster.is_hurt, True)
        
        for npc in self.npcs:
            if self.game_map.explored[npc.x][npc.y] and self.game_map.visible[npc.x][npc.y]:
                self.dungeon_renderer.draw_npc(self.screen, npc.x, npc.y, self.camera_x, self.camera_y, npc, True)
        
        for effect in self.combat.skill_effects:
            self.player_renderer.skill_effect_renderer.draw_skill_effect(self.screen, effect, self.camera_x, self.camera_y)
        
        class_name = CLASSES[self.player.class_type]['name']
        if self.player.is_alive():
            if not (hasattr(self.player, 'is_invisible') and self.player.is_invisible):
                if class_name == '战士':
                    self.player_renderer.draw_warrior(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
                elif class_name == '法师':
                    self.player_renderer.draw_mage(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
                elif class_name == '盗贼':
                    self.player_renderer.draw_rogue(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
                elif class_name == '圣骑士':
                    self.player_renderer.draw_paladin(self.screen, self.player.x, self.player.y, self.camera_x, self.camera_y, self.player.is_hurt)
        else:
            px = self.player.x * TILE_SIZE - int(self.camera_x)
            py = self.player.y * TILE_SIZE - int(self.camera_y)
            death_text = FONT_NORMAL.render('💀', True, (150, 150, 150))
            death_rect = death_text.get_rect(center=(px + TILE_SIZE // 2, py + TILE_SIZE // 2))
            self.screen.blit(death_text, death_rect)
        
        if self.game_mode == 'coop' and self.player2:
            if self.game_map.explored[self.player2.x][self.player2.y] and self.game_map.visible[self.player2.x][self.player2.y]:
                if self.player2.is_alive():
                    class_name2 = CLASSES[self.player2.class_type]['name']
                    if not (hasattr(self.player2, 'is_invisible') and self.player2.is_invisible):
                        if class_name2 == '战士':
                            self.player_renderer.draw_warrior(self.screen, self.player2.x, self.player2.y, self.camera_x, self.camera_y, self.player2.is_hurt)
                        elif class_name2 == '法师':
                            self.player_renderer.draw_mage(self.screen, self.player2.x, self.player2.y, self.camera_x, self.camera_y, self.player2.is_hurt)
                        elif class_name2 == '盗贼':
                            self.player_renderer.draw_rogue(self.screen, self.player2.x, self.player2.y, self.camera_x, self.camera_y, self.player2.is_hurt)
                        elif class_name2 == '圣骑士':
                            self.player_renderer.draw_paladin(self.screen, self.player2.x, self.player2.y, self.camera_x, self.camera_y, self.player2.is_hurt)
                else:
                    px = self.player2.x * TILE_SIZE - int(self.camera_x)
                    py = self.player2.y * TILE_SIZE - int(self.camera_y)
                    death_text = FONT_NORMAL.render('💀', True, (150, 150, 150))
                    death_rect = death_text.get_rect(center=(px + TILE_SIZE // 2, py + TILE_SIZE // 2))
                    self.screen.blit(death_text, death_rect)
        
        self.player_renderer.skill_effect_renderer.draw_damage_numbers(self.screen, self.combat.damage_numbers, self.camera_x, self.camera_y)
        
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
    
    def draw_transparent_rect(self, rect, color, alpha=UI_ALPHA):
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.fill((color[0], color[1], color[2], alpha))
        self.screen.blit(surf, (rect.x, rect.y))
    
    def draw_transparent_border(self, rect, color, alpha=UI_ALPHA, border_width=2):
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (color[0], color[1], color[2], alpha), (0, 0, rect.width, rect.height), border_width)
        self.screen.blit(surf, (rect.x, rect.y))
    
    def render_ui(self):
        top_left_log_rect = pygame.Rect(10, 10, 350, 180)
        self.draw_transparent_rect(top_left_log_rect, (20, 20, 30))
        self.draw_transparent_border(top_left_log_rect, (80, 80, 100))
        
        log_title = FONT_NORMAL.render('📜 战斗日志', True, GOLD)
        log_title.set_alpha(UI_ALPHA)
        self.screen.blit(log_title, (top_left_log_rect.x + 10, top_left_log_rect.y + 8))
        
        y_log = top_left_log_rect.y + 35
        for msg in self.message_log[-6:]:
            msg_text = FONT_SMALL.render(msg, True, (200, 200, 220))
            msg_text.set_alpha(UI_ALPHA)
            self.screen.blit(msg_text, (top_left_log_rect.x + 12, y_log))
            y_log += 22
        
        skill_panel_rect = pygame.Rect(10, 200, 350, 100)
        self.draw_transparent_rect(skill_panel_rect, (20, 20, 30))
        self.draw_transparent_border(skill_panel_rect, (80, 80, 100))
        
        skill_data = SKILLS[self.player.class_type]
        basic_skill = skill_data['basic']
        ultimate_skill = skill_data['ultimate']
        
        basic_cd = self.player.skill_cooldowns.get('basic', 0)
        ult_cd = self.player.skill_cooldowns.get('ultimate', 0)
        
        basic_color = WHITE if basic_cd <= 0 else GRAY
        ult_color = WHITE if ult_cd <= 0 else GRAY
        
        basic_text = FONT_SMALL.render(f'[Q] {basic_skill["name"]}', True, basic_color)
        basic_text.set_alpha(UI_ALPHA)
        self.screen.blit(basic_text, (skill_panel_rect.x + 10, skill_panel_rect.y + 10))
        
        basic_cd_text = FONT_SMALL.render(f'CD: {basic_cd} | MP:{basic_skill["mp_cost"]}', True, (150, 150, 180))
        basic_cd_text.set_alpha(UI_ALPHA)
        self.screen.blit(basic_cd_text, (skill_panel_rect.x + 10, skill_panel_rect.y + 35))
        
        ult_text = FONT_SMALL.render(f'[R] {ultimate_skill["name"]}', True, ult_color)
        ult_text.set_alpha(UI_ALPHA)
        self.screen.blit(ult_text, (skill_panel_rect.x + 180, skill_panel_rect.y + 10))
        
        ult_cd_text = FONT_SMALL.render(f'CD: {ult_cd} | MP:{ultimate_skill["mp_cost"]}', True, (150, 150, 180))
        ult_cd_text.set_alpha(UI_ALPHA)
        self.screen.blit(ult_cd_text, (skill_panel_rect.x + 180, skill_panel_rect.y + 35))
        
        key_hints_rect = pygame.Rect(10, 310, 350, 80)
        self.draw_transparent_rect(key_hints_rect, (20, 20, 30))
        self.draw_transparent_border(key_hints_rect, (80, 80, 100))
        
        if self.game_mode == 'coop':
            hint_lines = [
                'P1: WASD移动 | 空格攻击 | Q小技能 | R大招',
                'P2: 小键盘8456移动 | 回车攻击 | 7小技能 | 9大招',
                'E:交互 | I:背包 | T:天赋 | ESC:暂停'
            ]
        else:
            hint_lines = [
                'WASD/方向键:移动 | 空格:攻击 | E:交互',
                'Q:小技能 | R:大招 | I:背包 | T:天赋 | ESC:暂停'
            ]
        y_hint = key_hints_rect.y + 8
        for line in hint_lines:
            hint_text = FONT_SMALL.render(line, True, (150, 150, 180))
            hint_text.set_alpha(UI_ALPHA)
            self.screen.blit(hint_text, (key_hints_rect.x + 10, y_hint))
            y_hint += 22
        
        if self.game_mode == 'coop' and self.player2:
            self.render_player_status(self.player, SCREEN_WIDTH // 2 - 310, 10, 'P1')
            self.render_player_status(self.player2, SCREEN_WIDTH // 2 + 10, 10, 'P2')
        else:
            self.render_player_status(self.player, SCREEN_WIDTH // 2 - 250, 10)
        
        left_panel_rect = pygame.Rect(10, 400, 200, 350)
        self.draw_transparent_rect(left_panel_rect, (25, 25, 38))
        self.draw_transparent_border(left_panel_rect, (80, 80, 100))
        
        y = left_panel_rect.y + 12
        stats_title = FONT_NORMAL.render('📊 属性', True, GOLD)
        stats_title.set_alpha(UI_ALPHA)
        self.screen.blit(stats_title, (left_panel_rect.x + 12, y))
        y += 28
        
        stats_text = [
            f'⚔️ 物攻: {self.player.get_total_physical_attack()}',
            f'✨ 法攻: {self.player.get_total_magic_attack()}',
            f'🛡️ 物防: {self.player.get_total_physical_defense()}',
            f'💪 力量: {self.player.get_total_str()}',
            f'🏃 敏捷: {self.player.get_total_dex()}',
            f'📖 智力: {self.player.get_total_int()}',
            f'🎯 暴击: {self.player.get_total_critical_chance()}%',
            f'⚡ 暴伤: {self.player.get_total_critical_damage()}%',
            f'👻 闪避: {self.player.get_total_evasion()}%'
        ]
        for text in stats_text:
            stat_text = FONT_SMALL.render(text, True, (200, 200, 200))
            stat_text.set_alpha(UI_ALPHA)
            self.screen.blit(stat_text, (left_panel_rect.x + 12, y))
            y += 24
        
        y += 8
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        gold_text.set_alpha(UI_ALPHA)
        self.screen.blit(gold_text, (left_panel_rect.x + 12, y))
        
        if self.player.shield > 0:
            y += 28
            shield_text = FONT_SMALL.render(f'🛡️ 护盾: {self.player.shield}', True, (100, 150, 255))
            shield_text.set_alpha(UI_ALPHA)
            self.screen.blit(shield_text, (left_panel_rect.x + 12, y))
        
        if hasattr(self.player, 'is_berserk') and self.player.is_berserk:
            y += 24
            berserk_text = FONT_SMALL.render(f'🔥 狂暴! ({self.player.berserk_duration})', True, (255, 100, 50))
            berserk_text.set_alpha(UI_ALPHA)
            self.screen.blit(berserk_text, (left_panel_rect.x + 12, y))
        
        if self.player.status_effects:
            y += 24
            status_title = FONT_SMALL.render('状态:', True, GOLD)
            status_title.set_alpha(UI_ALPHA)
            self.screen.blit(status_title, (left_panel_rect.x + 12, y))
            y += 20
            for status in self.player.status_effects[:3]:
                status_color = {
                    'poison': (100, 200, 100),
                    'burning': (255, 100, 50),
                    'frozen': (150, 200, 255),
                    'stunned': (200, 200, 100),
                    'slowed': (150, 150, 200),
                    'haste': (255, 255, 100)
                }.get(status['type'], WHITE)
                status_text = FONT_SMALL.render(f"  {status['type']} ({status['duration']})", True, status_color)
                status_text.set_alpha(UI_ALPHA)
                self.screen.blit(status_text, (left_panel_rect.x + 12, y))
                y += 18
        
        right_panel_rect = pygame.Rect(SCREEN_WIDTH - 220, 10, 210, 380)
        self.draw_transparent_rect(right_panel_rect, (25, 25, 38))
        self.draw_transparent_border(right_panel_rect, (80, 80, 100))
        
        minimap_size = 190
        minimap_rect = pygame.Rect(right_panel_rect.x + 10, right_panel_rect.y + 10, minimap_size, minimap_size)
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
        
        quest_targets = self.quest_manager.get_quest_target_positions()
        for (pos, quest_type) in quest_targets:
            tx, ty = pos
            if self.game_map.explored[tx][ty]:
                px = int(minimap_rect.x + tx * scale)
                py = int(minimap_rect.y + ty * scale)
                if quest_type == 'collect':
                    pygame.draw.circle(self.screen, (100, 255, 100), (px, py), 4)
                elif quest_type == 'delivery':
                    pygame.draw.circle(self.screen, (100, 200, 255), (px, py), 4)
        
        for npc in self.npcs:
            if self.game_map.explored[npc.x][npc.y]:
                px = int(minimap_rect.x + npc.x * scale)
                py = int(minimap_rect.y + npc.y * scale)
                pygame.draw.circle(self.screen, (200, 200, 100), (px, py), 3)
        
        for room in self.game_map.rooms:
            if room.room_type == 'shop':
                room_center_x = (room.x1 + room.x2) // 2
                room_center_y = (room.y1 + room.y2) // 2
                if self.game_map.explored[room_center_x][room_center_y]:
                    px = int(minimap_rect.x + room_center_x * scale)
                    py = int(minimap_rect.y + room_center_y * scale)
                    pygame.draw.rect(self.screen, (0, 255, 100), (px - 4, py - 4, 8, 8))
                    shop_text = FONT_SMALL.render('$', True, (0, 255, 100))
                    shop_rect = shop_text.get_rect(center=(px, py))
                    self.screen.blit(shop_text, shop_rect)
        
        px = int(minimap_rect.x + self.player.x * scale)
        py = int(minimap_rect.y + self.player.y * scale)
        pygame.draw.circle(self.screen, CYAN, (px, py), 5)
        pygame.draw.circle(self.screen, WHITE, (px, py), 3)
        
        floor_text = FONT_NORMAL.render(f'第 {self.floor} 层', True, WHITE)
        floor_rect = floor_text.get_rect(center=(minimap_rect.centerx, minimap_rect.y + minimap_size + 15))
        self.screen.blit(floor_text, floor_rect)
        
        exp_bar_rect = pygame.Rect(right_panel_rect.x + 10, minimap_rect.y + minimap_size + 45, 190, 14)
        pygame.draw.rect(self.screen, (40, 40, 0), exp_bar_rect)
        exp_ratio = self.player.exp / self.player.exp_to_next
        pygame.draw.rect(self.screen, (200, 200, 0), (exp_bar_rect.x, exp_bar_rect.y, int(190 * exp_ratio), 14))
        exp_text = FONT_SMALL.render(f'EXP: {self.player.exp}/{self.player.exp_to_next}', True, WHITE)
        exp_rect = exp_text.get_rect(center=(exp_bar_rect.centerx, exp_bar_rect.y + 28))
        self.screen.blit(exp_text, exp_rect)
        
        collection_text = FONT_SMALL.render(f'📚 图鉴: {self.player.get_collection_count()}', True, GOLD)
        self.screen.blit(collection_text, (right_panel_rect.x + 12, exp_bar_rect.y + 55))
        
        material_text = FONT_SMALL.render(f'💎 材料: {self.player.enhance_materials}', True, (150, 200, 255))
        self.screen.blit(material_text, (right_panel_rect.x + 12, exp_bar_rect.y + 78))
    
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
        title_bg = pygame.Rect(SCREEN_WIDTH // 2 - 300, 30, 600, 70)
        pygame.draw.rect(self.screen, (40, 40, 60), title_bg)
        pygame.draw.rect(self.screen, GOLD, title_bg, 3)
        
        if self.game_mode == 'coop':
            if hasattr(self, 'selected_class1') and self.selected_class1:
                p1_class = CLASSES[self.selected_class1]['name']
                title = FONT_LARGE.render(f'玩家2选择职业 (P1: {p1_class})', True, GOLD)
            else:
                title = FONT_LARGE.render('玩家1选择职业', True, GOLD)
        else:
            title = FONT_LARGE.render('选择你的职业', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 65))
        self.screen.blit(title, title_rect)
        
        class_data = [
            ('warrior', '战士', '主打破甲近战爆发', RED, ['HP: 150', 'MP: 30', '小技能: 破甲猛击', '大招: 狂怒碎山斩']),
            ('mage', '法师', '主打持续伤害群控', BLUE, ['HP: 80', 'MP: 120', '小技能: 烈焰弹', '大招: 陨星天火']),
            ('rogue', '盗贼', '主打背刺高速偷袭', GREEN, ['HP: 100', 'MP: 50', '小技能: 暗影突袭', '大招: 影杀千刃']),
            ('paladin', '圣骑士', '主打护盾续航治疗', (255, 215, 0), ['HP: 130', 'MP: 80', '小技能: 神圣庇护', '大招: 圣光审判'])
        ]
        
        for i, (key, name, desc, color, stats) in enumerate(class_data):
            x = 80 + i * 350
            panel_rect = pygame.Rect(x, 120, 300, 480)
            
            if i == self.menu_selection:
                bg_color = (50, 50, 70)
                border_color = GOLD
            else:
                bg_color = (30, 30, 45)
                border_color = (70, 70, 90)
            
            pygame.draw.rect(self.screen, bg_color, panel_rect)
            pygame.draw.rect(self.screen, border_color, panel_rect, 3)
            
            class_title = FONT_LARGE.render(name, True, color)
            self.screen.blit(class_title, (x + 30, 140))
            
            pygame.draw.circle(self.screen, color, (x + 150, 230), 40)
            pygame.draw.circle(self.screen, WHITE, (x + 150, 230), 40, 3)
            pygame.draw.circle(self.screen, WHITE, (x + 135, 220), 8)
            pygame.draw.circle(self.screen, WHITE, (x + 165, 220), 8)
            pygame.draw.circle(self.screen, BLACK, (x + 135, 220), 4)
            pygame.draw.circle(self.screen, BLACK, (x + 165, 220), 4)
            
            y = 290
            for stat in stats:
                stat_text = FONT_NORMAL.render(stat, True, WHITE)
                self.screen.blit(stat_text, (x + 30, y))
                y += 30
            
            desc_text = FONT_SMALL.render(desc, True, GRAY)
            self.screen.blit(desc_text, (x + 30, y + 10))
            
            skill_info = FONT_SMALL.render(f'Q:小技能 R:大招', True, (150, 200, 255))
            self.screen.blit(skill_info, (x + 30, y + 35))
        
        if self.game_mode == 'coop':
            footer_text = FONT_NORMAL.render('按 ← → 选择，回车确认，ESC返回', True, GRAY)
        else:
            footer_text = FONT_NORMAL.render('按 ← → 选择职业，按回车键开始游戏', True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
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
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 500, 50, 1000, 650)
        pygame.draw.rect(self.screen, (25, 25, 38), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        title = FONT_LARGE.render('🎒 背包 & 装备', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        self.screen.blit(gold_text, (SCREEN_WIDTH // 2 + 400, 85))
        
        equip_panel_rect = pygame.Rect(panel_rect.x + 20, 110, 280, 400)
        pygame.draw.rect(self.screen, (20, 20, 30), equip_panel_rect)
        pygame.draw.rect(self.screen, (70, 70, 90), equip_panel_rect, 2)
        
        equip_title = FONT_NORMAL.render('⚔️ 已装备', True, GOLD)
        self.screen.blit(equip_title, (equip_panel_rect.x + 15, equip_panel_rect.y + 12))
        
        slot_positions = [
            ('weapon', equip_panel_rect.x + 20, equip_panel_rect.y + 50),
            ('helmet', equip_panel_rect.x + 150, equip_panel_rect.y + 50),
            ('chest', equip_panel_rect.x + 20, equip_panel_rect.y + 110),
            ('leggings', equip_panel_rect.x + 150, equip_panel_rect.y + 110),
            ('boots', equip_panel_rect.x + 20, equip_panel_rect.y + 170),
            ('accessory', equip_panel_rect.x + 150, equip_panel_rect.y + 170)
        ]
        
        for slot, x, y in slot_positions:
            item = self.player.equipment[slot]
            slot_rect = pygame.Rect(x, y, 110, 50)
            
            if item:
                quality_color = QUALITY_BORDER_COLORS.get(item.quality, GRAY)
                pygame.draw.rect(self.screen, (40, 40, 55), slot_rect)
                pygame.draw.rect(self.screen, quality_color, slot_rect, 2)
                
                if item.quality == 'legendary':
                    glow_surf = pygame.Surface((114, 54), pygame.SRCALPHA)
                    glow_alpha = int(100 + 50 * pygame.time.get_ticks() / 500 % 1)
                    pygame.draw.rect(glow_surf, (255, 215, 0, glow_alpha), (2, 2, 110, 50), 2)
                    self.screen.blit(glow_surf, (x - 2, y - 2))
                
                name_color = QUALITY_COLORS.get(item.quality, WHITE)
                name_text = FONT_SMALL.render(item.name, True, name_color)
                name_rect = name_text.get_rect(center=(slot_rect.centerx, slot_rect.y + 15))
                self.screen.blit(name_text, name_rect)
                
                power_text = FONT_SMALL.render(f'战力:{item.get_power()}', True, YELLOW)
                power_rect = power_text.get_rect(center=(slot_rect.centerx, slot_rect.y + 35))
                self.screen.blit(power_text, power_rect)
            else:
                pygame.draw.rect(self.screen, (30, 30, 40), slot_rect)
                pygame.draw.rect(self.screen, (60, 60, 70), slot_rect, 2)
                slot_text = FONT_SMALL.render(SLOT_NAMES[slot], True, GRAY)
                slot_rect_text = slot_text.get_rect(center=slot_rect.center)
                self.screen.blit(slot_text, slot_rect_text)
        
        set_counts = self.player.get_set_counts()
        if set_counts:
            y_set = equip_panel_rect.y + 240
            set_title = FONT_SMALL.render('📦 套装效果:', True, GOLD)
            self.screen.blit(set_title, (equip_panel_rect.x + 15, y_set))
            y_set += 22
            for set_name, count in set_counts.items():
                set_text = FONT_SMALL.render(f'  {set_name} ({count}/5)', True, CYAN)
                self.screen.blit(set_text, (equip_panel_rect.x + 15, y_set))
                y_set += 18
        
        items_panel_rect = pygame.Rect(panel_rect.x + 310, 110, 400, 500)
        pygame.draw.rect(self.screen, (20, 20, 30), items_panel_rect)
        pygame.draw.rect(self.screen, (70, 70, 90), items_panel_rect, 2)
        
        items_title = FONT_NORMAL.render('📦 物品列表', True, GOLD)
        self.screen.blit(items_title, (items_panel_rect.x + 15, items_panel_rect.y + 12))
        
        sort_text = FONT_SMALL.render('排序:战力 | 筛选:全部', True, GRAY)
        self.screen.blit(sort_text, (items_panel_rect.x + 200, items_panel_rect.y + 15))
        
        display_items = self.player.get_sorted_inventory()
        y_item = items_panel_rect.y + 45
        for i, item in enumerate(display_items[:18]):
            if i == self.inventory_selection:
                bg_color = (50, 50, 70)
            else:
                bg_color = (35, 35, 50)
            
            item_bg = pygame.Rect(items_panel_rect.x + 8, y_item, 384, 24)
            pygame.draw.rect(self.screen, bg_color, item_bg)
            
            if hasattr(item, 'quality'):
                quality_color = QUALITY_COLORS.get(item.quality, WHITE)
            else:
                quality_color = WHITE
            
            prefix = '⚔️ ' if hasattr(item, 'slot') else '🧪 ' if hasattr(item, 'potion_type') else '📜 ' if hasattr(item, 'scroll_type') else '💰 '
            item_text = FONT_SMALL.render(f'{prefix}{item.name}', True, quality_color)
            self.screen.blit(item_text, (items_panel_rect.x + 15, y_item + 3))
            
            if hasattr(item, 'get_power'):
                power_text = FONT_SMALL.render(f'{item.get_power()}', True, YELLOW)
                self.screen.blit(power_text, (items_panel_rect.x + 340, y_item + 3))
            
            y_item += 26
        
        detail_panel_rect = pygame.Rect(panel_rect.x + 720, 110, 260, 500)
        pygame.draw.rect(self.screen, (20, 20, 30), detail_panel_rect)
        pygame.draw.rect(self.screen, (70, 70, 90), detail_panel_rect, 2)
        
        if display_items and 0 <= self.inventory_selection < len(display_items):
            selected = display_items[self.inventory_selection]
            
            name_color = QUALITY_COLORS.get(selected.quality, GOLD) if hasattr(selected, 'quality') else GOLD
            name_text = FONT_NORMAL.render(selected.name, True, name_color)
            self.screen.blit(name_text, (detail_panel_rect.x + 15, detail_panel_rect.y + 15))
            
            y_detail = detail_panel_rect.y + 45
            
            if hasattr(selected, 'quality'):
                quality_text = FONT_SMALL.render(f'品质: {QUALITY_NAMES[selected.quality]}', True, quality_color)
                self.screen.blit(quality_text, (detail_panel_rect.x + 15, y_detail))
                y_detail += 22
            
            if hasattr(selected, 'slot'):
                type_text = FONT_SMALL.render(f'部位: {SLOT_NAMES.get(selected.slot, "其他")}', True, WHITE)
                self.screen.blit(type_text, (detail_panel_rect.x + 15, y_detail))
                y_detail += 22
            
            if hasattr(selected, 'enhance_level') and selected.enhance_level > 0:
                enhance_text = FONT_SMALL.render(f'强化: +{selected.enhance_level}', True, YELLOW)
                self.screen.blit(enhance_text, (detail_panel_rect.x + 15, y_detail))
                y_detail += 22
            
            if hasattr(selected, 'base_stats') and selected.base_stats:
                y_detail += 5
                stat_title = FONT_SMALL.render('基础属性:', True, CYAN)
                self.screen.blit(stat_title, (detail_panel_rect.x + 15, y_detail))
                y_detail += 18
                for stat, value in selected.base_stats.items():
                    stat_name = BASE_STAT_NAMES.get(stat, stat)
                    stat_text = FONT_SMALL.render(f'  +{value} {stat_name}', True, GREEN)
                    self.screen.blit(stat_text, (detail_panel_rect.x + 15, y_detail))
                    y_detail += 16
            
            if hasattr(selected, 'sub_stats') and selected.sub_stats:
                y_detail += 5
                sub_stat_title = FONT_SMALL.render('副词条:', True, (200, 150, 255))
                self.screen.blit(sub_stat_title, (detail_panel_rect.x + 15, y_detail))
                y_detail += 18
                for stat, value in selected.sub_stats.items():
                    stat_name = SUB_STAT_NAMES.get(stat, stat)
                    stat_text = FONT_SMALL.render(f'  +{value}% {stat_name}', True, (180, 220, 255))
                    self.screen.blit(stat_text, (detail_panel_rect.x + 15, y_detail))
                    y_detail += 16
            
            if hasattr(selected, 'element_enchant') and selected.element_enchant:
                y_detail += 5
                element_color = ELEMENT_COLORS[selected.element_enchant]
                element_text = FONT_SMALL.render(f'附魔: +{selected.element_damage} {ELEMENT_NAMES[selected.element_enchant]}伤害', True, element_color)
                self.screen.blit(element_text, (detail_panel_rect.x + 15, y_detail))
                y_detail += 18
            
            if hasattr(selected, 'rune_slots') and selected.rune_slots > 0:
                y_detail += 5
                rune_title = FONT_SMALL.render(f'符文槽 ({selected.rune_slots}):', True, (255, 200, 100))
                self.screen.blit(rune_title, (detail_panel_rect.x + 15, y_detail))
                y_detail += 18
                for i, rune in enumerate(selected.runes):
                    if rune:
                        rune_text = FONT_SMALL.render(f'  [{i+1}] {RUNE_NAMES[rune]}', True, (255, 220, 150))
                    else:
                        rune_text = FONT_SMALL.render(f'  [{i+1}] 空槽', True, GRAY)
                    self.screen.blit(rune_text, (detail_panel_rect.x + 15, y_detail))
                    y_detail += 16
            
            if hasattr(selected, 'set_name') and selected.set_name:
                y_detail += 5
                set_text = FONT_SMALL.render(f'📦 {selected.set_name}', True, (200, 100, 255))
                self.screen.blit(set_text, (detail_panel_rect.x + 15, y_detail))
                y_detail += 18
            
            value_text = FONT_SMALL.render(f'价值: {selected.value} 金币', True, GRAY)
            self.screen.blit(value_text, (detail_panel_rect.x + 15, detail_panel_rect.y + 470))
        
        help_bg = pygame.Rect(panel_rect.x + 20, panel_rect.y + panel_rect.height - 55, 960, 40)
        pygame.draw.rect(self.screen, (25, 25, 35), help_bg)
        
        help_lines = [
            '↑↓:选择 | E:装备 | U:脱下 | D:分解(金币) | R:批量分解白装 | 空格:使用 | ESC:关闭'
        ]
        help_text = FONT_NORMAL.render(help_lines[0], True, GRAY)
        help_rect = help_text.get_rect(center=help_bg.center)
        self.screen.blit(help_text, help_rect)
    
    def render_shop(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 500, 40, 1000, 680)
        pygame.draw.rect(self.screen, (30, 30, 45), panel_rect)
        
        shop_title = '神秘商人' if self.shop.is_mysterious else '商店'
        title_color = (255, 0, 255) if self.shop.is_mysterious else GOLD
        pygame.draw.rect(self.screen, title_color, panel_rect, 3)
        
        title = FONT_LARGE.render(shop_title, True, title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 70))
        self.screen.blit(title, title_rect)
        
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        self.screen.blit(gold_text, (SCREEN_WIDTH // 2 + 400, 70))
        
        if self.shop.discount < 1.0:
            discount_text = FONT_NORMAL.render(f'🎉 折扣: {int(self.shop.discount * 100)}%!', True, (255, 100, 100))
            self.screen.blit(discount_text, (SCREEN_WIDTH // 2 - 480, 70))
        
        tab_y = 105
        tab_width = 150
        tab_names = ['购买', '出售', '刷新', '赌装备', '砍价']
        for i, name in enumerate(tab_names):
            tab_rect = pygame.Rect(panel_rect.x + 20 + i * tab_width, tab_y, tab_width - 5, 35)
            if self.shop_tab == i:
                pygame.draw.rect(self.screen, (60, 80, 120), tab_rect)
                tab_color = YELLOW
            else:
                pygame.draw.rect(self.screen, (40, 40, 60), tab_rect)
                tab_color = WHITE
            pygame.draw.rect(self.screen, (80, 80, 100), tab_rect, 2)
            tab_text = FONT_NORMAL.render(name, True, tab_color)
            tab_text_rect = tab_text.get_rect(center=tab_rect.center)
            self.screen.blit(tab_text, tab_text_rect)
        
        items_rect = pygame.Rect(panel_rect.x + 20, 150, 960, 460)
        pygame.draw.rect(self.screen, (25, 25, 35), items_rect)
        pygame.draw.rect(self.screen, (60, 60, 80), items_rect, 2)
        
        if self.shop_tab in [0, 1]:
            self.shop_mode = 'buy' if self.shop_tab == 0 else 'sell'
            items = self.shop.inventory if self.shop_mode == 'buy' else self.player.inventory
            
            y = 160
            for i, item in enumerate(items[:14]):
                if i == self.shop_selection:
                    bg_color = (60, 70, 90)
                    text_color = YELLOW
                else:
                    bg_color = (35, 35, 50)
                    text_color = WHITE
                
                item_bg = pygame.Rect(items_rect.x + 10, y, 940, 28)
                pygame.draw.rect(self.screen, bg_color, item_bg)
                
                price = self.shop.get_item_price(item) if self.shop_mode == 'buy' else max(1, item.value // 2)
                
                quality_color = QUALITY_COLORS.get(item.quality, WHITE) if hasattr(item, 'quality') else WHITE
                item_text = FONT_NORMAL.render(f'{i + 1}. {item.name}', True, quality_color)
                price_text = FONT_NORMAL.render(f'{price} 金币', True, text_color)
                
                self.screen.blit(item_text, (items_rect.x + 20, y + 3))
                self.screen.blit(price_text, (items_rect.x + 850, y + 3))
                y += 30
        
        elif self.shop_tab == 2:
            refresh_cost = self.shop.get_refresh_cost()
            info_text = FONT_NORMAL.render(f'当前刷新费用: {refresh_cost} 金币', True, WHITE)
            info_rect = info_text.get_rect(center=(items_rect.centerx, items_rect.y + 50))
            self.screen.blit(info_text, info_rect)
            
            count_text = FONT_NORMAL.render(f'已刷新次数: {self.shop.refresh_count}', True, GRAY)
            count_rect = count_text.get_rect(center=(items_rect.centerx, items_rect.y + 90))
            self.screen.blit(count_text, count_rect)
            
            hint_text = FONT_NORMAL.render('按回车键刷新商品', True, YELLOW)
            hint_rect = hint_text.get_rect(center=(items_rect.centerx, items_rect.y + 150))
            self.screen.blit(hint_text, hint_rect)
            
            hint2_text = FONT_NORMAL.render('楼层越高，刷新出高品质物品概率越高！', True, GRAY)
            hint2_rect = hint2_text.get_rect(center=(items_rect.centerx, items_rect.y + 190))
            self.screen.blit(hint2_text, hint2_rect)
        
        elif self.shop_tab == 3:
            gamble_options = [
                ('普通赌注 (50金币)', 'common', 50),
                ('稀有赌注 (150金币)', 'uncommon', 150),
                ('史诗赌注 (400金币)', 'rare', 400),
                ('传说赌注 (1000金币)', 'epic', 1000)
            ]
            
            y = items_rect.y + 30
            for i, (name, quality, price) in enumerate(gamble_options):
                gamble_rect = pygame.Rect(items_rect.x + 50, y, 860, 50)
                if self.gamble_selection == i:
                    pygame.draw.rect(self.screen, (80, 60, 100), gamble_rect)
                    border_color = YELLOW
                else:
                    pygame.draw.rect(self.screen, (40, 40, 60), gamble_rect)
                    border_color = (80, 80, 100)
                pygame.draw.rect(self.screen, border_color, gamble_rect, 2)
                
                quality_color = QUALITY_COLORS.get(quality, WHITE)
                gamble_text = FONT_NORMAL.render(name, True, quality_color)
                gamble_rect_text = gamble_text.get_rect(center=gamble_rect.center)
                self.screen.blit(gamble_text, gamble_rect_text)
                y += 65
            
            hint_text = FONT_NORMAL.render('按回车键赌装备！有几率获得更高品质装备！', True, YELLOW)
            hint_rect = hint_text.get_rect(center=(items_rect.centerx, items_rect.y + 320))
            self.screen.blit(hint_text, hint_rect)
        
        elif self.shop_tab == 4:
            attempts_text = FONT_NORMAL.render(f'剩余砍价次数: {self.shop.max_bargain_attempts - self.shop.bargain_attempts}', True, WHITE)
            attempts_rect = attempts_text.get_rect(center=(items_rect.centerx, items_rect.y + 50))
            self.screen.blit(attempts_text, attempts_rect)
            
            if self.shop.inventory and 0 <= self.shop_selection < len(self.shop.inventory):
                item = self.shop.inventory[self.shop_selection]
                current_price = self.shop.get_item_price(item)
                
                item_text = FONT_NORMAL.render(f'选中物品: {item.name}', True, YELLOW)
                item_rect = item_text.get_rect(center=(items_rect.centerx, items_rect.y + 100))
                self.screen.blit(item_text, item_rect)
                
                price_text = FONT_NORMAL.render(f'当前价格: {current_price} 金币', True, GOLD)
                price_rect = price_text.get_rect(center=(items_rect.centerx, items_rect.y + 140))
                self.screen.blit(price_text, price_rect)
                
                hint_text = FONT_NORMAL.render('按回车键尝试砍价！成功降价，失败涨价！', True, WHITE)
                hint_rect = hint_text.get_rect(center=(items_rect.centerx, items_rect.y + 200))
                self.screen.blit(hint_text, hint_rect)
            else:
                hint_text = FONT_NORMAL.render('请先在购买标签页选择要砍价的物品', True, GRAY)
                hint_rect = hint_text.get_rect(center=(items_rect.centerx, items_rect.y + 150))
                self.screen.blit(hint_text, hint_rect)
        
        exit_btn_rect = pygame.Rect(panel_rect.x + panel_rect.width - 220, panel_rect.y + panel_rect.height - 55, 200, 45)
        pygame.draw.rect(self.screen, (100, 40, 40), exit_btn_rect)
        exit_text = FONT_NORMAL.render('离开商店', True, WHITE)
        exit_text_rect = exit_text.get_rect(center=exit_btn_rect.center)
        self.screen.blit(exit_text, exit_text_rect)
        self.shop_exit_btn = exit_btn_rect
        
        help_text = FONT_SMALL.render('← →切换标签 | ↑↓选择 | 回车确认 | ESC关闭', True, GRAY)
        help_rect = help_text.get_rect(center=(panel_rect.centerx, panel_rect.y + panel_rect.height - 30))
        self.screen.blit(help_text, help_rect)
    
    def render_synthesis(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 500, 50, 1000, 650)
        pygame.draw.rect(self.screen, (25, 25, 38), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        title = FONT_LARGE.render('⚗️ 装备合成', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 85))
        self.screen.blit(title, title_rect)
        
        gold_text = FONT_NORMAL.render(f'💰 {self.player.gold}', True, GOLD)
        self.screen.blit(gold_text, (SCREEN_WIDTH // 2 + 400, 85))
        
        formula_text = FONT_NORMAL.render('合成公式: 3件同品质 → 1件更高品质', True, CYAN)
        formula_rect = formula_text.get_rect(center=(SCREEN_WIDTH // 2, 125))
        self.screen.blit(formula_text, formula_rect)
        
        quality_options = ['common', 'uncommon', 'rare', 'epic', 'legendary']
        quality_names = ['白装 → 蓝装', '蓝装 → 紫装', '紫装 → 橙装', '橙装 → 金装', '金装 → 红装']
        
        for i, (q, name) in enumerate(zip(quality_options, quality_names)):
            q_rect = pygame.Rect(panel_rect.x + 50 + i * 180, 150, 170, 40)
            if self.synthesis_quality == q:
                pygame.draw.rect(self.screen, (60, 70, 100), q_rect)
                border_color = YELLOW
            else:
                pygame.draw.rect(self.screen, (35, 35, 50), q_rect)
                border_color = (70, 70, 90)
            pygame.draw.rect(self.screen, border_color, q_rect, 2)
            
            q_color = QUALITY_COLORS.get(q, WHITE)
            q_text = FONT_SMALL.render(name, True, q_color)
            q_text_rect = q_text.get_rect(center=q_rect.center)
            self.screen.blit(q_text, q_text_rect)
        
        equip_by_quality = self.synthesis.get_synthesizeable_equipment(self.player.inventory)
        count = len(equip_by_quality.get(self.synthesis_quality, []))
        
        count_text = FONT_NORMAL.render(f'当前可合成材料: {count} 件 (需要3件)', True, WHITE)
        count_rect = count_text.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self.screen.blit(count_text, count_rect)
        
        items_rect = pygame.Rect(panel_rect.x + 20, 230, 450, 350)
        pygame.draw.rect(self.screen, (20, 20, 30), items_rect)
        pygame.draw.rect(self.screen, (70, 70, 90), items_rect, 2)
        
        items_title = FONT_NORMAL.render('可合成材料', True, GOLD)
        self.screen.blit(items_title, (items_rect.x + 15, items_rect.y + 10))
        
        materials = equip_by_quality.get(self.synthesis_quality, [])
        y = items_rect.y + 40
        for i, item in enumerate(materials[:12]):
            if i == self.synthesis_selection:
                bg_color = (50, 50, 70)
            else:
                bg_color = (30, 30, 45)
            
            item_bg = pygame.Rect(items_rect.x + 8, y, 434, 24)
            pygame.draw.rect(self.screen, bg_color, item_bg)
            
            quality_color = QUALITY_COLORS.get(item.quality, WHITE)
            item_text = FONT_SMALL.render(item.name, True, quality_color)
            self.screen.blit(item_text, (items_rect.x + 15, y + 3))
            y += 26
        
        history_rect = pygame.Rect(panel_rect.x + 490, 230, 490, 350)
        pygame.draw.rect(self.screen, (20, 20, 30), history_rect)
        pygame.draw.rect(self.screen, (70, 70, 90), history_rect, 2)
        
        history_title = FONT_NORMAL.render('合成记录', True, GOLD)
        self.screen.blit(history_title, (history_rect.x + 15, history_rect.y + 10))
        
        history = self.synthesis.get_synthesis_history()
        y = history_rect.y + 40
        for record in history[-12:]:
            record_text = FONT_SMALL.render(f"{record['result']}", True, (200, 200, 200))
            self.screen.blit(record_text, (history_rect.x + 15, y))
            y += 26
        
        synthesize_btn = pygame.Rect(panel_rect.x + 20, panel_rect.y + panel_rect.height - 60, 200, 45)
        bulk_btn = pygame.Rect(panel_rect.x + 240, panel_rect.y + panel_rect.height - 60, 200, 45)
        exit_btn = pygame.Rect(panel_rect.x + panel_rect.width - 220, panel_rect.y + panel_rect.height - 60, 200, 45)
        
        if count >= 3:
            pygame.draw.rect(self.screen, (40, 100, 60), synthesize_btn)
            synth_color = WHITE
        else:
            pygame.draw.rect(self.screen, (60, 60, 60), synthesize_btn)
            synth_color = GRAY
        pygame.draw.rect(self.screen, (60, 100, 140), bulk_btn)
        pygame.draw.rect(self.screen, (100, 40, 40), exit_btn)
        
        synth_text = FONT_NORMAL.render('合成', True, synth_color)
        bulk_text = FONT_NORMAL.render('批量合成', True, WHITE)
        exit_text = FONT_NORMAL.render('关闭', True, WHITE)
        
        self.screen.blit(synth_text, synth_text.get_rect(center=synthesize_btn.center))
        self.screen.blit(bulk_text, bulk_text.get_rect(center=bulk_btn.center))
        self.screen.blit(exit_text, exit_text.get_rect(center=exit_btn.center))
        
        self.synth_btn = synthesize_btn
        self.bulk_synth_btn = bulk_btn
        self.synth_exit_btn = exit_btn
        
        help_text = FONT_SMALL.render('← →选择品质 | ↑↓选择物品 | 回车:合成 | B:批量 | ESC:关闭', True, GRAY)
        help_rect = help_text.get_rect(center=(panel_rect.centerx, panel_rect.y + panel_rect.height - 30))
        self.screen.blit(help_text, help_rect)
    
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
        if self.floor >= MAX_FLOOR:
            self.show_ending()
        else:
            self.state = GameState.VICTORY
            score = self.player.level * 100 + self.floor * 1000
            self.save_manager.save_score(self.player.name, score, self.floor)
            self.save_manager.delete_save()
    
    def show_ending(self):
        if self.is_fighting_final_boss:
            self.behavior_tracker.final_boss_no_damage = (self.final_boss_damage_taken == 0)
        
        ending_type = self.ending_system.determine_ending(
            self.behavior_tracker, 
            self.quest_manager, 
            self.floor
        )
        
        self.current_ending = ending_type
        self.ending_data = {
            'floor': self.floor,
            'monsters_killed': self.behavior_tracker.monsters_killed,
            'quests_completed': self.quest_manager.completed_quests,
            'play_time': self.behavior_tracker.play_time
        }
        
        self.state = GameState.ENDING
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
                elif self.state == GameState.MODE_SELECT:
                    self.handle_mode_select_input(event)
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
                elif self.state == GameState.SYNTHESIS:
                    self.handle_synthesis_input(event)
                elif self.state == GameState.QUEST_PANEL:
                    self.handle_quest_panel_input(event)
                elif self.state == GameState.NPC_INTERACT:
                    self.handle_npc_interact_input(event)
                elif self.state == GameState.ENDING:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                        self.current_ending = None
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
                self.state = GameState.MODE_SELECT
                self.menu_selection = 0
            elif self.menu_selection == 1:
                if self.save_manager.has_save():
                    self.load_saved_game()
                else:
                    self.add_message('没有找到存档！')
            elif self.menu_selection == 2:
                self.state = GameState.LEADERBOARD
            elif self.menu_selection == 3:
                self.running = False
        elif event.key == pygame.K_ESCAPE:
            self.running = False
    
    def handle_mode_select_input(self, event):
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.menu_selection = (self.menu_selection - 1) % 2
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.menu_selection = (self.menu_selection + 1) % 2
        elif event.key == pygame.K_RETURN:
            if self.menu_selection == 0:
                self.game_mode = 'single'
                self.state = GameState.CLASS_SELECT
                self.menu_selection = 0
            elif self.menu_selection == 1:
                self.game_mode = 'coop'
                self.state = GameState.CLASS_SELECT
                self.menu_selection = 0
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
            self.menu_selection = 0
    
    def handle_class_select_input(self, event):
        if event.key in [pygame.K_LEFT, pygame.K_a]:
            self.menu_selection = (self.menu_selection - 1) % 4
        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
            self.menu_selection = (self.menu_selection + 1) % 4
        elif event.key == pygame.K_RETURN:
            classes = list(CLASSES.keys())
            if self.game_mode == 'single':
                self.new_game(classes[self.menu_selection])
            else:
                if not hasattr(self, 'selected_class1') or self.selected_class1 is None:
                    self.selected_class1 = classes[self.menu_selection]
                    self.add_message(f'玩家1选择了{CLASSES[self.selected_class1]["name"]}')
                    self.menu_selection = (self.menu_selection + 1) % 4
                else:
                    self.new_game(self.selected_class1, classes[self.menu_selection])
                    self.selected_class1 = None
        elif event.key == pygame.K_ESCAPE:
            if hasattr(self, 'selected_class1') and self.selected_class1 is not None:
                self.selected_class1 = None
                self.add_message('已取消玩家1选择')
            else:
                self.state = GameState.MODE_SELECT
                self.menu_selection = 0
    
    def handle_game_input(self, event):
        allies = [self.player]
        if self.game_mode == 'coop' and self.player2:
            allies.append(self.player2)
        
        if self.player.is_alive():
            if event.key in [pygame.K_UP, pygame.K_w]:
                self.move_player(0, -1)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.move_player(0, 1)
            elif event.key in [pygame.K_LEFT, pygame.K_a]:
                self.move_player(-1, 0)
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                self.move_player(1, 0)
            elif event.key == pygame.K_q:
                if self.use_player_skill(self.player, 'basic', allies):
                    self.end_player_turn()
            elif event.key == pygame.K_r:
                if self.use_player_skill(self.player, 'ultimate', allies):
                    self.end_player_turn()
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
                self.handle_interaction()
            elif event.key in [pygame.K_i]:
                self.state = GameState.INVENTORY
                self.inventory_selection = 0
            elif event.key in [pygame.K_t]:
                self.state = GameState.TALENT
                self.talent_selection = 0
            elif event.key in [pygame.K_c]:
                self.state = GameState.SYNTHESIS
                self.synthesis_selection = 0
            elif event.key in [pygame.K_j]:
                self.state = GameState.QUEST_PANEL
                self.quest_selection = 0
            elif event.key == pygame.K_ESCAPE:
                self.state = GameState.PAUSED
                self.menu_selection = 0
        
        if self.game_mode == 'coop' and self.player2 and self.player2.is_alive():
            if event.key == pygame.K_KP8:
                self.move_player2(0, -1)
            elif event.key == pygame.K_KP5:
                self.move_player2(0, 1)
            elif event.key == pygame.K_KP4:
                self.move_player2(-1, 0)
            elif event.key == pygame.K_KP6:
                self.move_player2(1, 0)
            elif event.key == pygame.K_KP7:
                if self.use_player_skill(self.player2, 'basic', allies):
                    self.end_player_turn()
            elif event.key == pygame.K_KP9:
                if self.use_player_skill(self.player2, 'ultimate', allies):
                    self.end_player_turn()
            elif event.key == pygame.K_KP_ENTER:
                for monster in self.monsters:
                    if monster.get_distance_to(self.player2) <= 1.5:
                        attack_count = self.player2.get_total_attack_count()
                        for _ in range(attack_count):
                            if monster.is_alive():
                                self.combat.attack(self.player2, monster)
                        if not monster.is_alive():
                            self.monsters.remove(monster)
                        self.end_player_turn()
                        break
    
    def handle_interaction(self):
        for npc in self.npcs:
            if npc.get_distance_to(self.player) <= 1.5:
                delivery_completed, quest = self.quest_manager.check_delivery_quests(npc, self.player)
                if delivery_completed and quest:
                    self.add_message(f'{npc.name}: 谢谢你送来的信件！')
                    success, message = self.quest_manager.complete_quest(quest, self.player)
                    if success:
                        self.add_message(f'完成任务：{quest.name}！获得奖励！')
                    return
                
                self.current_npc = npc
                self.state = GameState.NPC_INTERACT
                self.quest_selection = 0
                self.add_message(f'{npc.name}: {npc.dialogue}')
                return
        
        self.handle_special_room_interaction()
    
    def handle_special_room_interaction(self):
        room = self.game_map.get_room_at(self.player.x, self.player.y)
        if not room:
            self.add_message('这里没有可交互的对象！')
            return
        
        room_id = (room.x1, room.y1, room.x2, room.y2)
        room_type = room.room_type
        interaction_happened = False
        
        special_room_types = ['altar', 'blacksmith', 'library', 'event', 'rest']
        
        if room_type in special_room_types and room_id in self.used_rooms:
            self.add_message('这个房间的效果已经使用过了！')
            return
        
        if room_type == 'altar':
            if self.player.hp > 10:
                sacrifice = int(self.player.get_total_max_hp() * 0.2)
                self.player.hp -= sacrifice
                self.player.str += 3
                self.player.defense += 2
                self.add_message(f'献祭了{sacrifice}点生命，获得力量提升！')
                interaction_happened = True
            else:
                self.add_message('生命值不足，无法献祭！')
        
        elif room_type == 'blacksmith':
            if self.player.gold >= 50:
                self.player.gold -= 50
                self.player.base_attack_count += 1
                self.add_message('花费50金币，铁匠强化了你的攻击！')
                interaction_happened = True
            else:
                self.add_message('金币不足，无法强化！')
        
        elif room_type == 'library':
            self.player.int += 5
            max_mp_boost = 20
            self.player.max_mp += max_mp_boost
            self.player.mp = self.player.get_total_max_mp()
            self.add_message(f'阅读古老典籍，智力+5，最大魔力+{max_mp_boost}！')
            interaction_happened = True
        
        elif room_type == 'event':
            event_roll = random.random()
            if event_roll < 0.3:
                heal_amount = int(self.player.get_total_max_hp() * 0.5)
                actual_heal = self.player.heal(heal_amount)
                self.add_message(f'神秘泉水恢复了{actual_heal}点生命！')
            elif event_roll < 0.6:
                gold = random.randint(30, 80)
                self.player.gold += gold
                self.add_message(f'发现了一个藏宝箱，获得{gold}金币！')
            elif event_roll < 0.8:
                self.player.add_status('poison', 5, 3)
                self.add_message('触发了古老诅咒，中毒了！')
            else:
                self.player.str += 2
                self.player.dex += 2
                self.add_message('获得了神秘的祝福！力量+2，敏捷+2！')
            interaction_happened = True
        
        elif room_type == 'rest':
            heal_amount = int(self.player.get_total_max_hp() * 0.3)
            mp_amount = int(self.player.get_total_max_mp() * 0.3)
            actual_heal = self.player.heal(heal_amount)
            actual_mp = self.player.restore_mp(mp_amount)
            self.add_message(f'在休息点恢复了{actual_heal}生命和{actual_mp}魔力！')
            interaction_happened = True
        else:
            self.add_message('这个房间没有特殊功能。')
        
        if interaction_happened:
            if room_type in special_room_types:
                self.used_rooms.add(room_id)
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
        display_items = self.player.get_sorted_inventory()
        
        if not display_items:
            self.inventory_selection = 0
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.PLAYING
            return
        
        self.inventory_selection = max(0, min(self.inventory_selection, len(display_items) - 1))
        
        if event.key in [pygame.K_UP, pygame.K_w]:
            if self.inventory_selection > 0:
                self.inventory_selection -= 1
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            if self.inventory_selection < len(display_items) - 1:
                self.inventory_selection += 1
        elif event.key in [pygame.K_e]:
            if 0 <= self.inventory_selection < len(display_items):
                item = display_items[self.inventory_selection]
                if hasattr(item, 'slot'):
                    if self.player.equip_item(item):
                        self.add_message(f'✨ 装备了 {item.name}！')
                    else:
                        self.add_message(f'无法装备 {item.name}！')
                else:
                    self.add_message('这个物品无法装备！')
        elif event.key in [pygame.K_u]:
            if 0 <= self.inventory_selection < len(display_items):
                item = display_items[self.inventory_selection]
                if hasattr(item, 'slot'):
                    slot = item.slot
                    equipped_item = self.player.equipment.get(slot)
                    if equipped_item:
                        if len(self.player.inventory) < 50:
                            self.player.inventory.append(equipped_item)
                            self.player.equipment[slot] = None
                            self.add_message(f'📤 已脱下 {equipped_item.name}！')
                        else:
                            self.add_message('背包已满，无法脱下！')
                    else:
                        self.add_message(f'{SLOT_NAMES[slot]}部位没有装备！')
                else:
                    self.add_message('只能脱下装备！')
        elif event.key in [pygame.K_d]:
            if 0 <= self.inventory_selection < len(display_items):
                item = display_items[self.inventory_selection]
                if hasattr(item, 'item_type') and item.item_type == 'equipment':
                    gold = item.value
                    self.player.gold += gold
                    if item in self.player.inventory:
                        self.player.inventory.remove(item)
                    elif item in self.player.equipment.values():
                        for slot, equip in self.player.equipment.items():
                            if equip == item:
                                self.player.equipment[slot] = None
                                break
                    self.add_message(f'� 分解了 {item.name}，获得 {gold} 金币！')
                    self.inventory_selection = min(self.inventory_selection, len(self.player.get_sorted_inventory()) - 1)
                else:
                    self.add_message('只能分解装备！')
        elif event.key in [pygame.K_r]:
            total_gold = 0
            quality_order = {'common': 1, 'uncommon': 2, 'rare': 3, 'epic': 4, 'legendary': 5}
            
            to_decompose = []
            for item in self.player.inventory:
                if (hasattr(item, 'item_type') and item.item_type == 'equipment' and 
                    quality_order.get(item.quality, 1) <= 1):
                    to_decompose.append(item)
            
            for item in to_decompose:
                total_gold += item.value
                self.player.inventory.remove(item)
            
            if total_gold > 0:
                self.player.gold += total_gold
                self.add_message(f'� 批量分解完成，获得 {total_gold} 金币！')
            else:
                self.add_message('没有可分解的白装！')
            self.inventory_selection = 0
        elif event.key in [pygame.K_SPACE]:
            if 0 <= self.inventory_selection < len(display_items):
                item = display_items[self.inventory_selection]
                if hasattr(item, 'use'):
                    item_type = getattr(item, 'item_type', None)
                    if item_type in ['revive_scroll', 'teleport_anchor', 'summon_card', 'map_reveal']:
                        msg = item.use(self.player, self)
                    else:
                        msg = item.use(self.player)
                    if msg:
                        self.add_message(msg)
                        if '无法' not in msg and '没有' not in msg and '上限' not in msg:
                            self.player.remove_item(item)
                            self.inventory_selection = min(self.inventory_selection, len(display_items) - 2)
                    else:
                        self.add_message('这个物品无法使用！')
                else:
                    self.add_message('这个物品无法使用！')
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def handle_shop_input(self, event):
        if event.key in [pygame.K_LEFT, pygame.K_a]:
            self.shop_tab = max(0, self.shop_tab - 1)
            self.shop_selection = 0
        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
            self.shop_tab = min(4, self.shop_tab + 1)
            self.shop_selection = 0
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
        
        if self.shop_tab in [0, 1]:
            items = self.shop.inventory if self.shop_tab == 0 else self.player.inventory
            if items:
                self.shop_selection = max(0, min(self.shop_selection, len(items) - 1))
                
                if event.key in [pygame.K_UP, pygame.K_w]:
                    if self.shop_selection > 0:
                        self.shop_selection -= 1
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    if self.shop_selection < len(items) - 1:
                        self.shop_selection += 1
                elif event.key == pygame.K_RETURN:
                    if items and 0 <= self.shop_selection < len(items):
                        item = items[self.shop_selection]
                        if self.shop_tab == 0:
                            price = self.shop.get_item_price(item)
                            if self.player.gold >= price:
                                if self.player.add_item(item):
                                    self.player.gold -= price
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
        
        elif self.shop_tab == 2:
            if event.key == pygame.K_RETURN:
                success, msg = self.shop.manual_refresh(self.player, self.game_mode, self.floor)
                self.add_message(msg)
        
        elif self.shop_tab == 3:
            gamble_qualities = ['common', 'uncommon', 'rare', 'epic']
            if event.key in [pygame.K_UP, pygame.K_w]:
                if self.gamble_selection > 0:
                    self.gamble_selection -= 1
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                if self.gamble_selection < 3:
                    self.gamble_selection += 1
            elif event.key == pygame.K_RETURN:
                quality = gamble_qualities[self.gamble_selection]
                success, msg, equip = self.shop.gamble_equipment(self.player, quality, self.floor)
                self.add_message(msg)
        
        elif self.shop_tab == 4:
            if event.key == pygame.K_RETURN:
                if self.shop.inventory and 0 <= self.shop_selection < len(self.shop.inventory):
                    item = self.shop.inventory[self.shop_selection]
                    success, msg = self.shop.bargain(self.player, item)
                    self.add_message(msg)
                else:
                    self.add_message('请先选择要砍价的物品！')
    
    def handle_synthesis_input(self, event):
        quality_options = ['common', 'uncommon', 'rare', 'epic', 'legendary']
        
        if event.key in [pygame.K_LEFT, pygame.K_a]:
            idx = quality_options.index(self.synthesis_quality)
            if idx > 0:
                self.synthesis_quality = quality_options[idx - 1]
                self.synthesis_selection = 0
            return
        
        if event.key in [pygame.K_RIGHT, pygame.K_d]:
            idx = quality_options.index(self.synthesis_quality)
            if idx < len(quality_options) - 1:
                self.synthesis_quality = quality_options[idx + 1]
                self.synthesis_selection = 0
            return
        
        equip_by_quality = self.synthesis.get_synthesizeable_equipment(self.player.inventory)
        materials = equip_by_quality.get(self.synthesis_quality, [])
        
        if materials:
            self.synthesis_selection = max(0, min(self.synthesis_selection, len(materials) - 1))
            if event.key in [pygame.K_UP, pygame.K_w]:
                if self.synthesis_selection > 0:
                    self.synthesis_selection -= 1
                return
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                if self.synthesis_selection < len(materials) - 1:
                    self.synthesis_selection += 1
                return
        
        if event.key == pygame.K_RETURN:
            if len(materials) >= 3:
                success, msg, new_equip = self.synthesis.synthesize(self.synthesis_quality, self.player.inventory, self.floor)
                if success and new_equip:
                    self.player.inventory.append(new_equip)
                self.add_message(msg)
            else:
                self.add_message('材料不足！需要3件同品质装备')
            return
        
        if event.key == pygame.K_b:
            success, msg, results = self.synthesis.bulk_synthesize(self.synthesis_quality, self.player.inventory, self.floor)
            self.add_message(msg)
            return
        
        if event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
            return
    
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
    
    def handle_quest_panel_input(self, event):
        quests = self.quest_manager.get_active_quests()
        max_quests = max(1, len(quests))
        
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.quest_selection = (self.quest_selection - 1) % max_quests
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.quest_selection = (self.quest_selection + 1) % max_quests
        elif event.key == pygame.K_a:
            if quests and self.quest_selection < len(quests):
                quest = quests[self.quest_selection]
                if quest.quest_type == 'collect' and quest.can_complete():
                    self.quest_manager.complete_quest(quest, self.player)
                    self.add_message(f'完成任务：{quest.name}！')
                    for reward in quest.rewards:
                        if isinstance(reward, str) and reward.startswith('gold:'):
                            gold = int(reward.split(':')[1])
                            self.player.gold += gold
                        elif isinstance(reward, str) and reward.startswith('talent:'):
                            points = int(reward.split(':')[1])
                            self.player.talent_points += points
                        elif hasattr(reward, 'name'):
                            self.player.add_item(reward)
        elif event.key == pygame.K_d:
            if quests and self.quest_selection < len(quests):
                quest = quests[self.quest_selection]
                self.quest_manager.abandon_quest(quest)
                self.add_message(f'已放弃任务：{quest.name}')
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def handle_npc_interact_input(self, event):
        if not self.current_npc:
            self.state = GameState.PLAYING
            return
        
        available_quests = self.current_npc.quests
        max_options = len(available_quests) + 1
        
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.quest_selection = (self.quest_selection - 1) % max_options
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.quest_selection = (self.quest_selection + 1) % max_options
        elif event.key == pygame.K_RETURN:
            if self.quest_selection == len(available_quests):
                self.state = GameState.PLAYING
                self.current_npc = None
            else:
                quest = available_quests[self.quest_selection]
                success, message = self.quest_manager.accept_quest(quest)
                if success:
                    self.add_message(f'接受任务：{quest.name}')
                    available_quests.remove(quest)
                    
                    if quest.quest_type == 'delivery':
                        target_npc = quest.target_data.get('target_npc', '')
                        letter = DeliveryLetter(0, 0, quest.floor, target_npc)
                        self.player.add_item(letter)
                        self.add_message('获得了重要信件！')
                        
                        for npc in self.npcs:
                            if npc.name == target_npc:
                                quest.set_target_position(npc.x, npc.y)
                                break
                    
                    elif quest.quest_type == 'collect':
                        collect_items = quest.spawn_collect_items(self.game_map, self.game_map.rooms)
                        for item in collect_items:
                            self.items.append(item)
                        self.add_message(f'地图上出现了 {len(collect_items)} 个任务物品！')
                else:
                    self.add_message(message)
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
            self.current_npc = None
    
    def render_quest_panel(self):
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 450, 80, 900, 600)
        pygame.draw.rect(self.screen, (20, 20, 35), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        title = FONT_LARGE.render('任务面板', True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 110))
        self.screen.blit(title, title_rect)
        
        quests = self.quest_manager.get_active_quests()
        completed = self.quest_manager.completed_quests
        
        stats_text = FONT_SMALL.render(f'已完成: {completed} | 进行中: {len(quests)}/5', True, LIGHT_GRAY)
        self.screen.blit(stats_text, (SCREEN_WIDTH // 2 - 430, 140))
        
        if not quests:
            no_quest_text = FONT_NORMAL.render('暂无进行中的任务', True, LIGHT_GRAY)
            no_quest_rect = no_quest_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
            self.screen.blit(no_quest_text, no_quest_rect)
        else:
            list_rect = pygame.Rect(SCREEN_WIDTH // 2 - 430, 160, 860, 400)
            pygame.draw.rect(self.screen, (30, 30, 50), list_rect)
            
            for i, quest in enumerate(quests[:10]):
                y = 170 + i * 38
                if i == self.quest_selection:
                    pygame.draw.rect(self.screen, (50, 50, 80), (SCREEN_WIDTH // 2 - 425, y, 850, 35))
                
                type_colors = {'delivery': CYAN, 'hunt': RED, 'collect': GREEN}
                type_names = {'delivery': '送信', 'hunt': '猎杀', 'collect': '收集'}
                type_color = type_colors.get(quest.quest_type, WHITE)
                
                type_text = FONT_SMALL.render(f'[{type_names.get(quest.quest_type, "任务")}]', True, type_color)
                self.screen.blit(type_text, (SCREEN_WIDTH // 2 - 420, y + 8))
                
                name_text = FONT_SMALL.render(quest.name, True, WHITE)
                self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 360, y + 8))
                
                progress = quest.get_progress_text()
                progress_text = FONT_SMALL.render(progress, True, YELLOW)
                self.screen.blit(progress_text, (SCREEN_WIDTH // 2 + 100, y + 8))
                
                status_color = GREEN if quest.can_complete() else LIGHT_GRAY
                status = '可提交(A)' if quest.can_complete() else '进行中'
                status_text = FONT_SMALL.render(status, True, status_color)
                self.screen.blit(status_text, (SCREEN_WIDTH // 2 + 300, y + 8))
            
            if quests and self.quest_selection < len(quests):
                quest = quests[self.quest_selection]
                desc_rect = pygame.Rect(SCREEN_WIDTH // 2 - 430, 570, 860, 90)
                pygame.draw.rect(self.screen, (30, 30, 50), desc_rect)
                pygame.draw.rect(self.screen, (100, 100, 150), desc_rect, 1)
                
                desc_text = FONT_SMALL.render(quest.description, True, LIGHT_GRAY)
                self.screen.blit(desc_text, (SCREEN_WIDTH // 2 - 420, 580))
                
                reward_text = FONT_SMALL.render(f'奖励: {quest.get_reward_text()}', True, GOLD)
                self.screen.blit(reward_text, (SCREEN_WIDTH // 2 - 420, 620))
        
        hint_text = FONT_SMALL.render('W/S:选择 | A:提交 | D:放弃 | ESC:返回', True, LIGHT_GRAY)
        self.screen.blit(hint_text, (SCREEN_WIDTH // 2 - 200, 680))
    
    def render_npc_interact(self):
        if not self.current_npc:
            return
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 400, 120, 800, 500)
        pygame.draw.rect(self.screen, (25, 25, 45), panel_rect)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3)
        
        name_bg = pygame.Rect(SCREEN_WIDTH // 2 - 400, 120, 800, 60)
        pygame.draw.rect(self.screen, (40, 40, 70), name_bg)
        npc_name = FONT_LARGE.render(self.current_npc.name, True, YELLOW)
        name_rect = npc_name.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(npc_name, name_rect)
        
        dialogue_rect = pygame.Rect(SCREEN_WIDTH // 2 - 380, 190, 760, 80)
        pygame.draw.rect(self.screen, (35, 35, 55), dialogue_rect)
        dialogue_text = FONT_SMALL.render(f'"{self.current_npc.dialogue}"', True, LIGHT_GRAY)
        dialogue_rect_text = dialogue_text.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(dialogue_text, dialogue_rect_text)
        
        quests_title = FONT_NORMAL.render('可接任务:', True, GOLD)
        self.screen.blit(quests_title, (SCREEN_WIDTH // 2 - 380, 290))
        
        available_quests = self.current_npc.quests
        total_options = len(available_quests) + 1
        
        for i, quest in enumerate(available_quests):
            y = 330 + i * 50
            if i == self.quest_selection:
                pygame.draw.rect(self.screen, (60, 60, 100), (SCREEN_WIDTH // 2 - 380, y, 760, 45))
            
            type_colors = {'delivery': CYAN, 'hunt': RED, 'collect': GREEN}
            type_names = {'delivery': '送信', 'hunt': '猎杀', 'collect': '收集'}
            type_color = type_colors.get(quest.quest_type, WHITE)
            
            type_text = FONT_SMALL.render(f'[{type_names.get(quest.quest_type, "任务")}]', True, type_color)
            self.screen.blit(type_text, (SCREEN_WIDTH // 2 - 370, y + 12))
            
            name_text = FONT_NORMAL.render(quest.name, True, WHITE)
            self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 300, y + 10))
            
            reward_text = FONT_SMALL.render(f'奖励: {quest.get_reward_text()}', True, GOLD)
            self.screen.blit(reward_text, (SCREEN_WIDTH // 2 + 100, y + 15))
        
        exit_y = 330 + len(available_quests) * 50
        if len(available_quests) == self.quest_selection:
            pygame.draw.rect(self.screen, (60, 60, 100), (SCREEN_WIDTH // 2 - 380, exit_y, 760, 45))
        
        exit_text = FONT_NORMAL.render('离开', True, LIGHT_GRAY)
        self.screen.blit(exit_text, (SCREEN_WIDTH // 2 - 370, exit_y + 10))
        
        hint_text = FONT_SMALL.render('W/S:选择 | 回车:确认 | ESC:离开', True, LIGHT_GRAY)
        self.screen.blit(hint_text, (SCREEN_WIDTH // 2 - 180, 580))
    
    def render_ending(self):
        if not self.current_ending or not self.ending_data:
            return
        
        ending_config = ENDING_TYPES.get(self.current_ending, ENDING_TYPES['normal'])
        
        bg_color = ending_config['bg_color']
        self.screen.fill(bg_color)
        
        title = FONT_LARGE.render(ending_config['title'], True, ending_config['title_color'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        subtitle = FONT_NORMAL.render(ending_config['subtitle'], True, ending_config['text_color'])
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        story_rect = pygame.Rect(SCREEN_WIDTH // 2 - 400, 280, 800, 250)
        pygame.draw.rect(self.screen, (30, 30, 50, 200), story_rect)
        pygame.draw.rect(self.screen, ending_config['title_color'], story_rect, 2)
        
        story_lines = [ending_config['story'][i:i+40] for i in range(0, len(ending_config['story']), 40)]
        for i, line in enumerate(story_lines[:8]):
            line_text = FONT_SMALL.render(line, True, ending_config['text_color'])
            self.screen.blit(line_text, (SCREEN_WIDTH // 2 - 380, 300 + i * 28))
        
        stats_y = 550
        stats = [
            f'通关楼层: {self.ending_data.get("floor", 1)}',
            f'击败怪物: {self.ending_data.get("monsters_killed", 0)}',
            f'完成任务: {self.ending_data.get("quests_completed", 0)}',
            f'游戏时长: {self.ending_data.get("play_time", 0)}回合'
        ]
        for i, stat in enumerate(stats):
            stat_text = FONT_SMALL.render(stat, True, LIGHT_GRAY)
            self.screen.blit(stat_text, (SCREEN_WIDTH // 2 - 380 + i * 200, stats_y))
        
        prompt_text = FONT_NORMAL.render('按回车或ESC返回主菜单', True, LIGHT_GRAY)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 650))
        self.screen.blit(prompt_text, prompt_rect)
    
    def run(self):
        while self.running:
            self.handle_input()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
