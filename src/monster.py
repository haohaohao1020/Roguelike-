import random
import math
from .config import *
from .entity import Entity
from .items import create_random_equipment

class Monster(Entity):
    def __init__(self, x, y, name, monster_type='normal'):
        super().__init__(x, y, name, RED)
        self.monster_type = monster_type
        self.hp = 30
        self.max_hp = 30
        self.damage = 10
        self.defense = 5
        self.evasion = 5
        self.exp = 20
        self.gold = 10
        
        self.ai_type = 'passive'
        self.aggro_range = 5
        self.is_aggro = False
        self.frozen = 0
        self.stunned = 0
        
        self.status_effects = []
        self.blocks_movement = True
        self.attack_cooldown = 0
        
        self.dodge_trap = True
        
        self.summons = []
        self.summon_cooldown = 0
        self.master = None
        
        self.is_invisible = False
        self.invisible_cooldown = 0
        self.reveal_stun = 0
        
        self.revive_count = 0
        self.max_revive = 0
        self.is_down = False
        self.down_timer = 0
        
        self.knockback_skill_cooldown = 0
        
        self.floor = 1
    
    def add_status(self, status_type, duration, damage=0):
        for status in self.status_effects:
            if status['type'] == status_type:
                status['duration'] = max(status['duration'], duration)
                return
        
        self.status_effects.append({
            'type': status_type,
            'duration': duration,
            'damage': damage
        })
        
        if status_type in ['stunned', 'frozen']:
            if self.is_invisible:
                self.is_invisible = False
                self.reveal_stun = 2
    
    def has_status(self, status_type):
        return any(s['type'] == status_type for s in self.status_effects)
    
    def update_status_effects(self):
        for status in self.status_effects[:]:
            if status['damage'] > 0:
                self.hp -= status['damage']
            
            status['duration'] -= 1
            if status['duration'] <= 0:
                self.status_effects.remove(status)
        
        if self.has_status('frozen'):
            self.frozen = 3
        if self.has_status('stunned'):
            self.stunned = 2
    
    def take_damage(self, amount):
        super().take_damage(amount)
        actual = max(1, amount - self.defense // 2)
        
        if self.is_invisible:
            self.is_invisible = False
            self.reveal_stun = 2
        
        self.hp -= actual
        self.is_aggro = True
        return actual
    
    def is_alive(self):
        return self.hp > 0 or self.is_down
    
    def should_remove(self):
        return self.hp <= 0 and not self.is_down
    
    def get_total_defense(self):
        return self.defense
    
    def get_total_magic_defense(self):
        return self.defense // 2
    
    def get_total_physical_defense(self):
        return self.defense
    
    def get_lifesteal(self):
        return 0
    
    def get_manasteal(self):
        return 0
    
    def get_crit_chance(self):
        return 5
    
    def get_crit_damage(self):
        return 150
    
    def get_drop_quality(self):
        quality_weights = {
            1: [70, 25, 5, 0, 0],
            2: [60, 30, 10, 0, 0],
            3: [45, 35, 18, 2, 0],
            4: [30, 35, 30, 5, 0],
            5: [20, 30, 35, 13, 2],
            6: [15, 25, 35, 20, 5],
            7: [10, 20, 35, 25, 10],
            8: [5, 15, 30, 35, 15],
            9: [0, 10, 25, 40, 25],
            10: [0, 5, 20, 40, 35]
        }
        floor = min(self.floor, 10)
        weights = quality_weights.get(floor, [60, 25, 10, 4, 1])
        qualities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
        return random.choices(qualities, weights=weights, k=1)[0]
    
    def drop_loot(self):
        drops = []
        
        if self.monster_type == 'normal':
            if random.random() < 0.15:
                quality = self.get_drop_quality()
                equip = create_random_equipment(0, 0, self.floor)
                equip.quality = quality
                equip.generate_stats()
                equip.generate_sub_stats()
                equip.calculate_value()
                drops.append(equip)
        elif self.monster_type in ['elite', 'boss']:
            num_drops = 1 if self.monster_type == 'elite' else random.randint(2, 4)
            for _ in range(num_drops):
                quality = self.get_drop_quality()
                equip = create_random_equipment(0, 0, self.floor)
                equip.quality = quality
                equip.generate_stats()
                equip.generate_sub_stats()
                equip.calculate_value()
                drops.append(equip)
        
        return drops
    
    def find_path_around_traps(self, game_map, target_x, target_y, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        
        moves = []
        
        if abs(dx) > abs(dy):
            moves.append((1 if dx > 0 else -1, 0))
            if dy != 0:
                moves.append((0, 1 if dy > 0 else -1))
        else:
            moves.append((0, 1 if dy > 0 else -1))
            if dx != 0:
                moves.append((1 if dx > 0 else -1, 0))
        
        moves.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])
        
        safe_moves = []
        dangerous_moves = []
        
        for mdx, mdy in moves:
            new_x = self.x + mdx
            new_y = self.y + mdy
            
            if game_map.is_walkable(new_x, new_y) and not self.is_blocked(new_x, new_y, entities):
                terrain = game_map.terrain[new_x][new_y]
                if terrain in ['thorns', 'poison', 'lava'] and self.dodge_trap:
                    dangerous_moves.append((mdx, mdy))
                else:
                    safe_moves.append((mdx, mdy))
        
        if safe_moves:
            return safe_moves[0]
        elif dangerous_moves and not self.dodge_trap:
            return dangerous_moves[0]
        
        return None
    
    def update_ai(self, game_map, player, entities, all_players=None):
        if self.is_down:
            self.down_timer -= 1
            
            if self.has_status('stunned') or self.has_status('frozen'):
                self.is_down = False
                self.hp = 0
                return
            
            if self.down_timer <= 0:
                if self.revive_count < self.max_revive:
                    self.revive_count += 1
                    self.is_down = False
                    heal_percent = random.uniform(0.3, 0.5)
                    self.hp = int(self.max_hp * heal_percent)
                else:
                    self.hp = 0
            return
        
        if self.frozen > 0:
            self.frozen -= 1
            return
        if self.stunned > 0:
            self.stunned -= 1
            return
        if self.reveal_stun > 0:
            self.reveal_stun -= 1
            return
        
        if hasattr(self, 'update_special'):
            self.update_special(game_map, player, entities, all_players)
        
        if all_players:
            alive_players = [p for p in all_players if p.is_alive()]
            if alive_players:
                target_player = min(alive_players, key=lambda p: p.hp / p.get_total_max_hp())
            else:
                target_player = player
        else:
            target_player = player
        
        distance = self.get_distance_to(target_player)
        
        if self.is_invisible:
            if random.random() < 0.3:
                self.move_towards_target(game_map, target_player.x, target_player.y, entities)
            return
        
        aggro_multiplier = 1.5 if self.monster_type == 'boss' else 1.0
        actual_aggro_range = self.aggro_range * aggro_multiplier
        
        if distance <= actual_aggro_range:
            self.is_aggro = True
        
        if self.is_aggro:
            if self.hp < self.max_hp * 0.3 and random.random() < 0.2 and self.ai_type != 'aggressive':
                self.move_away(game_map, target_player, entities)
            else:
                moves = 2 if self.monster_type == 'boss' else 1
                for _ in range(moves):
                    if random.random() < 0.8:
                        self.move_towards_target(game_map, target_player.x, target_player.y, entities)
        
        elif self.ai_type == 'aggressive' and distance <= actual_aggro_range * 2:
            self.is_aggro = True
            self.move_towards_target(game_map, target_player.x, target_player.y, entities)
    
    def move_towards_target(self, game_map, target_x, target_y, entities):
        move = self.find_path_around_traps(game_map, target_x, target_y, entities)
        if move:
            dx, dy = move
            new_x = self.x + dx
            new_y = self.y + dy
            self.x = new_x
            self.y = new_y
    
    def move_towards(self, game_map, target, entities):
        self.move_towards_target(game_map, target.x, target.y, entities)
    
    def move_away(self, game_map, target, entities):
        dx = self.x - target.x
        dy = self.y - target.y
        
        if abs(dx) > abs(dy):
            dx = 1 if dx > 0 else -1
            dy = 0
        else:
            dx = 0
            dy = 1 if dy > 0 else -1
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        if game_map.is_walkable(new_x, new_y):
            if not self.is_blocked(new_x, new_y, entities):
                self.x = new_x
                self.y = new_y
    
    def is_blocked(self, x, y, entities):
        for entity in entities:
            if entity != self and entity.blocks_movement and entity.x == x and entity.y == y:
                return True
        return False

