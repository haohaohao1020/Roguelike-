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
    def __init__(self, x, y, name, slot):
        super().__init__(x, y, name, 'equipment')
        self.slot = slot
        self.stats = {}
        self.generate_stats()
    
    def generate_stats(self):
        quality_multipliers = {
            'common': 1.0,
            'uncommon': 1.5,
            'rare': 2.0,
            'epic': 2.5,
            'legendary': 3.5
        }
        mult = quality_multipliers[self.quality]
        
        if self.slot == 'weapon':
            self.stats['damage'] = int(random.randint(5, 15) * mult)
            self.stats['str'] = int(random.randint(0, 3) * mult)
        elif self.slot == 'armor':
            self.stats['defense'] = int(random.randint(5, 15) * mult)
            self.stats['hp'] = int(random.randint(10, 30) * mult)
        elif self.slot == 'helmet':
            self.stats['defense'] = int(random.randint(3, 10) * mult)
            self.stats['mp'] = int(random.randint(5, 20) * mult)
        elif self.slot == 'boots':
            self.stats['defense'] = int(random.randint(2, 8) * mult)
            self.stats['dex'] = int(random.randint(0, 3) * mult)
        elif self.slot == 'accessory':
            stat_choices = ['str', 'dex', 'int', 'hp', 'mp']
            for _ in range(random.randint(1, 3)):
                stat = random.choice(stat_choices)
                self.stats[stat] = int(random.randint(2, 8) * mult)
        
        self.value = int(self.value * mult)

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

class Chest(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, '宝箱', GOLD)
        self.is_open = False
        self.items = []
        self.blocks_movement = True
    
    def open(self, user):
        if not self.is_open:
            self.is_open = True
            if random.random() < 0.7:
                gold = Gold(self.x, self.y, random.randint(10, 50))
                user.gold += gold.amount
            if random.random() < 0.5:
                potion = Potion(self.x, self.y, random.choice(['health', 'mana']))
                user.add_item(potion)
            if random.random() < 0.3:
                equip = create_random_equipment(self.x, self.y)
                user.add_item(equip)
            return '打开了宝箱！'
        return '宝箱已经打开过了'

def create_random_equipment(x, y):
    slot = random.choice(EQUIPMENT_SLOTS)
    names = {
        'weapon': ['短剑', '长剑', '战斧', '战锤', '魔杖'],
        'armor': ['皮甲', '锁子甲', '板甲', '法袍'],
        'helmet': ['皮帽', '铁盔', '头盔', '法师帽'],
        'boots': ['皮靴', '铁靴', '速度之靴'],
        'accessory': ['戒指', '护符', '项链', '徽章']
    }
    name = random.choice(names[slot])
    equip = Equipment(x, y, name, slot)
    
    qualities = ['common', 'common', 'common', 'uncommon', 'uncommon', 'rare', 'epic', 'legendary']
    equip.quality = random.choice(qualities)
    equip.generate_stats()
    
    return equip

def create_random_item(x, y):
    item_type = random.choice(['potion', 'scroll', 'equipment', 'gold'])
    if item_type == 'potion':
        return Potion(x, y, random.choice(['health', 'mana']))
    elif item_type == 'scroll':
        return Scroll(x, y)
    elif item_type == 'equipment':
        return create_random_equipment(x, y)
    elif item_type == 'gold':
        return Gold(x, y, random.randint(5, 30))
    return None
