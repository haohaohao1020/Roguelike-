import random
from .config import *
from .entity import Entity

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
        
        self.blocks_movement = True
    
    def take_damage(self, amount):
        super().take_damage(amount)
        actual = max(1, amount - self.defense // 2)
        self.hp -= actual
        self.is_aggro = True
        return actual
    
    def is_alive(self):
        return self.hp > 0
    
    def update_ai(self, game_map, player, entities):
        if self.frozen > 0:
            self.frozen -= 1
            return
        if self.stunned > 0:
            self.stunned -= 1
            return
        
        distance = self.get_distance_to(player)
        
        if self.ai_type == 'passive':
            if distance <= self.aggro_range:
                self.is_aggro = True
            if self.is_aggro:
                self.move_towards(game_map, player, entities)
        
        elif self.ai_type == 'aggressive':
            self.is_aggro = True
            self.move_towards(game_map, player, entities)
        
        elif self.ai_type == 'ranged':
            if distance <= 3:
                self.move_away(game_map, player, entities)
            elif distance <= self.aggro_range:
                pass
            else:
                self.move_towards(game_map, player, entities)
        
        if self.hp < self.max_hp * 0.3 and random.random() < 0.3:
            self.move_away(game_map, player, entities)
    
    def move_towards(self, game_map, target, entities):
        dx = target.x - self.x
        dy = target.y - self.y
        
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
            if entity.blocks_movement and entity.x == x and entity.y == y:
                return True
        return False

class Goblin(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, '哥布林', 'normal')
        self.hp = 20
        self.max_hp = 20
        self.damage = 8
        self.defense = 3
        self.evasion = 10
        self.exp = 15
        self.gold = 8
        self.ai_type = 'aggressive'
        self.aggro_range = 6

class Orc(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, '兽人', 'normal')
        self.hp = 40
        self.max_hp = 40
        self.damage = 12
        self.defense = 8
        self.evasion = 5
        self.exp = 25
        self.gold = 15
        self.ai_type = 'aggressive'
        self.aggro_range = 5

class Skeleton(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, '骷髅', 'normal')
        self.hp = 25
        self.max_hp = 25
        self.damage = 10
        self.defense = 5
        self.evasion = 8
        self.exp = 20
        self.gold = 10
        self.ai_type = 'passive'
        self.aggro_range = 4

class Mage(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, '黑暗法师', 'normal')
        self.hp = 20
        self.max_hp = 20
        self.damage = 15
        self.defense = 2
        self.evasion = 10
        self.exp = 30
        self.gold = 20
        self.ai_type = 'ranged'
        self.aggro_range = 8

class EliteOrc(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, '精英兽人', 'elite')
        self.hp = 80
        self.max_hp = 80
        self.damage = 18
        self.defense = 12
        self.evasion = 8
        self.exp = 60
        self.gold = 40
        self.ai_type = 'aggressive'
        self.aggro_range = 7
        self.color = ORANGE

class Dragon(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, '远古巨龙', 'boss')
        self.hp = 200
        self.max_hp = 200
        self.damage = 30
        self.defense = 20
        self.evasion = 10
        self.exp = 200
        self.gold = 100
        self.ai_type = 'aggressive'
        self.aggro_range = 10
        self.color = PURPLE

def create_monster(x, y, floor=1):
    monster_types = [Goblin, Orc, Skeleton, Mage]
    weights = [0.4, 0.3, 0.2, 0.1]
    
    scaled_weights = []
    for i, w in enumerate(weights):
        scaled_weights.append(w * (1 + floor * 0.1))
    
    monster_class = random.choices(monster_types, weights=scaled_weights)[0]
    monster = monster_class(x, y)
    
    monster.hp = int(monster.hp * (1 + floor * 0.2))
    monster.max_hp = monster.hp
    monster.damage = int(monster.damage * (1 + floor * 0.15))
    monster.exp = int(monster.exp * (1 + floor * 0.3))
    monster.gold = int(monster.gold * (1 + floor * 0.2))
    
    return monster

def create_elite(x, y, floor=1):
    elite = EliteOrc(x, y)
    elite.hp = int(elite.hp * (1 + floor * 0.25))
    elite.max_hp = elite.hp
    elite.damage = int(elite.damage * (1 + floor * 0.2))
    elite.exp = int(elite.exp * (1 + floor * 0.4))
    elite.gold = int(elite.gold * (1 + floor * 0.3))
    return elite

def create_boss(x, y, floor=5):
    boss = Dragon(x, y)
    boss.hp = int(boss.hp * (1 + floor * 0.1))
    boss.max_hp = boss.hp
    boss.damage = int(boss.damage * (1 + floor * 0.1))
    return boss
