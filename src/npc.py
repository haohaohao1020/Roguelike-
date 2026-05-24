import random
from .config import *
from .entity import Entity
from .items import create_random_equipment, Gold, Potion, Rune, Material, Item

class QuestItem(Item):
    def __init__(self, x, y, quest_id, item_name, item_type='quest'):
        super().__init__(x, y, item_name, 'quest_item')
        self.quest_id = quest_id
        self.quest_item_type = item_type
        self.color = (255, 200, 100)
    
    def get_color(self):
        return self.color

class DeliveryLetter(Item):
    def __init__(self, x, y, target_floor, target_npc_name):
        super().__init__(x, y, '重要信件', 'delivery_letter')
        self.target_floor = target_floor
        self.target_npc_name = target_npc_name
        self.color = (200, 200, 255)
    
    def get_color(self):
        return self.color

class NPC(Entity):
    def __init__(self, x, y, npc_type='merchant'):
        name = random.choice(NPC_NAMES)
        super().__init__(x, y, name, (100, 150, 200))
        self.npc_type = npc_type
        self.blocks_movement = True
        self.quests = []
        self.dialogue = self.generate_dialogue()
        self.is_interacting = False
        self.floor = 1
    
    def generate_dialogue(self):
        dialogues = {
            'merchant': [
                '欢迎光临！看看我的货物吧~',
                '这些都是稀世珍宝哦！',
                '朋友，要买点什么吗？'
            ],
            'hunter': [
                '这片地牢可不安全...',
                '要一起猎杀怪物吗？',
                '我听说深处有强大的Boss...'
            ],
            'mage': [
                '魔法的奥秘无穷无尽...',
                '需要我帮你做点什么吗？',
                '小心那些黑暗生物。'
            ],
            'healer': [
                '愿圣光保佑你，冒险者。',
                '需要治疗吗？我可以帮你。',
                '保持希望，光明终将到来。'
            ]
        }
        return random.choice(dialogues.get(self.npc_type, ['你好，冒险者！']))
    
    def can_offer_quest(self):
        return len(self.quests) < 3
    
    def interact(self, player, game=None):
        return self.dialogue