class SummonerMonster(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '召唤法师', 'normal')
        self.color = (150, 50, 150)
        self.hp = int(35 * (1 + floor * 0.2))
        self.max_hp = self.hp
        self.damage = int(8 * (1 + floor * 0.15))
        self.defense = 4
        self.evasion = 8
        self.exp = 35
        self.gold = 20
        self.ai_type = 'passive'
        self.aggro_range = 6
        self.summon_cooldown = 0
        self.summons = []
        self.floor = floor
    
    def update_special(self, game_map, player, entities, all_players=None):
        if self.summon_cooldown > 0:
            self.summon_cooldown -= 1
        else:
            if len(self.summons) < 4 and self.is_aggro:
                self.summon_cooldown = 5
                num_summon = random.randint(1, 2)
                for _ in range(num_summon):
                    summon_positions = [
                        (self.x + dx, self.y + dy)
                        for dx in [-1, 0, 1]
                        for dy in [-1, 0, 1]
                        if (dx != 0 or dy != 0)
                        and game_map.is_walkable(self.x + dx, self.y + dy)
                    ]
                    random.shuffle(summon_positions)
                    if summon_positions:
                        sx, sy = summon_positions[0]
                        summon = SummonMinion(sx, sy, self, self.floor)
                        self.summons.append(summon)
    
    def cleanup_summons(self):
        self.summons = []

