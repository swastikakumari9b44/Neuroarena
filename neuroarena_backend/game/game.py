import pygame
import random
import math

# -----------------------------
# Initialize Pygame
# -----------------------------
pygame.init()

# Sound initialization
pygame.mixer.init()

clock = pygame.time.Clock()


# -----------------------------
# Window
# -----------------------------
WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "NeuroArena"
)


# -----------------------------
# Fonts
# -----------------------------
font = pygame.font.SysFont(
    None,
    36
)

big_font = pygame.font.SysFont(
    None,
    72
)

menu_font = pygame.font.SysFont(
    None,
    48
)

small_font = pygame.font.SysFont(
    None,
    28
)


# -----------------------------
# Colors
# -----------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (130, 130, 130)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)


# -----------------------------
# Sizes
# -----------------------------
player_size = 40
enemy_size = 40
gem_size = 30
wall_size = 40



# -----------------------------
# Load Player Images
# -----------------------------

player_walk = [

    pygame.image.load(
        "assets/player_walk1.png"
    ).convert_alpha(),


    pygame.image.load(
        "assets/player_walk2.png"
    ).convert_alpha(),


    pygame.image.load(
        "assets/player_walk3.png"
    ).convert_alpha(),


    pygame.image.load(
        "assets/player_walk4.png"
    ).convert_alpha()

]


for i in range(len(player_walk)):

    player_walk[i] = pygame.transform.scale(
        player_walk[i],
        (
            player_size,
            player_size
        )
    )



# -----------------------------
# Load Enemy Image
# -----------------------------

enemy_img = pygame.image.load(
    "assets/enemy.png"
).convert_alpha()


enemy_img = pygame.transform.scale(
    enemy_img,
    (
        enemy_size,
        enemy_size
    )
)



# -----------------------------
# Load Gem Image
# -----------------------------

gem_img = pygame.image.load(
    "assets/gem.png"
).convert_alpha()


gem_img = pygame.transform.scale(
    gem_img,
    (
        gem_size,
        gem_size
    )
)



# -----------------------------
# Load Wall Image
# -----------------------------

wall_img = pygame.image.load(
    "assets/wall.png"
).convert_alpha()


wall_img = pygame.transform.scale(
    wall_img,
    (
        wall_size,
        wall_size
    )
)



# -----------------------------
# PHASE 16 SOUND LOADING
# -----------------------------

gem_sound = pygame.mixer.Sound(
    "assets/ding.wav"
)


enemy_sound = pygame.mixer.Sound(
    "assets/ouch.wav"
)


win_sound = pygame.mixer.Sound(
    "assets/victory.wav"
)


# -----------------------------
# PHASE 17 SETTINGS (volume / sound toggle)
# -----------------------------

sound_volume = 0.5
sound_on = True


def apply_volume():
    """Applies the current volume/mute settings to all loaded sounds."""

    vol = sound_volume if sound_on else 0.0

    gem_sound.set_volume(vol)
    enemy_sound.set_volume(vol)
    win_sound.set_volume(vol)


apply_volume()



# -----------------------------
# Player Variables (defaults, real reset happens in reset_game)
# -----------------------------

player_speed = 5

animation_speed = 0.18



# -----------------------------
# Enemy Variables
# -----------------------------

enemy_speed = 4



# -----------------------------
# Walls
# -----------------------------

walls = [

    pygame.Rect(
        200,
        100,
        40,
        250
    ),


    pygame.Rect(
        450,
        200,
        40,
        250
    ),


    pygame.Rect(
        600,
        50,
        40,
        200
    ),


    pygame.Rect(
        100,
        420,
        250,
        40
    ),


    pygame.Rect(
        350,
        500,
        250,
        40
    )

]
# -----------------------------
# Spawn Gem Function
# -----------------------------

def spawn_gem():

    while True:

        x = random.randint(
            50,
            WIDTH - gem_size - 50
        )

        y = random.randint(
            50,
            HEIGHT - gem_size - 50
        )


        gem_rect = pygame.Rect(
            x,
            y,
            gem_size,
            gem_size
        )


        collision = False


        for wall in walls:

            if gem_rect.colliderect(wall):

                collision = True
                break


        if not collision:

            return x, y



# -----------------------------
# PHASE 18: Human vs AI - Difficulty Levels
# -----------------------------
#
# "chase_chance"  : probability each frame the AI actively hunts the
#                   player instead of running its old left/right patrol
# "prediction"    : how many frames ahead it aims, based on the
#                   player's current velocity (higher = harder to juke)
# "cooldown_ms"   : how soon after a hit it can damage the player again

