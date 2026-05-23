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
            'legendary': 2.8,
            'mythic': 4.0
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
            'legendary': 4,
            'mythic': 5
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
            'legendary': 3,
            'mythic': 4
        }
        self.rune_slots = slot_counts[self.quality]
        self.runes = [None] * self.rune_slots
    
    def generate_set(self):
        set_chance = {
            'common': 0,
            'uncommon': 0,
            'rare': 0.1,
            'epic': 0.4,
            'legendary': 0.7,
            'mythic': 1.0
        }
        if random.random() < set_chance.get(self.quality, 0):
            self.set_name = random.choice(SET_NAMES)
    
    def calculate_value(self):
        base_value = {
            'common': 20,
            'uncommon': 50,
            'rare': 120,
            'epic': 300,
            'legendary': 800,
            'mythic': 2000
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

class TeleportAnchor(Item):
    def __init__(self, x, y, amount=1):
        super().__init__(x, y, '传送锚点', 'teleport_anchor')
        self.amount = amount
        self.value = 150
        self.color = CYAN
        self.stackable = True
        self.description = '使用后标记当前位置，可随时传送返回'
    
    def use(self, user, game=None):
        if not game:
            return '无法使用！'
        
        if not hasattr(user, 'teleport_anchors'):
            user.teleport_anchors = []
        
        if len(user.teleport_anchors) >= 5:
            return '锚点数量已达上限(5个)！'
        
        anchor_data = {
            'floor': game.floor,
            'x': user.x,
            'y': user.y,
            'name': f'锚点{len(user.teleport_anchors) + 1}'
        }
        user.teleport_anchors.append(anchor_data)
        
        return f'标记了传送锚点！当前共{len(user.teleport_anchors)}个锚点'

class RespecBook(Item):
    def __init__(self, x, y, amount=1):
        super().__init__(x, y, '洗点书', 'respec_book')
        self.amount = amount
        self.value = 300
        self.color = PURPLE
        self.stackable = True
        self.description = '重置所有天赋点数，可重新分配'
    
    def use(self, user):
        talent_points_refund = 0
        
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
        
        for talent_id, learned in user.talents.items():
            if learned and talent_id in talent_effects:
                talent_points_refund += 1
                stat, value = talent_effects[talent_id]
                if stat == 'max_hp':
                    user.max_hp -= value
                    user.hp = min(user.hp, user.max_hp)
                elif stat == 'max_mp':
                    user.max_mp -= value
                    user.mp = min(user.mp, user.max_mp)
                else:
                    current_value = getattr(user, stat, 0)
                    setattr(user, stat, max(0, current_value - value))
        
        for talent_id in user.talents:
            user.talents[talent_id] = False
        
        user.skill_points += talent_points_refund
        
        return f'重置了{talent_points_refund}点天赋点数！'

class SummonCard(Item):
    def __init__(self, x, y, amount=1):
        super().__init__(x, y, '随机召唤卡', 'summon_card')
        self.amount = amount
        self.value = 200
        self.color = ORANGE
        self.stackable = True
        self.description = '随机召唤一只怪物协助作战，持续30回合'
    
    def use(self, user, game=None):
        if not game:
            return '无法使用！'
        
        from .monster import create_monster, create_elite
        
        is_elite = random.random() < 0.3
        
        summon_positions = [
            (user.x + 1, user.y),
            (user.x - 1, user.y),
            (user.x, user.y + 1),
            (user.x, user.y - 1),
            (user.x + 1, user.y + 1),
            (user.x - 1, user.y - 1),
            (user.x + 1, user.y - 1),
            (user.x - 1, user.y + 1)
        ]
        
        summon_x, summon_y = user.x + 1, user.y
        for sx, sy in summon_positions:
            if game.game_map.is_walkable(sx, sy):
                is_blocked = False
                for m in game.monsters:
                    if m.x == sx and m.y == sy:
                        is_blocked = True
                        break
                if not is_blocked:
                    summon_x, summon_y = sx, sy
                    break
        
        if is_elite:
            summon = create_elite(summon_x, summon_y, game.floor)
            summon.name = f'召唤的{summon.name}'
        else:
            summon = create_monster(summon_x, summon_y, game.floor)
            summon.name = f'召唤的{summon.name}'
        
        summon.is_summon = True
        summon.summon_master = user
        summon.summon_duration = 30
        summon.is_hostile = False
        summon.is_aggro = True
        summon.ai_type = 'aggressive'
        
        summon.max_hp = int(summon.max_hp * 1.2)
        summon.hp = summon.max_hp
        summon.damage = int(summon.damage * 1.3)
        summon.exp = 0
        summon.gold = 0
        
        game.monsters.append(summon)
        
        quality = '精英' if is_elite else '普通'
        return f'召唤了一只{quality}怪物协助作战！持续30回合'

class MapReveal(Item):
    def __init__(self, x, y, amount=1):
        super().__init__(x, y, '全局地图透视', 'map_reveal')
        self.amount = amount
        self.value = 250
        self.color = YELLOW
        self.stackable = True
        self.description = '临时显示整张地图的所有内容'
    
    def use(self, user, game=None):
        if not game or not game.game_map:
            return '无法使用！'
        
        game.game_map.reveal_all()
        game.map_reveal_duration = 30
        
        return '地图已完全透视！持续30回合'

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

class SynthesisSystem:
    def __init__(self):
        self.synthesis_recipes = {
            'common': 'uncommon',
            'uncommon': 'rare',
            'rare': 'epic',
            'epic': 'legendary',
            'legendary': 'mythic'
        }
        self.synthesis_history = []
    
    def get_synthesizeable_equipment(self, inventory):
        equipment_by_quality = {}
        for item in inventory:
            if hasattr(item, 'item_type') and item.item_type == 'equipment':
                quality = item.quality
                if quality not in ['mythic']:
                    if quality not in equipment_by_quality:
                        equipment_by_quality[quality] = []
                    equipment_by_quality[quality].append(item)
        return equipment_by_quality
    
    def can_synthesize(self, quality, inventory):
        equipment_by_quality = self.get_synthesizeable_equipment(inventory)
        return len(equipment_by_quality.get(quality, [])) >= 3
    
    def synthesize(self, quality, inventory, floor=1):
        equipment_by_quality = self.get_synthesizeable_equipment(inventory)
        candidates = equipment_by_quality.get(quality, [])
        
        if len(candidates) < 3:
            return False, '材料不足！需要3件同品质装备', None
        
        materials = candidates[:3]
        
        for material in materials:
            if material in inventory:
                inventory.remove(material)
        
        target_quality = self.synthesis_recipes.get(quality, quality)
        
        new_equip = create_random_equipment(0, 0, floor)
        new_equip.quality = target_quality
        new_equip.generate_stats()
        new_equip.generate_sub_stats()
        new_equip.generate_rune_slots()
        new_equip.generate_set()
        new_equip.calculate_value()
        
        if random.random() < 0.3:
            extra_sub_stats = random.sample(SUB_STAT_TYPES, 1)
            for stat in extra_sub_stats:
                if stat not in new_equip.sub_stats:
                    new_equip.sub_stats[stat] = round(random.uniform(1, 8), 1)
        
        record = {
            'materials': [f'{m.name}({QUALITY_NAMES.get(m.quality, m.quality)})' for m in materials],
            'result': f'{new_equip.name}({QUALITY_NAMES.get(new_equip.quality, new_equip.quality)})',
            'floor': floor
        }
        self.synthesis_history.append(record)
        if len(self.synthesis_history) > 20:
            self.synthesis_history.pop(0)
        
        quality_name = QUALITY_NAMES.get(target_quality, target_quality)
        return True, f'合成成功！获得{quality_name} {new_equip.name}！', new_equip
    
    def bulk_synthesize(self, quality, inventory, floor=1):
        results = []
        total_synthesized = 0
        
        while self.can_synthesize(quality, inventory):
            success, message, equip = self.synthesize(quality, inventory, floor)
            if success:
                total_synthesized += 1
                results.append(message)
                if equip:
                    inventory.append(equip)
            else:
                break
        
        if total_synthesized > 0:
            return True, f'批量合成完成！共合成{total_synthesized}件装备', results
        return False, '没有可合成的装备', []
    
    def get_synthesis_history(self):
        return self.synthesis_history
