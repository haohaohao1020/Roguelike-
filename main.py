#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地牢探险 Roguelike 游戏
使用 Python + Pygame 开发
"""

import sys
import os

try:
    import pygame
except ImportError:
    print("错误: 请先安装 pygame: pip install pygame")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.game import Game

def main():
    print("=" * 50)
    print("地牢探险 Roguelike 游戏")
    print("=" * 50)
    print("操作说明:")
    print("  方向键/WASD - 移动")
    print("  空格 - 攻击")
    print("  I - 打开背包")
    print("  ESC - 暂停")
    print("=" * 50)
    
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"游戏发生错误: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()
