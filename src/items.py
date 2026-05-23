import random
from .config import *
from .entity import Entity
from .asset_loader import asset_loader

class Item(Entity):
    def __init__(self, x, y, name, item_type='item'):
        super().__init__(x, y, name)
        self.item_type = item_type
        self.quality = 'common'
        self.description = ''
        self.value = 10
    
    def use(self, user):
        pass

class Equipment(Item):
    def __init__(self, x, y, name, slot, quality='common', floor=1):
        super().__init__(x, y, name, 'equipment')
        self.slot = slot
        self.quality = quality
        self.floor = floor
        self.base_stats = {}
        self.sub_stats = {}
        self.element_enchant = None
        self.element_damage = 0
        self.rune_slots = 0
        self.runes = []
        self.set_name = None
        self.appearance = None
        self.level = 1
        self.enhance_level = 0
        self.generate_stats()
        self.generate_sub_stats()
        self.generate_rune_slots()
        self.generate_set()
        self.calculate_value()
    
    def use(self, user):
        if hasattr(user, 'equip_item'):
            success = user.equip_item(self)
            if success:
                return f'装备了 {self.name}！'
            return '背包中已装备这个物品'
        return None
    
    def generate_stats(self):
        quality_multipliers = {
            'common': 1.0,
            'uncommon': 1.3,
            'rare': 1.6,
            'epic': 2.0,
            'legendary': 2.8
        }
        mult = quality_multipliers[self.quality]
        floor_mult = 1 + (self.floor - 1) * 0.15
        
        if self.slot == 'weapon':
            self.base_stats['physical_attack'] = int(random.randint(8, 20) * mult * floor_mult)
            self.base_stats['magic_attack'] = int(random.randint(5, 15) * mult * floor_mult)
            if random.random() < 0.3:
                self.base_stats['critical_chance'] = int(random.randint(1, 5) * mult)
        elif self.slot == 'helmet':
            self.base_stats['physical_defense'] = int(random.randint(5, 12) * mult * floor_mult)
            self.base_stats['magic_defense'] = int(random.randint(4, 10) * mult * floor_mult)
            self.base_stats['max_hp'] = int(random.randint(20, 50) * mult * floor_mult)
        elif self.slot == 'chest':
            self.base_stats['physical_defense'] = int(random.randint(10, 25) * mult * floor_mult)
            self.base_stats['magic_defense'] = int(random.randint(8, 20) * mult * floor_mult)
            self.base_stats['max_hp'] = int(random.randint(30, 80) * mult * floor_mult)
        elif self.slot == 'leggings':
            self.base_stats['physical_defense'] = int(random.randint(8, 18) * mult * floor_mult)
            self.base_stats['magic_defense'] = int(random.randint(6, 15) * mult * floor_mult)
            self.base_stats['max_hp'] = int(random.randint(25, 60) * mult * floor_mult)
        elif self.slot == 'boots':
            self.base_stats['physical_defense'] = int(random.randint(4, 10) * mult * floor_mult)
            self.base_stats['magic_defense'] = int(random.randint(3, 8) * mult * floor_mult)
            self.base_stats['move_speed'] = int(random.randint(1, 3) * mult)
            self.base_stats['evasion'] = int(random.randint(1, 5) * mult)
        elif self.slot == 'accessory':
            stat_choices = ['max_hp', 'max_mp', 'critical_chance', 'critical_damage', 
                           'physical_attack', 'magic_attack', 'evasion', 'block_rate']
            num_stats = random.randint(2, 4)
            chosen_stats = random.sample(stat_choices, num_stats)
            for stat in chosen_stats:
                if stat in ['max_hp', 'max_mp']:
                    self.base_stats[stat] = int(random.randint(20, 60) * mult * floor_mult)
                elif stat in ['critical_damage']:
                    self.base_stats[stat] = int(random.randint(5, 15) * mult)
                else:
                    self.base_stats[stat] = int(random.randint(2, 8) * mult)
    
    def generate_sub_stats(self):
        sub_stat_counts = {
            'common': 0,
            'uncommon': 1,
            'rare': 2,
            'epic': 3,
            'legendary': 4
        }
        num_sub_stats = sub_stat_counts[self.quality]
        
        if num_sub_stats > 0:
            chosen_sub_stats = random.sample(SUB_STAT_TYPES, min(num_sub_stats, len(SUB_STAT_TYPES)))
            for sub_stat in chosen_sub_stats:
                if sub_stat in ['hp_regen', 'mp_regen']:
                    self.sub_stats[sub_stat] = round(random.uniform(1, 5), 1)
                elif sub_stat in ['physical_lifesteal', 'magic_lifesteal', 'damage_reflect',
                                 'status_resistance', 'boss_damage', 'mob_damage', 'damage_reduction']:
                    self.sub_stats[sub_stat] = round(random.uniform(1, 10), 1)
    
    def generate_rune_slots(self):
        slot_counts = {
            'common': 0,
            'uncommon': 0,
            'rare': 1,
            'epic': 2,
            'legendary': 3
        }
        self.rune_slots = slot_counts[self.quality]
        self.runes = [None] * self.rune_slots
    
    def generate_set(self):
        if self.quality in ['epic', 'legendary'] and random.random() < 0.4:
            self.set_name = random.choice(SET_NAMES)
    
    def calculate_value(self):
        base_value = {
            'common': 20,
            'uncommon': 50,
            'rare': 120,
            'epic': 300,
            'legendary': 800
        }
        self.value = base_value[self.quality] + self.enhance_level * 20
        if self.set_name:
            self.value *= 1.5
        self.value = int(self.value)
    
    def enchant(self, element_type, damage):
        self.element_enchant = element_type
        self.element_damage = damage
    
    def insert_rune(self, rune_type, slot_index):
        if 0 <= slot_index < self.rune_slots and self.runes[slot_index] is None:
            self.runes[slot_index] = rune_type
            return True
        return False
    
    def remove_rune(self, slot_index):
        if 0 <= slot_index < self.rune_slots:
            rune = self.runes[slot_index]
            self.runes[slot_index] = None
            return rune
        return None
    
    def enhance(self):
        if self.enhance_level < 10:
            self.enhance_level += 1
            for stat in self.base_stats:
                self.base_stats[stat] = int(self.base_stats[stat] * 1.1)
            self.calculate_value()
            return True
        return False
    
    def reforge_sub_stats(self):
        self.sub_stats = {}
        self.generate_sub_stats()
    
    def get_power(self):
        power = 0
        for stat, value in self.base_stats.items():
            if stat in ['physical_attack', 'magic_attack']:
                power += value * 2
            elif stat in ['max_hp', 'max_mp']:
                power += value * 0.5
            else:
                power += value
        power += self.element_damage
        power += self.enhance_level * 10
        return int(power)

