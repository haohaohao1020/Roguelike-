import random
from .config import *

class DamageNumber:
    def __init__(self, x, y, damage, is_crit=False, is_heal=False, color=None):
        self.x = x
        self.y = y
        self.damage = damage
        self.is_crit = is_crit
        self.is_heal = is_heal
        self.color = color
        self.life = 60
        self.vy = -2
        self.alpha = 255
    
    def update(self):
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1
        if self.life < 30:
            self.alpha = int(255 * (self.life / 30))
        return self.life > 0

class CombatSystem:
    def __init__(self):
        self.log = []
        self.damage_numbers = []
        self.skill_effects = []
    
    def add_damage_number(self, x, y, damage, is_crit=False, is_heal=False, color=None):
        num = DamageNumber(x, y, damage, is_crit, is_heal, color)
        self.damage_numbers.append(num)
    
    def add_skill_effect(self, effect_type, x, y, duration=30):
        self.skill_effects.append({
            'type': effect_type,
            'x': x,
            'y': y,
            'life': duration,
            'max_life': duration
        })
    
    def attack(self, attacker, target):
        if hasattr(attacker, 'attack'):
            attacker.attack()
        
        attack_power = attacker.get_attack_power() if hasattr(attacker, 'get_attack_power') else attacker.damage
        evasion = target.get_evasion() if hasattr(target, 'get_evasion') else target.evasion
        
        if hasattr(attacker, 'is_invisible') and attacker.is_invisible:
            evasion = 0
        
        if random.randint(0, 100) < evasion:
            self.add_log(f'{target.name} 闪避了攻击！')
            return False
        
        damage = attack_power + random.randint(-5, 5)
        
        is_crit = False
        crit_chance = attacker.get_total_critical_chance() if hasattr(attacker, 'get_total_critical_chance') else 5
        if hasattr(attacker, 'is_berserk') and attacker.is_berserk:
            crit_chance += 30
        
        if random.randint(0, 100) < crit_chance:
            is_crit = True
            crit_damage = attacker.get_total_critical_damage() if hasattr(attacker, 'get_total_critical_damage') else 150
            damage = int(damage * crit_damage / 100)
            if hasattr(attacker, 'is_berserk') and attacker.is_berserk:
                damage = int(damage * 1.5)
        
        damage = max(1, damage)
        
        if hasattr(target, 'take_damage'):
            actual_damage = target.take_damage(damage)
        else:
            target.hp -= damage
            actual_damage = damage
        
        if hasattr(attacker, 'get_lifesteal'):
            lifesteal = attacker.get_lifesteal() / 100
            if lifesteal > 0 and hasattr(attacker, 'heal'):
                heal_amount = int(actual_damage * lifesteal)
                attacker.heal(heal_amount)
                self.add_log(f'{attacker.name} 吸血 {heal_amount} 点生命！')
        
        self.add_damage_number(target.x, target.y, actual_damage, is_crit)
        
        crit_text = '暴击！' if is_crit else ''
        self.add_log(f'{attacker.name} 对 {target.name} 造成了 {actual_damage} 点伤害！{crit_text}')
        
        if hasattr(target, 'is_alive'):
            if not target.is_alive():
                self.handle_death(attacker, target)
        elif target.hp <= 0:
            self.handle_death(attacker, target)
        
        return True
    
    def handle_death(self, killer, victim):
        self.add_log(f'💀 {victim.name} 被击败了！')
        
        if hasattr(victim, 'drop_loot') and hasattr(killer, 'add_item'):
            if victim.monster_type in ['elite', 'boss', 'normal']:
                drops = victim.drop_loot()
                for drop in drops:
                    if killer.add_item(drop):
                        quality_name = QUALITY_NAMES.get(drop.quality, '普通')
                        self.add_log(f'💎 {victim.name} 掉落了 {quality_name} {drop.name}！已存入背包！')
                    else:
                        quality_name = QUALITY_NAMES.get(drop.quality, '普通')
                        self.add_log(f'📦 {victim.name} 掉落了 {quality_name} {drop.name}！背包已满！')
        
        if hasattr(killer, 'gain_exp') and hasattr(victim, 'exp'):
            killer.gain_exp(victim.exp)
            self.add_log(f'✨ {killer.name} 获得了 {victim.exp} 经验！')
        
        if hasattr(killer, 'gold') and hasattr(victim, 'gold'):
            killer.gold += victim.gold
            self.add_log(f'💰 {killer.name} 获得了 {victim.gold} 金币！')
    
    def use_basic_skill(self, user, target=None, all_enemies=None, allies=None):
        can_use, message = user.can_use_skill('basic')
        if not can_use:
            self.add_log(f'无法释放技能：{message}')
            return False
        
        skill_data = SKILLS[user.class_type]['basic']
        success = False
        
        if user.class_type == 'warrior':
            success = self._warrior_basic(user, target, skill_data)
        elif user.class_type == 'mage':
            success = self._mage_basic(user, target, skill_data)
        elif user.class_type == 'rogue':
            success = self._rogue_basic(user, target, skill_data)
        elif user.class_type == 'paladin':
            success = self._paladin_basic(user, skill_data, allies)
        
        if success:
            user.use_skill_mp('basic')
            self.add_skill_effect(f'{user.class_type}_basic', user.x, user.y)
        
        return success
    
    def use_ultimate_skill(self, user, target=None, all_enemies=None, allies=None):
        can_use, message = user.can_use_skill('ultimate')
        if not can_use:
            self.add_log(f'无法释放大招：{message}')
            return False
        
        skill_data = SKILLS[user.class_type]['ultimate']
        success = False
        
        if user.class_type == 'warrior':
            success = self._warrior_ultimate(user, target, skill_data)
        elif user.class_type == 'mage':
            success = self._mage_ultimate(user, all_enemies, skill_data)
        elif user.class_type == 'rogue':
            success = self._rogue_ultimate(user, target, skill_data)
        elif user.class_type == 'paladin':
            success = self._paladin_ultimate(user, all_enemies, allies, skill_data)
        
        if success:
            user.use_skill_mp('ultimate')
            self.add_skill_effect(f'{user.class_type}_ultimate', user.x, user.y, 60)
        
        return success
    
    def _warrior_basic(self, user, target, skill_data):
        if not target or target.get_distance_to(user) > skill_data['range']:
            self.add_log('目标不在攻击范围内！')
            return False
        
        self.add_log(f'{user.name} 使用 破甲猛击！')
        
        base_damage = user.get_total_physical_attack() * skill_data['damage_multiplier']
        is_crit = random.randint(0, 100) < user.get_total_critical_chance()
        
        if is_crit:
            crit_damage = user.get_total_critical_damage()
            base_damage = int(base_damage * crit_damage / 100)
        
        armor_reduction = target.get_total_defense() * skill_data['armor_reduction']
        damage = max(1, int(base_damage - (target.get_total_defense() - armor_reduction) // 2))
        actual = target.take_damage(damage)
        
        target_id = id(target)
        user.armor_reduction_targets[target_id] = {
            'amount': skill_data['armor_reduction'],
            'duration': skill_data['armor_reduction_duration']
        }
        
        lifesteal_amount = int(actual * skill_data['lifesteal'])
        user.heal(lifesteal_amount)
        
        self.add_damage_number(target.x, target.y, actual, is_crit, color=(255, 100, 50))
        self.add_log(f'造成 {actual} 点伤害，降低目标30%防御，吸血 {lifesteal_amount}！')
        
        if hasattr(target, 'is_alive') and not target.is_alive():
            self.handle_death(user, target)
        
        return True
    
    def _warrior_ultimate(self, user, target, skill_data):
        if not target or target.get_distance_to(user) > skill_data['range']:
            self.add_log('目标不在攻击范围内！')
            return False
        
        self.add_log(f'{user.name} 使用 狂怒碎山斩！')
        
        base_damage = user.get_total_physical_attack() * skill_data['damage_multiplier']
        is_crit = random.randint(0, 100) < (user.get_total_critical_chance() + skill_data['berserk_crit_bonus'])
        
        if is_crit:
            crit_damage = user.get_total_critical_damage()
            base_damage = int(base_damage * crit_damage / 100)
        
        damage = max(1, int(base_damage - target.get_total_defense() // 2))
        actual = target.take_damage(damage)
        
        user.is_berserk = True
        user.berserk_duration = skill_data['berserk_duration']
        
        self.add_damage_number(target.x, target.y, actual, True, color=(255, 50, 0))
        self.add_log(f'造成 {actual} 点巨额伤害！进入狂暴状态！')
        
        if hasattr(target, 'is_alive') and not target.is_alive():
            self.handle_death(user, target)
        
        return True
    
    def _mage_basic(self, user, target, skill_data):
        if not target or target.get_distance_to(user) > skill_data['range']:
            self.add_log('目标不在攻击范围内！')
            return False
        
        self.add_log(f'{user.name} 使用 烈焰弹！')
        
        base_damage = user.get_total_magic_attack() * skill_data['damage_multiplier']
        damage = max(1, int(base_damage - target.get_total_magic_defense() // 2))
        actual = target.take_damage(damage)
        
        target.add_status('burning', skill_data['burn_duration'], skill_data['burn_damage'])
        
        self.add_damage_number(target.x, target.y, actual, color=(255, 150, 0))
        self.add_log(f'造成 {actual} 点火焰伤害，目标被灼烧！')
        
        if hasattr(target, 'is_alive') and not target.is_alive():
            self.handle_death(user, target)
        
        return True
    
    def _mage_ultimate(self, user, all_enemies, skill_data):
        self.add_log(f'{user.name} 使用 陨星天火！')
        
        total_damage = 0
        for enemy in all_enemies:
            if enemy.is_alive():
                base_damage = user.get_total_magic_attack() * skill_data['damage_multiplier']
                damage = max(1, int(base_damage - enemy.get_total_magic_defense() // 2))
                actual = enemy.take_damage(damage)
                
                enemy.add_status('burning', skill_data['burn_duration'], skill_data['burn_damage'])
                enemy.add_status('slowed', skill_data['slow_duration'], 0)
                
                self.add_damage_number(enemy.x, enemy.y, actual, color=(255, 100, 0))
                total_damage += actual
                
                if not enemy.is_alive():
                    self.handle_death(user, enemy)
        
        self.add_log(f'对所有敌人造成共 {total_damage} 点伤害！全体灼烧并减速！')
        return True
    
    def _rogue_basic(self, user, target, skill_data):
        if not target or target.get_distance_to(user) > skill_data['range']:
            self.add_log('目标不在攻击范围内！')
            return False
        
        self.add_log(f'{user.name} 使用 暗影突袭！')
        
        base_damage = user.get_total_physical_attack() * skill_data['damage_multiplier']
        is_crit = True
        
        crit_damage = user.get_total_critical_damage()
        base_damage = int(base_damage * crit_damage / 100)
        
        damage = max(1, int(base_damage - target.get_total_defense() // 2))
        actual = target.take_damage(damage)
        
        user.evasion_bonus += skill_data['evasion_bonus']
        user.evasion_bonus_duration = skill_data['evasion_duration']
        
        self.add_damage_number(target.x, target.y, actual, is_crit, color=(100, 255, 100))
        self.add_log(f'背刺造成 {actual} 点暴击伤害！闪避率提升！')
        
        if hasattr(target, 'is_alive') and not target.is_alive():
            self.handle_death(user, target)
        
        return True
    
    def _rogue_ultimate(self, user, target, skill_data):
        if not target or target.get_distance_to(user) > skill_data['range']:
            self.add_log('目标不在攻击范围内！')
            return False 
        
        self.add_log(f'{user.name} 使用 影杀千刃！')
        
        user.is_invisible = True
        user.invisible_duration = skill_data['invisible_duration']
        
        total_damage = 0
        hit_count = skill_data['hit_count']
        for i in range(hit_count):
            if not target.is_alive():
                break
            
            base_damage = user.get_total_physical_attack() * skill_data['damage_multiplier']
            is_crit = random.randint(0, 100) < (user.get_total_critical_chance() + 30)
            
            if is_crit:
                crit_damage = user.get_total_critical_damage()
                base_damage = int(base_damage * crit_damage / 100)
            
            effective_defense = target.get_total_defense() * (1 - skill_data['defense_ignore'])
            damage = max(1, int(base_damage - effective_defense // 2))
            actual = target.take_damage(damage)
            total_damage += actual
            
            self.add_damage_number(target.x + random.uniform(-0.3, 0.3), 
                                   target.y + random.uniform(-0.3, 0.3), 
                                   actual, is_crit, color=(150, 255, 150))
        
        user.speed_bonus = skill_data['speed_bonus']
        user.speed_bonus_duration = skill_data['speed_duration']
        user.crit_damage_bonus = skill_data['crit_damage_bonus']
        user.crit_damage_bonus_duration = skill_data['crit_damage_duration']
        
        self.add_log(f'连击造成共 {total_damage} 点伤害！隐身并提升移速和暴伤！')
        
        if hasattr(target, 'is_alive') and not target.is_alive():
            self.handle_death(user, target)
        
        return True
    
    def _paladin_basic(self, user, skill_data, allies=None):
        self.add_log(f'{user.name} 使用 神圣庇护！')
        
        user.shield += skill_data['shield_amount']
        user.shield_duration = max(user.shield_duration, skill_data['shield_duration'])
        
        if allies:
            for ally in allies:
                if ally != user and ally.is_alive():
                    if hasattr(ally, 'shield'):
                        ally.shield += int(skill_data['shield_amount'] * 0.5)
        
        self.add_log(f'获得 {skill_data["shield_amount"]} 点神圣护盾！')
        return True
    
    def _paladin_ultimate(self, user, all_enemies, allies, skill_data):
        self.add_log(f'{user.name} 使用 圣光审判！')
        
        total_damage = 0
        for enemy in all_enemies:
            if enemy.is_alive():
                base_damage = (user.get_total_physical_attack() + user.get_total_magic_attack()) * skill_data['damage_multiplier'] / 2
                damage = max(1, int(base_damage))
                actual = enemy.take_damage(damage)
                self.add_damage_number(enemy.x, enemy.y, actual, color=(255, 255, 150))
                total_damage += actual
                
                if not enemy.is_alive():
                    self.handle_death(user, enemy)
        
        heal_amount = int(user.get_total_max_hp() * skill_data['heal_amount'])
        user.heal(heal_amount)
        self.add_damage_number(user.x, user.y, heal_amount, is_heal=True, color=(150, 255, 150))
        
        if allies:
            for ally in allies:
                if ally != user and ally.is_alive():
                    ally.heal(int(heal_amount * 0.5))
                    self.add_damage_number(ally.x, ally.y, int(heal_amount * 0.5), is_heal=True, color=(150, 255, 150))
        
        user.clear_negative_status()
        
        self.add_log(f'造成 {total_damage} 点神圣伤害，恢复 {heal_amount} 点生命！清除负面状态！')
        return True
    
    def add_log(self, message):
        self.log.append(message)
        if len(self.log) > 10:
            self.log.pop(0)
    
    def update(self):
        self.damage_numbers = [d for d in self.damage_numbers if d.update()]
        for e in self.skill_effects:
            e['life'] -= 1
        self.skill_effects = [e for e in self.skill_effects if e['life'] > 0]
