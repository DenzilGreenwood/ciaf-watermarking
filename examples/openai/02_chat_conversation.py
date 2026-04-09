"""
OpenAI + CIAF Watermarking - Chat Conversation Example

Demonstrates watermarking multi-turn conversations with OpenAI.
Each response is watermarked individually with conversation context.

Usage:
    export OPENAI_API_KEY="your-key-here"
    python 02_chat_conversation.py

Features:
    - Multi-turn conversation tracking
    - Each response watermarked separately
    - Conversation context in evidence metadata
    - Aggregated verification
"""

import os
import json
from datetime import datetime
from openai import OpenAI
from ciaf_watermarks import watermark_ai_output


def main():
    """Chat conversation watermarking example."""

    print("=" * 70)
    print("OpenAI Chat Conversation with Watermarking")
    print("=" * 70)

    # Setup
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    client = OpenAI(api_key=api_key)

    # Conversation state
    conversation_history = []
    conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    evidence_records = []

    print(f"\n🆔 Conversation ID: {conversation_id}")
    print("💬 Starting chat (type 'exit' to quit)...\n")

    # Simulate a conversation (you can make this interactive)
    demo_messages = [
        "What is machine learning?",
        "How is it different from traditional programming?",
        "Can you give me a simple example?",
    ]

    for i, user_message in enumerate(demo_messages, 1):
        print(f"\n{'=' * 70}")
        print(f"Turn {i}")
        print(f"{'=' * 70}")

        # Display user message
        print(f"\n👤 User: {user_message}")

        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_message})

        # Call OpenAI
        print("🤖 Assistant is typing...")

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful AI assistant."}]
                + conversation_history,
                temperature=0.7,
                max_tokens=300,
            )

            assistant_message = response.choices[0].message.content

            # Watermark the response
            evidence, watermarked_response = watermark_ai_output(
                artifact=assistant_message,
                model_id="gpt-3.5-turbo",
                model_version="2024-03",
                actor_id=f"conversation:{conversation_id}",
                prompt=f"[Turn {i}] {user_message}",
                watermark_config={"text": {"style": "inline"}},  # Less visible for chat
                enable_forensic_fragments=True,
            )

            # Add watermarked response to history
            conversation_history.append({"role": "assistant", "content": watermarked_response})

            # Store evidence
            evidence_records.append(
                {
                    "turn": i,
                    "user_message": user_message,
                    "artifact_id": evidence.artifact_id,
                    "watermark_id": evidence.watermark.watermark_id,
                    "evidence": evidence,
                }
            )

            # Display watermarked response
            print(f"\n🤖 Assistant: {watermarked_response}")
            print(f"   [Watermark ID: {evidence.watermark.watermark_id}]")

        except Exception as e:
            print(f"❌ Error: {e}")
            break

    # ========================================================================
    # SAVE CONVERSATION WITH EVIDENCE
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Saving Conversation Evidence")
    print(f"{'=' * 70}")

    evidence_dir = "evidence/conversations"
    os.makedirs(evidence_dir, exist_ok=True)

    # Save individual evidence records
    for record in evidence_records:
        evidence_file = os.path.join(evidence_dir, f"{conversation_id}_turn{record['turn']}.json")
        with open(evidence_file, "w") as f:
            json.dump(record["evidence"].to_dict(), f, indent=2)
        print(f"💾 Saved: {evidence_file}")

    # Save conversation summary
    conversation_summary = {
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "turns": len(evidence_records),
        "watermarks": [
            {
                "turn": r["turn"],
                "user_message": r["user_message"],
                "watermark_id": r["watermark_id"],
                "artifact_id": r["artifact_id"],
            }
            for r in evidence_records
        ],
    }

    summary_file = os.path.join(evidence_dir, f"{conversation_id}_summary.json")
    with open(summary_file, "w") as f:
        json.dump(conversation_summary, f, indent=2)

    print(f"📋 Summary saved: {summary_file}")

    # ========================================================================
    # VERIFY CONVERSATION
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Verifying Conversation Authenticity")
    print(f"{'=' * 70}")

    from ciaf_watermarks.text import verify_text_artifact

    verified_turns = 0
    for record in evidence_records:
        # Get the watermarked message from history
        turn_index = (record["turn"] - 1) * 2 + 1  # Account for user messages
        assistant_message = conversation_history[turn_index]["content"]

        result = verify_text_artifact(assistant_message, record["evidence"])

        print(f"\n✅ Turn {record['turn']}:")
        print(f"   Authentic: {result.is_authentic()}")
        print(f"   Confidence: {result.confidence:.0%}")

        if result.is_authentic():
            verified_turns += 1

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Conversation Summary")
    print(f"{'=' * 70}")
    print("\n📊 Statistics:")
    print(f"   - Total turns: {len(evidence_records)}")
    print("   - All responses watermarked: Yes")
    print(f"   - Verified authentic: {verified_turns}/{len(evidence_records)}")
    print(f"   - Evidence directory: {evidence_dir}/")

    print("\n💡 Use Cases:")
    print("   - Customer service chat logs")
    print("   - Legal compliance (prove AI responses)")
    print("   - Content moderation audit trails")
    print("   - Research conversation datasets")


if __name__ == "__main__":
    main()
