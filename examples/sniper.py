# Stays still, aims where the enemy is GOING to be, and fires big shots.
# Concepts: lists, loops, maths, memory.

import math

NAME = "Sniper"
COLOR = "purple"

BULLET_SPEED = 12


def weakest(enemies):
    best = enemies[0]
    for enemy in enemies:
        if enemy.health < best.health:
            best = enemy
    return best


def think(me, enemies, arena):
    target = weakest(enemies)

    # Predict where the target will be when our bullet gets there.
    ticks_to_arrive = me.distance_to(target) / BULLET_SPEED
    heading = math.radians(target.heading)
    future_x = target.x + math.sin(heading) * target.speed * ticks_to_arrive
    future_y = target.y - math.cos(heading) * target.speed * ticks_to_arrive

    me.turn_toward((future_x, future_y))

    # Run away if someone gets close.
    if me.distance_to(me.closest(enemies)) < 120:
        me.backward()

    difference = abs(me.angle_to((future_x, future_y)) - me.heading) % 360
    if me.can_fire() and (difference < 5 or difference > 355):
        me.fire(3)