DIFFICULTIES = {

    "Easy": {
        "speed": 4,
        "chase_chance": 0.0,
        "prediction": 0,
        "cooldown_ms": 500
    },

    "Medium": {
        "speed": 5,
        "chase_chance": 0.5,
        "prediction": 5,
        "cooldown_ms": 400
    },

    "Hard": {
        "speed": 6,
        "chase_chance": 0.85,
        "prediction": 15,
        "cooldown_ms": 300
    },

    "Impossible": {
        "speed": 7,
        "chase_chance": 1.0,
        "prediction": 25,
        "cooldown_ms": 150
    }

}

difficulty_options = ["Easy", "Medium", "Hard", "Impossible"]

# Default selection sits on Medium
difficulty_index = 1

# Where to return once setup is confirmed: "start" (fresh game from
# the Main Menu) or "pause" (mid-game change, no reset)
difficulty_source = "start"


def current_difficulty_name():
    return difficulty_options[difficulty_index]


# -----------------------------
# PHASE 8: Different Maps
# -----------------------------

MAPS = {

    "Classic": [
        pygame.Rect(200, 100, 40, 250),
        pygame.Rect(450, 200, 40, 250),
        pygame.Rect(600, 50, 40, 200),
        pygame.Rect(100, 420, 250, 40),
        pygame.Rect(350, 500, 250, 40),
    ],

    "Cross": [
        pygame.Rect(380, 0, 40, 240),
        pygame.Rect(380, 360, 40, 240),
        pygame.Rect(0, 280, 240, 40),
        pygame.Rect(560, 280, 240, 40),
    ],

    "Open": [
        pygame.Rect(340, 260, 120, 40),
    ],

}

map_options = ["Classic", "Cross", "Open", "Random"]
map_index = 0


def current_map_name():
    """Resolves 'Random' into one of the real maps at game-start time."""

    chosen = map_options[map_index]

    if chosen == "Random":
        return random.choice(list(MAPS.keys()))

    return chosen


# -----------------------------
# PHASE 8: Different AI Personalities
# -----------------------------
#
# These change HOW the enemy chases (its targeting style), separate
# from Difficulty, which controls raw speed/prediction/cooldown.

PERSONALITIES = {

    "Aggressive": {"guard_gem": False, "cutoff": False, "jitter": 0.0},
    "Defensive":  {"guard_gem": True,  "cutoff": False, "jitter": 0.0},
    "Erratic":    {"guard_gem": False, "cutoff": False, "jitter": 3.0},
    "Tactical":   {"guard_gem": False, "cutoff": True,  "jitter": 0.0},

}

personality_options = ["Aggressive", "Defensive", "Erratic", "Tactical"]
personality_index = 0


def current_personality_name():
    return personality_options[personality_index]


# -----------------------------
# PHASE 8: Multiple Game Modes
# -----------------------------

game_mode_options = ["Classic", "Survival", "Deathmatch"]
game_mode_index = 0


def current_game_mode():
    return game_mode_options[game_mode_index]


# -----------------------------
# PHASE 8: Obstacles / Fog of War / Items toggles
# -----------------------------

obstacles_enabled = False
fog_enabled = False
items_enabled = False

OBSTACLE_COUNT = 4
OBSTACLE_SIZE = 60
VISION_RADIUS = 220

item_size = 28

STUN_DURATION_MS = 1500
SHIELD_DURATION_MS = 4000
ARMED_DURATION_MS = 4000
HEAL_AMOUNT = 30


def resolve_enemy_move(ex, ey, move_x, move_y):
    """
    Moves the AI opponent by (move_x, move_y), sliding along walls
    instead of just stopping dead, the same way a real opponent would
    try to route around an obstacle rather than freeze against it.
    """

    target_x = max(0, min(WIDTH - enemy_size, ex + move_x))
    target_y = max(0, min(HEIGHT - enemy_size, ey + move_y))


    full_rect = pygame.Rect(target_x, target_y, enemy_size, enemy_size)

    if not any(full_rect.colliderect(w) for w in walls):
        return target_x, target_y


    # Full move blocked - try sliding along just the X axis
    x_rect = pygame.Rect(target_x, ey, enemy_size, enemy_size)

    if not any(x_rect.colliderect(w) for w in walls):
        return target_x, ey


    # Try sliding along just the Y axis
    y_rect = pygame.Rect(ex, target_y, enemy_size, enemy_size)

    if not any(y_rect.colliderect(w) for w in walls):
        return ex, target_y


    # Fully blocked this frame
    return ex, ey


