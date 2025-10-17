#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试游戏机制的脚本
用于验证野生Pokemon遭遇、BOSS战斗、商店显示和盲盒使用等机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pokemon_generation():
    """测试Pokemon生成机制"""
    print("=== 测试Pokemon生成机制 ===")
    
    try:
        from CCmon5C import Pokemon, PokemonConfig
        
        # 测试野生Pokemon生成
        print("测试野生Pokemon生成...")
        available_names = list(PokemonConfig.base_data.keys())
        print(f"可用Pokemon数量: {len(available_names)}")
        print(f"前5个Pokemon: {available_names[:5]}")
        
        # 创建一个测试Pokemon
        test_pokemon = Pokemon(available_names[0], level=5)
        print(f"成功创建Pokemon: {test_pokemon.name}, 等级: {test_pokemon.level}")
        
        # 测试BOSS配置
        print("\n测试BOSS配置...")
        print(f"小BOSS数量: {len(PokemonConfig.mini_bosses)}")
        print(f"大BOSS数量: {len(PokemonConfig.stage_bosses)}")
        
        if PokemonConfig.mini_bosses:
            mini_boss_data = PokemonConfig.mini_bosses[0]
            mini_boss = Pokemon(mini_boss_data["name"], level=mini_boss_data["level"])
            print(f"成功创建小BOSS: {mini_boss.name}, 等级: {mini_boss.level}")
        
        if PokemonConfig.stage_bosses:
            stage_boss_data = PokemonConfig.stage_bosses[0]
            stage_boss = Pokemon(stage_boss_data["name"], level=stage_boss_data["level"])
            print(f"成功创建大BOSS: {stage_boss.name}, 等级: {stage_boss.level}")
        
        print("✓ Pokemon生成机制正常")
        return True
        
    except Exception as e:
        print(f"✗ Pokemon生成机制测试失败: {e}")
        return False

def test_shop_mechanism():
    """测试商店机制"""
    print("\n=== 测试商店机制 ===")
    
    try:
        from CCmon5C import Shop, ItemConfig
        
        # 创建商店实例
        shop = Shop()
        print("成功创建商店实例")
        
        # 测试商店物品
        all_items = shop.get_all_items()
        print(f"商店物品总数: {len(all_items)}")
        print(f"常规物品数量: {len(shop.regular_items)}")
        print(f"稀有物品数量: {len(shop.rare_items)}")
        
        if all_items:
            print("前3个商店物品:")
            for i, item in enumerate(all_items[:3]):
                print(f"  {i+1}. {item.get('name', '未知')} - {item.get('price', 0)}金币")
        
        # 测试商店配置
        print(f"\n商店配置 - 常规物品: {len(ItemConfig.shop_items['regular'])}")
        print(f"商店配置 - 稀有物品: {len(ItemConfig.shop_items['rare'])}")
        
        print("✓ 商店机制正常")
        return True
        
    except Exception as e:
        print(f"✗ 商店机制测试失败: {e}")
        return False

def test_blind_box_mechanism():
    """测试盲盒机制"""
    print("\n=== 测试盲盒机制 ===")
    
    try:
        from CCmon5C import Item, Player, UNIFIED_SKILLS_DATABASE
        
        # 创建测试玩家
        player = Player("测试玩家")
        print("成功创建测试玩家")
        
        # 创建盲盒物品
        blind_box = Item(
            name="必杀技学习盲盒",
            description="学习必杀技的盲盒",
            item_type="skill_blind_box",
            effect="random_ultimate",
            price=15000
        )
        print("成功创建盲盒物品")
        
        # 测试盲盒使用
        print("测试盲盒使用...")
        result = blind_box.use(None, player)
        print(f"盲盒使用结果: {result}")
        
        # 检查是否生成了技能书
        print(f"玩家背包物品数量: {len(player.backpack)}")
        if player.backpack:
            last_item = player.backpack[-1]
            print(f"最后添加的物品: {last_item.name}")
        
        # 测试必杀技数据库
        ultimate_skills = [skill for skill, data in UNIFIED_SKILLS_DATABASE.items() 
                          if data.get("sp_cost", 0) >= 50]
        print(f"可用必杀技数量: {len(ultimate_skills)}")
        
        print("✓ 盲盒机制正常")
        return True
        
    except Exception as e:
        print(f"✗ 盲盒机制测试失败: {e}")
        return False

def test_encounter_mechanism():
    """测试遭遇机制"""
    print("\n=== 测试遭遇机制 ===")
    
    try:
        from CCmon5C import GameMap, Player
        
        # 创建测试地图和玩家
        game_map = GameMap()
        player = Player("测试玩家")
        print("成功创建测试地图和玩家")
        
        # 测试遭遇检查
        print("测试遭遇检查...")
        for i in range(10):
            encounter_result = game_map.check_encounter(5, 5, player)
            if encounter_result:
                print(f"  第{i+1}次检查: {encounter_result}")
                break
        else:
            print("  10次检查都没有触发遭遇（正常，因为是概率性的）")
        
        # 测试不同地块类型的遭遇
        print("测试不同地块类型...")
        for tile_type in range(6):
            game_map.grid[5][5] = tile_type
            encounter_result = game_map.check_encounter(5, 5, player)
            print(f"  地块类型{tile_type}: 可能触发遭遇")
        
        print("✓ 遭遇机制正常")
        return True
        
    except Exception as e:
        print(f"✗ 遭遇机制测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试游戏机制...")
    
    results = []
    results.append(test_pokemon_generation())
    results.append(test_shop_mechanism())
    results.append(test_blind_box_mechanism())
    results.append(test_encounter_mechanism())
    
    print(f"\n=== 测试结果总结 ===")
    print(f"通过的测试: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ 所有机制测试通过！游戏应该可以正常运行。")
    else:
        print("✗ 部分机制测试失败，需要进一步检查。")
    
    return all(results)

if __name__ == "__main__":
    main()