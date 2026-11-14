"""Render the original animated CortexState architecture GIF.

Requires Pillow for asset generation only. Run from the repository root with
``python assets/build_learning_loop.py``.
"""
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1600, 980
BG = "#081321"
PANEL = "#0d1c2d"
CARD = "#13263a"
CARD_ACTIVE = "#18384b"
TEXT = "#f4f7fb"
MUTED = "#b4c3d3"
SUBTLE = "#8295aa"
TEAL = "#67e2c1"
BLUE = "#8db8ff"
PURPLE = "#c3a5ff"
AMBER = "#f5c77e"
LINE = "#294259"
OUTLINE = "#2b435a"

FONT_CANDIDATES = {
    False: [Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")],
    True: [Path("C:/Windows/Fonts/segoeuib.ttf"),
           Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")],
}


def font(size, bold=False):
    for candidate in FONT_CANDIDATES[bold]:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


TITLE = font(40, True)
SUBTITLE = font(20)
SECTION = font(16, True)
CARD_TITLE = font(18, True)
CARD_COPY = font(15)
TAG = font(13, True)
FOOT = font(15)
SMALL = font(13)

CARD_W, CARD_H = 190, 142
RUNTIME_Y = 220
RUNTIME = [
    ("Agent stack", "Model · harness\nskills · tools", TEAL),
    ("Host policy", "Consent · identity\ntool authorization", TEAL),
    ("Connectors", "Python · TypeScript\ntrusted HTTP API", BLUE),
    ("Scope guard", "Tenant · user\nagent · session", BLUE),
    ("Memory core", "Facts · revisions\nexpiry · deletion", TEAL),
    ("Recall builder", "Filter · rank\nbudgeted context", BLUE),
    ("Agent response", "Model uses context\nunder host policy", TEAL),
]
RUNTIME_X = [56 + i * 216 for i in range(7)]

LEARN_Y = 485
LEARN_W, LEARN_H = 220, 128
LEARNING = [
    ("1  Observe", "Task outcome\nsuccess · correction\nfailure · safety", TEAL),
    ("2  Protect data", "Consent · redact\nexact scope\nsource provenance", TEAL),
    ("3  Stage lesson", "Link evidence\npropose · revise\nreject", TEAL),
    ("4  Evaluate", "Same protected suite\nbaseline vs candidate\nquality · safety · cost", BLUE),
    ("5  Approve", "No safety regression\nstrict measured gain\nreviewer decision", AMBER),
    ("6  Promote", "Scoped memory\nversioned change\nrollback available", TEAL),
]
LEARN_X = [58 + i * 252 for i in range(6)]

RL_Y = 755
RL_W, RL_H = 290, 112
RL = [
    ("Curated task streams", "Consent-screened · redacted\nversioned · ordered episodes"),
    ("Offline ACT + WRITE", "Trainable weights only\nactor acts · writer selects"),
    ("Delayed reward", "Later-task gain − resource cost\nsafety failures are ineligible"),
    ("Holdout + canary", "Model owner validates policy\nthen controls deployment"),
]
RL_X = [90 + i * 380 for i in range(4)]


def arrow(draw, start, end, color=LINE, width=3):
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 11
    left = (end[0] - size * math.cos(angle - .48),
            end[1] - size * math.sin(angle - .48))
    right = (end[0] - size * math.cos(angle + .48),
             end[1] - size * math.sin(angle + .48))
    draw.polygon([end, left, right], fill=color)


def pill(draw, x, y, text, color, *, right=None):
    bbox = TAG.getbbox(text)
    width = bbox[2] - bbox[0] + 24
    if right is not None:
        x = right - width
    draw.rounded_rectangle((x, y, x + width, y + 31), radius=15,
                           fill="#122b3b", outline="#29485b", width=1)
    draw.text((x + 12, y + 7), text, font=TAG, fill=color)
    return x, x + width


def centered_multiline(draw, box, text, face, fill, spacing=5):
    x0, y0, x1, y1 = box
    bounds = draw.multiline_textbbox((0, 0), text, font=face, spacing=spacing,
                                     align="center")
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.multiline_text((x0 + (x1 - x0 - width) / 2,
                         y0 + (y1 - y0 - height) / 2 - bounds[1]),
                        text, font=face, fill=fill, spacing=spacing,
                        align="center")


def card(draw, x, y, width, height, title, copy, accent,
         *, active=False, compact=False):
    fill = CARD_ACTIVE if active else CARD
    border = accent if active else OUTLINE
    draw.rounded_rectangle((x, y, x + width, y + height), radius=18,
                           fill=fill, outline=border, width=3 if active else 2)
    draw.rounded_rectangle((x + 16, y + 16, x + 22, y + 43), radius=3,
                           fill=accent)
    title_font = CARD_TITLE if not compact else font(17, True)
    draw.text((x + 34, y + 17), title, font=title_font, fill=TEXT)
    centered_multiline(draw, (x + 10, y + 52, x + width - 10, y + height - 12),
                       copy, CARD_COPY, MUTED, spacing=5)


def active_path(draw, xs, y, width, count, step, color):
    center = y + CARD_H // 2 if width == CARD_W else y + LEARN_H // 2
    for i in range(count - 1):
        begin = (xs[i] + width + 5, center)
        end = (xs[i + 1] - 7, center)
        is_active_edge = step == i
        arrow(draw, begin, end, color if is_active_edge else LINE,
              width=4 if is_active_edge else 2)
        if is_active_edge:
            t = (step % 4 + 1) / 5
            px = begin[0] + (end[0] - begin[0]) * t
            draw.ellipse((px - 6, center - 6, px + 6, center + 6),
                         fill=TEXT, outline=color, width=3)


def build_frame(step):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.ellipse((1170, -370, 1740, 180), fill="#10243a")
    draw.ellipse((-300, 680, 230, 1210), fill="#0d2234")
    draw.rounded_rectangle((24, 20, WIDTH - 24, HEIGHT - 20), radius=28,
                           fill=BG, outline="#1e3348", width=2)

    draw.text((58, 45), "CortexState", font=TITLE, fill=TEXT)
    draw.text((60, 101),
              "Shared memory and reviewed improvement for agents in deployment",
              font=SUBTITLE, fill=MUTED)
    pill(draw, 60, 145, "MODEL + HARNESS NEUTRAL", TEAL)
    pill(draw, 0, 145, "CAMI 0.1.0 · PROPOSED SPEC", BLUE, right=WIDTH - 60)

    # Runtime path.
    draw.text((60, 198), "01  RUNTIME MEMORY PATH", font=SECTION, fill=TEAL)
    draw.text((WIDTH - 60, 198), "Same API · exact scope · explicit trust boundary",
              font=SMALL, fill=SUBTLE, anchor="ra")
    draw.line((60, 218, WIDTH - 60, 218), fill=LINE, width=1)
    active_path(draw, RUNTIME_X, RUNTIME_Y, CARD_W, len(RUNTIME), step, TEAL)
    for i, (title, copy, accent) in enumerate(RUNTIME):
        card(draw, RUNTIME_X[i], RUNTIME_Y, CARD_W, CARD_H, title, copy,
             accent, active=(step == i))

    # Outcome learning path.
    draw.text((60, 423), "02  REVIEWED DEPLOYMENT LEARNING", font=SECTION,
              fill=TEAL)
    draw.text((WIDTH - 60, 423), "No silent writes · external evaluation · human approval",
              font=SMALL, fill=SUBTLE, anchor="ra")
    draw.line((60, 446, WIDTH - 60, 446), fill=LINE, width=1)
    learn_step = step - len(RUNTIME)
    for i in range(len(LEARNING) - 1):
        start = (LEARN_X[i] + LEARN_W + 5, LEARN_Y + LEARN_H // 2)
        end = (LEARN_X[i + 1] - 7, LEARN_Y + LEARN_H // 2)
        is_active = learn_step == i
        arrow(draw, start, end, TEAL if is_active else LINE,
              width=4 if is_active else 2)
        if is_active:
            px = start[0] + (end[0] - start[0]) * .55
            py = start[1]
            draw.ellipse((px - 6, py - 6, px + 6, py + 6),
                         fill=TEXT, outline=TEAL, width=3)
    for i, (title, copy, accent) in enumerate(LEARNING):
        card(draw, LEARN_X[i], LEARN_Y, LEARN_W, LEARN_H, title, copy,
             accent, active=(learn_step == i), compact=True)

    # Feedback connector: only approved lessons enter normal memory recall.
    engine_x = RUNTIME_X[4] + CARD_W // 2
    promote_x = LEARN_X[-1] + LEARN_W // 2
    feedback_x = WIDTH - 46
    feedback_y = 370
    draw.line([(promote_x, LEARN_Y + LEARN_H),
               (promote_x, 658), (feedback_x, 658),
               (feedback_x, feedback_y), (engine_x, feedback_y)],
              fill="#376d69", width=2)
    arrow(draw, (engine_x, feedback_y),
          (engine_x, RUNTIME_Y + CARD_H + 3), TEAL, width=2)
    draw.text((promote_x - 12, 638), "approved lesson", font=SMALL,
              fill="#8dbeb5", anchor="rm")
    draw.text((engine_x, 388), "returns to scoped memory", font=SMALL,
              fill="#8dbeb5", anchor="mm")

    # Optional policy-training lane. This updates owned weights offline; it is
    # not a runtime memory feature or a trainer included in the current release.
    draw.text((60, 698), "03  OPTIONAL OFFLINE RL", font=SECTION, fill=PURPLE)
    draw.text((WIDTH - 60, 698), "Separate from the shared memory API · trainer not included",
              font=SMALL, fill=AMBER, anchor="ra")
    draw.line((60, 721, WIDTH - 60, 721), fill=LINE, width=1)
    rl_step = step - len(RUNTIME) - len(LEARNING)
    for i in range(len(RL) - 1):
        start = (RL_X[i] + RL_W + 5, RL_Y + RL_H // 2)
        end = (RL_X[i + 1] - 7, RL_Y + RL_H // 2)
        is_active = rl_step == i
        arrow(draw, start, end, PURPLE if is_active else LINE,
              width=4 if is_active else 2)
        if is_active:
            px = start[0] + (end[0] - start[0]) * .55
            py = start[1]
            draw.ellipse((px - 6, py - 6, px + 6, py + 6),
                         fill=TEXT, outline=PURPLE, width=3)
    for i, (title, copy) in enumerate(RL):
        card(draw, RL_X[i], RL_Y, RL_W, RL_H, title, copy, PURPLE,
             active=(rl_step == i), compact=True)

    # Status strip changes with the animated focus to explain each loop.
    draw.rounded_rectangle((60, 892, WIDTH - 60, 942), radius=14,
                           fill=PANEL, outline="#20374c", width=1)
    if step < len(RUNTIME):
        status = "LIVE PATH  ·  Retrieve only authorized, relevant context; the host keeps model and tool policy."
        tone = TEAL
    elif step < len(RUNTIME) + len(LEARNING):
        status = "IMPROVEMENT LOOP  ·  Evidence proposes a lesson; protected evaluation and review gate promotion."
        tone = TEAL
    else:
        status = "OPTIONAL RL  ·  Offline training for weights you control; validate on held-out streams before rollout."
        tone = PURPLE
    draw.ellipse((80, 910, 94, 924), fill=tone)
    draw.text((108, 906), status, font=FOOT, fill=MUTED)
    draw.text((WIDTH - 80, 960), "CORTEXSTATE  ·  PROPOSED INTERCHANGE PROFILE  ·  DRAFT 0.1.0",
              font=SMALL, fill=SUBTLE, anchor="ra")
    return image


def main():
    # Walk the three distinct loops: shared runtime memory, reviewed outcome
    # learning, then the optional offline training lane.
    total = len(RUNTIME) + len(LEARNING) + len(RL)
    frames = [build_frame(step) for step in range(total)]
    palette = frames[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE)
              for frame in frames]
    frames[0].save(ROOT / "cortexstate-learning-loop.gif", save_all=True,
                   append_images=frames[1:],
                   duration=[560] * (total - 1) + [1500],
                   loop=0, optimize=True, disposal=1)


if __name__ == "__main__":
    main()
