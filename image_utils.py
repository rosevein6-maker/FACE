"""업로드 이미지 전처리: EXIF 회전 보정, 리사이즈, JPEG 변환, base64 data URL 생성."""

import base64
import io
from typing import BinaryIO

from PIL import Image, ImageOps

MAX_SIDE = 1024
JPEG_QUALITY = 85
# 파일 용량은 작아도 해상도가 거대한 이미지(디컴프레션 폭탄)를 디코딩 전에 차단한다.
# 2,500만 화소 ≈ 최신 스마트폰 원본 사진보다 넉넉한 수준.
MAX_PIXELS = 25_000_000


class ImageTooLargeError(ValueError):
    """이미지 해상도(픽셀 수)가 MAX_PIXELS를 넘을 때."""


def check_pixels(image: Image.Image) -> None:
    """헤더의 크기 정보만으로 픽셀 수를 검사한다 (픽셀 디코딩 전)."""
    width, height = image.size
    if width * height > MAX_PIXELS:
        raise ImageTooLargeError(f"{width}x{height}")


def load_image(file: BinaryIO) -> Image.Image:
    """파일 객체를 열어 EXIF 회전을 보정한 RGB 이미지로 반환한다."""
    image = Image.open(file)
    check_pixels(image)
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


def resize_image(image: Image.Image, max_side: int = MAX_SIDE) -> Image.Image:
    """긴 변이 max_side를 넘으면 비율을 유지하며 축소한다."""
    image = image.copy()
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return image


def to_data_url(image: Image.Image) -> str:
    """이미지를 JPEG로 인코딩해 base64 data URL 문자열로 반환한다."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def prepare_image(file: BinaryIO) -> str:
    """업로드 파일을 OpenAI 전송용 data URL로 변환한다 (메모리에서만 처리)."""
    return to_data_url(resize_image(load_image(file)))
