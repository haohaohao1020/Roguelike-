import json
import os
import pickle
import random
from .config import *

class SaveManager:
    def __init__(self):
        self.save_file = os.path.join(SAVES_DIR, 'game_save.pkl')
        self.leaderboard_file = os.path.join(SAVES_DIR, 'leaderboard.json')
    
    def save_game(self, game_state):
        try:
            with open(self.save_file, 'wb') as f:
                pickle.dump(game_state, f)
            return True
        except Exception as e:
            print(f'保存失败: {e}')
            return False
    
    def load_game(self):
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f'读取失败: {e}')
        return None
    
    def has_save(self):
        return os.path.exists(self.save_file)
    
    def delete_save(self):
        if os.path.exists(self.save_file):
            os.remove(self.save_file)
    
    def get_leaderboard(self):
        try:
            if os.path.exists(self.leaderboard_file):
                with open(self.leaderboard_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_score(self, name, score, floor):
        leaderboard = self.get_leaderboard()
        leaderboard.append({
            'name': name,
            'score': score,
            'floor': floor
        })
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        leaderboard = leaderboard[:10]
        
        try:
            with open(self.leaderboard_file, 'w', encoding='utf-8') as f:
                json.dump(leaderboard, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

class Shop:
    def __init__(self):
        self.inventory = []
        self.refresh_count = 0
        self.discount = 1.0
        self.bargain_attempts = 0
        self.max_bargain_attempts = 3
        self.is_mysterious = False
        self.gamble_prices = {
            'common': 50,
            'uncommon': 150,
            'rare': 400,
            'epic': 1000
        }
        self.refresh_items()
    
    def refresh_items(self, game_mode='single', floor=1):
        self.inventory = []
        self.refresh_count = 0
        self.bargain_attempts = 0
        
        self.discount = 1.0
        if random.random() < 0.3:
            self.discount = random.choice([0.7, 0.8, 0.9])
        
        from .items import create_random_equipment, Potion, Scroll, ReviveScroll, TeleportAnchor, RespecBook, SummonCard
        
        equip_count = 3 if not self.is_mysterious else 2
        for _ in range(equip_count):
            equip = create_random_equipment(0, 0, floor)
            equip.value = int(equip.value * 3)
            if self.is_mysterious:
                equip.value = int(equip.value * 1.5)
            self.inventory.append(equip)
        
        for _ in range(4):
            potion = Potion(0, 0)
            self.inventory.append(potion)
        
        for _ in range(2):
            scroll = Scroll(0, 0)
            self.inventory.append(scroll)
        
        special_items = [
            TeleportAnchor(0, 0),
            RespecBook(0, 0),
            SummonCard(0, 0)
        ]
        for item in special_items:
            if random.random() < 0.5:
                self.inventory.append(item)
        
        if game_mode == 'coop':
            revive_scroll = ReviveScroll(0, 0)
            self.inventory.append(revive_scroll)
        
        if self.is_mysterious:
            mythic_equip = create_random_equipment(0, 0, floor)
            mythic_equip.quality = 'mythic'
            mythic_equip.generate_stats()
            mythic_equip.generate_sub_stats()
            mythic_equip.generate_rune_slots()
            mythic_equip.generate_set()
            mythic_equip.calculate_value()
            mythic_equip.value = max(600, mythic_equip.value * 2)
            mythic_equip.name = f'传说的{mythic_equip.name}'
            self.inventory.append(mythic_equip)
            
            revive_scroll = ReviveScroll(0, 0)
            revive_scroll.value = 600
            self.inventory.append(revive_scroll)
            
            summon_card = SummonCard(0, 0)
            summon_card.value = 550
            self.inventory.append(summon_card)
    
    def get_refresh_cost(self):
        return 50 + self.refresh_count * 30
    
    def manual_refresh(self, player, game_mode='single', floor=1):
        cost = self.get_refresh_cost()
        if player.gold >= cost:
            player.gold -= cost
            self.refresh_count += 1
            self.refresh_items(game_mode, floor)
            return True, f'花费{cost}金币刷新了商品！'
        return False, '金币不足！'
    
    def gamble_equipment(self, player, target_quality, floor=1):
        price = self.gamble_prices.get(target_quality, 100)
        if player.gold < price:
            return False, '金币不足！', None
        
        player.gold -= price
        
        quality_weights = {
            'common': [70, 25, 4, 1, 0],
            'uncommon': [30, 45, 20, 4, 1],
            'rare': [10, 25, 40, 20, 5],
            'epic': [5, 15, 25, 35, 20]
        }
        weights = quality_weights.get(target_quality, [60, 25, 10, 4, 1])
        qualities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
        result_quality = random.choices(qualities, weights=weights, k=1)[0]
        
        from .items import create_random_equipment
        equip = create_random_equipment(0, 0, floor)
        equip.quality = result_quality
        equip.generate_stats()
        equip.generate_sub_stats()
        equip.generate_rune_slots()
        equip.generate_set()
        equip.calculate_value()
        
        quality_name = QUALITY_NAMES.get(result_quality, '普通')
        if player.add_item(equip):
            return True, f'赌出了{quality_name} {equip.name}！', equip
        return False, '背包已满！', equip
    
    def bargain(self, player, item):
        if self.bargain_attempts >= self.max_bargain_attempts:
            return False, '砍价次数已用完！'
        
        self.bargain_attempts += 1
        
        success_chance = 0.4 + (player.level * 0.02)
        
        if random.random() < success_chance:
            reduction = random.uniform(0.1, 0.25)
            item.value = int(item.value * (1 - reduction))
            return True, f'砍价成功！价格降低了{int(reduction * 100)}%！'
        else:
            increase = random.uniform(0.05, 0.15)
            item.value = int(item.value * (1 + increase))
            return False, f'砍价失败！价格上涨了{int(increase * 100)}%...'
    
    def get_item_price(self, item):
        return int(item.value * self.discount)
    
    def buy(self, player, item):
        price = self.get_item_price(item)
        if player.gold >= price:
            if player.add_item(item):
                player.gold -= price
                self.inventory.remove(item)
                return True, f'购买了 {item.name}！花费{price}金币'
            return False, '背包已满！'
        return False, '金币不足！'
    
    def sell(self, player, item):
        if item in player.inventory:
            player.remove_item(item)
            sell_price = int(item.value // 2)
            player.gold += sell_price
            return True, f'出售了 {item.name}，获得 {sell_price} 金币！'
        return False, '没有这个物品！'