class SummonMinion(Monster):
    def __init__(self, x, y, master, floor=1):
        super().__init__(x, y, '召唤小弟', 'normal')
        self.color = (100, 100, 150)
        self.hp = int(15 * (1 + floor * 0.15))
        self.max_hp = self.hp
        self.damage = int(5 * (1 + floor * 0.1))
        self.defense = 2
        self.evasion = 5
        self.exp = 5
        self.gold = 2
        self.ai_type = 'aggressive'
        self.aggro_range = 8
        self.master = master
        self.is_aggro = True
        self.floor = floor

class InvisibleMonster(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '幽灵刺客', 'normal')
        self.color = (100, 200, 255)
        self.hp = int(25 * (1 + floor * 0.2))
        self.max_hp = self.hp
        self.damage = int(12 * (1 + floor * 0.15))
        self.defense = 3
        self.evasion = 15
        self.exp = 30
        self.gold = 18
        self.ai_type = 'aggressive'
        self.aggro_range = 7
        self.is_invisible = False
        self.invisible_cooldown = 0
        self.invisible_duration = 0
        self.reveal_stun = 0
        self.floor = floor
    
    def update_special(self, game_map, player, entities, all_players=None):
        if self.invisible_cooldown > 0:
            self.invisible_cooldown -= 1
        elif not self.is_invisible:
            if random.random() < 0.3:
                self.is_invisible = True
                self.invisible_duration = random.randint(3, 5)
                self.invisible_cooldown = 8
        
        if self.is_invisible:
            self.invisible_duration -= 1
            if self.invisible_duration <= 0:
                self.is_invisible = False
                self.reveal_stun = 1

class ReviverMonster(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '不死战士', 'normal')
        self.color = (150, 100, 100)
        self.hp = int(40 * (1 + floor * 0.2))
        self.max_hp = self.hp
        self.damage = int(9 * (1 + floor * 0.15))
        self.defense = 6
        self.evasion = 6
        self.exp = 40
        self.gold = 25
        self.ai_type = 'aggressive'
        self.aggro_range = 5
        self.max_revive = 2
        self.revive_count = 0
        self.is_down = False
        self.down_timer = 0
        self.floor = floor
    
    def take_damage(self, amount):
        actual = max(1, amount - self.defense // 2)
        self.hp -= actual
        self.is_aggro = True
        
        if self.hp <= 0 and not self.is_down and self.revive_count < self.max_revive:
            if amount <= self.max_hp * 0.5:
                self.is_down = True
                self.down_timer = 3
                self.hp = 1
                return actual
        
        return actual
    
    def update_special(self, game_map, player, entities, all_players=None):
        if self.is_down:
            self.down_timer -= 1
            if self.down_timer <= 0:
                self.is_down = False
                self.revive_count += 1
                heal_percent = random.uniform(0.3, 0.5)
                self.hp = int(self.max_hp * heal_percent)

class Goblin(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '哥布林', 'normal')
        self.hp = int(25 * (1 + floor * 0.2))
        self.max_hp = self.hp
        self.damage = int(10 * (1 + floor * 0.15))
        self.defense = 4
        self.evasion = 12
        self.exp = 18
        self.gold = 12
        self.ai_type = 'aggressive'
        self.aggro_range = 6
        self.floor = floor

class Orc(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '兽人', 'normal')
        self.hp = int(50 * (1 + floor * 0.2))
        self.max_hp = self.hp
        self.damage = int(14 * (1 + floor * 0.15))
        self.defense = 10
        self.evasion = 5
        self.exp = 30
        self.gold = 20
        self.ai_type = 'aggressive'
        self.aggro_range = 5
        self.floor = floor

class Skeleton(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '骷髅', 'normal')
        self.hp = int(30 * (1 + floor * 0.2))
        self.max_hp = self.hp
        self.damage = int(12 * (1 + floor * 0.15))
        self.defense = 6
        self.evasion = 10
        self.exp = 25
        self.gold = 15
        self.ai_type = 'passive'
        self.aggro_range = 4
        self.floor = floor

class Mage(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '黑暗法师', 'normal')
        self.hp = int(25 * (1 + floor * 0.2))
        self.max_hp = self.hp
        self.damage = int(18 * (1 + floor * 0.15))
        self.defense = 3
        self.evasion = 12
        self.exp = 35
        self.gold = 25
        self.ai_type = 'ranged'
        self.aggro_range = 8
        self.color = (80, 40, 120)
        self.floor = floor

class EliteOrc(Monster):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '精英兽人', 'elite')
        self.hp = int(100 * (1 + floor * 0.25))
        self.max_hp = self.hp
        self.damage = int(22 * (1 + floor * 0.2))
        self.defense = 15
        self.evasion = 10
        self.exp = 80
        self.gold = 60
        self.ai_type = 'aggressive'
        self.aggro_range = 8
        self.color = ORANGE
        self.knockback_skill_cooldown = 0
        self.floor = floor
    
    def update_special(self, game_map, player, entities, all_players=None):
        if self.knockback_skill_cooldown > 0:
            self.knockback_skill_cooldown -= 1
    
    def use_knockback(self, target, game_map):
        if self.knockback_skill_cooldown <= 0:
            self.knockback_skill_cooldown = 4
            dx = target.x - self.x
            dy = target.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                dx = int(dx / dist * 3)
                dy = int(dy / dist * 3)
                new_x = target.x + dx
                new_y = target.y + dy
                if game_map.is_walkable(new_x, new_y):
                    target.x = new_x
                    target.y = new_y
            return True
        return False