class Potion(Item):
    def __init__(self, x, y, potion_type='health'):
        names = {
            'health': '生命药水',
            'mana': '魔力药水',
            'strength': '力量药水',
            'dexterity': '敏捷药水'
        }
        super().__init__(x, y, names[potion_type], 'potion')
        self.potion_type = potion_type
        self.value = 20
    
    def use(self, user):
        if self.potion_type == 'health':
            amount = user.heal(50)
            return f'恢复了 {amount} 点生命'
        elif self.potion_type == 'mana':
            amount = user.restore_mp(30)
            return f'恢复了 {amount} 点魔力'
        elif self.potion_type == 'strength':
            user.str += 5
            user.buffs.append({'type': 'strength', 'duration': 10, 'value': 5})
            return '力量增加了 5 点'
        elif self.potion_type == 'dexterity':
            user.dex += 5
            user.buffs.append({'type': 'dexterity', 'duration': 10, 'value': 5})
            return '敏捷增加了 5 点'
        return '使用了药水'

class Scroll(Item):
    def __init__(self, x, y, scroll_type='fireball'):
        names = {
            'fireball': '火球卷轴',
            'teleport': '传送卷轴',
            'freeze': '冰冻卷轴',
            'identify': '鉴定卷轴'
        }
        super().__init__(x, y, names[scroll_type], 'scroll')
        self.scroll_type = scroll_type
        self.value = 30

class Gold(Item):
    def __init__(self, x, y, amount=10):
        super().__init__(x, y, '金币', 'gold')
        self.amount = amount
        self.value = amount

class Rune(Item):
    def __init__(self, x, y, rune_type='strength', tier=1):
        super().__init__(x, y, RUNE_NAMES[rune_type], 'rune')
        self.rune_type = rune_type
        self.tier = tier
        self.value = 50 * tier

