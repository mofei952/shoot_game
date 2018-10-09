#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/7/26 19:43
# @File    : shoot.py
# @Software: PyCharm
import random
import threading
from abc import ABCMeta, abstractmethod
from enum import Enum

import pygame

# 窗口宽高
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 654
# 背景，开始，暂停，游戏结束图片
background_image = pygame.image.load('image/background.png')
start_image = pygame.image.load('image/start.png')
pause_image = pygame.image.load('image/pause.png')
gameover_image = pygame.image.load('image/gameover.png')
# 英雄机图片，两张图片切换
hero0_image = pygame.image.load('image/hero0.png')
hero1_image = pygame.image.load('image/hero1.png')
# 子弹图片
bullet_image = pygame.image.load('image/bullet.png')
# 敌机，大敌机，敌机爆炸图片
airplane_image = pygame.image.load('image/airplane.png')
airplane_rect = airplane_image.get_rect()
big_airplane_image = pygame.transform.scale(airplane_image, (airplane_rect.width * 2, airplane_rect.height * 2))
bomb_image = pygame.image.load('image/bomb.png')
bomb_rect = bomb_image.get_rect()
# 黄色星星，蓝色星星图片
yellow_star_image = pygame.image.load('image/star.png')
blue_star_image = pygame.image.load('image/blue_star.png')


class GameState(Enum):
    """游戏状态"""
    start = 0
    running = 1
    gameover = 2
    pause = 3


class Award(Enum):
    """奖励类型"""
    life = 0
    bullet = 1

    def hint(self):
        """获得奖励的提示"""
        if self == Award.life:
            return '生命+1'
        elif self == Award.bullet:
            return '火力+20'


class FlyingObject(pygame.sprite.Sprite):
    """飞行物"""
    __metaclass__ = ABCMeta

    def __init__(self):
        super(FlyingObject, self).__init__()
        self.image = None
        self.rect = None
        self.speed = 0
        self.life = 1

    def hit(self, fly):
        """撞击另一个飞行物"""
        # 其中一个已经毁灭，返回False表示撞击失败
        if not self.is_live() or not fly.is_live():
            return False
        # 两个飞行物都减少生命
        self.sub_life()
        fly.sub_life()
        return True

    def sub_life(self):
        """减少生命"""
        # 若已经毁灭，则返回失败
        if not self.is_live():
            return False
        self.life -= 1
        # 若减少之后生命不足，则毁灭
        if not self.is_live():
            self.destroy()

    def is_live(self):
        """是否存活"""
        return self.life > 0

    def destroy(self):
        """毁灭，不重写直接kill，可重写做延迟消失处理"""
        self.kill()

    @abstractmethod
    def update(self):
        """更新当前对象状态的方法，供子类实现"""
        pass


class Hint(FlyingObject):
    """提示"""

    def __init__(self, hint_str, pos):
        super(Hint, self).__init__()
        self.hint_str = hint_str
        # 元组不能更改，转换为list
        self.start_pos = list(pos)
        self.pos = self.start_pos.copy()

    def update(self):
        """上升一小段距离后消失"""
        self.pos[1] -= 1
        if self.start_pos[1] - self.pos[1] >= 40:
            self.kill()


class Bullet(FlyingObject):
    """子弹"""

    def __init__(self, pos):
        super(Bullet, self).__init__()
        self.image = bullet_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (pos[0] - self.rect.width / 2, pos[1])
        self.speed = 8

    def update(self):
        """向上移动，出上边界消失"""
        self.rect.top -= self.speed
        if self.rect.bottom < 0:
            self.kill()


class Enemy(FlyingObject):
    """敌人"""
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Enemy, self).__init__()
        self.score = 0

    def update(self):
        """向下移动，出下边界消失"""
        self.rect.top += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def destroy(self):
        """重写destroy方法，延迟消失"""
        # 将图片置为bomb图片，坐标移动到正中间
        x = self.rect.left + ((self.rect.width - bomb_rect.width) / 2)
        y = self.rect.top + ((self.rect.height - bomb_rect.height) / 2)
        self.rect.topleft = (x, y)
        self.image = bomb_image
        # 0.3秒后消失
        timer = threading.Timer(0.3, self.kill)
        timer.start()


class Airplane(Enemy):
    """敌机，敌人的子类"""

    def __init__(self):
        super(Airplane, self).__init__()
        self.image = airplane_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (random.randint(0, SCREEN_WIDTH - self.rect.width), (-self.rect.height))
        self.speed = 4
        self.score = 10


class BigAirplane(Enemy):
    """大敌机，敌人的子类"""

    def __init__(self):
        super(BigAirplane, self).__init__()
        self.image = big_airplane_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (random.randint(0, SCREEN_WIDTH - self.rect.width), (-self.rect.height))
        self.speed = 3
        self.life = 2
        self.score = 30


