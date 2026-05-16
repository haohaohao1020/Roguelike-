import random
from .config import *

class CombatSystem:
    def __init__(self):
        self.log = []
    
    def attack(self, attacker, target):
        if hasattr(attacker, 'attack'):
            attacker.attack()
        
        attack_power = attacker.get_attack_power() if hasattr(attacker, 'get_attack_power') else attacker.damage
        evasion = target.get_evasion() if hasattr(target, 'get_evasion') else target.evasion
        
        if random.randint(0, 100) < evasion:
            self.add_log(f'{target.name} 闪避了攻击！')
            return False
        
        damage = attack_power + random.randint(-5, 5)
        damage = max(1, damage)
        
        if hasattr(target, 'take_damage'):
            actual_damage = target.take_damage(damage)
        else:
            target.hp -= damage
            actual_damage = damage
        
        self.add_log(f'{attacker.name} 对 {target.name} 造成了伤害！')
        
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
        
        self.add_log(f'{caster.name} 使用 {spell_name}！')
        
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
            self.add_log(f'{killer.name} 获得了经验！')
        
        if hasattr(killer, 'gold') and hasattr(victim, 'gold'):
            killer.gold += victim.gold
            self.add_log(f'{killer.name} 获得了金币！')
    
    def use_skill(self, user, skill_name, target=None):
        if skill_name == 'power_strike':
            if user.mp >= 10 and target:
                user.mp -= 10
                damage = user.get_attack_power() * 2
                actual = target.take_damage(damage)
                self.add_log(f'{user.name} 使用强力一击！')
        elif skill_name == 'fireball':
            if user.mp >= 20 and target:
                user.mp -= 20
                self.magic_attack(user, target, '火球术', 30)
        elif skill_name == 'backstab':
            if user.mp >= 15 and target:
                user.mp -= 15
                damage = user.get_attack_power() * 3
                actual = target.take_damage(damage)
                self.add_log(f'{user.name} 使用背刺！')
        
        return True
    
    def add_log(self, message):
        self.log.append(message)
        if len(self.log) > 10:
            self.log.pop(0)
    
    def update(self):
        pass
