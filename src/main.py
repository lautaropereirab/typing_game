import pygame
import random

vec = pygame.math.Vector2

# -------------------------
# Helper funcs
# -------------------------
def spawn_outside_screen():
    side = random.choice(["top", "bottom", "left", "right"])
    margin = EnemySize

    if side == "top":
        x = random.randint(0, SCREEN_WIDTH)
        y = -margin
    elif side == "bottom":
        x = random.randint(0, SCREEN_WIDTH)
        y = SCREEN_HEIGHT + margin
    elif side == "left":
        x = -margin
        y = random.randint(0, SCREEN_HEIGHT)
    else:
        x = SCREEN_WIDTH + margin
        y = random.randint(0, SCREEN_HEIGHT)

    return vec(x, y)


def draw_text_with_outline(surface, text, font, color, outline_color, position):
    base = font.render(text, True, color)
    outline = font.render(text, True, outline_color)

    x, y = position

    surface.blit(outline, (x - 2, y))
    surface.blit(outline, (x + 2, y))
    surface.blit(outline, (x, y - 2))
    surface.blit(outline, (x, y + 2))
    surface.blit(base, (x, y))


def word_generator(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read().split()


def random_word_selector(lista):
    return random.choice(lista)


def EnemySearcher(enemy_group, prefix):
    return [e for e in enemy_group if e.word.startswith(prefix)]


# -------------------------
# Init
# -------------------------
pygame.init()
pygame.font.init()
pygame.key.start_text_input()

pygame.display.set_caption("Word Menace")
clock = pygame.time.Clock()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

SPANISH_WORDS_PATH = "assets/words/spanish_words.txt"
SPAWN_DELAY = 2000

BackgroundImage = pygame.image.load("assets/images/Background.png").convert()
BackgroundImage = pygame.transform.scale(BackgroundImage, (SCREEN_WIDTH, SCREEN_HEIGHT))
HeartImage = pygame.image.load("assets/images/heart.png").convert_alpha()
HeartSize = 85
HeartImage = pygame.transform.scale(HeartImage, (HeartSize, HeartSize))

# -------------------------
# Fonts
# -------------------------
PixelFontSmall = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)
PixelFontMedium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 22)
PixelFontLarge = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 30)

WordFont = PixelFontSmall
InputFont = PixelFontMedium
ScoreFont = PixelFontSmall
StageFont = PixelFontLarge
LivesFont = PixelFontSmall

UserInputText = ""

# -------------------------
# Variables
# -------------------------
PlayerSize = 150
EnemySize = 50
EnemySpeed = 1.5
EnemyMaxSpeed = 10

last_spawn_time = 0
enemies = pygame.sprite.Group()

Score = 0
StageCounter = 1
Lives = 3

lockedEnemy = None
candidates = None
input_error = False

cursor_visible = True
CURSOR_BLINK_MS = 500
last_cursor_toggle = 0

BOX_WIDTH = int(SCREEN_WIDTH * 0.2)
BOX_HEIGHT = int(InputFont.get_height() * 1.5)
BOX_Y = SCREEN_HEIGHT - 90

TextBox = pygame.Rect(0, 0, BOX_WIDTH, BOX_HEIGHT)
TextBox.centerx = SCREEN_WIDTH // 2
TextBox.y = BOX_Y

RandomWordList = word_generator(SPANISH_WORDS_PATH)