class Star(FlyingObject):
    """星星，英雄机可以吃星星获得奖励"""

    def __init__(self):
        super(Star, self).__init__()
        # 初始化奖励类型
        self.award = random.choices(list(Award), [1, 3])[0]
        # 生命奖励为黄色星星，火力奖励为蓝色星星
        self.image = yellow_star_image if self.award == Award.life else blue_star_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (random.randint(0, SCREEN_WIDTH - self.rect.width), (-self.rect.height))
        self.speed_x = 2
        self.speed_y = 4

    def update(self):
        """斜向下移动"""
        self.rect.left += self.speed_x
        self.rect.top += self.speed_y
        # 碰到左右边界speed_x取反
        if self.rect.left < 0 or self.rect.left > SCREEN_WIDTH - self.rect.width:
            self.speed_x = -self.speed_x
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Hero(FlyingObject):
    """英雄机"""

    def __init__(self):
        super(Hero, self).__init__()
        self.images = [hero0_image, hero1_image]
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = (int(SCREEN_WIDTH / 2 - self.rect.width / 2), SCREEN_HEIGHT - self.rect.height - 30)
        self.speed = 6
        self.life = 3
        self.init_directions()
        self.double_fire = 0
        # 控制图片切换
        self.index = 0
        # 子弹列表
        self.bullets = pygame.sprite.Group()

    def shoot(self):
        """射击"""
        step_x = self.rect.width / 4
        # 火力大于0时二连发
        if self.double_fire > 0:
            self.bullets.add(Bullet((self.rect.left + 1 * step_x, self.rect.top)))
            self.bullets.add(Bullet((self.rect.left + 3 * step_x, self.rect.top)))
            self.double_fire -= 2
        # 没有火力单发子弹
        else:
            self.bullets.add(Bullet(self.rect.midtop))

    def hit(self, fly):
        """重写hit，英雄机碰到的飞行物直接毁灭而不是减少生命"""
        if not self.is_live() or not fly.is_live():
            return False
        self.sub_life()
        fly.destroy()
        return True

    def set_direction_enabled(self, direction, enabled):
        """设置某个方向有效或无效"""
        self.directions[direction] = enabled

    def init_directions(self):
        """初始化方向的字典"""
        self.directions = {pygame.K_LEFT: False, pygame.K_RIGHT: False, pygame.K_UP: False, pygame.K_DOWN: False}

    def receive_award(self, award):
        """接受奖励"""
        if award == Award.life:
            self.life += 1
        elif award == Award.bullet:
            self.double_fire += 20

    def update(self):
        # 切换图片
        self.image = self.images[self.index // 10 % len(self.images)]
        self.index += 1
        # 移动，不能超出边界
        x = self.rect.left + (self.directions[pygame.K_RIGHT] - self.directions[pygame.K_LEFT]) * self.speed
        y = self.rect.top + (self.directions[pygame.K_DOWN] - self.directions[pygame.K_UP]) * self.speed
        if x < 0:
            x = 0
        elif x > SCREEN_WIDTH - self.rect.width:
            x = SCREEN_WIDTH - self.rect.width
        if y < 0:
            y = 0
        elif y > SCREEN_HEIGHT - self.rect.height:
            y = SCREEN_HEIGHT - self.rect.height
        self.rect.left = x
        self.rect.top = y


class Game:
    """游戏类"""

    def __init__(self):
        """初始化窗口"""
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption('shoot game')

        self.state = GameState.start
        self.init()

    def init(self):
        """初始化数据，供游戏第一次开始和死亡后重新开始时调用"""
        # 计数
        self.tick = 0
        # 分数
        self.point = 0
        # 英雄机对象
        self.hero = Hero()
        # 敌机组
        self.enemy_group = pygame.sprite.Group()
        # 星星组
        self.star_group = pygame.sprite.Group()
        # 提示组
        self.hint_group = pygame.sprite.Group()

    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        # 如果不是运行中，点击回车，置为运行中
        if self.state != GameState.running:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if self.state == GameState.gameover:
                    self.init()
                self.hero.init_directions()
                self.state = GameState.running
            return
            # 若在运行中，上下左右控制英雄机方向，回车暂停
        else:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.pause
                elif event.key in self.hero.directions:
                    self.hero.set_direction_enabled(event.key, True)
            elif event.type == pygame.KEYUP:
                if event.key in self.hero.directions:
                    self.hero.set_direction_enabled(event.key, False)

    def produce_flying_object(self):
        """产生飞行物"""
        fly_class = random.choices([Airplane, BigAirplane, Star], [4, 2, 1])[0]
        if fly_class == Airplane or fly_class == BigAirplane:
            self.enemy_group.add(fly_class())
        elif fly_class == Star:
            self.star_group.add(fly_class())

    def update(self):
        """子弹，敌机，提示，英雄机 更新位置"""
        self.hero.bullets.update()
        self.enemy_group.update()
        self.star_group.update()
        for hint in self.hint_group.sprites():
            hint.update()
        self.hero.update()

    def enemy_and_bullet_collide(self):
        """敌人和子弹碰撞 敌人生命-他撞到的子弹数量，若敌人生命=0则敌机毁灭然后获得分数"""
        enemy_and_bullet_list_dict = pygame.sprite.groupcollide(self.enemy_group, self.hero.bullets, False,
                                                                False)
        if enemy_and_bullet_list_dict:
            for enemy, bullet_list in enemy_and_bullet_list_dict.items():
                # 敌机已经毁灭，则跳过
                if not enemy.is_live():
                    continue
                # 遍历子弹 处理碰撞事件
                for bullet in bullet_list:
                    bullet.hit(enemy)
                    # 碰撞之后，敌机如果毁灭则得分，显示提示信息
                    if not enemy.is_live():
                        score = enemy.score
                        self.hint_group.add(Hint('分数+%d' % score, enemy.rect.topleft))
                        self.point += score
                        break

    def hero_and_star_collide(self):
        """星星和英雄机碰撞，获得奖励"""
        star_list = pygame.sprite.spritecollide(self.hero, self.star_group, True)
        if star_list:
            # 遍历星星，获得奖励并显示提示信息
            for star in star_list:
                self.hint_group.add(Hint(star.award.hint(), star.rect.topleft))
                self.hero.receive_award(star.award)

    def hero_and_enemy_collide(self):
        """敌机和英雄机碰撞，英雄机生命-1，敌机消失，若英雄机生命小于等于0游戏结束"""
        enemy_list = pygame.sprite.spritecollide(self.hero, self.enemy_group, True)
        if enemy_list:
            # 遍历敌机，若英雄机成功撞到敌机，显示提示信息并判断英雄机是否毁灭
            for enemy in enemy_list:
                if self.hero.hit(enemy):
                    self.hint_group.add(Hint('生命-1', self.hero.rect.topleft))
                    if not self.hero.is_live():
                        self.state = GameState.gameover

    def draw_flying_object(self):
        """绘制飞行物（子弹，敌机，星星，提示，英雄机）"""
        self.hero.bullets.draw(self.screen)
        self.enemy_group.draw(self.screen)
        self.star_group.draw(self.screen)
        for hint in self.hint_group.sprites():
            self.draw_string(hint.hint_str, 16, hint.pos)
        self.screen.blit(self.hero.image, self.hero.rect)

    def draw_string(self, s, size, pos, color=(255, 0, 0)):
        """绘制字符串"""
        font = pygame.font.SysFont("SimHei", size)
        text_surface = font.render(s, True, color)
        self.screen.blit(text_surface, pos)

    def draw_info(self):
        """绘制左上角的分数、生命、火力等信息"""
        self.draw_string("分数：%d" % self.point, 16, (0, 0))
        self.draw_string("生命：%d" % self.hero.life, 16, (80, 0))
        self.draw_string("火力：%d" % self.hero.double_fire, 16, (150, 0))

    def start(self):
        """游戏开始"""
        while True:
            """事件处理"""
            for event in pygame.event.get():
                self.handle_event(event)
            """画背景后，判断四个状态分别绘制"""
            # 画背景
            self.screen.blit(background_image, background_image.get_rect())
            # 若为开始界面，画开始图，写提示
            if self.state == GameState.start:
                self.screen.blit(start_image, start_image.get_rect())
                self.draw_string("press enter key to start", 30, (20, SCREEN_HEIGHT / 2 + 50), (150, 150, 150))
            # 若为暂停界面，画暂停图
            elif self.state == GameState.pause:
                self.screen.blit(pause_image, pause_image.get_rect())
            # 若为游戏结束界面，画游戏结束图、显示得分
            elif self.state == GameState.gameover:
                self.screen.blit(gameover_image, gameover_image.get_rect())
                self.draw_string("分数：%d" % self.point, 24, (140, SCREEN_HEIGHT / 2), (255, 0, 255))
            # 若为运行中
            elif self.state == GameState.running:
                # 每20个tick英雄射击，每50个tick产生飞行物
                if self.tick % 20 == 0:
                    self.hero.shoot()
                if self.tick % 50 == 0:
                    self.produce_flying_object()
                # 子弹，敌机，提示，英雄机 更新位置
                self.update()
                # 敌人和子弹碰撞 敌人生命-1，若敌人生命=0则敌机毁灭然后获得分数
                self.enemy_and_bullet_collide()
                # 星星和英雄机碰撞，获得奖励
                self.hero_and_star_collide()
                # 敌机和英雄机碰撞，英雄机生命-1，敌机消失，若英雄机生命小于等于0游戏结束
                self.hero_and_enemy_collide()
                # 绘制子弹，敌机，星星，提示，英雄机
                self.draw_flying_object()
                # 绘制左上角的分数、生命、火力
                self.draw_info()
                # 计数
                self.tick += 1

            pygame.display.flip()


if __name__ == '__main__':
    Game().start()
