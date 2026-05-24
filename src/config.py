import pygame
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
SAVES_DIR = os.path.join(BASE_DIR, 'saves')

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60

MAP_WIDTH = 60
MAP_HEIGHT = 60
TILE_SIZE = 32

MIN_ROOMS = 8
MAX_ROOMS = 15
ROOM_MIN_SIZE = 5
ROOM_MAX_SIZE = 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)
CYAN = (0, 255, 255)

QUALITY_COLORS = {
    'common': GRAY,
    'uncommon': GREEN,
    'rare': BLUE,
    'epic': PURPLE,
    'legendary': GOLD,
    'mythic': (255, 0, 0)
}

ROOM_TYPES = ['normal', 'treasure', 'shop', 'rest', 'trap', 'boss', 'altar', 'blacksmith', 'library', 'event']

TERRAIN_TYPES = {
    'normal': {'name': '普通地板', 'color': (80, 60, 40), 'effect': None},
    'ice': {'name': '冰面', 'color': (150, 200, 255), 'effect': 'slip'},
    'thorns': {'name': '荆棘', 'color': (50, 100, 50), 'effect': 'damage'},
    'poison': {'name': '毒池', 'color': (100, 150, 50), 'effect': 'poison'},
    'lava': {'name': '岩浆', 'color': (200, 100, 50), 'effect': 'fire'},
    'speed': {'name': '加速地板', 'color': (200, 150, 100), 'effect': 'speed'}
}

CLASSES = {
    'warrior': {
        'name': '战士',
        'hp': 150,
        'mp': 30,
        'str': 18,
        'dex': 10,
        'int': 6,
        'def': 15,
        'speed': 1,
        'description': '血厚防高近战猛'
    },
    'mage': {
        'name': '法师',
        'hp': 80,
        'mp': 120,
        'str': 6,
        'dex': 10,
        'int': 20,
        'def': 5,
        'speed': 1,
        'description': '血少但有远程魔法'
    },
    'rogue': {
        'name': '盗贼',
        'hp': 100,
        'mp': 50,
        'str': 12,
        'dex': 20,
        'int': 8,
        'def': 8,
        'speed': 2,
        'description': '跑得快闪避高还能背刺'
    },
    'paladin': {
        'name': '圣骑士',
        'hp': 130,
        'mp': 80,
        'str': 14,
        'dex': 10,
        'int': 14,
        'def': 18,
        'speed': 1,
        'description': '能奶能抗有光环'
    }
}

EQUIPMENT_SLOTS = ['weapon', 'helmet', 'chest', 'leggings', 'boots', 'accessory']

QUALITY_NAMES = {
    'common': '白装',
    'uncommon': '蓝装',
    'rare': '紫装',
    'epic': '橙装',
    'legendary': '金装',
    'mythic': '红装'
}

QUALITY_BORDER_COLORS = {
    'common': (150, 150, 150),
    'uncommon': (100, 200, 100),
    'rare': (100, 100, 255),
    'epic': (200, 100, 200),
    'legendary': (255, 215, 0),
    'mythic': (255, 0, 0)
}

SUB_STAT_TYPES = [
    'hp_regen', 'mp_regen', 'physical_lifesteal', 'magic_lifesteal',
    'damage_reflect', 'status_resistance', 'boss_damage', 'mob_damage',
    'damage_reduction'
]

SUB_STAT_NAMES = {
    'hp_regen': '生命回复',
    'mp_regen': '法力回复',
    'physical_lifesteal': '物理吸血',
    'magic_lifesteal': '法术吸血',
    'damage_reflect': '伤害反弹',
    'status_resistance': '异常抗性',
    'boss_damage': 'BOSS增伤',
    'mob_damage': '小怪增伤',
    'damage_reduction': '减伤百分比'
}

ELEMENT_TYPES = ['fire', 'ice', 'lightning', 'poison']
ELEMENT_NAMES = {
    'fire': '火焰',
    'ice': '冰霜',
    'lightning': '雷电',
    'poison': '剧毒'
}
ELEMENT_COLORS = {
    'fire': (255, 100, 50),
    'ice': (100, 200, 255),
    'lightning': (255, 255, 100),
    'poison': (100, 200, 100)
}

RUNE_TYPES = ['strength', 'dexterity', 'intelligence', 'vitality', 'critical']
RUNE_NAMES = {
    'strength': '力量符文',
    'dexterity': '敏捷符文',
    'intelligence': '智力符文',
    'vitality': '体力符文',
    'critical': '暴击符文'
}

SET_NAMES = [
    '烈焰套装', '寒冰套装', '雷霆套装', '剧毒套装',
    '战士套装', '法师套装', '盗贼套装', '圣骑士套装'
]

