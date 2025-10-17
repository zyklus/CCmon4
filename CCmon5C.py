# 顾问游戏 - 随机地图与BOSS系统版本 (优化版本)
#
# 配置切换说明:
# 要切换初始游戏配置，请修改第2994行的 GAME_CONFIG_PLAN 变量:
# - "PlanA": 默认配置（颓废的夏书文，1000金币，基础物品）
# - "PlanB": 隐藏配置（6个高级顾问，60万金币，特殊物品）
#
# 性能优化说明:
# 1. 表面缓存系统: 实现了地图、UI元素的缓存，避免重复绘制
# 2. 对象池: 减少Surface对象的创建和销毁开销
# 3. 脏矩形更新: 只重绘发生变化的区域
# 4. 字体管理优化: 单例模式的字体管理器，避免重复加载
# 5. 图像缓存: 优化的图像加载和缩放缓存系统
# 6. 数据结构优化: 使用__slots__减少内存占用
# 7. 预计算常量: 预计算常用的数值以减少运行时计算
# 8. 游戏循环优化: 减少不必要的重绘和内存分配
import pygame
import random
import sys
import os
import textwrap
import json
from pygame.locals import *
from enum import Enum
from dataclasses import dataclass, field
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from typing import List, Dict, Optional

# 导入模块化的组件
from skills import (
    SkillAttribute, EffectType, SkillEffect, Skill, SkillCategory, 
    SkillManager, SP_CONFIG, UNIFIED_SKILLS_DATABASE, ULTIMATE_LINES_DATABASE,
    skill_manager
)
from combat import CombatManager, BattleAction, BattleResult
from ui_renderer import UIRenderer

# ==================== 游戏常量和配置 ====================

# 屏幕和地图配置
SCREEN_WIDTH = 720  # 统一界面宽度
SCREEN_HEIGHT = 720  # 统一界面高度
TILE_SIZE = 60       # 调整格子尺寸以适配屏幕
MAP_SIZE = 12        # 保持12x12地图
FPS = 30             # 帧率

# 预计算常用值以提高性能
MAP_PIXEL_WIDTH = MAP_SIZE * TILE_SIZE
MAP_PIXEL_HEIGHT = MAP_SIZE * TILE_SIZE
MAP_START_X = (SCREEN_WIDTH - MAP_PIXEL_WIDTH) // 2
MAP_START_Y = (SCREEN_HEIGHT - MAP_PIXEL_HEIGHT) // 2
HALF_TILE_SIZE = TILE_SIZE // 2

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
MINT_GREEN = (152, 251, 152)  # 薄荷绿
MINT_GREEN_HOVER = (144, 238, 144)  # 薄荷绿悬停色
ORANGE = (255, 165, 0)  # 橙色
BATTLE_BG_COLOR = (100, 180, 100)
BATTLE_INFO_BG = (240, 240, 240)
MENU_BG = (50, 100, 180)
MENU_HOVER = (80, 130, 210)
HIGHLIGHT = YELLOW  # 用于标记默认出战顾问，复用YELLOW常量
PURPLE = (128, 0, 128)  # 紫色用于SP条

# ==================== 游戏枚举和数据结构 ====================

# 技能相关的枚举和类已移动到 skills.py 模块

# ==================== 技能数据库 ====================

# 技能数据库已移动到 skills.py 模块
# 技能管理系统已移动到 skills.py 模块

# ==================== 字体管理系统 ====================

class FontManager:
    """优化的字体管理器"""
    _fonts = {}
    _chinese_fonts = {}
    
    @classmethod
    def get_font(cls, size=24, chinese=True):
        """统一的字体获取方法"""
        cache = cls._chinese_fonts if chinese else cls._fonts
        if size not in cache:
            if chinese:
                cache[size] = cls._load_chinese_font(size)
            else:
                cache[size] = pygame.font.Font(None, size)
        return cache[size]
    
    @classmethod
    def _load_chinese_font(cls, size):
        """加载中文字体"""
        # 确保pygame字体模块已初始化
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
            
        font_names = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Microsoft YaHei", "Arial Unicode MS"]
        
        for font_name in font_names:
            try:
                return pygame.font.SysFont(font_name, size)
            except (pygame.error, OSError):
                continue
        
        # 如果没有找到中文字体，使用默认字体
        return pygame.font.Font(None, size)
    
    @classmethod
    def get_common_fonts(cls):
        """获取常用字体集合"""
        return {
            'font': cls.get_font(20),
            'small_font': cls.get_font(16),
            'battle_font': cls.get_font(20),
            'menu_font': cls.get_font(20),
            'large_font': cls.get_font(32),
            'title_font': cls.get_font(24)
        }

# 保持向后兼容的函数
def load_chinese_font(size):
    """保持向后兼容"""
    return FontManager.get_font(size, chinese=True)

def get_fonts():
    """保持向后兼容的字体获取函数"""
    fonts = FontManager.get_common_fonts()
    return fonts['font'], fonts['small_font'], fonts['battle_font'], fonts['menu_font']

# ==================== 图像管理系统 ====================

# 图像加载类
class ImageLoader:
    _image_cache = {}
    _scaled_cache = {}
    
    @staticmethod
    def clear_cache():
        """清空图像缓存"""
        ImageLoader._image_cache.clear()
        ImageLoader._scaled_cache.clear()
        
    @staticmethod
    def create_default_image(size, path=""):
        """创建默认图像"""
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill((100, 100, 100, 128))  # 半透明灰色
        return surface
# UNIFIED_SKILLS_DATABASE已废弃，统一使用UNIFIED_SKILLS_DATABASE

# 必杀技台词数据库
ULTIMATE_LINES_DATABASE = {
    # 我方顾问台词
    "ally": {
        "Deric的阴影": "看见阴影了吗？那就是你的结局！",
        "酒精打击": "你挣钱不就是来喝的吗",
        "心灵震爆": "感受心灵的力量吧！",
        "精神污染": "让混乱占据你的内心！",
        # 整合的技能台词
        "带队酗酒": "我都两杯了，你快点",
        "酒后逃逸": "这不是回家的车，我要~跳车~",
        "小嘴抹毒": "所以那是你同事吗？",
        "茶颜悦色": "你要跟我比夹夹，还是跟我比茶茶",
        "快乐小狗": "轻一点，不要打扰我偷听JJZ骂人",
        "躺平": "他不会看细节的",
        "绝世骰手": "阿巴次阿巴次，阿巴次阿巴次，喝！",
        "小考拉之怒": "相机就是我的女朋友",
        "沉默的牛马": "我去看了亚洲最大的gay吧",
        "威士忌之友": "你能不能闻到泥煤味",
        "躺平才是王道": "你又不是朱总，我怕个Der",
        "我要休产假了": "来陪邱总上厕所呀",
        "DGL逼我的": "我两个基地一直都排名前三",
        "表没对齐": "你自己调整一下",
        "情报总监上线": "我和你说哦",
        "摸下腹肌~~": "不是8块，是3圈！",
        "我来给你讲下原理": "董事长是我哥们",
        "ValueConcern!": "我跟他也不熟",
        "马总的关爱": "你就在我办公室偷偷吃方便面吧",
        "我来自珠海": "新伟你这样是不对的",
        "无锡的羔羊": "你见过白油倒流没",
        "来打羽毛球啊": "实在是干不动了",
        "G总,你不懂OPS": "这不是我想做的",
        "27岁500强总监": "我是DML史上最年轻的总监",
        "我和他谈笑风生": "我离职的原因是不好意思让董事长天天飞上海找我",
        "信不信我投诉你": "你为什么没有发现我的错误！",
        "我在XX时代": "那天我在仓库里，突然发现一颗烟头",
        "骚扰专家": "傅老师，你帮我写一下述职报告",
        "深呼吸": "你们要负全责！",
        "扣除效益": "所所所所有损失从你们费用里扣！",
        "浆板下水": "不用浆好像还比较快啊",
        "倒立攻击": "书文总，我们比下倒立",
        "治疗": "使用治疗技能恢复生命值",
        "default": "这就是我的必杀技！"
    }
}

# ==================== 技能管理系统 ====================

# 技能管理系统已移动到 skills.py 模块

# ==================== 字体管理系统 ====================

class FontManager:
    """优化的字体管理器"""
    _fonts = {}
    _chinese_fonts = {}
    
    @classmethod
    def get_font(cls, size=24, chinese=True):
        """统一的字体获取方法"""
        cache = cls._chinese_fonts if chinese else cls._fonts
        if size not in cache:
            if chinese:
                cache[size] = cls._load_chinese_font(size)
            else:
                cache[size] = pygame.font.Font(None, size)
        return cache[size]
    
    @classmethod
    def _load_chinese_font(cls, size):
        """加载中文字体"""
        # 确保pygame字体模块已初始化
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
            
        font_names = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Microsoft YaHei", "Arial Unicode MS"]
        
        for font_name in font_names:
            try:
                return pygame.font.SysFont(font_name, size)
            except (pygame.error, OSError):
                continue
        
        font_files = ["simhei.ttf", "msyh.ttc", "simsun.ttc"]
        for font_file in font_files:
            if os.path.exists(font_file):
                try:
                    return pygame.font.Font(font_file, size)
                except (pygame.error, OSError):
                    continue
        
        return pygame.font.Font(None, size)
    
    @classmethod
    def get_common_fonts(cls):
        """获取常用字体集合"""
        return {
            'font': cls.get_font(20),
            'small_font': cls.get_font(16),
            'battle_font': cls.get_font(20),
            'menu_font': cls.get_font(20),
            'large_font': cls.get_font(32),
            'title_font': cls.get_font(24)
        }

# 保持向后兼容的函数
def load_chinese_font(size):
    """保持向后兼容"""
    return FontManager.get_font(size, chinese=True)

def get_fonts():
    """保持向后兼容的字体获取函数"""
    fonts = FontManager.get_common_fonts()
    return fonts['font'], fonts['small_font'], fonts['battle_font'], fonts['menu_font']

# ==================== 图像管理系统 ====================

# 图像加载类
class ImageLoader:
    _image_cache = {}
    _scaled_cache = {}
    
    @staticmethod
    def clear_cache():
        """清空图像缓存"""
        ImageLoader._image_cache.clear()
        ImageLoader._scaled_cache.clear()
        
    @staticmethod
    def create_default_image(size, path=""):
        """创建默认图像"""
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill((100, 100, 100, 128))  # 半透明灰色
        
        # 在图像上绘制一些默认内容
        if size[0] > 20 and size[1] > 20:
            pygame.draw.rect(surface, (150, 150, 150), (2, 2, size[0]-4, size[1]-4), 2)
            
        return surface
    
    @staticmethod
    def load_image(path, size=None, use_default=True):
        """加载并缓存图像"""
        cache_key = f"{path}_{size}"
        
        # 检查缓存
        if cache_key in ImageLoader._image_cache:
            return ImageLoader._image_cache[cache_key]
        
        try:
            if not os.path.exists(path):
                if use_default:
                    default_image = ImageLoader.create_default_image(size or (TILE_SIZE, TILE_SIZE), path)
                    ImageLoader._image_cache[cache_key] = default_image
                    return default_image
                return None
            
            # 加载图像
            image = pygame.image.load(path).convert_alpha()
            
            # 缩放图像
            if size:
                image = pygame.transform.scale(image, size)
            
            # 缓存图像
            ImageLoader._image_cache[cache_key] = image
            return image
            
        except Exception as e:
            print(f"加载图片失败: {e}")
            if use_default:
                default_image = ImageLoader.create_default_image(size or (TILE_SIZE, TILE_SIZE), path)
                ImageLoader._image_cache[cache_key] = default_image
                return default_image
            return None


# ==================== 游戏工具函数 ====================

TILE_TYPES = {
    # 基础地块类型
    'flat': 0, 'wheat': 1, 'sand': 2, 'grass': 3, 
    'town': 4, 'rock': 5, 'wood': 6,
    # 特殊地块类型
    'chest': 7,        # 宝箱
    'shop': 8,         # 商店
    'training': 9,     # 训练中心
    'portal': 10,      # 传送门
    'mini_boss': 11,   # 小BOSS
    'stage_boss': 12   # 大BOSS
}

# 全局pygame对象（将在主程序入口处初始化）
screen = None
clock = None

# ==================== Surface工厂类 ====================

class SurfaceFactory:
    """Surface创建工厂类，减少重复的Surface创建代码"""
    
    @staticmethod
    def create_transparent_surface(size, color, alpha=128):
        """创建半透明Surface"""
        surface = pygame.Surface(size, pygame.SRCALPHA)
        if len(color) == 3:
            surface.fill((*color, alpha))
        else:
            surface.fill(color)
        return surface
    
    @staticmethod
    def create_overlay(screen_size, color, alpha=128):
        """创建全屏覆盖层"""
        return SurfaceFactory.create_transparent_surface(screen_size, color, alpha)
    
    @staticmethod
    def create_hp_bar_surface(width, height, percentage, color):
        """创建血条Surface"""
        fill_width = max(0, min(int(width * percentage), width))
        surface = pygame.Surface((fill_width, height), pygame.SRCALPHA)
        surface.fill((*color, 128))
        return surface
    
    @staticmethod
    def create_popup_background(width, height, bg_color=WHITE, alpha=240):
        """创建弹窗背景Surface"""
        return SurfaceFactory.create_transparent_surface((width, height), bg_color, alpha)

# ==================== 通用弹窗渲染器 ====================