# -------------------------
# Player
# -------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        img = pygame.image.load("assets/images/PlayerImage.png").convert_alpha()
        self.image = pygame.transform.smoothscale(img, (PlayerSize, PlayerSize))
        self.rect = self.image.get_rect()
        self.pos = vec(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.rect.center = self.pos

    def draw(self, surface):
        surface.blit(self.image, self.rect)


# -------------------------
# Enemy
# -------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, word):
        super().__init__()

        img = pygame.image.load("assets/images/EnemyImage.png").convert_alpha()
        self.image = pygame.transform.smoothscale(img, (EnemySize, EnemySize))
        self.rect = self.image.get_rect()

        self.word = word
        self.pos = spawn_outside_screen()
        self.rect.center = self.pos

    def update(self, target):
        direction = vec(target.pos) - self.pos
        if direction.length() != 0:
            self.pos += direction.normalize() * EnemySpeed
        self.rect.center = self.pos

    def draw(self, surface, locked_enemy):
        surface.blit(self.image, self.rect)

        text_rect = WordFont.render(self.word, True, (255,255,255)).get_rect()
        text_rect.midbottom = self.rect.midtop

        x_offset = text_rect.x

        for i, letter in enumerate(self.word):

            if self == locked_enemy and i < len(UserInputText):
                color = (0, 255, 0)
            elif self == locked_enemy:
                color = (255, 255, 255)
            else:
                color = (0, 255, 255)

            letter_surface = WordFont.render(letter, True, color)
            outline_surface = WordFont.render(letter, True, (0, 0, 0))

            letter_rect = letter_surface.get_rect()
            letter_rect.topleft = (x_offset, text_rect.y)

            surface.blit(outline_surface, (letter_rect.x - 1, letter_rect.y))
            surface.blit(outline_surface, (letter_rect.x + 1, letter_rect.y))
            surface.blit(outline_surface, (letter_rect.x, letter_rect.y - 1))
            surface.blit(outline_surface, (letter_rect.x, letter_rect.y + 1))

            surface.blit(letter_surface, letter_rect)

            x_offset += letter_rect.width


P1 = Player()

# -------------------------
# GAME LOOP
# -------------------------
running = True
while running:

    if Lives == 0:
        running = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.TEXTINPUT:
            ch = event.text
            proposed = UserInputText + ch
            input_error = False

            if lockedEnemy is not None:
                if lockedEnemy.word.startswith(proposed):
                    UserInputText = proposed

                    if UserInputText == lockedEnemy.word:
                        Score += 1
                        lockedEnemy.kill()
                        lockedEnemy = None
                        candidates = None
                        UserInputText = ""
                else:
                    if (StageCounter == 1) and (Score < 0):
                        Lives -=1
                    elif (StageCounter == 1) and (Score >= 0):
                        Score -= 1

                    if (StageCounter == 2) and (Score < 10):
                        Lives -= 1
                    elif (StageCounter == 2) and (Score >= 10):
                        Score -= 1

                    if (StageCounter == 3) and (Score < 20):
                        Lives -= 1
                    elif (StageCounter == 3) and (Score >= 20):
                        Score -= 1
                    
                    input_error = True
                    lockedEnemy = None
                    candidates = None
                    UserInputText = ""

            else:
                if candidates is None:
                    candidates = EnemySearcher(enemies, proposed)
                else:
                    candidates = [e for e in candidates if e.word.startswith(proposed)]

                if not candidates:
                    input_error = True
                    candidates = None
                    UserInputText = ""
                else:
                    UserInputText = proposed
                    if len(candidates) == 1:
                        lockedEnemy = candidates[0]
                        candidates = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                UserInputText = UserInputText[:-1]
                lockedEnemy = None
                input_error = False

                if UserInputText == "":
                    candidates = None
                else:
                    candidates = EnemySearcher(enemies, UserInputText)
                    if len(candidates) == 1:
                        lockedEnemy = candidates[0]
                        candidates = None

    current_time = pygame.time.get_ticks()
    if current_time - last_spawn_time >= SPAWN_DELAY:
        enemies.add(Enemy(random_word_selector(RandomWordList)))
        last_spawn_time = current_time

    if Score >= 10 and StageCounter == 1:
        enemies.empty()
        lockedEnemy = None
        candidates = None
        StageCounter = 2

    if Score >= 20 and StageCounter == 2:
        enemies.empty()
        lockedEnemy = None
        candidates = None
        StageCounter = 3

    # ---------------- DRAW ----------------
    DISPLAYSURF.blit(BackgroundImage, (0, 0))

    # -------- STAGE --------
    stage_text = f"STAGE {StageCounter}"
    stage_rect = StageFont.render(stage_text, True, (200,100,255)).get_rect(center=(SCREEN_WIDTH//2, 25))
    draw_text_with_outline(
        DISPLAYSURF,
        stage_text,
        StageFont,
        (200,100,255),  # color principal
        (0,0,0),        # outline
        (stage_rect.x, stage_rect.y)
    )

    # ❤️ LIVES (ahora arriba, donde estaba SCORE)
    heart_spacing = 10
    total_width = Lives * HeartSize + (Lives - 1) * heart_spacing
    start_x = SCREEN_WIDTH // 2 - total_width // 2
    y_pos = 55

    for i in range(Lives):
        x = start_x + i * (HeartSize + heart_spacing)
        DISPLAYSURF.blit(HeartImage, (x, y_pos))


    # SCORE (ahora abajo, donde estaban las vidas)
    score_text = f"SCORE {Score}"
    score_rect = ScoreFont.render(score_text, True, (0,255,255)).get_rect(center=(SCREEN_WIDTH//2, TextBox.y - 30))
    draw_text_with_outline(DISPLAYSURF, score_text, ScoreFont, (0,255,255), (0,0,0), (score_rect.x, score_rect.y))

    # Cursor blink
    now = pygame.time.get_ticks()
    if now - last_cursor_toggle >= CURSOR_BLINK_MS:
        cursor_visible = not cursor_visible
        last_cursor_toggle = now

    # Textbox
    bg_color = (230, 230, 230)
    border_color = (200, 50, 50) if input_error else (40, 40, 40)

    pygame.draw.rect(DISPLAYSURF, bg_color, TextBox, border_radius=10)
    pygame.draw.rect(DISPLAYSURF, border_color, TextBox, width=2, border_radius=10)

    text_surface = InputFont.render(UserInputText, True, (20, 20, 20))
    text_rect = text_surface.get_rect(center=TextBox.center)
    DISPLAYSURF.blit(text_surface, text_rect)

    if cursor_visible:
        cursor_surface = InputFont.render("|", True, (20, 20, 20))
        cursor_rect = cursor_surface.get_rect()
        cursor_rect.midleft = (text_rect.right + 2, TextBox.centery)

        prev_clip = DISPLAYSURF.get_clip()
        DISPLAYSURF.set_clip(TextBox)
        DISPLAYSURF.blit(cursor_surface, cursor_rect)
        DISPLAYSURF.set_clip(prev_clip)

    P1.draw(DISPLAYSURF)
    enemies.update(P1)

# ---------------- COLLISION LOGIC ----------------
    for enemy in enemies.copy():
        if enemy.rect.colliderect(P1.rect):
            enemy.kill()
            Lives -= 1

            lockedEnemy = None
            candidates = None
            UserInputText = ""
            input_error = False

            if Lives <= 0:
                running = False

    for enemy in enemies:
        enemy.draw(DISPLAYSURF, lockedEnemy)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()