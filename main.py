import pygame, random, math, os, array

pygame.init()
win = pygame.display.set_mode((0, 0))
pygame.display.set_caption("GOLD RAIN")
WW, WH = win.get_size()

# ====== إعدادات (غيّرها براحتك) ======
SCALE = 0.7            # دقة اللعبة: 0.5 أخف، 0.8 أحلى
STAR_COUNT = 25        # عدد النجوم
MAX_ENEMIES = 5        # أقصى عدد أعداء عاديين
LEVEL_FRAMES = 60 * 6  # مستوى جديد كل 8 ثواني
BOSS_LEVEL = 25        # البوس بيظهر في الليفل ده (وكل مضاعفاته)
RAIN_DMG = 3           # ضرر المطر في الفريم
ENEMY_SPEED = 3      # سرعة الأعداء في البداية
SPEED_PER_LEVEL = 1  # زيادة السرعة مع كل ليفل
MAX_SPEED = 17         # أقصى سرعة
ZONE_LEVELS = 5        # الخلفية بتتغير كل كام ليفل
START_LEVEL = 1        # للتجربة: ابدأ من ليفل 14 مثلا عشان تشوف الأعداء الجداد
SOUND = True           # False لو عايز تقفل الصوت
# =====================================

W, H = int(WW * SCALE), int(WH * SCALE)
kx, ky = W / WW, H / WH
screen = pygame.Surface((W, H))
clock = pygame.time.Clock()
u = min(W, H) / 720
font = pygame.font.SysFont(None, int(40 * u))
small = pygame.font.SysFont(None, int(26 * u))
big = pygame.font.SysFont(None, int(96 * u))

GOLD = (255, 200, 40)
BTN = pygame.Rect(W - int(110 * u), H - int(110 * u), int(90 * u), int(90 * u))
PR = int(18 * u)
RAIN_R = int(300 * u)

# ---------- أنواع الأعداء ----------
ET = {
    0: dict(col=(220, 50, 60),  gl=(255, 70, 70),   n=4,  sz=1.0,  hp=1.0, sp=1.0,  flee=True),    # مطارد
    1: dict(col=(255, 140, 30), gl=(255, 170, 60),  n=4,  sz=1.0,  hp=1.0, sp=1.0,  flee=True),    # متوقّع
    2: dict(col=(180, 60, 220), gl=(220, 90, 255),  n=4,  sz=1.0,  hp=1.0, sp=1.0,  flee=True),    # محاصِر
    3: dict(col=(30, 200, 200), gl=(80, 255, 240),  n=3,  sz=1.05, hp=0.9, sp=0.7,  flee=True),    # مندفع
    4: dict(col=(150, 210, 40), gl=(190, 255, 70),  n=5,  sz=1.0,  hp=0.8, sp=0.85, flee=True),    # قنّاص
    5: dict(col=(255, 100, 170), gl=(255, 150, 210), n=6, sz=1.2,  hp=1.3, sp=0.9,  flee=True),    # منقسم
    6: dict(col=(80, 110, 200), gl=(120, 150, 255), n=8,  sz=1.7,  hp=1.2, sp=0.5,  flee=False),   # دبابة
    7: dict(col=(255, 130, 190), gl=(255, 170, 215), n=3, sz=0.6,  hp=0.3, sp=1.2,  flee=False),   # صغير
    8: dict(col=(190, 30, 80),  gl=(255, 60, 140),  n=6,  sz=3.2,  hp=1.0, sp=0.35, flee=False),   # البوس
    9: dict(col=(200, 150, 60), gl=(255, 210, 90),  n=7,  sz=0.9,  hp=0.7, sp=1.3,  flee=True, harm=False),  # اللص
    10: dict(col=(150, 170, 255), gl=(200, 215, 255), n=10, sz=1.0, hp=0.8, sp=0.95, flee=True),   # الشبح
    11: dict(col=(40, 200, 140), gl=(90, 255, 190), n=6,  sz=1.1,  hp=1.0, sp=0.8,  flee=True),    # الحامي
}
# (النوع، من أي ليفل)
UNLOCK = ((1, 2), (2, 3), (3, 5), (9, 6), (4, 8), (10, 10), (5, 12), (11, 14), (6, 16))

# ---------- خلفيات الزونات (بتتغير كل ZONE_LEVELS ليفل) ----------
THEMES = (((12, 10, 35), (32, 18, 65)),    # بنفسجي ليلي
          ((8, 32, 40), (14, 70, 80)),     # أزرق محيط
          ((38, 10, 22), (80, 22, 44)),    # أحمر داكن
          ((16, 36, 16), (36, 74, 34)),    # أخضر غابة
          ((34, 18, 10), (86, 46, 18)))    # برتقالي صحراء


def make_bg(t):
    s = pygame.Surface((W, H))
    c0, c1 = t
    for yy in range(H):
        kk = yy / H
        col = tuple(int(c0[i] + (c1[i] - c0[i]) * kk) for i in range(3))
        pygame.draw.line(s, col, (0, yy), (W, yy))
    return s.convert()


