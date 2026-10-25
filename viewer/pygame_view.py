"""Watch matches in a window.

Keys:  SPACE pause   +/- speed   ESC skip to the result   N / ENTER next
       F fullscreen  Q quit
"""

import math

import pygame

from engine import config

SIDEBAR = 280
TOPBAR = 44
WIDTH = config.ARENA_WIDTH + SIDEBAR
HEIGHT = config.ARENA_HEIGHT + TOPBAR
FPS = 60
SPEEDS = [0.25, 0.5, 1, 2, 4, 8, 16]

BG = (18, 20, 28)
FLOOR = (32, 36, 48)
GRID = (40, 45, 60)
TEXT = (230, 232, 240)
DIM = (140, 145, 160)
BAD = (240, 90, 90)
GOOD = (90, 220, 120)


class ViewerClosed(Exception):
    """The teacher closed the window or pressed Q."""


def _darker(color, amount=0.55):
    return tuple(int(c * amount) for c in color)


class Viewer:
    def __init__(self, caption="Robot Wars"):
        pygame.init()
        pygame.display.set_caption(caption)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.small = pygame.font.Font(None, 18)
        self.big = pygame.font.Font(None, 40)
        self.huge = pygame.font.Font(None, 72)
        self.mono = pygame.font.SysFont("dejavusansmono,consolas,menlo,couriernew,monospace", 18)
        self.speed_index = SPEEDS.index(1)
        self.effects = []

    def close(self):
        pygame.quit()

    # ---- public --------------------------------------------------------
    def play(self, match, title="", auto_advance=None):
        """Show a match until it ends and the teacher moves on. Returns the MatchResult.

        auto_advance: seconds to wait on the result screen before carrying on by itself.
        """
        self.effects = []
        paused = False
        progress = 0.0
        while not match.result:
            for event in self._events():
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS, pygame.K_UP):
                    self.speed_index = min(self.speed_index + 1, len(SPEEDS) - 1)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS, pygame.K_DOWN):
                    self.speed_index = max(self.speed_index - 1, 0)
                elif event.key == pygame.K_ESCAPE:
                    match.run()
            if not paused and not match.result:
                progress += config.TICKS_PER_SECOND * SPEEDS[self.speed_index] / FPS
                while progress >= 1 and not match.result:
                    progress -= 1
                    match.step()
                    self._collect_effects(match.world.events)
            self._draw_match(match, title, paused)
            pygame.display.flip()
            self.clock.tick(FPS)

        self._wait(lambda: self._draw_match(match, title, False, show_result=True), auto_advance)
        return match.result

    def show_text(self, title, lines, auto_advance=None):
        """A full-screen text page, e.g. a leaderboard between matches."""
        def draw():
            self.screen.fill(BG)
            self._text(title, self.big, TEXT, (WIDTH // 2, 50), center=True)
            width = max((self.mono.size(line)[0] for line in lines), default=0)
            x = max(12, (WIDTH - width) // 2)
            y = 100
            for line in lines:
                self._text(line, self.mono, TEXT, (x, y))
                y += 24
            self._text("Press N or ENTER to continue", self.small, DIM, (WIDTH // 2, HEIGHT - 30), center=True)
        self._wait(draw, auto_advance)

    # ---- loop helpers ---------------------------------------------------
    def _events(self):
        """Yield key presses, handling quit and fullscreen here."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise ViewerClosed()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    raise ViewerClosed()
                if event.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
                    continue
                yield event

    def _wait(self, draw, auto_advance):
        waited = 0.0
        while auto_advance is None or waited < auto_advance:
            for event in self._events():
                if event.key in (pygame.K_n, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                    return
            draw()
            pygame.display.flip()
            waited += self.clock.tick(FPS) / 1000

    # ---- effects --------------------------------------------------------
    def _collect_effects(self, events):
        for event in events:
            kind = event[0]
            if kind == "boom":
                self.effects.append(["boom", event[1], event[2], 0, 40, event[3]])
            elif kind == "hit":
                self.effects.append(["hit", event[1], event[2], 0, 10, (255, 230, 120)])
            elif kind == "fire":
                self.effects.append(["fire", event[1], event[2], 0, 5, (255, 255, 200)])

    def _draw_effects(self, oy):
        alive = []
        for effect in self.effects:
            kind, x, y, age, life, color = effect
            t = age / life
            if kind == "boom":
                radius = int(10 + 60 * t)
                pygame.draw.circle(self.screen, color, (x, y + oy), radius, max(1, int(8 * (1 - t))))
                pygame.draw.circle(self.screen, (255, 200, 80), (x, y + oy), int(radius * 0.6), max(1, int(5 * (1 - t))))
            elif kind == "hit":
                pygame.draw.circle(self.screen, color, (x, y + oy), int(4 + 14 * t), 2)
            else:
                pygame.draw.circle(self.screen, color, (x, y + oy), int(6 * (1 - t)) + 1)
            effect[3] += 1
            if effect[3] < life:
                alive.append(effect)
        self.effects = alive

    # ---- drawing --------------------------------------------------------
    def _text(self, text, font, color, pos, center=False):
        surface = font.render(str(text), True, color)
        rect = surface.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        self.screen.blit(surface, rect)

    def _draw_match(self, match, title, paused, show_result=False):
        world = match.world
        oy = TOPBAR
        self.screen.fill(BG)

        # top bar
        seconds_left = max(0, (config.MAX_TICKS - world.tick) / config.TICKS_PER_SECOND)
        self._text(title, self.big, TEXT, (12, 8))
        status = f"{int(seconds_left) // 60}:{int(seconds_left) % 60:02d}   speed x{SPEEDS[self.speed_index]:g}"
        if paused:
            status = "PAUSED   " + status
        self._text(status, self.font, DIM, (config.ARENA_WIDTH - 230, 14))

        # arena floor
        pygame.draw.rect(self.screen, FLOOR, (0, oy, config.ARENA_WIDTH, config.ARENA_HEIGHT))
        for gx in range(0, config.ARENA_WIDTH, 50):
            pygame.draw.line(self.screen, GRID, (gx, oy), (gx, oy + config.ARENA_HEIGHT))
        for gy in range(0, config.ARENA_HEIGHT, 50):
            pygame.draw.line(self.screen, GRID, (0, oy + gy), (config.ARENA_WIDTH, oy + gy))
        pygame.draw.rect(self.screen, DIM, (0, oy, config.ARENA_WIDTH, config.ARENA_HEIGHT), 2)

        r = config.ROBOT_RADIUS
        for robot in world.robots:
            if not robot.alive:
                pygame.draw.circle(self.screen, (60, 60, 66), (robot.x, robot.y + oy), r)
                pygame.draw.circle(self.screen, (90, 90, 96), (robot.x, robot.y + oy), r, 2)

        for bullet in world.bullets:
            pygame.draw.circle(self.screen, (255, 245, 180), (bullet.x, bullet.y + oy), config.BULLET_RADIUS + bullet.power - 1)

        for robot in world.alive:
            x, y = robot.x, robot.y + oy
            rad = math.radians(robot.heading)
            tip = (x + math.sin(rad) * (r + 10), y - math.cos(rad) * (r + 10))
            pygame.draw.line(self.screen, _darker(robot.color, 0.4), (x, y), tip, 7)
            pygame.draw.circle(self.screen, robot.color, (x, y), r)
            pygame.draw.circle(self.screen, _darker(robot.color), (x, y), r, 3)
            pygame.draw.line(self.screen, (240, 240, 240), (x, y), tip, 3)
            self._text(robot.name, self.small, TEXT, (x, y - r - 18), center=True)
            bar = 40
            pygame.draw.rect(self.screen, (60, 20, 20), (x - bar / 2, y + r + 6, bar, 5))
            pygame.draw.rect(self.screen, _health_color(robot.health), (x - bar / 2, y + r + 6, bar * robot.health / config.START_HEALTH, 5))

        self._draw_effects(oy)
        self._draw_sidebar(world)

        if show_result and match.result:
            self._draw_result(match.result)

    def _draw_sidebar(self, world):
        x0 = config.ARENA_WIDTH + 12
        pygame.draw.rect(self.screen, (26, 29, 40), (config.ARENA_WIDTH, 0, SIDEBAR, HEIGHT))
        y = 12
        self._text("ROBOTS", self.font, DIM, (x0, y))
        y += 30
        ranked = sorted(world.robots, key=lambda r: (r.alive, r.health, r.died_at or 0), reverse=True)
        row_height = max(34, min(62, (HEIGHT - 60) // max(1, len(ranked))))
        for robot in ranked:
            pygame.draw.circle(self.screen, robot.color if robot.alive else (80, 80, 86), (x0 + 8, y + 9), 8)
            self._text(robot.name, self.font, TEXT if robot.alive else DIM, (x0 + 24, y + 2))
            self._text(f"{robot.health:.0f}", self.font, TEXT, (x0 + SIDEBAR - 52, y + 2))
            if row_height >= 46:
                bar = SIDEBAR - 40
                pygame.draw.rect(self.screen, (60, 20, 20), (x0 + 24, y + 22, bar - 24, 5))
                pygame.draw.rect(self.screen, _health_color(robot.health), (x0 + 24, y + 22, (bar - 24) * robot.health / config.START_HEALTH, 5))
                note, color = _robot_note(robot)
                if note:
                    self._text(note[:44], self.small, color, (x0 + 24, y + 31))
            y += row_height

    def _draw_result(self, result):
        overlay = pygame.Surface((config.ARENA_WIDTH, 220), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        top = TOPBAR + config.ARENA_HEIGHT // 2 - 110
        self.screen.blit(overlay, (0, top))
        cx = config.ARENA_WIDTH // 2
        if result.winner:
            self._text("WINNER", self.big, DIM, (cx, top + 40), center=True)
            self._text(result.winner.name, self.huge, result.winner.color, (cx, top + 95), center=True)
        else:
            self._text("DRAW", self.huge, TEXT, (cx, top + 80), center=True)
        self._text(result.reason, self.font, DIM, (cx, top + 150), center=True)
        self._text("Press N or ENTER to continue", self.small, DIM, (cx, top + 190), center=True)


def _health_color(health):
    if health > 60:
        return GOOD
    if health > 30:
        return (240, 200, 70)
    return BAD


def _robot_note(robot):
    if robot.status.startswith("disqualified"):
        return robot.status, BAD
    if robot.last_error:
        return robot.last_error, BAD
    if not robot.alive:
        return robot.status, DIM
    return f"shots {robot.shots}  hits {robot.hits}", DIM
