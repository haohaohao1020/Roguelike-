import json
import os
import pickle
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
        self.refresh_items()
    
    def refresh_items(self):
        self.inventory = []
        from .items import create_random_equipment, Potion, Scroll
        
        for _ in range(3):
            equip = create_random_equipment(0, 0)
            equip.value = int(equip.value * 3)
            self.inventory.append(equip)
        
        for _ in range(4):
            potion = Potion(0, 0)
            self.inventory.append(potion)
        
        for _ in range(2):
            scroll = Scroll(0, 0)
            self.inventory.append(scroll)
    
    def buy(self, player, item):
        if player.gold >= item.value:
            if player.add_item(item):
                player.gold -= item.value
                self.inventory.remove(item)
                return True, f'购买了 {item.name}！'
            return False, '背包已满！'
        return False, '金币不足！'
    
    def sell(self, player, item):
        if item in player.inventory:
            player.remove_item(item)
            player.gold += int(item.value // 2)
            return True, f'出售了 {item.name}，获得 {item.value // 2} 金币！'
        return False, '没有这个物品！'
