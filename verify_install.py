"""
Package Installation Verification Script

This script verifies that the ciaf-watermarks package is properly installed
and all core functionality is accessible.

Usage:
    python verify_install.py

Author: Denzil James Greenwood
Created: 2026-04-06
"""

import sys
import importlib.util


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        if "." in module_name:
            # Handle submodule imports
            parent, child = module_name.rsplit(".", 1)
            parent_mod = __import__(parent, fromlist=[child])
            getattr(parent_mod, child)
        else:
            __import__(module_name)
        print(f"✓ {description}: OK")
        return True
    except ImportError as e:
        print(f"✗ {description}: FAILED - {e}")
        return False
    except AttributeError as e:
        print(f"✗ {description}: FAILED - {e}")
        return False


def check_optional_dependency(module_name, description):
    """Check if an optional dependency is available."""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        print(f"✓ {description}: Available")
        return True
    else:
        print(f"○ {description}: Not installed (optional)")
        return False


def main():
    print("=" * 60)
    print("CIAF Watermarks - Installation Verification")
    print("=" * 60)
    print()

    # Core imports
    print("Core Package:")
    print("-" * 60)
    core_checks = [
        ("ciaf_watermarks", "Main package"),
        ("ciaf_watermarks.models", "Data models"),
        ("ciaf_watermarks.unified_interface", "Unified interface"),
        ("ciaf_watermarks.signature_envelope", "Signature envelopes"),
        ("ciaf_watermarks.hashing", "Hashing utilities"),
        ("ciaf_watermarks.fragment_selection", "Fragment selection"),
        ("ciaf_watermarks.fragment_verification", "Fragment verification"),
        ("ciaf_watermarks.hierarchical_verification", "Hierarchical verification"),
    ]
    
    core_success = all(check_import(mod, desc) for mod, desc in core_checks)
    print()

    # Submodules
    print("Submodules:")
    print("-" * 60)
    submodule_checks = [
        ("ciaf_watermarks.text", "Text watermarking"),
        ("ciaf_watermarks.images", "Image watermarking"),
        ("ciaf_watermarks.pdf", "PDF watermarking"),
        ("ciaf_watermarks.video", "Video watermarking"),
        ("ciaf_watermarks.audio", "Audio watermarking"),
        ("ciaf_watermarks.binary", "Binary watermarking"),
        ("ciaf_watermarks.gpu", "GPU acceleration"),
    ]
    
    submodule_success = all(check_import(mod, desc) for mod, desc in submodule_checks)
    print()

    # Key functions
    print("Key Functions:")
    print("-" * 60)
    function_checks = [
        ("ciaf_watermarks.watermark_ai_output", "watermark_ai_output"),
        ("ciaf_watermarks.detect_artifact_type", "detect_artifact_type"),
        ("ciaf_watermarks.build_text_artifact_evidence", "build_text_artifact_evidence"),
        ("ciaf_watermarks.verify_text_artifact", "verify_text_artifact"),
    ]
    
    function_success = all(check_import(func, desc) for func, desc in function_checks)
    print()

    # Optional dependencies
    print("Optional Dependencies:")
    print("-" * 60)
    optional_deps = [
        ("pydantic", "Pydantic (required)"),
        ("PIL", "Pillow - Image support"),
        ("imagehash", "ImageHash - Perceptual hashing"),
        ("qrcode", "QRCode - QR code generation"),
        ("pypdf", "PyPDF - PDF support"),
        ("reportlab", "ReportLab - PDF generation"),
        ("ffmpeg", "FFmpeg-Python - Video support"),
        ("cv2", "OpenCV - Video processing"),
        ("librosa", "Librosa - Audio analysis"),
        ("soundfile", "SoundFile - Audio I/O"),
        ("torch", "PyTorch - GPU acceleration"),
    ]
    
    for module, desc in optional_deps:
        check_optional_dependency(module, desc)
    print()

    # Final summary
    print("=" * 60)
    if core_success and submodule_success and function_success:
        print("✓ Installation verification PASSED")
        print("  All core components are accessible.")
        print()
        print("Quick Test:")
        print("-" * 60)
        try:
            from ciaf_watermarks import detect_artifact_type
            result = detect_artifact_type("Sample text")
            print(f"✓ detect_artifact_type('Sample text') = {result}")
            print()
            print("Package is ready to use!")
        except Exception as e:
            print(f"✗ Quick test failed: {e}")
        
        return 0
    else:
        print("✗ Installation verification FAILED")
        print("  Some core components are not accessible.")
        print("  Please reinstall: pip install -e .")
        return 1


if __name__ == "__main__":
    sys.exit(main())
