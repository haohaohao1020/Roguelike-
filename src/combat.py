import random
from .config import *

class CombatSystem:
    def __init__(self):
        self.damage_numbers = []
        self.effects = []
        self.log = []
    
    def attack(self, attacker, target):
        if hasattr(attacker, 'attack'):
            attacker.attack()
        
        attack_power = attacker.get_attack_power() if hasattr(attacker, 'get_attack_power') else attacker.damage
        evasion = target.get_evasion() if hasattr(target, 'get_evasion') else target.evasion
        
        if random.randint(0, 100) < evasion:
            self.add_log(f'{target.name} 闪避了攻击！')
            self.add_damage_number(target.x, target.y, 'MISS', GRAY)
            return False
        
        damage = attack_power + random.randint(-5, 5)
        damage = max(1, damage)
        
        if hasattr(target, 'take_damage'):
            actual_damage = target.take_damage(damage)
        else:
            target.hp -= damage
            actual_damage = damage
        
        self.add_log(f'{attacker.name} 对 {target.name} 造成了 {actual_damage} 点伤害！')
        self.add_damage_number(target.x, target.y, str(actual_damage), RED)
        
        if hasattr(target, 'is_alive'):
            if not target.is_alive():
                self.handle_death(attacker, target)
        elif target.hp <= 0:
            self.handle_death(attacker, target)
        
        return True
    
    def magic_attack(self, caster, target, spell_name, base_damage):
        magic_power = caster.get_magic_power() if hasattr(caster, 'get_magic_power') else base_damage
        damage = int((magic_power + base_damage) * (0.8 + random.random() * 0.4))
        
        if hasattr(target, 'take_damage'):
            actual_damage = target.take_damage(damage)
        else:
            target.hp -= damage
            actual_damage = damage
        
        self.add_log(f'{caster.name} 使用 {spell_name} 对 {target.name} 造成了 {actual_damage} 点伤害！')
        self.add_damage_number(target.x, target.y, str(actual_damage), BLUE)
        self.add_effect(target.x, target.y, 'magic')
        
        if hasattr(target, 'is_alive'):
            if not target.is_alive():
                self.handle_death(caster, target)
        elif target.hp <= 0:
            self.handle_death(caster, target)
        
        return True
    
    def handle_death(self, killer, victim):
        self.add_log(f'{victim.name} 被击败了！')
        
        if hasattr(killer, 'gain_exp') and hasattr(victim, 'exp'):
            killer.gain_exp(victim.exp)
            self.add_log(f'{killer.name} 获得了 {victim.exp} 点经验！')
        
        if hasattr(killer, 'gold') and hasattr(victim, 'gold'):
            killer.gold += victim.gold
            self.add_log(f'{killer.name} 获得了 {victim.gold} 金币！')
    
    def use_skill(self, user, skill_name, target=None):
        if skill_name == 'power_strike':
            if user.mp >= 10:
                user.mp -= 10
                if target:
                    damage = user.get_attack_power() * 2
                    actual = target.take_damage(damage)
                    self.add_log(f'{user.name} 使用强力一击造成了 {actual} 点伤害！')
                    self.add_damage_number(target.x, target.y, str(actual), ORANGE)
        elif skill_name == 'fireball':
            if user.mp >= 20:
                user.mp -= 20
                if target:
                    self.magic_attack(user, target, '火球术', 30)
        elif skill_name == 'backstab':
            if user.mp >= 15:
                user.mp -= 15
                if target:
                    damage = user.get_attack_power() * 3
                    actual = target.take_damage(damage)
                    self.add_log(f'{user.name} 使用背刺造成了 {actual} 点伤害！')
                    self.add_damage_number(target.x, target.y, str(actual), YELLOW)
        
        return True
    
    def add_damage_number(self, x, y, text, color):
        self.damage_numbers.append({
            'x': x, 'y': y, 'text': text, 'color': color,
            'timer': 60, 'offset_y': 0
        })
    
    def add_effect(self, x, y, effect_type):
        self.effects.append({
            'x': x, 'y': y, 'type': effect_type, 'timer': 30, 'frame': 0
        })
    
    def add_log(self, message):
        self.log.append(message)
        if len(self.log) > 10:
            self.log.pop(0)
    
    def update(self):
        for dn in self.damage_numbers[:]:
            dn['timer'] -= 1
            dn['offset_y'] -= 1
            if dn['timer'] <= 0:
                self.damage_numbers.remove(dn)
        
        for ef in self.effects[:]:
            ef['timer'] -= 1
            ef['frame'] += 1
            if ef['timer'] <= 0:
                self.effects.remove(ef)
