from ..models import ArtifactEvidence, VerificationResult, sha256_bytes
from .metadata import extract_video_metadata_watermark


def verify_video_artifact(
    suspect_video_bytes: bytes,
    evidence: ArtifactEvidence,
    enable_keyframe_matching: bool = True,
) -> VerificationResult:
    """
    Verify video artifact against stored evidence.

    Multi-tier strategy:
    1. Exact byte match to post-watermark artifact
    2. Exact byte match to pre-watermark artifact
    3. Metadata watermark match
    4. Perceptual hash match
    """

    suspect_hash = sha256_bytes(suspect_video_bytes)

    # Tier 1: exact distributed match
    if suspect_hash == evidence.hashes.content_hash_after_watermark:
        return VerificationResult(
            artifact_id=evidence.artifact_id,
            exact_match_after_watermark=True,
            exact_match_before_watermark=False,
            likely_tag_removed=False,
            watermark_present=True,
            watermark_intact=True,
            content_modified=False,
            notes=["Exact match to watermarked version (Tier 1)."],
            confidence=1.0,
            evidence_record=evidence,
        )

    # Tier 1b: exact original match (watermark removed)
    if suspect_hash == evidence.hashes.content_hash_before_watermark:
        return VerificationResult(
            artifact_id=evidence.artifact_id,
            exact_match_after_watermark=False,
            exact_match_before_watermark=True,
            likely_tag_removed=True,
            watermark_present=False,
            watermark_intact=False,
            content_modified=False,
            notes=["Exact match to original pre-watermark version; watermark likely removed."],
            confidence=0.99,
            evidence_record=evidence,
        )

    notes: list[str] = []
    watermark_present = False
    watermark_intact = False
    normalized_match_after = False
    perceptual_similarity_score = None

    # Tier 2: metadata watermark extraction
    extracted_watermark = extract_video_metadata_watermark(suspect_video_bytes)
    if extracted_watermark:
        watermark_present = True
        if extracted_watermark.get("watermark_id") == evidence.watermark.watermark_id:
            watermark_intact = True
            normalized_match_after = True
            notes.append("Video metadata watermark matches evidence record.")
        else:
            notes.append("Video contains watermark metadata, but watermark_id does not match evidence.")

    # Tier 3: perceptual comparison
    if evidence.hashes.perceptual_hash_after:
        try:
            from ..hashing import perceptual_hash_video

            suspect_perceptual = perceptual_hash_video(suspect_video_bytes)
            if suspect_perceptual == evidence.hashes.perceptual_hash_after:
                perceptual_similarity_score = 1.0
                notes.append("Perceptual video hash matches watermarked artifact.")
            elif (
                evidence.hashes.perceptual_hash_before
                and suspect_perceptual == evidence.hashes.perceptual_hash_before
            ):
                perceptual_similarity_score = 1.0
                notes.append("Perceptual video hash matches pre-watermark artifact.")
        except Exception as exc:
            notes.append(f"Perceptual hash comparison skipped: {exc}")

    # Tier 4 placeholder
    if enable_keyframe_matching and evidence.fingerprints:
        notes.append("Keyframe fragment matching not yet implemented.")

    content_modified = not (
        normalized_match_after or (perceptual_similarity_score and perceptual_similarity_score > 0.0)
    )

    confidence = 0.0
    if watermark_intact:
        confidence = 0.90
    elif perceptual_similarity_score:
        confidence = 0.85
    elif watermark_present:
        confidence = 0.40

    return VerificationResult(
        artifact_id=evidence.artifact_id,
        exact_match_after_watermark=False,
        exact_match_before_watermark=False,
        likely_tag_removed=False,
        normalized_match_before=False,
        normalized_match_after=normalized_match_after,
        perceptual_similarity_score=perceptual_similarity_score,
        simhash_distance=None,
        watermark_present=watermark_present,
        watermark_intact=watermark_intact,
        content_modified=content_modified,
        notes=notes,
        confidence=confidence,
        evidence_record=evidence,
    )