class Material(Item):
    def __init__(self, x, y, material_type='enhance_stone', amount=1):
        names = {
            'enhance_stone': '强化石',
            'reforge_stone': '洗练石',
            'enchant_crystal': '附魔水晶'
        }
        super().__init__(x, y, names[material_type], 'material')
        self.material_type = material_type
        self.amount = amount
        self.value = 30

class ReviveScroll(Item):
    def __init__(self, x, y, amount=1):
        super().__init__(x, y, '复活符', 'revive_scroll')
        self.amount = amount
        self.value = 500
        self.color = (255, 200, 200)
        self.stackable = True
        self.item_type = 'revive_scroll'
    
    def use(self, user, game=None):
        if not game or game.game_mode != 'coop':
            return '单人模式无法使用复活符！'
        
        target = None
        if hasattr(user, 'is_player1') and user.is_player1:
            if game.player2 and not game.player2.is_alive():
                target = game.player2
        elif hasattr(user, 'is_player2') and user.is_player2:
            if game.player and not game.player.is_alive():
                target = game.player
        
        if not target:
            return '没有需要复活的队友！'
        
        target.hp = target.get_total_max_hp()
        target.mp = target.get_total_max_mp()
        target.x = user.x
        target.y = user.y
        target.is_dead = False
        
        return f'复活了 {target.name}！'

class Chest(Entity):
    def __init__(self, x, y, floor=1):
        super().__init__(x, y, '宝箱', GOLD)
        self.is_open = False
        self.items = []
        self.blocks_movement = True
        self.floor = floor
    
    def open(self, user):
        if not self.is_open:
            self.is_open = True
            if random.random() < 0.8:
                gold = Gold(self.x, self.y, random.randint(10, 50) * self.floor)
                user.gold += gold.amount
            if random.random() < 0.6:
                potion = Potion(self.x, self.y, random.choice(['health', 'mana']))
                user.add_item(potion)
            if random.random() < 0.5:
                equip = create_random_equipment(self.x, self.y, self.floor)
                user.add_item(equip)
                user.add_to_collection(equip)
            if random.random() < 0.2:
                material = Material(self.x, self.y, random.choice(['enhance_stone', 'reforge_stone']))
                user.add_item(material)
            return '打开了宝箱！'
        return '宝箱已经打开过了'

def create_random_equipment(x, y, floor=1):
    slot = random.choice(EQUIPMENT_SLOTS)
    names = {
        'weapon': ['短剑', '长剑', '战斧', '战锤', '魔杖', '法杖', '匕首', '巨剑'],
        'helmet': ['皮帽', '铁盔', '头盔', '法师帽', '骑士盔', '皇冠'],
        'chest': ['皮甲', '锁子甲', '板甲', '法袍', '骑士胸甲', '龙鳞甲'],
        'leggings': ['皮裤', '锁甲裤', '板甲腿', '护腿', '骑士腿甲'],
        'boots': ['皮靴', '铁靴', '速度之靴', '骑士靴', '龙鳞靴'],
        'accessory': ['力量戒指', '智慧护符', '生命项链', '防御徽章', '暴击戒指']
    }
    name = random.choice(names[slot])
    
    quality_weights = {
        1: [60, 25, 10, 4, 1],
        2: [50, 30, 14, 5, 1],
        3: [40, 30, 20, 8, 2],
        4: [30, 30, 25, 12, 3],
        5: [20, 25, 30, 18, 7]
    }
    weights = quality_weights.get(min(floor, 5), [60, 25, 10, 4, 1])
    qualities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
    quality = random.choices(qualities, weights=weights, k=1)[0]
    
    equip = Equipment(x, y, name, slot, quality, floor)
    return equip

def create_random_item(x, y, floor=1):
    item_type = random.choice(['potion', 'scroll', 'equipment', 'gold', 'material'])
    if item_type == 'potion':
        return Potion(x, y, random.choice(['health', 'mana']))
    elif item_type == 'scroll':
        return Scroll(x, y)
    elif item_type == 'equipment':
        return create_random_equipment(x, y, floor)
    elif item_type == 'gold':
        return Gold(x, y, random.randint(5, 30) * floor)
    elif item_type == 'material':
        return Material(x, y)
    return None