BOSS_DATA = {
    1: {
        'name': '哥布林王·咕噜',
        'color': (100, 200, 100),
        'hp_mult': 2.0,
        'dmg_mult': 1.5,
        'special': '召唤哥布林'
    },
    2: {
        'name': '兽人酋长·血斧',
        'color': (200, 100, 50),
        'hp_mult': 2.5,
        'dmg_mult': 1.8,
        'special': '狂暴冲锋'
    },
    3: {
        'name': '巫妖·寒霜',
        'color': (100, 200, 255),
        'hp_mult': 2.2,
        'dmg_mult': 2.0,
        'special': '冰冻射线'
    },
    4: {
        'name': '暗影领主·虚空',
        'color': (100, 50, 150),
        'hp_mult': 2.8,
        'dmg_mult': 2.2,
        'special': '暗影突袭'
    },
    5: {
        'name': '远古巨龙·炎狱',
        'color': (255, 100, 50),
        'hp_mult': 3.5,
        'dmg_mult': 2.5,
        'special': '龙息吐焰'
    }
}

class Boss(Monster):
    def __init__(self, x, y, floor=1):
        boss_data = BOSS_DATA.get(floor, BOSS_DATA[5])
        super().__init__(x, y, boss_data['name'], 'boss')
        self.color = boss_data['color']
        self.hp = int(150 * boss_data['hp_mult'] * (1 + floor * 0.15))
        self.max_hp = self.hp
        self.damage = int(25 * boss_data['dmg_mult'] * (1 + floor * 0.12))
        self.defense = int(15 * (1 + floor * 0.1))
        self.evasion = 12
        self.exp = int(200 * (1 + floor * 0.3))
        self.gold = int(150 * (1 + floor * 0.25))
        self.ai_type = 'aggressive'
        self.aggro_range = 12
        self.special_ability = boss_data['special']
        self.special_cooldown = 0
        self.floor = floor
    
    def update_special(self, game_map, player, entities, all_players=None):
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
    
    def use_special_ability(self, game_map, targets):
        if self.special_cooldown <= 0:
            self.special_cooldown = 5
            return True, self.special_ability
        return False, None

def create_monster(x, y, floor=1):
    monster_types = [Goblin, Orc, Skeleton, Mage, SummonerMonster, InvisibleMonster, ReviverMonster]
    weights = [0.25, 0.2, 0.15, 0.1, 0.1, 0.1, 0.1]
    
    scaled_weights = []
    for w in weights:
        scaled_weights.append(w * (1 + floor * 0.05))
    
    monster_class = random.choices(monster_types, weights=scaled_weights)[0]
    
    if monster_class in [SummonerMonster, InvisibleMonster, ReviverMonster]:
        monster = monster_class(x, y, floor)
    else:
        monster = monster_class(x, y, floor)
    
    monster.floor = floor
    return monster

def create_elite(x, y, floor=1):
    elite = EliteOrc(x, y, floor)
    elite.floor = floor
    return elite

def create_boss(x, y, floor=1):
    boss = Boss(x, y, floor)
    boss.floor = floor
    return boss
