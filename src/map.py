import random
import math
from .config import *

class Room:
    def __init__(self, x, y, w, h, room_type='normal'):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.width = w
        self.height = h
        self.room_type = room_type
        self.connected = False
    
    def center(self):
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return (center_x, center_y)
    
    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
    
    def get_random_position(self):
        x = random.randint(self.x1 + 1, self.x2 - 1)
        y = random.randint(self.y1 + 1, self.y2 - 1)
        return (x, y)

class GameMap:
    def __init__(self, width, height, floor=1):
        self.width = width
        self.height = height
        self.floor = floor
        
        self.room_min_size = max(4, 5 + floor // 2)
        self.room_max_size = max(8, 10 + floor)
        self.max_rooms = max(8, 12 + floor * 2)
        self.min_rooms = max(5, 6 + floor)
        
        self.tiles = [[1 for _ in range(height)] for _ in range(width)]
        self.terrain = [['normal' for _ in range(height)] for _ in range(width)]
        self.explored = [[False for _ in range(height)] for _ in range(width)]
        self.visible = [[False for _ in range(height)] for _ in range(width)]
        self.rooms = []
        self.room_types = {}
        self.stairs_pos = None
        self.walked_path = []
        self.markers = []
    
    def generate_map(self):
        num_rooms = 0
        max_attempts = 200
        
        for _ in range(max_attempts):
            if len(self.rooms) >= self.max_rooms:
                break
            
            w = random.randint(self.room_min_size, self.room_max_size)
            h = random.randint(self.room_min_size, self.room_max_size)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            new_room = Room(x, y, w, h)
            
            intersect = False
            for other_room in self.rooms:
                if new_room.intersect(other_room):
                    intersect = True
                    break
            
            if not intersect:
                self.create_room(new_room)
                
                if len(self.rooms) > 0:
                    prev_room = self.rooms[-1]
                    new_x, new_y = new_room.center()
                    prev_x, prev_y = prev_room.center()
                    
                    if random.random() < 0.5:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                
                self.rooms.append(new_room)
                num_rooms += 1
        
        self.assign_room_types()
        self.place_stairs()
        self.generate_terrain()
    
    def create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y] = 0
    
    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[x][y] = 0
    
    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[x][y] = 0
    
    def assign_room_types(self):
        if len(self.rooms) < 2:
            return
        
        self.rooms[-1].room_type = 'boss'
        
        available_indices = list(range(1, len(self.rooms) - 1))
        random.shuffle(available_indices)
        
        type_counts = {'treasure': 0, 'shop': 0, 'rest': 0, 'trap': 0, 'altar': 0, 'blacksmith': 0, 'library': 0, 'event': 0}
        max_counts = {'treasure': 2, 'shop': 1, 'rest': 1, 'trap': 2, 'altar': 1, 'blacksmith': 1, 'library': 1, 'event': 2}
        
        for idx in available_indices:
            room_type = random.choice(['treasure', 'shop', 'rest', 'trap', 'altar', 'blacksmith', 'library', 'event', 'normal', 'normal'])
            if room_type != 'normal' and type_counts[room_type] < max_counts.get(room_type, 999):
                self.rooms[idx].room_type = room_type
                type_counts[room_type] += 1
    
    def place_stairs(self):
        if self.rooms:
            self.stairs_pos = self.rooms[-1].center()
    
    def is_walkable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y] == 0
        return False
    
    def update_fov(self, player_x, player_y, radius=8):
        for x in range(self.width):
            for y in range(self.height):
                self.visible[x][y] = False
        
        for angle in range(0, 360, 1):
            rad = math.radians(angle)
            for r in range(radius):
                x = int(player_x + math.cos(rad) * r)
                y = int(player_y + math.sin(rad) * r)
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.visible[x][y] = True
                    self.explored[x][y] = True
                    if self.tiles[x][y] == 1:
                        break
    
    def get_room_at(self, x, y):
        for room in self.rooms:
            if room.x1 < x < room.x2 and room.y1 < y < room.y2:
                return room
        return None
    
    def get_random_walkable_position(self):
        room = random.choice(self.rooms)
        return room.get_random_position()
    
    def generate_terrain(self):
        terrain_chance = 0.08 + self.floor * 0.03
        dangerous_terrain_bias = min(0.6, 0.3 + self.floor * 0.05)
        
        for room in self.rooms:
            for x in range(room.x1 + 1, room.x2):
                for y in range(room.y1 + 1, room.y2):
                    if random.random() < terrain_chance:
                        if random.random() < dangerous_terrain_bias:
                            terrain_type = random.choice(['thorns', 'poison', 'lava'])
                        else:
                            terrain_type = random.choice(['ice', 'speed'])
                        self.terrain[x][y] = terrain_type
    
    def get_terrain_effect(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.terrain[x][y]
        return 'normal'
    
    def apply_terrain_effect(self, entity, x, y):
        terrain = self.get_terrain_effect(x, y)
        effect = TERRAIN_TYPES[terrain]['effect']
        
        if effect == 'slip':
            if random.random() < 0.5:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                if dx != 0 or dy != 0:
                    new_x = x + dx
                    new_y = y + dy
                    if self.is_walkable(new_x, new_y):
                        entity.x = new_x
                        entity.y = new_y
                        return True, '滑倒了！'
            return False, None
        
        elif effect == 'damage':
            if hasattr(entity, 'take_damage'):
                entity.take_damage(5)
            return True, '被荆棘刺伤！'
        
        elif effect == 'poison':
            if hasattr(entity, 'add_status'):
                entity.add_status('poison', 3, 5)
            return True, '陷入毒池！'
        
        elif effect == 'fire':
            if hasattr(entity, 'take_damage'):
                entity.take_damage(10)
            if hasattr(entity, 'add_status'):
                entity.add_status('burning', 2, 5)
            return True, '踏入岩浆！'
        
        elif effect == 'speed':
            if hasattr(entity, 'add_status'):
                entity.add_status('haste', 3, 0)
            return True, '获得加速！'
        
        return False, None
    
    def add_to_path(self, x, y):
        if (x, y) not in self.walked_path:
            self.walked_path.append((x, y))
    
    def add_marker(self, x, y, marker_type):
        self.markers.append({'x': x, 'y': y, 'type': marker_type})
