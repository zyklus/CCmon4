# 统一弹窗渲染器 - 用于替换重复的弹窗渲染代码
import pygame

class PopupRenderer:
    """统一的弹窗渲染器，减少重复的弹窗绘制代码"""
    
    # 预定义的弹窗样式
    STYLES = {
        'default': {
            'overlay_color': (0, 0, 0, 150),
            'bg_color': (255, 255, 255, 230),
            'border_color': (0, 0, 0),
            'border_width': 3,
            'title_color': (0, 0, 0),
            'text_color': (0, 0, 0)
        },
        'training': {
            'overlay_color': (0, 0, 0, 150),
            'bg_color': (255, 255, 255, 220),
            'border_color': (0, 0, 0),
            'border_width': 3,
            'title_color': (0, 0, 0),
            'text_color': (0, 0, 0)
        },
        'battle': {
            'overlay_color': (0, 0, 0, 180),
            'bg_color': (240, 240, 240, 240),
            'border_color': (0, 0, 0),
            'border_width': 2,
            'title_color': (0, 0, 0),
            'text_color': (0, 0, 0)
        }
    }
    
    @staticmethod
    def create_overlay(screen_width, screen_height, color=(0, 0, 0, 150)):
        """创建半透明遮罩层"""
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill(color)
        return overlay
    
    @staticmethod
    def create_popup_background(width, height, bg_color=(255, 255, 255, 230)):
        """创建弹窗背景"""
        popup_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        popup_surface.fill(bg_color)
        return popup_surface
    
    @staticmethod
    def draw_popup_frame(screen, x, y, width, height, style='default'):
        """
        绘制标准弹窗框架（遮罩 + 背景 + 边框）
        
        Args:
            screen: 游戏屏幕surface
            x, y: 弹窗位置
            width, height: 弹窗尺寸
            style: 弹窗样式名称
        
        Returns:
            popup_rect: 弹窗矩形区域
        """
        style_config = PopupRenderer.STYLES.get(style, PopupRenderer.STYLES['default'])
        
        # 绘制半透明遮罩
        overlay = PopupRenderer.create_overlay(
            screen.get_width(), 
            screen.get_height(), 
            style_config['overlay_color']
        )
        screen.blit(overlay, (0, 0))
        
        # 绘制弹窗背景
        popup_bg = PopupRenderer.create_popup_background(width, height, style_config['bg_color'])
        screen.blit(popup_bg, (x, y))
        
        # 绘制边框
        popup_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, style_config['border_color'], popup_rect, style_config['border_width'])
        
        return popup_rect
    
    @staticmethod
    def draw_centered_popup(screen, width, height, style='default'):
        """
        绘制居中的弹窗框架
        
        Args:
            screen: 游戏屏幕surface
            width, height: 弹窗尺寸
            style: 弹窗样式名称
        
        Returns:
            popup_rect: 弹窗矩形区域
        """
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        return PopupRenderer.draw_popup_frame(screen, x, y, width, height, style)
    
    @staticmethod
    def draw_popup_title(screen, popup_rect, title, font, style='default'):
        """
        在弹窗顶部绘制标题
        
        Args:
            screen: 游戏屏幕surface
            popup_rect: 弹窗矩形区域
            title: 标题文本
            font: 字体对象
            style: 弹窗样式名称
        
        Returns:
            title_bottom_y: 标题底部的Y坐标
        """
        style_config = PopupRenderer.STYLES.get(style, PopupRenderer.STYLES['default'])
        
        title_text = font.render(title, True, style_config['title_color'])
        title_x = popup_rect.centerx - title_text.get_width() // 2
        title_y = popup_rect.y + 20
        
        screen.blit(title_text, (title_x, title_y))
        
        # 绘制标题下方分割线
        line_y = title_y + title_text.get_height() + 10
        pygame.draw.line(
            screen, 
            style_config['border_color'], 
            (popup_rect.x + 20, line_y), 
            (popup_rect.right - 20, line_y), 
            1
        )
        
        return line_y + 10
    
    @staticmethod
    def draw_popup_buttons(screen, popup_rect, buttons_config, button_height=40, button_spacing=20):
        """
        在弹窗底部绘制按钮组
        
        Args:
            screen: 游戏屏幕surface
            popup_rect: 弹窗矩形区域
            buttons_config: 按钮配置列表 [{'text': '确认', 'color': (100,200,100)}, ...]
            button_height: 按钮高度
            button_spacing: 按钮间距
        
        Returns:
            button_rects: 按钮矩形区域列表
        """
        button_count = len(buttons_config)
        if button_count == 0:
            return []
        
        # 计算按钮尺寸和位置
        total_button_width = button_count * 100 + (button_count - 1) * button_spacing
        start_x = popup_rect.centerx - total_button_width // 2
        button_y = popup_rect.bottom - button_height - 20
        
        button_rects = []
        
        for i, button_config in enumerate(buttons_config):
            button_x = start_x + i * (100 + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, 100, button_height)
            
            # 绘制按钮背景
            button_color = button_config.get('color', (200, 200, 200))
            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, (0, 0, 0), button_rect, 2)
            
            # 绘制按钮文字
            font = button_config.get('font', pygame.font.Font(None, 24))
            text_color = button_config.get('text_color', (0, 0, 0))
            text_surface = font.render(button_config['text'], True, text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)
            
            button_rects.append(button_rect)
        
        return button_rects
    
    @staticmethod
    def draw_confirmation_popup(screen, message, title="确认", style='default'):
        """
        绘制标准确认弹窗
        
        Args:
            screen: 游戏屏幕surface
            message: 确认消息
            title: 弹窗标题
            style: 弹窗样式名称
        
        Returns:
            (popup_rect, confirm_button_rect, cancel_button_rect)
        """
        popup_width = 400
        popup_height = 200
        
        popup_rect = PopupRenderer.draw_centered_popup(screen, popup_width, popup_height, style)
        
        # 绘制标题
        title_font = pygame.font.Font(None, 32)
        content_start_y = PopupRenderer.draw_popup_title(screen, popup_rect, title, title_font, style)
        
        # 绘制消息文本
        message_font = pygame.font.Font(None, 24)
        style_config = PopupRenderer.STYLES.get(style, PopupRenderer.STYLES['default'])
        
        # 简单的文本换行处理
        words = message.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if message_font.size(test_line)[0] <= popup_width - 40:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 绘制文本行
        text_y = content_start_y + 10
        for line in lines:
            text_surface = message_font.render(line, True, style_config['text_color'])
            text_x = popup_rect.x + 20
            screen.blit(text_surface, (text_x, text_y))
            text_y += text_surface.get_height() + 5
        
        # 绘制确认和取消按钮
        buttons_config = [
            {'text': '确认', 'color': (100, 200, 100), 'font': message_font},
            {'text': '取消', 'color': (200, 100, 100), 'font': message_font}
        ]
        
        button_rects = PopupRenderer.draw_popup_buttons(screen, popup_rect, buttons_config)
        
        return popup_rect, button_rects[0] if len(button_rects) > 0 else None, button_rects[1] if len(button_rects) > 1 else None