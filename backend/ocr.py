from __future__ import annotations

import importlib.metadata
import os
import re
import tempfile
from pathlib import Path

# PaddleOCR 3.x / PaddleX: 모델 호스트 연결 검사 생략
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

if os.environ.get("OCR_ENABLE_MKLDNN", "").lower() not in ("1", "true", "yes"):
    os.environ.setdefault("FLAGS_use_mkldnn", "0")

_MAX_INPUT_SIDE = 3000
_TEXT_DET_LIMIT_SIDE_LEN = 960

# lazy singleton
_ocr_engine: object | None = None
_ocr_major: int | None = None


def normalize_for_match(s: str) -> str:
    """공백 제거 후 비교(한글·영문 혼합, OCR 띄어쓰기 불일치 완화)."""
    t = (s or "").strip()
    t = re.sub(r"\s+", "", t)
    return t.casefold()


def ocr_texts_contain_name_and_school(texts: list[str], name: str, school_name: str) -> bool:
    """OCR 결과 전체에 입력한 이름·학교명이 부분 문자열로 포함되는지 검사."""
    blob = normalize_for_match("".join(texts))
    if not blob:
        return False
    n = normalize_for_match(name)
    s = normalize_for_match(school_name)
    print(n, s, blob)
    if not n or not s:
        return False
    return n in blob and s in blob


def _prepare_image_for_ocr(path: Path, max_side: int = _MAX_INPUT_SIDE) -> tuple[str, bool]:
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        if max(w, h) <= max_side:
            return str(path), False
        scale = max_side / max(w, h)
        nw, nh = int(w * scale), int(h * scale)
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    fd, tmp = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    im.save(tmp, "JPEG", quality=92)
    return tmp, True


def _extract_paddleocr_v2(result: object) -> list[str]:
    texts: list[str] = []
    if not result:
        return texts
    for page in result:
        if not page:
            continue
        for line in page:
            if line and len(line) >= 2 and line[1]:
                texts.append(line[1][0])
    return texts


def _extract_paddleocr_v3(result: object) -> list[str]:
    texts: list[str] = []
    for res in result:
        if res is None:
            continue
        data = None
        if hasattr(res, "json") and callable(res.json):
            data = res.json()
        elif isinstance(res, dict):
            data = res
        if not isinstance(data, dict):
            continue
        block = data.get("res", data)
        if isinstance(block, dict) and "rec_texts" in block:
            texts.extend(str(t) for t in block["rec_texts"] if t)
    return texts


def _ensure_paddle_ocr() -> tuple[object, int]:
    global _ocr_engine, _ocr_major
    if _ocr_engine is not None and _ocr_major is not None:
        return _ocr_engine, _ocr_major

    try:
        ver = importlib.metadata.version("paddleocr")
        major = int(ver.split(".", 1)[0])
    except importlib.metadata.PackageNotFoundError as e:
        raise RuntimeError(
            "paddleocr 패키지가 설치되어 있지 않습니다. "
            "pip install paddlepaddle paddleocr pillow 를 실행하세요."
        ) from e

    import paddle

    _use_mkldnn = os.environ.get("OCR_ENABLE_MKLDNN", "").lower() in (
        "1",
        "true",
        "yes",
    )
    try:
        paddle.set_flags({"FLAGS_use_mkldnn": _use_mkldnn})
    except Exception:
        pass

    from paddleocr import PaddleOCR

    if major >= 3:
        ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=_use_mkldnn,
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="korean_PP-OCRv5_mobile_rec",
            text_det_limit_side_len=_TEXT_DET_LIMIT_SIDE_LEN,
            text_det_limit_type="max",
            text_recognition_batch_size=12,
            cpu_threads=min(16, (os.cpu_count() or 8)),
        )
    else:
        ocr = PaddleOCR(use_angle_cls=True, lang="korean", show_log=False)

    _ocr_engine = ocr
    _ocr_major = major
    return ocr, major


def run_ocr_on_image_path(image_path: str | Path) -> list[str]:
    """이미지 파일 경로에서 OCR 텍스트 줄 목록을 반환합니다."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    ocr, major = _ensure_paddle_ocr()
    img_input, img_is_temp = _prepare_image_for_ocr(path)
    try:
        if major >= 3:
            result = ocr.predict(img_input)
            return _extract_paddleocr_v3(result)
        result = ocr.ocr(img_input, cls=True)
        return _extract_paddleocr_v2(result)
    finally:
        if img_is_temp:
            try:
                os.unlink(img_input)
            except OSError:
                pass


def main() -> None:
    base = Path(__file__).resolve().parent
    img_path = base / "test.jpg"
    if not img_path.is_file():
        print(f"파일을 찾을 수 없습니다: {img_path}")
        return

    try:
        texts = run_ocr_on_image_path(img_path)
    except RuntimeError as e:
        print(str(e))
        print(
            '  python -m pip install paddlepaddle -i https://www.paddlepaddle.org.cn/packages/stable/cpu/\n'
            '  python -m pip install "paddleocr[all]" pillow'
        )
        return
    except Exception as e:
        print(f"OCR 실패: {e}")
        return

    print("\n".join(texts).strip())


if __name__ == "__main__":
    main()
