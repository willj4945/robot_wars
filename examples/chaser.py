# Finds the closest enemy, drives at it and shoots.
# Concepts: variables, if statements, comparisons.

NAME = "Chaser"
COLOR = "red"


def think(me, enemies, arena):
    target = me.closest(enemies)
    me.turn_toward(target)

    # Don't get too close, or we'll ram them and both take damage.
    if me.distance_to(target) > 150:
        me.forward()
    else:
        me.stop()

    if me.can_fire():
        me.fire()
