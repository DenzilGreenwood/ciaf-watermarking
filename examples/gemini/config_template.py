# Gemini + CIAF Configuration Template

# Copy this file and customize for your project
# Save as: config.py or gemini_config.py

import os
from typing import Dict, Any

# ============================================================================
# GEMINI API CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# Default Gemini model
GEMINI_MODEL = "gemini-pro"
GEMINI_VERSION = "1.5"  # Or use date: "2024-03"

# Gemini generation config (optional)
GEMINI_GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# ============================================================================
# CIAF WATERMARKING CONFIGURATION
# ============================================================================

# Where to verify watermarked content
# Options:
#   - Your public API: "https://verify.yourapp.com"
#   - Local dev: "http://localhost:8000/verify"
#   - None: No verification URL embedded
VERIFICATION_BASE_URL = os.environ.get("VERIFICATION_URL", "https://verify.example.com")

# Evidence storage strategy
# Options:
#   - "json": Save to local JSON files
#   - "mongodb": Use MongoDB vault (requires setup)
#   - "s3": AWS S3 (requires AWS credentials)
EVIDENCE_STORAGE = "json"

# Evidence storage path (if using JSON)
EVIDENCE_DIR = "./evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# MongoDB config (if using mongodb storage)
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = "watermark_vault"
MONGODB_COLLECTION = "evidence"

# ============================================================================
# WATERMARK STYLE CONFIGURATION
# ============================================================================

# Text watermark styles
TEXT_WATERMARK_CONFIG = {
    "style": "footer",  # Options: "footer", "header", "inline"
    "include_simhash": True,  # Enable perceptual similarity matching
}

# Image watermark config (if using Gemini for images)
IMAGE_WATERMARK_CONFIG = {
    "mode": "visual",  # Options: "visual", "qr"
    "opacity": 0.4,  # 0.0-1.0 for visual watermarks
    "position": "bottom_right",  # "top_left", "top_right", "bottom_left", "bottom_right", "center"
    "include_qr": True,  # Add QR code with verification URL
    "qr_position": "top_right",
}

# PDF watermark config
PDF_WATERMARK_CONFIG = {
    "mode": "metadata",  # Options: "metadata", "visual"
    "add_visual_qr": False,
}

# ============================================================================
# CIAF GLOBAL DEFAULTS
# ============================================================================

CIAF_GLOBAL_CONFIG: Dict[str, Any] = {
    "verification_base_url": VERIFICATION_BASE_URL,
    "store_in_vault": (EVIDENCE_STORAGE == "mongodb"),
    "enable_forensic_fragments": True,  # Always recommended
    "text": TEXT_WATERMARK_CONFIG,
    "image": IMAGE_WATERMARK_CONFIG,
    "pd": PDF_WATERMARK_CONFIG,
}

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

# Your application identifier
APP_NAME = "my-gemini-app"
APP_VERSION = "1.0.0"

# User ID format for actor_id
# Examples:
#   - "user:{email}"
#   - "session:{session_id}"
#   - "api_key:{key_hash}"
ACTOR_ID_PREFIX = "user"

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_WATERMARKING_OPERATIONS = True
LOG_VERIFICATION_REQUESTS = True

# ============================================================================
# VERIFICATION CONFIGURATION
# ============================================================================

# Verification confidence thresholds
VERIFICATION_THRESHOLDS = {
    "high_confidence": 0.95,  # Tier 1: Exact match
    "medium_confidence": 0.80,  # Tier 2: Fragment match
    "low_confidence": 0.70,  # Tier 3: Similarity match
}

# Cache verification results (optional)
CACHE_VERIFICATION_RESULTS = False
VERIFICATION_CACHE_TTL = 3600  # seconds

# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================

# Async processing (for background evidence generation)
ENABLE_ASYNC_PROCESSING = False
ASYNC_WORKER_THREADS = 4

# Batch processing
BATCH_SIZE = 10  # Process N requests together
ENABLE_BATCH_PROCESSING = False

# Rate limiting (if applicable)
RATE_LIMIT_ENABLED = False
RATE_LIMIT_REQUESTS_PER_MINUTE = 60

# ============================================================================
# ERROR HANDLING CONFIGURATION
# ============================================================================

# What to do if watermarking fails
WATERMARK_FAILURE_STRATEGY = "degrade_gracefully"
# Options:
#   - "raise_error": Fail the request
#   - "degrade_gracefully": Return unwatermarked content with warning
#   - "retry": Retry watermarking N times

WATERMARK_RETRY_ATTEMPTS = 3
WATERMARK_RETRY_DELAY = 1.0  # seconds

# What to do if evidence storage fails
EVIDENCE_STORAGE_FAILURE_STRATEGY = "log_and_continue"
# Options:
#   - "raise_error": Fail the request
#   - "log_and_continue": Log error, continue serving watermarked content
#   - "queue_retry": Queue for background retry

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Hash prompts containing PII
HASH_PROMPTS_WITH_PII = True
PII_PATTERNS = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b\d{16}\b",  # Credit card
]

