# UI工具类 - 统一管理常用的UI渲染功能
import pygame

class UIUtils:
    """UI工具类，提供常用的UI渲染功能，减少代码重复"""
    
    # 常用颜色常量
    COLORS = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'gray': (128, 128, 128),
        'light_gray': (200, 200, 200),
        'dark_gray': (80, 80, 80),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'mint_green': (152, 251, 152),
        'light_blue': (173, 216, 230),
        'selection_highlight': (200, 230, 255),
        'item_background': (240, 240, 240)
    }
    
    @staticmethod
    def create_surface_with_alpha(size, color=(255, 255, 255, 128)):
        """
        创建带透明度的Surface
        
        Args:
            size: (width, height) 尺寸元组
            color: RGBA颜色元组
        
        Returns:
            pygame.Surface: 带透明度的Surface对象
        """
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill(color)
        return surface
    
    @staticmethod
    def draw_rounded_rect(surface, color, rect, radius=5, border_color=None, border_width=0):
        """
        绘制圆角矩形
        
        Args:
            surface: 目标surface
            color: 填充颜色
            rect: pygame.Rect对象或(x, y, width, height)元组
            radius: 圆角半径
            border_color: 边框颜色
            border_width: 边框宽度
        """
        if isinstance(rect, tuple):
            rect = pygame.Rect(rect)
        
        # 简化的圆角矩形实现
        # 绘制主体矩形
        pygame.draw.rect(surface, color, rect)
        
        # 如果需要边框
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, rect, border_width)
    
    @staticmethod
    def draw_text_with_background(surface, text, font, text_color, bg_color, x, y, padding=5):
        """
        绘制带背景的文本
        
        Args:
            surface: 目标surface
            text: 文本内容
            font: 字体对象
            text_color: 文字颜色
            bg_color: 背景颜色
            x, y: 文本位置
            padding: 背景内边距
        
        Returns:
            pygame.Rect: 文本区域矩形
        """
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect()
        
        # 绘制背景
        bg_rect = pygame.Rect(
            x - padding, 
            y - padding, 
            text_rect.width + 2 * padding, 
            text_rect.height + 2 * padding
        )
        
        if len(bg_color) == 4:  # RGBA
            bg_surface = UIUtils.create_surface_with_alpha(
                (bg_rect.width, bg_rect.height), 
                bg_color
            )
            surface.blit(bg_surface, bg_rect.topleft)
        else:  # RGB
            pygame.draw.rect(surface, bg_color, bg_rect)
        
        # 绘制文本
        surface.blit(text_surface, (x, y))
        
        return pygame.Rect(x, y, text_rect.width, text_rect.height)
    
    @staticmethod
    def draw_progress_bar(surface, x, y, width, height, progress, bg_color=None, fill_color=None, border_color=None):
        """
        绘制进度条
        
        Args:
            surface: 目标surface
            x, y: 进度条位置
            width, height: 进度条尺寸
            progress: 进度值 (0.0 - 1.0)
            bg_color: 背景颜色
            fill_color: 填充颜色
            border_color: 边框颜色
        """
        bg_color = bg_color or UIUtils.COLORS['light_gray']
        fill_color = fill_color or UIUtils.COLORS['green']
        border_color = border_color or UIUtils.COLORS['black']
        
        # 限制进度值范围
        progress = max(0.0, min(1.0, progress))
        
        # 绘制背景
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, bg_color, bg_rect)
        
        # 绘制填充
        if progress > 0:
            fill_width = int(width * progress)
            fill_rect = pygame.Rect(x, y, fill_width, height)
            pygame.draw.rect(surface, fill_color, fill_rect)
        
        # 绘制边框
        pygame.draw.rect(surface, border_color, bg_rect, 1)
    
    @staticmethod
    def draw_list_item(surface, x, y, width, height, text, font, selected=False, index=None):
        """
        绘制列表项
        
        Args:
            surface: 目标surface
            x, y: 列表项位置
            width, height: 列表项尺寸
            text: 显示文本
            font: 字体对象
            selected: 是否选中
            index: 项目索引（可选）
        
        Returns:
            pygame.Rect: 列表项矩形区域
        """
        item_rect = pygame.Rect(x, y, width, height)
        
        # 绘制背景
        if selected:
            bg_color = UIUtils.COLORS['selection_highlight']
        else:
            bg_color = UIUtils.COLORS['item_background']
        
        pygame.draw.rect(surface, bg_color, item_rect)
        pygame.draw.rect(surface, UIUtils.COLORS['black'], item_rect, 1)
        
        # 绘制文本
        text_color = UIUtils.COLORS['black']
        text_surface = font.render(text, True, text_color)
        text_x = x + 10
        text_y = y + (height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))
        
        return item_rect
    
    @staticmethod
    def draw_button(surface, x, y, width, height, text, font, 
                   bg_color=None, text_color=None, border_color=None, 
                   hover=False, pressed=False):
        """
        绘制按钮
        
        Args:
            surface: 目标surface
            x, y: 按钮位置
            width, height: 按钮尺寸
            text: 按钮文本
            font: 字体对象
            bg_color: 背景颜色
            text_color: 文字颜色
            border_color: 边框颜色
            hover: 是否悬停状态
            pressed: 是否按下状态
        
        Returns:
            pygame.Rect: 按钮矩形区域
        """
        button_rect = pygame.Rect(x, y, width, height)
        
        # 确定颜色
        if bg_color is None:
            if pressed:
                bg_color = UIUtils.COLORS['dark_gray']
            elif hover:
                bg_color = UIUtils.COLORS['light_blue']
            else:
                bg_color = UIUtils.COLORS['light_gray']
        
        text_color = text_color or UIUtils.COLORS['black']
        border_color = border_color or UIUtils.COLORS['black']
        
        # 绘制按钮背景
        pygame.draw.rect(surface, bg_color, button_rect)
        pygame.draw.rect(surface, border_color, button_rect, 2)
        
        # 绘制按钮文本
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        surface.blit(text_surface, text_rect)
        
        return button_rect
    
    @staticmethod
    def draw_tooltip(surface, text, font, x, y, max_width=300):
        """
        绘制工具提示
        
        Args:
            surface: 目标surface
            text: 提示文本
            font: 字体对象
            x, y: 提示位置
            max_width: 最大宽度
        
        Returns:
            pygame.Rect: 提示框矩形区域
        """
        # 简单的文本换行
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width - 20:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 计算提示框尺寸
        line_height = font.get_height()
        tooltip_width = max(font.size(line)[0] for line in lines) + 20
        tooltip_height = len(lines) * line_height + 20
        
        # 调整位置避免超出屏幕
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width
        if y + tooltip_height > screen_height:
            y = screen_height - tooltip_height
        
        # 绘制提示框背景
        tooltip_rect = pygame.Rect(x, y, tooltip_width, tooltip_height)
        tooltip_surface = UIUtils.create_surface_with_alpha(
            (tooltip_width, tooltip_height), 
            (255, 255, 255, 230)
        )
        surface.blit(tooltip_surface, (x, y))
        pygame.draw.rect(surface, UIUtils.COLORS['black'], tooltip_rect, 1)
        
        # 绘制文本
        text_y = y + 10
        for line in lines:
            text_surface = font.render(line, True, UIUtils.COLORS['black'])
            surface.blit(text_surface, (x + 10, text_y))
            text_y += line_height
        
        return tooltip_rect
    
    @staticmethod
    def create_gradient_surface(width, height, start_color, end_color, vertical=True):
        """
        创建渐变色Surface
        
        Args:
            width, height: 尺寸
            start_color: 起始颜色
            end_color: 结束颜色
            vertical: 是否垂直渐变
        
        Returns:
            pygame.Surface: 渐变Surface
        """
        surface = pygame.Surface((width, height))
        
        if vertical:
            for y in range(height):
                ratio = y / height
                color = [
                    int(start_color[i] + (end_color[i] - start_color[i]) * ratio)
                    for i in range(3)
                ]
                pygame.draw.line(surface, color, (0, y), (width, y))
        else:
            for x in range(width):
                ratio = x / width
                color = [
                    int(start_color[i] + (end_color[i] - start_color[i]) * ratio)
                    for i in range(3)
                ]
                pygame.draw.line(surface, color, (x, 0), (x, height))
        
        return surface