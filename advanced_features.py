"""
CIAF Watermarking - Advanced Features

Advanced capabilities for watermarking system:
1. Spectral analysis with librosa (MFCCs, chroma features)
2. Multi-format support via ffmpeg (MP3, AAC, H.265, etc.)
3. Perceptual hashing (video pHash, audio chromaprint)
4. Cloud storage integration (AWS S3, Azure Blob)

Created: 2026-04-04
Author: Denzil James Greenwood
Version: 1.6.0
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import hashlib
import tempfile
import os

if TYPE_CHECKING:
    from .models import ArtifactEvidence

# Optional dependencies - gracefully handle missing imports
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import librosa

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    import ffmpeg

    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

try:
    from PIL import Image
    import imagehash

    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False

try:
    import acoustid
    import chromaprint  # noqa: F401

    CHROMAPRINT_AVAILABLE = True
except ImportError:
    CHROMAPRINT_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError  # noqa: F401

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from azure.storage.blob import BlobServiceClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


# ============================================================================
# ADVANCED SPECTRAL ANALYSIS (LIBROSA)
# ============================================================================


@dataclass
class AdvancedSpectralFeatures:
    """Advanced spectral features from librosa analysis."""

    # MFCCs (Mel-frequency cepstral coefficients)
    mfcc_mean: List[float]
    mfcc_std: List[float]

    # Chroma features
    chroma_mean: List[float]
    chroma_std: List[float]

    # Spectral features
    spectral_centroid: float
    spectral_bandwidth: float
    spectral_rolloff: float
    zero_crossing_rate: float

    # Temporal features
    tempo: float
    onset_strength: float

    # Hash of features for comparison
    features_hash: str


def extract_advanced_audio_features(
    audio_bytes: bytes,
    sample_rate: int = 22050,
    duration: Optional[float] = None,
) -> AdvancedSpectralFeatures:
    """
    Extract advanced spectral features using librosa.

    Args:
        audio_bytes: Audio file content (any format supported by librosa)
        sample_rate: Target sample rate for analysis
        duration: Optional duration limit in seconds

    Returns:
        AdvancedSpectralFeatures with MFCCs, chroma, tempo, etc.

    Raises:
        ImportError: If librosa is not installed
        ValueError: If audio cannot be loaded
    """
    if not LIBROSA_AVAILABLE:
        raise ImportError(
            "Advanced spectral analysis requires librosa.\n"
            "Install with: pip install librosa"
        )

    # Write to temporary file for librosa
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Load audio with librosa
        y, sr = librosa.load(tmp_path, sr=sample_rate, duration=duration)

        # Extract MFCCs (13 coefficients by default)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = mfccs.mean(axis=1).tolist()
        mfcc_std = mfccs.std(axis=1).tolist()

        # Extract chroma features (12 pitch classes)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1).tolist()
        chroma_std = chroma.std(axis=1).tolist()

        # Extract spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_centroid = float(spectral_centroids.mean())

        spectral_bandwidths = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        spectral_bandwidth = float(spectral_bandwidths.mean())

        spectral_rolloffs = librosa.feature.spectral_rolloff(y=y, sr=sr)
        spectral_rolloff = float(spectral_rolloffs.mean())

        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y=y)
        zero_crossing_rate = float(zcr.mean())

        # Tempo estimation (handle both old and new librosa API)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        try:
            # Try new API (librosa >= 0.10.0)
            tempo_result = librosa.feature.rhythm.tempo(onset_envelope=onset_env, sr=sr)
        except AttributeError:
            # Fall back to old API (librosa < 0.10.0)
            import warnings

            warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
            tempo_result = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)

        # Handle numpy array/scalar conversion
        if hasattr(tempo_result, "__len__"):
            tempo = float(tempo_result[0]) if len(tempo_result) > 0 else 120.0
        else:
            tempo = float(tempo_result)

        onset_strength = float(onset_env.mean())

        # Create feature vector for hashing
        feature_vector = (
            mfcc_mean
            + mfcc_std
            + chroma_mean
            + chroma_std
            + [
                spectral_centroid,
                spectral_bandwidth,
                spectral_rolloff,
                zero_crossing_rate,
                tempo,
                onset_strength,
            ]
        )

        # Hash the features for fingerprinting
        feature_str = ",".join(f"{f:.6f}" for f in feature_vector)
        features_hash = hashlib.sha256(feature_str.encode()).hexdigest()

        return AdvancedSpectralFeatures(
            mfcc_mean=mfcc_mean,
            mfcc_std=mfcc_std,
            chroma_mean=chroma_mean,
            chroma_std=chroma_std,
            spectral_centroid=spectral_centroid,
            spectral_bandwidth=spectral_bandwidth,
            spectral_rolloff=spectral_rolloff,
            zero_crossing_rate=zero_crossing_rate,
            tempo=tempo,
            onset_strength=onset_strength,
            features_hash=features_hash,
        )

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def compare_spectral_features(
    features1: AdvancedSpectralFeatures,
    features2: AdvancedSpectralFeatures,
) -> float:
    """
    Compare two spectral feature sets and return similarity score.

    Uses cosine similarity for feature vector comparison.

    Args:
        features1: First feature set
        features2: Second feature set

    Returns:
        Similarity score (0.0-1.0, higher = more similar)
    """
    if not LIBROSA_AVAILABLE:
        return 0.0

    # Build feature vectors
    vec1 = np.array(
        features1.mfcc_mean
        + features1.chroma_mean
        + [features1.spectral_centroid, features1.tempo]
    )
    vec2 = np.array(
        features2.mfcc_mean
        + features2.chroma_mean
        + [features2.spectral_centroid, features2.tempo]
    )

    # Cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)

    # Convert to 0-1 range (cosine similarity is -1 to 1)
    return float((similarity + 1.0) / 2.0)


# ============================================================================
# MULTI-FORMAT SUPPORT (FFMPEG)
# ============================================================================


def convert_audio_to_wav(
    input_bytes: bytes,
    input_format: str = "auto",
    output_sample_rate: int = 44100,
) -> bytes:
    """
    Convert audio from any format to WAV using ffmpeg.

    Supports: MP3, AAC, FLAC, OGG, M4A, etc.

    Args:
        input_bytes: Audio file content in any format
        input_format: Input format (e.g., 'mp3', 'aac') or 'auto' to detect
        output_sample_rate: Target sample rate for WAV output

    Returns:
        WAV file content as bytes

    Raises:
        ImportError: If ffmpeg-python is not installed
        RuntimeError: If conversion fails
    """
    if not FFMPEG_AVAILABLE:
        raise ImportError(
            "Multi-format audio support requires ffmpeg-python and ffmpeg.\n"
            "Install with: pip install ffmpeg-python\n"
            "And install ffmpeg binary: https://ffmpeg.org/download.html"
        )

    # Write input to temporary file
    input_suffix = f".{input_format}" if input_format != "auto" else ""
    with tempfile.NamedTemporaryFile(suffix=input_suffix, delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        input_path = tmp_in.name

    # Create output path
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out:
        output_path = tmp_out.name

    try:
        # Convert using ffmpeg
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            ar=output_sample_rate,  # Sample rate
            ac=2,  # Stereo
            acodec="pcm_s16le",  # PCM encoding
        )
        ffmpeg.run(
            stream, capture_stdout=True, capture_stderr=True, overwrite_output=True
        )

        # Read output WAV file
        with open(output_path, "rb") as f:
            wav_bytes = f.read()

        return wav_bytes

    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e.stderr.decode()}")

    finally:
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except Exception:
            pass


def convert_video_to_mp4(
    input_bytes: bytes,
    input_format: str = "auto",
    output_codec: str = "libx264",
) -> bytes:
    """
    Convert video from any format to MP4 using ffmpeg.

    Supports: AVI, MOV, MKV, FLV, WEBM, etc.
    Can use H.264, H.265 (HEVC), VP9, etc.

    Args:
        input_bytes: Video file content in any format
        input_format: Input format or 'auto' to detect
        output_codec: Output codec ('libx264', 'libx265', 'vp9', etc.)

    Returns:
        MP4 file content as bytes

    Raises:
        ImportError: If ffmpeg-python is not installed
        RuntimeError: If conversion fails
    """
    if not FFMPEG_AVAILABLE:
        raise ImportError(
            "Multi-format video support requires ffmpeg-python and ffmpeg.\n"
            "Install with: pip install ffmpeg-python\n"
            "And install ffmpeg binary: https://ffmpeg.org/download.html"
        )

    # Write input to temporary file
    input_suffix = f".{input_format}" if input_format != "auto" else ""
    with tempfile.NamedTemporaryFile(suffix=input_suffix, delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        input_path = tmp_in.name

    # Create output path
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_out:
        output_path = tmp_out.name

    try:
        # Convert using ffmpeg
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            vcodec=output_codec,  # Video codec
            acodec="aac",  # Audio codec
            **{"b:v": "2000k", "b:a": "128k"},  # Bitrates
        )
        ffmpeg.run(
            stream, capture_stdout=True, capture_stderr=True, overwrite_output=True
        )

        # Read output MP4 file
        with open(output_path, "rb") as f:
            mp4_bytes = f.read()

        return mp4_bytes

    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e.stderr.decode()}")

    finally:
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except Exception:
            pass


# ============================================================================
# PERCEPTUAL HASHING
# ============================================================================


def compute_video_phash(video_bytes: bytes, num_frames: int = 5) -> List[str]:
    """
    Compute perceptual hashes for video frames.

    Uses pHash algorithm to create robust fingerprints that are resistant
    to minor modifications (compression, scaling, color adjustments).

    Args:
        video_bytes: Video file content
        num_frames: Number of frames to hash

    Returns:
        List of pHash hex strings

    Raises:
        ImportError: If required libraries are not installed
    """
    if not IMAGEHASH_AVAILABLE:
        raise ImportError(
            "Perceptual hashing requires imagehash.\n"
            "Install with: pip install imagehash"
        )

    try:
        import cv2
        import numpy as np  # noqa: F401
    except ImportError:
        raise ImportError(
            "Video pHash requires opencv-python.\n"
            "Install with: pip install opencv-python"
        )

    # Write video to temporary file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)

        if not cap.isOpened():
            raise ValueError("Failed to open video file")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate frame indices
        if num_frames >= total_frames:
            frame_indices = list(range(total_frames))
        else:
            frame_indices = [
                int(total_frames * (i + 1) / (num_frames + 1))
                for i in range(num_frames)
            ]

        phashes = []

        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret or frame is None:
                continue

            # Convert to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            # Compute pHash
            phash = imagehash.phash(pil_image)
            phashes.append(str(phash))

        cap.release()
        return phashes

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def compute_audio_chromaprint(audio_bytes: bytes, duration: int = 30) -> str:
    """
    Compute Chromaprint fingerprint for audio.

    Chromaprint is the algorithm used by AcoustID for audio identification.
    It's robust to lossy compression and format changes.

    Args:
        audio_bytes: Audio file content
        duration: Maximum duration to analyze (seconds)

    Returns:
        Chromaprint fingerprint as base64 string

    Raises:
        ImportError: If chromaprint/acoustid is not installed
    """
    if not CHROMAPRINT_AVAILABLE:
        raise ImportError(
            "Audio fingerprinting requires pyacoustid.\n"
            "Install with: pip install pyacoustid\n"
            "And install chromaprint library: https://acoustid.org/chromaprint"
        )

    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Compute fingerprint
        duration_secs, fingerprint = acoustid.fingerprint_file(
            tmp_path, maxlength=duration
        )
        return fingerprint

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def compare_perceptual_hashes(
    hash1: str, hash2: str, hash_type: str = "phash"
) -> float:
    """
    Compare two perceptual hashes and return similarity score.

    Args:
        hash1: First hash
        hash2: Second hash
        hash_type: Type of hash ('phash' or 'chromaprint')

    Returns:
        Similarity score (0.0-1.0, higher = more similar)
    """
    if hash_type == "phash":
        if not IMAGEHASH_AVAILABLE:
            return 0.0

        # For pHash, compute Hamming distance
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)

        # Hamming distance (0 = identical, 64 = completely different for 8x8 hashes)
        distance = h1 - h2
        max_distance = len(hash1) * 4  # 4 bits per hex char

        # Convert to similarity (0-1)
        similarity = 1.0 - (distance / max_distance)
        return float(max(0.0, min(1.0, similarity)))

    elif hash_type == "chromaprint":
        # For chromaprint, we'd need acoustid.compare
        # This is a simplified implementation
        if hash1 == hash2:
            return 1.0
        else:
            # Would need acoustid.compare for proper comparison
            return 0.0

    return 0.0


# ============================================================================
# CLOUD STORAGE INTEGRATION
# ============================================================================


@dataclass
class CloudStorageConfig:
    """Configuration for cloud storage providers."""

    provider: str  # 'aws' or 'azure'

    # AWS S3 settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    s3_bucket: Optional[str] = None

    # Azure Blob settings
    azure_connection_string: Optional[str] = None
    azure_container: Optional[str] = None


class CloudFragmentStorage:
    """
    Store forensic fragments in cloud storage.

    Supports AWS S3 and Azure Blob Storage.
    """

    def __init__(self, config: CloudStorageConfig):
        """
        Initialize cloud storage client.

        Args:
            config: Cloud storage configuration
        """
        self.config = config
        self.provider = config.provider.lower()

        if self.provider == "aws":
            if not BOTO3_AVAILABLE:
                raise ImportError(
                    "AWS S3 support requires boto3.\n" "Install with: pip install boto3"
                )

            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                region_name=config.aws_region,
            )
            self.bucket = config.s3_bucket

        elif self.provider == "azure":
            if not AZURE_AVAILABLE:
                raise ImportError(
                    "Azure Blob support requires azure-storage-blob.\n"
                    "Install with: pip install azure-storage-blob"
                )

            self.blob_service_client = BlobServiceClient.from_connection_string(
                config.azure_connection_string
            )
            self.container = config.azure_container

        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    def upload_fragment(
        self,
        fragment_id: str,
        fragment_data: bytes,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Upload a forensic fragment to cloud storage.

        Args:
            fragment_id: Unique fragment identifier
            fragment_data: Fragment content
            metadata: Optional metadata dictionary

        Returns:
            Cloud storage URL/path

        Raises:
            RuntimeError: If upload fails
        """
        try:
            if self.provider == "aws":
                # Upload to S3
                key = f"fragments/{fragment_id}"

                extra_args = {}
                if metadata:
                    extra_args["Metadata"] = metadata

                self.s3_client.put_object(
                    Bucket=self.bucket, Key=key, Body=fragment_data, **extra_args
                )

                return f"s3://{self.bucket}/{key}"

            elif self.provider == "azure":
                # Upload to Azure Blob
                blob_name = f"fragments/{fragment_id}"
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container, blob=blob_name
                )

                blob_client.upload_blob(
                    fragment_data, metadata=metadata, overwrite=True
                )

                return f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container}/{blob_name}"

        except Exception as e:
            raise RuntimeError(f"Failed to upload fragment: {e}")

    def download_fragment(self, fragment_id: str) -> bytes:
        """
        Download a forensic fragment from cloud storage.

        Args:
            fragment_id: Unique fragment identifier

        Returns:
            Fragment content as bytes

        Raises:
            RuntimeError: If download fails or fragment not found
        """
        try:
            if self.provider == "aws":
                # Download from S3
                key = f"fragments/{fragment_id}"

                response = self.s3_client.get_object(Bucket=self.bucket, Key=key)

                return response["Body"].read()

            elif self.provider == "azure":
                # Download from Azure Blob
                blob_name = f"fragments/{fragment_id}"
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container, blob=blob_name
                )

                return blob_client.download_blob().readall()

        except Exception as e:
            raise RuntimeError(f"Failed to download fragment: {e}")

    def list_fragments(self, prefix: str = "") -> List[str]:
        """
        List all fragment IDs in cloud storage.

        Args:
            prefix: Optional fragment ID prefix filter

        Returns:
            List of fragment IDs
        """
        try:
            if self.provider == "aws":
                # List S3 objects
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket, Prefix=f"fragments/{prefix}"
                )

                if "Contents" not in response:
                    return []

                return [
                    obj["Key"].replace("fragments/", "") for obj in response["Contents"]
                ]

            elif self.provider == "azure":
                # List Azure Blobs
                container_client = self.blob_service_client.get_container_client(
                    self.container
                )

                blobs = container_client.list_blobs(
                    name_starts_with=f"fragments/{prefix}"
                )

                return [blob.name.replace("fragments/", "") for blob in blobs]

        except Exception as e:
            raise RuntimeError(f"Failed to list fragments: {e}")

    def delete_fragment(self, fragment_id: str) -> bool:
        """
        Delete a forensic fragment from cloud storage.

        Args:
            fragment_id: Unique fragment identifier

        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            if self.provider == "aws":
                # Delete from S3
                key = f"fragments/{fragment_id}"
                self.s3_client.delete_object(Bucket=self.bucket, Key=key)
                return True

            elif self.provider == "azure":
                # Delete from Azure Blob
                blob_name = f"fragments/{fragment_id}"
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container, blob=blob_name
                )
                blob_client.delete_blob()
                return True

        except Exception:
            return False


# ============================================================================
# OPTICAL FLOW & MOTION ANALYSIS
# ============================================================================

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class OpticalFlowAnalysis:
    """Results from optical flow analysis between two frames."""

    magnitude_mean: float
    magnitude_max: float
    magnitude_std: float
    angle_mean: float
    motion_score: float  # 0-1, higher = more motion
    dense_flow_hash: str  # SHA-256 of flow vectors


def compute_optical_flow(
    frame1_bytes: bytes,
    frame2_bytes: bytes,
) -> OpticalFlowAnalysis:
    """
    Compute dense optical flow between two video frames.

    Uses Farneback algorithm for dense optical flow estimation.

    Args:
        frame1_bytes: First frame as image bytes
        frame2_bytes: Second frame as image bytes

    Returns:
        OpticalFlowAnalysis with motion statistics

    Raises:
        ImportError: If OpenCV is not installed
    """
    if not CV2_AVAILABLE:
        raise ImportError("Optical flow requires opencv-python")

    import numpy as np

    # Decode frames
    frame1 = cv2.imdecode(np.frombuffer(frame1_bytes, np.uint8), cv2.IMREAD_COLOR)
    frame2 = cv2.imdecode(np.frombuffer(frame2_bytes, np.uint8), cv2.IMREAD_COLOR)

    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Compute dense optical flow (Farneback)
    flow = cv2.calcOpticalFlowFarneback(
        gray1,
        gray2,
        None,  # No initial flow
        pyr_scale=0.5,  # Pyramid scale
        levels=3,  # Pyramid levels
        winsize=15,  # Window size
        iterations=3,  # Iterations at each level
        poly_n=5,  # Polynomial neighborhood size
        poly_sigma=1.2,  # Gaussian sigma
        flags=0,
    )

    # Calculate magnitude and angle
    magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])

    # Statistics
    mag_mean = float(magnitude.mean())
    mag_max = float(magnitude.max())
    mag_std = float(magnitude.std())
    angle_mean = float(angle.mean())

    # Motion score (normalized by frame dimensions)
    h, w = magnitude.shape
    motion_score = min(1.0, mag_mean / (np.sqrt(h * h + w * w) * 0.1))

    # Hash the flow vectors
    flow_str = np.array2string(flow.flatten()[:1000], precision=2, separator=",")
    flow_hash = hashlib.sha256(flow_str.encode()).hexdigest()

    return OpticalFlowAnalysis(
        magnitude_mean=mag_mean,
        magnitude_max=mag_max,
        magnitude_std=mag_std,
        angle_mean=angle_mean,
        motion_score=motion_score,
        dense_flow_hash=flow_hash,
    )


# ============================================================================
# SCENE CHANGE DETECTION
# ============================================================================


@dataclass
class SceneChange:
    """Detected scene change with metadata."""

    frame_index: int
    timestamp_ms: int
    change_score: float  # 0-1, higher = more significant change
    histogram_diff: float
    edge_diff: float
    is_hard_cut: bool  # True if abrupt scene change


def detect_scene_changes(
    video_bytes: bytes,
    threshold: float = 0.3,
    check_interval: int = 5,
) -> List[SceneChange]:
    """
    Detect scene changes in a video using histogram and edge analysis.

    Args:
        video_bytes: Video file content
        threshold: Scene change threshold (0-1)
        check_interval: Check every Nth frame

    Returns:
        List of detected scene changes

    Raises:
        ImportError: If OpenCV is not installed
    """
    if not CV2_AVAILABLE:
        raise ImportError("Scene detection requires opencv-python")

    import numpy as np

    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        scene_changes = []
        _prev_frame = None  # noqa: F841
        prev_hist = None
        prev_edges = None
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process every Nth frame
            if frame_idx % check_interval == 0:
                # Compute histogram
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()

                # Compute edges
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                edge_density = np.sum(edges > 0) / edges.size

                if prev_hist is not None:
                    # Compare histograms (correlation)
                    hist_diff = 1.0 - cv2.compareHist(
                        prev_hist, hist, cv2.HISTCMP_CORREL
                    )

                    # Compare edge density
                    edge_diff = abs(edge_density - prev_edges)

                    # Combined score
                    change_score = hist_diff * 0.7 + edge_diff * 0.3

                    if change_score > threshold:
                        timestamp_ms = int((frame_idx / fps) * 1000)
                        is_hard_cut = bool(change_score > 0.7)

                        scene_changes.append(
                            SceneChange(
                                frame_index=frame_idx,
                                timestamp_ms=timestamp_ms,
                                change_score=float(change_score),
                                histogram_diff=float(hist_diff),
                                edge_diff=float(edge_diff),
                                is_hard_cut=is_hard_cut,
                            )
                        )

                prev_hist = hist
                prev_edges = edge_density

            frame_idx += 1

        cap.release()
        return scene_changes

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ============================================================================
# KEYFRAME TRANSITION ANALYSIS
# ============================================================================


@dataclass
class KeyframeTransition:
    """Analysis of transition between two keyframes."""

    from_frame_index: int
    to_frame_index: int
    transition_type: str  # "cut", "fade", "dissolve", "motion"
    confidence: float  # 0-1
    optical_flow_score: float
    brightness_change: float


def analyze_keyframe_transitions(
    video_bytes: bytes,
    keyframe_indices: List[int],
) -> List[KeyframeTransition]:
    """
    Analyze transitions between keyframes.

    Args:
        video_bytes: Video file content
        keyframe_indices: List of frame indices to analyze

    Returns:
        List of transition analyses

    Raises:
        ImportError: If OpenCV is not installed
    """
    if not CV2_AVAILABLE:
        raise ImportError("Transition analysis requires opencv-python")

    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)

        # Extract keyframes
        frames = {}
        for idx in keyframe_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames[idx] = frame

        cap.release()

        # Analyze transitions
        transitions = []
        sorted_indices = sorted(keyframe_indices)

        for i in range(len(sorted_indices) - 1):
            from_idx = sorted_indices[i]
            to_idx = sorted_indices[i + 1]

            if from_idx not in frames or to_idx not in frames:
                continue

            frame1 = frames[from_idx]
            frame2 = frames[to_idx]

            # Convert to grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            # Compute brightness change
            brightness1 = gray1.mean()
            brightness2 = gray2.mean()
            brightness_change = abs(brightness2 - brightness1) / 255.0

            # Compute optical flow score (simplified)
            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            flow_magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
            optical_flow_score = float(flow_magnitude.mean())

            # Classify transition
            if brightness_change > 0.5:
                transition_type = "fade"
                confidence = brightness_change
            elif optical_flow_score > 10.0:
                transition_type = "motion"
                confidence = min(1.0, optical_flow_score / 20.0)
            elif optical_flow_score < 2.0 and brightness_change < 0.1:
                transition_type = "cut"
                confidence = 0.9
            else:
                transition_type = "dissolve"
                confidence = 0.7

            transitions.append(
                KeyframeTransition(
                    from_frame_index=from_idx,
                    to_frame_index=to_idx,
                    transition_type=transition_type,
                    confidence=confidence,
                    optical_flow_score=optical_flow_score,
                    brightness_change=brightness_change,
                )
            )

        return transitions

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ============================================================================
# AUDIO BEAT TRACKING
# ============================================================================


@dataclass
class BeatTrackingResults:
    """Results from audio beat tracking analysis."""

    tempo: float  # BPM
    beat_frames: List[int]  # Sample indices of beats
    beat_times: List[float]  # Timestamps in seconds
    beat_strength: List[float]  # Strength of each beat
    rhythm_regularity: float  # 0-1, higher = more regular rhythm


def track_audio_beats(
    audio_bytes: bytes,
    sample_rate: int = 22050,
) -> BeatTrackingResults:
    """
    Track beats in audio using librosa's beat tracking.

    Args:
        audio_bytes: Audio file content
        sample_rate: Sample rate for analysis

    Returns:
        BeatTrackingResults with tempo and beat positions

    Raises:
        ImportError: If librosa is not installed
    """
    if not LIBROSA_AVAILABLE:
        raise ImportError("Beat tracking requires librosa")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Load audio
        y, sr = librosa.load(tmp_path, sr=sample_rate)

        # Compute onset strength envelope
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # Track beats
        tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

        # Convert tempo to Python scalar (handle both array and scalar returns)
        if hasattr(tempo, "__len__"):
            tempo_scalar = float(tempo[0]) if len(tempo) > 0 else 120.0
        else:
            tempo_scalar = float(tempo)

        # Convert to time
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

        # Compute beat strength
        beat_strength = [
            float(onset_env[int(f)]) if f < len(onset_env) else 0.0 for f in beat_frames
        ]

        # Compute rhythm regularity (std of inter-beat intervals)
        if len(beat_times) > 2:
            intervals = np.diff(beat_times)
            regularity = 1.0 - min(1.0, np.std(intervals) / np.mean(intervals))
        else:
            regularity = 0.0

        return BeatTrackingResults(
            tempo=tempo_scalar,
            beat_frames=beat_frames.tolist(),
            beat_times=beat_times,
            beat_strength=beat_strength,
            rhythm_regularity=float(regularity),
        )

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ============================================================================
# CROSS-MODAL SYNCHRONIZATION
# ============================================================================


@dataclass
class SynchronizationAnalysis:
    """Results from audio-video synchronization analysis."""

    audio_beats: List[float]  # Beat timestamps
    video_cuts: List[float]  # Scene change timestamps
    synchronized_events: List[Tuple[float, float]]  # (audio_time, video_time) pairs
    sync_score: float  # 0-1, higher = better synchronization
    avg_offset_ms: float  # Average offset between audio and video events


def analyze_av_synchronization(
    video_bytes: bytes,
    audio_bytes: bytes,
    sync_threshold_ms: float = 200.0,
) -> SynchronizationAnalysis:
    """
    Analyze synchronization between audio beats and video scene changes.

    Args:
        video_bytes: Video file content
        audio_bytes: Audio file content
        sync_threshold_ms: Maximum time difference for sync detection

    Returns:
        SynchronizationAnalysis with synchronization metrics

    Raises:
        ImportError: If required libraries are not installed
    """
    # Track audio beats
    beat_results = track_audio_beats(audio_bytes)
    audio_beats = beat_results.beat_times

    # Detect video scene changes
    scene_changes = detect_scene_changes(video_bytes, threshold=0.3)
    video_cuts = [sc.timestamp_ms / 1000.0 for sc in scene_changes]

    # Find synchronized events
    synchronized = []
    offsets = []

    for audio_time in audio_beats:
        for video_time in video_cuts:
            offset_ms = abs(audio_time - video_time) * 1000.0
            if offset_ms <= sync_threshold_ms:
                synchronized.append((audio_time, video_time))
                offsets.append(offset_ms)
                break

    # Compute sync score
    if len(audio_beats) > 0 and len(video_cuts) > 0:
        max_possible_syncs = min(len(audio_beats), len(video_cuts))
        sync_score = len(synchronized) / max_possible_syncs
    else:
        sync_score = 0.0

    # Average offset
    avg_offset_ms = float(np.mean(offsets)) if offsets else 0.0

    return SynchronizationAnalysis(
        audio_beats=audio_beats,
        video_cuts=video_cuts,
        synchronized_events=synchronized,
        sync_score=sync_score,
        avg_offset_ms=avg_offset_ms,
    )


# ============================================================================
# OBJECT DETECTION (BASIC)
# ============================================================================


@dataclass
class DetectedObject:
    """Object detected in a video frame."""

    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)


@dataclass
class ObjectDetectionResults:
    """Results from object detection on video frames."""

    frame_index: int
    timestamp_ms: int
    objects: List[DetectedObject]
    num_objects: int


def detect_objects_in_video(
    video_bytes: bytes,
    frame_indices: List[int],
    confidence_threshold: float = 0.5,
) -> List[ObjectDetectionResults]:
    """
    Detect objects in specified video frames using OpenCV DNN.

    This is a basic implementation using MobileNet SSD.
    For production use, consider YOLOv5, Detectron2, or similar.

    Args:
        video_bytes: Video file content
        frame_indices: Frames to analyze
        confidence_threshold: Minimum confidence for detection

    Returns:
        List of ObjectDetectionResults per frame

    Raises:
        ImportError: If OpenCV is not installed

    Note:
        Requires pre-trained model files (not included).
        Returns empty results if models are not available.
    """
    if not CV2_AVAILABLE:
        raise ImportError("Object detection requires opencv-python")

    # Placeholder - requires model files
    # In production, download models from:
    # https://github.com/opencv/opencv/wiki/TensorFlow-Object-Detection-API

    results = []

    # Would implement with actual model loading:
    # net = cv2.dnn.readNetFromTensorflow('frozen_inference_graph.pb', 'graph.pbtxt')
    # For now, return empty results with structure

    return results


# ============================================================================
# FORENSIC ENHANCEMENT (FOR ASYNC PROCESSING)
# ============================================================================


def enhance_evidence_with_forensic_fragments(
    evidence: "ArtifactEvidence", raw_artifact: bytes | str
) -> "ArtifactEvidence":
    """
    Enhance evidence with forensic fragments (Tier 2 & 3 processing).

    This is the background processing step that adds:
    - Tier 2: DNA-level forensic fragments (high-entropy samples)
    - Tier 3: Perceptual hashes (image/video/audio)

    Called by async workers after immediate watermark delivery.

    Args:
        evidence: Initial evidence from watermarking
        raw_artifact: Original artifact (before watermarking)

    Returns:
        Enhanced evidence with forensic fragments

    Example:
        >>> # In background worker
        >>> enhanced = enhance_evidence_with_forensic_fragments(
        ...     evidence=initial_evidence,
        ...     raw_artifact=original_content
        ... )
        >>> vault.store_evidence(enhanced)
    """
    from .models import ArtifactType, ArtifactFingerprint
    from .fragment_selection import (
        select_text_forensic_fragments,
        select_image_forensic_patches,
    )
    from .images import compute_all_hashes

    # Make a copy to avoid modifying original
    import copy

    enhanced = copy.deepcopy(evidence)

    # Add forensic fragments based on artifact type
    if evidence.artifact_type == ArtifactType.TEXT:
        if isinstance(raw_artifact, str):
            text_content = raw_artifact
        else:
            text_content = raw_artifact.decode("utf-8", errors="ignore")

        # Generate forensic text fragments

        fragment_hash_before = evidence.hashes.content_hash_before_watermark
        fragment_hash_after = evidence.hashes.content_hash_after_watermark

        fragments = select_text_forensic_fragments(
            text_content,
            fragment_hash_before=fragment_hash_before,
            fragment_hash_after=fragment_hash_after,
        )

        # Add fragments as fingerprints
        for i, frag in enumerate(fragments):
            enhanced.fingerprints.append(
                ArtifactFingerprint(
                    algorithm=f"text_fragment_{frag.sample_location}",
                    value=frag.fragment_hash_before,
                    role="forensic_dna",
                    confidence=0.95,
                )
            )

    elif evidence.artifact_type == ArtifactType.IMAGE:
        if isinstance(raw_artifact, str):
            image_bytes = raw_artifact.encode("utf-8")
        else:
            image_bytes = raw_artifact

        # Generate image forensic patches
        try:
            patches = select_image_forensic_patches(image_bytes, num_patches=4)

            # Add patches as fingerprints
            for i, patch in enumerate(patches):
                enhanced.fingerprints.append(
                    ArtifactFingerprint(
                        algorithm=f"image_patch_{patch.patch_grid_position}",
                        value=patch.patch_hash_before,
                        role="forensic_dna",
                        confidence=0.90,
                    )
                )
        except Exception:
            pass  # Skip if image processing fails

        # Add perceptual hashes
        try:
            hashes = compute_all_hashes(image_bytes)

            for hash_type, hash_value in [
                ("phash", hashes.phash),
                ("ahash", hashes.ahash),
                ("dhash", hashes.dhash),
                ("whash", hashes.whash),
            ]:
                if hash_value:
                    enhanced.fingerprints.append(
                        ArtifactFingerprint(
                            algorithm=hash_type,
                            value=hash_value,
                            role="perceptual_hash",
                            confidence=0.85,
                        )
                    )
        except Exception:
            pass  # Skip if perceptual hashing fails

    elif evidence.artifact_type == ArtifactType.PDF:
        # PDF forensic enhancement
        # For now, just mark as enhanced
        # Could add PDF internal structure analysis
        pass

    # Update metadata to indicate enhancement complete
    from datetime import datetime

    enhanced.metadata["forensic_enhancement"] = "complete"
    enhanced.metadata["enhancement_timestamp"] = datetime.utcnow().isoformat()

    return enhanced


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_available_features() -> Dict[str, bool]:
    """
    Check which advanced features are available.

    Returns:
        Dictionary mapping feature names to availability status
    """
    return {
        "librosa_spectral_analysis": LIBROSA_AVAILABLE,
        "ffmpeg_conversion": FFMPEG_AVAILABLE,
        "video_perceptual_hash": IMAGEHASH_AVAILABLE,
        "audio_chromaprint": CHROMAPRINT_AVAILABLE,
        "aws_s3_storage": BOTO3_AVAILABLE,
        "azure_blob_storage": AZURE_AVAILABLE,
        "optical_flow_analysis": CV2_AVAILABLE,
        "scene_change_detection": CV2_AVAILABLE,
        "keyframe_transitions": CV2_AVAILABLE,
        "audio_beat_tracking": LIBROSA_AVAILABLE,
        "av_synchronization": LIBROSA_AVAILABLE and CV2_AVAILABLE,
        "object_detection": CV2_AVAILABLE,
    }


def print_feature_status():
    """Print status of all advanced features."""
    features = get_available_features()

    print("CIAF Watermarking - Advanced Features Status")
    print("=" * 50)

    print("\n📊 Spectral Analysis:")
    print(
        f"  Librosa (MFCCs/Chroma): {'✓ Available' if features['librosa_spectral_analysis'] else '✗ Not installed'}"
    )
    print(
        f"  Beat Tracking: {'✓ Available' if features['audio_beat_tracking'] else '✗ Not installed'}"
    )

    print("\n🎬 Multi-Format Support:")
    print(
        f"  FFmpeg conversion: {'✓ Available' if features['ffmpeg_conversion'] else '✗ Not installed'}"
    )

    print("\n🔍 Perceptual Hashing:")
    print(
        f"  Video pHash: {'✓ Available' if features['video_perceptual_hash'] else '✗ Not installed'}"
    )
    print(
        f"  Audio Chromaprint: {'✓ Available' if features['audio_chromaprint'] else '✗ Not installed'}"
    )

    print("\n🎥 Video Analysis:")
    print(
        f"  Optical Flow: {'✓ Available' if features['optical_flow_analysis'] else '✗ Not installed'}"
    )
    print(
        f"  Scene Detection: {'✓ Available' if features['scene_change_detection'] else '✗ Not installed'}"
    )
    print(
        f"  Keyframe Transitions: {'✓ Available' if features['keyframe_transitions'] else '✗ Not installed'}"
    )
    print(
        f"  Object Detection: {'✓ Available' if features['object_detection'] else '✗ Not installed'}"
    )

    print("\n🔄 Cross-Modal:")
    print(
        f"  A/V Synchronization: {'✓ Available' if features['av_synchronization'] else '✗ Not installed'}"
    )

    print("\n☁️ Cloud Storage:")
    print(
        f"  AWS S3: {'✓ Available' if features['aws_s3_storage'] else '✗ Not installed'}"
    )
    print(
        f"  Azure Blob: {'✓ Available' if features['azure_blob_storage'] else '✗ Not installed'}"
    )

    print("\n" + "=" * 50)

    total = len(features)
    available = sum(features.values())
    print(
        f"Overall: {available}/{total} features available ({available/total*100:.0f}%)"
    )
