# Spins in a circle and fires whenever the gun is ready.
# Concepts: calling functions, if statements.

NAME = "Spinner"
COLOR = "orange"


def think(me, enemies, arena):
    me.forward(2)
    me.turn_right()
    if me.can_fire():
        me.fire()
