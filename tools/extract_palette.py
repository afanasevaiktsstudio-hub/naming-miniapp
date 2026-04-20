"""Извлекает доминантные цвета из аватарки канала @analiticada."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from PIL import Image


def hex_of(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def extract(path: Path, num_colors: int = 10) -> list[tuple[str, int]]:
    img = Image.open(path).convert("RGB")
    img = img.resize((200, 200))
    # quantize выдаёт палитру из N цветов
    q = img.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette = q.getpalette() or []
    counts = Counter(q.getdata())
    result: list[tuple[str, int]] = []
    for idx, count in counts.most_common():
        r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
        result.append((hex_of((r, g, b)), count))
    return result


if __name__ == "__main__":
    avatar = Path(__file__).parent / "analiticada_avatar.jpg"
    top = extract(avatar, num_colors=12)
    total = sum(c for _, c in top)
    print(f"{'HEX':<10}{'SHARE':>8}")
    for hx, count in top:
        share = count / total * 100
        print(f"{hx:<10}{share:>7.1f}%")
