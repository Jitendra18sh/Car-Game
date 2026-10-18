import random
import sys
import pygame

# ======================== CONFIGURATION ========================

WIDTH = 900
HEIGHT = 700
FPS = 60

ROAD_WIDTH = 500
ROAD_LEFT = (WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH

LANES = 4
LANE_WIDTH = ROAD_WIDTH / LANES

PLAYER_WIDTH = 48
PLAYER_HEIGHT = 84

TRAFFIC_WIDTH = 46
TRAFFIC_HEIGHT = 80

MAX_SPEED = 560
ACCELERATION = 250
BRAKING = 430
DRAG = 90
STEERING_SPEED = 330

CYAN = (64, 224, 255)
WHITE = (246, 248, 250)
YELLOW = (255, 214, 76)
MUTED = (180, 192, 204)
ROAD_COLOR = (47, 49, 56)

pygame.init()

# Full-screen display
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

# Get the actual screen resolution
WIDTH, HEIGHT = screen.get_size()

pygame.display.set_caption("Neon Highway - Car Racing")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("arial", 22, bold=True)
SMALL_FONT = pygame.font.SysFont("arial", 16)
BIG_FONT = pygame.font.SysFont("arial", 58, bold=True)


# ======================== HELPER FUNCTIONS ========================

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def draw_text(surface, value, font, color, center):
    image = font.render(value, True, color)
    surface.blit(image, image.get_rect(center=center))


def draw_rounded_rect(surface, color, rect, radius=8, width=0):
    pygame.draw.rect(
        surface,
        color,
        rect,
        width=width,
        border_radius=radius
    )


# ======================== CAR GRAPHICS ========================

def draw_car(surface, rect, color, player=False):
    x, y, w, h = rect

    # Wheels
    wheel_width = max(7, w // 7)
    wheel_height = max(15, h // 5)

    for wheel_x in (x - 2, x + w - wheel_width + 2):
        for wheel_y in (
            y + 13,
            y + h - wheel_height - 12
        ):
            draw_rounded_rect(
                surface,
                (12, 14, 18),
                (
                    wheel_x,
                    wheel_y,
                    wheel_width,
                    wheel_height
                ),
                3
            )

    # Car body
    draw_rounded_rect(
        surface,
        (8, 10, 15),
        (x - 1, y - 1, w + 2, h + 2),
        11
    )

    draw_rounded_rect(
        surface,
        color,
        rect,
        10
    )

    # Hood highlight
    brighter_color = tuple(
        min(255, channel + 25)
        for channel in color
    )

    pygame.draw.polygon(
        surface,
        brighter_color,
        [
            (x + 8, y + 10),
            (x + w - 8, y + 10),
            (x + w - 5, y + 30),
            (x + 5, y + 30)
        ]
    )

    # Windshield
    glass_color = (
        (115, 190, 213)
        if player
        else (115, 145, 162)
    )

    pygame.draw.polygon(
        surface,
        glass_color,
        [
            (x + 9, y + 30),
            (x + w - 9, y + 30),
            (x + w - 13, y + 47),
            (x + 13, y + 47)
        ]
    )

    # Rear window
    pygame.draw.polygon(
        surface,
        (40, 65, 79),
        [
            (x + 13, y + 54),
            (x + w - 13, y + 54),
            (x + w - 16, y + 64),
            (x + 16, y + 64)
        ]
    )

    # Headlights
    draw_rounded_rect(
        surface,
        (255, 245, 190),
        (x + 5, y + 5, 9, 5),
        2
    )

    draw_rounded_rect(
        surface,
        (255, 245, 190),
        (x + w - 14, y + 5, 9, 5),
        2
    )

    # Rear lights
    draw_rounded_rect(
        surface,
        (255, 55, 60),
        (x + 5, y + h - 8, 9, 4),
        2
    )

    draw_rounded_rect(
        surface,
        (255, 55, 60),
        (x + w - 14, y + h - 8, 9, 4),
        2
    )

    # Player racing stripe
    if player:
        pygame.draw.rect(
            surface,
            CYAN,
            (x + w // 2 - 2, y + 12, 4, 15)
        )


# ======================== TRAFFIC CAR ========================

class TrafficCar:

    def __init__(self, lane):
        self.lane = lane

        self.x = (
            ROAD_LEFT
            + lane * LANE_WIDTH
            + (LANE_WIDTH - TRAFFIC_WIDTH) / 2
        )

        self.y = -TRAFFIC_HEIGHT - random.randint(10, 80)

        self.color = random.choice([
            (255, 89, 94),
            (255, 166, 77),
            (170, 125, 255),
            (255, 215, 85),
            (230, 238, 245),
            (70, 205, 145)
        ])

        self.speed_factor = random.uniform(0.52, 0.84)

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x),
            int(self.y),
            TRAFFIC_WIDTH,
            TRAFFIC_HEIGHT
        )

    def update(self, dt, road_speed):
        self.y += road_speed * self.speed_factor * dt

    def draw(self, surface):
        draw_car(surface, self.rect, self.color)


# ======================== MAIN GAME ========================

class CarRacingGame:

    def __init__(self):
        self.best_score = 0
        self.reset()

    def reset(self):
        self.player_x = WIDTH / 2 - PLAYER_WIDTH / 2
        self.player_y = HEIGHT - PLAYER_HEIGHT - 42

        self.player_rect = pygame.Rect(
            int(self.player_x),
            int(self.player_y),
            PLAYER_WIDTH,
            PLAYER_HEIGHT
        )

        self.speed = 0
        self.distance = 0
        self.elapsed = 0
        self.score = 0

        self.road_offset = 0
        self.grass_offset = 0
        self.spawn_timer = 0

        self.traffic = []

        self.crashed = False
        self.paused = False

    # -------------------- Traffic spawning --------------------

    def spawn_traffic(self):
        lanes = list(range(LANES))
        random.shuffle(lanes)

        for lane in lanes:

            # Avoid stacking cars in the same lane near the top.
            occupied = any(
                car.lane == lane and car.y < 150
                for car in self.traffic
            )

            if occupied:
                continue

            self.traffic.append(TrafficCar(lane))
            return

    # -------------------- Player and traffic update --------------------

    def update(self, dt, keys):

        if self.crashed or self.paused:
            return

        self.elapsed += dt

        # Acceleration
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += ACCELERATION * dt

        # Braking
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= BRAKING * dt

        # Natural deceleration
        else:
            self.speed -= DRAG * dt

        self.speed = clamp(
            self.speed,
            0,
            MAX_SPEED
        )

        # Steering
        direction = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1

        steering_factor = (
            0.65
            + 0.35 * self.speed / MAX_SPEED
        )

        self.player_x += (
            direction
            * STEERING_SPEED
            * steering_factor
            * dt
        )

        # Keep the player on the road.
        self.player_x = clamp(
            self.player_x,
            ROAD_LEFT + 14,
            ROAD_RIGHT - PLAYER_WIDTH - 14
        )

        self.player_rect.x = int(self.player_x)

        # Road movement
        road_speed = 280 + self.speed * 0.72

        self.road_offset = (
            self.road_offset + road_speed * dt
        ) % 90

        self.grass_offset = (
            self.grass_offset + road_speed * dt
        ) % 80

        # Scoring
        self.distance += self.speed / 3.6 * dt

        self.score = int(
            self.distance * 2
            + self.elapsed * 3
        )

        # Gradually increase traffic frequency.
        spawn_interval = max(
            0.43,
            1.05 - self.elapsed * 0.008
        )

        self.spawn_timer += dt

        if self.spawn_timer >= spawn_interval:
            self.spawn_timer = 0
            self.spawn_traffic()

        # Update traffic
        for car in self.traffic:
            car.update(dt, road_speed)

        self.traffic = [
            car for car in self.traffic
            if car.y < HEIGHT + 100
        ]

        # Collision detection
        player_hitbox = self.player_rect.inflate(-14, -12)

        for car in self.traffic:

            traffic_hitbox = car.rect.inflate(-10, -8)

            if player_hitbox.colliderect(traffic_hitbox):
                self.crashed = True

                self.best_score = max(
                    self.best_score,
                    self.score
                )

                break

    # -------------------- Draw road and background --------------------

    def draw_background(self):

        screen.fill((18, 100, 57))

        # Scrolling grass strips
        start_y = -int(self.grass_offset)

        for index, y in enumerate(
            range(start_y, HEIGHT, 80)
        ):

            color = (
                (20, 112, 62)
                if index % 2 == 0
                else (18, 103, 55)
            )

            pygame.draw.rect(
                screen,
                color,
                (0, y, ROAD_LEFT, 80)
            )

            pygame.draw.rect(
                screen,
                color,
                (ROAD_RIGHT, y, WIDTH - ROAD_RIGHT, 80)
            )

        # Road shoulders
        pygame.draw.rect(
            screen,
            (230, 230, 218),
            (
                ROAD_LEFT - 8,
                0,
                ROAD_WIDTH + 16,
                HEIGHT
            )
        )

        # Main road
        pygame.draw.rect(
            screen,
            ROAD_COLOR,
            (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT)
        )

        # Lane markings
        offset = int(self.road_offset)

        for lane in range(1, LANES):

            x = int(
                ROAD_LEFT + lane * LANE_WIDTH
            )

            for y in range(-48 + offset, HEIGHT, 90):

                pygame.draw.rect(
                    screen,
                    (230, 230, 215),
                    (x - 3, y, 6, 48),
                    border_radius=3
                )

        # Roadside reflectors
        reflector_offset = int(
            self.road_offset * 1.2
        ) % 70

        for y in range(
            -20 + reflector_offset,
            HEIGHT,
            70
        ):

            pygame.draw.circle(
                screen,
                YELLOW,
                (ROAD_LEFT - 4, y),
                4
            )

            pygame.draw.circle(
                screen,
                YELLOW,
                (ROAD_RIGHT + 4, y),
                4
            )

    # -------------------- HUD --------------------

    def draw_hud(self):

        panel = pygame.Surface(
            (WIDTH - 32, 82),
            pygame.SRCALPHA
        )

        panel.fill((13, 20, 31, 220))

        screen.blit(panel, (16, 14))

        draw_text(
            screen,
            "NEON HIGHWAY",
            FONT,
            CYAN,
            (150, 39)
        )

        draw_text(
            screen,
            f"SCORE  {self.score:06d}",
            FONT,
            WHITE,
            (WIDTH // 2, 39)
        )

        draw_text(
            screen,
            f"BEST  {max(self.best_score, self.score):06d}",
            SMALL_FONT,
            YELLOW,
            (WIDTH - 130, 37)
        )

        # Speed bar
        bar = pygame.Rect(35, 58, 190, 10)

        draw_rounded_rect(
            screen,
            (50, 62, 73),
            bar,
            5
        )

        fill = bar.copy()

        fill.width = int(
            bar.width * self.speed / MAX_SPEED
        )

        if fill.width > 0:
            draw_rounded_rect(
                screen,
                CYAN,
                fill,
                5
            )

        draw_text(
            screen,
            f"{int(self.speed / MAX_SPEED * 220)} KM/H",
            SMALL_FONT,
            WHITE,
            (WIDTH // 2, 72)
        )

        draw_text(
            screen,
            "WASD / ARROWS TO DRIVE",
            SMALL_FONT,
            MUTED,
            (WIDTH - 155, 72)
        )

    # -------------------- Game overlay --------------------

    def draw_overlay(self, title, subtitle, footer):

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((4, 8, 16, 175))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect(
            WIDTH // 2 - 250,
            HEIGHT // 2 - 130,
            500,
            260
        )

        draw_rounded_rect(
            screen,
            (11, 20, 34),
            box,
            22
        )

        pygame.draw.rect(
            screen,
            CYAN,
            box,
            2,
            border_radius=22
        )

        draw_text(
            screen,
            title,
            BIG_FONT,
            WHITE,
            (WIDTH // 2, box.y + 65)
        )

        draw_text(
            screen,
            subtitle,
            FONT,
            MUTED,
            (WIDTH // 2, box.y + 125)
        )

        draw_text(
            screen,
            footer,
            SMALL_FONT,
            CYAN,
            (WIDTH // 2, box.y + 190)
        )

    # -------------------- Render frame --------------------

    def draw(self):

        self.draw_background()

        for car in self.traffic:
            car.draw(screen)

        self.player_rect.x = int(self.player_x)
        self.player_rect.y = int(self.player_y)

        draw_car(
            screen,
            self.player_rect,
            (35, 145, 255),
            player=True
        )

        self.draw_hud()

        if self.paused and not self.crashed:

            self.draw_overlay(
                "PAUSED",
                "Take a breath, racer.",
                "Press P to continue"
            )

        elif self.crashed:

            self.draw_overlay(
                "CRASH!",
                f"Final score: {self.score}",
                "Press R to race again  |  Esc to quit"
            )


# ======================== GAME LOOP ========================

def main():

    game = CarRacingGame()
    running = True

    while running:

        # Cap delta time to prevent large physics jumps.
        dt = min(
            clock.tick(FPS) / 1000.0,
            0.04
        )

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif (
                    event.key == pygame.K_p
                    and not game.crashed
                ):
                    game.paused = not game.paused

                elif (
                    event.key == pygame.K_r
                    and game.crashed
                ):
                    game.reset()

        keys = pygame.key.get_pressed()

        game.update(dt, keys)
        game.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()