import random
import math
from .config import *
from .asset_loader import asset_loader

class Entity:
    def __init__(self, x, y, name, color=WHITE):
        self.x = x
        self.y = y
        self.name = name
        self.color = color
        self.blocks_movement = False
        self.animation_frame = 0
        self.animation_timer = 0
        self.is_hurt = False
        self.hurt_timer = 0
    
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
    
    def get_distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
    
    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
        
        if self.is_hurt:
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.is_hurt = False
    
    def take_damage(self, amount):
        self.is_hurt = True
        self.hurt_timer = 20

class Character(Entity):
    def __init__(self, x, y, name, class_type='warrior'):
        super().__init__(x, y, name, WHITE)
        self.class_type = class_type
        class_data = CLASSES[class_type]
        
        self.max_hp = class_data['hp']
        self.hp = self.max_hp
        self.max_mp = class_data['mp']
        self.mp = self.max_mp
        
        self.str = class_data['str']
        self.dex = class_data['dex']
        self.int = class_data['int']
        self.defense = class_data['def']
        self.speed = class_data['speed']
        
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        self.gold = 50
        self.skill_points = 0
        
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        self.inventory = []
        self.skills = []
        self.buffs = []
        self.status_effects = []
        
        self.blocks_movement = True
        self.is_attacking = False
        self.attack_timer = 0
        
        self.base_attack_count = 1
        self.extra_attacks = 0
        
        self.level_up_animation = 0
        self.is_leveling_up = False
    
    def get_total_str(self):
        total = self.str
        for slot, item in self.equipment.items():
            if item and 'str' in item.stats:
                total += item.stats['str']
        return total
    
    def get_total_dex(self):
        total = self.dex
        for slot, item in self.equipment.items():
            if item and 'dex' in item.stats:
                total += item.stats['dex']
        return total
    
    def get_total_int(self):
        total = self.int
        for slot, item in self.equipment.items():
            if item and 'int' in item.stats:
                total += item.stats['int']
        return total
    
    def get_total_defense(self):
        total = self.defense
        for slot, item in self.equipment.items():
            if item and 'defense' in item.stats:
                total += item.stats['defense']
        return total
    
    def get_attack_power(self):
        base = self.get_total_str() * 2
        weapon = self.equipment['weapon']
        if weapon:
            base += weapon.stats.get('damage', 0)
        return base
    
    def get_magic_power(self):
        return self.get_total_int() * 3
    
    def get_evasion(self):
        return self.get_total_dex() * 2
    
    def take_damage(self, amount):
        super().take_damage(amount)
        actual_damage = max(1, amount - self.get_total_defense() // 2)
        self.hp -= actual_damage
        return actual_damage
    
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
        return amount
    
    def restore_mp(self, amount):
        self.mp = min(self.max_mp, self.mp + amount)
        return amount
    
    def gain_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.skill_points += 1
        self.max_hp += 20
        self.max_mp += 10
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.str += 2
        self.dex += 1
        self.int += 1
        self.defense += 2
        self.exp_to_next = int(self.exp_to_next * 1.5)
        self.is_leveling_up = True
        self.level_up_animation = 120
    
    def equip_item(self, item):
        if item.slot in self.equipment:
            old_item = self.equipment[item.slot]
            if old_item:
                self.inventory.append(old_item)
            self.equipment[item.slot] = item
            if item in self.inventory:
                self.inventory.remove(item)
            return True
        return False
    
    def unequip_item(self, slot):
        if self.equipment[slot]:
            self.inventory.append(self.equipment[slot])
            self.equipment[slot] = None
            return True
        return False
    
    def add_item(self, item):
        if len(self.inventory) < 20:
            self.inventory.append(item)
            return True
        return False
    
    def remove_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False
    
    def update_animation(self):
        super().update_animation()
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False
    
    def attack(self):
        self.is_attacking = True
        self.attack_timer = 15
    
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
    
    def remove_status(self, status_type):
        self.status_effects = [s for s in self.status_effects if s['type'] != status_type]
    
    def has_status(self, status_type):
        return any(s['type'] == status_type for s in self.status_effects)
    
    def update_status_effects(self):
        messages = []
        for status in self.status_effects[:]:
            if status['damage'] > 0:
                self.hp -= status['damage']
                messages.append(f'{status["type"]} 造成 {status["damage"]} 点伤害！')
            
            status['duration'] -= 1
            if status['duration'] <= 0:
                self.status_effects.remove(status)
                messages.append(f'{status["type"]} 效果消失了！')
        
        return messages
    
    def get_total_attack_count(self):
        count = self.base_attack_count + self.extra_attacks
        if self.has_status('haste'):
            count += 1
        return count
    
    def apply_passive_effects(self):
        if self.class_type == 'paladin':
            self.defense += 2
            if self.hp < self.max_hp * 0.3:
                heal = int(self.max_hp * 0.02)
                self.hp = min(self.max_hp, self.hp + heal)