def spawn_free_point(size, avoid_rects=None):
    """Generic free-space spawner used for the gem, items, and obstacles."""

    avoid_rects = avoid_rects or []

    while True:

        x = random.randint(50, WIDTH - size - 50)
        y = random.randint(50, HEIGHT - size - 50)

        rect = pygame.Rect(x, y, size, size)

        if any(rect.colliderect(w) for w in walls):
            continue

        if any(rect.colliderect(r) for r in avoid_rects):
            continue

        return x, y



# -----------------------------
# Game Variables
# -----------------------------

TARGET_GEMS = 20

TIME_LIMIT = 60

damage_cooldown = 500



# -----------------------------
# PHASE 17: Reset / Restart function
# -----------------------------

def reset_game():
    """Resets all gameplay state so the game can be (re)started fresh."""

    global player_x, player_y
    global player_vx, player_vy
    global enemy_x, enemy_y, direction
    global animation_index, moving
    global score, health, gems_collected
    global start_ticks
    global gem_x, gem_y
    global last_hit_time
    global walls, active_map_name
    global enemy_health
    global weapon_pos, shield_pos, heal_pos
    global player_shield_until, enemy_stun_until, player_armed_until

    player_x = 100
    player_y = 150

    player_vx = 0
    player_vy = 0

    enemy_x = 300
    enemy_y = 250
    direction = 1

    animation_index = 0
    moving = False

    score = 0
    health = 100
    gems_collected = 0

    enemy_health = 100  # only relevant in Deathmatch mode

    start_ticks = pygame.time.get_ticks()

    active_map_name = current_map_name()
    walls = list(MAPS[active_map_name])

    if obstacles_enabled:
        for _ in range(OBSTACLE_COUNT):
            ox, oy = spawn_free_point(OBSTACLE_SIZE)
            walls.append(pygame.Rect(ox, oy, OBSTACLE_SIZE, OBSTACLE_SIZE))

    gem_x, gem_y = spawn_gem()

    weapon_pos = None
    shield_pos = None
    heal_pos = None

    if items_enabled:
        weapon_pos = spawn_free_point(item_size, avoid_rects=[pygame.Rect(gem_x, gem_y, gem_size, gem_size)])
        shield_pos = spawn_free_point(item_size, avoid_rects=[pygame.Rect(gem_x, gem_y, gem_size, gem_size)])
        heal_pos = spawn_free_point(item_size, avoid_rects=[pygame.Rect(gem_x, gem_y, gem_size, gem_size)])

    last_hit_time = 0

    player_shield_until = 0
    enemy_stun_until = 0
    player_armed_until = 0


# Initialize variables once so they exist before the loop starts
reset_game()



# -----------------------------
# PHASE 17: Game States
# -----------------------------

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_SETTINGS = "settings"
STATE_SETUP = "setup"
STATE_GAMEOVER = "gameover"

state = STATE_MENU

# Remembers which state to go back to when leaving Settings
previous_state = STATE_MENU

# Result of the last match: "win" / "lose" / "draw" (Deathmatch only)
match_outcome = None


pause_options = [
    "Resume",
    "Settings",
    "Game Setup",
    "Restart",
    "Main Menu"
]
pause_index = 0


gameover_options = [
    "Restart",
    "Main Menu"
]
gameover_index = 0


# -----------------------------
# PHASE 8: Setup Menu rows
# -----------------------------
# Each row cycles its own option list independently with LEFT/RIGHT;
# UP/DOWN moves between rows.

setup_rows = [
    {"label": "Difficulty",  "options": difficulty_options,   "get_index": lambda: difficulty_index},
    {"label": "Personality", "options": personality_options,  "get_index": lambda: personality_index},
    {"label": "Map",         "options": map_options,          "get_index": lambda: map_index},
    {"label": "Game Mode",   "options": game_mode_options,    "get_index": lambda: game_mode_index},
    {"label": "Obstacles",   "options": ["Off", "On"],        "get_index": lambda: int(obstacles_enabled)},
    {"label": "Fog of War",  "options": ["Off", "On"],        "get_index": lambda: int(fog_enabled)},
    {"label": "Items",       "options": ["Off", "On"],        "get_index": lambda: int(items_enabled)},
]