SET_BONUSES = {
    '烈焰套装': {
        2: {'fire_damage': 10},
        3: {'fire_resistance': 20},
        5: {'fire_aoe': True}
    },
    '寒冰套装': {
        2: {'ice_damage': 10},
        3: {'freeze_chance': 10},
        5: {'ice_shield': True}
    },
    '雷霆套装': {
        2: {'lightning_damage': 10},
        3: {'attack_speed': 15},
        5: {'chain_lightning': True}
    },
    '剧毒套装': {
        2: {'poison_damage': 10},
        3: {'poison_duration': 3},
        5: {'poison_explosion': True}
    },
    '战士套装': {
        2: {'physical_defense': 20},
        3: {'max_hp': 100},
        5: {'berserker': True}
    },
    '法师套装': {
        2: {'magic_attack': 15},
        3: {'max_mp': 50},
        5: {'spell_amplify': True}
    },
    '盗贼套装': {
        2: {'evasion': 10},
        3: {'critical_chance': 10},
        5: {'backstab': True}
    },
    '圣骑士套装': {
        2: {'heal_power': 20},
        3: {'holy_shield': 15},
        5: {'divine_blessing': True}
    }
}

SLOT_NAMES = {
    'weapon': '武器',
    'helmet': '头盔',
    'chest': '胸甲',
    'leggings': '护腿',
    'boots': '鞋子',
    'accessory': '饰品'
}

BASE_STAT_NAMES = {
    'physical_attack': '物理攻击',
    'magic_attack': '法术攻击',
    'physical_defense': '物理防御',
    'magic_defense': '法术防御',
    'max_hp': '最大生命',
    'max_mp': '最大法力',
    'move_speed': '移动速度',
    'critical_chance': '暴击率',
    'critical_damage': '暴击伤害',
    'evasion': '闪避率',
    'block_rate': '格挡率'
}

MAX_FLOOR = 10

FLOOR_THEMES = {
    1: {
        'name': '幽暗密林',
        'description': '植被茂密的古老森林，野兽与丛林魔物盘踞',
        'floor_color': (30, 60, 30),
        'wall_color': (40, 80, 40),
        'accent_color': (60, 120, 60),
        'monster_types': ['forest_wolf', 'giant_spider', 'wood_sprite', 'poison_vine'],
        'boss_name': '森林守护者·树人长老',
        'boss_color': (50, 150, 50),
        'bgm': 'forest'
    },
    2: {
        'name': '幽深墓穴',
        'description': '古老的地下陵墓，亡灵骷髅类怪物出没',
        'floor_color': (40, 40, 50),
        'wall_color': (60, 60, 70),
        'accent_color': (100, 100, 120),
        'monster_types': ['skeleton', 'ghost', 'wraith', 'bone_guard'],
        'boss_name': '亡灵君主·骸骨王',
        'boss_color': (150, 150, 180),
        'bgm': 'crypt'
    },
    3: {
        'name': '烈焰地狱',
        'description': '炙热的岩浆地貌，火焰妖魔镇守',
        'floor_color': (80, 30, 20),
        'wall_color': (120, 50, 30),
        'accent_color': (200, 80, 40),
        'monster_types': ['fire_imp', 'lava_golem', 'flame_demon', 'ash_wraith'],
        'boss_name': '炎狱领主·焚天魔',
        'boss_color': (255, 100, 30),
        'bgm': 'hell'
    },
    4: {
        'name': '虚空深渊',
        'description': '暗黑虚无的空间，暗影诡谲怪物潜伏',
        'floor_color': (20, 10, 40),
        'wall_color': (40, 20, 60),
        'accent_color': (80, 40, 120),
        'monster_types': ['shadow_wraith', 'void_creature', 'dark_mage', 'nightmare'],
        'boss_name': '虚空之主·暗影',
        'boss_color': (100, 50, 180),
        'bgm': 'abyss'
    },
    5: {
        'name': '废弃古堡',
        'description': '残破的欧式建筑，铠甲守卫游荡',
        'floor_color': (60, 50, 40),
        'wall_color': (90, 70, 50),
        'accent_color': (140, 110, 80),
        'monster_types': ['armor_guard', 'ghost_knight', 'blood_servant', 'animated_armor'],
        'boss_name': '古堡主人·吸血伯爵',
        'boss_color': (180, 60, 80),
        'bgm': 'castle'
    },
    6: {
        'name': '古龙巢穴',
        'description': '险峻的山石洞窟，远古龙族的领地',
        'floor_color': (70, 60, 50),
        'wall_color': (100, 80, 60),
        'accent_color': (160, 120, 80),
        'monster_types': ['young_dragon', 'wyrm', 'dragon_hatchling', 'fire_drake'],
        'boss_name': '炎龙·赤焰',
        'boss_color': (255, 150, 50),
        'bgm': 'dragon'
    },
    7: {
        'name': '远古神殿',
        'description': '神秘的远古遗迹，神圣力量与诅咒并存',
        'floor_color': (80, 70, 90),
        'wall_color': (110, 90, 120),
        'accent_color': (180, 160, 200),
        'monster_types': ['temple_guardian', 'fallen_priest', 'angelic_warrior', 'holy_construct'],
        'boss_name': '神殿守护者·光暗双生',
        'boss_color': (200, 180, 220),
        'bgm': 'temple'
    },
    8: {
        'name': '冰封秘境',
        'description': '永恒的冰雪世界，极寒之地的考验',
        'floor_color': (100, 150, 200),
        'wall_color': (130, 180, 230),
        'accent_color': (180, 220, 255),
        'monster_types': ['ice_golem', 'frost_wraith', 'snow_beast', 'glacial_spirit'],
        'boss_name': '冰霜女王·极寒',
        'boss_color': (150, 220, 255),
        'bgm': 'frost'
    },
    9: {
        'name': '混沌领域',
        'description': '混乱扭曲的空间，法则崩坏之地',
        'floor_color': (80, 20, 80),
        'wall_color': (120, 40, 120),
        'accent_color': (180, 60, 180),
        'monster_types': ['chaos_spawn', 'abomination', 'warped_horror', 'void_serpent'],
        'boss_name': '混沌之主·湮灭',
        'boss_color': (200, 80, 200),
        'bgm': 'chaos'
    },
    10: {
        'name': '终焉圣殿',
        'description': '命运的终点，最终决战之地',
        'floor_color': (50, 50, 80),
        'wall_color': (80, 80, 120),
        'accent_color': (150, 150, 200),
        'monster_types': ['final_guardian', 'archangel', 'demon_lord', 'aspect_of_death'],
        'boss_name': '终焉神·创世',
        'boss_color': (255, 215, 0),
        'bgm': 'final'
    }
}

