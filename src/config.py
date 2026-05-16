import pygame
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
SAVES_DIR = os.path.join(BASE_DIR, 'saves')

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

MAP_WIDTH = 50
MAP_HEIGHT = 50
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

ROOM_TYPES = ['normal', 'treasure', 'shop', 'rest', 'trap', 'boss']

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
    }
}

EQUIPMENT_SLOTS = ['weapon', 'armor', 'helmet', 'boots', 'accessory']

MAX_FLOOR = 5

pygame.font.init()
FONT_SMALL = pygame.font.Font(None, 20)
FONT_NORMAL = pygame.font.Font(None, 24)
FONT_LARGE = pygame.font.Font(None, 36)
FONT_TITLE = pygame.font.Font(None, 48)
