from .config import *

class BehaviorTracker:
    def __init__(self):
        self.battles_avoided = 0
        self.battles_fought = 0
        self.friendly_npcs_harmed = 0
        self.cursed_items_used = 0
        self.quests_completed = 0
        self.quests_abandoned = 0
        self.artifacts_collected = set()
        self.damage_taken = 0
        self.total_healing_done = 0
        self.monsters_killed = 0
        self.elites_killed = 0
        self.bosses_killed = 0
        self.final_boss_no_damage = False
        self.rooms_explored = 0
        self.items_collected = 0
        self.gold_earned = 0
        self.play_time_turns = 0
        self.deaths = 0
    
    def record_battle_avoided(self):
        self.battles_avoided += 1
    
    def record_battle_fought(self):
        self.battles_fought += 1
    
    def record_npc_harmed(self):
        self.friendly_npcs_harmed += 1
    
    def record_cursed_item_used(self):
        self.cursed_items_used += 1
    
    def record_quest_completed(self):
        self.quests_completed += 1
    
    def record_quest_abandoned(self):
        self.quests_abandoned += 1
    
    def record_artifact_collected(self, artifact_name):
        self.artifacts_collected.add(artifact_name)
    
    def record_damage_taken(self, amount):
        self.damage_taken += amount
    
    def record_healing_done(self, amount):
        self.total_healing_done += amount
    
    def record_monster_killed(self, monster_type='normal'):
        self.monsters_killed += 1
        if monster_type == 'elite':
            self.elites_killed += 1
        elif monster_type == 'boss':
            self.bosses_killed += 1
    
    def record_final_boss_no_damage(self, value=True):
        self.final_boss_no_damage = value
    
    def record_room_explored(self):
        self.rooms_explored += 1
    
    def record_item_collected(self):
        self.items_collected += 1
    
    def record_gold_earned(self, amount):
        self.gold_earned += amount
    
    def record_turn_passed(self):
        self.play_time_turns += 1
    
    def update_play_time(self):
        self.play_time_turns += 1
    
    @property
    def play_time(self):
        return self.play_time_turns
    
    def record_death(self):
        self.deaths += 1
    
    def get_artifact_count(self):
        return len(self.artifacts_collected)
    
    def has_all_artifacts(self):
        return len(self.artifacts_collected) >= 10
    
    def get_battle_rate(self):
        total = self.battles_fought + self.battles_avoided
        if total == 0:
            return 1.0
        return self.battles_fought / total
    
    def get_summary(self):
        return {
            'battles_fought': self.battles_fought,
            'battles_avoided': self.battles_avoided,
            'npcs_harmed': self.friendly_npcs_harmed,
            'cursed_items': self.cursed_items_used,
            'quests_completed': self.quests_completed,
            'artifacts': len(self.artifacts_collected),
            'damage_taken': self.damage_taken,
            'monsters_killed': self.monsters_killed,
            'elites_killed': self.elites_killed,
            'bosses_killed': self.bosses_killed,
            'final_boss_no_damage': self.final_boss_no_damage
        }

class EndingSystem:
    def __init__(self):
        self.unlocked_endings = set()
        self.ending_records = []
    
    def determine_ending(self, behavior_tracker, quest_manager, current_floor):
        battle_rate = behavior_tracker.get_battle_rate()
        quests_completed = quest_manager.get_completed_quests_count() if quest_manager else 0
        total_quests = quest_manager.get_total_quests_count() if quest_manager else 0
        quest_completion_rate = quests_completed / max(1, total_quests) if total_quests > 0 else 0
        
        bad_ending_conditions = [
            battle_rate < 0.3,
            behavior_tracker.friendly_npcs_harmed > 0,
            behavior_tracker.cursed_items_used > 3
        ]
        
        true_ending_conditions = [
            current_floor >= MAX_FLOOR,
            behavior_tracker.has_all_artifacts(),
            quests_completed >= 15,
            behavior_tracker.final_boss_no_damage,
            behavior_tracker.deaths == 0
        ]
        
        normal_ending_conditions = [
            current_floor >= MAX_FLOOR,
            quest_completion_rate >= 0.5,
            battle_rate >= 0.5
        ]
        
        if all(true_ending_conditions):
            return 'true'
        elif any(bad_ending_conditions):
            return 'bad'
        elif all(normal_ending_conditions):
            return 'normal'
        elif current_floor >= MAX_FLOOR:
            return 'normal'
        else:
            return 'bad'
    
    def get_ending_data(self, ending_type):
        return ENDING_TYPES.get(ending_type, ENDING_TYPES['normal'])
    
    def unlock_ending(self, ending_type):
        self.unlocked_endings.add(ending_type)
    
    def is_ending_unlocked(self, ending_type):
        return ending_type in self.unlocked_endings
    
    def record_ending(self, ending_type, play_data):
        record = {
            'ending': ending_type,
            'data': play_data,
            'timestamp': None
        }
        self.ending_records.append(record)
        self.unlock_ending(ending_type)
    
    def get_ending_story(self, ending_type):
        stories = {
            'bad': [
                '你在黑暗的地牢中迷失了方向...',
                '逃避战斗让你变得懦弱，最终...',
                '诅咒的力量侵蚀了你的灵魂...',
                '地牢的黑暗吞噬了一切，包括你。'
            ],
            'normal': [
                '恭喜你，勇敢的冒险者！',
                '你成功征服了这座神秘的地牢！',
                '你的名字将被载入冒险者的史册！',
                '传说才刚刚开始...'
            ],
            'true': [
                '🌟 传说中的英雄诞生了！🌟',
                '你不仅征服了地牢，还揭开了所有秘密！',
                '你集齐了所有古老的神器，',
                '无伤击败了终焉神·创世！',
                '你是真正的传奇！'
            ]
        }
        return stories.get(ending_type, stories['normal'])
    
    def get_all_unlocked_endings(self):
        return list(self.unlocked_endings)
    
    def get_ending_statistics(self):
        stats = {}
        for ending in ['bad', 'normal', 'true']:
            stats[ending] = self.ending_records.count(ending)
        return stats

def create_artifact_item(floor):
    from .items import Item
    if 1 <= floor <= len(ARTIFACT_NAMES):
        artifact_name = ARTIFACT_NAMES[floor - 1]
        item = Item(0, 0, artifact_name, 'artifact')
        item.quality = 'legendary'
        item.value = 1000
        item.floor = floor
        return item
    return None