ENDING_TYPES = {
    'bad': {
        'name': '灰暗落败结局',
        'description': '你逃避了太多战斗，滥用诅咒道具，伤害了无辜之人...',
        'color': (80, 80, 80),
        'title_color': (100, 100, 100)
    },
    'normal': {
        'name': '圆满通关结局',
        'description': '你稳步推进了冒险，完成了众多任务，成为了真正的勇者！',
        'color': (100, 150, 200),
        'title_color': (150, 200, 255)
    },
    'true': {
        'name': '隐藏真结局',
        'description': '你集齐了所有信物，完成了全部任务，无伤击败了终极BOSS！你是传说中的英雄！',
        'color': (255, 215, 0),
        'title_color': (255, 255, 200)
    }
}

QUEST_TYPES = ['delivery', 'hunt', 'collect']
QUEST_NAMES = {
    'delivery': '送信任务',
    'hunt': '猎杀任务',
    'collect': '收集任务'
}

SKILLS = {
    'warrior': {
        'basic': {
            'name': '破甲猛击',
            'mp_cost': 15,
            'cooldown': 3,
            'damage_multiplier': 2.0,
            'armor_reduction': 0.3,
            'armor_reduction_duration': 2,
            'lifesteal': 0.2,
            'description': '近距离重击敌人，造成高额物理伤害，降低敌方30%防御，持续2回合',
            'unlock_level': 1,
            'range': 1.5
        },
        'ultimate': {
            'name': '狂怒碎山斩',
            'mp_cost': 50,
            'cooldown': 8,
            'damage_multiplier': 4.0,
            'berserk_duration': 3,
            'berserk_crit_bonus': 30,
            'berserk_damage_bonus': 0.5,
            'description': '全力劈砍造成巨额伤害，进入狂暴状态3回合，提升暴击率和伤害',
            'unlock_level': 1,
            'range': 1.5,
            'unstoppable': True
        }
    },
    'mage': {
        'basic': {
            'name': '烈焰弹',
            'mp_cost': 12,
            'cooldown': 2,
            'damage_multiplier': 1.5,
            'burn_damage': 8,
            'burn_duration': 3,
            'description': '远程释放火焰法球，造成火系伤害并附加灼烧状态',
            'unlock_level': 1,
            'range': 5.0
        },
        'ultimate': {
            'name': '陨星天火',
            'mp_cost': 60,
            'cooldown': 10,
            'damage_multiplier': 2.5,
            'burn_damage': 15,
            'burn_duration': 3,
            'slow_amount': 0.5,
            'slow_duration': 2,
            'description': '召唤大范围天火，对全场敌人造成伤害并附加灼烧和减速',
            'unlock_level': 1,
            'range': 999.0
        }
    },
    'rogue': {
        'basic': {
            'name': '暗影突袭',
            'mp_cost': 18,
            'cooldown': 3,
            'damage_multiplier': 2.5,
            'guaranteed_crit': True,
            'evasion_bonus': 30,
            'evasion_duration': 2,
            'description': '瞬间突进至敌人身后背刺，百分百暴击，提升闪避率',
            'unlock_level': 1,
            'range': 3.0
        },
        'ultimate': {
            'name': '影杀千刃',
            'mp_cost': 55,
            'cooldown': 9,
            'damage_multiplier': 1.2,
            'hit_count': 5,
            'defense_ignore': 0.5,
            'invisible_duration': 1,
            'speed_bonus': 2,
            'speed_duration': 3,
            'crit_damage_bonus': 50,
            'crit_damage_duration': 3,
            'description': '隐身连续穿刺多段伤害，无视部分防御，结束后提升移速和暴伤',
            'unlock_level': 1,
            'range': 2.0
        }
    },
    'paladin': {
        'basic': {
            'name': '神圣庇护',
            'mp_cost': 20,
            'cooldown': 4,
            'shield_amount': 50,
            'shield_duration': 3,
            'team_defense_bonus': 0.2,
            'team_defense_duration': 3,
            'description': '为自身附加神圣护盾，同时小幅提升队友防御力',
            'unlock_level': 1,
            'range': 0
        },
        'ultimate': {
            'name': '圣光审判',
            'mp_cost': 65,
            'cooldown': 12,
            'damage_multiplier': 2.0,
            'heal_amount': 0.5,
            'cleanse_negative': True,
            'description': '全屏圣光造成神圣伤害，恢复生命并清除负面状态',
            'unlock_level': 1,
            'range': 999.0
        }
    }
}