bgs = [make_bg(t) for t in THEMES]
stars = [[random.uniform(0, W), random.uniform(0, H), random.choice([1, 1, 2, 3]),
          random.uniform(0, 6.28), random.uniform(0.2, 0.8)] for _ in range(STAR_COUNT)]

# ---------- أسطح جاهزة ----------
rain_surf = pygame.Surface((RAIN_R * 2, RAIN_R * 2), pygame.SRCALPHA)
pygame.draw.circle(rain_surf, GOLD + (28,), (RAIN_R, RAIN_R), RAIN_R)
pygame.draw.circle(rain_surf, GOLD + (140,), (RAIN_R, RAIN_R), RAIN_R, max(2, int(3 * u)))
overlay = pygame.Surface((W, H), pygame.SRCALPHA)
overlay.fill((0, 0, 0, 150))

glow_cache = {}


def glow(x, y, r, color):
    r = max(8, int(r) // 8 * 8)
    s = glow_cache.get((r, color))
    if s is None:
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -6):
            a = int(110 * (1 - i / r) ** 2)
            pygame.draw.circle(s, color + (a,), (r, r), i)
        glow_cache[(r, color)] = s
    screen.blit(s, (int(x) - r, int(y) - r))


tcache = {}


def text(f, s, col, pos, center=True, alpha=255):
    key = (id(f), s, col)
    v = tcache.get(key)
    if v is None:
        if len(tcache) > 150:
            tcache.clear()
        v = (f.render(s, True, col), f.render(s, True, (0, 0, 0)))
        tcache[key] = v
    img, shadow = v
    img.set_alpha(alpha)
    shadow.set_alpha(alpha)
    r = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
    screen.blit(shadow, (r.x + 2, r.y + 2))
    screen.blit(img, r)


# ---------- أعلى سكور ----------
try:
    HS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")
except Exception:
    HS_FILE = "highscore.txt"


def load_hs():
    try:
        with open(HS_FILE) as f:
            return int(f.read())
    except Exception:
        return 0


def save_hs(v):
    try:
        with open(HS_FILE, "w") as f:
            f.write(str(v))
    except Exception:
        pass


highscore = load_hs()

# ---------- الصوت (متولّد بالكود) ----------
RATE = 22050
try:
    pygame.mixer.quit()
    pygame.mixer.init(RATE, -16, 1, 512)
    pygame.mixer.set_num_channels(16)
    SOUND_ON = SOUND
except Exception:
    SOUND_ON = False


def tone(f0, f1, dur, vol=0.4, wave="sine", noise=0.0):
    n = int(RATE * dur)
    out = array.array("h")
    ph = 0.0
    for i in range(n):
        k = i / n
        ph += 6.2832 * (f0 + (f1 - f0) * k) / RATE
        if wave == "sine":
            s = math.sin(ph)
        elif wave == "square":
            s = 1.0 if math.sin(ph) > 0 else -1.0
        else:
            s = (ph / math.pi) % 2 - 1
        if noise:
            s = s * (1 - noise) + random.uniform(-1, 1) * noise
        out.append(int(s * (1 - k) ** 2 * vol * 32767))
    return out


def make_snd(f0, f1, dur, vol=0.4, wave="sine", noise=0.0):
    return pygame.mixer.Sound(buffer=tone(f0, f1, dur, vol, wave, noise).tobytes())


def make_seq(notes, vol=0.4, wave="sine"):
    out = array.array("h")
    for f, d in notes:
        out.extend(tone(f, f, d, vol, wave))
    return pygame.mixer.Sound(buffer=out.tobytes())


def sfx(s):
    if SOUND_ON and s is not None:
        try:
            s.play()
        except Exception:
            pass


S_COIN = [None] * 5
S_RAIN = S_KILL = S_HURT = S_SHOOT = S_READY = S_STEAL = None
S_LEVEL = S_BOSS = S_BOSSDEAD = S_OVER = None

if SOUND_ON:
    try:
        S_COIN = [make_snd(700 + i * 130, 1000 + i * 180, 0.12, 0.3) for i in range(5)]
        S_RAIN = make_snd(200, 900, 0.7, 0.4, "saw", 0.4)
        S_KILL = make_snd(300, 60, 0.18, 0.3, "square", 0.3)
        S_HURT = make_snd(220, 60, 0.3, 0.5, "saw", 0.4)
        S_SHOOT = make_snd(900, 400, 0.08, 0.2, "square")
        S_READY = make_snd(660, 990, 0.15, 0.3)
        S_STEAL = make_snd(600, 200, 0.2, 0.3, "square")
        S_LEVEL = make_seq([(523, 0.08), (659, 0.08), (784, 0.14)], 0.35)
        S_BOSS = make_seq([(110, 0.25), (98, 0.25), (82, 0.4)], 0.5, "saw")
        S_BOSSDEAD = make_seq([(392, 0.1), (523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.3)], 0.4)
        S_OVER = make_seq([(440, 0.15), (370, 0.15), (294, 0.15), (220, 0.4)], 0.4, "square")
    except Exception:
        SOUND_ON = False
# ---------- أدوات ----------
def spawn_coin(pop=0.0):
    return [random.randint(40, W - 40), random.randint(40, H - 40),
            random.uniform(0, 6.28), pop]