class Quest:
    def __init__(self, quest_type, floor=1):
        self.quest_type = quest_type
        self.floor = floor
        self.quest_id = f"{quest_type}_{floor}_{random.randint(1000, 9999)}"
        self.quest_name = self.generate_name()
        self.name = self.quest_name
        self.description = ''
        self.rewards = []
        self.is_accepted = False
        self.is_completed = False
        self.is_abandoned = False
        self.is_failed = False
        self.progress = 0
        self.target = 1
        self.target_data = {}
        self.target_positions = []
        self.is_floor_locked = False
        self.spawned_items = []
        self.generate_quest()
    
    def generate_name(self):
        names = TASK_NAMES.get(self.quest_type, ['未知任务'])
        return random.choice(names)
    
    def generate_quest(self):
        if self.quest_type == 'delivery':
            self.generate_delivery_quest()
        elif self.quest_type == 'hunt':
            self.generate_hunt_quest()
        elif self.quest_type == 'collect':
            self.generate_collect_quest()
        self.generate_rewards()
    
    def generate_delivery_quest(self):
        self.is_floor_locked = True
        target_npc_name = random.choice(NPC_NAMES)
        self.description = f'将重要信件交给本层的 {target_npc_name}'
        self.target = 1
        self.target_data = {
            'item_name': '重要信件',
            'target_floor': self.floor,
            'target_npc': target_npc_name
        }
    
    def generate_hunt_quest(self):
        self.is_floor_locked = False
        monster_counts = [3, 5, 8, 10]
        self.target = random.choice(monster_counts)
        monster_type = random.choice(list(MONSTER_NAMES_CN.keys()))
        monster_name = MONSTER_NAMES_CN.get(monster_type, '怪物')
        self.description = f'击杀 {self.target} 只 {monster_name}'
        self.target_data = {
            'monster_type': monster_type,
            'monster_name': monster_name
        }
    
    def generate_collect_quest(self):
        self.is_floor_locked = True
        collect_items = ['神秘碎片', '古老宝石', '魔法结晶', '稀有矿石', '符文残片']
        item = random.choice(collect_items)
        self.target = random.randint(3, 6)
        self.description = f'在本层收集 {self.target} 个 {item}'
        self.target_data = {
            'item_type': item,
            'item_name': item
        }
    
    def generate_rewards(self):
        base_reward = int(50 * self.floor)
        gold_reward = Gold(0, 0, int(base_reward * (1 + self.target * 0.1)))
        self.rewards.append(gold_reward)
        
        if random.random() < 0.5:
            potion = Potion(0, 0, random.choice(['health', 'mana']))
            self.rewards.append(potion)
        
        if random.random() < 0.3:
            equip = create_random_equipment(0, 0, self.floor)
            self.rewards.append(equip)
        
        if random.random() < 0.2:
            rune_type = random.choice(RUNE_TYPES)
            rune = Rune(0, 0, rune_type, 1)
            self.rewards.append(rune)
        
        if random.random() < 0.1 and self.floor >= 5:
            material = Material(0, 0, 'enhance_stone', random.randint(1, 3))
            self.rewards.append(material)
    
    def update_progress(self, data=None):
        if self.is_completed or not self.is_accepted:
            return
        
        if self.quest_type == 'hunt':
            if data and 'monster_type' in data:
                if data['monster_type'] == self.target_data.get('monster_type'):
                    self.progress += 1
        
        elif self.quest_type == 'collect':
            self.progress += 1
        
        elif self.quest_type == 'delivery':
            if data and 'floor' in data:
                if data['floor'] == self.target_data.get('target_floor'):
                    self.progress = 1
        
        if self.progress >= self.target:
            self.is_completed = True
    
    def get_reward_text(self):
        reward_texts = []
        for reward in self.rewards:
            if hasattr(reward, 'amount') and reward.item_type == 'gold':
                reward_texts.append(f'{reward.amount} 金币')
            else:
                reward_texts.append(reward.name)
        return ', '.join(reward_texts)
    
    def abandon(self):
        self.is_abandoned = True
        self.is_accepted = False
    
    def accept(self):
        self.is_accepted = True
        self.progress = 0
    
    def can_complete(self):
        return self.is_accepted and self.progress >= self.target
    
    def get_progress_text(self):
        if self.is_failed:
            return '任务失败'
        if self.quest_type == 'hunt':
            monster_name = self.target_data.get('monster_name', '怪物')
            return f'击杀 {self.progress}/{self.target} {monster_name}'
        elif self.quest_type == 'collect':
            item_type = self.target_data.get('item_type', '物品')
            return f'收集 {self.progress}/{self.target} {item_type}'
        elif self.quest_type == 'delivery':
            return '送信任务' if self.progress == 0 else '已送达'
        return f'{self.progress}/{self.target}'
    
    def set_target_position(self, x, y):
        self.target_positions = [(x, y)]
    
    def set_target_positions(self, positions):
        self.target_positions = positions
    
    def fail(self):
        self.is_failed = True
        self.is_accepted = False
    
    def is_active(self):
        return self.is_accepted and not self.is_completed and not self.is_abandoned and not self.is_failed
    
    def spawn_collect_items(self, game_map, rooms):
        if self.quest_type != 'collect':
            return []
        
        items = []
        item_name = self.target_data.get('item_name', '任务物品')
        available_rooms = [r for r in rooms if r.room_type == 'normal']
        
        for i in range(self.target):
            if available_rooms:
                room = random.choice(available_rooms)
                x, y = room.get_random_position()
                item = QuestItem(x, y, self.quest_id, item_name, 'collect')
                items.append(item)
                self.target_positions.append((x, y))
        
        self.spawned_items = items
        return items
    
    def on_item_collected(self, quest_item):
        if self.quest_type == 'collect' and quest_item.quest_id == self.quest_id:
            self.progress += 1
            if quest_item in self.spawned_items:
                self.spawned_items.remove(quest_item)
            if (quest_item.x, quest_item.y) in self.target_positions:
                self.target_positions.remove((quest_item.x, quest_item.y))
            if self.progress >= self.target:
                self.is_completed = True
            return True
        return False
    
    def check_delivery_target(self, npc):
        if self.quest_type == 'delivery':
            target_npc = self.target_data.get('target_npc', '')
            if npc.name == target_npc:
                self.progress = 1
                self.is_completed = True
                return True
        return False

