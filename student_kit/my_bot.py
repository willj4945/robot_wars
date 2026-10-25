# ============================================================
#  MY ROBOT
#  Change the NAME and COLOR, then make think() smarter!
#
#  Test it:   python check_my_bot.py my_bot.py
#  Watch it:  python watch.py my_bot.py chaser
# ============================================================

NAME = "My First Robot"   # up to 24 letters
COLOR = "blue"            # red blue green yellow orange purple pink cyan
                          # white lime teal gold silver magenta brown navy


def think(me, enemies, arena):
    # This runs 30 times every second. Each time, tell your robot what to do.
    #
    #   me       -> your robot. me.x, me.y, me.health, me.forward(), me.fire() ...
    #   enemies  -> a list of the other robots still fighting
    #   arena    -> arena.width, arena.height, arena.tick
    #
    # See GUIDE.md for everything your robot can do.

    target = me.closest(enemies)

    me.turn_toward(target)
    me.forward()

    if me.can_fire():
        me.fire()
