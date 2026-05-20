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
        
        self.physical_attack = 10
        self.magic_attack = 5
        self.physical_defense = 5
        self.magic_defense = 3
        self.move_speed = 1
        self.critical_chance = 5
        self.critical_damage = 150
        self.evasion = 5
        self.block_rate = 0
        
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        self.gold = 50
        self.skill_points = 1
        
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        self.inventory = []
        self.skills = []
        self.buffs = []
        self.status_effects = []
        
        self.collection = set()
        self.enhance_materials = 0
        self.reforge_stones = 0
        
        self.blocks_movement = True
        self.is_attacking = False
        self.attack_timer = 0
        
        self.base_attack_count = 1
        self.extra_attacks = 0
        
        self.level_up_animation = 0
        self.is_leveling_up = False
        
        self.talents = {
            'strength_1': False,
            'strength_2': False,
            'strength_3': False,
            'dexterity_1': False,
            'dexterity_2': False,
            'dexterity_3': False,
            'intelligence_1': False,
            'intelligence_2': False,
            'intelligence_3': False,
            'defense_1': False,
            'defense_2': False,
            'defense_3': False,
            'hp_1': False,
            'hp_2': False,
            'hp_3': False,
            'mp_1': False,
            'mp_2': False,
            'mp_3': False
        }
    
    def get_total_str(self):
        total = self.str
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'strength':
                        total += 5
        return total
    
    def get_total_dex(self):
        total = self.dex
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'dexterity':
                        total += 5
        return total
    
    def get_total_int(self):
        total = self.int
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'intelligence':
                        total += 5
        return total
    
    def get_total_physical_attack(self):
        total = self.physical_attack + self.str * 2
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('physical_attack', 0)
                if item.element_enchant:
                    total += item.element_damage
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'strength':
                        total += 3
                    if rune == 'critical':
                        total += 5
        return total
    
    def get_total_magic_attack(self):
        total = self.magic_attack + self.int * 3
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('magic_attack', 0)
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'intelligence':
                        total += 5
        return total
    
    def get_total_physical_defense(self):
        total = self.physical_defense + self.defense
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('physical_defense', 0)
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'vitality':
                        total += 10
        return total
    
    def get_total_magic_defense(self):
        total = self.magic_defense
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('magic_defense', 0)
        return total
    
    def get_total_max_hp(self):
        total = self.max_hp + self.str * 5
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('max_hp', 0)
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'vitality':
                        total += 30
        set_bonus = self.get_set_bonuses()
        total += set_bonus.get('max_hp', 0)
        return total
    
    def get_total_max_mp(self):
        total = self.max_mp + self.int * 3
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('max_mp', 0)
        return total
    
    def get_total_critical_chance(self):
        total = self.critical_chance + self.dex
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('critical_chance', 0)
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'runes'):
                for rune in item.runes:
                    if rune == 'critical':
                        total += 5
        set_bonus = self.get_set_bonuses()
        total += set_bonus.get('critical_chance', 0)
        return min(100, total)
    
    def get_total_critical_damage(self):
        total = self.critical_damage
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('critical_damage', 0)
        return total
    
    def get_total_evasion(self):
        total = self.evasion + self.dex * 2
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('evasion', 0)
        set_bonus = self.get_set_bonuses()
        total += set_bonus.get('evasion', 0)
        return min(80, total)
    
    def get_total_block_rate(self):
        total = self.block_rate
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('block_rate', 0)
        set_bonus = self.get_set_bonuses()
        total += set_bonus.get('holy_shield', 0)
        return min(50, total)
    
    def get_total_move_speed(self):
        total = self.move_speed
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'base_stats'):
                total += item.base_stats.get('move_speed', 0)
        return total
    
    def get_sub_stats(self):
        sub_stats = {stat: 0 for stat in SUB_STAT_TYPES}
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'sub_stats'):
                for stat, value in item.sub_stats.items():
                    sub_stats[stat] += value
        return sub_stats
    
    def get_set_counts(self):
        set_counts = {}
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'set_name') and item.set_name:
                set_counts[item.set_name] = set_counts.get(item.set_name, 0) + 1
        return set_counts
    
    def get_set_bonuses(self):
        bonuses = {}
        set_counts = self.get_set_counts()
        for set_name, count in set_counts.items():
            if set_name in SET_BONUSES:
                for required, bonus in SET_BONUSES[set_name].items():
                    if count >= required:
                        bonuses.update(bonus)
        return bonuses
    
    def get_attack_power(self):
        return self.get_total_physical_attack()
    
    def get_magic_power(self):
        return self.get_total_magic_attack()
    
    def get_evasion(self):
        return self.get_total_evasion()
    
    def get_total_defense(self):
        return self.get_total_physical_defense()
    
    def take_damage(self, amount):
        super().take_damage(amount)
        actual_damage = max(1, amount - self.get_total_defense() // 2)
        self.hp -= actual_damage
        return actual_damage
    
    def heal(self, amount):
        max_hp = self.get_total_max_hp()
        actual_heal = min(amount, max_hp - self.hp)
        self.hp = min(max_hp, self.hp + amount)
        return actual_heal
    
    def restore_mp(self, amount):
        max_mp = self.get_total_max_mp()
        actual_restore = min(amount, max_mp - self.mp)
        self.mp = min(max_mp, self.mp + amount)
        return actual_restore
    
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
    
    def can_unlock_talent(self, talent_id):
        talent_tiers = {
            'strength_1': 1, 'strength_2': 3, 'strength_3': 5,
            'dexterity_1': 1, 'dexterity_2': 3, 'dexterity_3': 5,
            'intelligence_1': 1, 'intelligence_2': 3, 'intelligence_3': 5,
            'defense_1': 1, 'defense_2': 3, 'defense_3': 5,
            'hp_1': 1, 'hp_2': 3, 'hp_3': 5,
            'mp_1': 1, 'mp_2': 3, 'mp_3': 5
        }
        prerequisites = {
            'strength_2': 'strength_1',
            'strength_3': 'strength_2',
            'dexterity_2': 'dexterity_1',
            'dexterity_3': 'dexterity_2',
            'intelligence_2': 'intelligence_1',
            'intelligence_3': 'intelligence_2',
            'defense_2': 'defense_1',
            'defense_3': 'defense_2',
            'hp_2': 'hp_1',
            'hp_3': 'hp_2',
            'mp_2': 'mp_1',
            'mp_3': 'mp_2'
        }
        
        if self.talents.get(talent_id, False):
            return False, '已学会'
        
        if self.skill_points <= 0:
            return False, '点数不足'
        
        if self.level < talent_tiers.get(talent_id, 1):
            return False, f'需要等级{talent_tiers.get(talent_id, 1)}'
        
        if talent_id in prerequisites and not self.talents.get(prerequisites[talent_id], False):
            return False, '需要前置天赋'
        
        return True, '可以学习'
    
    def unlock_talent(self, talent_id):
        can_unlock, message = self.can_unlock_talent(talent_id)
        if not can_unlock:
            return False, message
        
        talent_effects = {
            'strength_1': ('str', 3),
            'strength_2': ('str', 5),
            'strength_3': ('str', 8),
            'dexterity_1': ('dex', 3),
            'dexterity_2': ('dex', 5),
            'dexterity_3': ('dex', 8),
            'intelligence_1': ('int', 3),
            'intelligence_2': ('int', 5),
            'intelligence_3': ('int', 8),
            'defense_1': ('defense', 3),
            'defense_2': ('defense', 5),
            'defense_3': ('defense', 8),
            'hp_1': ('max_hp', 30),
            'hp_2': ('max_hp', 50),
            'hp_3': ('max_hp', 80),
            'mp_1': ('max_mp', 20),
            'mp_2': ('max_mp', 35),
            'mp_3': ('max_mp', 50)
        }
        
        if talent_id in talent_effects:
            stat, value = talent_effects[talent_id]
            if stat == 'max_hp':
                self.max_hp += value
                self.hp = min(self.hp + value, self.max_hp)
            elif stat == 'max_mp':
                self.max_mp += value
                self.mp = min(self.mp + value, self.max_mp)
            else:
                setattr(self, stat, getattr(self, stat) + value)
        
        self.talents[talent_id] = True
        self.skill_points -= 1
        return True, '学习成功'
    
    def equip_item(self, item):
        if hasattr(item, 'slot') and item.slot in self.equipment:
            old_item = self.equipment[item.slot]
            if old_item:
                self.inventory.append(old_item)
            self.equipment[item.slot] = item
            if item in self.inventory:
                self.inventory.remove(item)
            return True
        return False
    
    def unequip_item(self, slot):
        if slot in self.equipment and self.equipment[slot]:
            if len(self.inventory) < 50:
                self.inventory.append(self.equipment[slot])
                self.equipment[slot] = None
                return True
        return False
    
    def unequip_all(self):
        unequipped = []
        for slot in EQUIPMENT_SLOTS:
            if self.equipment[slot] and len(self.inventory) < 50:
                self.inventory.append(self.equipment[slot])
                unequipped.append(slot)
                self.equipment[slot] = None
        return unequipped
    
    def quick_swap(self, equipment_set):
        old_equipment = dict(self.equipment)
        success = True
        for slot, item in equipment_set.items():
            if item:
                if not self.equip_item(item):
                    success = False
                    break
        if not success:
            self.equipment = old_equipment
        return success
    
    def add_to_collection(self, item):
        if hasattr(item, 'name') and hasattr(item, 'quality'):
            key = f"{item.name}_{item.quality}"
            self.collection.add(key)
    
    def is_in_collection(self, item):
        key = f"{item.name}_{item.quality}"
        return key in self.collection
    
    def get_collection_count(self):
        return len(self.collection)
    
    def add_item(self, item):
        if len(self.inventory) < 50:
            self.inventory.append(item)
            if hasattr(item, 'item_type') and item.item_type == 'equipment':
                self.add_to_collection(item)
            return True
        return False
    
    def remove_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False
    
    def get_sorted_inventory(self, sort_by='power', filter_quality=None, filter_slot=None):
        items = [item for item in self.inventory if hasattr(item, 'item_type')]
        
        if filter_quality:
            items = [item for item in items if hasattr(item, 'quality') and item.quality == filter_quality]
        
        if filter_slot:
            items = [item for item in items if hasattr(item, 'slot') and item.slot == filter_slot]
        
        if sort_by == 'power':
            items.sort(key=lambda x: x.get_power() if hasattr(x, 'get_power') else 0, reverse=True)
        elif sort_by == 'quality':
            quality_order = {'legendary': 5, 'epic': 4, 'rare': 3, 'uncommon': 2, 'common': 1}
            items.sort(key=lambda x: quality_order.get(getattr(x, 'quality', 'common'), 0), reverse=True)
        elif sort_by == 'value':
            items.sort(key=lambda x: getattr(x, 'value', 0), reverse=True)
        elif sort_by == 'name':
            items.sort(key=lambda x: getattr(x, 'name', ''))
        
        return items
    
    def decompose_equipment(self, item):
        if hasattr(item, 'item_type') and item.item_type == 'equipment':
            quality_materials = {
                'common': 1,
                'uncommon': 2,
                'rare': 5,
                'epic': 12,
                'legendary': 30
            }
            materials = quality_materials.get(item.quality, 1)
            self.enhance_materials += materials
            if item in self.inventory:
                self.inventory.remove(item)
            elif item in self.equipment.values():
                for slot, equip in self.equipment.items():
                    if equip == item:
                        self.equipment[slot] = None
                        break
            return materials
        return 0
    
    def bulk_decompose(self, min_quality='common'):
        quality_order = {'common': 1, 'uncommon': 2, 'rare': 3, 'epic': 4, 'legendary': 5}
        min_level = quality_order.get(min_quality, 1)
        
        total_materials = 0
        to_decompose = []
        
        for item in self.inventory:
            if (hasattr(item, 'item_type') and item.item_type == 'equipment' and 
                quality_order.get(item.quality, 1) <= min_level):
                to_decompose.append(item)
        
        for item in to_decompose:
            total_materials += self.decompose_equipment(item)
        
        return total_materials
    
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
