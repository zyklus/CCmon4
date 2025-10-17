# UI渲染模块 - 整合所有UI渲染功能
import pygame
import textwrap
from typing import List, Tuple, Optional, Dict, Any
from popup_renderer import PopupRenderer
from ui_utils import UIUtils

# 导入常量和字体管理器
try:
    from CCmon5C import (
        SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, MAP_START_X, MAP_START_Y,
        WHITE, BLACK, RED, GREEN, BLUE, YELLOW, GRAY, LIGHT_BLUE, MINT_GREEN,
        ORANGE, PURPLE, BATTLE_BG_COLOR, FontManager, GameState
    )
except ImportError:
    # 如果无法导入，定义基本常量
    SCREEN_WIDTH = 720
    SCREEN_HEIGHT = 720
    TILE_SIZE = 60
    MAP_START_X = 0
    MAP_START_Y = 0
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    GRAY = (200, 200, 200)
    LIGHT_BLUE = (173, 216, 230)
    MINT_GREEN = (152, 251, 152)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    BATTLE_BG_COLOR = (100, 180, 100)

# ==================== UI渲染器主类 ====================

class UIRenderer:
    """统一的UI渲染器"""
    
    def __init__(self, game_instance):
        """初始化UI渲染器"""
        self.game = game_instance
        self.popup_renderer = PopupRenderer()
        self.ui_utils = UIUtils()
    
    def safe_get_player_attr(self, attr_name, default_value=None):
        """安全地获取玩家属性"""
        if (hasattr(self.game, 'player') and 
            hasattr(self.game.player, attr_name)):
            return getattr(self.game.player, attr_name)
        return default_value
    
    def safe_get_game_attr(self, attr_path, default_value=None):
        """安全地获取游戏属性（支持嵌套路径，如 'images.player'）"""
        try:
            obj = self.game
            for attr in attr_path.split('.'):
                if hasattr(obj, attr):
                    obj = getattr(obj, attr)
                else:
                    return default_value
            return obj
        except (AttributeError, TypeError):
            return default_value
        
    # ==================== 通用渲染函数 ====================
    
    def draw_multiline_text(self, surface, text, font, color, x, y, max_width, line_spacing=5):
        """
        绘制多行文本
        
        Args:
            surface: 目标surface
            text: 文本内容
            font: 字体对象
            color: 文字颜色
            x, y: 起始位置
            max_width: 最大宽度
            line_spacing: 行间距
        
        Returns:
            int: 下一行的Y坐标
        """
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        current_y = y
        for line in lines:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (x, current_y))
            current_y += text_surface.get_height() + line_spacing
        
        return current_y
    
    def draw_multiline_text_with_background(self, surface, text, font, color, x, y, max_width, 
                                          line_spacing=5, bg_color=(255, 255, 255, 128), padding=5):
        """
        绘制带背景的多行文本
        
        Args:
            surface: 目标surface
            text: 文本内容
            font: 字体对象
            color: 文字颜色
            x, y: 起始位置
            max_width: 最大宽度
            line_spacing: 行间距
            bg_color: 背景颜色 (RGBA)
            padding: 内边距
        
        Returns:
            int: 下一行的Y坐标
        """
        # 计算文本行
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width - 2 * padding:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 计算背景尺寸
        line_height = font.get_height()
        total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing + 2 * padding
        bg_width = max_width
        
        # 绘制背景
        bg_surface = UIUtils.create_surface_with_alpha((bg_width, total_height), bg_color)
        surface.blit(bg_surface, (x - padding, y - padding))
        
        # 绘制文本
        current_y = y
        for line in lines:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (x, current_y))
            current_y += line_height + line_spacing
        
        return y + total_height
    
    def draw_status_icons(self, surface, pokemon, x, y, icon_size=30, spacing=5, caster_filter=None):
        """
        绘制状态图标
        
        Args:
            surface: 目标surface
            pokemon: 顾问对象
            x, y: 起始位置
            icon_size: 图标尺寸
            spacing: 图标间距
            caster_filter: 施法者过滤器 ("self", "enemy", None)
        """
        if not hasattr(pokemon, 'status_effects'):
            return
        
        current_x = x
        current_y = y
        icons_per_row = 5  # 每行最多5个图标
        icon_count = 0
        
        for effect_name, effect_data in pokemon.status_effects.items():
            # 根据施法者过滤器决定是否显示
            if caster_filter:
                effect_caster = effect_data.get('caster', 'unknown')
                if caster_filter != effect_caster:
                    continue
            
            # 绘制状态图标背景
            icon_rect = pygame.Rect(current_x, current_y, icon_size, icon_size)
            
            # 根据效果类型选择颜色
            effect_type = effect_data.get('type', 'unknown')
            if effect_type in ['buff', 'heal', 'hot']:
                icon_color = GREEN
            elif effect_type in ['debuff', 'dot', 'damage']:
                icon_color = RED
            elif effect_type == 'dodge':
                icon_color = BLUE
            else:
                icon_color = GRAY
            
            pygame.draw.rect(surface, icon_color, icon_rect)
            pygame.draw.rect(surface, BLACK, icon_rect, 2)
            
            # 绘制效果名称缩写
            font = FontManager.get_font(12) if 'FontManager' in globals() else pygame.font.Font(None, 12)
            
            # 生成缩写
            if len(effect_name) <= 3:
                abbrev = effect_name
            elif effect_name == "攻击力提升":
                abbrev = "攻↑"
            elif effect_name == "防御力提升":
                abbrev = "防↑"
            elif effect_name == "攻击力下降":
                abbrev = "攻↓"
            elif effect_name == "防御力下降":
                abbrev = "防↓"
            elif effect_name == "持续治疗":
                abbrev = "治"
            elif effect_name == "持续伤害":
                abbrev = "毒"
            elif effect_name == "回避":
                abbrev = "避"
            else:
                abbrev = effect_name[:2]
            
            text_surface = font.render(abbrev, True, WHITE)
            text_rect = text_surface.get_rect(center=icon_rect.center)
            surface.blit(text_surface, text_rect)
            
            # 绘制剩余回合数
            turns_left = effect_data.get('turns_left', 0)
            if turns_left > 0:
                turns_font = FontManager.get_font(10) if 'FontManager' in globals() else pygame.font.Font(None, 10)
                turns_text = turns_font.render(str(turns_left), True, YELLOW)
                surface.blit(turns_text, (current_x + icon_size - 12, current_y + icon_size - 12))
            
            # 更新位置
            icon_count += 1
            if icon_count % icons_per_row == 0:
                current_x = x
                current_y += icon_size + spacing
            else:
                current_x += icon_size + spacing
    
    # ==================== 探索界面渲染 ====================
    
    def draw_exploration(self, screen):
        """绘制探索界面"""
        try:
            # 绘制地图（使用游戏实例的地图缓存）
            if hasattr(self.game, '_map_surface') and self.game._map_surface:
                screen.blit(self.game._map_surface, (MAP_START_X, MAP_START_Y))
            
            # 绘制玩家
            if (hasattr(self.game, 'player') and 
                hasattr(self.game.player, 'x') and 
                hasattr(self.game.player, 'y') and 
                hasattr(self.game, 'images')):
                player_x = MAP_START_X + self.game.player.y * TILE_SIZE + 10
                player_y = MAP_START_Y + self.game.player.x * TILE_SIZE + 10
                if hasattr(self.game.images, 'player'):
                    screen.blit(self.game.images.player, (player_x, player_y))
            
            # 绘制UI元素
            self._draw_exploration_ui(screen)
            
        except Exception as e:
            print(f"绘制探索界面时出错: {e}")
    
    def _draw_exploration_ui(self, screen):
        """绘制探索界面的UI元素"""
        # 绘制菜单按钮
        menu_surface = pygame.Surface((100, 40), pygame.SRCALPHA)
        menu_surface.fill((152, 251, 152, 102))  # 薄荷绿色，40%透明度
        screen.blit(menu_surface, (10, 10))
        pygame.draw.rect(screen, BLACK, (10, 10, 100, 40), 2)
        
        menu_font = FontManager.get_font(20) if 'FontManager' in globals() else pygame.font.Font(None, 20)
        menu_text = menu_font.render("菜单", True, BLACK)
        screen.blit(menu_text, (60 - menu_text.get_width()//2, 30 - menu_text.get_height()//2))
        
        # 绘制金币信息
        if hasattr(self.game, 'player') and hasattr(self.game.player, 'money'):
            money_surface = pygame.Surface((150, 40), pygame.SRCALPHA)
            money_surface.fill((152, 251, 152, 102))
            screen.blit(money_surface, (SCREEN_WIDTH - 160, 10))
            pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 160, 10, 150, 40), 2)
            
            money_font = FontManager.get_font(20) if 'FontManager' in globals() else pygame.font.Font(None, 20)
            money_value = getattr(self.game.player, 'money', 0)
            money_text = money_font.render(f"金币: {money_value}", True, BLACK)
            screen.blit(money_text, (SCREEN_WIDTH - 155, 20))
            
            # 绘制UT条
            self._draw_ut_bar(screen)
    
    def _draw_ut_bar(self, screen):
        """绘制UT条"""
        ut_value = self.safe_get_player_attr('ut', 0)
        if ut_value is None:
            return
        
        ut_percentage = ut_value / 100.0 if ut_value > 0 else 0
        
        # 绘制背景
        pygame.draw.rect(screen, GRAY, (120, 10, 200, 40))
        
        # 绘制蓝色半透明UT条
        ut_surface = pygame.Surface((int(200 * ut_percentage), 40), pygame.SRCALPHA)
        ut_surface.fill((0, 0, 255, 128))  # 蓝色，50%透明度
        screen.blit(ut_surface, (120, 10))
        
        # 绘制黑色边框
        pygame.draw.rect(screen, BLACK, (120, 10, 200, 40), 2)
        
        # 绘制UT文字
        font = FontManager.get_font(16) if 'FontManager' in globals() else pygame.font.Font(None, 16)
        ut_text = font.render(f"UT: {ut_value}/100", True, BLACK)
        screen.blit(ut_text, (125, 20))
        
        # 显示UT耗尽提示
        ut_empty_counter = self.safe_get_player_attr('ut_empty_counter', 0)
        if ut_empty_counter > 0:
            # 安全地减少计数器
            if hasattr(self.game, 'player') and hasattr(self.game.player, 'ut_empty_counter'):
                self.game.player.ut_empty_counter -= 1
            
            ut_empty_image = self.safe_get_game_attr('images.ut_empty')
            if ut_empty_image:
                screen.blit(ut_empty_image, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 100))
            
            warning_font = FontManager.get_font(24) if 'FontManager' in globals() else pygame.font.Font(None, 24)
            warning_text = warning_font.render("UT已耗尽！所有顾问等级下降！", True, RED)
            screen.blit(warning_text, (SCREEN_WIDTH//2 - warning_text.get_width()//2, SCREEN_HEIGHT//2 + 120))
    
    # ==================== 战斗界面渲染 ====================
    
    def draw_battle(self, screen):
        """绘制战斗界面"""
        try:
            enemy_pkm = self.game.boss_pokemon if self.game.is_boss_battle else self.game.wild_pokemon
            if not enemy_pkm:
                return
            
            # 确定文字颜色
            text_color = BLUE if self.game.is_boss_battle else BLACK
            
            # 绘制战斗背景
            self._draw_battle_background(screen)
            
            # 计算区域尺寸
            top_area_height = int(SCREEN_HEIGHT * 0.6)
            bottom_area_height = int(SCREEN_HEIGHT * 0.4)
            bottom_area_y = SCREEN_HEIGHT - bottom_area_height
            
            # 绘制下方区域背景
            self._draw_battle_bottom_area(screen, bottom_area_y, bottom_area_height)
            
            # 绘制敌我双方信息
            self._draw_battle_combatants(screen, enemy_pkm, text_color)
            
            # 绘制战斗信息和按钮
            self._draw_battle_info_and_buttons(screen, bottom_area_y, text_color)
            
        except Exception as e:
            print(f"绘制战斗界面时出错: {e}")
    
    def _draw_battle_background(self, screen):
        """绘制战斗背景"""
        if (self.game.is_boss_battle and 
            hasattr(self.game, 'images') and 
            hasattr(self.game.images, 'boss_battle_bg') and 
            self.game.images.boss_battle_bg):
            bg_scaled = pygame.transform.scale(self.game.images.boss_battle_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(bg_scaled, (0, 0))
        elif (hasattr(self.game, 'images') and 
              hasattr(self.game.images, 'battle_bg') and 
              self.game.images.battle_bg):
            bg_scaled = pygame.transform.scale(self.game.images.battle_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(bg_scaled, (0, 0))
        else:
            screen.fill(BATTLE_BG_COLOR)
    
    def _draw_battle_bottom_area(self, screen, bottom_area_y, bottom_area_height):
        """绘制战斗界面下方区域背景"""
        bottom_surface = pygame.Surface((SCREEN_WIDTH, bottom_area_height), pygame.SRCALPHA)
        bottom_surface.fill((240, 240, 240, 180))  # 半透明白色背景
        screen.blit(bottom_surface, (0, bottom_area_y))
        pygame.draw.line(screen, BLACK, (0, bottom_area_y), (SCREEN_WIDTH, bottom_area_y), 2)
    
    def _draw_battle_combatants(self, screen, enemy_pkm, text_color):
        """绘制战斗双方信息"""
        battle_info_font = FontManager.get_font(16) if 'FontManager' in globals() else pygame.font.Font(None, 16)
        
        # 绘制敌方信息
        self._draw_enemy_info(screen, enemy_pkm, battle_info_font, text_color)
        
        # 绘制玩家信息
        self._draw_player_info(screen, battle_info_font, text_color)
    
    def _draw_enemy_info(self, screen, enemy_pkm, font, text_color):
        """绘制敌方信息"""
        enemy_x = 50
        enemy_status_y = 50
        
        # 敌方状态文字
        enemy_advantages = ", ".join(enemy_pkm.advantages)
        enemy_disadvantages = ", ".join(enemy_pkm.disadvantages)
        enemy_status_text = f"{enemy_pkm.name} (Lv.{enemy_pkm.level})" + (" [BOSS]" if self.game.is_boss_battle else "")
        enemy_advantages_text = f"优点: {enemy_advantages}"
        enemy_disadvantages_text = f"缺点: {enemy_disadvantages}"
        
        enemy_status_y = self.draw_multiline_text_with_background(screen, enemy_status_text, font, text_color, 
                                                                enemy_x, enemy_status_y, 400)
        enemy_status_y = self.draw_multiline_text_with_background(screen, enemy_advantages_text, font, text_color, 
                                                                enemy_x, enemy_status_y, 400)
        enemy_status_y = self.draw_multiline_text_with_background(screen, enemy_disadvantages_text, font, text_color, 
                                                                enemy_x, enemy_status_y, 400)
        enemy_status_y += 10
        
        # 绘制HP条和SP条
        enemy_status_y = self._draw_hp_bar(screen, enemy_pkm, enemy_x, enemy_status_y, 300, font, RED)
        enemy_status_y = self._draw_sp_bar(screen, enemy_pkm, enemy_x, enemy_status_y, 300, font)
        
        # 绘制敌方头像
        if hasattr(self.game, 'images') and hasattr(self.game.images, 'pokemon'):
            enemy_img = self.game.images.pokemon.get(enemy_pkm.name)
            if enemy_img:
                screen.blit(enemy_img, (enemy_x, enemy_status_y))
        
        # 绘制状态图标
        enemy_status_icon_x = min(SCREEN_WIDTH - 100, enemy_x + 160)
        enemy_status_icon_y = enemy_status_y + 10
        self.draw_status_icons(screen, enemy_pkm, enemy_status_icon_x, enemy_status_icon_y, caster_filter="self")
        
        enemy_left_icon_x = max(20, enemy_x - 200)
        enemy_left_icon_y = enemy_status_y + 10
        self.draw_status_icons(screen, enemy_pkm, enemy_left_icon_x, enemy_left_icon_y, caster_filter="enemy")
        
        # 绘制必杀技台词
        if hasattr(self.game, 'enemy_line_display') and self.game.enemy_line_display and hasattr(self.game, 'enemy_ultimate_line'):
            self._draw_ultimate_line(screen, self.game.enemy_ultimate_line, enemy_x, enemy_status_y + 160, 300, RED, font)
    
    def _draw_player_info(self, screen, font, text_color):
        """绘制玩家信息"""
        player_pkm = None
        if hasattr(self.game, 'player') and hasattr(self.game.player, 'get_active_pokemon'):
            player_pkm = self.game.player.get_active_pokemon()
        
        if not player_pkm:
            no_pokemon_text = font.render("你没有可用的顾问了！", True, text_color)
            screen.blit(no_pokemon_text, (SCREEN_WIDTH - 400, 100))
            return
        
        player_x = SCREEN_WIDTH - 200
        player_status_y = 50
        player_text_x = SCREEN_WIDTH - 320
        
        # 玩家状态文字
        player_advantages = ", ".join(player_pkm.advantages)
        player_disadvantages = ", ".join(player_pkm.disadvantages)
        player_status_text = f"你的 {player_pkm.name} (Lv.{player_pkm.level})"
        player_advantages_text = f"优点: {player_advantages}"
        player_disadvantages_text = f"缺点: {player_disadvantages}"
        
        player_status_y = self.draw_multiline_text_with_background(screen, player_status_text, font, text_color, 
                                                                 player_text_x, player_status_y, 400)
        player_status_y = self.draw_multiline_text_with_background(screen, player_advantages_text, font, text_color, 
                                                                 player_text_x, player_status_y, 400)
        player_status_y = self.draw_multiline_text_with_background(screen, player_disadvantages_text, font, text_color, 
                                                                 player_text_x, player_status_y, 400)
        player_status_y += 10
        
        # 绘制HP条和SP条
        player_hp_x = SCREEN_WIDTH - 320
        player_status_y = self._draw_hp_bar(screen, player_pkm, player_hp_x, player_status_y, 300, font, GREEN)
        player_status_y = self._draw_sp_bar(screen, player_pkm, player_hp_x, player_status_y, 300, font)
        
        # 绘制玩家头像
        if hasattr(self.game, 'images') and hasattr(self.game.images, 'pokemon'):
            pkm_img = self.game.images.pokemon.get(player_pkm.name)
            if pkm_img:
                screen.blit(pkm_img, (player_x, player_status_y))
        
        # 绘制状态图标
        player_status_icon_x = max(player_x - 160, SCREEN_WIDTH // 2)
        player_status_icon_y = player_status_y + 10
        self.draw_status_icons(screen, player_pkm, player_status_icon_x, player_status_icon_y, caster_filter="self")
        
        player_right_icon_x = min(SCREEN_WIDTH - 100, player_x + 160)
        player_right_icon_y = player_status_y + 10
        self.draw_status_icons(screen, player_pkm, player_right_icon_x, player_right_icon_y, caster_filter="enemy")
        
        # 绘制必杀技台词
        if hasattr(self.game, 'ally_line_display') and self.game.ally_line_display and hasattr(self.game, 'ally_ultimate_line'):
            line_box_x = SCREEN_WIDTH - 320
            self._draw_ultimate_line(screen, self.game.ally_ultimate_line, line_box_x, player_status_y + 160, 300, BLUE, font)
    
    def _draw_hp_bar(self, screen, pokemon, x, y, width, font, color):
        """绘制HP条"""
        height = 25
        
        # 绘制背景
        pygame.draw.rect(screen, WHITE, (x, y, width, height))
        
        # 绘制HP填充
        hp_percentage = pokemon.get_hp_percentage()
        fill_width = int((width - 4) * hp_percentage)
        hp_surface = pygame.Surface((fill_width, height - 4), pygame.SRCALPHA)
        hp_surface.fill((*color, 128))
        screen.blit(hp_surface, (x + 2, y + 2))
        
        # 绘制边框
        pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
        
        # 绘制HP文字
        hp_text = f"HP: {pokemon.hp}/{pokemon.max_hp}"
        hp_text_surface = font.render(hp_text, True, BLACK)
        hp_text_rect = hp_text_surface.get_rect(center=(x + width // 2, y + height // 2))
        
        # 绘制文字背景
        hp_text_bg = pygame.Surface((hp_text_rect.width + 6, hp_text_rect.height + 2), pygame.SRCALPHA)
        hp_text_bg.fill((255, 255, 255, 128))
        screen.blit(hp_text_bg, (hp_text_rect.x - 3, hp_text_rect.y - 1))
        
        screen.blit(hp_text_surface, hp_text_rect)
        
        return y + height + 10
    
    def _draw_sp_bar(self, screen, pokemon, x, y, width, font):
        """绘制SP条"""
        height = 20
        
        # 绘制背景
        pygame.draw.rect(screen, WHITE, (x, y, width, height))
        
        # 绘制SP填充
        sp_percentage = pokemon.get_sp_percentage()
        fill_width = int((width - 4) * sp_percentage)
        sp_surface = pygame.Surface((fill_width, height - 4), pygame.SRCALPHA)
        sp_surface.fill((*PURPLE, 128))
        screen.blit(sp_surface, (x + 2, y + 2))
        
        # 绘制边框
        pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
        
        # 绘制SP文字
        sp_text = f"SP: {pokemon.sp}/{pokemon.max_sp}"
        sp_text_surface = font.render(sp_text, True, BLACK)
        sp_text_rect = sp_text_surface.get_rect(center=(x + width // 2, y + height // 2))
        
        # 绘制文字背景
        sp_text_bg = pygame.Surface((sp_text_rect.width + 6, sp_text_rect.height + 2), pygame.SRCALPHA)
        sp_text_bg.fill((255, 255, 255, 128))
        screen.blit(sp_text_bg, (sp_text_rect.x - 3, sp_text_rect.y - 1))
        
        screen.blit(sp_text_surface, sp_text_rect)
        
        return y + height + 15
    
    def _draw_ultimate_line(self, screen, line_text, x, y, width, border_color, font):
        """绘制必杀技台词"""
        height = 60
        
        # 绘制背景
        line_box_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if border_color == RED:
            line_box_surface.fill((0, 0, 0, 180))  # 黑色背景
        else:
            line_box_surface.fill((0, 100, 200, 180))  # 蓝色背景
        screen.blit(line_box_surface, (x, y))
        
        # 绘制边框
        pygame.draw.rect(screen, border_color, (x, y, width, height), 2)
        
        # 绘制文字
        self.draw_multiline_text(screen, line_text, font, WHITE, x + 10, y + 10, width - 20, 5)
    
    def _draw_battle_info_and_buttons(self, screen, bottom_area_y, text_color):
        """绘制战斗信息和按钮"""
        # 战斗信息文本框区域
        battle_text_area_width = int(SCREEN_WIDTH * 0.75)
        battle_text_x = 20
        battle_text_y = bottom_area_y + 20
        
        # 战斗消息
        if hasattr(self.game, 'battle_messages'):
            battle_info_font = FontManager.get_font(16) if 'FontManager' in globals() else pygame.font.Font(None, 16)
            display_messages = self.game.battle_messages[-5:] if len(self.game.battle_messages) > 5 else self.game.battle_messages
            current_y = battle_text_y
            for msg in display_messages:
                current_y = self.draw_multiline_text(
                    screen, msg, battle_info_font, text_color, 
                    battle_text_x, current_y, battle_text_area_width - 40, 5
                )
        
        # 绘制按钮
        if hasattr(self.game, 'state') and hasattr(self.game, 'battle_buttons'):
            # 这里需要导入GameState或者使用字符串比较
            if (hasattr(self.game.state, 'name') and 
                self.game.state.name in ['BATTLE', 'BOSS_BATTLE']):
                for button in self.game.battle_buttons:
                    if hasattr(button, 'draw'):
                        button.draw(screen)
        
        if hasattr(self.game, 'move_buttons'):
            for button in self.game.move_buttons:
                if hasattr(button, 'draw'):
                    button.draw(screen)
    
    # ==================== 菜单界面渲染 ====================
    
    def draw_menu(self, screen):
        """绘制菜单界面"""
        try:
            # 绘制半透明背景
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            # 绘制菜单背景
            menu_width = 400
            menu_height = 500
            menu_x = (SCREEN_WIDTH - menu_width) // 2
            menu_y = (SCREEN_HEIGHT - menu_height) // 2
            
            menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
            menu_surface.fill((255, 255, 255, 230))
            screen.blit(menu_surface, (menu_x, menu_y))
            pygame.draw.rect(screen, BLACK, (menu_x, menu_y, menu_width, menu_height), 3)
            
            # 绘制标题
            title_font = FontManager.get_font(32) if 'FontManager' in globals() else pygame.font.Font(None, 32)
            title_text = title_font.render("游戏菜单", True, BLACK)
            title_x = menu_x + (menu_width - title_text.get_width()) // 2
            screen.blit(title_text, (title_x, menu_y + 20))
            
            # 绘制菜单按钮
            if hasattr(self.game, 'menu_buttons'):
                for button in self.game.menu_buttons:
                    if hasattr(button, 'draw'):
                        button.draw(screen)
            
        except Exception as e:
            print(f"绘制菜单界面时出错: {e}")
    
    # ==================== 商店界面渲染 ====================
    
    def draw_shop(self, screen):
        """绘制商店界面"""
        try:
            # 绘制背景
            screen.fill(WHITE)
            
            # 绘制标题
            title_font = FontManager.get_font(32) if 'FontManager' in globals() else pygame.font.Font(None, 32)
            title_text = title_font.render("商店", True, BLACK)
            screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
            
            # 绘制金币信息
            money_value = self.safe_get_player_attr('money', 0)
            if money_value is not None:
                money_font = FontManager.get_font(24) if 'FontManager' in globals() else pygame.font.Font(None, 24)
                money_text = money_font.render(f"金币: {money_value}", True, BLACK)
                screen.blit(money_text, (20, 70))
            
            # 绘制商品列表
            if hasattr(self.game, 'shop'):
                self._draw_shop_items(screen)
            
            # 绘制按钮
            if hasattr(self.game, 'shop_buttons'):
                for button in self.game.shop_buttons:
                    if hasattr(button, 'draw'):
                        button.draw(screen)
            
        except Exception as e:
            print(f"绘制商店界面时出错: {e}")
    
    def _draw_shop_items(self, screen):
        """绘制商店物品列表"""
        try:
            item_font = FontManager.get_font(20) if 'FontManager' in globals() else pygame.font.Font(None, 20)
            start_y = 120
            item_height = 60
            
            # 获取所有商店物品
            all_items = []
            if hasattr(self.game.shop, 'get_all_items'):
                all_items = self.game.shop.get_all_items()
            elif hasattr(self.game.shop, 'regular_items') and hasattr(self.game.shop, 'rare_items'):
                all_items = self.game.shop.regular_items + self.game.shop.rare_items
            
            # 绘制物品
            for i, item in enumerate(all_items):
                item_y = start_y + i * item_height
                item_rect = pygame.Rect(20, item_y, SCREEN_WIDTH - 40, item_height - 5)
                
                # 绘制物品背景
                pygame.draw.rect(screen, LIGHT_BLUE, item_rect)
                pygame.draw.rect(screen, BLACK, item_rect, 2)
                
                # 绘制物品信息
                item_name = item.get("name", "未知物品")
                item_price = item.get("price", 0)
                item_stock = item.get("stock", 0)
                item_text = f"{item_name} - {item_price}金币 (库存: {item_stock})"
                text_surface = item_font.render(item_text, True, BLACK)
                screen.blit(text_surface, (item_rect.x + 10, item_rect.y + 10))
                
                # 绘制物品描述
                desc_font = FontManager.get_font(16) if 'FontManager' in globals() else pygame.font.Font(None, 16)
                item_desc = item.get("description", "无描述")
                desc_surface = desc_font.render(item_desc, True, BLACK)
                screen.blit(desc_surface, (item_rect.x + 10, item_rect.y + 35))
        except Exception as e:
            print(f"绘制商店物品时出错: {e}")
            # 绘制错误信息
            error_font = FontManager.get_font(20) if 'FontManager' in globals() else pygame.font.Font(None, 20)
            error_text = error_font.render("商店物品加载失败", True, RED)
            screen.blit(error_text, (50, 150))
    
    # ==================== 背包界面渲染 ====================
    
    def draw_backpack_menu(self, screen):
        """绘制背包界面"""
        try:
            # 绘制背景
            screen.fill(WHITE)
            
            # 绘制标题
            title_font = FontManager.get_font(32) if 'FontManager' in globals() else pygame.font.Font(None, 32)
            title_text = title_font.render("背包", True, BLACK)
            screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
            
            # 绘制物品列表
            backpack = self.safe_get_player_attr('backpack', [])
            if backpack is not None:
                self._draw_backpack_items(screen)
            
            # 绘制按钮
            if hasattr(self.game, 'backpack_buttons'):
                for button in self.game.backpack_buttons:
                    if hasattr(button, 'draw'):
                        button.draw(screen)
            
        except Exception as e:
            print(f"绘制背包界面时出错: {e}")
    
    def _draw_backpack_items(self, screen):
        """绘制背包物品列表"""
        item_font = FontManager.get_font(20) if 'FontManager' in globals() else pygame.font.Font(None, 20)
        start_y = 80
        item_height = 50
        
        backpack = self.safe_get_player_attr('backpack', [])
        if not backpack:
            empty_text = item_font.render("背包是空的", True, BLACK)
            screen.blit(empty_text, (SCREEN_WIDTH//2 - empty_text.get_width()//2, start_y + 100))
            return
        
        for i, item in enumerate(backpack):
            item_y = start_y + i * item_height
            item_rect = pygame.Rect(20, item_y, SCREEN_WIDTH - 40, item_height - 5)
            
            # 绘制物品背景
            pygame.draw.rect(screen, MINT_GREEN, item_rect)
            pygame.draw.rect(screen, BLACK, item_rect, 2)
            
            # 绘制物品信息
            item_text = f"{item.name}"
            text_surface = item_font.render(item_text, True, BLACK)
            screen.blit(text_surface, (item_rect.x + 10, item_rect.y + 5))
            
            # 绘制物品描述
            desc_font = FontManager.get_font(14) if 'FontManager' in globals() else pygame.font.Font(None, 14)
            desc_surface = desc_font.render(item.description, True, BLACK)
            screen.blit(desc_surface, (item_rect.x + 10, item_rect.y + 25))
    
    # ==================== 训练中心界面渲染 ====================
    
    def draw_training_center(self, screen):
        """绘制训练中心界面"""
        try:
            # 绘制背景
            screen.fill(WHITE)
            
            # 绘制标题
            title_font = FontManager.get_font(32) if 'FontManager' in globals() else pygame.font.Font(None, 32)
            title_text = title_font.render("训练中心", True, BLACK)
            screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
            
            # 绘制训练中心信息
            if hasattr(self.game, 'training_center'):
                self._draw_training_info(screen)
            
            # 绘制按钮
            if hasattr(self.game, 'training_buttons'):
                for button in self.game.training_buttons:
                    if hasattr(button, 'draw'):
                        button.draw(screen)
            
        except Exception as e:
            print(f"绘制训练中心界面时出错: {e}")
    
    def _draw_training_info(self, screen):
        """绘制训练中心信息"""
        info_font = FontManager.get_font(20) if 'FontManager' in globals() else pygame.font.Font(None, 20)
        
        # 显示寄养信息
        deposited_info = self.game.training_center.get_deposited_pokemon_info()
        
        info_y = 80
        if deposited_info:
            info_text = f"当前寄养顾问数量: {len(deposited_info)}"
            text_surface = info_font.render(info_text, True, BLACK)
            screen.blit(text_surface, (20, info_y))
            
            # 显示每个寄养的顾问
            for i, info in enumerate(deposited_info):
                item_y = info_y + 40 + i * 30
                pokemon_text = f"{info['name']} (Lv.{info['level']}) - 寄养{info['days_deposited']}天"
                text_surface = info_font.render(pokemon_text, True, BLACK)
                screen.blit(text_surface, (40, item_y))
        else:
            no_pokemon_text = info_font.render("当前没有寄养的顾问", True, BLACK)
            screen.blit(no_pokemon_text, (20, info_y))
    
    # ==================== 弹窗渲染 ====================
    
    def draw_skill_tooltip(self, screen, skill_info):
        """绘制技能提示框"""
        if not skill_info:
            return
        
        # 使用PopupRenderer绘制提示框
        tooltip_width = 300
        tooltip_height = 150
        tooltip_x = (SCREEN_WIDTH - tooltip_width) // 2
        tooltip_y = (SCREEN_HEIGHT - tooltip_height) // 2
        
        popup_rect = self.popup_renderer.draw_popup_frame(
            screen, tooltip_x, tooltip_y, tooltip_width, tooltip_height, 'default'
        )
        
        # 绘制技能信息
        font = FontManager.get_font(16) if 'FontManager' in globals() else pygame.font.Font(None, 16)
        
        y_offset = popup_rect.y + 20
        
        # 技能名称
        name_text = font.render(f"技能: {skill_info.get('name', '未知')}", True, BLACK)
        screen.blit(name_text, (popup_rect.x + 10, y_offset))
        y_offset += 25
        
        # SP消耗
        sp_cost = skill_info.get('sp_cost', 0)
        sp_text = font.render(f"SP消耗: {sp_cost}", True, BLACK)
        screen.blit(sp_text, (popup_rect.x + 10, y_offset))
        y_offset += 25
        
        # 技能描述
        description = skill_info.get('description', '无描述')
        self.draw_multiline_text(screen, description, font, BLACK, 
                               popup_rect.x + 10, y_offset, tooltip_width - 20)
    
    def draw_confirmation_popup(self, screen, message, title="确认"):
        """绘制确认弹窗"""
        return self.popup_renderer.draw_confirmation_popup(screen, message, title)
    
    # ==================== 消息渲染 ====================
    
    def draw_message(self, screen):
        """绘制消息"""
        if not hasattr(self.game, 'current_message') or not self.game.current_message:
            return
        
        # 绘制消息背景
        message_width = 500
        message_height = 200
        message_x = (SCREEN_WIDTH - message_width) // 2
        message_y = (SCREEN_HEIGHT - message_height) // 2
        
        popup_rect = self.popup_renderer.draw_popup_frame(
            screen, message_x, message_y, message_width, message_height, 'default'
        )
        
        # 绘制消息文本
        font = FontManager.get_font(20) if 'FontManager' in globals() else pygame.font.Font(None, 20)
        self.draw_multiline_text(screen, self.game.current_message, font, BLACK,
                               popup_rect.x + 20, popup_rect.y + 20, message_width - 40)
        
        # 绘制确认按钮
        button_config = [{'text': '确定', 'color': MINT_GREEN, 'font': font}]
        self.popup_renderer.draw_popup_buttons(screen, popup_rect, button_config)