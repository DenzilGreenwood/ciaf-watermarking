"""
Google Gemini + CIAF Watermarking - Batch Processing Example

Demonstrates watermarking multiple Gemini generations in batch mode.
Useful for bulk content generation, report creation, or dataset preparation.

Usage:
    export GEMINI_API_KEY="your-key-here"
    python 04_batch_processing.py

Features:
    - Process multiple prompts efficiently
    - Watermark all outputs
    - Track processing statistics
    - Save batch evidence records
"""

import os
import json
from datetime import datetime

# from concurrent.futures import ThreadPoolExecutor, as_completed Uncomment if using parallel processing see Option B: Parallel processing (uncomment to use)
import google.generativeai as genai
from ciaf_watermarks import watermark_ai_output


def process_single_prompt(prompt_data, model, batch_id):
    """
    Process a single prompt with Gemini and watermark the result.

    Args:
        prompt_data: Dict with 'id', 'prompt', and optional 'context'
        model: Gemini model instance
        batch_id: Batch identifier for tracking

    Returns:
        Dict with results and evidence
    """
    prompt_id = prompt_data["id"]
    prompt_text = prompt_data["prompt"]
    context = prompt_data.get("context", "")

    print(f"   ⏳ Processing prompt {prompt_id}...", flush=True)

    try:
        # Generate content with Gemini
        full_prompt = f"{context}\n\n{prompt_text}" if context else prompt_text
        response = model.generate_content(full_prompt)
        generated_text = response.text

        # Watermark the output
        evidence, watermarked_text = watermark_ai_output(
            artifact=generated_text,
            model_id="gemini-1.5-flash",
            model_version="1.5",
            actor_id=f"batch:{batch_id}",
            prompt=prompt_text,
            enable_forensic_fragments=True,
        )

        print(f"   ✅ Completed prompt {prompt_id}", flush=True)

        return {
            "success": True,
            "prompt_id": prompt_id,
            "prompt": prompt_text,
            "original_length": len(generated_text),
            "watermarked_length": len(watermarked_text),
            "watermarked_text": watermarked_text,
            "artifact_id": evidence.artifact_id,
            "watermark_id": evidence.watermark.watermark_id,
            "evidence": evidence,
        }

    except Exception as e:
        print(f"   ❌ Failed prompt {prompt_id}: {e}", flush=True)
        return {"success": False, "prompt_id": prompt_id, "prompt": prompt_text, "error": str(e)}


