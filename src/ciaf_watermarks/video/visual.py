"""
CIAF Watermarking - Video Visual Watermarking

Apply visual watermarks to video frames (requires re-encoding).

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from typing import Tuple, Optional
from dataclasses import dataclass
import tempfile
import os


@dataclass
class VideoWatermarkSpec:
    """
    Specification for video visual watermark.

    Attributes:
        text: Watermark text to display
        opacity: Watermark opacity (0.0-1.0)
        position: Position ("top_left", "top_right", "bottom_left", "bottom_right", "center")
        font_size: Font size in pixels
        font_color: Font color (R, G, B) tuple
        font_file: Path to TTF font file (optional)
        enable_qr: Whether to include QR code
        qr_position: QR code position (same options as text position)
        qr_size: QR code size in pixels
    """

    text: str
    opacity: float = 0.5
    position: str = "bottom_right"
    font_size: int = 24
    font_color: Tuple[int, int, int] = (255, 255, 255)
    font_file: Optional[str] = None
    enable_qr: bool = False
    qr_position: str = "top_right"
    qr_size: int = 100


def apply_video_visual_watermark(
    video_bytes: bytes,
    watermark_spec: VideoWatermarkSpec,
    verification_url: Optional[str] = None,
) -> bytes:
    """
    Apply visual watermark overlay to video frames.

    WARNING: This requires re-encoding the video, which will reduce quality.
    For lossless watermarking, use metadata watermarking instead.

    Args:
        video_bytes: Original video data
        watermark_spec: Watermark specification
        verification_url: URL for QR code (if enable_qr=True)

    Returns:
        Watermarked video bytes (re-encoded)

    Raises:
        ImportError: If ffmpeg-python not installed
        RuntimeError: If ffmpeg processing fails

    Example:
        >>> from ciaf.watermarks.video import (
        ...     apply_video_visual_watermark,
        ...     VideoWatermarkSpec
        ... )
        >>>
        >>> spec = VideoWatermarkSpec(
        ...     text="AI Generated - Confidential",
        ...     opacity=0.4,
        ...     position="bottom_right",
        ...     font_size=20,
        ... )
        >>>
        >>> watermarked = apply_video_visual_watermark(
        ...     video_bytes=video_bytes,
        ...     watermark_spec=spec,
        ... )
    """
    try:
        import ffmpeg
    except ImportError:
        raise ImportError(
            "Video visual watermarking requires ffmpeg-python. "
            "Install with: pip install ffmpeg-python"
        )

    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_input:
        tmp_input.write(video_bytes)
        input_path = tmp_input.name

    output_path = input_path.replace(".mp4", "_watermarked.mp4")

    try:
        # Calculate text position based on spec
        position_map = {
            "top_left": ("10", "10"),
            "top_right": ("(w-text_w-10)", "10"),
            "bottom_left": ("10", "(h-text_h-10)"),
            "bottom_right": ("(w-text_w-10)", "(h-text_h-10)"),
            "center": ("(w-text_w)/2", "(h-text_h)/2"),
        }

        x_pos, y_pos = position_map.get(watermark_spec.position, position_map["bottom_right"])

        r, g, b = watermark_spec.font_color
        color_hex = f"{r:02x}{g:02x}{b:02x}"

        # Run ffmpeg with drawtext filter
        (
            ffmpeg.input(input_path)
            .filter(
                "drawtext",
                **{
                    "text": watermark_spec.text,
                    "fontsize": watermark_spec.font_size,
                    "fontcolor": f"{color_hex}@{watermark_spec.opacity}",
                    "x": x_pos,
                    "y": y_pos,
                },
            )
            .output(
                output_path,
                vcodec="libx264",  # H.264 encoding
                preset="medium",  # Encoding speed/quality balance
                crf=23,  # Quality (lower = better)
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )

        # Read watermarked video
        with open(output_path, "rb") as f:
            watermarked_bytes = f.read()

        return watermarked_bytes

    except ffmpeg.Error as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else "Unknown error"
        raise RuntimeError(f"ffmpeg visual watermarking failed: {stderr}")

    finally:
        # Cleanup temporary files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


def apply_video_qr_watermark(
    video_bytes: bytes,
    qr_data: str,
    position: str = "top_right",
    qr_size: int = 100,
) -> bytes:
    """
    Add QR code watermark to video.

    Args:
        video_bytes: Original video
        qr_data: Data to encode in QR code (typically verification URL)
        position: QR code position
        qr_size: QR code size in pixels

    Returns:
        Video with QR code overlay

    Raises:
        ImportError: If qrcode library not installed
        RuntimeError: If processing fails

    Example:
        >>> watermarked = apply_video_qr_watermark(
        ...     video_bytes=video_bytes,
        ...     qr_data="https://vault.example.com/verify/wmk-abc123",
        ...     position="top_right",
        ...     qr_size=80,
        ... )
    """
    try:
        import qrcode
        from PIL import Image  # noqa: F401
        import ffmpeg
    except ImportError:
        raise ImportError(
            "QR watermarking requires qrcode and Pillow. "
            "Install with: pip install qrcode[pil] Pillow"
        )

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((qr_size, qr_size))

    # Save QR code to temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_qr:
        qr_img.save(tmp_qr.name)
        qr_path = tmp_qr.name

    # Create temporary files for video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_input:
        tmp_input.write(video_bytes)
        input_path = tmp_input.name

    output_path = input_path.replace(".mp4", "_qr.mp4")

    try:
        # Calculate QR position
        position_map = {
            "top_left": ("10", "10"),
            "top_right": (f"(main_w-{qr_size}-10)", "10"),
            "bottom_left": ("10", f"(main_h-{qr_size}-10)"),
            "bottom_right": (f"(main_w-{qr_size}-10)", f"(main_h-{qr_size}-10)"),
        }

        x_pos, y_pos = position_map.get(position, position_map["top_right"])

        # Overlay QR code using ffmpeg
        input_video = ffmpeg.input(input_path)
        qr_overlay = ffmpeg.input(qr_path)

        (
            ffmpeg.filter([input_video, qr_overlay], "overlay", x=x_pos, y=y_pos)
            .output(
                output_path,
                vcodec="libx264",
                preset="medium",
                crf=23,
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )

        # Read watermarked video
        with open(output_path, "rb") as f:
            watermarked_bytes = f.read()

        return watermarked_bytes

    except ffmpeg.Error as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else "Unknown error"
        raise RuntimeError(f"ffmpeg QR overlay failed: {stderr}")

    finally:
        # Cleanup
        for path in [input_path, output_path, qr_path]:
            if os.path.exists(path):
                os.remove(path)