def burst(x, y, color, n=12, size=3):
    n = max(2, n // 2)
    for _ in range(n):
        a = random.uniform(0, 6.28)
        s = random.uniform(1.5, 6) * u
        particles.append([x, y, math.cos(a) * s, math.sin(a) * s,
                          random.randint(18, 34), color, size * u])


def popup(x, y, s, color):
    texts.append([x, y, s, 45, color])


def shoot(x, y, ang, spd, col):
    bullets.append([x, y, math.cos(ang) * spd, math.sin(ang) * spd, 240, col])


def hurt():
    global lives, inv, shake, over
    lives -= 1
    inv = 90
    shake = 14
    sfx(S_HURT)
    burst(px, py, (0, 200, 255), 18)
    if lives <= 0:
        over = True


def make_enemy(kind, x, y, hp):
    return {"x": x, "y": y, "hp": hp, "max": hp, "kind": kind,
            "a": random.uniform(0, 6.28), "rot": random.uniform(0, 6.28),
            "born": 0, "flash": 0, "cd": random.randint(40, 90),
            "state": 0, "st": 0, "dx": 0.0, "dy": 0.0,
            "shielded": False, "tgt": None, "carry": False, "escaped": False}


def spawn_enemy(lv):
    for _ in range(12):
        x = random.randint(int(50 * u), W - int(50 * u))
        y = random.randint(int(50 * u), H - int(50 * u))
        if math.hypot(x - px, y - py) > 260 * u:
            break
    kinds = [0]
    for kd, from_lv in UNLOCK:
        if lv >= from_lv:
            kinds.append(kd)
    kd = random.choice(kinds)
    hp = max(10, int((35 + lv * 6) * ET[kd]["hp"]))
    return make_enemy(kd, x, y, hp)


def spawn_boss():
    return make_enemy(8, W / 2, H * 0.25, 320 + 150 * boss_no)


def reset():
    global px, py, vx, vy, lives, inv, score, energy, frames, coins, enemies
    global particles, texts, trail, rain, touching, over, spawn_t, level, saved
    global shake, banner, new_best, over_t
    global combo, combo_t
    global bullets, boss, next_boss, boss_no, banner_txt
    global cur_theme, prev_theme, fade, banner_zone
    px, py, vx, vy = W / 2, H / 2, 0.0, 0.0
    lives, inv, score, energy = 3, 0, 0, 0
    frames = (START_LEVEL - 1) * LEVEL_FRAMES
    coins = [spawn_coin(1.0) for _ in range(4)]
    enemies, particles, texts, trail, bullets = [], [], [], [], []
    rain, touching, over, spawn_t = 0, False, False, 0
    level, saved = START_LEVEL, False
    shake, banner, new_best, over_t = 0, 0, False, 0
    combo, combo_t = 0, 0
    boss, next_boss, boss_no, banner_txt = None, BOSS_LEVEL, 0, ""
    cur_theme = prev_theme = ((START_LEVEL - 1) // ZONE_LEVELS) % len(bgs)
    fade, banner_zone = 0, False


# ---------- الرسم ----------
def draw_hero():
    x, y = px, py
    n = len(trail)
    for i, (tx, ty) in enumerate(trail):
        k = i / max(1, n)
        pygame.draw.circle(screen, (int(10 + 10 * k), int(30 + 90 * k), int(60 + 130 * k)),
                           (int(tx), int(ty)), max(1, int(PR * k * 0.75)))
    if rain > 0:
        glow(x, y, PR * 4 + math.sin(tick * 0.3) * 6 * u, GOLD)
    glow(x, y, PR * 3, (0, 180, 255))
    r = PR + math.sin(tick * 0.12) * 1.5 * u
    ri = int(r)
    pygame.draw.circle(screen, (0, 200, 255), (int(x), int(y)), ri)
    pygame.draw.circle(screen, (0, 140, 210), (int(x), int(y)), ri, max(2, int(3 * u)))
    pygame.draw.circle(screen, (170, 240, 255), (int(x - r * 0.4), int(y - r * 0.5)), max(1, int(r * 0.22)))
    lx, ly = vx, vy
    best = 1e9
    for en in enemies:
        d = math.hypot(en["x"] - x, en["y"] - y)
        if d < best:
            best, lx, ly = d, en["x"] - x, en["y"] - y
    m = math.hypot(lx, ly)
    lx, ly = (lx / m, ly / m) if m > 0.01 else (0, 0)
    for sgn in (-1, 1):
        ex, ey = x + sgn * r * 0.38, y - r * 0.02
        pygame.draw.circle(screen, (255, 255, 255), (int(ex), int(ey)), max(2, int(r * 0.3)))
        pygame.draw.circle(screen, (10, 20, 50),
                           (int(ex + lx * r * 0.1), int(ey + ly * r * 0.1)), max(1, int(r * 0.15)))


def draw_enemy(en):
    x, y = en["x"], en["y"]
    kd = en["kind"]
    et = ET[kd]
    base, gl = et["col"], et["gl"]
    sc = min(1.0, en["born"] / 40)
    h = 15 * u * et["sz"] * sc * (1 + 0.06 * math.sin(tick * 0.2 + en["a"]))
    if en["born"] < 40:
        pygame.draw.circle(screen, gl, (int(x), int(y)), int(40 * u * et["sz"] * (1 - sc) + 4), 2)

    # الشبح: مخفي إلا لو قريب منك أو جوه المطر أو اتضرب
    if kd == 10 and en["born"] >= 40:
        dp = math.hypot(px - x, py - y)
        visible = en["flash"] > 0 or dp < 230 * u or (rain > 0 and dp < RAIN_R)
        if not visible:
            pygame.draw.circle(screen, (70, 80, 125), (int(x), int(y)),
                               int(h * 1.5 + math.sin(tick * 0.3) * 3 * u), 1)
            return

    if kd == 3 and en["state"] == 1:   # خط تحذير قبل الاندفاع
        pygame.draw.line(screen, gl, (int(x), int(y)),
                         (int(x + en["dx"] * 450 * u), int(y + en["dy"] * 450 * u)), max(2, int(3 * u)))
    glow(x, y, h * 3, gl)
    n = et["n"]
    pts = [(x + math.cos(en["rot"] + i * 6.2832 / n) * h * 1.35,
            y + math.sin(en["rot"] + i * 6.2832 / n) * h * 1.35) for i in range(n)]
    col = (255, 255, 255) if en["flash"] > 0 else base
    pygame.draw.polygon(screen, col, pts)
    pygame.draw.polygon(screen, (int(base[0] * 0.5), int(base[1] * 0.5), int(base[2] * 0.5)), pts, 2)
    dx, dy = px - x, py - y
    m = math.hypot(dx, dy) + 0.001
    for sgn in (-1, 1):
        ex, ey = x + sgn * h * 0.4, y - h * 0.1
        pygame.draw.circle(screen, (255, 255, 255), (int(ex), int(ey)), max(2, int(h * 0.3)))
        pygame.draw.circle(screen, (20, 0, 0), (int(ex + dx / m * h * 0.12), int(ey + dy / m * h * 0.12)),
                           max(1, int(h * 0.15)))
        pygame.draw.line(screen, (30, 0, 0), (x + sgn * h * 0.75, y - h * 0.62),
                         (x + sgn * h * 0.12, y - h * 0.32), max(2, int(2 * u)))
    # اللص شايل عملة
    if kd == 9 and en["carry"]:
        cy2 = int(y - h * 2.1 + math.sin(tick * 0.3) * 2 * u)
        pygame.draw.circle(screen, GOLD, (int(x), cy2), max(4, int(7 * u)))
        pygame.draw.circle(screen, (200, 140, 20), (int(x), cy2), max(4, int(7 * u)), 2)
    # درع الحامي
    if en["shielded"]:
        rr = int(h * 2.4 + math.sin(tick * 0.25) * 3 * u)
        pygame.draw.circle(screen, (80, 255, 190), (int(x), int(y)), rr, max(2, int(3 * u)))
        pygame.draw.circle(screen, (40, 150, 110), (int(x), int(y)), rr - max(3, int(5 * u)), 1)
    if en["hp"] < en["max"] and sc >= 1 and kd != 8:
        bw = int(h * 2.6)
        bx, by = int(x - bw / 2), int(y - h * 2)
        pygame.draw.rect(screen, (60, 60, 60), (bx, by, bw, 4))
        pygame.draw.rect(screen, (80, 220, 80), (bx, by, int(bw * max(0, en["hp"]) / en["max"]), 4))


def draw_coin(c):
    x = c[0]
    y = c[1] + math.sin(tick * 0.07 + c[2]) * 4 * u
    r = 12 * u * c[3]
    if r < 2:
        return
    glow(x, y, r * 2.6, GOLD)
    w = max(2, abs(math.cos(tick * 0.08 + c[2])) * r)
    rect = pygame.Rect(0, 0, int(w * 2), int(r * 2))
    rect.center = (int(x), int(y))
    pygame.draw.ellipse(screen, (255, 215, 70), rect)
    pygame.draw.ellipse(screen, (200, 140, 20), rect, max(1, int(2 * u)))
    if rect.w > 8:
        pygame.draw.ellipse(screen, (255, 240, 150), rect.inflate(-int(rect.w * 0.5), -int(rect.h * 0.5)))


def heart(x, y, s, col):
    r = s * 0.25
    pygame.draw.circle(screen, col, (int(x - r), int(y)), int(r) + 1)
    pygame.draw.circle(screen, col, (int(x + r), int(y)), int(r) + 1)
    pygame.draw.polygon(screen, col, [(x - 2 * r * 0.95, y + r * 0.35),
                                      (x + 2 * r * 0.95, y + r * 0.35), (x, y + r * 2.6)])
reset()
started = False
tick = 0
running = True
pointer_x, pointer_y = W / 2, H / 2

while running:
    tick += 1
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            if e.type == pygame.FINGERDOWN:
                mx_, my_ = e.x * W, e.y * H
            else:
                mx_, my_ = e.pos[0] * kx, e.pos[1] * ky
            pointer_x, pointer_y = mx_, my_
            if not started:
                started = True
            elif over:
                if over_t > 40:
                    reset()
            elif BTN.collidepoint(mx_, my_):
                if energy >= 5 and rain == 0:
                    energy, rain = 0, 180
                    shake = 10
                    burst(px, py, GOLD, 30, 4)
                    sfx(S_RAIN)
            else:
                touching = True
        elif e.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
            if e.type == pygame.FINGERMOTION:
                pointer_x, pointer_y = e.x * W, e.y * H
            else:
                pointer_x, pointer_y = e.pos[0] * kx, e.pos[1] * ky
        elif e.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
            touching = False

    # ================= التحديث =================
    if started and not over:
        if boss is None:          # الوقت بيقف أثناء معركة البوس
            frames += 1
        newlvl = 1 + frames // LEVEL_FRAMES
        if newlvl != level:
            level = newlvl
            banner, banner_txt, banner_zone = 120, f"LEVEL {level}", False
            sfx(S_LEVEL)
            nt = ((level - 1) // ZONE_LEVELS) % len(bgs)
            if nt != cur_theme:
                prev_theme, cur_theme = cur_theme, nt
                fade = 90
                banner_zone = True

        # ظهور البوس
        if boss is None and level >= next_boss:
            boss = spawn_boss()
            for en in enemies:
                burst(en["x"], en["y"], ET[en["kind"]]["gl"], 10)
            enemies = [boss]
            bullets = []
            banner, banner_txt, banner_zone = 150, "BOSS!", False
            sfx(S_BOSS)
            shake = 20

        ox, oy = px, py
        if touching:
            px += (pointer_x - px) * 0.1
            py += (pointer_y - py) * 0.1
        vx, vy = px - ox, py - oy
        if inv > 0: inv -= 1
        if combo_t > 0:
            combo_t -= 1
        else:
            combo = 0
        trail.append((px, py))
        if len(trail) > 10: trail.pop(0)

        # العملات (مغناطيس خفيف + كومبو)
        for c in coins:
            c[3] = min(1.0, c[3] + 0.08)
            d = math.hypot(c[0] - px, c[1] - py)
            if d < 110 * u and c[3] >= 1:
                c[0] += (px - c[0]) * 0.08
                c[1] += (py - c[1]) * 0.08
            if d < PR + 14 * u and c[3] >= 1:
                combo = combo + 1 if combo_t > 0 else 1
                combo_t = 120
                mult = min(combo, 5)
                sfx(S_COIN[mult - 1])
                burst(c[0], c[1], GOLD, 12)
                popup(c[0], c[1], f"+{10 * mult}", GOLD)
                c[0], c[1], c[2], c[3] = spawn_coin()
                score += 10 * mult
                if energy == 4:
                    popup(px, py - 40 * u, "RAIN READY!", (255, 240, 150))
                    sfx(S_READY)
                energy = min(5, energy + 1)

        # ظهور الأعداء العاديين
        spawn_t += 1
        normal = sum(1 for q in enemies if q["kind"] not in (7, 8))
        cap = 1 if boss is not None else MAX_ENEMIES
        if spawn_t >= max(25, 90 - level * 8) and normal < cap:
            enemies.append(spawn_enemy(level))
            spawn_t = 0

        if rain > 0:
            rain -= 1

        # ---- تحديث الدروع (الحامي) ----
        for en in enemies:
            en["shielded"] = False
        for en in enemies:
            tg = en["tgt"]
            if en["kind"] == 11 and tg is not None:
                if tg["hp"] > 0 and any(o is tg for o in enemies):
                    tg["shielded"] = True
                else:
                    en["tgt"] = None

        # ================= عقل الأعداء =================
        speed = min(ENEMY_SPEED + level * SPEED_PER_LEVEL, MAX_SPEED) * u
        for en in enemies:
            kd = en["kind"]
            et = ET[kd]
            en["born"] += 1
            en["rot"] += 0.01 if kd == 8 else 0.03 + speed * 0.01
            if en["flash"] > 0: en["flash"] -= 1
            if en["born"] < 40:
                continue
            dx, dy = px - en["x"], py - en["y"]
            dist = math.hypot(dx, dy) + 0.001
            ux, uy = dx / dist, dy / dist
            sp = speed * et["sp"]
            if kd == 8 and en["hp"] < en["max"] * 0.5:
                sp *= 1.4   # المرحلة التانية أسرع

            if et["flee"] and rain > 0 and dist < RAIN_R * 1.4 and en["state"] == 0:
                mx, my = -ux, -uy                      # بيخاف من المطر

            elif kd == 1:                              # المتوقّع: بيقطع عليك الطريق
                tx, ty = px + vx * 18, py + vy * 18
                d2 = math.hypot(tx - en["x"], ty - en["y"]) + 0.001
                mx, my = (tx - en["x"]) / d2, (ty - en["y"]) / d2

            elif kd == 2 and dist > 220 * u:           # المحاصِر: بيلف حواليك
                en["a"] += 0.03
                tx = px + math.cos(en["a"]) * 160 * u
                ty = py + math.sin(en["a"]) * 160 * u
                d2 = math.hypot(tx - en["x"], ty - en["y"]) + 0.001
                mx, my = (tx - en["x"]) / d2, (ty - en["y"]) / d2

            elif kd == 3:                              # المندفع: يقف، يحذّر، يندفع
                if en["state"] == 0:
                    mx, my = ux, uy
                    en["cd"] -= 1
                    if en["cd"] <= 0 and dist < 380 * u:
                        en["state"], en["st"] = 1, 40
                        en["dx"], en["dy"] = ux, uy
                elif en["state"] == 1:
                    mx = my = 0
                    en["st"] -= 1
                    if en["st"] <= 0:
                        en["state"], en["st"] = 2, 22
                else:
                    mx, my = en["dx"], en["dy"]
                    sp = speed * 5
                    en["st"] -= 1
                    if en["st"] <= 0:
                        en["state"], en["cd"] = 0, 80

            elif kd == 4:                              # القنّاص: يحافظ على مسافة ويضرب
                sgn = 1 if en["a"] < 3.14 else -1
                if dist > 320 * u:
                    mx, my = ux, uy
                elif dist < 220 * u:
                    mx, my = -ux, -uy
                else:
                    mx, my = -uy * sgn, ux * sgn
                en["cd"] -= 1
                if en["cd"] <= 0:
                    shoot(en["x"], en["y"], math.atan2(dy, dx), 5 * u, (200, 255, 80))
                    burst(en["x"], en["y"], (200, 255, 80), 4, 2)
                    sfx(S_SHOOT)
                    en["cd"] = max(60, 120 - level * 2)

            elif kd == 9:                              # اللص: يسرق عملة ويهرب بيها
                if en["state"] == 0:
                    best, bd = None, 1e9
                    for c in coins:
                        if c[3] >= 1:
                            dd = math.hypot(c[0] - en["x"], c[1] - en["y"])
                            if dd < bd:
                                bd, best = dd, c
                    if best is not None:
                        mx, my = (best[0] - en["x"]) / (bd + 0.001), (best[1] - en["y"]) / (bd + 0.001)
                        if bd < 22 * u:
                            best[0], best[1], best[2], best[3] = spawn_coin()
                            en["state"], en["st"], en["carry"] = 1, 360, True
                            popup(en["x"], en["y"], "STOLEN!", (255, 120, 120))
                            sfx(S_STEAL)
                    else:
                        mx = my = 0
                else:
                    mx, my = -ux, -uy
                    sp = speed * 1.15
                    en["st"] -= 1
                    if en["st"] <= 0:                  # هرب بالعملة
                        en["escaped"] = True
                        en["hp"] = 0

            elif kd == 10:                             # الشبح: بيتمايل وهو جاي عليك
                en["a"] += 0.08
                wob = math.sin(en["a"]) * 0.6
                mx, my = ux - uy * wob, uy + ux * wob

            elif kd == 11:                             # الحامي: بيحمي عدو تاني بدرع
                tg = en["tgt"]
                if tg is None:
                    bestd = 1e9
                    for o in enemies:
                        if o is not en and o["kind"] not in (8, 11) and o["hp"] > 0 and not o["shielded"]:
                            dd = math.hypot(o["x"] - en["x"], o["y"] - en["y"])
                            if dd < bestd:
                                bestd, tg = dd, o
                    en["tgt"] = tg
                if tg is not None:
                    dd = math.hypot(tg["x"] - en["x"], tg["y"] - en["y"]) + 0.001
                    if dd > 110 * u:
                        mx, my = (tg["x"] - en["x"]) / dd, (tg["y"] - en["y"]) / dd
                    else:
                        mx = my = 0
                else:
                    mx, my = (-ux, -uy) if dist < 300 * u else (0, 0)

            elif kd == 8:                              # البوس
                ph2 = en["hp"] < en["max"] * 0.5
                if dist > 260 * u:
                    mx, my = ux, uy
                else:
                    sgn = 1 if en["a"] < 3.14 else -1
                    mx, my = -uy * sgn, ux * sgn
                en["cd"] -= 1
                if en["cd"] <= 0:
                    n_b = 14 if ph2 else 10
                    off = random.uniform(0, 6.28)
                    for i in range(n_b):
                        shoot(en["x"], en["y"], off + i * 6.2832 / n_b, 3.6 * u, (255, 80, 150))
                    if ph2:
                        a0 = math.atan2(dy, dx)
                        for da in (-0.25, 0, 0.25):
                            shoot(en["x"], en["y"], a0 + da, 6 * u, (255, 200, 60))
                    en["cd"] = 75 if ph2 else 110
                    shake = max(shake, 5)
                    burst(en["x"], en["y"], (255, 80, 150), 16, 4)
                    sfx(S_SHOOT)

            else:                                      # مطارد عادي / منقسم / دبابة / صغير
                mx, my = ux, uy

            # عشان ميتجمعوش فوق بعض
            if en["state"] == 0 and kd != 8:
                for o in enemies:
                    if o is not en:
                        ddx, ddy = en["x"] - o["x"], en["y"] - o["y"]
                        dd = math.hypot(ddx, ddy)
                        if 0 < dd < 40 * u:
                            mx += ddx / dd * 0.8
                            my += ddy / dd * 0.8

            en["x"] = min(max(en["x"] + mx * sp, 0), W)
            en["y"] = min(max(en["y"] + my * sp, 0), H)

            # أذى المطر (المحمي بدرع مبيتأذّاش)
            if rain > 0 and dist < RAIN_R:
                if en["shielded"]:
                    en["flash"] = 0
                    if tick % 20 == 0:
                        popup(en["x"], en["y"] - 24 * u, "BLOCKED", (120, 255, 200))
                else:
                    en["hp"] -= RAIN_DMG
                    if tick % 6 == 0:
                        en["flash"] = 3

            # لمس البطل (اللص مبيأذيش)
            if dist < PR + 14 * u * et["sz"] and inv == 0 and et.get("harm", True):
                hurt()
                if kd == 8:                            # البوس بيزقّك بعيد
                    px = min(max(px + ux * 90 * u, 0), W)
                    py = min(max(py + uy * 90 * u, 0), H)
                else:
                    en["x"] -= ux * 50 * u
                    en["y"] -= uy * 50 * u

        # ---- الرصاص ----
        nb = []
        for b in bullets:
            b[0] += b[2]
            b[1] += b[3]
            b[4] -= 1
            if b[4] <= 0 or b[0] < -40 or b[0] > W + 40 or b[1] < -40 or b[1] > H + 40:
                continue
            if rain > 0 and math.hypot(b[0] - px, b[1] - py) < RAIN_R:
                continue                               # المطر بيدمّر الرصاص
            if inv == 0 and not over and math.hypot(b[0] - px, b[1] - py) < PR + 5 * u:
                hurt()
                continue
            nb.append(b)
        bullets = nb

        # ---- موت الأعداء ----
        alive, born_new = [], []
        for en in enemies:
            if en["hp"] > 0:
                alive.append(en)
                continue
            kd = en["kind"]
            gl = ET[kd]["gl"]
            if kd == 9 and en["escaped"]:              # اللص هرب بالعملة
                burst(en["x"], en["y"], gl, 10, 3)
                popup(en["x"], en["y"], "ESCAPED", (255, 120, 120))
                energy = max(0, energy - 1)
            elif kd == 8:
                score += 500
                shake = 30
                burst(en["x"], en["y"], gl, 60, 5)
                popup(en["x"], en["y"], "+500", GOLD)
                sfx(S_BOSSDEAD)
                banner, banner_txt, banner_zone = 150, "BOSS DEFEATED!", False
                boss = None
                boss_no += 1
                next_boss += BOSS_LEVEL
                bullets = []
                energy = 5          # مكافأة: المطر جاهز
            else:
                pts = {7: 10, 6: 40, 10: 35, 11: 35}.get(kd, 25)
                if kd == 9 and en["carry"]:            # رجّعت العملة المسروقة
                    pts = 60
                    energy = min(5, energy + 1)
                    popup(en["x"], en["y"] - 24 * u, "GOT IT BACK!", GOLD)
                score += pts
                shake = max(shake, 12)
                burst(en["x"], en["y"], gl, 22, 4)
                popup(en["x"], en["y"], f"+{pts}", (255, 255, 255))
                sfx(S_KILL)
                if kd == 5:         # المنقسم بيطلع منه اتنين صغيرين
                    for sgn in (-1, 1):
                        m2 = make_enemy(7, en["x"] + sgn * 20 * u, en["y"], 14)
                        m2["born"] = 40
                        born_new.append(m2)
        enemies = alive + born_new

        if over and not saved:
            saved = True
            sfx(S_OVER)
            if score > highscore:
                highscore, new_best = score, True
                save_hs(highscore)

    if over:
        over_t += 1

    for p in particles:
        p[0] += p[2]
        p[1] += p[3]
        p[2] *= 0.96
        p[3] *= 0.96
        p[4] -= 1
    particles = [p for p in particles if p[4] > 0]
    for t in texts:
        t[1] -= 1.2 * u
        t[3] -= 1
    texts = [t for t in texts if t[3] > 0]
    if shake > 0: shake -= 1
    if banner > 0: banner -= 1
    if fade > 0: fade -= 1

    # ================= الرسم =================
    screen.blit(bgs[cur_theme], (0, 0))
    if fade > 0:                                       # انتقال ناعم بين الخلفيات
        old = bgs[prev_theme]
        old.set_alpha(int(255 * fade / 90))
        screen.blit(old, (0, 0))
    for s in stars:
        s[1] += s[4] * 0.3 * u
        if s[1] > H:
            s[1], s[0] = 0, random.uniform(0, W)
        b = int(130 + 100 * math.sin(tick * 0.05 + s[3]))
        pygame.draw.circle(screen, (b, b, min(255, b + 30)), (int(s[0]), int(s[1])),
                           max(1, int(s[2] * u * 0.8)))

    if rain > 0:
        screen.blit(rain_surf, (int(px) - RAIN_R, int(py) - RAIN_R))
        pr = int(RAIN_R * ((tick % 40) / 40))
        if pr > 2:
            pygame.draw.circle(screen, (255, 215, 90), (int(px), int(py)), pr, 1)

    for c in coins:
        draw_coin(c)
    # خط الحماية بين الحامي والعدو اللي بيحميه
    for en in enemies:
        tg = en["tgt"]
        if en["kind"] == 11 and tg is not None and tg["hp"] > 0:
            pygame.draw.line(screen, (80, 255, 190), (int(en["x"]), int(en["y"])),
                             (int(tg["x"]), int(tg["y"])), max(2, int(2 * u)))
    for en in enemies:
        draw_enemy(en)
    for b in bullets:
        glow(b[0], b[1], 10 * u, b[5])
        pygame.draw.circle(screen, b[5], (int(b[0]), int(b[1])), max(3, int(5 * u)))
        pygame.draw.circle(screen, (255, 255, 255), (int(b[0]), int(b[1])), max(1, int(2 * u)))
    for p in particles:
        rr = max(1, int(p[6] * min(1.0, p[4] / 18)))
        pygame.draw.circle(screen, p[5], (int(p[0]), int(p[1])), rr)

    if inv == 0 or (inv // 5) % 2 == 0:
        draw_hero()

    for t in texts:
        text(small, t[2], t[4], (int(t[0]), int(t[1])), alpha=min(255, t[3] * 8))

    # ---- الواجهة ----
    if started:
        for i in range(3):
            heart(30 * u + i * 38 * u, 34 * u, 28 * u,
                  (255, 70, 100) if i < lives else (70, 50, 70))
        text(font, str(score), (255, 255, 255), (W // 2, int(32 * u)))
        text(small, f"BEST {highscore}", (200, 200, 220), (W // 2, int(62 * u)))
        text(small, f"LEVEL {level}", (200, 200, 255), (W - int(80 * u), int(34 * u)))
        if combo > 1:
            text(font, f"x{min(combo, 5)} COMBO", GOLD, (W // 2, int(100 * u)))

        # شريط صحة البوس
        if boss is not None:
            bw = int(W * 0.6)
            bx, by, bh = (W - bw) // 2, H - int(40 * u), int(14 * u)
            pygame.draw.rect(screen, (60, 30, 50), (bx, by, bw, bh))
            pygame.draw.rect(screen, (255, 60, 140), (bx, by, int(bw * max(0, boss["hp"]) / boss["max"]), bh))
            pygame.draw.rect(screen, (255, 200, 220), (bx, by, bw, bh), 2)
            text(small, "BOSS", (255, 200, 220), (W // 2, by - int(14 * u)))

        cx, cy = BTN.center
        br = BTN.w // 2
        ready = energy >= 5 and rain == 0
        if ready:
            glow(cx, cy, br * 2 + math.sin(tick * 0.2) * 8 * u, GOLD)
        pygame.draw.circle(screen, GOLD if ready else (40, 34, 20), (cx, cy), br)
        prog = rain / 180 if rain > 0 else energy / 5
        if prog > 0:
            pygame.draw.arc(screen, GOLD, BTN.inflate(-6, -6), math.pi / 2,
                            math.pi / 2 + 6.283 * min(prog, 0.999), max(4, int(6 * u)))
        pygame.draw.circle(screen, (255, 225, 120), (cx, cy), br, 2)
        text(small, "RAIN" if ready else f"{energy}/5",
             (20, 20, 40) if ready else (255, 225, 120), (cx, cy))

        if banner > 0 and not over:
            bcol = (255, 230, 120) if banner_txt.startswith("LEVEL") else (255, 90, 150)
            by2 = int(H * 0.28 - (150 - banner) * 0.3)
            text(big, banner_txt, bcol, (W // 2, by2), alpha=min(255, banner * 6))
            if banner_zone:
                text(font, "NEW ZONE!", (120, 230, 255), (W // 2, by2 + int(70 * u)),
                     alpha=min(255, banner * 6))
    else:
        text(big, "GOLD RAIN", GOLD, (W // 2, int(H * 0.25 + math.sin(tick * 0.05) * 8 * u)))
        text(small, "touch to move  -  grab the gold  -  use RAIN", (210, 210, 240),
             (W // 2, int(H * 0.25 + 70 * u)))
        if (tick // 30) % 2 == 0:
            text(font, "TAP TO START", (255, 255, 255), (W // 2, int(H * 0.8)))

    if over:
        screen.blit(overlay, (0, 0))
        text(big, "GAME OVER", (230, 50, 60), (W // 2, H // 2 - int(50 * u)))
        text(font, f"Score: {score}", (255, 255, 255), (W // 2, H // 2 + int(20 * u)))
        if new_best:
            text(font, "NEW BEST!", GOLD, (W // 2, H // 2 + int(65 * u)),
                 alpha=int(170 + 85 * math.sin(tick * 0.2)))
        if over_t > 40 and (tick // 30) % 2 == 0:
            text(small, "tap to restart", (220, 220, 240), (W // 2, H // 2 + int(110 * u)))

    sx = sy = 0
    if shake > 0:
        m = int(shake * 0.7 * u * 1.6) + 1
        sx, sy = random.randint(-m, m), random.randint(-m, m)
    win.fill((0, 0, 0))
    win.blit(pygame.transform.scale(screen, (WW, WH)), (sx, sy))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()