# Encrypt evidence at rest
ENCRYPT_EVIDENCE = False  # Set True for production
ENCRYPTION_KEY = os.environ.get("EVIDENCE_ENCRYPTION_KEY")

# API authentication (for verification endpoint)
REQUIRE_API_AUTH = True
API_KEY_HEADER = "X-API-Key"
VALID_API_KEYS = set(os.environ.get("VALID_API_KEYS", "").split(","))

# ============================================================================
# MONITORING CONFIGURATION
# ============================================================================

# Metrics
ENABLE_METRICS = False
METRICS_PORT = 9090  # Prometheus metrics

# Track these metrics:
#   - watermarking_requests_total
#   - watermarking_latency_seconds
#   - verification_requests_total
#   - verification_confidence_score
#   - evidence_storage_failures_total

# Health check endpoint
ENABLE_HEALTH_CHECK = True
HEALTH_CHECK_PATH = "/health"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_actor_id(user_identifier: str) -> str:
    """
    Format actor_id from user identifier.

    Args:
        user_identifier: Email, session ID, or other identifier

    Returns:
        Formatted actor_id string
    """
    return f"{ACTOR_ID_PREFIX}:{user_identifier}"


def get_watermark_config(artifact_type: str = "text") -> Dict[str, Any]:
    """
    Get watermark config for specific artifact type.

    Args:
        artifact_type: "text", "image", or "pd"

    Returns:
        Configuration dictionary
    """
    config_map = {
        "text": TEXT_WATERMARK_CONFIG,
        "image": IMAGE_WATERMARK_CONFIG,
        "pdf": PDF_WATERMARK_CONFIG,
    }
    return config_map.get(artifact_type, {})


def get_evidence_path(artifact_id: str) -> str:
    """
    Get file path for storing evidence JSON.

    Args:
        artifact_id: Unique artifact identifier

    Returns:
        Full path to evidence file
    """
    import os

    return os.path.join(EVIDENCE_DIR, f"{artifact_id}.json")


def should_hash_prompt(prompt: str) -> bool:
    """
    Check if prompt contains PII and should be hashed.

    Args:
        prompt: User's input prompt

    Returns:
        True if prompt should be hashed before storage
    """
    if not HASH_PROMPTS_WITH_PII:
        return False

    import re

    for pattern in PII_PATTERNS:
        if re.search(pattern, prompt):
            return True
    return False


def hash_prompt(prompt: str) -> str:
    """
    Hash prompt containing PII.

    Args:
        prompt: Original prompt

    Returns:
        SHA-256 hash of prompt
    """
    import hashlib

    return hashlib.sha256(prompt.encode()).hexdigest()


# ============================================================================
# VALIDATION
# ============================================================================


def validate_config():
    """Validate configuration on startup."""
    errors = []

    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY not set")

    if EVIDENCE_STORAGE == "mongodb" and not MONGODB_URI:
        errors.append("MONGODB_URI not set but mongodb storage selected")

    if ENCRYPT_EVIDENCE and not ENCRYPTION_KEY:
        errors.append("ENCRYPT_EVIDENCE=True but ENCRYPTION_KEY not set")

    if REQUIRE_API_AUTH and not VALID_API_KEYS:
        errors.append("REQUIRE_API_AUTH=True but no VALID_API_KEYS configured")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# ============================================================================
# INITIALIZATION
# ============================================================================


def initialize_ciaf():
    """Initialize CIAF watermarking with global config."""
    from ciaf_watermarks import set_default_watermark_config

    set_default_watermark_config(CIAF_GLOBAL_CONFIG)
    print("✓ CIAF watermarking initialized")
    print(f"  - Verification URL: {VERIFICATION_BASE_URL}")
    print(f"  - Evidence storage: {EVIDENCE_STORAGE}")
    print(f"  - Forensic fragments: {CIAF_GLOBAL_CONFIG['enable_forensic_fragments']}")


def initialize_gemini():
    """Initialize Gemini API client."""
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    print("✓ Gemini API initialized")
    print(f"  - Model: {GEMINI_MODEL}")
    print(f"  - Version: {GEMINI_VERSION}")


def initialize_all():
    """Initialize all systems."""
    print("Initializing Gemini + CIAF integration...")
    validate_config()
    initialize_gemini()
    initialize_ciaf()
    print("✓ Initialization complete\n")


# Auto-initialize on import (optional)
# Uncomment to auto-initialize when config is imported
# initialize_all()

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
Example usage in your application:

from config import (
    GEMINI_MODEL,
    CIAF_GLOBAL_CONFIG,
    get_actor_id,
    get_evidence_path,
    initialize_all
)

# Initialize once at startup
initialize_all()

# Use in your code
actor_id = get_actor_id(user_email)
evidence_file = get_evidence_path(artifact_id)
"""