UI_ALPHA = 120

pygame.font.init()

def get_chinese_font(size):
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    ]
    for path in font_paths:
        try:
            if os.path.exists(path):
                return pygame.font.Font(path, size)
        except:
            continue
    return pygame.font.Font(None, size)

FONT_SMALL = get_chinese_font(20)
FONT_NORMAL = get_chinese_font(24)
FONT_LARGE = get_chinese_font(36)
FONT_TITLE = get_chinese_font(48)

ARTIFACT_NAMES = [
    '森林之心', '灵魂宝石', '火焰精华', '暗影之核', '血族徽记',
    '龙鳞护符', '圣光遗物', '冰霜之心', '混沌碎片', '创世之眼'
]

NPC_NAMES = [
    '神秘商人·李', '老猎人·王', '流浪法师·陈', '圣骑士·赵', '冒险家·周',
    '幽灵船长', '神秘旅者', '暗影刺客', '光之使者', '时间旅行者'
]

TASK_NAMES = {
    'delivery': [
        '重要密函', '珍贵卷轴', '魔法信件', '家族信物', '紧急情报'
    ],
    'hunt': [
        '清除威胁', '复仇猎杀', '精英挑战', '怪物歼灭', '危险驱逐'
    ],
    'collect': [
        '材料收集', '珍稀采集', '遗物搜寻', '宝物探索', '资源获取'
    ]
}

MONSTER_NAMES_CN = {
    'forest_wolf': '森林狼',
    'giant_spider': '巨型蜘蛛',
    'wood_sprite': '树精',
    'poison_vine': '毒藤怪',
    'skeleton': '骷髅兵',
    'ghost': '幽灵',
    'wraith': '怨灵',
    'bone_guard': '骨甲守卫',
    'fire_imp': '火妖',
    'lava_golem': '熔岩魔像',
    'flame_demon': '炎魔',
    'ash_wraith': '灰烬怨灵',
    'shadow_wraith': '暗影幽灵',
    'void_creature': '虚空造物',
    'dark_mage': '黑暗法师',
    'nightmare': '梦魇',
    'armor_guard': '铠甲守卫',
    'ghost_knight': '幽灵骑士',
    'blood_servant': '血仆',
    'animated_armor': '活化铠甲',
    'young_dragon': '幼龙',
    'wyrm': '亚龙',
    'dragon_hatchling': '龙崽',
    'fire_drake': '火龙兽',
    'temple_guardian': '神殿守卫',
    'fallen_priest': '堕落祭司',
    'angelic_warrior': '天使战士',
    'holy_construct': '圣物傀儡',
    'ice_golem': '冰霜魔像',
    'frost_wraith': '冰霜怨灵',
    'snow_beast': '雪兽',
    'glacial_spirit': '冰川精灵',
    'chaos_spawn': '混沌 spawn',
    'abomination': '憎恶',
    'warped_horror': '扭曲恐惧',
    'void_serpent': '虚空巨蛇',
    'final_guardian': '终极守卫',
    'archangel': '大天使',
    'demon_lord': '魔王',
    'aspect_of_death': '死亡化身'
}