class QuestManager:
    def __init__(self):
        self.active_quests = []
        self.completed_quests = []
        self.failed_quests = []
        self.max_active_quests = 5
        self.quest_history = set()
    
    def can_accept_quest(self, quest):
        if len(self.active_quests) >= self.max_active_quests:
            return False, '任务列表已满'
        quest_id = f"{quest.quest_type}_{quest.quest_name}_{quest.floor}"
        if quest_id in self.quest_history:
            return False, '已完成过该任务'
        return True, '可以接受'
    
    def accept_quest(self, quest):
        can_accept, message = self.can_accept_quest(quest)
        if not can_accept:
            return False, message
        quest.accept()
        self.active_quests.append(quest)
        return True, '接受任务成功！'
    
    def complete_quest(self, quest, player):
        if not quest.is_completed:
            return False, '任务未完成'
        
        for reward in quest.rewards:
            if hasattr(reward, 'amount') and reward.item_type == 'gold':
                player.gold += reward.amount
            elif hasattr(reward, 'item_type') and reward.item_type == 'potion':
                player.add_item(reward)
            elif hasattr(reward, 'item_type') and reward.item_type == 'equipment':
                player.add_item(reward)
            elif hasattr(reward, 'item_type') and reward.item_type == 'rune':
                player.add_item(reward)
            elif hasattr(reward, 'item_type') and reward.item_type == 'material':
                player.enhance_materials += getattr(reward, 'amount', 1)
        
        quest_id = f"{quest.quest_type}_{quest.quest_name}_{quest.floor}"
        self.quest_history.add(quest_id)
        
        self.active_quests.remove(quest)
        self.completed_quests.append(quest)
        
        return True, '任务完成！获得奖励！'
    
    def abandon_quest(self, quest):
        if quest in self.active_quests:
            quest.abandon()
            self.active_quests.remove(quest)
            return True, '已放弃任务'
        return False, '找不到该任务'
    
    def fail_quest(self, quest):
        if quest in self.active_quests:
            quest.fail()
            self.active_quests.remove(quest)
            self.failed_quests.append(quest)
            return True
        return False
    
    def fail_floor_locked_quests(self, current_floor):
        failed_quests = []
        for quest in self.active_quests[:]:
            if quest.is_floor_locked and quest.floor < current_floor:
                self.fail_quest(quest)
                failed_quests.append(quest)
        return failed_quests
    
    def update_hunt_progress(self, monster_type, monster_name=None):
        for quest in self.active_quests:
            if quest.quest_type == 'hunt' and quest.is_active():
                quest_monster_type = quest.target_data.get('monster_type', '')
                quest_monster_name = quest.target_data.get('monster_name', '')
                if monster_type == quest_monster_type or (monster_name and quest_monster_name in monster_name):
                    quest.progress += 1
                    if quest.progress >= quest.target:
                        quest.is_completed = True
    
    def update_collect_progress(self, quest_item):
        for quest in self.active_quests:
            if quest.quest_type == 'collect' and quest.is_active():
                if quest.on_item_collected(quest_item):
                    return True
        return False
    
    def check_delivery_quests(self, npc, player):
        for quest in self.active_quests:
            if quest.quest_type == 'delivery' and quest.is_active():
                if quest.check_delivery_target(npc):
                    if hasattr(player, 'inventory'):
                        for item in player.inventory[:]:
                            if hasattr(item, 'item_type') and item.item_type == 'delivery_letter':
                                player.inventory.remove(item)
                                break
                    return True, quest
        return False, None
    
    def get_completed_quests_count(self):
        return len(self.completed_quests)
    
    def get_total_quests_count(self):
        return len(self.completed_quests) + len(self.active_quests)
    
    def get_active_quests(self):
        return [q for q in self.active_quests if q.is_active()]
    
    def can_complete_quest(self, quest):
        return quest.is_completed and quest in self.active_quests
    
    def get_quest_target_positions(self):
        positions = []
        for quest in self.active_quests:
            if quest.is_active():
                for pos in quest.target_positions:
                    positions.append((pos, quest.quest_type))
        return positions

def create_random_npc(x, y, floor=1):
    npc_types = ['merchant', 'hunter', 'mage', 'healer']
    npc_type = random.choice(npc_types)
    npc = NPC(x, y, npc_type)
    npc.floor = floor
    
    quest_count = random.randint(0, 2)
    for _ in range(quest_count):
        quest_type = random.choice(QUEST_TYPES)
        quest = Quest(quest_type, floor)
        npc.quests.append(quest)
    
    return npc

def generate_quest_for_floor(floor):
    quest_type = random.choice(QUEST_TYPES)
    return Quest(quest_type, floor)