class PopupRenderer:
    """通用弹窗渲染器，减少弹窗绘制代码的重复"""
    
    @staticmethod
    def draw_base_popup(screen, x, y, width, height, title="", bg_color=WHITE, alpha=240):
        """绘制基础弹窗框架"""
        # 绘制半透明背景遮罩
        overlay = SurfaceFactory.create_overlay((SCREEN_WIDTH, SCREEN_HEIGHT), BLACK, 180)
        screen.blit(overlay, (0, 0))
        
        # 绘制弹窗背景
        popup_bg = SurfaceFactory.create_popup_background(width, height, bg_color, alpha)
        screen.blit(popup_bg, (x, y))
        
        # 绘制边框
        pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
        
        # 绘制标题
        if title:
            title_font = FontManager.get_font(24)
            title_text = title_font.render(title, True, BLACK)
            title_rect = title_text.get_rect(center=(x + width//2, y + 30))
            screen.blit(title_text, title_rect)
            
            # 绘制标题下方分割线
            pygame.draw.line(screen, BLACK, (x + 20, y + 50), (x + width - 20, y + 50), 1)
        
        return popup_bg
    
    @staticmethod
    def draw_confirmation_popup(screen, message, width=400, height=200):
        """绘制确认弹窗"""
        x = SCREEN_WIDTH//2 - width//2
        y = SCREEN_HEIGHT//2 - height//2
        
        PopupRenderer.draw_base_popup(screen, x, y, width, height, "确认")
        
        # 绘制消息文字
        font = FontManager.get_font(20)
        draw_multiline_text(screen, message, font, BLACK, x + 20, y + 70, width - 40)

# 文本自动换行函数
def wrap_text(text, font, max_width):
    """将文本按指定宽度自动换行，支持中文"""
    lines = []
    current_line = ""
    
    # 对于中文文本，逐字符检查换行
    for char in text:
        # 尝试添加当前字符
        test_line = current_line + char
        # 计算测试行宽度
        line_width = font.size(test_line)[0]
        
        if line_width <= max_width:
            current_line = test_line
        else:
            # 超过宽度则另起一行
            if current_line:
                lines.append(current_line)
            current_line = char
    
    # 添加最后一行
    if current_line:
        lines.append(current_line)
    
    return lines

# 绘制多行文本函数
def draw_multiline_text(surface, text, font, color, x, y, max_width, line_spacing=5):
    """绘制自动换行的多行文本"""
    lines = wrap_text(text, font, max_width)
    current_y = y
    
    for line in lines:
        text_surface = font.render(line, True, color)
        surface.blit(text_surface, (x, current_y))
        current_y += font.size(line)[1] + line_spacing  # 增加行间距
    
    return current_y  # 返回最后一行的y坐标，方便后续绘制

def draw_multiline_text_with_background(surface, text, font, color, x, y, max_width, line_spacing=5, bg_color=(255, 255, 255, 128), padding=5):
    """绘制带半透明背景的自动换行多行文本"""
    lines = wrap_text(text, font, max_width)
    if not lines:
        return y
    
    # 计算总文本区域大小
    total_height = 0
    max_line_width = 0
    for line in lines:
        line_width, line_height = font.size(line)
        max_line_width = max(max_line_width, line_width)
        total_height += line_height + line_spacing
    total_height -= line_spacing  # 移除最后一行的行间距
    
    # 绘制半透明背景
    bg_surface = pygame.Surface((max_line_width + 2 * padding, total_height + 2 * padding), pygame.SRCALPHA)
    bg_surface.fill(bg_color)
    surface.blit(bg_surface, (x - padding, y - padding))
    
    # 绘制文本
    current_y = y
    for line in lines:
        text_surface = font.render(line, True, color)
        surface.blit(text_surface, (x, current_y))
        current_y += font.size(line)[1] + line_spacing
    
    return current_y  # 返回最后一行的y坐标，方便后续绘制

def draw_status_icons(surface, pokemon, x, y, icon_size=30, spacing=5, caster_filter=None):
    """绘制状态效果图标
    Args:
        surface: 绘制表面
        pokemon: 顾问对象
        x: 起始x坐标
        y: 起始y坐标
        icon_size: 图标大小
        spacing: 图标间距
        caster_filter: 过滤器，只显示特定施放者的效果 ("self", "enemy", None表示显示所有)
    Returns:
        绘制的图标数量
    """
    icon_count = 0
    current_x = x
    font = FontManager.get_font(12)
    arrow_font = FontManager.get_font(16)
    
    # 检查状态修改效果
    stat_mods = pokemon.status_effects.get("stat_modifiers", {})
    attack_mult = stat_mods.get("attack_multiplier", 1.0)
    defense_mult = stat_mods.get("defense_multiplier", 1.0)
    turns_remaining = stat_mods.get("turns_remaining", 0)
    caster = stat_mods.get("caster", "self")  # 默认为自己施放
    
    # 应用施放者过滤
    if caster_filter and caster != caster_filter:
        turns_remaining = 0  # 不显示不符合过滤条件的效果
    
    if turns_remaining > 0:
        # 攻击力状态图标
        if attack_mult != 1.0:
            # 绘制图标背景
            icon_rect = pygame.Rect(current_x, y, icon_size, icon_size)
            pygame.draw.rect(surface, (50, 50, 50, 180), icon_rect)
            pygame.draw.rect(surface, PURPLE, icon_rect, 2)
            
            # 绘制ATK文字
            atk_text = font.render("ATK", True, WHITE)
            atk_rect = atk_text.get_rect(center=(current_x + icon_size//2, y + icon_size//3))
            surface.blit(atk_text, atk_rect)
            
            # 绘制箭头和数值
            if attack_mult > 1.0:
                arrow = "↑"
                arrow_color = GREEN
                value = f"+{int((attack_mult - 1) * 100)}%"
            else:
                arrow = "↓"
                arrow_color = RED
                value = f"-{int((1 - attack_mult) * 100)}%"
            
            arrow_text = arrow_font.render(arrow, True, arrow_color)
            arrow_rect = arrow_text.get_rect(center=(current_x + icon_size//2, y + icon_size*2//3))
            surface.blit(arrow_text, arrow_rect)
            
            # 绘制数值（在图标右下角）
            value_text = font.render(value, True, PURPLE)
            surface.blit(value_text, (current_x + icon_size + 2, y + icon_size - 15))
            
            # 绘制剩余回合数（在图标右上角）
            turns_text = font.render(str(turns_remaining), True, YELLOW)
            surface.blit(turns_text, (current_x + icon_size - 8, y - 5))
            
            current_x += icon_size + spacing + 25  # 为数值文字留出空间
            icon_count += 1
        
        # 防御力状态图标
        if defense_mult != 1.0:
            # 绘制图标背景
            icon_rect = pygame.Rect(current_x, y, icon_size, icon_size)
            pygame.draw.rect(surface, (50, 50, 50, 180), icon_rect)
            pygame.draw.rect(surface, PURPLE, icon_rect, 2)
            
            # 绘制DEF文字
            def_text = font.render("DEF", True, WHITE)
            def_rect = def_text.get_rect(center=(current_x + icon_size//2, y + icon_size//3))
            surface.blit(def_text, def_rect)
            
            # 绘制箭头和数值
            if defense_mult > 1.0:
                arrow = "↑"
                arrow_color = GREEN
                value = f"+{int((defense_mult - 1) * 100)}%"
            else:
                arrow = "↓"
                arrow_color = RED
                value = f"-{int((1 - defense_mult) * 100)}%"
            
            arrow_text = arrow_font.render(arrow, True, arrow_color)
            arrow_rect = arrow_text.get_rect(center=(current_x + icon_size//2, y + icon_size*2//3))
            surface.blit(arrow_text, arrow_rect)
            
            # 绘制数值（在图标右下角）
            value_text = font.render(value, True, PURPLE)
            surface.blit(value_text, (current_x + icon_size + 2, y + icon_size - 15))
            
            # 绘制剩余回合数（在图标右上角）
            turns_text = font.render(str(turns_remaining), True, YELLOW)
            surface.blit(turns_text, (current_x + icon_size - 8, y - 5))
            
            current_x += icon_size + spacing + 25  # 为数值文字留出空间
            icon_count += 1
    
    # 检查连续伤害效果
    for effect in pokemon.status_effects.get("continuous_damage", []):
        effect_caster = effect.get("caster", "self")  # 默认为自己施放
        # 应用施放者过滤
        if caster_filter and effect_caster != caster_filter:
            continue
            
        # 绘制DOT图标背景
        icon_rect = pygame.Rect(current_x, y, icon_size, icon_size)
        pygame.draw.rect(surface, (80, 20, 20, 180), icon_rect)  # 深红色背景
        pygame.draw.rect(surface, RED, icon_rect, 2)
        
        # 绘制DOT文字
        dot_text = font.render("DOT", True, WHITE)
        dot_rect = dot_text.get_rect(center=(current_x + icon_size//2, y + icon_size//2))
        surface.blit(dot_text, dot_rect)
        
        # 绘制伤害数值
        damage_text = font.render(str(effect["damage"]), True, RED)
        surface.blit(damage_text, (current_x + icon_size + 2, y + icon_size - 15))
        
        # 绘制剩余回合数
        turns_text = font.render(str(effect["turns"]), True, YELLOW)
        surface.blit(turns_text, (current_x + icon_size - 8, y - 5))
        
        current_x += icon_size + spacing + 20
        icon_count += 1
    
    # 检查延迟效果
    for effect in pokemon.status_effects.get("delayed_effects", []):
        effect_caster = effect.get("caster", "self")  # 默认为自己施放
        # 应用施放者过滤
        if caster_filter and effect_caster != caster_filter:
            continue
            
        # 绘制延迟效果图标背景
        icon_rect = pygame.Rect(current_x, y, icon_size, icon_size)
        pygame.draw.rect(surface, (128, 64, 0, 180), icon_rect)  # 橙色背景
        pygame.draw.rect(surface, ORANGE, icon_rect, 2)
        
        # 绘制延迟效果文字
        delay_text = font.render("DELAY", True, WHITE)
        delay_rect = delay_text.get_rect(center=(current_x + icon_size//2, y + icon_size//2 - 5))
        surface.blit(delay_text, delay_rect)
        
        # 绘制剩余回合数
        remaining_turns = effect["trigger_turn"] - pokemon.battle_turn_counter
        if remaining_turns > 0:
            turns_text = font.render(str(remaining_turns), True, ORANGE)
            turns_rect = turns_text.get_rect(center=(current_x + icon_size//2, y + icon_size//2 + 8))
            surface.blit(turns_text, turns_rect)
        
        current_x += icon_size + spacing + 25
        icon_count += 1
    
    # 检查连续治疗效果
    for effect in pokemon.status_effects.get("continuous_heal", []):
        effect_caster = effect.get("caster", "self")  # 默认为自己施放
        # 应用施放者过滤
        if caster_filter and effect_caster != caster_filter:
            continue
            
        # 绘制HOT图标背景
        icon_rect = pygame.Rect(current_x, y, icon_size, icon_size)
        pygame.draw.rect(surface, (20, 80, 20, 180), icon_rect)  # 深绿色背景
        pygame.draw.rect(surface, GREEN, icon_rect, 2)
        
        # 绘制HOT文字
        hot_text = font.render("HOT", True, WHITE)
        hot_rect = hot_text.get_rect(center=(current_x + icon_size//2, y + icon_size//2))
        surface.blit(hot_text, hot_rect)
        
        # 绘制治疗数值
        heal_text = font.render(str(effect["heal"]), True, GREEN)
        surface.blit(heal_text, (current_x + icon_size + 2, y + icon_size - 15))
        
        # 绘制剩余回合数
        turns_text = font.render(str(effect["turns"]), True, YELLOW)
        surface.blit(turns_text, (current_x + icon_size - 8, y - 5))
        
        current_x += icon_size + spacing + 20
        icon_count += 1
    
    return icon_count


# ==================== 游戏配置系统 ====================

# 统一的游戏配置管理器
class GameConfig:
    """统一的游戏配置管理器，整合所有配置类"""
    
    class Images:
        """图像资源配置"""
        player_image = "images/player.png"
        flat_image = "images/tiles/flat.png"
        wheat_image = "images/tiles/wheat.png"
        sand_image = "images/tiles/sand.png"
        grass_image = "images/tiles/grass.png"
        town_image = "images/tiles/town.png"
        rock_image = "images/tiles/rock.png"
        wood_image = "images/tiles/wood.png"
        chest_image = "images/tiles/treasure.png"
        shop_image = "images/tiles/shop.png"
        training_image = "images/tiles/training_center.png"
        portal_image = "images/tiles/portal.png"
        mini_boss_image = "images/tiles/PS.png"
        stage_boss_image = "images/tiles/PR.png"
        battle_background = "images/battle/bg.png"
        boss_battle_background = "images/battle/boss_bg.png"
        ut_empty_image = "images/ui/ut_empty.png"
        
        @staticmethod
        def get_pokemon_image(pokemon_name):
            """获取顾问图像路径"""
            pokemon_images = {
                "颓废的夏书文": "images/pokemon/SW1.png",
                "进击的夏书文": "images/pokemon/SW2.png",
                "害羞的吕瑞怡": "images/pokemon/RY1.png",
                "浪浪山吕瑞怡": "images/pokemon/RY2.png",
                "沉默的傅雪松": "images/pokemon/FXS1.png",
                "奔放的傅雪松": "images/pokemon/FXS2.png",
                "蚝汁傅雪松": "images/pokemon/FXS3.png",
                "DCC的托马斯": "images/pokemon/TT1.png",
                "做牛做马托马斯": "images/pokemon/TT2.png",
                "全旋托马斯": "images/pokemon/TT3.png",
                "没有干劲的随意": "images/pokemon/SY1.png",
                "满血隋毅": "images/pokemon/SY2.png",
                "超神隋总": "images/pokemon/SY3.png",
                "讲课的Raymond": "images/pokemon/Raymond1.png",
                "ValueConcernRaymond": "images/pokemon/Raymond2.png",
                "做表的Delia": "images/pokemon/Delia1.png",
                "大嘴Delia": "images/pokemon/Delia2.png",
                "酒后Delia": "images/pokemon/Delia3.png",
                "人畜无害的孙皓": "images/pokemon/SH1.png",
                "流浪的宏宇": "images/pokemon/HY1.png",
                # 客户顾问
                "梅折": "images/pokemon/client1.png",
                "李巷阳": "images/pokemon/client2.png",
                "袁钱保": "images/pokemon/client3.png",
                "王小容": "images/pokemon/client4.png",
                # 新增的野外顾问
                "夏港": "images/pokemon/XG.png",
                "何须强": "images/pokemon/HXQ.png",
            }
            return pokemon_images.get(pokemon_name)

# 保持向后兼容的图像配置类
class ImageConfig:
    player_image = "images/player.png"
    flat_image = "images/tiles/flat.png"
    wheat_image = "images/tiles/wheat.png"
    sand_image = "images/tiles/sand.png"
    grass_image = "images/tiles/grass.png"
    town_image = "images/tiles/town.png"
    rock_image = "images/tiles/rock.png"
    wood_image = "images/tiles/wood.png"
    chest_image = "images/tiles/treasure.png"
    shop_image = "images/tiles/shop.png"
    training_image = "images/tiles/training_center.png"
    portal_image = "images/tiles/portal.png"
    mini_boss_image = "images/tiles/PS.png"
    stage_boss_image = "images/tiles/PR.png"
    battle_background = "images/battle/bg.png"
    boss_battle_background = "images/battle/boss_bg.png"  # BOSS战背景
    ut_empty_image = "images/ui/ut_empty.png"  # UT耗尽提示图片
    pokemon_images = {
        "颓废的夏书文": "images/pokemon/SW1.png",
        "进击的夏书文": "images/pokemon/SW2.png",
        "害羞的吕瑞怡": "images/pokemon/RY1.png",
        "浪浪山吕瑞怡": "images/pokemon/RY2.png",
        "沉默的傅雪松": "images/pokemon/FXS1.png",
        "奔放的傅雪松": "images/pokemon/FXS2.png",
        "蚝汁傅雪松": "images/pokemon/FXS3.png",
        "DCC的托马斯": "images/pokemon/TT1.png",
        "做牛做马托马斯": "images/pokemon/TT2.png",
        "全旋托马斯": "images/pokemon/TT3.png",
        "没有干劲的随意": "images/pokemon/SY1.png",
        "满血隋毅": "images/pokemon/SY2.png",
        "超神隋总": "images/pokemon/SY3.png",
        "讲课的Raymond": "images/pokemon/Raymond1.png",
        "ValueConcernRaymond": "images/pokemon/Raymond2.png",
        "做表的Delia": "images/pokemon/Delia1.png",
        "大嘴Delia": "images/pokemon/Delia2.png",
        "酒后Delia": "images/pokemon/Delia3.png",
        "人畜无害的孙皓": "images/pokemon/SH1.png",
        "流浪的宏宇": "images/pokemon/HY1.png",
        # 客户顾问
        "梅折": "images/pokemon/client1.png",
        "李巷阳": "images/pokemon/client2.png",
        "袁钱保": "images/pokemon/client3.png",
        "王小容": "images/pokemon/client4.png",
        # 新增的野外顾问
        "夏港": "images/pokemon/XG.png",
        "何须强": "images/pokemon/HXQ.png",
        "张新炜": "images/pokemon/ZXW.png",
        "严斤": "images/pokemon/YJ.png",
        "半血小萱": "images/pokemon/LLX1.png",
        "泥潭中的小萱": "images/pokemon/LLX2.png",
        "拉膜圣手李小萱": "images/pokemon/LLX3.png",
        # BOSS顾问
        "质量总监ZZZ": "images/pokemon/boss1.png",
        "宇宙质量总监ZZZ": "images/pokemon/boss2.png",
        "HR总监JJZ": "images/pokemon/boss3.png",
        "平地挖坑刚子": "images/pokemon/boss4.png",
        "平静的老李": "images/pokemon/boss5.png",
        "暴怒的老李": "images/pokemon/boss6.png"
    }

# 经验值增长类型配置
class ExperienceConfig:
    # Pokemon Yellow风格的经验值曲线
    @staticmethod
    def get_exp_for_level(level, growth_type="medium_fast"):
        """
        获取达到指定等级所需的总经验值
        growth_type: "fast", "medium_fast", "medium_slow", "slow"
        """
        if level <= 1:
            return 0
            
        if growth_type == "fast":
            # 快速增长: 4 * n^3 / 5
            return int(4 * (level ** 3) / 5)
        elif growth_type == "medium_fast":
            # 中等快速增长: n^3
            return level ** 3
        elif growth_type == "medium_slow":
            # 中等慢速增长: 6/5 * n^3 - 15 * n^2 + 100 * n - 140
            return int(6/5 * (level ** 3) - 15 * (level ** 2) + 100 * level - 140)
        elif growth_type == "slow":
            # 慢速增长: 5 * n^3 / 4
            return int(5 * (level ** 3) / 4)
        else:
            return level ** 3  # 默认使用medium_fast
    
    @staticmethod
    def get_exp_to_next_level(current_level, growth_type="medium_fast"):
        """获取从当前等级升到下一级所需的经验值"""
        current_total = ExperienceConfig.get_exp_for_level(current_level, growth_type)
        next_total = ExperienceConfig.get_exp_for_level(current_level + 1, growth_type)
        return next_total - current_total
    
    @staticmethod
    def get_battle_exp_reward(defeated_level, victor_level):
        """
        计算战斗获得的经验值
        基于Pokemon的经验值奖励公式
        """
        # 基础经验值 (根据被击败者等级)
        base_exp = defeated_level * 7
        
        # 等级差异修正
        level_diff = defeated_level - victor_level
        if level_diff > 0:
            # 击败更高等级的敌人获得更多经验
            multiplier = 1.0 + min(level_diff * 0.1, 0.5)  # 最多50%加成
        else:
            # 击败低等级敌人经验递减
            multiplier = max(1.0 + level_diff * 0.05, 0.3)  # 最少30%经验
        
        return int(base_exp * multiplier)

# 顾问配置
class PokemonConfig:
    base_data = {
        "颓废的夏书文": {
            "hp": 35, "attack": 55, "defense": 40,
            "advantages": ["结构化", "PS", "共情", "耐心"],
            "disadvantages": ["节操", "networking"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "Empathy"},
                {"name": "酒精打击"},
                {"name": "酒仙"},
                {"name": "带队酗酒"},
                {"name": "问题解决"}
            ]
        },
        "进击的夏书文": {
            "hp": 60, "attack": 90, "defense": 55,
            "advantages": ["结构化", "PS", "共情", "韧性", "content", "耐心"],
            "disadvantages": ["节操", "networking"],
            "growth_type": "medium_slow",
            "moves": [
                {"name": "酒后逃逸"},
                {"name": "织条毯子"},
                {"name": "酒精打击"},
                {"name": "问题解决"}
            ]
        },
        "害羞的吕瑞怡": {
            "hp": 35, "attack": 55, "defense": 40,
            "advantages": ["共情", "节操", "networking"],
            "disadvantages": ["PS", "韧性", "content", "耐心"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "小嘴抹毒"},
                {"name": "快乐小狗"},
                {"name": "茶颜悦色"},
                {"name": "躺平"}
            ]
        },
        "浪浪山吕瑞怡": {
            "hp": 60, "attack": 90, "defense": 55,
            "advantages": ["共情", "节操", "networking"],
            "disadvantages": ["PS", "韧性", "content", "耐心"],
            "growth_type": "medium_slow",
            "moves": [
                {"name": "小嘴抹毒"},
                {"name": "快乐小狗"},
                {"name": "茶颜悦色"},
                {"name": "躺平"},
                {"name": "绝世骰手"},
                {"name": "雪松杀手"},
                {"name": "钓鱼执法"},
                {"name": "PTO"}
            ]
        },
        "沉默的傅雪松": {
            "hp": 30, "attack": 56, "defense": 35,
            "advantages": ["共情", "体力", "耐心"],
            "disadvantages": ["节操", "networking"],
            "growth_type": "fast",
            "moves": [
                {"name": "小考拉之怒"},
                {"name": "躺平"},
                {"name": "我有意见！"}
            ]
        },
        "奔放的傅雪松": {
            "hp": 55, "attack": 81, "defense": 60,
            "advantages": ["共情", "体力", "韧性", "耐心"],
            "disadvantages": ["节操", "networking"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "小考拉之怒"},
                {"name": "躺平"},
                {"name": "我有意见！"},
                {"name": "沉默的牛马"},
                {"name": "浆板下水"}
            ]
        },
        "蚝汁傅雪松": {
            "hp": 85, "attack": 101, "defense": 80,
            "advantages": ["共情", "体力", "PS", "耐心"],
            "disadvantages": ["节操", "networking"],
            "growth_type": "slow",
            "moves": [
                {"name": "小考拉之怒"},
                {"name": "躺平"},
                {"name": "我有意见！"},
                {"name": "沉默的牛马"},
                {"name": "浆板下水"},
                {"name": "威士忌之友"},
                {"name": "倒立攻击"}
            ]
        },
        "没有干劲的随意": {
            "hp": 45, "attack": 30, "defense": 35,
            "advantages": ["content", "PS", "体力"],
            "disadvantages": ["节操", "networking", "耐心"],
            "growth_type": "fast",
            "moves": [
                {"name": "躺平才是王道"},
                {"name": "奶茶攻击"},
                {"name": "心灵震爆"},
                {"name": "问题解决"},
                {"name": "嘲讽"}
            ]
        },
        "满血隋毅": {
            "hp": 50, "attack": 20, "defense": 50,
            "advantages": ["content", "PS", "勇气", "体力"],
            "disadvantages": ["节操", "networking", "耐心"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "躺平才是王道"},
                {"name": "奶茶攻击"},
                {"name": "心灵震爆"},
                {"name": "我要休产假了"},
                {"name": "我有意见！"},
                {"name": "问题解决"},
                {"name": "嘲讽"}
            ]
        },
        "超神隋总": {
            "hp": 70, "attack": 60, "defense": 70,
            "advantages": ["content", "PS", "勇气", "韧性", "体力"],
            "disadvantages": ["节操", "networking", "耐心"],
            "growth_type": "medium_slow",
            "moves": [
                {"name": "躺平才是王道"},
                {"name": "奶茶攻击"},
                {"name": "心灵震爆"},
                {"name": "我要休产假了"},
                {"name": "我有意见！"},
                {"name": "DGL逼我的"},
                {"name": "问题解决"},
                {"name": "嘲讽"}
            ]
        },
        "做表的Delia": {
            "hp": 30, "attack": 56, "defense": 35,
            "advantages": ["节操", "networking", "共情", "耐心"],
            "disadvantages": ["PS", "韧性", "体力"],
            "growth_type": "fast",
            "moves": [
                {"name": "表没对齐"},
                {"name": "画饼术"},
                {"name": "PTO"},
                {"name": "我有意见！"}
            ]
        },
        "大嘴Delia": {
            "hp": 55, "attack": 81, "defense": 60,
            "advantages": ["节操", "networking", "体力", "共情", "耐心"],
            "disadvantages": ["PS", "韧性"],
            "growth_type": "slow",
            "moves": [
                {"name": "表没对齐"},
                {"name": "画饼术"},
                {"name": "PTO"},
                {"name": "情报总监上线"},
                {"name": "酒精打击"}
            ]
        },
        "酒后Delia": {
            "hp": 85, "attack": 101, "defense": 80,
            "advantages": ["节操", "networking", "勇气", "体力", "共情", "耐心"],
            "disadvantages": ["PS", "韧性"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "表没对齐"},
                {"name": "画饼术"},
                {"name": "PTO"},
                {"name": "情报总监上线"},
                {"name": "酒精打击"},
                {"name": "摸下腹肌~~"}
            ]
        },
        "讲课的Raymond": {
            "hp": 40, "attack": 45, "defense": 35,
            "advantages": ["PS", "content", "勇气", "韧性", "耐心"],
            "disadvantages": ["节操"],
            "growth_type": "medium_slow",
            "moves": [
                {"name": "我来给你讲下原理"},
                {"name": "建模"},
                {"name": "循循善诱"},
                {"name": "心灵震爆"},
                {"name": "问题解决"}
            ]
        },
        "ValueConcernRaymond": {
            "hp": 80, "attack": 80, "defense": 70,
            "advantages": ["PS", "content", "勇气", "韧性"],
            "disadvantages": ["节操"],
            "growth_type": "fast",
            "moves": [
                {"name": "我来给你讲下原理"},
                {"name": "建模"},
                {"name": "循循善诱"},
                {"name": "ValueConcern!"},
                {"name": "我有意见！"},
                {"name": "问题解决"}
            ]
        },
         "DCC的托马斯": {
            "hp": 45, "attack": 30, "defense": 35,
            "advantages": ["content", "PS"],
            "disadvantages": ["节操", "networking", "体力", "耐心"],
            "growth_type": "slow",
            "moves": [
                {"name": "马总的关爱"},
                {"name": "我有意见！"},
                {"name": "躺平"},
                {"name": "问题解决"}
            ]
        },
        "做牛做马托马斯": {
            "hp": 50, "attack": 20, "defense": 50,
            "advantages": ["content", "PS", "韧性"],
            "disadvantages": ["节操", "networking", "体力", "耐心"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "马总的关爱"},
                {"name": "我有意见！"},
                {"name": "躺平"},
                {"name": "我来自珠海"},
                {"name": "奶茶攻击"},
                {"name": "问题解决"}
            ]
        },
        "全旋托马斯": {
            "hp": 70, "attack": 60, "defense": 70,
            "advantages": ["content", "PS", "勇气", "韧性"],
            "disadvantages": ["节操", "networking", "体力", "耐心"],
            "growth_type": "medium_slow",
            "moves": [
                {"name": "治疗"},
                {"name": "李代桃僵"},
                {"name": "鲁莽"},
                {"name": "我有意见！"},
                {"name": "沉默的牛马"},
                {"name": "浆板下水"}
            ]
        },
        "人畜无害的孙皓": {
            "hp": 50, "attack": 20, "defense": 50,
            "advantages": ["content", "PS", "勇气", "韧性", "体力", "耐心"],
            "disadvantages": ["节操", "networking"],
            "growth_type": "fast",
            "moves": [
                {"name": "来打羽毛球啊"},
                {"name": "循循善诱"},
                {"name": "我有意见！"},
                {"name": "躺平"}
            ]
        },
        "流浪的宏宇": {
            "hp": 50, "attack": 20, "defense": 50,
            "advantages": ["content", "PS", "勇气", "韧性", "体力", "耐心"],
            "disadvantages": ["节操", "networking"],
            "growth_type": "slow",
            "moves": [
                {"name": "G总,你不懂OPS"},
                {"name": "循循善诱"},
                {"name": "我有意见！"},
                {"name": "躺平"}
            ]
        },
        # 客户顾问数据
        "梅折": {
            "hp": 44, "attack": 51, "defense": 41,
            "advantages": ['节操'],
            "disadvantages": ['content', 'PS', '结构化', '勇气', '韧性'],
            "growth_type": "slow",
            "moves": [
                {"name": "腐蚀"}, 
                {"name": "唧唧歪歪"}, 
                {"name": "在你来前"}, 
                {"name": "感到冒犯"}
            ]
        },
        "李巷阳": {
            "hp": 43, "attack": 51, "defense": 35,
            "advantages": ['节操'],
            "disadvantages": ['content', 'PS', '结构化', '勇气', '韧性'],
            "growth_type": "fast",
            "moves": [
                {"name": "初级扯皮"}, 
                {"name": "磨磨蹭蹭"}, 
                {"name": "唧唧歪歪"}, 
                {"name": "感到冒犯"}
            ]
        },
        "袁钱保": {
            "hp": 39, "attack": 57, "defense": 38,
            "advantages": ['节操'],
            "disadvantages": ['content', 'PS', '结构化', '勇气', '韧性'],
            "growth_type": "slow",
            "moves": [
                {"name": "初级扯皮"}, 
                {"name": "磨磨蹭蹭"}, 
                {"name": "在你来前"}, 
                {"name": "感到冒犯"}
            ]
        },
        "王小容": {
            "hp": 41, "attack": 56, "defense": 44,
            "advantages": ['节操'],
            "disadvantages": ['content', 'PS', '结构化', '勇气', '韧性'],
            "growth_type": "fast",
            "moves": [
                {"name": "初级扯皮"}, 
                {"name": "技术创新"}, 
                {"name": "在你来前"}, 
                {"name": "感到冒犯"}
            ]
        },
        # BOSS顾问数据
        "质量总监ZZZ": {
            "hp": 150, "attack": 70, "defense": 50,
            "advantages": [],
            "disadvantages": ["共情"],
            "growth_type": "medium_fast",
            "level": 15,
            "reward": {
                "pokemon": "讲课的Raymond",
                "items": ["UT补充剂", "超级伤药", "必杀技学习盲盒"],
                "money": 500
            },
            "moves": [
                {"name": "27岁500强总监"},
                {"name": "PUA"},
                {"name": "腐蚀"},
                {"name": "哼哼唧唧"}
            ]
        },
        "宇宙质量总监ZZZ": {
            "hp": 180, "attack": 65, "defense": 60,
            "advantages": ["共情"],
            "disadvantages": [],
            "growth_type": "medium_slow",
            "level": 18,
            "reward": {
                "pokemon": "做表的Delia",
                "items": ["UT补充剂", "精灵球", "必杀技学习盲盒"],
                "money": 700
            },
            "moves": [
                {"name": "我和他谈笑风生"},
                {"name": "PUA"},
                {"name": "画饼术"},
                {"name": "团队增殖"}
            ]
        },
        "HR总监JJZ": {
            "hp": 300, "attack": 90, "defense": 80,
            "advantages": [],
            "disadvantages": ["共情"],
            "growth_type": "fast",
            "level": 30,
            "stage": 1,
            "reward": {
                "pokemon": "人畜无害的孙皓",
                "items": ["UT补充剂", "超级伤药", "必杀技学习盲盒"],
                "money": 2000
            },
            "moves": [
                {"name": "信不信我投诉你"},
                {"name": "PUA"},
                {"name": "开始抬杠"},
                {"name": "凌晨4点的太阳"}
            ]
        },
        "平静的老李": {
            "hp": 500, "attack": 120, "defense": 100,
            "advantages": ["共情", "结构化"],
            "disadvantages": ["体力"],
            "growth_type": "slow",
            "level": 50,
            "stage": 2,
            "reward": {
                "pokemon": "流浪的宏宇",
                "items": ["UT补充剂", "超级伤药", "精灵球", "必杀技学习盲盒"],
                "money": 5000
            },
            "moves": [
                {"name": "深呼吸"},
                {"name": "开始抬杠"},
                {"name": "大海无量"},
                {"name": "熬夜攻击"}
            ]
        },
        "暴怒的老李": {
            "hp": 800, "attack": 160, "defense": 130,
            "advantages": ["体力", "韧性", "节操"],
            "disadvantages": ["PS", "content"],
            "growth_type": "slow",
            "level": 70,
            "stage": 3,
            "reward": {
                "pokemon": "超神隋总",
                "items": ["UT补充剂", "超级伤药", "精灵球", "大师球", "必杀技学习盲盒"],
                "money": 10000
            },
            "moves": [
                {"name": "扣除效益"},
                {"name": "大海无量"},
                {"name": "无偿加班"},
                {"name": "既要又要还要"}
            ]
        },
        "平地挖坑刚子": {
            "hp": 350, "attack": 100, "defense": 85,
            "advantages": ["节操"],
            "disadvantages": ["共情", "PS", "content"],
            "growth_type": "slow",
            "level": 45,
            "reward": {
                "pokemon": "害羞的吕瑞怡",
                "items": ["UT补充剂", "超级伤药", "精灵球", "必杀技学习盲盒"],
                "money": 3000
            },
            "moves": [
                {"name": "我在XX时代"},
                {"name": "骚扰专家"},
                {"name": "开始抬杠"},
                {"name": "既要又要还要"}
            ]
        },
        # 新增的野外顾问
        "夏港": {
            "hp": 50, "attack": 65, "defense": 42,
            "advantages": ["节操", "耐心"],
            "disadvantages": ["content", "PS", "结构化", "勇气", "韧性"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "我有意见！"},
                {"name": "感到冒犯"},
                {"name": "既要又要还要"},
                {"name": "技术创新"}
            ]
        },
        "何须强": {
            "hp": 49, "attack": 58, "defense": 49,
            "advantages": ["节操"],
            "disadvantages": ["content", "PS", "结构化", "勇气", "韧性", "耐心"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "磨磨蹭蹭"},
                {"name": "开始抬杠"},
                {"name": "感到冒犯"},
                {"name": "我有意见！"}
            ]
        },
        "张新炜": {
            "hp": 40, "attack": 56, "defense": 46,
            "advantages": ["节操"],
            "disadvantages": ["content", "PS", "结构化", "勇气", "韧性", "耐心"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "哼哼唧唧"},
                {"name": "开始抬杠"},
                {"name": "我有意见！"},
                {"name": "心灵震爆"}
            ]
        },
        "严斤": {
            "hp": 46, "attack": 65, "defense": 43,
            "advantages": ["节操", "耐心"],
            "disadvantages": ["content", "PS", "结构化", "勇气", "韧性"],
            "growth_type": "slow",
            "moves": [
                {"name": "我有意见！"},
                {"name": "感到冒犯"},
                {"name": "既要又要还要"},
                {"name": "技术创新"}
            ]
        },
        "半血小萱": {
            "hp": 45, "attack": 60, "defense": 40,
            "advantages": ["PS", "韧性", "共情", "结构化"],
            "disadvantages": ["体力", "content", "勇气", "耐心"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "织条毯子"},
                {"name": "我有意见！"},
                {"name": "躺平"},
                {"name": "问题解决"},
                {"name": "鼓舞"}
            ]
        },
        "泥潭中的小萱": {
            "hp": 75, "attack": 90, "defense": 65,
            "advantages": ["PS", "韧性", "共情", "结构化"],
            "disadvantages": ["体力", "content", "耐心"],
            "growth_type": "medium_slow",
            "moves": [
                {"name": "织条毯子"},
                {"name": "问题解决"},
                {"name": "鼓舞"},
                {"name": "凌晨4点的太阳"},
                {"name": "躺平才是王道"},
                {"name": "我有意见！"},
                {"name": "天下兵马大元帅"}
            ]
        },
        "拉膜圣手李小萱": {
            "hp": 120, "attack": 130, "defense": 95,
            "advantages": ["PS", "韧性", "共情", "结构化", "勇气"],
            "disadvantages": ["体力", "耐心"],
            "growth_type": "slow",
            "moves": [
                {"name": "织条毯子"},
                {"name": "问题解决"},
                {"name": "鼓舞"},
                {"name": "凌晨4点的太阳"},
                {"name": "躺平才是王道"},
                {"name": "无锡的女武神"},
                {"name": "天下兵马大元帅"}
            ]
        },

    }
    
    # 小BOSS配置
    mini_bosses = [
        {
            "name": "质量总监ZZZ",
            "level": 15,
            "hp": 150,
            "attack": 70,
            "defense": 50,
            "advantages": [],
            "disadvantages": ["共情"],
            "growth_type": "medium_fast",
            "moves": [
                {"name": "27岁500强总监"},
                {"name": "PUA"},
                {"name": "腐蚀"},
                {"name": "哼哼唧唧"}
            ],
            "reward": {
                "pokemon": "讲课的Raymond",
                "items": ["UT补充剂", "超级伤药", "必杀技学习盲盒"],
                "money": 500
            }
        },
        {
            "name": "宇宙质量总监ZZZ",
            "level": 18,
            "hp": 180,
            "attack": 65,
            "defense": 60,
            "advantages": ["共情"],
            "disadvantages": [],
            "growth_type": "medium_slow",
            "moves": [
                {"name": "我和他谈笑风生"},
                {"name": "PUA"},
                {"name": "画饼术"},
                {"name": "团队增殖"}
            ],
            "reward": {
                "pokemon": "做表的Delia",
                "items": ["UT补充剂", "精灵球", "必杀技学习盲盒"],
                "money": 700
            }
        },
        {
            "name": "平地挖坑刚子",
            "level": 45,
            "hp": 350,
            "attack": 100,
            "defense": 85,
            "advantages": ["节操"],
            "disadvantages": ["共情", "PS", "content"],
            "growth_type": "slow",
            "moves": [
                {"name": "我在XX时代"},
                {"name": "骚扰专家"},
                {"name": "开始抬杠"},
                {"name": "既要又要还要"}
            ],
            "reward": {
                "pokemon": "害羞的吕瑞怡",
                "items": ["UT补充剂", "超级伤药", "精灵球", "必杀技学习盲盒"],
                "money": 3000
            }
        }
    ]
    
    # 大BOSS配置（阶段性）
    stage_bosses = [
        {
            "stage": 1,
            "name": "HR总监JJZ",
            "level": 30,
            "hp": 300,
            "attack": 90,
            "defense": 80,
            "advantages": [],
            "disadvantages": ["共情"],
            "growth_type": "fast",
            "moves": [
                {"name": "信不信我投诉你"},
                {"name": "PUA"},
                {"name": "开始抬杠"},
                {"name": "熬夜攻击"}
            ],
            "reward": {
                "pokemon": "人畜无害的孙皓",
                "items": ["UT补充剂", "超级伤药", "必杀技学习盲盒"],
                "money": 2000
            }
        },
        {
            "stage": 2,
            "name": "平静的老李",
            "level": 50,
            "hp": 500,
            "attack": 120,
            "defense": 100,
            "advantages": ["共情", "结构化"],
            "disadvantages": ["体力"],
            "growth_type": "slow",
            "moves": [
                {"name": "深呼吸"},
                {"name": "开始抬杠"},
                {"name": "大海无量"},
                {"name": "熬夜攻击"}
            ],
            "reward": {
                "pokemon": "流浪的宏宇",
                "items": ["UT补充剂", "超级伤药", "精灵球", "必杀技学习盲盒"],
                "money": 5000
            }
        },
        {
            "stage": 3,
            "name": "暴怒的老李",
            "level": 70,
            "hp": 800,
            "attack": 160,
            "defense": 130,
            "advantages": ["体力", "韧性", "节操"],
            "disadvantages": ["PS", "content"],
            "growth_type": "slow",
            "moves": [
                {"name": "扣除效益"},
                {"name": "大海无量"},
                {"name": "无偿加班"},
                {"name": "既要又要还要"}
            ],
            "reward": {
                "pokemon": "超神隋总",
                "items": ["UT补充剂", "超级伤药", "精灵球", "大师球", "必杀技学习盲盒"],
                "money": 10000
            }
        }
    ]
    
    evolution_data = {
        "颓废的夏书文": {"level": 20, "evolution": "进击的夏书文", "item": "Vicky付钱的红酒"},
        "沉默的傅雪松": {"level": 20, "evolution": "奔放的傅雪松", "item": "日本自由行船票"},
        "奔放的傅雪松": {"level": 40, "evolution": "蚝汁傅雪松", "item": "生蚝啤酒"},
        "没有干劲的随意": {"level": 7, "evolution": "满血隋毅", "item": "篮球赛通知"},
        "满血隋毅": {"level": 10, "evolution": "超神隋总", "item": "产假通知"},
        "讲课的Raymond": {"level": 22, "evolution": "ValueConcernRaymond", "item": "Wikipedia公式"},
        "害羞的吕瑞怡": {"level": 23, "evolution": "浪浪山吕瑞怡", "item": "骰子和杯子"},
        "做表的Delia": {"level": 15, "evolution": "大嘴Delia", "item": "办公室微信群"},
        "大嘴Delia": {"level": 34, "evolution": "酒后Delia", "item": "啤酒畅饮券"},
        "DCC的托马斯": {"level": 20, "evolution": "做牛做马托马斯", "item": "华哥的离职通知"},
        "做牛做马托马斯": {"level": 40, "evolution": "全旋托马斯", "item": "泥潭中的小萱的船票"},
        "半血小萱": {"level": 10, "evolution": "泥潭中的小萱", "item": "穿膜工具套装"},
        "泥潭中的小萱": {"level": 20, "evolution": "拉膜圣手李小萱", "item": "挤出机灭火套装"},
    }
    
    # 野外顾问池配置 - 按地块类型分配不同的遇敌池和概率
    field_advisor_pools = {
        0: {  # 食品地 (地块1)
            "夏港": 5,
            "DCC的托马斯": 5,
            "没有干劲的随意": 5,
            "半血小萱": 5,
            "沉默的傅雪松": 5,
            "严斤": 5,
            "张新炜": 5,
            "何须强": 5,
            "梅折": 15,
            "李巷阳": 15,
            "袁钱保": 15,
            "王小容": 15
        },
        1: {  # office (地块2)
            "夏港": 5,
            "DCC的托马斯": 5,
            "没有干劲的随意": 5,
            "半血小萱": 5,
            "沉默的傅雪松": 5,
            "严斤": 5,
            "张新炜": 5,
            "何须强": 5,
            "梅折": 15,
            "李巷阳": 15,
            "袁钱保": 15,
            "王小容": 15
        },
        2: {  # 客户现场 (地块3)
            "夏港": 5,
            "DCC的托马斯": 5,
            "没有干劲的随意": 5,
            "半血小萱": 5,
            "沉默的傅雪松": 5,
            "严斤": 5,
            "张新炜": 5,
            "何须强": 5,
            "梅折": 15,
            "李巷阳": 15,
            "袁钱保": 15,
            "王小容": 15
        },
        3: {  # retro (地块4)
            "夏港": 5,
            "DCC的托马斯": 5,
            "没有干劲的随意": 5,
            "半血小萱": 5,
            "沉默的傅雪松": 5,
            "严斤": 5,
            "张新炜": 5,
            "何须强": 5,
            "梅折": 15,
            "李巷阳": 15,
            "袁钱保": 15,
            "王小容": 15
        },
        4: {  # 培训 (地块5)
            "夏港": 5,
            "DCC的托马斯": 5,
            "没有干劲的随意": 5,
            "半血小萱": 5,
            "沉默的傅雪松": 5,
            "严斤": 5,
            "张新炜": 5,
            "何须强": 5,
            "梅折": 15,
            "李巷阳": 15,
            "袁钱保": 15,
            "王小容": 15
        },
        5: {  # beach (地块6)
            "夏港": 5,
            "DCC的托马斯": 5,
            "没有干劲的随意": 5,
            "半血小萱": 5,
            "沉默的傅雪松": 5,
            "严斤": 5,
            "张新炜": 5,
            "何须强": 5,
            "梅折": 15,
            "李巷阳": 15,
            "袁钱保": 15,
            "王小容": 15
        }
    }
    
    # 保留原有的wild_pool作为后备选项
    wild_pool = [
        # 梅折-4占80%的刷新比例（8/11）
        "梅折", "梅折",  # 梅折占约18%
        "李巷阳", "李巷阳",  # 李巷阳占约18%
        "袁钱保", "袁钱保",  # 袁钱保占约18%
        "王小容", "王小容",  # 王小容占约18%
        # 其他顾问占剩余比例（3/11）
        "沉默的傅雪松", "没有干劲的随意", "DCC的托马斯"
    ]
    
    @classmethod
    def get_field_advisor(cls, tile_type):
        """根据地块类型和概率权重选择野外顾问"""
        if tile_type not in cls.field_advisor_pools:
            # 如果地块类型不在配置中，使用原有的wild_pool
            return random.choice(cls.wild_pool)
        
        advisor_pool = cls.field_advisor_pools[tile_type]
        advisors = list(advisor_pool.keys())
        weights = list(advisor_pool.values())
        
        # 使用权重随机选择顾问
        return random.choices(advisors, weights=weights, k=1)[0]
    
# ==================== 游戏初始配置系统 ====================

# 配置选择器 - 修改这个变量来切换初始配置
# 注意：修改此变量后需要重新启动游戏才能生效
# "PlanA": 默认配置 - 颓废的夏书文(1级), 1000金币, 基础物品
# "PlanB": 隐藏配置 - 6个高级顾问(15-40级), 60万金币, 特殊物品
GAME_CONFIG_PLAN = "PlanB"  # 可选值: "PlanA" 或 "PlanB"

class GameInitialConfig:
    """游戏初始配置管理"""
    
    # PlanA配置 - 原有的初始配置
    PLAN_A = {
        "advisors": [
            {"name": "颓废的夏书文", "level": 1, "sp": 0}
        ],
        "money": 1000,
        "items": [
            {"name": "伤药", "description": "恢复30点HP", "item_type": "heal", "effect": 30, "quantity": 1},
            {"name": "超级伤药", "description": "恢复100点HP", "item_type": "heal", "effect": 100, "quantity": 1},
            {"name": "UT补充剂", "description": "将UT恢复至100点", "item_type": "ut_restore", "effect": 100, "quantity": 1}
        ]
    }
    
    # PlanB配置 - 隐藏的初始配置
    PLAN_B = {
        "advisors": [
            {"name": "拉膜圣手李小萱", "level": 40, "sp": 100},
            {"name": "蚝汁傅雪松", "level": 40, "sp": 100},
            {"name": "全旋托马斯", "level": 40, "sp": 100},
            {"name": "ValueConcernRaymond", "level": 40, "sp": 100},
            {"name": "做表的Delia", "level": 15, "sp": 100},
            {"name": "大嘴Delia", "level": 34, "sp": 100}
        ],
        "money": 600000,  # 60万
        "items": [
            {"name": "啤酒畅饮券", "description": "用于Delia二次进化", "item_type": "evolution", "effect": "啤酒畅饮券", "quantity": 1},
            {"name": "办公室微信群", "description": "用于Delia进化", "item_type": "evolution", "effect": "办公室微信群", "quantity": 1},
            {"name": "必杀技学习盲盒", "description": "学习必杀技的盲盒", "item_type": "skill_blind_box", "effect": None, "quantity": 10}
        ]
    }
    
    @classmethod
    def get_current_config(cls):
        """获取当前选择的配置"""
        if GAME_CONFIG_PLAN == "PlanB":
            return cls.PLAN_B
        else:
            return cls.PLAN_A
    

# 物品配置 - 增加可购买物品和价格
class ItemConfig:
    # 完整的物品数据库
    ITEMS_DATABASE = {
        # 恢复类物品
        "伤药": {
            "name": "伤药",
            "description": "恢复HP20点",
            "item_type": "heal",
            "effect": 20,
            "price": 200,
            "stock": 10,
            "rarity": 1
        },
        "超级伤药": {
            "name": "超级伤药",
            "description": "恢复HP50点",
            "item_type": "heal",
            "effect": 50,
            "price": 500,
            "stock": 5,
            "rarity": 1
        },
        "HP药": {
            "name": "HP药",
            "description": "恢复HP100点",
            "item_type": "heal",
            "effect": 100,
            "price": 1000,
            "stock": 3,
            "rarity": 1
        },
        "加冰美式1200ml装": {
            "name": "加冰美式1200ml装",
            "description": "恢复全部HP",
            "item_type": "heal",
            "effect": 9999,
            "price": 5000,
            "stock": 1,
            "rarity": 1
        },
        
        # UT类物品
        "UT补充剂": {
            "name": "UT补充剂",
            "description": "恢复1点UT值",
            "item_type": "ut_restore",
            "effect": 1,
            "price": 3000,
            "stock": 2,
            "rarity": 1
        },
        
        # 精灵球类
        "精灵球": {
            "name": "精灵球",
            "description": "用于捕捉顾问的道具",
            "item_type": "pokeball",
            "effect": 1,
            "price": 200,
            "stock": 20,
            "rarity": 1
        },
        "大师球": {
            "name": "大师球",
            "description": "100%捕获率的精灵球",
            "item_type": "master_ball",
            "effect": 1,
            "price": 10000,
            "stock": 1,
            "rarity": 1
        },
        
        # 进化物品
        "Vicky付钱的红酒": {
            "name": "Vicky付钱的红酒",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "Vicky付钱的红酒",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "日本自由行船票": {
            "name": "日本自由行船票",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "日本自由行船票",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "生蚝啤酒": {
            "name": "生蚝啤酒",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "生蚝啤酒",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "篮球赛通知": {
            "name": "篮球赛通知",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "篮球赛通知",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "产假通知": {
            "name": "产假通知",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "产假通知",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "Wikipedia公式": {
            "name": "Wikipedia公式",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "Wikipedia公式",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "骰子和杯子": {
            "name": "骰子和杯子",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "骰子和杯子",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "办公室微信群": {
            "name": "办公室微信群",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "办公室微信群",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "啤酒畅饮券": {
            "name": "啤酒畅饮券",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "啤酒畅饮券",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "华哥的离职通知": {
            "name": "华哥的离职通知",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "华哥的离职通知",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "泥潭中的小萱的船票": {
            "name": "泥潭中的小萱的船票",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "泥潭中的小萱的船票",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "穿膜工具套装": {
            "name": "穿膜工具套装",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "穿膜工具套装",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        "挤出机灭火套装": {
            "name": "挤出机灭火套装",
            "description": "特定顾问的进化道具",
            "item_type": "evolution",
            "effect": "挤出机灭火套装",
            "price": 8000,
            "stock": 1,
            "rarity": 2
        },
        
        # 特殊物品
        "经验糖果": {
            "name": "经验糖果",
            "description": "使用后获得100经验值",
            "item_type": "exp_candy",
            "effect": 100,
            "price": 2000,
            "stock": 3,
            "rarity": 2
        },
        "必杀技学习盲盒": {
            "name": "必杀技学习盲盒",
            "description": "随机学习一个必杀技",
            "item_type": "ultimate_box",
            "effect": "random_ultimate",
            "price": 15000,
            "stock": 1,
            "rarity": 3
        },
        "PTO通知": {
            "name": "PTO通知",
            "description": "使用后10步内不会遇敌",
            "item_type": "repel",
            "effect": 10,
            "price": 500,
            "stock": 5,
            "rarity": 1
        },
        "Marvin Award": {
            "name": "Marvin Award",
            "description": "提升顾问全属性",
            "item_type": "stat_boost",
            "effect": 10,
            "price": 20000,
            "stock": 1,
            "rarity": 3
        },
        "晚7点PS券": {
            "name": "晚7点PS券",
            "description": "特殊道具，效果未知",
            "item_type": "special",
            "effect": "unknown",
            "price": 5000,
            "stock": 1,
            "rarity": 2
        },
        "team norm打印件": {
            "name": "team norm打印件",
            "description": "特殊道具，效果未知",
            "item_type": "special",
            "effect": "unknown",
            "price": 5000,
            "stock": 1,
            "rarity": 2
        },
        "Lead course book": {
            "name": "Lead course book",
            "description": "特殊道具，效果未知",
            "item_type": "special",
            "effect": "unknown",
            "price": 5000,
            "stock": 1,
            "rarity": 2
        },
        "EM guidebook": {
            "name": "EM guidebook",
            "description": "特殊道具，效果未知",
            "item_type": "special",
            "effect": "unknown",
            "price": 5000,
            "stock": 1,
            "rarity": 2
        }
    }
    
    @staticmethod
    def get_item_data(item_name):
        """根据物品名称获取完整的物品数据"""
        return ItemConfig.ITEMS_DATABASE.get(item_name, None)
    
    # 掉落池 - 定义哪些物品可以掉落
    drop_pool_names = [
        "伤药", "超级伤药", "精灵球", "Vicky付钱的红酒", "日本自由行船票",
        "生蚝啤酒", "篮球赛通知", "产假通知", "Wikipedia公式", "骰子和杯子",
        "办公室微信群", "啤酒畅饮券", "华哥的离职通知", "泥潭中的小萱的船票",
        "穿膜工具套装", "挤出机灭火套装", "经验糖果", "UT补充剂", "必杀技学习盲盒"
    ]
    
    
    # 商店物品配置 - 仅定义哪些物品在商店出售
    shop_items = {
        # 常规物品（始终可用）
        "regular": ["精灵球", "大师球", "HP药", "UT补充剂", "加冰美式1200ml装", "PTO通知"],
        # 稀有物品（随机刷新）
        "rare": [
            "必杀技学习盲盒", "Marvin Award", "Vicky付钱的红酒", "日本自由行船票",
            "生蚝啤酒", "篮球赛通知", "产假通知", "Wikipedia公式", "骰子和杯子",
            "办公室微信群", "啤酒畅饮券", "华哥的离职通知", "泥潭中的小萱的船票",
            "穿膜工具套装", "挤出机灭火套装", "晚7点PS券", "team norm打印件",
            "Lead course book", "EM guidebook"
        ]
    }

# 招式配置
class MoveConfig:
    move_descriptions = {
        "建模": "使用wiki上看到的公式凑数，有几率麻痹对手。",
        "循循善诱": "使用复杂的数学模型震慑对手，有几率石化对手。",
        "我有意见！": "释放能量攻击对手，对自身伤害高，命中率却低下。",
        "PUA": "使用话术诱惑对手，有几率魅惑对手，对成年顾问效力下降。",
        "酒精打击": "威力62，有18%几率形成1.5倍伤害。你挣钱不就是来喝的吗",
        "Empathy": "保持倾听感化对手，有几率无效并对自身产生动摇。",
        "嘲讽": "造成自身攻击力15%伤害，连续3回合使对手防御力下降30%",
        "躺平": "他不会看细节的",
        "磨磨蹭蹭": "先去拿个外卖",
        "画饼术": "1个月你就能下",
        "开始抬杠": "你的话题我们会后讨论，我们先看我的",
        "哼哼唧唧": "这个数据我要请示",
        "感到冒犯": "外包又出花样了",
        "PTO": "我下周休假你backup一下",
        "雪松杀手": "傅雪松，我要你助我一臂之力！",
        "钓鱼执法": "你上钩了！",
        "熬夜攻击": "今晚一定要搞出来",
        "大海无量": "我们全部都要打开",
        "凌晨4点的太阳": "你见过珠海凌晨4点的太阳吗",
        "无偿加班": "五一你们休息两天了，也差不多了",
        "既要又要还要": "我相信群众里面一定有能人",
        "拖欠费用": "你凭什么拿这个钱",
        "整风运动": "你告诉我，为什么W基地一年换了7个总经理",
        "团队增殖": "我们组建了56人的全球团队，但是并不负责解决具体技术问题",
        "技术创新": "该方案采用的都是市面上已有的技术，并没有见到你们的独创性",
        "在你来前": "你们来前我们就开始做了",
        "奶茶攻击": "给整个办公室都来吨吨桶+12分糖",
        "织条毯子": "尽管目前有一点小问题，但是趋势是没有问题的",
        "李代桃僵": "老厂长你来回答一下。",
        "酒仙": "双倍IPA治疗失眠",
        "鲁莽": "干他",
        "心灵震爆": "你不干这个，我就投诉你",
        "腐蚀": "商后面是个啥字母来着",
        "鼓舞": "鼓舞士气提升战斗力",
        "精神污染": "造成精神污染效果",
        "浆板下水": "勇敢下水救人，既能攻击敌人又能治愈自己",
        "倒立攻击": "颠倒世界的独特攻击方式，造成伤害的同时提升自身攻击力"
    }

# 物品类 - 增加UT补充剂功能
class Item:
    def __init__(self, name, description, item_type, effect, price=0):
        self.name = name
        self.description = description
        self.item_type = item_type
        self.effect = effect
        self.price = price
        
    def use(self, target=None, player=None):
        if self.item_type == "heal":
            if target and hasattr(target, 'hp') and hasattr(target, 'max_hp'):
                heal_amount = self.effect
                prev_hp = target.hp
                target.hp = min(target.max_hp, target.hp + heal_amount)
                return f"{target.name}恢复了{target.hp - prev_hp}点HP！"
            return "无法在此使用这个物品"
            
        elif self.item_type == "evolution":
            if target and hasattr(target, 'can_evolve_with_item'):
                if target.can_evolve_with_item(self.effect):
                    result = target.evolve_with_item(self.effect)
                    return result
                else:
                    # 检查是否满足等级要求但缺少正确物品
                    if target.name in PokemonConfig.evolution_data:
                        evolution_info = PokemonConfig.evolution_data[target.name]
                        if target.level >= evolution_info["level"]:
                            if evolution_info["item"] != self.effect:
                                return f"不适合该顾问使用|FAILED"
                            else:
                                return f"{target.name}无法进化（可能已经是最终形态）|FAILED"
                        else:
                            return f"{target.name}需要达到{evolution_info['level']}级才能使用{self.effect}进化（当前{target.level}级）|FAILED"
                    else:
                        return f"不适合该顾问使用|FAILED"
            return "这个物品不能这样使用|FAILED"
            
        elif self.item_type == "pokeball":
            return "只能在战斗中使用精灵球"
            
        elif self.item_type == "exp_boost":
            if target and hasattr(target, 'gain_exp'):
                exp_amount = self.effect
                leveled_up, evolution_messages = target.gain_exp(exp_amount)
                msg = f"{target.name}获得了{exp_amount}点经验值！"
                if leveled_up:
                    msg += f"\n{target.name}升级到Lv.{target.level}了！"
                return msg
            return "这个物品需要对顾问使用"
            
        elif self.item_type == "ut_restore":
            if player and hasattr(player, 'ut') and hasattr(player, 'max_ut'):
                prev_ut = player.ut
                player.ut = min(player.max_ut, self.effect)
                return f"UT从{prev_ut}恢复到{player.ut}点！"
            return "无法恢复UT"
            
        elif self.item_type == "skill_book":
            if target and hasattr(target, 'moves'):
                skill_name = self.effect
                if skill_name not in [move["name"] for move in target.moves]:
                    # 添加新技能，如果技能数量超过4个，需要选择要忘记的技能
                    if len(target.moves) >= 4:
                        return f"SKILL_FORGET_DIALOG|{skill_name}"
                    else:
                        target.moves.append({"name": skill_name})
                        return f"{target.name}学会了{skill_name}！"
                else:
                    return f"{target.name}已经会{skill_name}了！|FAILED"
            return "这个技能书需要对顾问使用|FAILED"
            
        elif self.item_type == "permanent_boost":
            if target and hasattr(target, 'base_attack') and hasattr(target, 'base_defense'):
                stat = self.effect["stat"]
                value = self.effect["value"]
                if stat == "attack":
                    target.base_attack += value
                    return f"{target.name}的攻击力永久提升了{value}点！"
                elif stat == "defense":
                    target.base_defense += value
                    return f"{target.name}的防御力永久提升了{value}点！"
            return "这个药剂需要对顾问使用"
            
        elif self.item_type == "attribute_enhancer":
            if target and hasattr(target, 'advantages'):
                import random
                all_types = ["共情"]
                available_types = [t for t in all_types if t not in target.advantages]
                if available_types:
                    new_advantage = random.choice(available_types)
                    target.advantages.append(new_advantage)
                    return f"{target.name}获得了新的优点属性：{new_advantage}！"
                else:
                    return f"{target.name}已经拥有所有优点属性了！"
            return "这个增强器需要对顾问使用"
        
        elif self.item_type == "sp_enhancer":
            if target and hasattr(target, 'use_em_guidebook'):
                return target.use_em_guidebook()
            return "这个物品需要对顾问使用"
            
        elif self.item_type == "upgrade_gem":
            if target and hasattr(target, 'level'):
                # 简单实现：直接提升等级
                old_level = target.level
                target.level += self.effect
                target.exp_to_next_level = target.level * 100  # 重新计算经验需求
                return f"{target.name}从Lv.{old_level}提升到Lv.{target.level}！"
            return "这个宝石需要对顾问使用"
            
        elif self.item_type == "sp_restore":
            return "SP系统尚未开放，暂时无法使用"
            
        elif self.item_type == "battle_prevent":
            if player:
                player.battle_prevention_steps = self.effect
                return f"使用了{self.name}！{self.effect}步内不会触发战斗！"
            return "无法使用PTO通知"
            
        elif self.item_type == "skill_blind_box":
            if player:
                # 使用编码系统获取所有必杀技
                ultimate_skills = self._get_all_ultimate_skills()
                
                if ultimate_skills:
                    import random
                    # 随机选择一个必杀技编码
                    selected_skill_code = random.choice(list(ultimate_skills.keys()))
                    selected_skill = ultimate_skills[selected_skill_code]
                    
                    # 创建对应的必杀技学习书,包含详细信息
                    # 获取技能详细信息
                    skill_attributes = selected_skill.get('type', '未知')
                    skill_sp_cost = selected_skill.get('sp_cost', 0)
                    skill_description = selected_skill.get('description', '无描述')
                    skill_effects = selected_skill.get('effects', {})
                    
                    # 构建详细描述
                    detailed_description = f"学习必杀技：{selected_skill['name']}\n"
                    detailed_description += f"技能属性：{skill_attributes}\n"
                    detailed_description += f"SP消耗：{skill_sp_cost if skill_sp_cost > 0 else '无（使用后获得SP）'}\n"
                    detailed_description += f"技能描述：{skill_description}\n"
                    
                    # 添加技能效果信息
                    if skill_effects:
                        detailed_description += "技能效果："
                        if 'damage_range' in skill_effects:
                            min_dmg, max_dmg = skill_effects['damage_range']
                            detailed_description += f" 伤害{min_dmg}-{max_dmg}点"
                        if 'base_damage' in skill_effects:
                            detailed_description += f" 基础伤害{skill_effects['base_damage']}点"
                        if 'heal_percentage' in skill_effects:
                            heal_percent = int(skill_effects['heal_percentage'] * 100)
                            detailed_description += f" 治疗{heal_percent}%生命"
                        if 'turns' in skill_effects:
                            detailed_description += f" 持续{skill_effects['turns']}回合"
                        if 'attack_multiplier' in skill_effects:
                            mult = int(skill_effects['attack_multiplier'] * 100)
                            detailed_description += f" 攻击力变化{mult}%"
                        if 'defense_multiplier' in skill_effects:
                            mult = int(skill_effects['defense_multiplier'] * 100)
                            detailed_description += f" 防御力变化{mult}%"
                        if 'target_attack_multiplier' in skill_effects:
                            mult = int(skill_effects['target_attack_multiplier'] * 100)
                            detailed_description += f" 敌方攻击力变化{mult}%"
                        if 'execute_threshold' in skill_effects:
                            threshold = int(skill_effects['execute_threshold'] * 100)
                            detailed_description += f" 斩杀阈值HP<{threshold}%"
                    
                    skill_book = Item(
                        name=f"必杀技学习书：{selected_skill['name']}",
                        description=detailed_description,
                        item_type="skill_book",
                        effect=selected_skill['name'],
                        price=0
                    )
                    
                    # 添加到玩家背包
                    player.add_item(skill_book)
                    
                    return f"打开了{self.name}！获得了{skill_book.name}！（编码：{selected_skill_code}）"
                else:
                    return f"打开了{self.name},但没有找到可学习的必杀技..."
            return "无法使用必杀技学习盲盒"
            
        return f"使用了{self.name},但没有效果"
    
    def _get_all_ultimate_skills(self):
        """
        获取所有必杀技的编码系统，现在从统一技能数据库中获取
        """
        ultimate_skills = {}
        skill_id = 1
        
        # 从统一技能数据库中筛选必杀技（SP消耗大于50的技能）
        for skill_name, skill_data in UNIFIED_SKILLS_DATABASE.items():
            if skill_data.get("sp_cost", 0) >= 50:  # 必杀技标准：SP消耗>=50
                ultimate_skills[f"{skill_id:03d}"] = {
                    "name": skill_name,
                    "type": skill_data.get("type", ""),
                    "effects": skill_data.get("effects", {}),
                    "description": skill_data.get("description", ""),
                    "sp_cost": skill_data.get("sp_cost", 0),
                    "quote": skill_data.get("quote", "")
                }
                skill_id += 1
        
        return ultimate_skills
    
        
    def calculate_stats(self):
        """
        计算基于等级的战斗属性
        使用Pokemon Yellow风格的属性增长公式
        """
        # Pokemon Yellow风格的属性计算公式
        # Stat = floor(((Base + IV) * 2 + floor(sqrt(EV)/4)) * Level / 100) + Level + 10
        # 简化版本，不考虑IV和EV，使用基础属性和等级
        
        # HP计算 (HP有特殊公式)
        hp_stat = int((self.base_hp * 2 * self.level) / 100) + self.level + 10
        self.max_hp = hp_stat
        
        if not hasattr(self, 'hp'):
            self.hp = self.max_hp
        else:
            # 升级时按比例恢复HP
            hp_ratio = self.hp / getattr(self, 'old_max_hp', self.max_hp)
            self.hp = min(int(self.max_hp * hp_ratio), self.max_hp)
        
        self.old_max_hp = self.max_hp  # 保存旧的最大HP用于比例计算
        
        # 攻击力和防御力计算
        self.attack = int((self.base_attack * 2 * self.level) / 100) + 5
        self.defense = int((self.base_defense * 2 * self.level) / 100) + 5


# ==================== 游戏世界系统 ====================

# 地图类 - 修改为支持新地块和BOSS逻辑
class GameMap:
    def __init__(self, size=MAP_SIZE, player=None):
        self.size = size
        self.grid = []
        self.boss_positions = {}  # 存储BOSS位置: {"mini": (x,y), "stage": (x,y)}
        self.chest_positions = []  # 宝箱位置
        self.opened_chests = set()  # 已打开的宝箱
        self.timed_chest_positions = []  # 定时刷新的宝箱位置
        self.opened_timed_chests = set()  # 已打开的定时宝箱
        self.last_timed_chest_spawn = 0  # 上次生成定时宝箱的时间
        self.shop_position = None  # 商店位置
        self.training_position = None  # 训练中心位置
        self.portal_positions = []  # 传送门位置
        self.player = player  # 引用玩家对象以获取BOSS击败信息
        self.can_refresh = True  # 是否可以刷新地图，初始为True
        self.generate_map()  # 随机生成地图
        self.map_data = self.generate_map()  # 初始化地图数据
        # 确保特殊地块被正确放置（可选：手动指定关键地块位置）
        # 地块名称映射
        self.names = {
            0: "食品地", 1: "office", 2: "客户现场", 3: "retro", 
            4: "培训", 5: "beach", 6: "BOSS区域", 7: "宝箱",
            8: "商店", 9: "训练中心", 10: "传送门", 11: "小BOSS", 12: "大BOSS"
        }
        
    def generate_map(self):
        """随机生成地图，包含新地块和BOSS逻辑"""
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        
        # 确定是否生成大BOSS（每击败3个小BOSS）
        should_spawn_stage_boss = self.player is not None and self.player.mini_bosses_defeated % 3 == 0
        
        # 放置训练中心（确保至少有一个）
        self.training_position = (random.randint(1, self.size-2), random.randint(1, self.size-2))
        tx, ty = self.training_position
        self.grid[tx][ty] = TILE_TYPES['training']
        if self.player:
            self.player.training_center_pos = (tx, ty)
        
        # 放置商店
        while True:
            sx, sy = (random.randint(1, self.size-2), random.randint(1, self.size-2))
            if (sx, sy) != self.training_position:
                self.shop_position = (sx, sy)
                self.grid[sx][sy] = TILE_TYPES['shop']
                break
        
        # 放置传送门（2个）
        self.portal_positions = []
        while len(self.portal_positions) < 2:
            px, py = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            if (px, py) not in [self.training_position, self.shop_position] and (px, py) not in self.portal_positions:
                self.portal_positions.append((px, py))
                self.grid[px][py] = TILE_TYPES['portal']
        
        # 放置宝箱（7个）
        self.chest_positions = []
        num_chests = 7
        while len(self.chest_positions) < num_chests:
            cx, cy = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            if (cx, cy) not in [self.training_position, self.shop_position] and \
               (cx, cy) not in self.portal_positions and \
               (cx, cy) not in self.chest_positions:
                self.chest_positions.append((cx, cy))
                self.grid[cx][cy] = TILE_TYPES['chest']
        
        # 放置BOSS（根据条件放置小BOSS或大BOSS）
        if should_spawn_stage_boss and self.player and self.player.stage <= len(PokemonConfig.stage_bosses):
            # 放置大BOSS
            while True:
                bx, by = (random.randint(0, self.size-1), random.randint(0, self.size-1))
                if (bx, by) not in [self.training_position, self.shop_position] and \
                   (bx, by) not in self.portal_positions and \
                   (bx, by) not in self.chest_positions:
                    self.boss_positions['stage'] = (bx, by)
                    self.grid[bx][by] = TILE_TYPES['stage_boss']
                    break
        else:
            # 放置小BOSS
            while True:
                bx, by = (random.randint(0, self.size-1), random.randint(0, self.size-1))
                if (bx, by) not in [self.training_position, self.shop_position] and \
                   (bx, by) not in self.portal_positions and \
                   (bx, by) not in self.chest_positions:
                    self.boss_positions['mini'] = (bx, by)
                    self.grid[bx][by] = TILE_TYPES['mini_boss']
                    break
        
        # 填充其余地块
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 0:  # 尚未设置的地块
                    # 随机生成普通地块（0-5）
                    self.grid[i][j] = random.randint(0, 5)
    def refresh_map(self):
        """刷新地图，生成新的BOSS位置和新的宝箱"""
        if self.can_refresh:
            self.generate_map()
            # 只重置初始宝箱的已打开状态，让初始宝箱可以重新打开
            self.opened_chests = set()
            # 清空定时宝箱位置，但保持定时宝箱的已打开状态和定时器
            self.timed_chest_positions = []
            self.can_refresh = False  # 刷新后设置为不可刷新，直到击败BOSS
    
    def update_timed_chests(self):
        """更新定时宝箱系统，每2分钟随机生成一个宝箱"""
        import pygame
        current_time = pygame.time.get_ticks()
        
        # 初始化定时器（游戏开始时）
        if self.last_timed_chest_spawn == 0:
            self.last_timed_chest_spawn = current_time
            return
        
        # 检查是否过了2分钟（120000毫秒）
        if current_time - self.last_timed_chest_spawn >= 120000:
            if self.spawn_timed_chest():
                self.last_timed_chest_spawn = current_time
                return True  # 返回True表示生成了新宝箱
        return False
    
    def spawn_timed_chest(self):
        """生成一个定时宝箱"""
        max_attempts = 50  # 最大尝试次数，防止无限循环
        attempts = 0
        
        while attempts < max_attempts:
            cx, cy = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            
            # 检查位置是否可用（不与现有特殊地块冲突）
            if (cx, cy) not in [self.training_position, self.shop_position] and \
               (cx, cy) not in self.portal_positions and \
               (cx, cy) not in self.chest_positions and \
               (cx, cy) not in self.timed_chest_positions and \
               (cx, cy) not in self.boss_positions.values():
                
                # 检查该位置不是BOSS地块
                current_tile = self.get_tile_type(cx, cy)
                if current_tile not in [TILE_TYPES['mini_boss'], TILE_TYPES['stage_boss']]:
                    self.timed_chest_positions.append((cx, cy))
                    self.grid[cx][cy] = TILE_TYPES['chest']
                    return True  # 成功生成宝箱
            
            attempts += 1
        
    def get_tile_type(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.grid[x][y]
        return -1
        
    def check_encounter(self, x, y, player=None):
        tile_type = self.get_tile_type(x, y)
        
        # 特殊地块不触发随机遇敌
        special_tiles = [
            TILE_TYPES['chest'],        # 7 - 宝箱
            TILE_TYPES['shop'],         # 8 - 商店
            TILE_TYPES['training'],     # 9 - 训练中心
            TILE_TYPES['portal'],       # 10 - 传送门
            TILE_TYPES['mini_boss'],    # 11 - 小BOSS
            TILE_TYPES['stage_boss']    # 12 - 大BOSS
        ]
        
        if tile_type in special_tiles:
            return None  # 特殊地块不触发随机遇敌
            
        # 检查PTO通知是否生效
        if player and player.battle_prevention_steps > 0:
            return None  # PTO通知生效期间不触发战斗
        
        # BOSS地块（类型6，旧版本兼容）必定触发BOSS战
        if tile_type == 6:
            return "boss"
        # 其他地块的普通遇敌概率（调整为20-30%）
        elif tile_type == 0:  # 食品地
            return "wild" if random.random() < 0.25 else None
        elif tile_type == 1:  # office
            return "wild" if random.random() < 0.25 else None
        elif tile_type == 2:  # 客户现场
            return "wild" if random.random() < 0.25 else None
        elif tile_type == 3:  # retro
            return "wild" if random.random() < 0.25 else None
        elif tile_type == 4:  # 培训
            return "wild" if random.random() < 0.25 else None
        elif tile_type == 5:  # beach
            return "wild" if random.random() < 0.25 else None
        return None
        
    def is_chest_opened(self, x, y):
        """检查宝箱是否已打开"""
        if (x, y) in self.chest_positions:
            return (x, y) in self.opened_chests
        elif (x, y) in self.timed_chest_positions:
            return (x, y) in self.opened_timed_chests
        return False
        
    def open_chest(self, x, y):
        """打开宝箱"""
        # 检查是否是初始宝箱或定时宝箱
        if (x, y) in self.chest_positions and not self.is_chest_opened(x, y):
            self.opened_chests.add((x, y))
        elif (x, y) in self.timed_chest_positions and not self.is_chest_opened(x, y):
            self.opened_timed_chests.add((x, y))
        else:
            return None  # 不是宝箱或已经打开
        
        # 随机生成奖励
        reward_type = random.choice(['item', 'money', 'both'])
        rewards = []
        
        if reward_type in ['item', 'both']:
            # 随机物品
            # 从掉落池中随机选择一个物品
            item_name = random.choice(ItemConfig.drop_pool_names)
            item_data = ItemConfig.get_item_data(item_name)
            if item_data:
                item = Item(item_data["name"], item_data["description"], 
                           item_data["item_type"], item_data["effect"], 
                           item_data.get("price", 0))
                rewards.append(("item", item))
            else:
                print(f"警告: 物品 '{item_name}' 在数据库中未找到")
            
        if reward_type in ['money', 'both']:
            # 随机金钱
            money = random.randint(50, 500)
            rewards.append(("money", money))
            
        return rewards
    
    def get_portal_pair(self, x, y):
        """获取另一个传送门的位置"""
        if (x, y) in self.portal_positions:
            for portal in self.portal_positions:
                if portal != (x, y):
                    return portal
        return None
    def get_wild_pokemon_level(self, x, y, player_default_level=None):
        tile_type = self.get_tile_type(x, y)
        
        # 1-6地块都使用基于我方默认出战顾问等级的生成逻辑
        if tile_type in [0, 1, 2, 3, 4, 5, 6] and player_default_level is not None:
            # 新规则：7级之前，敌人等级与默认出战顾问等级相同
            if player_default_level < 7:
                return player_default_level
            
            # 7级及以上，沿用现有等级计算规则
            rand = random.random()
            if rand < 0.5:  # 50%概率：±2级之内
                level_offset = random.randint(-2, 2)
                return max(1, player_default_level + level_offset)
            elif rand < 0.9:  # 40%概率：+3~+4级
                level_offset = random.randint(3, 4)
                return player_default_level + level_offset
            else:  # 10%概率：+5级
                return player_default_level + 5
        
        # 当没有默认等级时的后备逻辑（保持原有固定等级范围）
        if tile_type == 0:  # 食品地
            return random.randint(1, 5)
        elif tile_type == 1:  # office
            return random.randint(3, 8)
        elif tile_type == 2:  # 客户现场
            return random.randint(5, 10)
        elif tile_type == 3:  # retro
            return random.randint(7, 12)
        elif tile_type == 4:  # 培训
            return random.randint(9, 18)
        elif tile_type == 5:  # beach
            return random.randint(18, 28)
        elif tile_type == 6:  # beach
            return random.randint(18, 28)
        return 1
        
    def get_adjacent_tile(self, x, y):
        """获取指定位置的一个相邻地块"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        valid_directions = []
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                valid_directions.append((nx, ny))
                
        if valid_directions:
            return random.choice(valid_directions)
        return (x, y)  # 如果没有有效相邻地块，返回原位置
        
    def to_dict(self):
        return {
            "size": self.size,
            "grid": self.grid,
            "boss_positions": self.boss_positions,
            "chest_positions": self.chest_positions,
            "opened_chests": list(self.opened_chests),
            "timed_chest_positions": self.timed_chest_positions,
            "opened_timed_chests": list(self.opened_timed_chests),
            "last_timed_chest_spawn": self.last_timed_chest_spawn,
            "shop_position": self.shop_position,
            "training_position": self.training_position,
            "portal_positions": self.portal_positions,
            "can_refresh": self.can_refresh,
        }
        
    @classmethod
    def from_dict(cls, data):
        game_map = cls(data["size"])
        game_map.grid = data.get("grid", game_map.grid)
        game_map.boss_positions = data.get("boss_positions", {})
        game_map.chest_positions = data.get("chest_positions", [])
        game_map.opened_chests = set(data.get("opened_chests", []))
        game_map.timed_chest_positions = data.get("timed_chest_positions", [])
        game_map.opened_timed_chests = set(data.get("opened_timed_chests", []))
        game_map.last_timed_chest_spawn = data.get("last_timed_chest_spawn", 0)
        game_map.shop_position = data.get("shop_position", None)
        game_map.training_position = data.get("training_position", None)
        game_map.portal_positions = data.get("portal_positions", [])
        game_map.can_refresh = data.get("can_refresh", True)
        return game_map
 


# 移除BOSS地块函数
def remove_boss(game_map, x, y):
    """击败BOSS后移除地图上的BOSS地块，替换为普通地块"""
    # 兼容 GameMap 实例
    grid = game_map.grid if hasattr(game_map, "grid") else game_map
    size = game_map.size if hasattr(game_map, "size") else MAP_SIZE
    if 0 <= x < size and 0 <= y < size:
        grid[x][y] = TILE_TYPES['flat']
        # 尝试从 boss_positions 中清理对应位置
        if hasattr(game_map, "boss_positions"):
            for key, pos in list(game_map.boss_positions.items()):
                if pos == (x, y):
                    del game_map.boss_positions[key]
        return True
    return False

# ==================== 游戏实体系统 ====================

class Pokemon:
    def __init__(self, name, level=1, exp=0):
        base_data = PokemonConfig.base_data.get(name)
        if not base_data:
            raise ValueError(f"未知的顾问: {name}")
            
        self.name = name
        self.level = level
        self.exp = exp
        self.growth_type = base_data.get("growth_type", "medium_fast")
        
        
        # 使用新的经验值系统计算升级所需经验
        self.exp_to_next_level = ExperienceConfig.get_exp_to_next_level(self.level, self.growth_type)
        
        self.base_hp = base_data["hp"]
        self.base_attack = base_data["attack"]
        self.base_defense = base_data["defense"]
        self.moves = base_data["moves"]
        self.advantages = base_data["advantages"]
        self.disadvantages = base_data["disadvantages"]
        
        # Don't set hp yet - let calculate_stats() handle it properly
        self.original_name = name
        self.is_evolving = False
        
        # SP系统
        self.sp = SP_CONFIG["initial_sp"]
        self.max_sp = SP_CONFIG["max_sp"]
        self.has_em_guidebook = False
        
        # 状态效果系统
        self.status_effects = {
            "continuous_damage": [],  # 连续伤害效果 [{damage: int, turns: int, name: str, caster: str}]
            "continuous_heal": [],    # 连续治疗效果 [{heal: int, turns: int, name: str, caster: str}]
            "delayed_effects": [],    # 延迟效果 [{effect_type: str, value: float, trigger_turn: int, name: str, caster: str, target: str}]
            "stat_modifiers": {       # 属性修改效果
                "attack_multiplier": 1.0,
                "defense_multiplier": 1.0,
                "turns_remaining": 0,
                "effect_name": "",
                "caster": "self"      # 默认为自己施放
            }
        }
        
        # 回合计数器，用于延迟效果
        self.battle_turn_counter = 0
        
        self.calculate_stats()
        
    def calculate_stats(self):
        """
        计算基于等级的战斗属性
        使用Pokemon Yellow风格的属性增长公式
        """
        # Pokemon Yellow风格的属性计算公式
        # Stat = floor(((Base + IV) * 2 + floor(sqrt(EV)/4)) * Level / 100) + Level + 10
        # 简化版本，不考虑IV和EV，使用基础属性和等级
        
        # HP计算 (HP有特殊公式)
        hp_stat = int((self.base_hp * 2 * self.level) / 100) + self.level + 10
        self.max_hp = hp_stat
        
        if not hasattr(self, 'hp'):
            self.hp = self.max_hp
        else:
            # 升级时按比例恢复HP
            hp_ratio = self.hp / getattr(self, 'old_max_hp', self.max_hp)
            self.hp = min(int(self.max_hp * hp_ratio), self.max_hp)
        
        self.old_max_hp = self.max_hp  # 保存旧的最大HP用于比例计算
        
        # 攻击力和防御力计算
        self.attack = int((self.base_attack * 2 * self.level) / 100) + 5
        self.defense = int((self.base_defense * 2 * self.level) / 100) + 5
        
    def gain_exp(self, amount):
        """获取经验值，可能触发升级和进化"""
        self.exp += amount
        leveled_up = False
        evolution_messages = []
        
        # 使用Pokemon Yellow风格的经验值曲线
        current_total_exp = ExperienceConfig.get_exp_for_level(self.level, self.growth_type)
        
        while self.exp + current_total_exp >= ExperienceConfig.get_exp_for_level(self.level + 1, self.growth_type):
            # 升级
            next_level_total_exp = ExperienceConfig.get_exp_for_level(self.level + 1, self.growth_type)
            exp_used = next_level_total_exp - current_total_exp
            self.exp -= exp_used
            self.level += 1
            current_total_exp = next_level_total_exp
            
            self.calculate_stats()
            leveled_up = True
            
            evolve_msg = self.check_evolution()
            if evolve_msg:
                evolution_messages.append(evolve_msg)
        
        # 更新到下一级所需的经验值
        self.exp_to_next_level = ExperienceConfig.get_exp_to_next_level(self.level, self.growth_type) - self.exp
        
        return leveled_up, evolution_messages
        
    def lose_level(self):
        """降低一级"""
        if self.level > 1:
            self.level -= 1
            self.calculate_stats()
            return True
        return False
        
    def check_evolution(self):
        """检查是否满足进化条件"""
        if self.name in PokemonConfig.evolution_data:
            evolution_info = PokemonConfig.evolution_data[self.name]
            # 只有在不需要物品的情况下才自动进化
            if (self.level >= evolution_info["level"] and 
                evolution_info["item"] is None and 
                not self.is_evolving):
                self.is_evolving = True
                return f"{self.name}好像要进化了！"
        return None
        
    def can_evolve_with_item(self, item_name):
        """检查是否可以用物品进化"""
        if self.name in PokemonConfig.evolution_data:
            evolution_info = PokemonConfig.evolution_data[self.name]
            # 检查等级和物品条件
            return (evolution_info["item"] == item_name and 
                    self.level >= evolution_info["level"])
        return False
        
    def evolve_with_item(self, item_name):
        """使用物品进化"""
        if self.can_evolve_with_item(item_name):
            return self.perform_evolution()
        return f"{self.name}不能用{item_name}进化"
        
    def perform_evolution(self):
        """执行进化过程"""
        if not self.is_evolving and self.name in PokemonConfig.evolution_data:
            self.is_evolving = True
            
        if self.is_evolving and self.name in PokemonConfig.evolution_data:
            evolution_info = PokemonConfig.evolution_data[self.name]
            new_name = evolution_info["evolution"]
            
            new_data = PokemonConfig.base_data.get(new_name)
            if not new_data:
                self.is_evolving = False  # 恢复状态
                return "进化失败，未知的顾问形态！"
            
            self.base_hp = new_data["hp"]
            self.base_attack = new_data["attack"]
            self.base_defense = new_data["defense"]
            self.moves = new_data["moves"]
            self.advantages = new_data["advantages"]
            self.disadvantages = new_data["disadvantages"]
            
            old_name = self.name
            self.name = new_name
            self.is_evolving = False
            
            self.calculate_stats()
            
            return f"{old_name}进化成{new_name}了！"
        return ""
        
    def is_fainted(self):
        """检查是否已昏厥"""
        return self.hp <= 0
        
    def take_damage(self, damage):
        """承受伤害"""
        self.hp = max(0, self.hp - damage)
        return damage
        
    def get_hp_percentage(self):
        """获取HP百分比"""
        return self.hp / self.max_hp if self.max_hp > 0 else 0
    
    def get_base_hp_percentage(self):
        """获取基于默认HP的百分比（用于HP条显示）"""
        return min(1.0, self.hp / self.base_hp) if self.base_hp > 0 else 0
    
    def get_sp_percentage(self):
        """获取SP百分比"""
        return self.sp / self.max_sp if self.max_sp > 0 else 0
    
    def gain_sp(self, amount):
        """获得SP"""
        self.sp = min(self.max_sp, self.sp + amount)
        return amount
    
    def consume_sp(self, amount):
        """消耗SP"""
        if self.sp >= amount:
            self.sp -= amount
            return True
        return False
    
    def use_em_guidebook(self):
        """使用EM guidebook增加SP上限"""
        if not self.has_em_guidebook:
            self.has_em_guidebook = True
            self.max_sp = SP_CONFIG["max_sp_with_guidebook"]
            return f"{self.name}的SP上限提升到{self.max_sp}！"
        return f"{self.name}已经使用过EM guidebook了！"
    
    def calculate_type_effectiveness(self, move_type):
        """计算属性克制效果"""
        # 处理多属性技能
        if isinstance(move_type, list):
            # 如果技能有多个属性，采用"取最有利的属性"策略
            # 优先检查是否有任何属性命中敌方劣势（对攻击方有利）
            for attr in move_type:
                if attr in self.disadvantages:
                    return random.uniform(1.8, 2.5)  # 劣势属性，受到伤害增加（对攻击方有利）
            # 如果没有命中劣势，再检查是否命中优势
            for attr in move_type:
                if attr in self.advantages:
                    return random.uniform(0.2, 0.5)  # 优势属性，受到伤害减少（对攻击方不利）
            return 1.0
        else:
            # 单属性技能的原有逻辑
            if move_type in self.advantages:
                return random.uniform(0.2, 0.5)  # 优势属性，受到伤害减少
            elif move_type in self.disadvantages:
                return random.uniform(1.8, 2.5)  # 劣势属性，受到伤害增加
            return 1.0
        
    def calculate_move_damage(self, move, target):
        """计算技能伤害"""
        if not move:
            return 1, 1.0
            
        # 从UNIFIED_SKILLS_DATABASE获取技能信息
        skill_data = UNIFIED_SKILLS_DATABASE.get(move.get("name", ""), {})
        power_factor = skill_data.get("power", 0)
        move_type = skill_data.get("type", "")
        
        if power_factor == 0:
            return 1, 1.0
            
        level_factor = (self.level * 0.4 + 2)
        
        # 应用状态效果修改的攻击力
        modified_attack = self.attack * self.status_effects["stat_modifiers"]["attack_multiplier"]
        modified_defense = target.defense * target.status_effects["stat_modifiers"]["defense_multiplier"]
        
        attack_defense_ratio = modified_attack / modified_defense if modified_defense > 0 else 1
        
        base_damage = (level_factor * power_factor * attack_defense_ratio) / 50 + 2
        
        type_multiplier = target.calculate_type_effectiveness(move_type)
        
        random_factor = random.uniform(0.85, 1.0)
        final_damage = int(base_damage * type_multiplier * random_factor)
        
        return max(1, final_damage), type_multiplier
    
    def use_skill(self, skill_name, target=None, allies=None):
        """使用技能"""
        if skill_name not in UNIFIED_SKILLS_DATABASE:
            return None, [f"技能 {skill_name} 不存在"]
        
        skill_data = UNIFIED_SKILLS_DATABASE[skill_name]
        messages = []
        
        # 检查SP消耗
        if skill_data["sp_cost"] > 0:
            if not self.consume_sp(skill_data["sp_cost"]):
                return None, [f"{self.name}的SP不足，无法使用{skill_name}！"]
        
        category = skill_data["category"]
        
        # 处理伤害类技能
        if category == SkillCategory.DIRECT_DAMAGE:
            if target:
                effects = skill_data["effects"]
                
                # 检查是否有随机伤害百分比范围
                damage_percentage_min = effects.get("damage_percentage_min", 0)
                damage_percentage_max = effects.get("damage_percentage_max", 0)
                
                if damage_percentage_min > 0 and damage_percentage_max > 0:
                    # 随机伤害百分比
                    random_percentage = random.uniform(damage_percentage_min, damage_percentage_max)
                    base_damage_percentage = random_percentage
                else:
                    # 使用固定伤害百分比
                    base_damage_percentage = effects.get("base_damage_percentage", skill_data.get("power", 0) / 100.0)
                
                base_damage = int(self.attack * base_damage_percentage)
                
                # 检查暴击
                crit_chance = effects.get("crit_chance", 0)
                crit_multiplier = effects.get("crit_multiplier", 1.0)
                is_crit = random.random() < crit_chance
                
                if is_crit:
                    base_damage = int(base_damage * crit_multiplier)
                    messages.append(f"{self.name}使用了{skill_name}，暴击！")
                else:
                    messages.append(f"{self.name}使用了{skill_name}！")
                
                # 检查是否有特殊伤害类型（基于当前HP的伤害）
                current_hp_damage_percentage = effects.get("current_hp_damage_percentage", 0)
                if current_hp_damage_percentage > 0:
                    # 基于目标当前HP的伤害
                    hp_based_damage = int(target.hp * current_hp_damage_percentage)
                    base_damage = max(base_damage, hp_based_damage)
                
                # 计算属性克制
                type_multiplier = target.calculate_type_effectiveness(skill_data["type"])
                final_damage = int(base_damage * type_multiplier)
                
                # 应用防御减免
                defense_reduction = target.defense // 2
                actual_damage = max(1, final_damage - defense_reduction)
                
                target.hp = max(0, target.hp - actual_damage)
                messages.append(f"对{target.name}造成{actual_damage}点伤害！")
                
                # 处理自身减益效果（如Empathy的副作用）
                self_debuff_chance = effects.get("self_debuff_chance", 0)
                if self_debuff_chance > 0 and random.random() < self_debuff_chance:
                    self_attack_mult = effects.get("self_attack_multiplier", 1.0)
                    self_debuff_turns = effects.get("self_debuff_turns", 1)
                    self.add_stat_modifier(self_attack_mult, 1.0, self_debuff_turns, f"{skill_name}副作用", "self")
                    messages.append(f"{self.name}受到{skill_name}的副作用影响，攻击力下降！")
                
                return actual_damage, messages
            else:
                return 0, [f"{self.name}使用了{skill_name}，但没有目标！"]
        
        # 连续伤害技能（暂未实现）
        elif category == SkillCategory.CONTINUOUS_DAMAGE:
            return None, [f"{self.name}使用了{skill_name}（连续伤害效果暂未实现）"]
        
        # 持续伤害技能
        elif category == SkillCategory.DOT:
            if target:
                effects = skill_data["effects"]
                dot_percentage = effects.get("dot_percentage", 0)
                turns = effects.get("turns", 3)
                
                if dot_percentage > 0:
                    # 计算每回合伤害
                    damage_per_turn = int(self.attack * dot_percentage)
                    
                    # 添加持续伤害效果
                    target.add_continuous_damage(damage_per_turn, turns, skill_name, "enemy")
                    
                    messages.append(f"{self.name}使用了{skill_name}！")
                    messages.append(f"{target.name}将在接下来{turns}回合内每回合受到{damage_per_turn}点伤害！")
                    
                    # 处理额外效果（如麻痹、石化等）
                    paralyze_chance = effects.get("paralyze_chance", 0)
                    if paralyze_chance > 0 and random.random() < paralyze_chance:
                        paralyze_turns = effects.get("paralyze_turns", 1)
                        # 这里可以添加麻痹效果的实现
                        messages.append(f"{target.name}被麻痹了{paralyze_turns}回合！")
                    
                    petrify_chance = effects.get("petrify_chance", 0)
                    if petrify_chance > 0 and random.random() < petrify_chance:
                        petrify_turns = effects.get("petrify_turns", 1)
                        # 这里可以添加石化效果的实现
                        messages.append(f"{target.name}被石化了{petrify_turns}回合！")
                    
                    return damage_per_turn, messages
                else:
                    messages.append(f"{self.name}使用了{skill_name}，但没有产生效果！")
                    return 0, messages
            else:
                return 0, [f"{self.name}使用了{skill_name}，但没有目标！"]
        
        effects = skill_data["effects"]
        
        if category == SkillCategory.DIRECT_HEAL:
            # 直接治疗
            heal_percentage = effects["heal_percentage"]
            heal_amount = int(self.max_hp * heal_percentage)
            old_hp = self.hp
            self.hp = min(self.max_hp, self.hp + heal_amount)
            actual_heal = self.hp - old_hp
            messages.append(f"{self.name}使用了{skill_name}，回复了{actual_heal}点HP！")
            return actual_heal, messages
        
        elif category == SkillCategory.CONTINUOUS_HEAL:
            # 连续多回合治疗
            heal_percentage = effects["heal_percentage"]
            turns = effects["turns"]
            heal_per_turn = int(self.max_hp * heal_percentage)
            self.add_continuous_heal(heal_per_turn, turns, skill_name)
            messages.append(f"{self.name}使用了{skill_name}，将在接下来{turns}回合内每回合回复{heal_per_turn}点HP！")
            return heal_per_turn, messages
        
        elif category == SkillCategory.SELF_BUFF:
            # 改变己方属性多回合
            
            # 处理无锡的女武神特殊逻辑
            if skill_name == "无锡的女武神":
                # 恢复所有顾问血量（不包括自己）
                heal_percentage = effects.get("heal_percentage", 1.0)
                total_heal = 0
                
                # 恢复所有队友血量（不包括使用者自己）
                if allies:
                    for ally in allies:
                        if ally != self and not ally.is_fainted():  # 不包括自己，不治疗已倒下的队友
                            ally_heal_amount = int(ally.max_hp * heal_percentage)
                            old_ally_hp = ally.hp
                            ally.hp = min(ally.max_hp, ally.hp + ally_heal_amount)
                            ally_actual_heal = ally.hp - old_ally_hp
                            total_heal += ally_actual_heal
                            if ally_actual_heal > 0:
                                messages.append(f"{ally.name}恢复了{ally_actual_heal}点血量！")
                
                # 自身血量降为1（技能的核心牺牲效果）
                old_self_hp = self.hp
                if effects.get("self_hp_to_1", False):
                    if self.hp > 1:
                        hp_sacrificed = self.hp - 1
                        self.hp = 1
                        messages.append(f"{self.name}牺牲了{hp_sacrificed}点血量，血量降为1！")
                    else:
                        messages.append(f"{self.name}血量已经很低，但依然使用了{skill_name}！")
                
                # 所有顾问攻击力增加20%（不包括自己）
                all_allies_attack_buff = effects.get("all_allies_attack_buff", 0.2)
                team_buff_turns = effects.get("turns", 999)  # 持续整场战斗
                
                # 给所有队友添加攻击力增益
                if allies:
                    for ally in allies:
                        if ally != self and not ally.is_fainted():  # 不包括自己
                            ally.add_stat_modifier(1.0 + all_allies_attack_buff, 1.0, team_buff_turns, f"{skill_name}·团队加持", "self")
                            messages.append(f"{ally.name}的攻击力提升{int(all_allies_attack_buff*100)}%！")
                
                # 4回合后自身血量恢复为100%
                delayed_heal = effects.get("delayed_heal", {})
                if delayed_heal:
                    delay_turns = delayed_heal.get("turns", 4)
                    heal_percentage_delayed = delayed_heal.get("percentage", 1.0)
                    self.add_delayed_effect("heal_percentage", heal_percentage_delayed, delay_turns, f"{skill_name}·重生", "self", "self")
                
                # 自身攻击力翻倍
                attack_mult = effects.get("attack_multiplier", 2.0)
                turns = effects.get("turns", 999)  # 持续整场战斗
                self.add_stat_modifier(attack_mult, 1.0, turns, f"{skill_name}·武神之力", "self")
                
                messages.append(f"{self.name}使用了{skill_name}！队友血量恢复，攻击力大幅提升！")
                messages.append(f"{delay_turns}回合后将满血复活！")
                messages.append(f"自身攻击力翻倍，全队攻击力提升{int(all_allies_attack_buff*100)}%！")
                return total_heal, messages
            
            # 通用SELF_BUFF处理
            attack_mult = effects.get("attack_multiplier", 1.0)
            defense_mult = effects.get("defense_multiplier", 1.0)
            turns = effects.get("turns", 1)
            self.add_stat_modifier(attack_mult, defense_mult, turns, skill_name, "self")
            
            buff_desc = []
            if attack_mult > 1.0:
                buff_desc.append(f"攻击力提升{int((attack_mult-1)*100)}%")
            elif attack_mult < 1.0:
                buff_desc.append(f"攻击力下降{int((1-attack_mult)*100)}%")
            if defense_mult > 1.0:
                buff_desc.append(f"防御力提升{int((defense_mult-1)*100)}%")
            elif defense_mult < 1.0:
                buff_desc.append(f"防御力下降{int((1-defense_mult)*100)}%")
            
            messages.append(f"{self.name}使用了{skill_name}，{', '.join(buff_desc)}，持续{turns}回合！")
            return 0, messages
        
        elif category == SkillCategory.ENEMY_DEBUFF:
            # 改变敌方属性多回合
            if target:
                target_attack_mult = effects.get("target_attack_multiplier", 1.0)
                turns = effects["turns"]
                target.add_stat_modifier(target_attack_mult, 1.0, turns, skill_name, "enemy")
                
                debuff_desc = []
                if target_attack_mult < 1.0:
                    debuff_desc.append(f"攻击力下降{int((1-target_attack_mult)*100)}%")
                
                messages.append(f"{self.name}使用了{skill_name}，{target.name}{', '.join(debuff_desc)}，持续{turns}回合！")
                return 0, messages
        
        elif category == SkillCategory.SPECIAL_ATTACK:
            # 必杀技
            if target:
                effects = skill_data["effects"]
                
                # 处理不同类型的必杀技
                base_damage = effects.get("base_damage", 0)
                ignore_defense_damage_min = effects.get("ignore_defense_damage_min", 0)
                ignore_defense_damage_max = effects.get("ignore_defense_damage_max", 0)
                execute_threshold = effects.get("execute_threshold", 0)
                
                actual_damage = 0
                
                # 检查是否触发斩杀效果
                if execute_threshold > 0 and target.get_hp_percentage() < execute_threshold:
                    target.hp = 0
                    messages.append(f"{self.name}使用了{skill_name}，{target.name}的HP低于{int(execute_threshold*100)}%，直接被击败！")
                    return target.max_hp, messages
                
                # 处理固定伤害
                elif base_damage > 0:
                    actual_damage = target.take_damage(base_damage)
                    messages.append(f"{self.name}使用了{skill_name}，对{target.name}造成{actual_damage}点伤害！")
                
                # 处理无视防御的随机伤害
                elif ignore_defense_damage_min > 0 and ignore_defense_damage_max > 0:
                    random_damage = random.randint(ignore_defense_damage_min, ignore_defense_damage_max)
                    target.hp = max(0, target.hp - random_damage)
                    actual_damage = random_damage
                    messages.append(f"{self.name}使用了{skill_name}，无视防御对{target.name}造成{actual_damage}点伤害！")
                
                else:
                    # 如果没有明确的伤害定义，使用power值
                    power_damage = skill_data.get("power", 0)
                    if power_damage > 0:
                        actual_damage = target.take_damage(power_damage)
                        messages.append(f"{self.name}使用了{skill_name}，对{target.name}造成{actual_damage}点伤害！")
                    else:
                        messages.append(f"{self.name}使用了{skill_name}，但没有产生效果！")
                
                return actual_damage, messages
        
        elif category == SkillCategory.TEAM_BUFF:
            # 团队增益技能
            effects = skill_data["effects"]
            team_attack_mult = effects.get("team_attack_multiplier", 1.0)
            team_defense_mult = effects.get("team_defense_multiplier", 1.0)
            team_hp_cost = effects.get("team_hp_cost", 0)
            turns = effects.get("turns", 1)
            
            total_effect = 0
            
            # 给所有队友添加攻击力和防御力增益
            if allies and (team_attack_mult != 1.0 or team_defense_mult != 1.0):
                for ally in allies:
                    if not ally.is_fainted():  # 包括使用者自己
                        ally.add_stat_modifier(team_attack_mult, team_defense_mult, turns, f"{skill_name}·团队加持", "self")
                        
                        buff_desc = []
                        if team_attack_mult != 1.0:
                            attack_buff_percentage = int((team_attack_mult - 1.0) * 100)
                            buff_desc.append(f"攻击力提升{attack_buff_percentage}%")
                        if team_defense_mult != 1.0:
                            defense_buff_percentage = int((team_defense_mult - 1.0) * 100)
                            buff_desc.append(f"防御力提升{defense_buff_percentage}%")
                        
                        messages.append(f"{ally.name}的{', '.join(buff_desc)}，持续{turns}回合！")
            
            # 处理团队血量损失
            if allies and team_hp_cost > 0:
                for ally in allies:
                    if not ally.is_fainted():  # 包括使用者自己
                        hp_loss = int(ally.max_hp * team_hp_cost)
                        ally.hp = max(1, ally.hp - hp_loss)  # 血量不会降到0以下
                        total_effect += hp_loss
                        messages.append(f"{ally.name}失去了{hp_loss}点血量！")
            
            messages.append(f"{self.name}使用了{skill_name}！全队攻击力大幅提升！")
            return total_effect, messages
            
        elif category == SkillCategory.TEAM_HEAL:
            # 团队治疗技能
            effects = skill_data["effects"]
            team_heal_percentage = effects.get("team_heal_percentage", 0)
            turns = effects.get("turns", 1)
            
            total_heal = 0
            
            if allies and team_heal_percentage > 0:
                for ally in allies:
                    if not ally.is_fainted():  # 包括使用者自己
                        if turns > 1:
                            # 持续治疗
                            heal_per_turn = int(ally.max_hp * team_heal_percentage)
                            ally.add_continuous_heal(heal_per_turn, turns, f"{skill_name}·团队治疗")
                            total_heal += heal_per_turn * turns
                            messages.append(f"{ally.name}将在接下来{turns}回合内每回合回复{heal_per_turn}点HP！")
                        else:
                            # 立即治疗
                            heal_amount = int(ally.max_hp * team_heal_percentage)
                            old_hp = ally.hp
                            ally.hp = min(ally.max_hp, ally.hp + heal_amount)
                            actual_heal = ally.hp - old_hp
                            total_heal += actual_heal
                            if actual_heal > 0:
                                messages.append(f"{ally.name}恢复了{actual_heal}点血量！")
            
            messages.append(f"{self.name}使用了{skill_name}！全队获得治疗效果！")
            return total_heal, messages
            
        elif category == SkillCategory.TEAM_DEBUFF:
            # 团队减益技能（对敌方团队）
            effects = skill_data["effects"]
            direct_damage = effects.get("direct_damage", 0)
            target_attack_mult = effects.get("target_attack_multiplier", 1.0)
            turns = effects.get("turns", 1)
            
            total_damage = 0
            
            # 对目标造成直接伤害
            if target and direct_damage > 0:
                actual_damage = target.take_damage(direct_damage)
                total_damage += actual_damage
                messages.append(f"{self.name}使用了{skill_name}，对{target.name}造成{actual_damage}点伤害！")
            
            # 对目标添加攻击力减益（注：这里只能处理单个目标，多目标需要在战斗系统中处理）
            if target and target_attack_mult != 1.0:
                target.add_stat_modifier(target_attack_mult, 1.0, turns, f"{skill_name}·减益效果", "enemy")
                debuff_percentage = int((1.0 - target_attack_mult) * 100)
                messages.append(f"{target.name}的攻击力下降{debuff_percentage}%，持续{turns}回合！")
            
            messages.append(f"{self.name}使用了{skill_name}！对敌方造成伤害和减益效果！")
            return total_damage, messages

        elif category == SkillCategory.SPECIAL:
            # 特殊技能处理（包括多回合技能）
            effects = skill_data["effects"]
            
            # 处理天下兵马大元帅技能
            if skill_name == "天下兵马大元帅":
                # 第一回合：增益效果
                attack_mult = effects.get("attack_multiplier", 1.0)
                defense_mult = effects.get("defense_multiplier", 1.0)
                turns = effects.get("turns", 2)
                self.add_stat_modifier(attack_mult, defense_mult, turns, skill_name, "self")
                
                # 第二回合：延迟伤害
                delayed_damage_percentage = effects.get("delayed_damage_percentage", 0)
                delayed_turns = effects.get("delayed_turns", 1)
                if delayed_damage_percentage > 0 and target:
                    self.add_delayed_effect("damage_percentage", delayed_damage_percentage, delayed_turns, f"{skill_name}·万箭齐发", "self", "enemy")
                
                messages.append(f"{self.name}使用了{skill_name}！攻击力提升{int((attack_mult-1)*100)}%，防御力提升{int((defense_mult-1)*100)}%！")
                messages.append(f"第二回合将造成{int(delayed_damage_percentage*100)}%攻击力伤害！")
                return 0, messages
            
            # 处理ValueConcern!技能
            elif skill_name == "ValueConcern!":
                # 无敌2回合 + 攻击力变为80%
                invincible_turns = effects.get("invincible_turns", 2)
                attack_mult = effects.get("attack_multiplier", 0.8)
                self.add_stat_modifier(attack_mult, 1.0, invincible_turns, f"{skill_name}·价值关怀", "self")
                
                # 2回合后造成240%伤害并自杀
                final_damage_percentage = effects.get("final_damage_percentage", 2.4)
                if target:
                    self.add_delayed_effect("damage_percentage", final_damage_percentage, 2, f"{skill_name}·最终爆发", "self", "enemy")
                
                # 自杀效果
                if effects.get("self_sacrifice", False):
                    self.add_delayed_effect("self_sacrifice", 0, 2, f"{skill_name}·献身", "self", "self")
                
                messages.append(f"{self.name}使用了{skill_name}！无敌2回合，攻击力变为80%！")
                messages.append(f"2回合后将造成{int(final_damage_percentage*100)}%攻击力伤害并献身！")
                return 0, messages
            
            # 其他特殊技能的通用处理
            else:
                messages.append(f"{self.name}使用了{skill_name}！")
                return 0, messages
        
        return 0, messages
    
    def apply_status_effects(self, target_pokemon=None):
        """应用状态效果（每回合调用）"""
        messages = []
        
        # 处理连续伤害
        for effect in self.status_effects["continuous_damage"][:]:
            damage = effect["damage"]
            self.hp = max(0, self.hp - damage)
            messages.append(f"{self.name}受到{effect['name']}的持续伤害{damage}点！")
            effect["turns"] -= 1
            if effect["turns"] <= 0:
                self.status_effects["continuous_damage"].remove(effect)
                messages.append(f"{self.name}的{effect['name']}效果消失了！")
        
        # 处理连续治疗
        for effect in self.status_effects["continuous_heal"][:]:
            heal = effect["heal"]
            old_hp = self.hp
            self.hp = min(self.max_hp, self.hp + heal)
            actual_heal = self.hp - old_hp
            if actual_heal > 0:
                messages.append(f"{self.name}受到{effect['name']}的治疗效果，回复{actual_heal}点HP！")
            effect["turns"] -= 1
            if effect["turns"] <= 0:
                self.status_effects["continuous_heal"].remove(effect)
                messages.append(f"{self.name}的{effect['name']}效果消失了！")
        
        # 处理延迟效果
        for effect in self.status_effects["delayed_effects"][:]:
            if effect["trigger_turn"] <= self.battle_turn_counter:
                effect_type = effect["effect_type"]
                value = effect["value"]
                name = effect["name"]
                
                if effect_type == "damage_percentage":
                    # 按攻击力百分比造成伤害
                    damage = int(self.attack * value)
                    if effect["target"] == "enemy" and target_pokemon:
                        target_pokemon.hp = max(0, target_pokemon.hp - damage)
                        messages.append(f"{name}触发！{target_pokemon.name}受到{damage}点伤害！")
                    elif effect["target"] == "self":
                        self.hp = max(0, self.hp - damage)
                        messages.append(f"{name}触发！{self.name}受到{damage}点伤害！")
                        
                elif effect_type == "heal_percentage":
                    # 按最大血量百分比治疗
                    heal = int(self.max_hp * value)
                    old_hp = self.hp
                    self.hp = min(self.max_hp, self.hp + heal)
                    actual_heal = self.hp - old_hp
                    if actual_heal > 0:
                        messages.append(f"{name}触发！{self.name}恢复{actual_heal}点HP！")
                        
                elif effect_type == "self_sacrifice":
                    # 自杀效果
                    self.hp = 0
                    messages.append(f"{name}触发！{self.name}血量归零！")
                
                # 移除已触发的延迟效果
                self.status_effects["delayed_effects"].remove(effect)
        
        # 处理属性修改效果
        if self.status_effects["stat_modifiers"]["turns_remaining"] > 0:
            self.status_effects["stat_modifiers"]["turns_remaining"] -= 1
            if self.status_effects["stat_modifiers"]["turns_remaining"] <= 0:
                self.status_effects["stat_modifiers"]["attack_multiplier"] = 1.0
                self.status_effects["stat_modifiers"]["defense_multiplier"] = 1.0
                messages.append(f"{self.name}的{self.status_effects['stat_modifiers']['effect_name']}效果消失了！")
                self.status_effects["stat_modifiers"]["effect_name"] = ""
        
        return messages
    
    def add_continuous_damage(self, damage, turns, name, caster="self"):
        """添加连续伤害效果"""
        self.status_effects["continuous_damage"].append({
            "damage": damage,
            "turns": turns,
            "name": name,
            "caster": caster  # 记录施放者
        })
    
    def add_continuous_heal(self, heal, turns, name, caster="self"):
        """添加连续治疗效果"""
        self.status_effects["continuous_heal"].append({
            "heal": heal,
            "turns": turns,
            "name": name,
            "caster": caster  # 记录施放者
        })
    
    def add_stat_modifier(self, attack_mult, defense_mult, turns, name, caster="self"):
        """添加属性修改效果"""
        self.status_effects["stat_modifiers"] = {
            "attack_multiplier": attack_mult,
            "defense_multiplier": defense_mult,
            "turns_remaining": turns,
            "effect_name": name,
            "caster": caster  # 记录施放者
        }
    
    def add_delayed_effect(self, effect_type, value, delay_turns, name, caster="self", target="enemy"):
        """添加延迟效果"""
        trigger_turn = self.battle_turn_counter + delay_turns
        self.status_effects["delayed_effects"].append({
            "effect_type": effect_type,  # "damage", "heal", "damage_percentage", "heal_percentage", "self_sacrifice"
            "value": value,
            "trigger_turn": trigger_turn,
            "name": name,
            "caster": caster,
            "target": target
        })
    
    def increment_battle_turn(self):
        """增加战斗回合计数器"""
        self.battle_turn_counter += 1
        
    def to_dict(self):
        """转换为字典用于存档"""
        return {
            "name": self.name,
            "original_name": self.original_name,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next_level": self.exp_to_next_level,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "hp": self.hp,
            "moves": self.moves,
            "advantages": self.advantages,
            "disadvantages": self.disadvantages,
            "is_evolving": self.is_evolving,
            "sp": self.sp,
            "max_sp": self.max_sp,
            "has_em_guidebook": self.has_em_guidebook,
            "status_effects": self.status_effects,
            "battle_turn_counter": self.battle_turn_counter
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典加载数据"""
        pkm = cls(
            data["name"],
            data["level"],
            data["exp"]
        )
        pkm.original_name = data["original_name"]
        pkm.exp_to_next_level = data["exp_to_next_level"]
        pkm.base_hp = data["base_hp"]
        pkm.base_attack = data["base_attack"]
        pkm.base_defense = data["base_defense"]
        pkm.hp = data["hp"]
        pkm.moves = data["moves"]
        pkm.advantages = data["advantages"]
        pkm.disadvantages = data["disadvantages"]
        pkm.is_evolving = data["is_evolving"]
        
        # 加载SP系统数据（向后兼容）
        pkm.sp = data.get("sp", SP_CONFIG["initial_sp"])
        pkm.max_sp = data.get("max_sp", SP_CONFIG["max_sp"])
        pkm.has_em_guidebook = data.get("has_em_guidebook", False)
        
        # 加载状态效果数据（向后兼容）
        pkm.status_effects = data.get("status_effects", {
            "continuous_damage": [],
            "continuous_heal": [],
            "delayed_effects": [],
            "stat_modifiers": {
                "attack_multiplier": 1.0,
                "defense_multiplier": 1.0,
                "turns_remaining": 0,
                "effect_name": "",
                "caster": "self"
            }
        })
        
        # 加载回合计数器（向后兼容）
        pkm.battle_turn_counter = data.get("battle_turn_counter", 0)
        
        # 确保现有数据的向后兼容性
        if "caster" not in pkm.status_effects["stat_modifiers"]:
            pkm.status_effects["stat_modifiers"]["caster"] = "self"
        
        # 为现有的连续伤害和治疗效果添加施放者信息
        for effect in pkm.status_effects["continuous_damage"]:
            if "caster" not in effect:
                effect["caster"] = "self"
        
        for effect in pkm.status_effects["continuous_heal"]:
            if "caster" not in effect:
                effect["caster"] = "self"
        
        return pkm

class Player:
    def __init__(self, name):
        self.name = name
        self.pokemon_team = []
        self.x, self.y = 0, 0
        self.backpack = []
        self.inventory = {}  # 添加inventory属性，用于商店系统
        self.pokeballs = 20
        self.master_balls = 0  # 大师球数量
        # 初始化精灵球到inventory中
        self.inventory["精灵球"] = self.pokeballs
        self.inventory["大师球"] = self.master_balls
        self.default_pokemon_index = 0
        self.ut = 100  # UT值，初始100点
        self.max_ut = 100  # 最大UT值
        self.ut_empty_counter = 0  # UT耗尽提示计数器
        self.stage = 1  # 游戏阶段，用于决定大BOSS
        self.mini_bosses_defeated = 0  # 击败的小BOSS数量
        # 根据配置设置初始金币数量
        config = GameInitialConfig.get_current_config()
        self.money = config["money"]
        self.battle_prevention_steps = 0  # PTO通知剩余步数
        self.initialize_backpack()
        
    def initialize_backpack(self):
        # 使用配置系统获取初始物品
        config = GameInitialConfig.get_current_config()
        for item_config in config["items"]:
            item_name = item_config["name"]
            quantity = item_config.get("quantity", 1)
            
            # 从物品数据库获取完整的物品数据
            item_data = ItemConfig.get_item_data(item_name)
            if item_data:
                # 根据数量添加物品到背包
                for _ in range(quantity):
                    self.backpack.append(Item(
                        item_data["name"],
                        item_data["description"],
                        item_data["item_type"],
                        item_data["effect"],
                        item_data.get("price", 0)
                    ))
                # 同时初始化inventory
                self.inventory[item_name] = quantity
        
    def add_pokemon(self, pokemon):
        self.pokemon_team.append(pokemon)
        if len(self.pokemon_team) == 1:
            self.default_pokemon_index = 0
            
    def get_active_pokemon(self):
        if 0 <= self.default_pokemon_index < len(self.pokemon_team) and not self.pokemon_team[self.default_pokemon_index].is_fainted():
            return self.pokemon_team[self.default_pokemon_index]
            
        for pokemon in self.pokemon_team:
            if not pokemon.is_fainted():
                return pokemon
        return None
        
    def set_default_pokemon(self, index):
        if 0 <= index < len(self.pokemon_team):
            self.default_pokemon_index = index
            return True
        return False
        
    def add_item(self, item):
        self.backpack.append(item)
        
    def remove_item(self, index):
        if 0 <= index < len(self.backpack):
            return self.backpack.pop(index)
        return None
        
    def use_ut_restorer(self, item_index):
        """使用UT补充剂"""
        if 0 <= item_index < len(self.backpack):
            item = self.backpack[item_index]
            if item.item_type == "ut_restore":
                result = item.use(player=self)
                self.remove_item(item_index)
                self.ut_empty_counter = 0  # 重置UT耗尽提示
                return result
        return "无法使用UT补充剂"
        
    def decrease_ut(self, amount=1):
        """减少UT值"""
        self.ut = max(0, self.ut - amount)
        # 如果UT耗尽，处理惩罚
        if self.ut <= 0:
            self.ut_empty_counter = 60  # 显示1秒的提示（假设60FPS）
            # 所有顾问降一级
            for pokemon in self.pokemon_team:
                pokemon.lose_level()
            return True
        return False
        
    def to_dict(self):
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "pokemon_team": [p.to_dict() for p in self.pokemon_team],
            "backpack": [{"name": i.name, "description": i.description, 
                          "item_type": i.item_type, "effect": i.effect} for i in self.backpack],
            "pokeballs": self.pokeballs,
            "master_balls": self.master_balls,
            "default_pokemon_index": self.default_pokemon_index,
            "ut": self.ut,
            "stage": self.stage,
            "mini_bosses_defeated": self.mini_bosses_defeated,
            "money": self.money,
            "battle_prevention_steps": self.battle_prevention_steps
        }
        
    @classmethod
    def from_dict(cls, data):
        player = cls(data["name"])
        player.x = data["x"]
        player.y = data["y"]
        player.pokemon_team = [Pokemon.from_dict(p) for p in data["pokemon_team"]]
        player.backpack = [Item(i["name"], i["description"], i["item_type"], i["effect"]) for i in data["backpack"]]
        player.pokeballs = data.get("pokeballs", 20)
        player.master_balls = data.get("master_balls", 0)
        player.default_pokemon_index = data.get("default_pokemon_index", 0)
        player.ut = data.get("ut", 100)
        player.stage = data.get("stage", 1)
        player.mini_bosses_defeated = data.get("mini_bosses_defeated", 0)
        player.money = data.get("money", 1000)
        player.battle_prevention_steps = data.get("battle_prevention_steps", 0)
        return player

# 地图生成类
class MapGenerator:
    @staticmethod
    def generate_map():
        """生成随机地图"""
        # 初始化地图为平地
        game_map = [[TILE_TYPES['flat'] for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        
        # 随机放置不同地形
        for x in range(MAP_SIZE):
            for y in range(MAP_SIZE):
                # 跳过起点
                if x == 0 and y == 0:
                    continue
                    
                # 随机地形
                rand = random.random()
                if rand < 0.3:
                    game_map[x][y] = TILE_TYPES['grass']
                elif rand < 0.45:
                    game_map[x][y] = TILE_TYPES['wheat']
                elif rand < 0.55:
                    game_map[x][y] = TILE_TYPES['sand']
                elif rand < 0.6:
                    game_map[x][y] = TILE_TYPES['rock']
                elif rand < 0.65:
                    game_map[x][y] = TILE_TYPES['wood']
                    
        # 放置城镇（2-3个）
        town_count = random.randint(2, 3)
        for _ in range(town_count):
            x, y = MapGenerator.get_random_position(game_map, avoid_start=True)
            game_map[x][y] = TILE_TYPES['town']
            
        # 放置特殊地块
        special_locations = {
            'chest': 3,    # 3个宝箱
            'shop': 2,     # 2个商店
            'training': 2, # 2个训练中心
            'portal': 1    # 1个传送门
        }
        
        for tile_type, count in special_locations.items():
            for _ in range(count):
                x, y = MapGenerator.get_random_position(game_map, avoid_start=True)
                game_map[x][y] = TILE_TYPES[tile_type]
                
        # 放置小BOSS（2个）
        for _ in range(2):
            x, y = MapGenerator.get_random_position(game_map, min_distance=5, avoid_start=True)
            game_map[x][y] = TILE_TYPES['mini_boss']
            
        # 放置当前阶段的大BOSS
        x, y = MapGenerator.get_random_position(game_map, min_distance=8, avoid_start=True)
        game_map[x][y] = TILE_TYPES['stage_boss']
        
        return game_map
        
    @staticmethod
    def get_random_position(game_map, min_distance=0, avoid_start=False):
        """获取随机位置，可指定与起点的最小距离"""
        while True:
            x = random.randint(0, MAP_SIZE - 1)
            y = random.randint(0, MAP_SIZE - 1)
            
            # 避开起点
            if avoid_start and x == 0 and y == 0:
                continue
                
            # 检查距离起点的距离
            distance = abs(x) + abs(y)  # 曼哈顿距离
            if distance >= min_distance:
                # 确保该位置是平地（可以被替换）
                if game_map[x][y] == TILE_TYPES['flat']:
                    return x, y

# 游戏状态管理
class GameState:
    EXPLORING = 0
    BATTLE = 1
    BOSS_BATTLE = 2  # BOSS战斗状态
    BATTLE_MOVE_SELECT = 3
    BATTLE_ANIMATION = 4
    MENU_MAIN = 5
    MENU_POKEMON = 6
    MENU_POKEMON_DETAIL = 7
    MENU_BACKPACK = 8
    MENU_ITEM_USE = 9
    CAPTURE_SELECT = 10  # 捕捉选择状态
    EVOLUTION_ANIMATION = 11
    CAPTURE_ANIMATION = 12
    BATTLE_SWITCH_POKEMON = 13
    UT_EMPTY_ALERT = 14  # UT耗尽提示
    MESSAGE = 15  # 消息显示状态
    SHOP = 16  # 商店界面
    TRAINING_CENTER = 17  # 训练中心界面
    MENU_TARGET_SELECTION = 18  # 目标选择状态

# 通知系统类
class NotificationSystem:
    def __init__(self):
        self.notifications = []
        self.max_notifications = 3
        self.notification_duration = 3000  # 3秒
        
    def add_notification(self, message, notification_type="info"):
        """添加通知消息"""
        notification = {
            "message": message,
            "type": notification_type,  # "success", "info", "warning", "error"
            "timestamp": pygame.time.get_ticks(),
            "alpha": 255
        }
        
        self.notifications.append(notification)
        
        # 限制通知数量
        if len(self.notifications) > self.max_notifications:
            self.notifications.pop(0)
    
    def update(self):
        """更新通知状态"""
        current_time = pygame.time.get_ticks()
        
        # 移除过期的通知
        self.notifications = [n for n in self.notifications 
                            if current_time - n["timestamp"] < self.notification_duration]
        
        # 更新透明度（淡出效果）
        for notification in self.notifications:
            elapsed = current_time - notification["timestamp"]
            if elapsed > self.notification_duration * 0.7:  # 最后30%时间开始淡出
                fade_progress = (elapsed - self.notification_duration * 0.7) / (self.notification_duration * 0.3)
                notification["alpha"] = max(0, int(255 * (1 - fade_progress)))
    
    def draw(self, screen):
        """绘制通知"""
        y_offset = 10
        
        for i, notification in enumerate(self.notifications):
            # 根据类型选择颜色
            if notification["type"] == "success":
                bg_color = (0, 150, 0)
                text_color = WHITE
            elif notification["type"] == "warning":
                bg_color = (255, 165, 0)
                text_color = BLACK
            elif notification["type"] == "error":
                bg_color = (200, 0, 0)
                text_color = WHITE
            else:  # info
                bg_color = (0, 100, 200)
                text_color = WHITE
            
            # 创建带透明度的表面
            notification_surface = pygame.Surface((400, 50))
            notification_surface.set_alpha(notification["alpha"])
            notification_surface.fill(bg_color)
            
            # 添加边框
            pygame.draw.rect(notification_surface, WHITE, (0, 0, 400, 50), 2)
            
            # 渲染文字
            font = FontManager.get_font(16)
            text = font.render(notification["message"], True, text_color)
            text_rect = text.get_rect(center=(200, 25))
            notification_surface.blit(text, text_rect)
            
            # 绘制到屏幕
            screen.blit(notification_surface, (SCREEN_WIDTH - 410, y_offset + i * 60))
    
    def clear_all(self):
        """清除所有通知"""
        self.notifications.clear()

# 按钮类
class Button:
    __slots__ = ['rect', 'text', 'action', 'color', 'hover_color', 'active', 'text_color', '_cached_surface']
    
    def __init__(self, x, y, width, height, text, action=None, text_color=BLACK, color=GRAY, hover_color=LIGHT_BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.active = False
        self.text_color = text_color
        self._cached_surface = None
        
    def draw(self, surface):
        color = self.hover_color if self.active else self.color
        # 如果是橙色按钮，绘制半透明效果
        if color == ORANGE:
            button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            button_surface.fill((255, 165, 0, 128))  # 橙色，50%透明度
            surface.blit(button_surface, self.rect)
        else:
            pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # 获取小字体
        small_font = FontManager.get_font(16)
        draw_multiline_text(
            surface, 
            self.text, 
            small_font, 
            self.text_color, 
            self.rect.x + 5, 
            self.rect.y + 5, 
            self.rect.width - 10, 
            2
        )
        
    def check_hover(self, pos):
        self.active = self.rect.collidepoint(pos)
        
    def check_click(self, pos):
        return self.rect.collidepoint(pos)

# 图像资源管理
class GameImages:
    def __init__(self):
        self.player = ImageLoader.load_image(ImageConfig.player_image, (TILE_SIZE-20, TILE_SIZE-20))
        self.grass = ImageLoader.load_image(ImageConfig.grass_image, (TILE_SIZE, TILE_SIZE))
        self.town = ImageLoader.load_image(ImageConfig.town_image, (TILE_SIZE, TILE_SIZE))
        self.rock = ImageLoader.load_image(ImageConfig.rock_image, (TILE_SIZE, TILE_SIZE))
        self.flat = ImageLoader.load_image(ImageConfig.flat_image, (TILE_SIZE, TILE_SIZE))
        self.wheat = ImageLoader.load_image(ImageConfig.wheat_image, (TILE_SIZE, TILE_SIZE))
        self.sand = ImageLoader.load_image(ImageConfig.sand_image, (TILE_SIZE, TILE_SIZE))
        self.wood = ImageLoader.load_image(ImageConfig.wood_image, (TILE_SIZE, TILE_SIZE))
        self.chest = ImageLoader.load_image(ImageConfig.chest_image, (TILE_SIZE, TILE_SIZE))
        self.shop = ImageLoader.load_image(ImageConfig.shop_image, (TILE_SIZE, TILE_SIZE))
        self.training = ImageLoader.load_image(ImageConfig.training_image, (TILE_SIZE, TILE_SIZE))
        self.portal = ImageLoader.load_image(ImageConfig.portal_image, (TILE_SIZE, TILE_SIZE))
        self.mini_boss = ImageLoader.load_image(ImageConfig.mini_boss_image, (TILE_SIZE, TILE_SIZE))
        self.stage_boss = ImageLoader.load_image(ImageConfig.stage_boss_image, (TILE_SIZE, TILE_SIZE))
        self.battle_bg = ImageLoader.load_image(ImageConfig.battle_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.boss_battle_bg = ImageLoader.load_image(ImageConfig.boss_battle_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.ut_empty = ImageLoader.load_image(ImageConfig.ut_empty_image, (300, 200))
        
        self.pokemon = {}
        for name, path in ImageConfig.pokemon_images.items():
            self.pokemon[name] = ImageLoader.load_image(path, (150, 150))


# 战斗系统类

# 商店类
class Shop:
    def __init__(self):
        self.regular_items = []
        self.rare_items = []
        self.selected_item = None
        self.selected_quantity = 1
        self.refresh_shop()
    
    def refresh_shop(self):
        """刷新商店物品"""
        import copy
        import random
        
        # 重置常规物品 - 从数据库加载完整数据
        self.regular_items = []
        for item_name in ItemConfig.shop_items["regular"]:
            item_data = ItemConfig.get_item_data(item_name)
            if item_data:
                # 创建商店物品的副本，包含所有必要的属性
                shop_item = copy.deepcopy(item_data)
                self.regular_items.append(shop_item)
        
        # 随机选择1-3个稀有物品
        self.rare_items = []
        num_rare = random.randint(1, 3)
        available_rare = list(ItemConfig.shop_items["rare"])  # 创建副本
        for _ in range(min(num_rare, len(available_rare))):
            if available_rare:
                item_name = random.choice(available_rare)
                item_data = ItemConfig.get_item_data(item_name)
                if item_data:
                    # 创建商店物品的副本
                    shop_item = copy.deepcopy(item_data)
                    self.rare_items.append(shop_item)
                available_rare.remove(item_name)
    
    def get_all_items(self):
        """获取所有商店物品"""
        return self.regular_items + self.rare_items
    
    def buy_item(self, player, item_index, quantity=1):
        """购买物品"""
        all_items = self.get_all_items()
        if 0 <= item_index < len(all_items):
            item = all_items[item_index]
            total_price = item["price"] * quantity
            
            if player.money >= total_price and item["stock"] >= quantity:
                # 扣除金钱
                player.money -= total_price
                # 减少库存
                item["stock"] -= quantity
                
                # 添加物品到背包
                for _ in range(quantity):
                    if item["item_type"] == "pokeball":
                        player.pokeballs += item["effect"]
                        # 同步更新inventory
                        if "精灵球" in player.inventory:
                            player.inventory["精灵球"] = player.pokeballs
                    elif item["item_type"] == "master_ball":
                        player.master_balls = getattr(player, 'master_balls', 0) + item["effect"]
                        # 同步更新inventory
                        if "大师球" in player.inventory:
                            player.inventory["大师球"] = player.master_balls
                    else:
                        # 创建物品对象并添加到背包
                        new_item = Item(item["name"], item["description"], 
                                      item["item_type"], item["effect"], item["price"])
                        player.add_item(new_item)
                
                return f"购买成功！花费{total_price}金币"
            elif player.money < total_price:
                return "金币不足！"
            else:
                return "库存不足！"
        return "无效的物品选择！"

# 训练中心类
class TrainingCenter:
    def __init__(self):
        self.deposited_pokemon = {}  # 存储寄养的顾问 {pokemon_id: deposit_info}
        self.daily_exp_gain = 20  # 每天获得的经验值
    
    def heal_all_pokemon(self, player):
        """恢复所有顾问的HP"""
        # 免费恢复所有顾问的HP
        healed_pokemon = []
        for pokemon in player.pokemon_team:
            old_hp = pokemon.hp
            pokemon.hp = pokemon.max_hp
            healed_pokemon.append(f"• {pokemon.name}: {old_hp} → {pokemon.max_hp} HP")
        
        # 返回详细的治疗信息
        result_text = f"HP恢复服务完成！\n\n免费服务，无需花费金币\n当前金币: {player.money}\n\n恢复详情:\n" + "\n".join(healed_pokemon)
        return result_text
    
    def deposit_pokemon(self, player, pokemon_index):
        """寄养顾问"""
        if 0 <= pokemon_index < len(player.pokemon_team):
            pokemon = player.pokemon_team[pokemon_index]
            if len(player.pokemon_team) > 1:  # 确保至少保留一个顾问
                import time
                deposit_info = {
                    "pokemon": pokemon,
                    "deposit_time": time.time(),
                    "last_exp_time": time.time()
                }
                pokemon_id = f"{pokemon.name}_{pokemon_index}"
                self.deposited_pokemon[pokemon_id] = deposit_info
                player.pokemon_team.remove(pokemon)
                
                # 返回详细的寄养信息
                result_text = f"顾问寄养成功！\n\n寄养顾问: {pokemon.name}\n等级: Lv.{pokemon.level}\n当前HP: {pokemon.hp}/{pokemon.max_hp}\n\n寄养说明:\n• 每天自动获得 {self.daily_exp_gain} 经验值\n• 可随时回来领取顾问\n• 寄养期间会持续成长\n\n队伍中剩余顾问: {len(player.pokemon_team)} 个"
                return result_text
            else:
                return "寄养失败！\n\n错误原因: 至少要保留一个顾问在队伍中\n\n建议:\n• 先捕捉更多顾问\n• 或者选择其他顾问进行寄养"
        return "寄养失败！\n\n错误原因: 无效的顾问选择\n\n请重新选择要寄养的顾问。"
    
    def withdraw_pokemon(self, player, pokemon_id):
        """领取顾问"""
        if pokemon_id in self.deposited_pokemon:
            deposit_info = self.deposited_pokemon[pokemon_id]
            pokemon = deposit_info["pokemon"]
            
            # 计算经验值增长和寄养时间
            import time
            current_time = time.time()
            days_passed = (current_time - deposit_info["last_exp_time"]) / 86400  # 86400秒 = 1天
            total_days = (current_time - deposit_info["deposit_time"]) / 86400
            exp_gained = int(days_passed * self.daily_exp_gain)
            
            old_level = pokemon.level
            if exp_gained > 0:
                pokemon.gain_experience(exp_gained)
                deposit_info["last_exp_time"] = current_time
            
            # 将顾问加回队伍
            player.pokemon_team.append(pokemon)
            del self.deposited_pokemon[pokemon_id]
            
            # 返回详细的领取信息
            level_change = f"Lv.{old_level} → Lv.{pokemon.level}" if pokemon.level > old_level else f"Lv.{pokemon.level}"
            result_text = f"顾问领取成功！\n\n领回顾问: {pokemon.name}\n等级变化: {level_change}\n\n寄养统计:\n• 寄养天数: {total_days:.1f} 天\n• 获得经验: {exp_gained} 点\n• 当前HP: {pokemon.hp}/{pokemon.max_hp}\n\n{pokemon.name} 很高兴重新加入队伍！"
            return result_text
        else:
            return "领取失败！\n\n错误原因: 未找到指定的寄养顾问\n\n请检查是否选择了正确的顾问。"
    
    def get_deposited_pokemon_info(self):
        """获取寄养顾问信息"""
        info_list = []
        import time
        current_time = time.time()
        
        for pokemon_id, deposit_info in self.deposited_pokemon.items():
            pokemon = deposit_info["pokemon"]
            days_deposited = (current_time - deposit_info["deposit_time"]) / 86400
            potential_exp = int((current_time - deposit_info["last_exp_time"]) / 86400 * self.daily_exp_gain)
            
            info_list.append({
                "id": pokemon_id,
                "name": pokemon.name,
                "level": pokemon.level,
                "days_deposited": int(days_deposited),
                "potential_exp": potential_exp
            })
        
        return info_list

# ==================== 游戏主程序 ====================

# 游戏主类
class PokemonGame:
    def __init__(self):
        self.state = GameState.EXPLORING
        self.map = GameMap()
        self.player = Player("BA")
        self.images = self.load_images()
        self.wild_pokemon = None
        self.boss_pokemon = None  # 当前BOSS
        self.is_boss_battle = False  # 是否为BOSS战
        self.battle_buttons = []
        self.move_buttons = []
        
        # 初始化模块化组件
        self.combat_manager = CombatManager(self)
        self.ui_renderer = UIRenderer(self)
        self.battle_messages = []
        self.battle_step = 0
        self.current_turn = None
        self.animation_timer = 0
        self.animation_delay = 1000
        self.menu_buttons = []
        self.selected_pokemon_index = 0
        self.selected_item_index = 0
        # 技能按钮滚动相关
        self.skill_scroll_offset = 0
        self.max_visible_skills = 3  # 最多同时显示3个技能按钮
        self.skill_scrollbar_area = None  # 技能选择界面的滚动条区域
        self.skill_slider_area = None  # 技能选择界面的滑块区域
        self.skill_scrollbar_dragging = False  # 是否正在拖拽滚动条
        self.skill_drag_start_y = 0  # 拖拽开始的Y坐标
        self.skill_drag_start_offset = 0  # 拖拽开始时的滚动偏移
        self.skill_forget_dialog = None  # 技能忘记对话框状态
        
        # 技能悬浮提示相关
        self.hovered_skill_info = None  # 存储当前悬浮的技能信息
        
        # 背包滚动相关
        self.backpack_scroll_offset = 0
        # 动态计算最大可见物品数（将在绘制时计算）
        
        # 必杀技台词显示相关
        self.ally_ultimate_line = None  # 我方必杀技台词
        self.enemy_ultimate_line = None  # 敌方必杀技台词
        self.ally_line_display = False  # 是否显示我方台词
        self.enemy_line_display = False  # 是否显示敌方台词
        # 商店和训练中心
        self.shop = Shop()
        self.training_center = TrainingCenter()
        self.shop_selected_item = 0
        self.shop_selected_quantity = 1
        self.training_selected_pokemon = 0
        self.setup_game()
        
        self.menu_stack = []
        self.pending_item_use = None  # 待处理的物品使用
        
        # 初始化通知系统
        self.notification_system = NotificationSystem()
        
        # 性能优化：缓存系统
        self._surface_cache = {}
        self._text_cache = {}
        self._map_surface = None
        self._map_dirty = True
        self._ui_surfaces = {}
        self._last_state = None
        
        # Surface对象池
        self._surface_pool = {}
        self._max_pool_size = 50
        
        # 脏矩形系统
        self._dirty_rects = []
        self._last_player_pos = (self.player.x, self.player.y)
        self._need_full_redraw = True
        
        # 战斗场景缓存
        self._battle_bg_cache = None
        self._battle_ui_cache = None
        self._battle_cache_dirty = True
        
        # 退出请求标志
        self._request_exit = False
        
    def load_images(self):
        images = GameImages()
        return images
    
    def _get_cached_surface(self, key, create_func, *args, **kwargs):
        """获取缓存的surface，如果不存在则创建"""
        if key not in self._surface_cache:
            self._surface_cache[key] = create_func(*args, **kwargs)
        return self._surface_cache[key]
    
    def _get_cached_text(self, text, font, color):
        """获取缓存的文本surface"""
        cache_key = f"{text}_{font}_{color}"
        if cache_key not in self._text_cache:
            self._text_cache[cache_key] = font.render(text, True, color)
        return self._text_cache[cache_key]
    
    def _invalidate_cache(self, pattern=None):
        """清除缓存"""
        if pattern is None:
            self._surface_cache.clear()
            self._text_cache.clear()
        else:
            # 清除匹配模式的缓存
            keys_to_remove = [k for k in self._surface_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._surface_cache[key]
    
    def _get_pooled_surface(self, size, flags=0):
        """从对象池获取Surface，如果不存在则创建"""
        key = f"{size[0]}x{size[1]}_{flags}"
        if key not in self._surface_pool:
            self._surface_pool[key] = []
        
        pool = self._surface_pool[key]
        if pool:
            return pool.pop()
        else:
            if flags & pygame.SRCALPHA:
                return pygame.Surface(size, pygame.SRCALPHA)
            else:
                return pygame.Surface(size)
    
    def _return_surface_to_pool(self, surface, size, flags=0):
        """将Surface返回到对象池"""
        key = f"{size[0]}x{size[1]}_{flags}"
        if key not in self._surface_pool:
            self._surface_pool[key] = []
        
        pool = self._surface_pool[key]
        if len(pool) < self._max_pool_size:
            # 清除surface内容
            surface.fill((0, 0, 0, 0) if flags & pygame.SRCALPHA else (0, 0, 0))
            pool.append(surface)
    
    def _add_dirty_rect(self, rect):
        """添加需要重绘的矩形区域"""
        self._dirty_rects.append(rect)
    
    def _clear_dirty_rects(self):
        """清除所有脏矩形"""
        self._dirty_rects.clear()
    
    def _check_player_movement(self):
        """检查玩家是否移动并添加相应的脏矩形"""
        current_pos = (self.player.x, self.player.y)
        if current_pos != self._last_player_pos:
            # 计算地图显示偏移
            map_width = self.map.size * TILE_SIZE
            map_height = self.map.size * TILE_SIZE
            start_x = (SCREEN_WIDTH - map_width) // 2
            start_y = (SCREEN_HEIGHT - map_height) // 2
            
            # 添加旧位置和新位置的脏矩形
            old_x = start_x + self._last_player_pos[1] * TILE_SIZE
            old_y = start_y + self._last_player_pos[0] * TILE_SIZE
            new_x = start_x + current_pos[1] * TILE_SIZE
            new_y = start_y + current_pos[0] * TILE_SIZE
            
            self._add_dirty_rect(pygame.Rect(old_x, old_y, TILE_SIZE, TILE_SIZE))
            self._add_dirty_rect(pygame.Rect(new_x, new_y, TILE_SIZE, TILE_SIZE))
            
            self._last_player_pos = current_pos
    
    def _optimized_render(self):
        """优化的渲染方法"""
        # 绘制当前状态
        if self.state == GameState.EXPLORING:
            self.draw_exploration()
        elif self.state in [GameState.BATTLE, GameState.BOSS_BATTLE, 
                           GameState.BATTLE_MOVE_SELECT, GameState.BATTLE_ANIMATION,
                           GameState.CAPTURE_ANIMATION, GameState.BATTLE_SWITCH_POKEMON]:
            self.draw_battle()
        elif self.state in [GameState.MENU_MAIN, GameState.MENU_POKEMON,
                           GameState.MENU_POKEMON_DETAIL, GameState.MENU_BACKPACK,
                           GameState.MENU_ITEM_USE, GameState.CAPTURE_SELECT, 
                           GameState.MENU_TARGET_SELECTION]:
            self.draw_menu()
        elif self.state == GameState.MESSAGE:
            self.draw_exploration()  # 先绘制地图背景
            self.draw_message()  # 再绘制消息框
        elif self.state == GameState.SHOP:
            self.draw_shop()
        elif self.state == GameState.TRAINING_CENTER:
            self.draw_training_center()
        
        # 重置完全重绘标志
        self._need_full_redraw = False
        
        # 如果状态改变，清除相关缓存
        if self.state in [GameState.BATTLE, GameState.BOSS_BATTLE]:
            if self._battle_cache_dirty:
                self._battle_bg_cache = None
                self._battle_ui_cache = None
    
    def _create_optimized_map_surface(self):
        """创建优化的地图surface"""
        map_surface = pygame.Surface((MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT))
        
        # 创建tile类型到图像的映射以减少条件判断
        tile_images = {
            0: self.images.grass,
            1: self.images.town,
            2: self.images.rock,
            3: self.images.sand,
            4: self.images.wheat,
            5: self.images.wood,
            6: self.images.flat,
            7: self.images.chest,
            8: self.images.shop,
            9: self.images.training,
            10: self.images.portal,
            11: self.images.mini_boss,
            12: self.images.stage_boss
        }
        
        # 批量绘制地图块
        for i in range(self.map.size):
            for j in range(self.map.size):
                x = j * TILE_SIZE
                y = i * TILE_SIZE
                tile_type = self.map.get_tile_type(i, j)
                
                # 特殊处理宝箱：如果已经打开，则不显示宝箱图像
                if tile_type == 7:  # chest
                    if self.map.is_chest_opened(i, j):
                        # 宝箱已打开，显示对应的地面图块
                        continue
                
                # 使用映射直接获取图像
                if tile_type in tile_images:
                    map_surface.blit(tile_images[tile_type], (x, y))
                
                # 特殊处理BOSS区域
                if tile_type == 12:  # stage_boss
                    pygame.draw.rect(map_surface, RED, (x, y, TILE_SIZE, TILE_SIZE), 4)
                    # 使用缓存的文本
                    font, small_font, battle_font, menu_font = get_fonts()
                    boss_text = self._get_cached_text("BOSS", small_font, RED)
                    text_rect = boss_text.get_rect(center=(x + TILE_SIZE//2, y + TILE_SIZE//2))
                    map_surface.blit(boss_text, text_rect)
        
        return map_surface
        
    def setup_game(self):
        self.player.x, self.player.y = 3, 3
        
        # 根据配置添加初始顾问
        config = GameInitialConfig.get_current_config()
        for advisor_data in config["advisors"]:
            pokemon = Pokemon(advisor_data["name"], level=advisor_data["level"])
            # 设置SP值
            pokemon.sp = advisor_data["sp"]
            # 如果SP大于默认最大值，更新最大SP
            if advisor_data["sp"] > pokemon.max_sp:
                pokemon.max_sp = advisor_data["sp"]
            self.player.add_pokemon(pokemon)
        
    def start_battle(self, battle_type="wild"):
        """开始战斗，battle_type: "wild", "mini_boss" 或 "stage_boss"""
        # 委托给战斗管理器处理
        return self.combat_manager.start_battle(battle_type)
    
    def generate_battle_drop(self):
        if self.is_boss_battle and self.boss_pokemon:
            # BOSS战胜利奖励
            boss_name = self.boss_pokemon.name
            # 查找BOSS奖励配置
            boss_data = next((b for b in PokemonConfig.mini_bosses + PokemonConfig.stage_bosses if b["name"] == boss_name), None)
            
            if boss_data and "reward" in boss_data:
                messages = []
                # 奖励顾问
                if "pokemon" in boss_data["reward"]:
                    pkm_name = boss_data["reward"]["pokemon"]
                    self.player.add_pokemon(Pokemon(pkm_name, level=10))
                    messages.append(f"获得了新顾问: {pkm_name}！")
                
                # 奖励物品
                if "items" in boss_data["reward"]:
                    for item_name in boss_data["reward"]["items"]:
                        # 从物品数据库查找物品数据
                        item_data = ItemConfig.get_item_data(item_name)
                        if item_data:
                            new_item = Item(
                                item_data["name"],
                                item_data["description"],
                                item_data["item_type"],
                                item_data["effect"],
                                item_data.get("price", 0)
                            )
                            self.player.add_item(new_item)
                            
                            if item_data["item_type"] == "pokeball":
                                self.player.pokeballs += item_data["effect"]
                                # 同步更新inventory
                                if "精灵球" in self.player.inventory:
                                    self.player.inventory["精灵球"] = self.player.pokeballs
                                messages.append(f"获得了{item_data['name']}！现在有{self.player.pokeballs}个精灵球。")
                            else:
                                messages.append(f"获得了{item_data['name']}！已添加到背包。")
                        else:
                            print(f"警告: BOSS奖励物品 '{item_name}' 在数据库中未找到")
                
                # 如果是大BOSS，提升游戏阶段
                if any(boss_name == b["name"] for b in PokemonConfig.stage_bosses):
                    self.player.stage += 1
                    messages.append(f"恭喜！你已进入第{self.player.stage}阶段！")
                
                return messages
        else:
            # 普通战斗奖励
            if random.random() < 0.8:
                # 基于稀有度的加权随机选择
                weights = []
                for name in ItemConfig.drop_pool_names:
                    item_data = ItemConfig.get_item_data(name)
                    weights.append(item_data.get("rarity", 1) if item_data else 1)
                
                total_rarity = sum(weights)
                rand_val = random.uniform(0, total_rarity)
                
                cumulative = 0
                for i, weight in enumerate(weights):
                    cumulative += weight
                    if rand_val <= cumulative:
                        item_name = ItemConfig.drop_pool_names[i]
                        item_data = ItemConfig.get_item_data(item_name)
                        if item_data:
                            new_item = Item(
                                item_data["name"],
                                item_data["description"],
                                item_data["item_type"],
                                item_data["effect"],
                                item_data.get("price", 0)
                            )
                            self.player.add_item(new_item)
                        
                            if item_data["item_type"] == "pokeball":
                                self.player.pokeballs += item_data["effect"]
                                # 同步更新inventory
                                if "精灵球" in self.player.inventory:
                                    self.player.inventory["精灵球"] = self.player.pokeballs
                                return [f"太棒了！野生的顾问留下了{item_data['name']}！现在有{self.player.pokeballs}个精灵球。"]
                            return [f"太棒了！野生的顾问留下了{item_data['name']}！已添加到背包。"]
                        else:
                            print(f"警告: 掉落物品 '{item_name}' 在数据库中未找到")
                            break
        
        # 没有获得物品
        consolation_messages = [
            "野生的顾问逃走了，什么也没留下...",
            "虽然没获得物品，但你的顾问获得了宝贵的战斗经验！",
            "对方什么也没留下，但你感觉顾问变得更强了！"
        ]
        return [random.choice(consolation_messages)]
        
    def process_battle_turn(self, move_idx=None, action=None, ball_type="normal"):
        """处理战斗回合，委托给战斗管理器"""
        return self.combat_manager.process_battle_turn(move_idx, action, ball_type)
    
    def update_battle_animation(self):
        """更新战斗动画，委托给战斗管理器"""
        return self.combat_manager.update_battle_animation()
    
    def flee_battle(self):
        """逃跑"""
        self.process_battle_turn(action="flee")
        
    def use_item_in_battle(self, item_index):
        if 0 <= item_index < len(self.player.backpack):
            item = self.player.backpack[item_index]
            self.current_turn = {
                "action": "use_item",
                "item": item,
                "item_index": item_index
            }
            self.state = GameState.BATTLE_ANIMATION
            self.battle_step = 0
            self.animation_timer = pygame.time.get_ticks()
        
    def switch_pokemon(self, index):
        if 0 <= index < len(self.player.pokemon_team) and not self.player.pokemon_team[index].is_fainted():
            self.player.set_default_pokemon(index)
            new_pkm = self.player.get_active_pokemon()
            advantages = ", ".join(new_pkm.advantages)
            disadvantages = ", ".join(new_pkm.disadvantages)
            self.battle_messages.append(f"派出了{new_pkm.name} (Lv.{new_pkm.level})！")
            self.battle_messages.append(f"优点: {advantages}, 缺点: {disadvantages}")
            
            # 如果在战斗中切换顾问，当前回合结束
            if self.state in [GameState.BATTLE, GameState.BOSS_BATTLE, GameState.BATTLE_SWITCH_POKEMON]:
                self.battle_messages.append("更换顾问后，当前回合结束！")
                # 创建一个切换顾问的turn来触发回合结束逻辑
                self.current_turn = {
                    "action": "switch_pokemon",
                    "switched": True
                }
                self.state = GameState.BATTLE_ANIMATION
                self.battle_step = 7  # 直接结束回合
                self.animation_timer = pygame.time.get_ticks()
            else:
                self.go_back()
            return True
        return False
        
    def revive_all_pokemon(self):
        """将所有顾问的HP恢复到1点"""
        for pokemon in self.player.pokemon_team:
            if pokemon.is_fainted():
                pokemon.hp = 1
        self.battle_messages.append("所有顾问的HP恢复到1点！")

    def end_battle(self):
        try:
            # 清除必杀技台词显示
            self.ally_line_display = False
            self.enemy_line_display = False
            self.ally_ultimate_line = None
            self.enemy_ultimate_line = None
            
            # 判断战斗结果
            player_victory = False
            enemy_pkm = self.boss_pokemon if self.is_boss_battle else self.wild_pokemon
            
            # 检查是否通过击败敌方顾问获胜
            if enemy_pkm and enemy_pkm.is_fainted():
                player_victory = True
            
            # 检查是否通过捕捉成功获胜
            if (self.current_turn and 
                self.current_turn.get("action") == "catch" and 
                self.current_turn.get("capture_success", False)):
                player_victory = True
                
            # 修复顾问HP bug：当顾问在战斗中被击败后，将其HP设为1以防止再次进入战斗时死机
            for pokemon in self.player.pokemon_team:
                if pokemon.is_fainted():
                    pokemon.hp = 1
                
            # BOSS战胜利，增加计数器并刷新地图
            if self.is_boss_battle and player_victory:
                # 判断击败的是哪种BOSS并增加计数
                boss_name = self.boss_pokemon.name if self.boss_pokemon else ""
                is_mini_boss = any(boss_name == b["name"] for b in PokemonConfig.mini_bosses)
                if is_mini_boss:
                    self.player.mini_bosses_defeated += 1
                    self.battle_messages.append(f"击败了小BOSS！已击败{self.player.mini_bosses_defeated}个小BOSS")
                else:
                    self.battle_messages.append("击败了阶段BOSS！")
                
                self.map.can_refresh = True  # 击败BOSS后允许地图刷新
                self.map.refresh_map()
                self.shop.refresh_shop()  # 同时刷新商店物品
                self.battle_messages.append("地图已刷新，新的BOSS出现了！")
                self.battle_messages.append("商店物品也已更新！")
            
            # BOSS战失败，返回训练中心附近
            if self.is_boss_battle and not player_victory:
                # 将玩家传送到训练中心附近
                if self.map.training_position:
                    new_x, new_y = self.map.get_adjacent_tile(self.map.training_position[0], self.map.training_position[1])
                    self.player.x, self.player.y = new_x, new_y
                    self.battle_messages.append("BOSS战失败，被送回训练中心附近！")
                else:
                    # 如果没有训练中心，使用默认位置
                    self.player.x, self.player.y = 3, 3
                    self.battle_messages.append("BOSS战失败，被送回安全区域！")
            
            self.state = GameState.EXPLORING
            self.wild_pokemon = None
            self.boss_pokemon = None
            self.is_boss_battle = False
            self.battle_buttons = []
            self.move_buttons = []
            self.battle_messages = []
            self.current_turn = None
            self.animation_delay = 1000
            self.menu_stack = []
        except Exception as e:
            print(f"结束战斗时出错: {e}")
            self.state = GameState.EXPLORING
            self.wild_pokemon = None
            self.boss_pokemon = None
            self.is_boss_battle = False
            self.menu_stack = []
    
    def save_game(self):
        try:
            save_data = {
                "player": self.player.to_dict(),
                "map": self.map.to_dict(),
                "timestamp": pygame.time.get_ticks()
            }
            
            with open("pokemon_save.json", "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            
            # 添加成功通知
            self.notification_system.add_notification("游戏已成功保存！", "success")
            return "游戏已保存！"
        except Exception as e:
            print(f"保存游戏出错: {e}")
            # 添加错误通知
            self.notification_system.add_notification("保存失败！请检查磁盘空间", "error")
            return "保存失败！"
    
    def load_game(self):
        try:
            if not os.path.exists("pokemon_save.json"):
                # 添加警告通知
                self.notification_system.add_notification("没有找到存档文件！", "warning")
                return "没有找到存档文件！"
                
            with open("pokemon_save.json", "r", encoding="utf-8") as f:
                save_data = json.load(f)
                
            self.player = Player.from_dict(save_data["player"])
            self.map = GameMap.from_dict(save_data["map"])
            
            self.images = self.load_images()
            
            self.state = GameState.EXPLORING
            self.wild_pokemon = None
            self.boss_pokemon = None
            self.is_boss_battle = False
            self.battle_buttons = []
            self.move_buttons = []
            self.battle_messages = []
            self.menu_stack = []
            
            # 添加成功通知
            self.notification_system.add_notification("游戏已成功加载！", "success")
            return "游戏已加载！"
        except Exception as e:
            print(f"加载游戏出错: {e}")
            # 添加错误通知
            self.notification_system.add_notification("加载失败！存档文件可能损坏", "error")
            return "加载失败！"
    
    def _create_menu_button(self, x, y, width, height, text, action):
        """创建标准样式的菜单按钮"""
        return Button(x, y, width, height, text, action, BLACK, MINT_GREEN, MINT_GREEN_HOVER)
    
    def open_main_menu(self):
        self.menu_stack.append(self.state)
        self.menu_buttons = [
            self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 130, 200, 40, "顾问", "pokemon"),
            self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 80, 200, 40, "背包", "backpack"),
            self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30, 200, 40, "保存", "save"),
            self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 20, 200, 40, "加载", "load"),
            self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 70, 200, 40, "退出", "exit"),
            self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 120, 200, 40, "返回上级", "back")
        ]
        self.state = GameState.MENU_MAIN
    
    
    def open_pokemon_menu(self):
        self.menu_stack.append(self.state)
        self.menu_buttons = []
        for i, pokemon in enumerate(self.player.pokemon_team):
            status = "战斗不能" if pokemon.is_fainted() else f"HP: {pokemon.hp}/{pokemon.max_hp}"
            is_default = i == self.player.default_pokemon_index
            text = f"{i+1}. {pokemon.name} (Lv.{pokemon.level}) - {status}"
            if is_default:
                text += " [默认出战]"
                
            self.menu_buttons.append(
                self._create_menu_button(SCREEN_WIDTH//2 - 200, 100 + i * 60, 400, 50, text, f"pokemon_{i}")
            )
        
        self.menu_buttons.append(
            self._create_menu_button(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 150, 300, 40, "设置默认出战顾问", "set_default")
        )
        self.menu_buttons.append(
            self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 100, 200, 40, "返回上级", "back")
        )
        self.state = GameState.MENU_POKEMON
        self.selected_pokemon_index = 0
    
    def show_pokemon_detail(self, index):
        if 0 <= index < len(self.player.pokemon_team):
            self.menu_stack.append(self.state)
            self.selected_pokemon_index = index
            self.detail_scroll_offset = 0  # 重置滚动偏移
            self.menu_buttons = [
                self._create_menu_button(SCREEN_WIDTH//2 - 350, SCREEN_HEIGHT - 150, 200, 40, "设为默认出战顾问", f"make_default_{index}"),
                self._create_menu_button(SCREEN_WIDTH//2 - 350, SCREEN_HEIGHT - 100, 200, 40, "返回上级", "back")
            ]
            self.state = GameState.MENU_POKEMON_DETAIL
    
    def open_backpack_menu(self):
        self.menu_stack.append(self.state)
        self.menu_buttons = []
        
        # 初始化背包选择状态
        self.selected_item_index = 0
        self.backpack_popup_state = False  # 是否显示确认弹窗
        self.backpack_scroll_offset = 0  # 重置滚动偏移
        
        self.state = GameState.MENU_BACKPACK
    
    def open_item_use_menu(self, item_index):
        if 0 <= item_index < len(self.player.backpack):
            self.menu_stack.append(self.state)
            self.selected_item_index = item_index
            self.menu_buttons = []
            
            # 检查是否在战斗中，决定使用什么颜色
            is_in_battle = self.state in [GameState.BATTLE, GameState.BOSS_BATTLE, GameState.BATTLE_MOVE_SELECT, GameState.BATTLE_SWITCH_POKEMON]
            button_color = ORANGE if is_in_battle else MINT_GREEN
            hover_color = ORANGE if is_in_battle else MINT_GREEN_HOVER
            
            for i, pokemon in enumerate(self.player.pokemon_team):
                status = "战斗不能" if pokemon.is_fainted() else f"HP: {pokemon.hp}/{pokemon.max_hp}"
                self.menu_buttons.append(
                    Button(
                        SCREEN_WIDTH//2 - 200, 
                        100 + i * 60, 
                        400, 
                        50, 
                        f"对 {pokemon.name} 使用", 
                        f"use_on_{i}",
                        BLACK, button_color, hover_color
                    )
                )
            
            self.menu_buttons.append(
                Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 100, 200, 40, "返回上级", "back", BLACK, button_color, hover_color)
            )
            self.state = GameState.MENU_ITEM_USE
    
    def use_item(self, item_index, target_index):
        if 0 <= item_index < len(self.player.backpack) and 0 <= target_index < len(self.player.pokemon_team):
            item = self.player.backpack[item_index]
            target = self.player.pokemon_team[target_index]
            
            result = item.use(target, self.player)
            
            if item.item_type in ["heal", "evolution", "exp_boost", "ut_restore", "battle_prevent", "skill_blind_box", "skill_book"]:
                self.player.remove_item(item_index)
                # 添加物品使用成功通知
                self.notification_system.add_notification(f"成功使用了{item.name}！", "success")
            else:
                # 添加物品使用信息通知
                self.notification_system.add_notification(f"使用了{item.name}", "info")
                
            return result
        # 添加物品使用失败通知
        self.notification_system.add_notification("无法使用物品！", "warning")
        return "无法使用物品"
    
    def use_item_directly(self, item_index):
        """直接使用物品,自动选择最佳目标"""
        if 0 <= item_index < len(self.player.backpack):
            item = self.player.backpack[item_index]
            
            if item.item_type == "heal":
                # 选择HP最低的顾问
                target = None
                for pokemon in self.player.pokemon_team:
                    if pokemon.hp < pokemon.max_hp:
                        if target is None or pokemon.hp < target.hp:
                            target = pokemon
                
                if target:
                    result = item.use(target, self.player)
                    self.player.remove_item(item_index)
                    # 添加治疗成功通知
                    self.notification_system.add_notification(f"对{target.name}使用了{item.name}！", "success")
                    return result
                else:
                    # 添加治疗失败通知
                    self.notification_system.add_notification("所有顾问HP已满！", "info")
                    return "所有顾问HP已满"
                    
            elif item.item_type == "ut_restore":
                result = item.use(None, self.player)
                self.player.remove_item(item_index)
                # 添加UT恢复通知
                self.notification_system.add_notification(f"使用了{item.name},恢复UT！", "success")
                return result
                
            elif item.item_type == "battle_prevent":
                result = item.use(None, self.player)
                self.player.remove_item(item_index)
                # 添加PTO通知使用通知
                self.notification_system.add_notification(f"使用了{item.name},战斗保护生效！", "success")
                return result
                
            elif item.item_type == "skill_blind_box":
                result = item.use(None, self.player)
                self.player.remove_item(item_index)
                # 添加盲盒使用通知,显示详细结果
                self.notification_system.add_notification(result, "success")
                
                # 调整选择索引到新生成的技能书（背包末尾）
                if self.player.backpack:
                    self.selected_item_index = len(self.player.backpack) - 1
                    # 调整滚动偏移以显示新物品
                    visible_area_height = SCREEN_HEIGHT - 140
                    max_visible_items = visible_area_height // 60
                    if len(self.player.backpack) > max_visible_items:
                        self.backpack_scroll_offset = len(self.player.backpack) - max_visible_items
                
                return result
                
            elif item.item_type == "evolution":
                # 进化道具：先使用,然后选择目标
                self.pending_item_use = {
                    "item_index": item_index,
                    "item": item,
                    "type": "evolution"
                }
                self.open_target_selection_menu("evolution")
                return "请选择要进化的顾问"
            
            elif item.item_type == "permanent_boost":
                # 攻击力/防御力道具：先使用,然后选择目标
                self.pending_item_use = {
                    "item_index": item_index,
                    "item": item,
                    "type": "permanent_boost"
                }
                self.open_target_selection_menu("permanent_boost")
                return "请选择要使用道具的顾问"
                
            elif item.item_type == "skill_book":
                # 必杀技学习书：需要选择学习的顾问
                self.pending_item_use = {
                    "item_index": item_index,
                    "item": item,
                    "type": "skill_book"
                }
                self.open_target_selection_menu("skill_book")
                return "请选择要学习必杀技的顾问"
                
            else:
                # 添加物品无法使用通知
                self.notification_system.add_notification("这个物品无法直接使用", "warning")
                return "这个物品无法直接使用"
        
        # 添加物品不存在通知
        self.notification_system.add_notification("物品不存在", "error")
        return "物品不存在"
    
    def open_target_selection_menu(self, item_type):
        """打开目标选择菜单"""
        self.menu_stack.append(self.state)
        self.menu_buttons = []
        
        # 检查是否在战斗中，决定使用什么颜色
        is_in_battle = self.state in [GameState.BATTLE, GameState.BOSS_BATTLE, GameState.BATTLE_MOVE_SELECT, GameState.BATTLE_SWITCH_POKEMON]
        button_color = ORANGE if is_in_battle else MINT_GREEN
        hover_color = ORANGE if is_in_battle else MINT_GREEN_HOVER
        
        # 为每个顾问创建按钮
        for i, pokemon in enumerate(self.player.pokemon_team):
            button_text = f"{pokemon.name} (Lv.{pokemon.level})"
            
            # 根据物品类型添加额外信息
            if item_type == "evolution" and hasattr(self, 'pending_item_use'):
                item = self.pending_item_use["item"]
                if hasattr(pokemon, 'can_evolve_with_item') and pokemon.can_evolve_with_item(item.name):
                    button_text += " ✓"
                else:
                    button_text += " ✗"
            elif item_type == "permanent_boost":
                # 所有顾问都可以使用攻击力/防御力道具
                button_text += " ✓"
            elif item_type == "skill_book":
                # 所有顾问都可以学习必杀技
                button_text += " ✓"
            
            self.menu_buttons.append(
                Button(
                    SCREEN_WIDTH//2 - 200, 150 + i * 60, 400, 50,
                    button_text,
                    f"target_{i}",
                    BLACK, button_color, hover_color
                )
            )
        
        self.menu_buttons.append(
            Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 100, 200, 40, "取消", "cancel", BLACK, button_color, hover_color)
        )
        self.state = GameState.MENU_TARGET_SELECTION
    
    def use_pending_item_on_target(self, target_index):
        """对目标使用待处理的物品"""
        if not hasattr(self, 'pending_item_use') or not self.pending_item_use:
            return "没有待使用的物品"
        
        if 0 <= target_index < len(self.player.pokemon_team):
            item_data = self.pending_item_use
            item = item_data["item"]
            item_index = item_data["item_index"]
            target = self.player.pokemon_team[target_index]
            
            # 检查物品是否仍在背包中（防止重复使用）
            if item_index >= len(self.player.backpack) or self.player.backpack[item_index] != item:
                self.pending_item_use = None
                return "物品已被使用或不存在"
            
            result = item.use(target, self.player)
            
            # 检查是否需要技能忘记对话框
            if "SKILL_FORGET_DIALOG|" in result:
                skill_name = result.split("|")[1]
                self.open_skill_forget_dialog(target, skill_name, item, item_index)
                return "正在选择要忘记的技能..."
            
            # 检查是否使用成功
            success = False
            if "|FAILED" in result:
                success = False
                result = result.replace("|FAILED", "")  # 移除失败标记
            elif item_data["type"] == "evolution":
                success = "进化" in result and "无法" not in result
            elif item_data["type"] == "permanent_boost":
                success = "提升" in result or "增加" in result
            elif item_data["type"] == "skill_book":
                success = "学会了" in result or "学习了" in result
            
            if success:
                self.player.remove_item(item_index)
                self.notification_system.add_notification(f"成功对{target.name}使用了{item.name}！", "success")
            else:
                self.notification_system.add_notification(result, "info")
            
            # 清除待处理的物品使用
            self.pending_item_use = None
            return result
        
        return "无效的目标"
    
    def open_skill_forget_dialog(self, target, new_skill, item, item_index):
        """打开技能忘记选择对话框"""
        self.skill_forget_dialog = {
            'target': target,
            'new_skill': new_skill,
            'item': item,
            'item_index': item_index,
            'active': True
        }
        # 保存当前状态到菜单栈
        self.menu_stack.append(self.state)
        self.state = GameState.MENU_TARGET_SELECTION  # 复用目标选择状态
        
        # 创建技能选择按钮
        self.menu_buttons = []
        for i, move in enumerate(target.moves):
            button_text = f"忘记 {move['name']}"
            self.menu_buttons.append(
                Button(
                    SCREEN_WIDTH//2 - 200, 150 + i * 60, 400, 50,
                    button_text,
                    f"forget_{i}",
                    BLACK, LIGHT_BLUE, MENU_HOVER
                )
            )
        
        # 添加取消按钮
        self.menu_buttons.append(
            Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 100, 200, 40, "取消", "cancel", BLACK, LIGHT_BLUE, MENU_HOVER)
        )
    
    def handle_skill_forget_selection(self, selection):
        """处理技能忘记选择"""
        if not hasattr(self, 'skill_forget_dialog') or not self.skill_forget_dialog['active']:
            return "没有活跃的技能忘记对话框"
        
        dialog = self.skill_forget_dialog
        target = dialog['target']
        new_skill = dialog['new_skill']
        item = dialog['item']
        item_index = dialog['item_index']
        
        if selection == "cancel":
            # 取消学习技能
            self.skill_forget_dialog = None
            return "取消学习技能"
        elif selection.startswith("forget_"):
            # 选择忘记的技能
            forget_index = int(selection.split("_")[1])
            if 0 <= forget_index < len(target.moves):
                old_move = target.moves[forget_index]
                target.moves[forget_index] = {"name": new_skill}
                
                # 移除物品
                self.player.remove_item(item_index)
                self.skill_forget_dialog = None
                
                return f"{target.name}忘记了{old_move['name']}，学会了{new_skill}！"
        
        return "无效的选择"
    
    def _calculate_text_height(self, text, font, max_width, start_y):
        """计算文本在指定宽度下的渲染高度"""
        if not text.strip():
            return start_y + font.get_height()
        
        import textwrap
        lines = textwrap.wrap(text, width=int(max_width / font.size('A')[0]))
        if not lines:
            lines = [text]
        
        return start_y + len(lines) * font.get_height() + 5  # 添加5像素行间距
    
    def go_back(self):
        if self.menu_stack:
            prev_state = self.menu_stack.pop()
            self.state = prev_state
            
            # 统一的按钮位置计算
            bottom_area_height = int(SCREEN_HEIGHT * 0.4)
            bottom_area_y = SCREEN_HEIGHT - bottom_area_height
            button_width = int(SCREEN_WIDTH * 0.22)   # 按钮宽度，留些边距
            button_area_x = SCREEN_WIDTH - button_width - 5  # 右对齐，距离边框5像素
            button_height = 40
            button_spacing = 10
            
            if prev_state == GameState.BATTLE:
                self.battle_buttons = [
                    Button(button_area_x, bottom_area_y + 20, button_width, button_height, "战斗", "fight", BLACK, ORANGE, ORANGE),
                    Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 1, button_width, button_height, "背包", "bag", BLACK, ORANGE, ORANGE),
                    Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 2, button_width, button_height, "更换顾问", "switch", BLACK, ORANGE, ORANGE),
                    Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 3, button_width, button_height, "捕捉", "catch", BLACK, ORANGE, ORANGE),
                    Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 4, button_width, button_height, "逃跑", "flee", BLACK, ORANGE, ORANGE)
                ]
            elif prev_state == GameState.BOSS_BATTLE:
                self.battle_buttons = [
                    Button(button_area_x, bottom_area_y + 20, button_width, button_height, "战斗", "fight", BLACK, ORANGE, ORANGE),
                    Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 1, button_width, button_height, "背包", "bag", BLACK, ORANGE, ORANGE),
                    Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 2, button_width, button_height, "更换顾问", "switch", BLACK, ORANGE, ORANGE),
                    Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 3, button_width, button_height, "逃跑", "flee", BLACK, ORANGE, ORANGE)
                ]
            elif prev_state == GameState.BATTLE_MOVE_SELECT:
                # 不应该从技能选择界面返回到技能选择界面，这里应该重新创建战斗按钮
                if self.is_boss_battle:
                    self.battle_buttons = [
                        Button(button_area_x, bottom_area_y + 20, button_width, button_height, "战斗", "fight", BLACK, ORANGE, ORANGE),
                        Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 1, button_width, button_height, "背包", "bag", BLACK, ORANGE, ORANGE),
                        Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 2, button_width, button_height, "更换顾问", "switch", BLACK, ORANGE, ORANGE),
                        Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 3, button_width, button_height, "逃跑", "flee", BLACK, ORANGE, ORANGE)
                    ]
                else:
                    self.battle_buttons = [
                        Button(button_area_x, bottom_area_y + 20, button_width, button_height, "战斗", "fight", BLACK, ORANGE, ORANGE),
                        Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 1, button_width, button_height, "背包", "bag", BLACK, ORANGE, ORANGE),
                        Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 2, button_width, button_height, "更换顾问", "switch", BLACK, ORANGE, ORANGE),
                        Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 3, button_width, button_height, "捕捉", "catch", BLACK, ORANGE, ORANGE),
                        Button(button_area_x, bottom_area_y + 20 + (button_height + button_spacing) * 4, button_width, button_height, "逃跑", "flee", BLACK, ORANGE, ORANGE)
                    ]
            elif prev_state == GameState.MENU_MAIN:
                # 重新创建主菜单按钮
                self.menu_buttons = [
                    self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 80, 200, 40, "顾问", "pokemon"),
                    self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30, 200, 40, "背包", "backpack"),
                    self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 20, 200, 40, "保存", "save"),
                    self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 70, 200, 40, "加载", "load"),
                    self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 120, 200, 40, "退出", "exit"),
                    self._create_menu_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 170, 200, 40, "返回上级", "back")
                ]
            elif prev_state == GameState.EXPLORING:
                self.menu_buttons = []
        else:
            if self.state in [GameState.MENU_POKEMON, GameState.MENU_BACKPACK, GameState.MENU_ITEM_USE]:
                self.open_main_menu()
            else:
                self.state = GameState.EXPLORING
                self.menu_buttons = []
        
    def draw_exploration(self):
        """绘制探索界面，委托给UI渲染器"""
        return self.ui_renderer.draw_exploration(screen)
    
    def draw_battle(self):
        """绘制战斗界面，委托给UI渲染器"""
        return self.ui_renderer.draw_battle(screen)

    def draw_skill_tooltip(self, screen, skill_info):
        """绘制技能悬浮提示框"""
        try:
            # 获取鼠标位置
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # 提示框的基本设置
            tooltip_font = FontManager.get_font(16)
            tooltip_padding = 10
            tooltip_line_spacing = 5
            tooltip_max_width = 300
            
            # 构建要显示的文本行
            tooltip_lines = []
            tooltip_lines.append(f"技能: {skill_info['name']}")
            
            if skill_info.get('type'):
                tooltip_lines.append(f"属性: {skill_info['type']}")
            
            if skill_info.get('sp_cost', 0) > 0:
                tooltip_lines.append(f"SP消耗: {skill_info['sp_cost']}")
            else:
                tooltip_lines.append("SP消耗: 无")
            
            if skill_info.get('power', 0) > 0:
                tooltip_lines.append(f"威力: {skill_info['power']}")
            
            # 技能描述（可能需要换行）
            if skill_info.get('description'):
                tooltip_lines.append("")  # 空行分隔
                tooltip_lines.append("描述:")
                
                # 将长描述分成多行
                import textwrap
                desc_lines = textwrap.wrap(skill_info['description'], width=25)
                tooltip_lines.extend(desc_lines)
            
            # 计算提示框尺寸
            tooltip_width = 0
            tooltip_height = 0
            line_heights = []
            
            for line in tooltip_lines:
                if line:  # 非空行
                    text_surface = tooltip_font.render(line, True, BLACK)
                    tooltip_width = max(tooltip_width, text_surface.get_width())
                    line_height = text_surface.get_height()
                else:  # 空行
                    line_height = tooltip_font.get_height() // 2
                
                line_heights.append(line_height)
                tooltip_height += line_height + tooltip_line_spacing
            
            # 移除最后一个行间距
            if line_heights:
                tooltip_height -= tooltip_line_spacing
            
            # 添加内边距
            tooltip_width += tooltip_padding * 2
            tooltip_height += tooltip_padding * 2
            
            # 确保提示框不超出屏幕边界
            tooltip_x = mouse_x + 15
            tooltip_y = mouse_y - tooltip_height - 15
            
            if tooltip_x + tooltip_width > SCREEN_WIDTH:
                tooltip_x = mouse_x - tooltip_width - 15
            if tooltip_y < 0:
                tooltip_y = mouse_y + 15
            if tooltip_y + tooltip_height > SCREEN_HEIGHT:
                tooltip_y = SCREEN_HEIGHT - tooltip_height - 10
            
            # 绘制提示框背景
            tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
            tooltip_surface.fill((255, 255, 255, 240))  # 白色，94%不透明
            screen.blit(tooltip_surface, (tooltip_x, tooltip_y))
            
            # 绘制边框
            pygame.draw.rect(screen, BLACK, (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 2)
            
            # 绘制文本
            current_y = tooltip_y + tooltip_padding
            for i, line in enumerate(tooltip_lines):
                if line:  # 非空行
                    text_surface = tooltip_font.render(line, True, BLACK)
                    screen.blit(text_surface, (tooltip_x + tooltip_padding, current_y))
                
                current_y += line_heights[i] + tooltip_line_spacing
                
        except Exception as e:
            print(f"绘制技能提示框时出错: {e}")
            
    def handle_tile_event(self, tile_type):
        """处理地块事件"""
        # 首先检查是否触发随机遇敌
        encounter_result = self.map.check_encounter(self.player.x, self.player.y, self.player)
        if encounter_result == "wild":
            self.start_battle("wild")
            return
        elif encounter_result == "boss":
            self.start_battle("boss")
            return
            
        if tile_type == TILE_TYPES['grass']:
            # 草丛逻辑已在check_encounter中处理
            pass
                  
        elif tile_type == TILE_TYPES['chest']:
            # 检查宝箱是否已经打开
            if self.map.is_chest_opened(self.player.x, self.player.y):
                # 宝箱已经打开，什么都不做
                return
            
            # 宝箱奖励
            reward_messages = []
            
            # 使用地图的open_chest方法获取奖励
            chest_rewards = self.map.open_chest(self.player.x, self.player.y)
            if chest_rewards:
                for reward_type, reward_value in chest_rewards:
                    if reward_type == "item":
                        self.player.backpack.append(reward_value)
                        reward_messages.append(f"获得了{reward_value.name}！")
                    elif reward_type == "money":
                        self.player.money += reward_value
                        reward_messages.append(f"获得了{reward_value}金币！")
            else:
                # 如果map.open_chest没有返回奖励，使用原来的随机奖励逻辑作为备用
                reward_type = random.random()
                
                if reward_type < 0.4:  # 40%概率获得金钱
                    money_amount = random.randint(100, 500)
                    self.player.money += money_amount
                    reward_messages.append(f"获得了{money_amount}金币！")
                
                elif reward_type < 0.8:  # 40%概率获得物品
                    items = ["UT补充剂", "超级伤药", "精灵球"]
                    reward_item = random.choice(items)
                    # 创建物品对象并添加到背包
                    from collections import namedtuple
                    Item = namedtuple('Item', ['name', 'description', 'item_type', 'effect'])
                    item = Item(reward_item, f"从宝箱中获得的{reward_item}", "consumable", None)
                    self.player.backpack.append(item)
                    reward_messages.append(f"获得了{reward_item}！")
                
                else:  # 20%概率获得金钱+物品
                    money_amount = random.randint(50, 200)
                    self.player.money += money_amount
                    items = ["UT补充剂", "超级伤药", "精灵球"]
                    reward_item = random.choice(items)
                    from collections import namedtuple
                    Item = namedtuple('Item', ['name', 'description', 'item_type', 'effect'])
                    item = Item(reward_item, f"从宝箱中获得的{reward_item}", "consumable", None)
                    self.player.backpack.append(item)
                    reward_messages.append(f"获得了{money_amount}金币和{reward_item}！")
                
                # 标记宝箱为已打开（备用逻辑的情况下）
                self.map.open_chest(self.player.x, self.player.y)
            
            self.battle_result = f"发现宝箱！" + "".join(reward_messages)
            # 宝箱打开后变为1-6地块中的随机一块
            self.map.grid[self.player.x][self.player.y] = random.randint(1, 6)
            # 标记地图需要重新绘制
            self._map_dirty = True
            self.state = GameState.MESSAGE
            
        elif tile_type == TILE_TYPES['shop']:
            # 进入商店
            self.state = GameState.SHOP
            
        elif tile_type == TILE_TYPES['training']:
            # 进入训练中心
            self.state = GameState.TRAINING_CENTER
            
        elif tile_type == TILE_TYPES['portal']:
            # 传送门（随机传送）
            old_pos = (self.player.x, self.player.y)
            self.player.x, self.player.y = MapGenerator.get_random_position(self.map.grid)
            self.battle_result = f"通过传送门从({old_pos[0]},{old_pos[1]})传送到了({self.player.x},{self.player.y})！"
            self.state = GameState.MESSAGE
            
        elif tile_type == TILE_TYPES['mini_boss']:
            # 小BOSS战斗
            self.start_battle("mini_boss")
                
        elif tile_type == TILE_TYPES['stage_boss']:
            # 大BOSS战斗
            self.start_battle("stage_boss")

    
    def draw_message(self):
        """绘制消息界面"""
        try:
            # 绘制半透明背景遮罩
            overlay = SurfaceFactory.create_overlay((SCREEN_WIDTH, SCREEN_HEIGHT), BLACK, 180)
            screen.blit(overlay, (0, 0))
            
            # 检查是否有battle_messages需要显示
            if hasattr(self, 'battle_messages') and self.battle_messages:
                message_text = '\n'.join(self.battle_messages)
            elif hasattr(self, 'battle_result') and self.battle_result:
                message_text = self.battle_result
            else:
                message_text = "未知消息"
            
            # 根据消息长度动态调整消息框大小
            lines = message_text.split('\n')
            line_count = len(lines)
            
            # 动态计算消息框尺寸
            base_width = 650
            base_height = max(300, min(600, 80 + line_count * 25 + 80))  # 最小300，最大600
            msg_width, msg_height = base_width, base_height
            msg_x = (SCREEN_WIDTH - msg_width) // 2
            msg_y = (SCREEN_HEIGHT - msg_height) // 2
            
            # 判断是否是训练中心消息，使用特殊样式
            is_training_message = any(keyword in message_text for keyword in ["HP恢复", "寄养", "领取", "训练中心"])
            is_chest_message = "宝箱" in message_text
            
            if is_training_message:
                # 训练中心消息使用薄荷绿半透明背景
                training_surface = pygame.Surface((msg_width, msg_height), pygame.SRCALPHA)
                training_surface.fill((152, 251, 152, 220))  # 薄荷绿半透明
                screen.blit(training_surface, (msg_x, msg_y))
                pygame.draw.rect(screen, (32, 178, 170), (msg_x, msg_y, msg_width, msg_height), 3)
                text_color = BLACK
            elif is_chest_message:
                # 宝箱消息使用淡黄色半透明背景
                chest_surface = pygame.Surface((msg_width, msg_height), pygame.SRCALPHA)
                chest_surface.fill((255, 255, 224, 200))  # 淡黄色半透明
                screen.blit(chest_surface, (msg_x, msg_y))
                pygame.draw.rect(screen, (255, 215, 0), (msg_x, msg_y, msg_width, msg_height), 3)
                text_color = BLACK
            else:
                pygame.draw.rect(screen, WHITE, (msg_x, msg_y, msg_width, msg_height))
                pygame.draw.rect(screen, BLACK, (msg_x, msg_y, msg_width, msg_height), 3)
                text_color = BLACK
            
            # 显示消息文本
            font, small_font, battle_font, menu_font = get_fonts()
            text_font = FontManager.get_font(18) if line_count > 8 else FontManager.get_font(20)  # 行数多时用小字体
            
            # 计算文本起始位置
            text_start_y = msg_y + 20
            max_text_height = msg_height - 80  # 为提示文本留出空间
            
            for i, line in enumerate(lines):
                if line.strip():  # 只显示非空行
                    text_y = text_start_y + i * 22
                    if text_y + 22 > msg_y + max_text_height:  # 防止文本超出消息框
                        break
                    
                    # 处理过长的行，进行换行
                    if len(line) > 50:  # 如果行太长，截断显示
                        line = line[:47] + "..."
                    
                    text_surface = text_font.render(line, True, text_color)
                    # 左对齐显示，而不是居中
                    screen.blit(text_surface, (msg_x + 20, text_y))
            
            # 显示提示文本
            hint_text = small_font.render("按任意键继续...", True, GRAY)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, msg_y + msg_height - 30))
            screen.blit(hint_text, hint_rect)
            
        except Exception as e:
            print(f"绘制消息界面时出错: {e}")
            self.state = GameState.EXPLORING

    def draw_menu(self):
        try:
            # 检查是否在战斗中打开背包，决定背景颜色
            is_battle_menu = len(self.menu_stack) > 0 and self.menu_stack[-1] in [GameState.BATTLE, GameState.BOSS_BATTLE]
            
            if is_battle_menu and self.state == GameState.MENU_BACKPACK:
                # 战斗中的背包界面使用橙色背景
                overlay = SurfaceFactory.create_overlay((SCREEN_WIDTH, SCREEN_HEIGHT), ORANGE, 180)
                screen.blit(overlay, (0, 0))
                
                # 绘制菜单标题栏 - 橙色，40%透明度
                title_surface = SurfaceFactory.create_transparent_surface((SCREEN_WIDTH//2, 60), ORANGE, 102)
                screen.blit(title_surface, (SCREEN_WIDTH//4, 50))
                pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//4, 50, SCREEN_WIDTH//2, 60), 2)
            else:
                # 绘制半透明薄荷绿背景遮罩
                overlay = SurfaceFactory.create_overlay((SCREEN_WIDTH, SCREEN_HEIGHT), MINT_GREEN, 180)
                screen.blit(overlay, (0, 0))
                
                # 绘制菜单标题栏 - 薄荷绿色，40%透明度
                title_surface = SurfaceFactory.create_transparent_surface((SCREEN_WIDTH//2, 60), MINT_GREEN, 102)
                screen.blit(title_surface, (SCREEN_WIDTH//4, 50))
                pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//4, 50, SCREEN_WIDTH//2, 60), 2)
            
            # UT display removed from bag interface
            
            if self.state == GameState.MENU_MAIN:
                font, small_font, battle_font, menu_font = get_fonts()
                title = menu_font.render("主菜单", True, BLACK)  # 改为黑色文字
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))
                
                for button in self.menu_buttons:
                    button.draw(screen)
                    
            elif self.state == GameState.MENU_POKEMON:
                font, small_font, battle_font, menu_font = get_fonts()
                title = menu_font.render("顾问", True, BLACK)  # 改为黑色文字
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))
                
                # 高亮显示当前默认出战顾问
                for i, button in enumerate(self.menu_buttons[:-2]):
                    if i == self.player.default_pokemon_index:
                        pygame.draw.rect(screen, HIGHLIGHT, button.rect.inflate(6, 6), 3)
                    button.draw(screen)
                
                # 绘制最后两个按钮
                for button in self.menu_buttons[-2:]:
                    button.draw(screen)
                    
                # Ensure fonts are loaded
                font, small_font, battle_font, menu_font = get_fonts()
                info = small_font.render(f"队伍: {len(self.player.pokemon_team)}/6", True, WHITE)
                screen.blit(info, (SCREEN_WIDTH//4 + 20, 120))
                
            elif self.state == GameState.MENU_POKEMON_DETAIL:
                font, small_font, battle_font, menu_font = get_fonts()
                pokemon = self.player.pokemon_team[self.selected_pokemon_index]
                is_default = self.selected_pokemon_index == self.player.default_pokemon_index
                title_text = f"{pokemon.name} 的详细信息"
                if is_default:
                    title_text += " [当前默认出战]"
                    
                title = menu_font.render(title_text, True, BLACK)
                
                # 动态调整标题框大小以适应文字长度
                title_width = title.get_width() + 40  # 添加20像素的左右边距
                title_height = 60
                title_x = SCREEN_WIDTH//2 - title_width//2
                title_surface = pygame.Surface((title_width, title_height), pygame.SRCALPHA)
                title_surface.fill((152, 251, 152, 102))  # 薄荷绿色，40%透明度
                screen.blit(title_surface, (title_x, 50))
                pygame.draw.rect(screen, BLACK, (title_x, 50, title_width, title_height), 2)
                
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))
                
                pkm_img = self.images.pokemon.get(pokemon.name, 
                                                ImageLoader.create_default_image((200, 200), 
                                                                                f"pokemon_{pokemon.name}"))
                screen.blit(pkm_img, (20, 150))
                
                # 显示优点和缺点
                advantages = ", ".join(pokemon.advantages)
                disadvantages = ", ".join(pokemon.disadvantages)
                
                info_texts = [
                    f"名称: {pokemon.name}",
                    f"等级: Lv.{pokemon.level}",
                    f"优点属性: {advantages}",
                    f"缺点属性: {disadvantages}",
                    f"HP: {pokemon.hp}/{pokemon.max_hp}",
                    f"SP: {pokemon.sp}/{pokemon.max_sp}",
                    f"攻击: {pokemon.attack}",
                    f"防御: {pokemon.defense}",
                    f"经验值: {pokemon.exp}/{pokemon.exp_to_next_level}",
                    "技能:"
                ]
                
                for move in pokemon.moves:
                    info_texts.append("")  # 技能之间的空行
                    # 统一从UNIFIED_SKILLS_DATABASE获取技能信息
                    skill_data = UNIFIED_SKILLS_DATABASE.get(move["name"], {})
                    
                    # 技能名称（加粗显示）
                    info_texts.append(f"◆ 技能名称: {move['name']}")
                    
                    # 技能属性
                    move_type = skill_data.get("type", "")
                    if move_type:
                        info_texts.append(f"  技能属性: {move_type}")
                    
                    # 技能类型（如果有category）
                    if "category" in skill_data:
                        category_name = {
                            SkillCategory.DIRECT_DAMAGE: "直接伤害",
                            SkillCategory.CONTINUOUS_DAMAGE: "连续伤害", 
                            SkillCategory.DIRECT_HEAL: "直接治疗",
                            SkillCategory.CONTINUOUS_HEAL: "连续治疗",
                            SkillCategory.HEAL: "治疗",
                            SkillCategory.SELF_BUFF: "自身强化",
                            SkillCategory.ENEMY_DEBUFF: "敌方削弱",
                            SkillCategory.TEAM_BUFF: "团队强化",
                            SkillCategory.SPECIAL_ATTACK: "必杀技",
                            SkillCategory.DIRECT_ATTACK: "直接攻击",
                            SkillCategory.DOT: "持续伤害",
                            SkillCategory.HOT: "持续治疗",
                            SkillCategory.TEAM_HEAL: "团队治疗",
                            SkillCategory.MULTI_HIT: "多段攻击",
                            SkillCategory.REVIVE: "复活技能",
                            SkillCategory.MIXED_BUFF_DEBUFF: "混合效果",
                            SkillCategory.HOT_DOT: "持续效果",
                            SkillCategory.ULTIMATE: "终极技能",
                            SkillCategory.SPECIAL: "特殊技能",
                            SkillCategory.STAT_CHANGE: "属性改变"
                        }.get(skill_data.get("category"), "未知")
                        info_texts.append(f"  技能类型: {category_name}")
                    
                    # 威力（如果有）
                    power = skill_data.get("power", 0)
                    if power > 0:
                        info_texts.append(f"  威力: {power}")
                    
                    # SP消耗
                    sp_cost = skill_data.get("sp_cost", 0)
                    if sp_cost > 0:
                        info_texts.append(f"  SP消耗: {sp_cost}")
                    else:
                        info_texts.append(f"  SP消耗: 无（使用后获得SP）")
                    
                    # 技能效果详细信息
                    effects = skill_data.get('effects', {})
                    if effects:
                        info_texts.append(f"  技能效果:")
                        if 'damage_range' in effects:
                            min_dmg, max_dmg = effects['damage_range']
                            info_texts.append(f"    伤害: {min_dmg}-{max_dmg}点")
                        if 'base_damage' in effects:
                            info_texts.append(f"    基础伤害: {effects['base_damage']}点")
                        if 'heal_percentage' in effects:
                            heal_percent = int(effects['heal_percentage'] * 100)
                            info_texts.append(f"    治疗: 恢复{heal_percent}%生命")
                        if 'turns' in effects:
                            info_texts.append(f"    持续回合: {effects['turns']}回合")
                        if 'attack_multiplier' in effects:
                            mult = int(effects['attack_multiplier'] * 100)
                            info_texts.append(f"    攻击力变化: {mult}%")
                        if 'defense_multiplier' in effects:
                            mult = int(effects['defense_multiplier'] * 100)
                            info_texts.append(f"    防御力变化: {mult}%")
                        if 'target_attack_multiplier' in effects:
                            mult = int(effects['target_attack_multiplier'] * 100)
                            info_texts.append(f"    敌方攻击力变化: {mult}%")
                        if 'execute_threshold' in effects:
                            threshold = int(effects['execute_threshold'] * 100)
                            info_texts.append(f"    斩杀阈值: HP<{threshold}%时直接击败")
                    
                    # 技能描述
                    desc = skill_data.get("description", "")
                    if desc:
                        info_texts.append(f"  技能描述:")
                        max_chars_per_line = 24
                        wrapped_lines = textwrap.wrap(desc, width=max_chars_per_line)
                        for line in wrapped_lines:
                            info_texts.append(f"    {line}")
                
                if info_texts and info_texts[-1] == "":
                    info_texts.pop()
    
                info_texts.append("")
                    
                if pokemon.name in PokemonConfig.evolution_data:
                    evo_info = PokemonConfig.evolution_data[pokemon.name]
                    if evo_info["item"]:
                        info_texts.append(f"进化: {evo_info['evolution']} (使用{evo_info['item']})")
                    else:
                        info_texts.append(f"进化: {evo_info['evolution']} (Lv.{evo_info['level']})")
                else:
                    info_texts.append("进化: 已达到最终形态")
                
                
                # 创建滚动内容区域
                content_area_y = 150
                content_area_height = SCREEN_HEIGHT - 200  # 留出空间给按钮
                content_area_x = 240  # 内容区域起始x位置（顾问图片右侧）
                content_width = SCREEN_WIDTH - content_area_x - 20  # 内容宽度，留出20像素给滚动条
                
                # 计算总内容高度
                total_content_height = 0
                temp_y = 0
                # 确保字体已初始化
                font, small_font, battle_font, menu_font = get_fonts()
                for text in info_texts:
                    temp_y = self._calculate_text_height(text, small_font, content_width, temp_y)
                total_content_height = temp_y
                
                # 创建可滚动的内容表面
                if total_content_height > content_area_height:
                    # 内容超出可见区域，需要滚动
                    max_scroll = max(0, total_content_height - content_area_height)
                    self.detail_scroll_offset = max(0, min(self.detail_scroll_offset, max_scroll))
                    
                    # 创建内容表面
                    content_surface = pygame.Surface((content_width, total_content_height), pygame.SRCALPHA)
                    content_y = 0
                    for text in info_texts:
                        content_y = draw_multiline_text(
                            content_surface, 
                            text, 
                            small_font, 
                            BLACK, 
                            0, 
                            content_y, 
                            content_width
                        )
                    
                    # 绘制滚动后的内容
                    visible_rect = pygame.Rect(0, self.detail_scroll_offset, content_width, content_area_height)
                    screen.blit(content_surface, (content_area_x, content_area_y), visible_rect)
                    
                    # 绘制滚动条指示器 - 移动到最右侧
                    if max_scroll > 0:
                        scrollbar_height = max(20, int(content_area_height * content_area_height / total_content_height))
                        scrollbar_y = content_area_y + int(self.detail_scroll_offset * (content_area_height - scrollbar_height) / max_scroll)
                        scrollbar_x = SCREEN_WIDTH - 15  # 滚动条位置移到最右侧
                        pygame.draw.rect(screen, (128, 128, 128), (scrollbar_x, scrollbar_y, 10, scrollbar_height))
                        pygame.draw.rect(screen, BLACK, (scrollbar_x, content_area_y, 10, content_area_height), 1)
                else:
                    # 内容未超出，正常显示
                    current_y = content_area_y
                    for text in info_texts:
                        current_y = draw_multiline_text(
                            screen, 
                            text, 
                            small_font, 
                            BLACK, 
                            content_area_x, 
                            current_y, 
                            content_width
                        )
                
                for button in self.menu_buttons:
                    button.draw(screen)
                    
            elif self.state == GameState.MENU_BACKPACK:
                self.draw_backpack_menu()
                    
            elif self.state == GameState.MENU_ITEM_USE:
                font, small_font, battle_font, menu_font = get_fonts()
                item = self.player.backpack[self.selected_item_index]
                title = menu_font.render(f"使用 {item.name}", True, WHITE)
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))
                
                desc = small_font.render(item.description, True, WHITE)
                screen.blit(desc, (SCREEN_WIDTH//2 - desc.get_width()//2, 130))
                
                for button in self.menu_buttons:
                    button.draw(screen)
                    
            elif self.state == GameState.CAPTURE_SELECT:
                # 绘制捕捉选择界面
                screen.fill((60, 60, 60))  # 深灰色背景
                
                font, small_font, battle_font, menu_font = get_fonts()
                title = menu_font.render("选择精灵球", True, WHITE)
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))
                
                # 显示可用精灵球信息
                info_y = 150
                if self.player.pokeballs > 0:
                    pokeball_info = small_font.render(f"普通精灵球: {self.player.pokeballs}个", True, WHITE)
                    screen.blit(pokeball_info, (SCREEN_WIDTH//2 - pokeball_info.get_width()//2, info_y))
                    info_y += 30
                
                if self.player.master_balls > 0:
                    masterball_info = small_font.render(f"大师球: {self.player.master_balls}个", True, WHITE)
                    screen.blit(masterball_info, (SCREEN_WIDTH//2 - masterball_info.get_width()//2, info_y))
                    info_y += 30
                
                # 捕捉概率显示已移除
                
                # 绘制按钮
                for button in self.menu_buttons:
                    button.draw(screen)
            
            elif self.state == GameState.MENU_TARGET_SELECTION:
                # 目标选择界面或技能忘记对话框
                font, small_font, battle_font, menu_font = get_fonts()
                
                # 检查是否是技能忘记对话框
                if hasattr(self, 'skill_forget_dialog') and self.skill_forget_dialog and self.skill_forget_dialog['active']:
                    title = menu_font.render("workload不够用了，让我忘记一件事情", True, BLACK)
                    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))
                    
                    # 显示要学习的技能信息
                    dialog = self.skill_forget_dialog
                    skill_text = small_font.render(f"要学习的技能: {dialog['new_skill']}", True, WHITE)
                    screen.blit(skill_text, (SCREEN_WIDTH//2 - skill_text.get_width()//2, 100))
                    
                    info_text = small_font.render(f"选择 {dialog['target'].name} 要忘记的技能:", True, WHITE)
                    screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, 120))
                else:
                    title = menu_font.render("选择目标", True, BLACK)
                    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))
                    
                    # 显示物品信息
                    if hasattr(self, 'pending_item_use') and self.pending_item_use:
                        item = self.pending_item_use["item"]
                        item_text = small_font.render(f"使用物品: {item.name}", True, WHITE)
                        screen.blit(item_text, (SCREEN_WIDTH//2 - item_text.get_width()//2, 100))
                        
                        desc = small_font.render(item.description, True, WHITE)
                        screen.blit(desc, (SCREEN_WIDTH//2 - desc.get_width()//2, 120))
                
                # 绘制按钮
                for button in self.menu_buttons:
                    button.draw(screen)
                    
        except Exception as e:
            print(f"绘制菜单时出错: {e}")

    def handle_input(self, event):
        if event.type == QUIT:
            self._request_exit = True
            return
            
        if event.type == KEYDOWN:
            prev_x, prev_y = self.player.x, self.player.y
            # 消息状态处理 - 按任意键继续
            if self.state == GameState.MESSAGE:
                # 检查消息来源，决定返回到哪个状态
                if hasattr(self, 'battle_result') and self.battle_result and any(keyword in self.battle_result for keyword in ["HP恢复", "寄养", "领取", "训练中心"]):
                    self.state = GameState.TRAINING_CENTER  # 训练中心消息返回训练中心
                else:
                    self.state = GameState.EXPLORING  # 其他消息返回探索状态
                return
            
            # 通用ESC键处理
            if event.key == K_ESCAPE:
                if self.state in [GameState.BATTLE, GameState.BOSS_BATTLE, 
                                 GameState.BATTLE_MOVE_SELECT, GameState.BATTLE_SWITCH_POKEMON]:
                    self.go_back()
                elif self.state in [GameState.MENU_MAIN, GameState.MENU_POKEMON,
                                   GameState.MENU_POKEMON_DETAIL, GameState.MENU_BACKPACK,
                                   GameState.MENU_ITEM_USE]:
                    if self.menu_stack:
                        self.go_back()
                    else:
                        self.state = GameState.EXPLORING
                        self.menu_buttons = []
            
            # 顾问详细信息页面的滚动控制
            elif self.state == GameState.MENU_POKEMON_DETAIL:
                if event.key == K_UP or event.key == K_w:
                    if self.detail_scroll_offset > 0:
                        self.detail_scroll_offset -= 30
                elif event.key == K_DOWN or event.key == K_s:
                    self.detail_scroll_offset += 30
                elif event.key == K_PAGEUP:
                    self.detail_scroll_offset -= 150  # 快速滚动
                elif event.key == K_PAGEDOWN:
                    self.detail_scroll_offset += 150  # 快速滚动
            # 探索状态下的方向键控制
            if self.state == GameState.EXPLORING:
                prev_x, prev_y = self.player.x, self.player.y
                
                if event.key == K_UP:
                    self.player.x = max(0, self.player.x - 1)
                elif event.key == K_DOWN:
                    self.player.x = min(self.map.size - 1, self.player.x + 1)
                elif event.key == K_LEFT:
                    self.player.y = max(0, self.player.y - 1)
                elif event.key == K_RIGHT:
                    self.player.y = min(self.map.size - 1, self.player.y + 1)
                elif event.key == K_m:
                    self.open_main_menu()
                
                # 移动后检查是否触发地块事件
                if (self.player.x != prev_x or self.player.y != prev_y):
                    self.player.decrease_ut(1)
                    # 减少PTO通知剩余步数
                    if self.player.battle_prevention_steps > 0:
                        self.player.battle_prevention_steps -= 1
                        if self.player.battle_prevention_steps == 0:
                            self.notification_system.add_notification("PTO通知效果结束！", "warning")
                    # 获取当前地块类型
                    current_tile = self.map.get_tile_type(self.player.x, self.player.y)
                    if current_tile is not None:
                        # 触发地块事件
                        self.handle_tile_event(current_tile)
            
            elif self.state == GameState.SHOP:
                all_items = self.shop.get_all_items()
                if event.key == K_UP:
                    self.shop_selected_item = max(0, self.shop_selected_item - 1)
                    self.shop_selected_quantity = 1  # 重置购买数量
                elif event.key == K_DOWN:
                    self.shop_selected_item = min(len(all_items) - 1, self.shop_selected_item + 1)
                    self.shop_selected_quantity = 1  # 重置购买数量
                elif event.key == K_LEFT:
                    self.shop_selected_quantity = max(1, self.shop_selected_quantity - 1)
                elif event.key == K_RIGHT:
                    if all_items and self.shop_selected_item < len(all_items):
                        max_quantity = all_items[self.shop_selected_item]["stock"]
                        self.shop_selected_quantity = min(max_quantity, self.shop_selected_quantity + 1)
                elif event.key == K_RETURN or event.key == K_SPACE:  # 回车或空格购买
                    result = self.shop.buy_item(self.player, self.shop_selected_item, self.shop_selected_quantity)
                    self.battle_messages = [result]
                    self.shop_selected_quantity = 1  # 重置购买数量
                elif event.key == K_ESCAPE:  # ESC退出商店
                    self.state = GameState.EXPLORING
            
            elif self.state == GameState.MENU_BACKPACK:
                if hasattr(self, 'backpack_popup_state') and self.backpack_popup_state:
                    # 在弹窗状态下，ESC键关闭弹窗
                    if event.key == K_ESCAPE:
                        self.backpack_popup_state = False
                elif self.player.backpack:
                    # 上下键选择物品
                    if event.key == K_UP:
                        self.selected_item_index = max(0, self.selected_item_index - 1)
                        # 确保选中的物品在可见范围内
                        if self.selected_item_index < self.backpack_scroll_offset:
                            self.backpack_scroll_offset = self.selected_item_index
                    elif event.key == K_DOWN:
                        self.selected_item_index = min(len(self.player.backpack) - 1, self.selected_item_index + 1)
                        # 确保选中的物品在可见范围内
                        visible_area_height = SCREEN_HEIGHT - 140
                        max_visible_items = visible_area_height // 60
                        if self.selected_item_index >= self.backpack_scroll_offset + max_visible_items:
                            self.backpack_scroll_offset = self.selected_item_index - max_visible_items + 1
                    elif event.key == K_RETURN:
                        # 回车键使用物品
                        self.backpack_popup_state = True
            
            elif self.state == GameState.TRAINING_CENTER:
                if event.key == K_ESCAPE:  # ESC退出训练中心
                    self.state = GameState.EXPLORING
        
        # 鼠标事件处理
        if event.type == MOUSEMOTION:
            # 处理技能滚动条拖拽
            if (self.state == GameState.BATTLE_MOVE_SELECT and self.skill_scrollbar_dragging 
                and self.skill_scrollbar_area):
                # 计算拖拽距离
                drag_distance = event.pos[1] - self.skill_drag_start_y
                
                # 计算新的滚动偏移
                player_pkm = self.player.get_active_pokemon()
                if player_pkm and hasattr(player_pkm, 'moves') and player_pkm.moves:
                    total_skills = len(player_pkm.moves)
                    max_scroll = max(0, total_skills - self.max_visible_skills)
                    
                    if max_scroll > 0:
                        scrollbar_height = self.skill_scrollbar_area.height
                        slider_height = max(20, int(scrollbar_height * self.max_visible_skills / total_skills))
                        drag_range = scrollbar_height - slider_height
                        
                        if drag_range > 0:
                            # 将拖拽距离转换为滚动偏移
                            drag_ratio = drag_distance / drag_range
                            new_offset = self.skill_drag_start_offset + int(drag_ratio * max_scroll)
                            new_offset = max(0, min(new_offset, max_scroll))
                            
                            if new_offset != self.skill_scroll_offset:
                                self.skill_scroll_offset = new_offset
                                self.create_move_buttons()  # 重新创建按钮
            
            # 按钮hover效果
            elif self.state in [GameState.BATTLE, GameState.BOSS_BATTLE]:
                for button in self.battle_buttons:
                    button.check_hover(event.pos)
            elif self.state in [GameState.BATTLE_MOVE_SELECT, GameState.BATTLE_SWITCH_POKEMON]:
                # 重置悬浮技能信息
                self.hovered_skill_info = None
                
                for button in self.move_buttons:
                    button.check_hover(event.pos)
                    
                    # 如果是技能按钮且正在悬浮，获取技能信息
                    if (button.active and button.action and button.action.startswith("move_") and 
                        self.state == GameState.BATTLE_MOVE_SELECT):
                        try:
                            move_index = int(button.action.split("_")[1])
                            player_pkm = self.player.get_active_pokemon()
                            if player_pkm and 0 <= move_index < len(player_pkm.moves):
                                move = player_pkm.moves[move_index]
                                
                                # 从UNIFIED_SKILLS_DATABASE获取所有技能信息
                                skill_data = UNIFIED_SKILLS_DATABASE.get(move["name"], {})
                                
                                # 构建技能信息，从UNIFIED_SKILLS_DATABASE获取数据
                                skill_info = {
                                    "name": move["name"],
                                    "type": skill_data.get("type", ""),
                                    "power": skill_data.get("power", 0),
                                    "sp_cost": skill_data.get("sp_cost", 0),
                                    "description": skill_data.get("description", ""),
                                    "quote": skill_data.get("quote", "")
                                }
                                
                                self.hovered_skill_info = skill_info
                        except (ValueError, IndexError):
                            pass
            elif self.state in [GameState.MENU_MAIN, GameState.MENU_POKEMON,
                               GameState.MENU_POKEMON_DETAIL, GameState.MENU_BACKPACK,
                               GameState.MENU_ITEM_USE, GameState.MENU_TARGET_SELECTION]:
                for button in self.menu_buttons:
                    button.check_hover(event.pos)
            elif self.state == GameState.EXPLORING:
                # 检查菜单按钮hover
                menu_button = Button(10, 10, 100, 40, "菜单", "menu")
                menu_button.check_hover(event.pos)
        
        # 处理滚动条的鼠标按钮释放事件
        if event.type == MOUSEBUTTONUP:
            if event.button == 1:  # 左键释放
                # 停止拖拽滚动条
                if self.skill_scrollbar_dragging:
                    self.skill_scrollbar_dragging = False
        
        # 处理鼠标滚轮事件 - 支持新旧两种方式
        if event.type == MOUSEWHEEL:
            # 新版pygame的滚轮事件处理
            if event.y > 0:  # 滚轮向上
                if self.state == GameState.BATTLE_MOVE_SELECT and self.skill_scrollbar_area:
                    if self.skill_scroll_offset > 0:
                        old_offset = self.skill_scroll_offset
                        self.skill_scroll_offset -= 1
                        if old_offset != self.skill_scroll_offset:
                            self.create_move_buttons()  # 重新创建按钮
                elif self.state == GameState.MENU_POKEMON_DETAIL:
                    if self.detail_scroll_offset > 0:
                        self.detail_scroll_offset -= 30
                elif self.state == GameState.MENU_BACKPACK:
                    if self.backpack_scroll_offset > 0:
                        self.backpack_scroll_offset -= 1
            elif event.y < 0:  # 滚轮向下
                if self.state == GameState.BATTLE_MOVE_SELECT and self.skill_scrollbar_area:
                    # 计算最大滚动偏移
                    player_pkm = self.player.get_active_pokemon()
                    if player_pkm and hasattr(player_pkm, 'moves') and player_pkm.moves:
                        total_skills = len(player_pkm.moves)
                        max_scroll = max(0, total_skills - self.max_visible_skills)
                        if self.skill_scroll_offset < max_scroll:
                            old_offset = self.skill_scroll_offset
                            self.skill_scroll_offset += 1
                            if old_offset != self.skill_scroll_offset:
                                self.create_move_buttons()  # 重新创建按钮
                elif self.state == GameState.MENU_POKEMON_DETAIL:
                    self.detail_scroll_offset += 30
                elif self.state == GameState.MENU_BACKPACK:
                    visible_area_height = SCREEN_HEIGHT - 140
                    max_visible_items = visible_area_height // 60
                    max_scroll = max(0, len(self.player.backpack) - max_visible_items)
                    if self.backpack_scroll_offset < max_scroll:
                        self.backpack_scroll_offset += 1

        if event.type == MOUSEBUTTONDOWN:
            # 兼容旧版pygame的滚轮事件处理
            if event.button == 4:  # 滚轮向上
                if self.state == GameState.BATTLE_MOVE_SELECT and self.skill_scrollbar_area:
                    if self.skill_scroll_offset > 0:
                        old_offset = self.skill_scroll_offset
                        self.skill_scroll_offset -= 1
                        if old_offset != self.skill_scroll_offset:
                            self.create_move_buttons()  # 重新创建按钮
                elif self.state == GameState.MENU_POKEMON_DETAIL:
                    if self.detail_scroll_offset > 0:
                        self.detail_scroll_offset -= 30
                elif self.state == GameState.MENU_BACKPACK:
                    if self.backpack_scroll_offset > 0:
                        self.backpack_scroll_offset -= 1
            elif event.button == 5:  # 滚轮向下
                if self.state == GameState.BATTLE_MOVE_SELECT and self.skill_scrollbar_area:
                    # 计算最大滚动偏移
                    player_pkm = self.player.get_active_pokemon()
                    if player_pkm and hasattr(player_pkm, 'moves') and player_pkm.moves:
                        total_skills = len(player_pkm.moves)
                        max_scroll = max(0, total_skills - self.max_visible_skills)
                        if self.skill_scroll_offset < max_scroll:
                            old_offset = self.skill_scroll_offset
                            self.skill_scroll_offset += 1
                            if old_offset != self.skill_scroll_offset:
                                self.create_move_buttons()  # 重新创建按钮
                elif self.state == GameState.MENU_POKEMON_DETAIL:
                    self.detail_scroll_offset += 30
                elif self.state == GameState.MENU_BACKPACK:
                    visible_area_height = SCREEN_HEIGHT - 140
                    max_visible_items = visible_area_height // 60
                    max_scroll = max(0, len(self.player.backpack) - max_visible_items)
                    if self.backpack_scroll_offset < max_scroll:
                        self.backpack_scroll_offset += 1
            elif event.button == 1:  # 左键点击
                if self.state == GameState.EXPLORING:
                    # 检查菜单按钮点击
                    menu_rect = pygame.Rect(10, 10, 100, 40)
                    if menu_rect.collidepoint(event.pos):
                        self.open_main_menu()
                
                elif self.state in [GameState.BATTLE, GameState.BOSS_BATTLE]:
                    for button in self.battle_buttons:
                        if button.check_click(event.pos) and button.action:
                            # 清除我方必杀技台词显示（任何按钮操作都会清除）
                            self.ally_line_display = False
                            self.ally_ultimate_line = None
                            
                            if button.action == "fight":
                                self.state = GameState.BATTLE_MOVE_SELECT
                                self.create_move_buttons()
                            elif button.action == "catch" and not self.is_boss_battle:
                                self.try_catch()
                            elif button.action == "bag":
                                self.open_backpack_menu()
                            elif button.action == "flee":
                                self.flee_battle()
                            elif button.action == "switch":
                                self.create_switch_buttons()
                
                elif self.state in [GameState.BATTLE_MOVE_SELECT, GameState.BATTLE_SWITCH_POKEMON]:
                    # 首先检查滚动条点击事件（仅在技能选择界面）
                    if self.state == GameState.BATTLE_MOVE_SELECT and self.skill_scrollbar_area:
                        if self.skill_scrollbar_area.collidepoint(event.pos):
                            # 检查是否点击在滑块上
                            if self.skill_slider_area and self.skill_slider_area.collidepoint(event.pos):
                                # 开始拖拽滑块
                                self.skill_scrollbar_dragging = True
                                self.skill_drag_start_y = event.pos[1]
                                self.skill_drag_start_offset = self.skill_scroll_offset
                            else:
                                # 点击滚动条其他位置，跳转到相应位置
                                player_pkm = self.player.get_active_pokemon()
                                if player_pkm and hasattr(player_pkm, 'moves') and player_pkm.moves:
                                    total_skills = len(player_pkm.moves)
                                    max_scroll = max(0, total_skills - self.max_visible_skills)
                                    
                                    if max_scroll > 0:
                                        click_y = event.pos[1] - self.skill_scrollbar_area.y  # 相对于滚动条顶部的位置
                                        scrollbar_height = self.skill_scrollbar_area.height
                                        
                                        # 计算滚动比例
                                        scroll_ratio = click_y / scrollbar_height
                                        new_offset = int(scroll_ratio * max_scroll)
                                        new_offset = max(0, min(new_offset, max_scroll))
                                        
                                        if new_offset != self.skill_scroll_offset:
                                            self.skill_scroll_offset = new_offset
                                            self.create_move_buttons()  # 重新创建按钮
                            return  # 滚动条处理了事件，不再处理按钮点击
                    
                    for button in self.move_buttons:
                        if button.check_click(event.pos) and button.action:
                            # 清除我方必杀技台词显示（任何按钮操作都会清除）
                            self.ally_line_display = False
                            self.ally_ultimate_line = None
                            
                            if button.action == "back":
                                self.go_back()
                            elif button.action.startswith("move_"):
                                move_idx = int(button.action.split("_")[1])
                                self.player_attack(move_idx)
                            elif button.action.startswith("switch_"):
                                pkm_idx = int(button.action.split("_")[1])
                                self.switch_pokemon(pkm_idx)
                
                elif self.state == GameState.CAPTURE_ANIMATION:
                    # Handle the back button in capture animation
                    back_btn_rect = pygame.Rect(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 50, 150, 40)
                    if back_btn_rect.collidepoint(event.pos):
                        self.go_back()
                
                elif self.state == GameState.MENU_BACKPACK:
                    # 背包界面专门的鼠标处理
                    if hasattr(self, 'backpack_popup_state') and self.backpack_popup_state:
                        # 弹窗状态下的点击处理
                        if hasattr(self, 'popup_buttons'):
                            for action, rect in self.popup_buttons.items():
                                if rect.collidepoint(event.pos):
                                    if action == "use":
                                        # 执行物品使用
                                        result = self.use_item_directly(self.selected_item_index)
                                        self.battle_messages = [result]
                                        self.backpack_popup_state = False
                                    elif action == "cancel":
                                        self.backpack_popup_state = False
                    else:
                        # 正常界面状态下的点击处理
                        if hasattr(self, 'backpack_buttons'):
                            for action, rect in self.backpack_buttons.items():
                                if rect.collidepoint(event.pos):
                                    if action == "use":
                                        self.backpack_popup_state = True
                                    elif action == "back":
                                        self.go_back()
                        
                        # 点击物品列表选择物品
                        if hasattr(self, 'backpack_list_area') and self.backpack_list_area.collidepoint(event.pos):
                            display_item_index = (event.pos[1] - 110) // 60  # 在可见区域内的索引
                            actual_item_index = display_item_index + self.backpack_scroll_offset  # 实际物品索引
                            if 0 <= actual_item_index < len(self.player.backpack):
                                self.selected_item_index = actual_item_index
                        
                        # 点击滚动条处理
                        if hasattr(self, 'backpack_scrollbar_area') and self.backpack_scrollbar_area:
                            if self.backpack_scrollbar_area.collidepoint(event.pos):
                                # 计算点击位置对应的滚动偏移
                                visible_area_height = SCREEN_HEIGHT - 140
                                max_visible_items = visible_area_height // 60
                                total_items = len(self.player.backpack)
                                max_scroll = max(0, total_items - max_visible_items)
                                
                                if max_scroll > 0:
                                    click_y = event.pos[1] - 110  # 相对于滚动条顶部的位置
                                    scrollbar_height = visible_area_height - 20
                                    
                                    # 将点击位置转换为滚动偏移
                                    scroll_ratio = click_y / scrollbar_height
                                    self.backpack_scroll_offset = int(scroll_ratio * max_scroll)
                                    self.backpack_scroll_offset = max(0, min(self.backpack_scroll_offset, max_scroll))
                
                elif self.state in [GameState.MENU_MAIN, GameState.MENU_POKEMON,
                                   GameState.MENU_POKEMON_DETAIL, GameState.MENU_ITEM_USE]:
                    for button in self.menu_buttons:
                        if button.check_click(event.pos) and button.action:
                            if button.action == "menu":
                                self.open_main_menu()
                            elif button.action == "back":
                                self.go_back()
                            elif button.action == "pokemon":
                                self.open_pokemon_menu()
                            elif button.action == "backpack":
                                self.open_backpack_menu()
                            elif button.action == "save":
                                msg = self.save_game()
                                self.battle_messages = [msg]
                            elif button.action == "load":
                                msg = self.load_game()
                                self.battle_messages = [msg]
                            elif button.action == "exit":
                                self._request_exit = True
                            elif button.action.startswith("pokemon_"):
                                pkm_idx = int(button.action.split("_")[1])
                                self.show_pokemon_detail(pkm_idx)
                            elif button.action == "set_default":
                                self.player.set_default_pokemon(self.selected_pokemon_index)
                                self.battle_messages = [f"{self.player.pokemon_team[self.selected_pokemon_index].name}已设为默认出战顾问"]
                            elif button.action.startswith("make_default_"):
                                pkm_idx = int(button.action.split("_")[2])
                                self.player.set_default_pokemon(pkm_idx)
                                self.battle_messages = [f"{self.player.pokemon_team[pkm_idx].name}已设为默认出战顾问"]
                                self.go_back()
                            elif button.action.startswith("item_"):
                                item_idx = int(button.action.split("_")[1])
                                self.open_item_use_menu(item_idx)
                            elif button.action.startswith("use_on_"):
                                target_idx = int(button.action.split("_")[2])
                                result = self.use_item(self.selected_item_index, target_idx)
                                self.battle_messages = [result]
                                self.go_back()
                                self.go_back()
                            elif button.action.startswith("use_ut_"):
                                item_idx = int(button.action.split("_")[2])
                                result = self.player.use_ut_restorer(item_idx)
                                self.battle_messages = [result]
                            elif button.action.startswith("deposit_"):
                                pokemon_idx = int(button.action.split("_")[1])
                                result = self.training_center.deposit_pokemon(self.player, pokemon_idx)
                                self.battle_messages = [result]
                                self.state = GameState.TRAINING_CENTER
                            elif button.action.startswith("withdraw_"):
                                pokemon_id = button.action.split("_", 1)[1]  # 获取完整的pokemon_id
                                result = self.training_center.withdraw_pokemon(self.player, pokemon_id)
                                self.battle_messages = [result]
                                self.state = GameState.TRAINING_CENTER
                            elif button.action == "catch_normal":
                                self.process_battle_turn(action="catch", ball_type="normal")
                                # 不调用go_back()，让process_battle_turn处理状态转换
                            elif button.action == "catch_master":
                                self.process_battle_turn(action="catch", ball_type="master")
                                # 不调用go_back()，让process_battle_turn处理状态转换
                
                elif self.state == GameState.CAPTURE_SELECT:
                    for button in self.menu_buttons:
                        if button.check_click(event.pos) and button.action:
                            if button.action == "back":
                                self.go_back()
                            elif button.action == "catch_normal":
                                self.process_battle_turn(action="catch", ball_type="normal")
                                # 不调用go_back()，让process_battle_turn处理状态转换
                            elif button.action == "catch_master":
                                self.process_battle_turn(action="catch", ball_type="master")
                                # 不调用go_back()，让process_battle_turn处理状态转换
                
                elif self.state == GameState.MENU_TARGET_SELECTION:
                    for button in self.menu_buttons:
                        if button.check_click(event.pos) and button.action:
                            if button.action == "cancel":
                                # 检查是否是技能忘记对话框的取消
                                if hasattr(self, 'skill_forget_dialog') and self.skill_forget_dialog and self.skill_forget_dialog['active']:
                                    result = self.handle_skill_forget_selection("cancel")
                                    self.battle_messages = [result]
                                    self.skill_forget_dialog = None
                                    self.go_back()
                                else:
                                    # 取消使用物品
                                    if hasattr(self, 'pending_item_use'):
                                        self.pending_item_use = None
                                    self.go_back()
                            elif button.action.startswith("forget_"):
                                # 处理技能忘记选择
                                result = self.handle_skill_forget_selection(button.action)
                                self.battle_messages = [result]
                                self.notification_system.add_notification(result, "success")
                                self.go_back()
                            elif button.action.startswith("target_"):
                                target_idx = int(button.action.split("_")[1])
                                result = self.use_pending_item_on_target(target_idx)
                                self.battle_messages = [result]
                                self.go_back()
                            elif button.action == "catch_normal":
                                self.process_battle_turn(action="catch", ball_type="normal")
                                # 不调用go_back()，让process_battle_turn处理状态转换
                            elif button.action == "catch_master":
                                self.process_battle_turn(action="catch", ball_type="master")
                                # 不调用go_back()，让process_battle_turn处理状态转换
                
                elif self.state == GameState.SHOP:
                    # 检查是否在购买弹窗状态
                    if hasattr(self, 'shop_popup_state') and self.shop_popup_state:
                        # 处理购买弹窗中的点击
                        if hasattr(self, 'purchase_popup_buttons'):
                            if self.purchase_popup_buttons['minus'].collidepoint(event.pos):
                                if hasattr(self, 'purchase_quantity') and self.purchase_quantity > 1:
                                    self.purchase_quantity -= 1
                            elif self.purchase_popup_buttons['plus'].collidepoint(event.pos):
                                all_items = self.shop.get_all_items()
                                if self.shop_selected_item < len(all_items):
                                    selected_item = all_items[self.shop_selected_item]
                                    max_quantity = min(selected_item['stock'], self.player.money // selected_item['price'])
                                    if hasattr(self, 'purchase_quantity') and self.purchase_quantity < max_quantity:
                                        self.purchase_quantity += 1
                            elif self.purchase_popup_buttons['confirm'].collidepoint(event.pos):
                                # 执行购买
                                if hasattr(self, 'purchase_quantity'):
                                    result = self.shop.buy_item(self.player, self.shop_selected_item, self.purchase_quantity)
                                    self.battle_messages = [result]
                                self.shop_popup_state = None
                                self.purchase_quantity = 1
                            elif self.purchase_popup_buttons['cancel'].collidepoint(event.pos):
                                self.shop_popup_state = None
                                self.purchase_quantity = 1
                    else:
                        # 处理主界面点击
                        # 检查物品列表点击
                        if hasattr(self, 'shop_list_area') and self.shop_list_area.collidepoint(event.pos):
                            all_items = self.shop.get_all_items()
                            # 计算点击的物品索引
                            relative_y = event.pos[1] - 110  # 110是列表开始的y坐标
                            item_index = relative_y // 60  # 每个物品高度60像素
                            if 0 <= item_index < len(all_items):
                                self.shop_selected_item = item_index
                        
                        # 检查按钮点击
                        if hasattr(self, 'shop_buttons'):
                            if self.shop_buttons['buy'].collidepoint(event.pos):
                                all_items = self.shop.get_all_items()
                                if all_items and self.shop_selected_item < len(all_items):
                                    selected_item = all_items[self.shop_selected_item]
                                    if selected_item['stock'] > 0 and self.player.money >= selected_item['price']:
                                        self.shop_popup_state = True
                                        self.purchase_quantity = 1
                                    else:
                                        if selected_item['stock'] <= 0:
                                            self.battle_messages = ["该物品已售罄！"]
                                        else:
                                            self.battle_messages = ["金币不足！"]
                            elif self.shop_buttons['leave'].collidepoint(event.pos):
                                self.state = GameState.EXPLORING
                
                elif self.state == GameState.TRAINING_CENTER:
                    # 检查是否在弹窗状态
                    if hasattr(self, 'training_popup_state') and self.training_popup_state:
                        # 处理弹窗中的点击
                        if hasattr(self, 'popup_buttons'):
                            # 检查确认和取消按钮
                            if self.popup_buttons['confirm'].collidepoint(event.pos):
                                if self.training_popup_state == 'deposit':
                                    if hasattr(self, 'deposit_selected_index') and self.deposit_selected_index < len(self.player.pokemon_team):
                                        result = self.training_center.deposit_pokemon(self.player, self.deposit_selected_index)
                                        self.battle_result = result
                                        self.state = GameState.MESSAGE
                                elif self.training_popup_state == 'withdraw':
                                    deposited_info = self.training_center.get_deposited_pokemon_info()
                                    if deposited_info and hasattr(self, 'withdraw_selected_index') and self.withdraw_selected_index < len(deposited_info):
                                        pokemon_id = deposited_info[self.withdraw_selected_index]['id']
                                        result = self.training_center.withdraw_pokemon(self.player, pokemon_id)
                                        self.battle_result = result
                                        self.state = GameState.MESSAGE
                                self.training_popup_state = None
                            elif self.popup_buttons['cancel'].collidepoint(event.pos):
                                self.training_popup_state = None
                        
                        # 处理弹窗中的列表选择
                        if self.training_popup_state == 'deposit':
                            # 检查点击的顾问项
                            popup_x, popup_y = 100, 100
                            list_y = popup_y + 80
                            for i, pokemon in enumerate(self.player.pokemon_team):
                                item_rect = pygame.Rect(popup_x + 20, list_y + i * 60, SCREEN_WIDTH - 240, 50)
                                if item_rect.collidepoint(event.pos):
                                    self.deposit_selected_index = i
                        elif self.training_popup_state == 'withdraw':
                            # 检查点击的寄养顾问项
                            deposited_info = self.training_center.get_deposited_pokemon_info()
                            if deposited_info:
                                popup_x, popup_y = 100, 100
                                list_y = popup_y + 80
                                for i, info in enumerate(deposited_info):
                                    item_rect = pygame.Rect(popup_x + 20, list_y + i * 80, SCREEN_WIDTH - 240, 70)
                                    if item_rect.collidepoint(event.pos):
                                        self.withdraw_selected_index = i
                    else:
                        # 处理主界面按钮点击
                        if hasattr(self, 'training_buttons'):
                            if self.training_buttons['heal'].collidepoint(event.pos):
                                result = self.training_center.heal_all_pokemon(self.player)
                                self.battle_result = result  # 使用battle_result而不是battle_messages以显示详细文本框
                                self.state = GameState.MESSAGE
                            elif self.training_buttons['deposit'].collidepoint(event.pos):
                                if len(self.player.pokemon_team) > 1:
                                    self.training_popup_state = 'deposit'
                                    self.deposit_selected_index = 0
                                else:
                                    self.battle_result = "寄养失败！\n\n错误原因: 至少要保留一个顾问在队伍中\n\n建议:\n• 先捕捉更多顾问\n• 或者选择其他顾问进行寄养"
                                    self.state = GameState.MESSAGE
                            elif self.training_buttons['withdraw'].collidepoint(event.pos):
                                deposited_info = self.training_center.get_deposited_pokemon_info()
                                if deposited_info:
                                    self.training_popup_state = 'withdraw'
                                    self.withdraw_selected_index = 0
                                else:
                                    self.battle_result = "领取失败！\n\n错误原因: 没有寄养中的顾问\n\n建议:\n• 先寄养一些顾问\n• 等待一段时间后再来领取"
                                    self.state = GameState.MESSAGE
                            elif self.training_buttons['leave'].collidepoint(event.pos):
                                self.state = GameState.EXPLORING

    def open_deposit_menu(self):
        """打开寄养顾问菜单"""
        self.menu_buttons = []
        for i, pokemon in enumerate(self.player.pokemon_team):
            self.menu_buttons.append(
                Button(50, 100 + i * 50, 300, 40, f"{pokemon.name} (Lv.{pokemon.level})", f"deposit_{i}")
            )
        self.menu_buttons.append(Button(50, 100 + len(self.player.pokemon_team) * 50 + 20, 200, 40, "返回", "back"))
        self.state = GameState.MENU_MAIN  # 临时使用菜单状态
    
    def open_withdraw_menu(self):
        """打开领取顾问菜单"""
        deposited_info = self.training_center.get_deposited_pokemon_info()
        self.menu_buttons = []
        for i, info in enumerate(deposited_info):
            self.menu_buttons.append(
                Button(50, 100 + i * 50, 400, 40, 
                       f"{info['name']} (Lv.{info['level']}) - {info['potential_exp']}经验可领取", 
                       f"withdraw_{info['id']}")
            )
        self.menu_buttons.append(Button(50, 100 + len(deposited_info) * 50 + 20, 200, 40, "返回", "back"))
        self.state = GameState.MENU_MAIN  # 临时使用菜单状态

    def update(self):
        """更新游戏状态"""
        if self.state in [GameState.BATTLE_ANIMATION, GameState.CAPTURE_ANIMATION]:
            self.update_battle_animation()
        
        # 处理UT耗尽后的计数器
        if self.player.ut_empty_counter > 0:
            self.player.ut_empty_counter -= 1

    def draw_shop(self):
        """绘制商店，委托给UI渲染器"""
        return self.ui_renderer.draw_shop(screen)
    
    def draw_shop_old(self):
        """绘制商店界面"""
        # 绘制背景
        try:
            shop_bg = ImageLoader.load_image("images/ui/shop_bg.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(shop_bg, (0, 0))
        except (pygame.error, FileNotFoundError, OSError):
            # 如果背景图片不存在，使用默认背景
            screen.fill((139, 69, 19))  # 棕色背景
            # 添加淡紫色半透明背景框
            purple_surface = pygame.Surface((SCREEN_WIDTH-100, SCREEN_HEIGHT-100), pygame.SRCALPHA)
            purple_surface.fill((221, 160, 221, 128))  # 淡紫色半透明
            screen.blit(purple_surface, (50, 50))
            pygame.draw.rect(screen, (147, 112, 219), (50, 50, SCREEN_WIDTH-100, SCREEN_HEIGHT-100), 3)
        
        # 绘制标题
        title_font = FontManager.get_font(48)
        title_text = title_font.render("小卖部", True, BLACK)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
        
        # 绘制副标题
        subtitle_font = FontManager.get_font(16)
        subtitle_text = subtitle_font.render("不论是小卖部还是售货机，冰冷的可乐永远是你在客户现场最大的慰藉", True, BLACK)
        screen.blit(subtitle_text, (SCREEN_WIDTH//2 - subtitle_text.get_width()//2, 75))
        
        # 绘制玩家金钱信息
        money_font = FontManager.get_font(32)
        money_text = money_font.render(f"金币: {self.player.money}", True, BLACK)
        screen.blit(money_text, (SCREEN_WIDTH - money_text.get_width() - 20, 20))
        
        # 检查是否在显示购买弹窗
        if hasattr(self, 'shop_popup_state') and self.shop_popup_state:
            self.draw_purchase_popup()
            return
        
        # 计算布局区域
        left_width = int(SCREEN_WIDTH * 2 // 3)  # 左侧2/3宽度
        right_width = SCREEN_WIDTH - left_width - 60  # 右侧宽度
        right_x = left_width + 40
        
        # 绘制左侧物品列表 - 淡紫色半透明文字框
        list_surface = pygame.Surface((left_width - 40, SCREEN_HEIGHT - 140), pygame.SRCALPHA)
        list_surface.fill((221, 160, 221, 128))  # 淡紫色50%透明度
        screen.blit(list_surface, (20, 100))
        pygame.draw.rect(screen, BLACK, (20, 100, left_width - 40, SCREEN_HEIGHT - 140), 2)
        
        # 绘制物品列表
        all_items = self.shop.get_all_items()
        item_font = FontManager.get_font(20)
        y_offset = 110
        
        for i, item in enumerate(all_items):
            # 物品背景
            item_rect = pygame.Rect(30, y_offset + i * 60, left_width - 60, 50)
            if i == self.shop_selected_item:
                pygame.draw.rect(screen, (200, 230, 255, 180), item_rect)  # 选中高亮
            pygame.draw.rect(screen, BLACK, item_rect, 1)
            
            # 物品名称
            name_text = item_font.render(f"{item['name']}", True, BLACK)
            screen.blit(name_text, (item_rect.x + 5, item_rect.y + 2))
            
            # 持有数量、库存和价格
            player_count = self.player.inventory.get(item['name'], 0)
            info_text = FontManager.get_font(16).render(f"持有: {player_count} | 库存: {item['stock']} | 价格: {item['price']}金币", True, BLACK)
            screen.blit(info_text, (item_rect.x + 5, item_rect.y + 25))
        
        # 存储物品列表区域用于点击检测
        self.shop_list_area = pygame.Rect(30, 110, left_width - 60, len(all_items) * 60)
        
        # 绘制右侧详细信息区域 - 上部2/3
        detail_height = int((SCREEN_HEIGHT - 160) * 2 // 3)
        detail_surface = pygame.Surface((right_width, detail_height), pygame.SRCALPHA)
        detail_surface.fill((221, 160, 221, 128))  # 淡紫色50%透明度
        screen.blit(detail_surface, (right_x, 100))
        pygame.draw.rect(screen, BLACK, (right_x, 100, right_width, detail_height), 2)
        
        # 显示选中物品的详细信息
        if all_items and self.shop_selected_item < len(all_items):
            selected_item = all_items[self.shop_selected_item]
            detail_font = FontManager.get_font(18)
            detail_y = 120
            
            # 物品名称
            name_text = FontManager.get_font(24).render(selected_item['name'], True, BLACK)
            screen.blit(name_text, (right_x + 10, detail_y))
            detail_y += 40
            
            # 详细信息 - 使用自动换行
            desc_text = selected_item['description']
            detail_y = draw_multiline_text(
                screen, 
                desc_text, 
                detail_font, 
                BLACK, 
                right_x + 10, 
                detail_y, 
                right_width - 20  # 确保文字不超出边框
            )
            
            # 价格和库存信息
            detail_y += 20
            price_text = detail_font.render(f"价格: {selected_item['price']}金币", True, BLACK)
            screen.blit(price_text, (right_x + 10, detail_y))
            detail_y += 25
            
            stock_text = detail_font.render(f"库存: {selected_item['stock']}", True, BLACK)
            screen.blit(stock_text, (right_x + 10, detail_y))
            detail_y += 25
            
            player_count = self.player.inventory.get(selected_item['name'], 0)
            owned_text = detail_font.render(f"已持有: {player_count}", True, BLACK)
            screen.blit(owned_text, (right_x + 10, detail_y))
        
        # 绘制右侧下部按钮区域 - 下部1/3
        button_area_y = 100 + detail_height + 10
        button_area_height = SCREEN_HEIGHT - button_area_y - 40
        
        button_surface = pygame.Surface((right_width, button_area_height), pygame.SRCALPHA)
        button_surface.fill((221, 160, 221, 128))  # 淡紫色50%透明度
        screen.blit(button_surface, (right_x, button_area_y))
        pygame.draw.rect(screen, BLACK, (right_x, button_area_y, right_width, button_area_height), 2)
        
        # 购买和离开按钮
        button_width = right_width // 2 - 20
        button_height = 50
        buy_button_y = button_area_y + 20
        
        buy_rect = pygame.Rect(right_x + 10, buy_button_y, button_width, button_height)
        leave_rect = pygame.Rect(right_x + button_width + 30, buy_button_y, button_width, button_height)
        
        # 购买按钮
        pygame.draw.rect(screen, (144, 238, 144), buy_rect)
        pygame.draw.rect(screen, BLACK, buy_rect, 2)
        buy_font = FontManager.get_font(24)
        buy_text = buy_font.render("购买", True, BLACK)
        screen.blit(buy_text, (buy_rect.centerx - buy_text.get_width()//2, buy_rect.centery - buy_text.get_height()//2))
        
        # 离开按钮
        pygame.draw.rect(screen, (255, 182, 193), leave_rect)
        pygame.draw.rect(screen, BLACK, leave_rect, 2)
        leave_text = buy_font.render("离开", True, BLACK)
        screen.blit(leave_text, (leave_rect.centerx - leave_text.get_width()//2, leave_rect.centery - leave_text.get_height()//2))
        
        # 存储按钮区域用于点击检测
        self.shop_buttons = {
            'buy': buy_rect,
            'leave': leave_rect
        }
    
    def draw_backpack_menu(self):
        """绘制背包界面"""
        # 绘制背景
        screen.fill((60, 179, 113))  # 海绿色背景
        
        # 添加薄荷绿半透明背景框
        mint_surface = pygame.Surface((SCREEN_WIDTH-100, SCREEN_HEIGHT-100), pygame.SRCALPHA)
        mint_surface.fill((152, 251, 152, 150))  # 薄荷绿半透明
        screen.blit(mint_surface, (50, 50))
        pygame.draw.rect(screen, (32, 178, 170), (50, 50, SCREEN_WIDTH-100, SCREEN_HEIGHT-100), 3)
        
        # 绘制标题
        title_font = FontManager.get_font(48)
        title_text = title_font.render("背包", True, BLACK)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
        
        # 绘制副标题
        subtitle_font = FontManager.get_font(16)
        subtitle_text = subtitle_font.render(f"物品数量: {len(self.player.backpack)}", True, BLACK)
        screen.blit(subtitle_text, (SCREEN_WIDTH//2 - subtitle_text.get_width()//2, 75))
        
        # 检查是否在显示确认弹窗
        if hasattr(self, 'backpack_popup_state') and self.backpack_popup_state:
            self.draw_item_use_popup()
            return
        
        if not self.player.backpack:
            # 如果背包为空
            empty_font = FontManager.get_font(24)
            empty_text = empty_font.render("背包是空的", True, BLACK)
            screen.blit(empty_text, (SCREEN_WIDTH//2 - empty_text.get_width()//2, SCREEN_HEIGHT//2))
            
            # 返回按钮
            back_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 100, 200, 40)
            pygame.draw.rect(screen, MINT_GREEN, back_rect)
            pygame.draw.rect(screen, BLACK, back_rect, 2)
            back_text = FontManager.get_font(24).render("返回上级", True, BLACK)
            screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, back_rect.centery - back_text.get_height()//2))
            
            self.backpack_buttons = {'back': back_rect}
            return
        
        # 计算布局区域
        left_width = int(SCREEN_WIDTH * 2 // 3)  # 左侧2/3宽度
        right_width = SCREEN_WIDTH - left_width - 60  # 右侧宽度
        right_x = left_width + 40
        
        # 绘制左侧物品列表
        list_surface = pygame.Surface((left_width - 40, SCREEN_HEIGHT - 140), pygame.SRCALPHA)
        list_surface.fill((152, 251, 152, 150))  # 薄荷绿50%透明度
        screen.blit(list_surface, (20, 100))
        pygame.draw.rect(screen, BLACK, (20, 100, left_width - 40, SCREEN_HEIGHT - 140), 2)
        
        # 绘制物品列表（带滚动）
        item_font = FontManager.get_font(20)
        y_offset = 110
        item_height = 60
        
        # 计算可见区域
        visible_area_height = SCREEN_HEIGHT - 140
        max_visible_items = visible_area_height // item_height
        total_items = len(self.player.backpack)
        
        # 调整滚动偏移以确保不超出范围
        max_scroll = max(0, total_items - max_visible_items)
        self.backpack_scroll_offset = max(0, min(self.backpack_scroll_offset, max_scroll))
        
        # 计算可见物品范围
        visible_start = self.backpack_scroll_offset
        visible_end = min(visible_start + max_visible_items, total_items)
        
        # 绘制可见物品
        for i in range(visible_start, visible_end):
            item = self.player.backpack[i]
            display_index = i - visible_start  # 在可见区域内的索引
            
            # 物品背景
            item_rect = pygame.Rect(30, y_offset + display_index * item_height, left_width - 80, 50)  # 预留滚动条空间
            if i == self.selected_item_index:
                pygame.draw.rect(screen, (200, 255, 200, 180), item_rect)  # 选中高亮
            pygame.draw.rect(screen, BLACK, item_rect, 1)
            
            # 物品名称
            name_text = item_font.render(f"{item.name}", True, BLACK)
            screen.blit(name_text, (item_rect.x + 5, item_rect.y + 2))
            
            # 物品描述
            desc_text = FontManager.get_font(16).render(f"{item.description}", True, BLACK)
            screen.blit(desc_text, (item_rect.x + 5, item_rect.y + 25))
        
        # 存储物品列表区域用于点击检测（只包含可见区域）
        self.backpack_list_area = pygame.Rect(30, 110, left_width - 80, max_visible_items * item_height)
        
        # 绘制滚动条（如果需要）
        if total_items > max_visible_items:
            scrollbar_x = left_width - 35
            scrollbar_y = 110
            scrollbar_width = 15
            scrollbar_height = visible_area_height - 20
            
            # 滚动条背景
            pygame.draw.rect(screen, (200, 200, 200), (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
            pygame.draw.rect(screen, BLACK, (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height), 1)
            
            # 滚动条滑块
            slider_height = max(20, int(scrollbar_height * max_visible_items / total_items))
            slider_y = scrollbar_y + int(self.backpack_scroll_offset * (scrollbar_height - slider_height) / max_scroll) if max_scroll > 0 else scrollbar_y
            
            pygame.draw.rect(screen, (100, 100, 100), (scrollbar_x, slider_y, scrollbar_width, slider_height))
            pygame.draw.rect(screen, BLACK, (scrollbar_x, slider_y, scrollbar_width, slider_height), 1)
            
            # 存储滚动条区域用于点击检测
            self.backpack_scrollbar_area = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
            self.backpack_slider_area = pygame.Rect(scrollbar_x, slider_y, scrollbar_width, slider_height)
        else:
            self.backpack_scrollbar_area = None
            self.backpack_slider_area = None
        
        # 绘制右侧详细信息区域 - 上部2/3
        detail_height = int((SCREEN_HEIGHT - 160) * 2 // 3)
        detail_surface = pygame.Surface((right_width, detail_height), pygame.SRCALPHA)
        detail_surface.fill((152, 251, 152, 150))  # 薄荷绿50%透明度
        screen.blit(detail_surface, (right_x, 100))
        pygame.draw.rect(screen, BLACK, (right_x, 100, right_width, detail_height), 2)
        
        # 显示选中物品的详细信息和预测效果
        if self.player.backpack and self.selected_item_index < len(self.player.backpack):
            selected_item = self.player.backpack[self.selected_item_index]
            detail_font = FontManager.get_font(18)
            detail_y = 120
            
            # 物品名称
            name_text = FontManager.get_font(24).render(selected_item.name, True, BLACK)
            screen.blit(name_text, (right_x + 10, detail_y))
            detail_y += 40
            
            # 详细信息
            desc_text = selected_item.description
            detail_y = draw_multiline_text(
                screen, 
                desc_text, 
                detail_font, 
                BLACK, 
                right_x + 10, 
                detail_y, 
                right_width - 20
            )
            
            detail_y += 20
            
            # 预测使用效果
            effect_text = self.predict_item_effect(selected_item)
            effect_y = draw_multiline_text(
                screen,
                f"使用效果: {effect_text}",
                detail_font,
                BLACK,
                right_x + 10,
                detail_y,
                right_width - 20
            )
        
        # 绘制右侧下部按钮区域 - 下部1/3
        button_area_y = 100 + detail_height + 10
        button_area_height = SCREEN_HEIGHT - button_area_y - 40
        
        button_surface = pygame.Surface((right_width, button_area_height), pygame.SRCALPHA)
        button_surface.fill((152, 251, 152, 150))  # 薄荷绿50%透明度
        screen.blit(button_surface, (right_x, button_area_y))
        pygame.draw.rect(screen, BLACK, (right_x, button_area_y, right_width, button_area_height), 2)
        
        # 使用和返回按钮
        button_width = right_width // 2 - 20
        button_height = 50
        use_button_y = button_area_y + 20
        
        use_rect = pygame.Rect(right_x + 10, use_button_y, button_width, button_height)
        back_rect = pygame.Rect(right_x + button_width + 30, use_button_y, button_width, button_height)
        
        # 使用按钮
        pygame.draw.rect(screen, (144, 238, 144), use_rect)
        pygame.draw.rect(screen, BLACK, use_rect, 2)
        use_font = FontManager.get_font(24)
        use_text = use_font.render("使用", True, BLACK)
        screen.blit(use_text, (use_rect.centerx - use_text.get_width()//2, use_rect.centery - use_text.get_height()//2))
        
        # 返回按钮
        pygame.draw.rect(screen, (255, 182, 193), back_rect)
        pygame.draw.rect(screen, BLACK, back_rect, 2)
        back_text = use_font.render("返回", True, BLACK)
        screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, back_rect.centery - back_text.get_height()//2))
        
        # 存储按钮区域用于点击检测
        self.backpack_buttons = {
            'use': use_rect,
            'back': back_rect
        }
    
    def predict_item_effect(self, item):
        """预测物品使用效果"""
        if item.item_type == "heal":
            # 查找当前HP最低的顾问作为预测目标
            target = None
            for pokemon in self.player.pokemon_team:
                if pokemon.hp < pokemon.max_hp:
                    if target is None or pokemon.hp < target.hp:
                        target = pokemon
            
            if target:
                heal_amount = min(50, target.max_hp - target.hp)  # 假设恢复50HP
                if heal_amount > 0:
                    return f"{target.name}的HP从{target.hp}恢复到{target.hp + heal_amount}"
                else:
                    return f"{target.name}的HP已满,无需恢复"
            else:
                return "所有顾问HP已满"
                
        elif item.item_type == "evolution":
            # 检查是否有顾问可以进化
            can_evolve = False
            evolution_info = []
            
            for pokemon in self.player.pokemon_team:
                if hasattr(pokemon, 'can_evolve_with_item') and pokemon.can_evolve_with_item(item.name):
                    can_evolve = True
                    break
                elif pokemon.name in PokemonConfig.evolution_data:
                    evolution_data = PokemonConfig.evolution_data[pokemon.name]
                    if evolution_data["item"] == item.name:
                        required_level = evolution_data["level"]
                        if pokemon.level < required_level:
                            evolution_info.append(f"{pokemon.name}需要{required_level}级(当前{pokemon.level}级)")
            
            if can_evolve:
                return "可以让某个顾问进化"
            elif evolution_info:
                return f"进化条件未满足：{', '.join(evolution_info)}"
            else:
                return "队伍中没有可以用此道具进化的顾问"
                
        elif item.item_type == "ut_restore":
            if self.player.ut < self.player.max_ut:
                restore_amount = min(30, self.player.max_ut - self.player.ut)  # 假设恢复30UT
                return f"UT从{self.player.ut}恢复到{self.player.ut + restore_amount}"
            else:
                return "UT已满,无需恢复"
                
        elif item.item_type == "pokeball":
            return "只能在战斗中使用"
            
        elif item.item_type == "skill_blind_box":
            return "随机生成一个必杀技学习书"
            
        elif item.item_type == "skill_book":
            skill_name = item.effect
            return f"让选择的顾问学习必杀技：{skill_name}"
            
        elif item.item_type == "battle_prevent":
            return "100步内不会触发战斗"
            
        elif item.item_type == "sp_restore":
            return "SP恢复至100点"
            
        elif item.item_type == "permanent_boost":
            stat_name = "攻击力" if item.effect["stat"] == "attack" else "防御力"
            value = item.effect["value"]
            return f"永久增加{value}点{stat_name}"
            
        elif item.item_type == "upgrade_gem":
            return f"提升等级{item.effect}级"
            
        elif item.item_type == "attribute_enhancer":
            return "随机增加一个额外属性"
            
        elif item.item_type == "sp_enhancer":
            return "增加SP上限到120"
            
        elif item.item_type == "special":
            # 特殊物品可能需要特定的使用方式
            return "这是特殊物品,可能需要在特定情况下使用"
        else:
            return "似乎没有任何作用"
    
    def draw_item_use_popup(self):
        """绘制物品使用确认弹窗"""
        popup_width = 400
        popup_height = 300
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2
        
        # 获取选中的物品
        selected_item = self.player.backpack[self.selected_item_index]
        
        # 使用PopupRenderer绘制基础弹窗
        PopupRenderer.draw_base_popup(screen, popup_x, popup_y, popup_width, popup_height, f"使用 {selected_item.name}", WHITE, 230)
        
        # 效果预测
        effect_font = FontManager.get_font(18)
        effect_text = self.predict_item_effect(selected_item)
        
        # 使用多行文本绘制效果
        effect_y = popup_y + 80
        draw_multiline_text(
            screen,
            effect_text,
            effect_font,
            BLACK,
            popup_x + 20,
            effect_y,
            popup_width - 40
        )
        
        # 如果没有效果，只显示取消按钮
        if effect_text == "似乎没有任何作用":
            cancel_rect = pygame.Rect(popup_x + popup_width//2 - 75, popup_y + popup_height - 80, 150, 40)
            pygame.draw.rect(screen, (255, 182, 193), cancel_rect)
            pygame.draw.rect(screen, BLACK, cancel_rect, 2)
            cancel_text = FontManager.get_font(20).render("确定", True, BLACK)
            screen.blit(cancel_text, (cancel_rect.centerx - cancel_text.get_width()//2, cancel_rect.centery - cancel_text.get_height()//2))
            
            self.popup_buttons = {'cancel': cancel_rect}
        else:
            # 使用和取消按钮
            use_rect = pygame.Rect(popup_x + 50, popup_y + popup_height - 80, 120, 40)
            cancel_rect = pygame.Rect(popup_x + popup_width - 170, popup_y + popup_height - 80, 120, 40)
            
            # 使用按钮
            pygame.draw.rect(screen, (144, 238, 144), use_rect)
            pygame.draw.rect(screen, BLACK, use_rect, 2)
            use_text = FontManager.get_font(20).render("使用", True, BLACK)
            screen.blit(use_text, (use_rect.centerx - use_text.get_width()//2, use_rect.centery - use_text.get_height()//2))
            
            # 取消按钮
            pygame.draw.rect(screen, (255, 182, 193), cancel_rect)
            pygame.draw.rect(screen, BLACK, cancel_rect, 2)
            cancel_text = FontManager.get_font(20).render("取消", True, BLACK)
            screen.blit(cancel_text, (cancel_rect.centerx - cancel_text.get_width()//2, cancel_rect.centery - cancel_text.get_height()//2))
            
            self.popup_buttons = {'use': use_rect, 'cancel': cancel_rect}
        
        # 显示操作结果消息
        if self.battle_messages:
            message_y = SCREEN_HEIGHT - 80
            message_surface = pygame.Surface((SCREEN_WIDTH - 40, 60), pygame.SRCALPHA)
            message_surface.fill((255, 255, 255, 180))  # 半透明白色
            screen.blit(message_surface, (20, message_y))
            pygame.draw.rect(screen, BLACK, (20, message_y, SCREEN_WIDTH - 40, 60), 2)
            
            message_font = FontManager.get_font(20)
            for i, message in enumerate(self.battle_messages[-2:]):  # 显示最近2条消息
                message_text = message_font.render(message, True, BLACK)
                screen.blit(message_text, (30, message_y + 10 + i * 25))

    def draw_purchase_popup(self):
        """绘制购买数量弹窗"""
        # 绘制半透明背景遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        popup_width = 400
        popup_height = 300
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2
        
        # 绘制弹窗背景
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        popup_surface.fill((255, 255, 255, 230))
        screen.blit(popup_surface, (popup_x, popup_y))
        pygame.draw.rect(screen, BLACK, (popup_x, popup_y, popup_width, popup_height), 3)
        
        # 获取选中的物品
        all_items = self.shop.get_all_items()
        if self.shop_selected_item < len(all_items):
            selected_item = all_items[self.shop_selected_item]
            
            # 标题
            title_font = FontManager.get_font(28)
            title_text = title_font.render("购买数量", True, BLACK)
            screen.blit(title_text, (popup_x + popup_width//2 - title_text.get_width()//2, popup_y + 20))
            
            # 物品名称
            name_font = FontManager.get_font(24)
            name_text = name_font.render(f"物品: {selected_item['name']}", True, BLACK)
            screen.blit(name_text, (popup_x + 20, popup_y + 70))
            
            # 单价
            price_text = name_font.render(f"单价: {selected_item['price']}金币", True, BLACK)
            screen.blit(price_text, (popup_x + 20, popup_y + 100))
            
            # 库存限制
            max_quantity = min(selected_item['stock'], self.player.money // selected_item['price'])
            stock_text = FontManager.get_font(20).render(f"最大可购买: {max_quantity}", True, BLACK)
            screen.blit(stock_text, (popup_x + 20, popup_y + 130))
            
            # 初始化购买数量
            if not hasattr(self, 'purchase_quantity'):
                self.purchase_quantity = min(1, max_quantity)
            
            # 确保购买数量不超过限制
            self.purchase_quantity = min(self.purchase_quantity, max_quantity)
            if self.purchase_quantity < 1:
                self.purchase_quantity = 1
            
            # 购买数量显示和控制
            quantity_y = popup_y + 160
            quantity_font = FontManager.get_font(24)
            
            # 数量减少按钮
            minus_rect = pygame.Rect(popup_x + 50, quantity_y, 40, 40)
            pygame.draw.rect(screen, (255, 182, 193), minus_rect)
            pygame.draw.rect(screen, BLACK, minus_rect, 2)
            minus_text = quantity_font.render("-", True, BLACK)
            screen.blit(minus_text, (minus_rect.centerx - minus_text.get_width()//2, minus_rect.centery - minus_text.get_height()//2))
            
            # 数量显示
            quantity_text = quantity_font.render(f"{self.purchase_quantity}", True, BLACK)
            screen.blit(quantity_text, (popup_x + popup_width//2 - quantity_text.get_width()//2, quantity_y + 8))
            
            # 数量增加按钮
            plus_rect = pygame.Rect(popup_x + popup_width - 90, quantity_y, 40, 40)
            pygame.draw.rect(screen, (144, 238, 144), plus_rect)
            pygame.draw.rect(screen, BLACK, plus_rect, 2)
            plus_text = quantity_font.render("+", True, BLACK)
            screen.blit(plus_text, (plus_rect.centerx - plus_text.get_width()//2, plus_rect.centery - plus_text.get_height()//2))
            
            # 总价显示
            total_price = selected_item['price'] * self.purchase_quantity
            total_text = quantity_font.render(f"总价: {total_price}金币", True, BLACK)
            screen.blit(total_text, (popup_x + 20, popup_y + 210))
            
            # 确认和取消按钮
            confirm_rect = pygame.Rect(popup_x + 80, popup_y + 240, 100, 40)
            cancel_rect = pygame.Rect(popup_x + 220, popup_y + 240, 100, 40)
            
            pygame.draw.rect(screen, (144, 238, 144), confirm_rect)
            pygame.draw.rect(screen, BLACK, confirm_rect, 2)
            pygame.draw.rect(screen, (255, 182, 193), cancel_rect)
            pygame.draw.rect(screen, BLACK, cancel_rect, 2)
            
            button_font = FontManager.get_font(24)
            confirm_text = button_font.render("确认", True, BLACK)
            cancel_text = button_font.render("取消", True, BLACK)
            
            screen.blit(confirm_text, (confirm_rect.centerx - confirm_text.get_width()//2, confirm_rect.centery - confirm_text.get_height()//2))
            screen.blit(cancel_text, (cancel_rect.centerx - cancel_text.get_width()//2, cancel_rect.centery - cancel_text.get_height()//2))
            
            # 存储按钮区域
            self.purchase_popup_buttons = {
                'minus': minus_rect,
                'plus': plus_rect,
                'confirm': confirm_rect,
                'cancel': cancel_rect
            }


    def draw_training_center(self):
        """绘制训练中心界面"""
        # 绘制背景
        try:
            tc_bg = ImageLoader.load_image("images/ui/training_center_bg.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(tc_bg, (0, 0))
        except (pygame.error, FileNotFoundError, OSError):
            # 如果背景图片不存在，使用默认背景
            screen.fill((100, 149, 237))  # 蓝色背景
            # 添加薄荷绿半透明背景框
            mint_surface = pygame.Surface((SCREEN_WIDTH-100, SCREEN_HEIGHT-100), pygame.SRCALPHA)
            mint_surface.fill((152, 251, 152, 150))  # 薄荷绿半透明
            screen.blit(mint_surface, (50, 50))
            pygame.draw.rect(screen, (32, 178, 170), (50, 50, SCREEN_WIDTH-100, SCREEN_HEIGHT-100), 3)
        
        # 绘制标题
        title_font = FontManager.get_font(48)
        title_text = title_font.render("Retro", True, BLACK)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
        
        # 绘制副标题
        subtitle_font = FontManager.get_font(16)
        subtitle_text = subtitle_font.render("他们永远会在半夜接你的电话——听你倾诉或八卦", True, BLACK)
        screen.blit(subtitle_text, (SCREEN_WIDTH//2 - subtitle_text.get_width()//2, 75))
        
        # 绘制玩家金钱信息
        money_font = FontManager.get_font(32)
        money_text = money_font.render(f"金币: {self.player.money}", True, BLACK)
        screen.blit(money_text, (SCREEN_WIDTH - money_text.get_width() - 20, 20))
        
        # 检查是否在显示弹窗
        if hasattr(self, 'training_popup_state') and self.training_popup_state:
            self.draw_training_popup()
            return
        
        # 绘制功能区域 - 现在改为交互按钮
        y_offset = 100
        button_width = (SCREEN_WIDTH - 200) // 4
        button_height = 80
        button_y = y_offset
        
        # 创建半透明按钮背景
        button_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        button_surface.fill((255, 255, 255, 128))  # 半透明白色
        
        # HP恢复按钮
        heal_rect = pygame.Rect(50, button_y, button_width, button_height)
        screen.blit(button_surface, heal_rect)
        pygame.draw.rect(screen, BLACK, heal_rect, 2)
        
        heal_font = FontManager.get_font(24)
        heal_title = heal_font.render("恢复HP", True, BLACK)
        heal_desc = FontManager.get_font(16).render("免费服务", True, BLACK)
        screen.blit(heal_title, (heal_rect.centerx - heal_title.get_width()//2, heal_rect.y + 15))
        screen.blit(heal_desc, (heal_rect.centerx - heal_desc.get_width()//2, heal_rect.y + 45))
        
        # 寄养顾问按钮
        deposit_rect = pygame.Rect(70 + button_width, button_y, button_width, button_height)
        screen.blit(button_surface, deposit_rect)
        pygame.draw.rect(screen, BLACK, deposit_rect, 2)
        
        deposit_title = heal_font.render("寄养顾问", True, BLACK)
        deposit_desc = FontManager.get_font(16).render("提升等级", True, BLACK)
        screen.blit(deposit_title, (deposit_rect.centerx - deposit_title.get_width()//2, deposit_rect.y + 15))
        screen.blit(deposit_desc, (deposit_rect.centerx - deposit_desc.get_width()//2, deposit_rect.y + 45))
        
        # 领取顾问按钮
        withdraw_rect = pygame.Rect(90 + button_width * 2, button_y, button_width, button_height)
        screen.blit(button_surface, withdraw_rect)
        pygame.draw.rect(screen, BLACK, withdraw_rect, 2)
        
        withdraw_title = heal_font.render("领取顾问", True, BLACK)
        withdraw_desc = FontManager.get_font(16).render("取回寄养", True, BLACK)
        screen.blit(withdraw_title, (withdraw_rect.centerx - withdraw_title.get_width()//2, withdraw_rect.y + 15))
        screen.blit(withdraw_desc, (withdraw_rect.centerx - withdraw_desc.get_width()//2, withdraw_rect.y + 45))
        
        # 离开按钮
        leave_rect = pygame.Rect(110 + button_width * 3, button_y, button_width, button_height)
        screen.blit(button_surface, leave_rect)
        pygame.draw.rect(screen, BLACK, leave_rect, 2)
        
        leave_title = heal_font.render("离开", True, BLACK)
        screen.blit(leave_title, (leave_rect.centerx - leave_title.get_width()//2, leave_rect.y + 30))
        
        # 存储按钮区域以供点击检测
        self.training_buttons = {
            'heal': heal_rect,
            'deposit': deposit_rect,
            'withdraw': withdraw_rect,
            'leave': leave_rect
        }
        
        # 绘制信息显示区域 - 半透明文字框
        info_y = y_offset + 120
        info_surface = pygame.Surface((SCREEN_WIDTH - 100, 300), pygame.SRCALPHA)
        info_surface.fill((255, 255, 255, 128))  # 半透明白色
        screen.blit(info_surface, (50, info_y))
        pygame.draw.rect(screen, BLACK, (50, info_y, SCREEN_WIDTH - 100, 300), 2)
        
        # 显示当前队伍顾问
        team_y = info_y + 20
        team_font = FontManager.get_font(20)
        team_text = team_font.render("当前队伍:", True, BLACK)
        screen.blit(team_text, (60, team_y))
        
        for i, pokemon in enumerate(self.player.pokemon_team):
            pokemon_text = team_font.render(f"{i+1}. {pokemon.name} (Lv.{pokemon.level})", True, BLACK)
            screen.blit(pokemon_text, (70, team_y + 25 + i * 25))
        
        # 寄养中的顾问信息
        deposited_info = self.training_center.get_deposited_pokemon_info()
        if deposited_info:
            deposited_y = info_y + 180
            deposited_text = team_font.render("寄养中的顾问:", True, BLACK)
            screen.blit(deposited_text, (60, deposited_y))
            
            for i, info in enumerate(deposited_info):
                info_text = FontManager.get_font(18).render(
                    f"{info['name']} (Lv.{info['level']}) - 寄养{info['days_deposited']}天, 可获得{info['potential_exp']}经验", 
                    True, BLACK
                )
                screen.blit(info_text, (70, deposited_y + 25 + i * 25))
        

    def draw_training_popup(self):
        """绘制训练中心弹窗"""
        # 绘制半透明背景遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        popup_width = SCREEN_WIDTH - 200
        popup_height = SCREEN_HEIGHT - 200
        popup_x = 100
        popup_y = 100
        
        # 绘制弹窗背景
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        popup_surface.fill((255, 255, 255, 220))
        screen.blit(popup_surface, (popup_x, popup_y))
        pygame.draw.rect(screen, BLACK, (popup_x, popup_y, popup_width, popup_height), 3)
        
        if self.training_popup_state == 'deposit':
            self.draw_deposit_popup(popup_x, popup_y, popup_width, popup_height)
        elif self.training_popup_state == 'withdraw':
            self.draw_withdraw_popup(popup_x, popup_y, popup_width, popup_height)
    
    def draw_deposit_popup(self, x, y, width, height):
        """绘制寄养顾问弹窗"""
        title_font = FontManager.get_font(32)
        title_text = title_font.render("选择要寄养的顾问", True, BLACK)
        screen.blit(title_text, (x + width//2 - title_text.get_width()//2, y + 20))
        
        # 显示队伍中的顾问
        item_font = FontManager.get_font(24)
        list_y = y + 80
        
        if not hasattr(self, 'deposit_selected_index'):
            self.deposit_selected_index = 0
        
        for i, pokemon in enumerate(self.player.pokemon_team):
            item_rect = pygame.Rect(x + 20, list_y + i * 60, width - 40, 50)
            
            # 选中高亮
            if i == self.deposit_selected_index:
                pygame.draw.rect(screen, (200, 230, 255), item_rect)
            else:
                pygame.draw.rect(screen, (240, 240, 240), item_rect)
            pygame.draw.rect(screen, BLACK, item_rect, 2)
            
            pokemon_text = item_font.render(f"{pokemon.name} (Lv.{pokemon.level}) - HP: {pokemon.hp}/{pokemon.max_hp}", True, BLACK)
            screen.blit(pokemon_text, (item_rect.x + 10, item_rect.y + 15))
        
        # 绘制确认和取消按钮
        button_y = y + height - 80
        confirm_rect = pygame.Rect(x + width//2 - 120, button_y, 100, 40)
        cancel_rect = pygame.Rect(x + width//2 + 20, button_y, 100, 40)
        
        pygame.draw.rect(screen, (144, 238, 144), confirm_rect)
        pygame.draw.rect(screen, BLACK, confirm_rect, 2)
        pygame.draw.rect(screen, (255, 182, 193), cancel_rect)
        pygame.draw.rect(screen, BLACK, cancel_rect, 2)
        
        button_font = FontManager.get_font(24)
        confirm_text = button_font.render("确定", True, BLACK)
        cancel_text = button_font.render("取消", True, BLACK)
        
        screen.blit(confirm_text, (confirm_rect.centerx - confirm_text.get_width()//2, confirm_rect.centery - confirm_text.get_height()//2))
        screen.blit(cancel_text, (cancel_rect.centerx - cancel_text.get_width()//2, cancel_rect.centery - cancel_text.get_height()//2))
        
        # 存储按钮区域
        self.popup_buttons = {
            'confirm': confirm_rect,
            'cancel': cancel_rect
        }
    
    def draw_withdraw_popup(self, x, y, width, height):
        """绘制领取顾问弹窗"""
        title_font = FontManager.get_font(32)
        title_text = title_font.render("选择要领取的顾问", True, BLACK)
        screen.blit(title_text, (x + width//2 - title_text.get_width()//2, y + 20))
        
        # 获取寄养中的顾问信息
        deposited_info = self.training_center.get_deposited_pokemon_info()
        
        if not deposited_info:
            no_pokemon_text = FontManager.get_font(24).render("没有寄养中的顾问", True, BLACK)
            screen.blit(no_pokemon_text, (x + width//2 - no_pokemon_text.get_width()//2, y + height//2))
        else:
            item_font = FontManager.get_font(24)
            list_y = y + 80
            
            if not hasattr(self, 'withdraw_selected_index'):
                self.withdraw_selected_index = 0
            
            for i, info in enumerate(deposited_info):
                item_rect = pygame.Rect(x + 20, list_y + i * 80, width - 40, 70)
                
                # 选中高亮
                if i == self.withdraw_selected_index:
                    pygame.draw.rect(screen, (200, 230, 255), item_rect)
                else:
                    pygame.draw.rect(screen, (240, 240, 240), item_rect)
                pygame.draw.rect(screen, BLACK, item_rect, 2)
                
                # 显示顾问信息
                name_text = item_font.render(f"{info['name']} (Lv.{info['level']})", True, BLACK)
                days_text = FontManager.get_font(20).render(f"寄养天数: {info['days_deposited']}天", True, BLACK)
                exp_text = FontManager.get_font(20).render(f"可获得经验: {info['potential_exp']}", True, BLACK)
                
                screen.blit(name_text, (item_rect.x + 10, item_rect.y + 5))
                screen.blit(days_text, (item_rect.x + 10, item_rect.y + 30))
                screen.blit(exp_text, (item_rect.x + 10, item_rect.y + 50))
        
        # 绘制确认和取消按钮
        button_y = y + height - 80
        confirm_rect = pygame.Rect(x + width//2 - 120, button_y, 100, 40)
        cancel_rect = pygame.Rect(x + width//2 + 20, button_y, 100, 40)
        
        pygame.draw.rect(screen, (144, 238, 144), confirm_rect)
        pygame.draw.rect(screen, BLACK, confirm_rect, 2)
        pygame.draw.rect(screen, (255, 182, 193), cancel_rect)
        pygame.draw.rect(screen, BLACK, cancel_rect, 2)
        
        button_font = FontManager.get_font(24)
        confirm_text = button_font.render("确定", True, BLACK)
        cancel_text = button_font.render("取消", True, BLACK)
        
        screen.blit(confirm_text, (confirm_rect.centerx - confirm_text.get_width()//2, confirm_rect.centery - confirm_text.get_height()//2))
        screen.blit(cancel_text, (cancel_rect.centerx - cancel_text.get_width()//2, cancel_rect.centery - cancel_text.get_height()//2))
        
        # 存储按钮区域
        self.popup_buttons = {
            'confirm': confirm_rect,
            'cancel': cancel_rect
        }


    def run(self):
        """优化的游戏主循环"""
        running = True
        
        # 预分配事件列表以减少内存分配
        events = []
        
        while running:
            # 检查是否需要完全重绘
            state_changed = self._last_state != self.state
            if state_changed:
                self._need_full_redraw = True
                self._last_state = self.state
            
            # 只在需要时清屏
            if self._need_full_redraw:
                screen.fill(WHITE)
            
            # 批量处理事件
            events.clear()
            events.extend(pygame.event.get())
            
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break
                self.handle_input(event)
            
            # 检查退出请求
            if self._request_exit:
                running = False
            
            if not running:
                break
            
            # 检查玩家移动（用于脏矩形）
            if self.state == GameState.EXPLORING:
                self._check_player_movement()
            
            self.update()
            
            # 更新定时宝箱系统
            if hasattr(self, 'map') and self.map:
                if self.map.update_timed_chests():
                    self.notification_system.add_notification("发现新的宝箱出现了！", "info")
            
            # 更新通知系统
            self.notification_system.update()
            
            # 优化的渲染系统
            self._optimized_render()
            
            # 绘制通知系统（在所有其他元素之上）
            self.notification_system.draw(screen)
            
            pygame.display.flip()
            clock.tick(FPS)

# ==================== 程序入口 ====================

# 启动游戏
if __name__ == "__main__":
    try:
        # 初始化pygame
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("顾问游戏")
        clock = pygame.time.Clock()
        
        print("游戏启动中...")
        game = PokemonGame()
        print("游戏初始化完成，开始运行...")
        game.run()
        print("游戏循环结束，正在清理资源...")
        
    except KeyboardInterrupt:
        print("用户中断程序")
    except Exception as e:
        print(f"游戏运行时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("正在安全退出游戏...")
        try:
            pygame.quit()
            print("Pygame已安全关闭")
        except:
            print("Pygame关闭时出现问题，但程序仍会退出")
        
        try:
            sys.exit(0)
        except SystemExit:
            pass  # 正常的退出异常，忽略
