"""Render the original, animated CortexState architecture GIF.

Requires Pillow for asset generation only; CortexState does not depend on it.
Run from the repository root: python assets/build_learning_loop.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1200, 700
BG = "#0c1727"
PANEL = "#14243a"
CARD = "#1a2d45"
TEXT = "#f2f7fb"
MUTED = "#bdcad8"
TEAL = "#62dec0"
PURPLE = "#b4a2ff"
BLUE = "#8db2ff"
OUTLINE = "#3c5571"
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


TITLE = font(29, True)
SUBTITLE = font(16)
LANE = font(15, True)
NODE_TITLE = font(16, True)
NODE_COPY = font(13)
SMALL = font(12)
FOOT = font(13, True)


TOP = [
    (35, "Any agent stack", "Model · harness\n· skills", TEAL),
    (229, "Task outcome", "Success · correction\n· failure · safety", TEAL),
    (423, "Shared ledger", "Scoped evidence\n+ provenance", TEAL),
    (617, "Lesson candidate", "Propose · revise\n· reject", TEAL),
    (811, "Protected eval", "Baseline vs candidate\nquality · safety · cost", BLUE),
    (1005, "Approved memory", "Human gate · rollback\nscoped retrieval", TEAL),
]
BOTTOM = [
    (35, "Related task streams", "Consent · versions\nordered episodes", PURPLE),
    (229, "ACT · explore", "Solve current task\nfind useful evidence", PURPLE),
    (423, "WRITE · propose", "Compact · correct\nreusable memory", PURPLE),
    (617, "Delayed reward", "Future task gain\nminus token / latency cost", PURPLE),
    (811, "Offline RL", "Train actor + writer\ntrainable weights only", PURPLE),
    (1005, "Holdout · canary", "Pass gates before\nversioned deployment", BLUE),
]
CARD_W, CARD_H = 160, 112
TOP_Y, BOTTOM_Y = 178, 466


def arrow(draw, a, b, color, width=3):
    draw.line([a, b], fill=color, width=width)
    import math
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    size = 9
    left = (b[0] - size * math.cos(angle - .48), b[1] - size * math.sin(angle - .48))
    right = (b[0] - size * math.cos(angle + .48), b[1] - size * math.sin(angle + .48))
    draw.polygon([b, left, right], fill=color)


def draw_card(draw, x, y, title, copy, accent, active=False):
    outline = accent if active else OUTLINE
    fill = "#203d55" if active else CARD
    draw.rounded_rectangle((x, y, x + CARD_W, y + CARD_H), radius=13,
                           fill=fill, outline=outline, width=3 if active else 2)
    draw.rounded_rectangle((x + 13, y + 13, x + 19, y + 36), radius=3,
                           fill=accent if active else OUTLINE)
    draw.text((x + 29, y + 13), title, font=NODE_TITLE, fill=TEXT)
    draw.multiline_text((x + 15, y + 51), copy, font=NODE_COPY,
                        fill=MUTED, spacing=5)


def build_frame(step):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.ellipse((960, -220, 1370, 190), fill="#10263c")
    draw.ellipse((-160, 540, 220, 920), fill="#102638")
    draw.text((40, 30), "CortexState", font=TITLE, fill=TEXT)
    draw.text((42, 70), "Continuous improvement across models, harnesses, and skills",
              font=SUBTITLE, fill=MUTED)
    draw.rounded_rectangle((880, 34, 1160, 66), radius=16,
                           fill="#18344a", outline="#34546c", width=1)
    draw.text((898, 43), "SHARED MEMORY · OPTIONAL RL", font=SMALL, fill=TEAL)

    draw.text((40, 132), "RUNTIME PATH  ·  WORKS WITH ANY MODEL OR HARNESS", font=LANE, fill=TEAL)
    draw.line((40, 157, 1160, 157), fill="#2c455e", width=1)
    draw.text((40, 422), "OPTIONAL OFFLINE TRAINING  ·  TRAINABLE MODEL WEIGHTS ONLY",
              font=LANE, fill=PURPLE)
    draw.line((40, 447, 1160, 447), fill="#2c455e", width=1)

    for i in range(len(TOP) - 1):
        x1 = TOP[i][0] + CARD_W + 4
        x2 = TOP[i + 1][0] - 5
        color = TEAL if step == i else "#3c6170"
        arrow(draw, (x1, TOP_Y + CARD_H // 2), (x2, TOP_Y + CARD_H // 2), color)
    for i in range(len(BOTTOM) - 1):
        x1 = BOTTOM[i][0] + CARD_W + 4
        x2 = BOTTOM[i + 1][0] - 5
        color = PURPLE if step == 6 + i else "#594e79"
        arrow(draw, (x1, BOTTOM_Y + CARD_H // 2), (x2, BOTTOM_Y + CARD_H // 2), color)

    for i, (x, title, copy, accent) in enumerate(TOP):
        draw_card(draw, x, TOP_Y, title, copy, accent, active=(step == i))
    for i, (x, title, copy, accent) in enumerate(BOTTOM):
        draw_card(draw, x, BOTTOM_Y, title, copy, accent, active=(step == 6 + i))

    # Consent-screened deployment evidence can seed an offline task stream.
    draw.line([(503, TOP_Y + CARD_H + 3), (503, 348), (115, 348), (115, BOTTOM_Y - 7)],
              fill="#8277ae", width=2)
    arrow(draw, (115, BOTTOM_Y - 7), (115, BOTTOM_Y - 3), "#a797e6", width=2)
    draw.text((286, 355), "redact · version · curate", font=SMALL, fill="#b9abd9")

    # A gated model version returns to the host's model slot. This is a separate,
    # offline deployment path; the runtime memory API itself remains model-neutral.
    return_x = 1180
    return_y = TOP_Y - 12
    draw.line([(BOTTOM[-1][0] + CARD_W, BOTTOM_Y + 54), (return_x, BOTTOM_Y + 54),
               (return_x, return_y), (TOP[0][0] + CARD_W // 2, return_y)],
              fill="#758aa8", width=2)
    arrow(draw, (TOP[0][0] + CARD_W // 2, return_y),
          (TOP[0][0] + CARD_W // 2, TOP_Y - 4), "#a7b9d2", width=2)
    draw.text((627, 132), "gated policy version returns to the model owner", font=SMALL, fill="#aabbd0")

    draw.line((40, 624, 1160, 624), fill="#344a61", width=1)
    draw.text((40, 643), "RL trains memory-writing judgment offline; CortexState stores, evaluates, and gates lessons.",
              font=FOOT, fill=MUTED)
    draw.text((1160, 668), "RUNTIME RL TRAINER NOT INCLUDED", font=SMALL, fill="#f0c58d", anchor="ra")
    return image


def main():
    # Six runtime steps followed by six optional offline-RL steps. The pulse
    # pauses at each node and then advances along the architecture path.
    frames = [build_frame(step) for step in range(12)]
    palette = frames[0].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(ROOT / "cortexstate-learning-loop.gif", save_all=True,
                   append_images=frames[1:], duration=[700] * 11 + [1200],
                   loop=0, optimize=True, disposal=1)


if __name__ == "__main__":
    main()