def main():
    """Batch processing watermarking example."""

    print("=" * 70)
    print("Google Gemini Batch Processing with Watermarking")
    print("=" * 70)

    # Setup
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        print("   Get your key at: https://makersuite.google.com/app/apikey")
        return

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

    # ========================================================================
    # 1. DEFINE BATCH OF PROMPTS
    # ========================================================================

    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    prompts = [
        {
            "id": 1,
            "prompt": "Explain photosynthesis in 3 sentences.",
            "context": "Educational content for high school students",
        },
        {
            "id": 2,
            "prompt": "What are the main causes of climate change?",
            "context": "Scientific explanation",
        },
        {
            "id": 3,
            "prompt": "How does cryptocurrency mining work?",
            "context": "Technical explanation for beginners",
        },
        {"id": 4, "prompt": "Describe the water cycle.", "context": "Elementary school level"},
        {
            "id": 5,
            "prompt": "What is the theory of relativity?",
            "context": "Simplified explanation",
        },
    ]

    print(f"\n🆔 Batch ID: {batch_id}")
    print(f"📦 Number of prompts: {len(prompts)}")
    print("\n" + "=" * 70)
    print("Processing Prompts")
    print("=" * 70)

    # ========================================================================
    # 2. PROCESS BATCH (Sequential or Parallel)
    # ========================================================================

    start_time = datetime.now()
    results = []

    # Option A: Sequential processing (API rate limit friendly)
    print("\n🔄 Processing sequentially...\n")
    for prompt_data in prompts:
        result = process_single_prompt(prompt_data, model, batch_id)
        results.append(result)

    # Option B: Parallel processing (uncomment to use)
    # Note: Be mindful of API rate limits!
    # print("\n🔄 Processing in parallel...\n")
    # with ThreadPoolExecutor(max_workers=3) as executor:
    #     future_to_prompt = {
    #         executor.submit(process_single_prompt, prompt_data, model, batch_id): prompt_data
    #         for prompt_data in prompts
    #     }
    #     for future in as_completed(future_to_prompt):
    #         results.append(future.result())

    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()

    # ========================================================================
    # 3. ANALYZE RESULTS
    # ========================================================================

    print("\n" + "=" * 70)
    print("Batch Results")
    print("=" * 70)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print("\n📊 Statistics:")
    print(f"   - Total prompts: {len(prompts)}")
    print(f"   - Successful: {len(successful)}")
    print(f"   - Failed: {len(failed)}")
    print(f"   - Processing time: {processing_time:.2f} seconds")
    print(f"   - Average time per prompt: {processing_time / len(prompts):.2f} seconds")

    if failed:
        print("\n⚠️  Failed Prompts:")
        for result in failed:
            print(f"   - Prompt {result['prompt_id']}: {result['error']}")

    # ========================================================================
    # 4. SAVE EVIDENCE AND OUTPUTS
    # ========================================================================

    print("\n" + "=" * 70)
    print("Saving Results")
    print("=" * 70)

    evidence_dir = f"evidence/batch/{batch_id}"
    os.makedirs(evidence_dir, exist_ok=True)

    # Save individual evidence files
    for result in successful:
        evidence_file = os.path.join(evidence_dir, f"prompt_{result['prompt_id']}_evidence.json")
        with open(evidence_file, "w") as f:
            json.dump(result["evidence"].to_dict(), f, indent=2)

        # Save watermarked output
        output_file = os.path.join(evidence_dir, f"prompt_{result['prompt_id']}_output.txt")
        with open(output_file, "w") as f:
            f.write(result["watermarked_text"])

    print(f"💾 Saved {len(successful)} evidence files")
    print(f"💾 Saved {len(successful)} output files")

    # Save batch summary
    batch_summary = {
        "batch_id": batch_id,
        "timestamp": datetime.now().isoformat(),
        "model": "gemini-1.5-flash",
        "total_prompts": len(prompts),
        "successful": len(successful),
        "failed": len(failed),
        "processing_time_seconds": processing_time,
        "results": [
            {
                "prompt_id": r["prompt_id"],
                "prompt": r["prompt"],
                "success": r["success"],
                "artifact_id": r.get("artifact_id"),
                "watermark_id": r.get("watermark_id"),
                "original_length": r.get("original_length"),
                "watermarked_length": r.get("watermarked_length"),
                "error": r.get("error"),
            }
            for r in results
        ],
    }

    summary_file = os.path.join(evidence_dir, "batch_summary.json")
    with open(summary_file, "w") as f:
        json.dump(batch_summary, f, indent=2)

    print(f"📋 Batch summary saved: {summary_file}")

    # ========================================================================
    # 5. VERIFY BATCH
    # ========================================================================

    print("\n" + "=" * 70)
    print("Verifying Batch Authenticity")
    print("=" * 70)

    from ciaf_watermarks.text import verify_text_artifact

    verified_count = 0
    for result in successful:
        verification = verify_text_artifact(result["watermarked_text"], result["evidence"])
        if verification.is_authentic():
            verified_count += 1

    print("\n✅ Verification Results:")
    print(f"   - Verified authentic: {verified_count}/{len(successful)}")
    print(f"   - Verification rate: {verified_count/len(successful)*100:.0%}")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 70)
    print("✅ Batch Processing Complete!")
    print("=" * 70)
    print("\n📊 Final Summary:")
    print(f"   - Batch ID: {batch_id}")
    print("   - Model: Google Gemini Pro")
    print(f"   - Prompts processed: {len(successful)}/{len(prompts)}")
    print(f"   - Evidence directory: {evidence_dir}/")
    print(f"   - Total processing time: {processing_time:.2f}s")

    print("\n💡 Use Cases:")
    print("   - Bulk content generation for websites")
    print("   - Report generation from templates")
    print("   - Dataset preparation for research")
    print("   - Automated documentation creation")
    print("   - Content translation pipelines")

    print("\n🎯 Performance Tips:")
    print("   - Use parallel processing with rate limiting")
    print("   - Batch evidence saves to reduce I/O")
    print("   - Monitor API quotas and usage")
    print("   - Consider caching for repeated prompts")

    print("\n📚 Related Examples:")
    print("   - 01_basic_text_watermarking.py - Single prompt")
    print("   - 02_chat_conversation.py - Multi-turn chat")
    print("   - 03_streaming_response.py - Streaming output")


if __name__ == "__main__":
    main()