setup_row_index = 0


def cycle_setup_row(row_index, step):
    """Changes the value of whichever setup row is currently selected."""

    global difficulty_index, personality_index, map_index, game_mode_index
    global obstacles_enabled, fog_enabled, items_enabled

    row = setup_rows[row_index]
    label = row["label"]
    options = row["options"]

    if label == "Difficulty":
        difficulty_index = (difficulty_index + step) % len(options)

    elif label == "Personality":
        personality_index = (personality_index + step) % len(options)

    elif label == "Map":
        map_index = (map_index + step) % len(options)

    elif label == "Game Mode":
        game_mode_index = (game_mode_index + step) % len(options)

    elif label == "Obstacles":
        obstacles_enabled = not obstacles_enabled

    elif label == "Fog of War":
        fog_enabled = not fog_enabled

    elif label == "Items":
        items_enabled = not items_enabled



# -----------------------------
# PHASE 17: Menu Drawing Helpers
# -----------------------------

def draw_text_center(text, fnt, color, y):

    surf = fnt.render(text, True, color)

    screen.blit(
        surf,
        (
            WIDTH // 2 - surf.get_width() // 2,
            y
        )
    )


def draw_main_menu():

    screen.fill(BLACK)

    draw_text_center("NEUROARENA", big_font, WHITE, 160)

    draw_text_center("Press SPACE to Play", font, YELLOW, 300)

    draw_text_center("Press S for Settings", font, GRAY, 350)

    draw_text_center("Press ESC to Quit", small_font, GRAY, 400)


def draw_setup_menu():

    screen.fill(BLACK)

    draw_text_center("GAME SETUP", big_font, WHITE, 40)

    row_y = 110

    for i, row in enumerate(setup_rows):

        idx = row["get_index"]()
        value = row["options"][idx]

        color = YELLOW if i == setup_row_index else WHITE

        line = f"{row['label']} :  < {value} >" if i == setup_row_index else f"{row['label']} :  {value}"

        draw_text_center(line, font, color, row_y)

        row_y += 50

    draw_text_center(
        "UP/DOWN to select row, LEFT/RIGHT to change, ENTER to confirm, ESC to go back",
        small_font,
        GRAY,
        row_y + 20
    )


def draw_pause_menu():

    screen.fill(BLACK)

    draw_text_center("PAUSED", big_font, WHITE, 90)

    for i, option in enumerate(pause_options):

        color = YELLOW if i == pause_index else WHITE

        draw_text_center(option, menu_font, color, 220 + i * 60)

    draw_text_center(
        "UP/DOWN to select, ENTER to confirm, ESC to resume",
        small_font,
        GRAY,
        520
    )


def draw_settings_menu():

    screen.fill(BLACK)

    draw_text_center("SETTINGS", big_font, WHITE, 90)

    vol_percent = int(sound_volume * 100)

    draw_text_center(
        f"Volume: {vol_percent}%   (LEFT / RIGHT to change)",
        font,
        WHITE,
        260
    )

    sound_status = "ON" if sound_on else "OFF"

    draw_text_center(
        f"Sound: {sound_status}   (press M to toggle)",
        font,
        WHITE,
        320
    )

    draw_text_center(
        "Press ESC or BACKSPACE to go back",
        small_font,
        GRAY,
        450
    )


def draw_gameover_menu():

    screen.fill(BLACK)

    if match_outcome == "win":

        draw_text_center("YOU WIN!", big_font, GREEN, 120)

    elif match_outcome == "draw":

        draw_text_center("DRAW", big_font, YELLOW, 120)

    else:

        draw_text_center("GAME OVER", big_font, RED, 120)

    draw_text_center(f"Score : {score}", font, WHITE, 210)

    for i, option in enumerate(gameover_options):

        color = YELLOW if i == gameover_index else WHITE

        draw_text_center(option, menu_font, color, 300 + i * 60)

    draw_text_center(
        "UP/DOWN to select, ENTER to confirm",
        small_font,
        GRAY,
        520
    )



running = True



# -----------------------------
# MAIN GAME LOOP
# -----------------------------

