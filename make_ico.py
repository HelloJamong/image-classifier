"""Generate a multi-resolution Windows ICO from logo.png."""
from PIL import Image

_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def make_ico(png: str = "logo.png", ico: str = "logo.ico") -> None:
    img = Image.open(png).convert("RGBA")
    img.save(ico, format="ICO", sizes=_SIZES)
    print(f"[make_ico] {ico} 생성 완료 ({len(_SIZES)}개 해상도)")


if __name__ == "__main__":
    make_ico()
