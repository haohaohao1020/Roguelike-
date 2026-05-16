import pygame
import os
from .config import ASSETS_DIR

class AssetLoader:
    def __init__(self):
        self.images = {}
        self.load_all_assets()
    
    def load_all_assets(self):
        categories = ['tiles', 'characters', 'items', 'ui', 'effects']
        for category in categories:
            self.images[category] = {}
            category_path = os.path.join(ASSETS_DIR, category)
            if os.path.exists(category_path):
                for filename in os.listdir(category_path):
                    if filename.endswith('.png'):
                        name = filename[:-4]
                        img_path = os.path.join(category_path, filename)
                        try:
                            img = pygame.image.load(img_path).convert_alpha()
                            self.images[category][name] = img
                        except:
                            pass
        
        self.create_placeholder_images()
    
    def create_placeholder_images(self):
        tile_size = 32
        
        floor = pygame.Surface((tile_size, tile_size))
        floor.fill((100, 80, 60))
        pygame.draw.rect(floor, (80, 60, 40), (0, 0, tile_size, tile_size), 2)
        self.images['tiles']['floor'] = floor
        
        wall = pygame.Surface((tile_size, tile_size))
        wall.fill((50, 50, 50))
        pygame.draw.rect(wall, (30, 30, 30), (0, 0, tile_size, tile_size), 2)
        self.images['tiles']['wall'] = wall
        
        door = pygame.Surface((tile_size, tile_size))
        door.fill((139, 69, 19))
        pygame.draw.rect(door, (100, 50, 10), (0, 0, tile_size, tile_size), 2)
        self.images['tiles']['door'] = door
        
        stairs = pygame.Surface((tile_size, tile_size))
        stairs.fill((80, 80, 80))
        pygame.draw.rect(stairs, (60, 60, 60), (0, 0, tile_size, tile_size), 2)
        self.images['tiles']['stairs'] = stairs
        
        player = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(player, (0, 200, 255), (tile_size//2, tile_size//2), tile_size//2 - 4)
        pygame.draw.circle(player, (255, 255, 255), (tile_size//2, tile_size//2), tile_size//2 - 4, 2)
        self.images['characters']['player'] = player
        
        enemy = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(enemy, (255, 50, 50), (tile_size//2, tile_size//2), tile_size//2 - 4)
        pygame.draw.circle(enemy, (200, 0, 0), (tile_size//2, tile_size//2), tile_size//2 - 4, 2)
        self.images['characters']['enemy'] = enemy
        
        boss = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(boss, (200, 0, 200), (tile_size//2, tile_size//2), tile_size//2 - 2)
        pygame.draw.circle(boss, (150, 0, 150), (tile_size//2, tile_size//2), tile_size//2 - 2, 2)
        self.images['characters']['boss'] = boss
        
        chest = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.rect(chest, (139, 69, 19), (4, 8, 24, 20))
        pygame.draw.rect(chest, (100, 50, 10), (4, 8, 24, 8))
        self.images['items']['chest'] = chest
        
        potion = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(potion, (255, 0, 0), (tile_size//2, tile_size//2), 8)
        self.images['items']['potion'] = potion
        
        sword = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.line(sword, (192, 192, 192), (8, 24), (24, 8), 4)
        self.images['items']['sword'] = sword
        
        gold_img = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(gold_img, (255, 215, 0), (tile_size//2, tile_size//2), 8)
        self.images['items']['gold'] = gold_img
        
        button = pygame.Surface((200, 50))
        button.fill((80, 80, 80))
        pygame.draw.rect(button, (100, 100, 100), (0, 0, 200, 50), 3)
        self.images['ui']['button'] = button
        
        panel = pygame.Surface((300, 400))
        panel.fill((40, 40, 40))
        pygame.draw.rect(panel, (60, 60, 60), (0, 0, 300, 400), 3)
        self.images['ui']['panel'] = panel
        
        hit = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(hit, (255, 100, 0), (tile_size//2, tile_size//2), 10)
        self.images['effects']['hit'] = hit
        
        magic = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(magic, (0, 150, 255), (tile_size//2, tile_size//2), 12)
        self.images['effects']['magic'] = magic
    
    def get_image(self, category, name):
        return self.images.get(category, {}).get(name, None)

asset_loader = AssetLoader()
