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
    'legendary': GOLD
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
    'legendary': '金装'
}

QUALITY_BORDER_COLORS = {
    'common': (150, 150, 150),
    'uncommon': (100, 200, 100),
    'rare': (100, 100, 255),
    'epic': (200, 100, 200),
    'legendary': (255, 215, 0)
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

MAX_FLOOR = 5

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
