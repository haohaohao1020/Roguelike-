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

EQUIPMENT_SLOTS = ['weapon', 'armor', 'helmet', 'boots', 'accessory']

MAX_FLOOR = 5

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