while running:


    # -----------------------------
    # Events
    # -----------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False


        if event.type == pygame.KEYDOWN:


            # -----------------------------
            # PHASE 17: Main Menu input
            # -----------------------------

            if state == STATE_MENU:

                if event.key == pygame.K_SPACE:

                    difficulty_source = "start"
                    state = STATE_SETUP

                elif event.key == pygame.K_s:

                    previous_state = STATE_MENU
                    state = STATE_SETTINGS

                elif event.key == pygame.K_ESCAPE:

                    running = False


            # -----------------------------
            # In-game: open pause menu
            # -----------------------------

            elif state == STATE_PLAYING:

                if event.key == pygame.K_ESCAPE:

                    pause_index = 0
                    state = STATE_PAUSED


            # -----------------------------
            # PHASE 17: Pause Menu input
            # -----------------------------

            elif state == STATE_PAUSED:

                if event.key == pygame.K_UP:

                    pause_index = (pause_index - 1) % len(pause_options)

                elif event.key == pygame.K_DOWN:

                    pause_index = (pause_index + 1) % len(pause_options)

                elif event.key == pygame.K_RETURN:

                    choice = pause_options[pause_index]

                    if choice == "Resume":

                        state = STATE_PLAYING

                    elif choice == "Settings":

                        previous_state = STATE_PAUSED
                        state = STATE_SETTINGS

                    elif choice == "Game Setup":

                        difficulty_source = "pause"
                        state = STATE_SETUP

                    elif choice == "Restart":

                        reset_game()
                        state = STATE_PLAYING

                    elif choice == "Main Menu":

                        state = STATE_MENU

                elif event.key == pygame.K_ESCAPE:

                    state = STATE_PLAYING


            # -----------------------------
            # PHASE 17: Settings Menu input
            # -----------------------------

            elif state == STATE_SETTINGS:

                if event.key == pygame.K_LEFT:

                    sound_volume = max(0.0, round(sound_volume - 0.1, 1))
                    apply_volume()

                elif event.key == pygame.K_RIGHT:

                    sound_volume = min(1.0, round(sound_volume + 0.1, 1))
                    apply_volume()

                elif event.key == pygame.K_m:

                    sound_on = not sound_on
                    apply_volume()

                elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):

                    state = previous_state


            # -----------------------------
            # PHASE 8: Game Setup input
            # -----------------------------

            elif state == STATE_SETUP:

                if event.key == pygame.K_UP:

                    setup_row_index = (setup_row_index - 1) % len(setup_rows)

                elif event.key == pygame.K_DOWN:

                    setup_row_index = (setup_row_index + 1) % len(setup_rows)

                elif event.key == pygame.K_LEFT:

                    cycle_setup_row(setup_row_index, -1)

                elif event.key == pygame.K_RIGHT:

                    cycle_setup_row(setup_row_index, 1)

                elif event.key == pygame.K_RETURN:

                    if difficulty_source == "start":

                        reset_game()
                        state = STATE_PLAYING

                    else:

                        # Mid-game change: re-apply map/obstacles/items
                        # without wiping score, health, or gems
                        active_map_name = current_map_name()
                        walls = list(MAPS[active_map_name])

                        if obstacles_enabled:
                            for _ in range(OBSTACLE_COUNT):
                                ox, oy = spawn_free_point(OBSTACLE_SIZE)
                                walls.append(pygame.Rect(ox, oy, OBSTACLE_SIZE, OBSTACLE_SIZE))

                        state = STATE_PAUSED

                elif event.key == pygame.K_ESCAPE:

                    if difficulty_source == "start":

                        state = STATE_MENU

                    else:

                        state = STATE_PAUSED


            # -----------------------------
            # PHASE 17: Game Over Menu input
            # -----------------------------

            elif state == STATE_GAMEOVER:

                if event.key == pygame.K_UP:

                    gameover_index = (gameover_index - 1) % len(gameover_options)

                elif event.key == pygame.K_DOWN:

                    gameover_index = (gameover_index + 1) % len(gameover_options)

                elif event.key == pygame.K_RETURN:

                    choice = gameover_options[gameover_index]

                    if choice == "Restart":

                        reset_game()
                        state = STATE_PLAYING

                    elif choice == "Main Menu":

                        state = STATE_MENU



    # =====================================================
    # STATE: MAIN MENU
    # =====================================================

    if state == STATE_MENU:

        draw_main_menu()


    # =====================================================
    # STATE: SETTINGS
    # =====================================================

    elif state == STATE_SETTINGS:

        draw_settings_menu()


    # =====================================================
    # STATE: GAME SETUP
    # =====================================================

    elif state == STATE_SETUP:

        draw_setup_menu()


    # =====================================================
    # STATE: PAUSED
    # =====================================================

    elif state == STATE_PAUSED:

        draw_pause_menu()


    # =====================================================
    # STATE: GAME OVER
    # =====================================================

    elif state == STATE_GAMEOVER:

        draw_gameover_menu()


    # =====================================================
    # STATE: PLAYING (original gameplay, fully preserved)
    # =====================================================

    elif state == STATE_PLAYING:


        # -----------------------------
        # Timer
        # -----------------------------

        seconds = (

            pygame.time.get_ticks()
            -
            start_ticks

        ) // 1000



        time_left = max(
            0,
            TIME_LIMIT - seconds
        )



        # -----------------------------
        # Player Movement
        # -----------------------------

        keys = pygame.key.get_pressed()


        new_x = player_x
        new_y = player_y


        moving = False



        if keys[pygame.K_LEFT]:

            new_x -= player_speed
            moving = True



        if keys[pygame.K_RIGHT]:

            new_x += player_speed
            moving = True



        if keys[pygame.K_UP]:

            new_y -= player_speed
            moving = True



        if keys[pygame.K_DOWN]:

            new_y += player_speed
            moving = True




        # -----------------------------
        # Screen Boundary
        # -----------------------------

        new_x = max(
            0,
            min(
                WIDTH - player_size,
                new_x
            )
        )


        new_y = max(
            0,
            min(
                HEIGHT - player_size,
                new_y
            )
        )




        # -----------------------------
        # Wall Collision
        # -----------------------------

        future_player = pygame.Rect(

            new_x,
            new_y,
            player_size,
            player_size

        )


        blocked = False



        for wall in walls:


            if future_player.colliderect(wall):

                blocked = True
                break



        prev_player_x = player_x
        prev_player_y = player_y


        if not blocked:

            player_x = new_x
            player_y = new_y


        # PHASE 18: velocity feeds the AI opponent's prediction
        player_vx = player_x - prev_player_x
        player_vy = player_y - prev_player_y



        # -----------------------------
        # Player Animation
        # -----------------------------

        if moving:


            animation_index += animation_speed


            if animation_index >= len(player_walk):

                animation_index = 0



        else:

            animation_index = 0




        # -----------------------------
        # PHASE 18 + PHASE 8: AI Opponent Movement (Difficulty + Personality)
        # -----------------------------

        diff = DIFFICULTIES[current_difficulty_name()]
        personality = PERSONALITIES[current_personality_name()]

        ai_speed = diff["speed"]
        chase_chance = diff["chase_chance"]
        prediction_frames = diff["prediction"]

        now_ticks = pygame.time.get_ticks()
        enemy_is_stunned = now_ticks < enemy_stun_until

        if enemy_is_stunned:

            # Stunned by a weapon pickup - can't move this frame
            pass

        elif random.random() < chase_chance:

            # Chase: aim at where the player is *heading*, not just
            # where they are right now - the harder the difficulty,
            # the further ahead it aims.

            target_x = player_x + player_vx * prediction_frames
            target_y = player_y + player_vy * prediction_frames

            if personality["guard_gem"] or personality["cutoff"]:

                # Defensive loiters near the gem; Tactical aims for a
                # point between the player and the gem to cut off the
                # path rather than tailing directly
                target_x = (target_x + gem_x) / 2
                target_y = (target_y + gem_y) / 2

            target_x = max(0, min(WIDTH - player_size, target_x))
            target_y = max(0, min(HEIGHT - player_size, target_y))

            dx = target_x - enemy_x
            dy = target_y - enemy_y

            dist = math.hypot(dx, dy)

            if dist > 0:

                move_x = (dx / dist) * ai_speed
                move_y = (dy / dist) * ai_speed

            else:

                move_x = 0
                move_y = 0

            if personality["jitter"] > 0:

                move_x += random.uniform(-personality["jitter"], personality["jitter"])
                move_y += random.uniform(-personality["jitter"], personality["jitter"])

            enemy_x, enemy_y = resolve_enemy_move(
                enemy_x,
                enemy_y,
                move_x,
                move_y
            )

            # keep patrol direction sensible if it drops back to patrolling
            direction = 1 if move_x >= 0 else -1


        else:

            # Old patrol behavior - predictable side-to-side sweep
            enemy_x += ai_speed * direction

            if enemy_x <= 0:

                direction = 1

            if enemy_x >= WIDTH - enemy_size:

                direction = -1




        # -----------------------------
        # Rectangles
        # -----------------------------

        player_rect = pygame.Rect(

            player_x,
            player_y,
            player_size,
            player_size

        )


        enemy_rect = pygame.Rect(

            enemy_x,
            enemy_y,
            enemy_size,
            enemy_size

        )


        gem_rect = pygame.Rect(

            gem_x,
            gem_y,
            gem_size,
            gem_size

        )



        # -----------------------------
        # GEM COLLECTION
        # -----------------------------

        if player_rect.colliderect(gem_rect):


            score += 10


            gems_collected += 1



            # 🔊 Gem sound

            gem_sound.play()



            gem_x, gem_y = spawn_gem()


        # -----------------------------
        # PHASE 8: ITEM PICKUPS
        # -----------------------------

        if items_enabled:

            now_ticks = pygame.time.get_ticks()

            if weapon_pos and player_rect.colliderect(pygame.Rect(*weapon_pos, item_size, item_size)):

                if current_game_mode() == "Deathmatch":
                    # In Deathmatch the weapon arms the player instead
                    # of stunning - contact while armed damages the enemy
                    player_armed_until = now_ticks + ARMED_DURATION_MS
                else:
                    enemy_stun_until = now_ticks + STUN_DURATION_MS

                gem_sound.play()
                weapon_pos = spawn_free_point(item_size, avoid_rects=[gem_rect])

            if shield_pos and player_rect.colliderect(pygame.Rect(*shield_pos, item_size, item_size)):

                player_shield_until = now_ticks + SHIELD_DURATION_MS
                gem_sound.play()
                shield_pos = spawn_free_point(item_size, avoid_rects=[gem_rect])

            if heal_pos and player_rect.colliderect(pygame.Rect(*heal_pos, item_size, item_size)):

                health = min(100, health + HEAL_AMOUNT)
                gem_sound.play()
                heal_pos = spawn_free_point(item_size, avoid_rects=[gem_rect])



        # -----------------------------
        # ENEMY COLLISION
        # -----------------------------

        current_time = pygame.time.get_ticks()

        player_shielded = current_time < player_shield_until
        player_armed = current_time < player_armed_until


        if player_rect.colliderect(enemy_rect):


            if current_time - last_hit_time > diff["cooldown_ms"]:


                if not player_shielded:

                    health -= 10

                    # 🔊 Enemy hit sound

                    enemy_sound.play()


                if current_game_mode() == "Deathmatch":

                    enemy_health -= 10

                    if not player_shielded:
                        # both took a hit this exchange
                        pass

                elif player_armed:

                    # Weapon-armed contact in non-Deathmatch modes just
                    # stuns, matching the pickup effect above
                    enemy_stun_until = current_time + STUN_DURATION_MS


                last_hit_time = current_time
        # -----------------------------
        # Draw Background
        # -----------------------------

        screen.fill(BLACK)



        # -----------------------------
        # Draw Walls
        # -----------------------------

        for wall in walls:

            scaled_wall_img = pygame.transform.scale(
                wall_img,
                (wall.width, wall.height)
            )

            screen.blit(
                scaled_wall_img,
                (
                    wall.x,
                    wall.y
                )
            )



        # -----------------------------
        # PHASE 8: Draw Items
        # -----------------------------

        if items_enabled:

            if weapon_pos:
                pygame.draw.rect(screen, (255, 140, 0), (*weapon_pos, item_size, item_size))
                screen.blit(small_font.render("W", True, BLACK), (weapon_pos[0] + 8, weapon_pos[1] + 4))

            if shield_pos:
                pygame.draw.rect(screen, (0, 220, 220), (*shield_pos, item_size, item_size))
                screen.blit(small_font.render("S", True, BLACK), (shield_pos[0] + 8, shield_pos[1] + 4))

            if heal_pos:
                pygame.draw.rect(screen, (255, 0, 200), (*heal_pos, item_size, item_size))
                screen.blit(small_font.render("H", True, BLACK), (heal_pos[0] + 8, heal_pos[1] + 4))



        # -----------------------------
        # Draw Gem
        # -----------------------------

        screen.blit(
            gem_img,
            (
                gem_x,
                gem_y
            )
        )



        # -----------------------------
        # Draw Enemy (hidden if Fog of War is on and out of range)
        # -----------------------------

        enemy_visible = True

        if fog_enabled:
            enemy_dist = math.hypot(enemy_x - player_x, enemy_y - player_y)
            enemy_visible = enemy_dist <= VISION_RADIUS

        if enemy_visible:

            screen.blit(
                enemy_img,
                (
                    enemy_x,
                    enemy_y
                )
            )



        # -----------------------------
        # Draw Player Animation
        # -----------------------------

        screen.blit(

            player_walk[
                int(animation_index)
            ],

            (
                player_x,
                player_y
            )

        )



        # -----------------------------
        # Score Display
        # -----------------------------

        score_text = font.render(

            f"Score : {score}",

            True,

            WHITE

        )


        screen.blit(
            score_text,
            (10, 10)
        )



        # -----------------------------
        # Health Display
        # -----------------------------

        health_text = font.render(

            f"Health : {health}",

            True,

            WHITE

        )


        screen.blit(
            health_text,
            (10, 45)
        )



        # -----------------------------
        # Gem Display
        # -----------------------------

        gem_text = font.render(

            f"Gems : {gems_collected}/{TARGET_GEMS}",

            True,

            WHITE

        )


        screen.blit(
            gem_text,
            (10, 80)
        )



        # -----------------------------
        # Timer Display
        # -----------------------------

        timer_text = font.render(

            f"Time : {time_left}",

            True,

            WHITE

        )


        screen.blit(
            timer_text,
            (10, 115)
        )


        # -----------------------------
        # PHASE 18 + PHASE 8: Setup Display
        # -----------------------------

        setup_text = small_font.render(
            f"{current_difficulty_name()} | {current_personality_name()} | "
            f"{active_map_name} | {current_game_mode()}",
            True,
            GRAY
        )

        screen.blit(
            setup_text,
            (10, 150)
        )


        # -----------------------------
        # PHASE 8: Deathmatch enemy health
        # -----------------------------

        if current_game_mode() == "Deathmatch":

            enemy_health_text = font.render(
                f"Enemy HP : {enemy_health}",
                True,
                WHITE
            )

            screen.blit(enemy_health_text, (10, 180))


        # -----------------------------
        # PHASE 8: Status effect indicators
        # -----------------------------

        status_bits = []

        if items_enabled:
            if pygame.time.get_ticks() < player_shield_until:
                status_bits.append("SHIELDED")
            if pygame.time.get_ticks() < player_armed_until:
                status_bits.append("ARMED")
            if pygame.time.get_ticks() < enemy_stun_until:
                status_bits.append("ENEMY STUNNED")

        if status_bits:

            status_text = small_font.render(
                " | ".join(status_bits),
                True,
                YELLOW
            )

            screen.blit(status_text, (10, 210))


        # -----------------------------
        # PHASE 17: Pause hint
        # -----------------------------

        pause_hint = small_font.render(
            "ESC to pause",
            True,
            GRAY
        )

        screen.blit(
            pause_hint,
            (10, 240)
        )



        # -----------------------------
        # PHASE 8: WIN / LOSE CONDITIONS (mode-aware)
        # -----------------------------

        mode = current_game_mode()

        match_ended = False


        if mode == "Classic":

            if gems_collected >= TARGET_GEMS:

                win_sound.play()
                match_outcome = "win"
                match_ended = True

            elif health <= 0:

                match_outcome = "lose"
                match_ended = True

            elif time_left <= 0:

                match_outcome = "lose"
                match_ended = True


        elif mode == "Survival":

            if health <= 0:

                match_outcome = "lose"
                match_ended = True

            elif time_left <= 0:

                # Survived the full timer - that's the win condition here
                win_sound.play()
                match_outcome = "win"
                match_ended = True


        elif mode == "Deathmatch":

            if health <= 0 and enemy_health <= 0:

                match_outcome = "draw"
                match_ended = True

            elif health <= 0:

                match_outcome = "lose"
                match_ended = True

            elif enemy_health <= 0:

                win_sound.play()
                match_outcome = "win"
                match_ended = True

            elif time_left <= 0:

                if health > enemy_health:
                    match_outcome = "win"
                elif enemy_health > health:
                    match_outcome = "lose"
                else:
                    match_outcome = "draw"

                match_ended = True


        if match_ended:

            gameover_index = 0
            state = STATE_GAMEOVER




    # -----------------------------
    # Update Display
    # -----------------------------

    pygame.display.update()



    # -----------------------------
    # FPS
    # -----------------------------

    clock.tick(60)




# -----------------------------
# Quit Game
# -----------------------------

pygame.quit()