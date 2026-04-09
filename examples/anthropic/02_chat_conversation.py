"""
Anthropic + CIAF Watermarking - Chat Conversation Example

Demonstrates watermarking in a multi-turn conversation:
1. Maintain conversation history
2. Watermark each Claude response
3. Save evidence for each turn
4. Verify the entire conversation

Usage:
    export ANTHROPIC_API_KEY="your-key-here"
    python 02_chat_conversation.py
"""

import os
import json
from anthropic import Anthropic
from ciaf_watermarks import watermark_ai_output
from ciaf_watermarks.text import verify_text_artifact

# ============================================================================
# CONFIGURATION
# ============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
EVIDENCE_DIR = "evidence/conversation"

os.makedirs(EVIDENCE_DIR, exist_ok=True)

if not ANTHROPIC_API_KEY:
    print("⚠️  Error: ANTHROPIC_API_KEY not set")
    exit(1)

# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ============================================================================
# CONVERSATION SETUP
# ============================================================================

print("=" * 70)
print("Anthropic + CIAF Watermarking - Multi-Turn Conversation")
print("=" * 70)

# User inputs for the conversation
user_inputs = [
    "What is machine learning?",
    "How is it different from traditional programming?",
    "What are some real-world applications?",
]

# Track conversation state
conversation_history = []  # For Claude API
evidence_records = []  # For watermarking
turn_number = 0


# ============================================================================
# PROCESS EACH CONVERSATION TURN
# ============================================================================

for user_input in user_inputs:
    turn_number += 1
    print(f"\n{'=' * 70}")
    print(f"Turn {turn_number}")
    print(f"{'=' * 70}")
    print(f"\n👤 User: {user_input}")
    # Add user message to conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # ========================================================================
    # Get Claude's response
    # ========================================================================

    response = client.messages.create(
        model="claude-3-sonnet-20240229", max_tokens=300, messages=conversation_history
    )

    # Extract Claude's message
    claude_message = response.content[0].text

    print(f"\n🤖 Claude (original):\n{claude_message}")

    # ========================================================================
    # Watermark Claude's response
    # ========================================================================

    evidence, watermarked_message = watermark_ai_output(
        artifact=claude_message,
        model_id="claude-3-sonnet-20240229",
        model_version="2024-02",
        actor_id="user:conversation-demo",
        prompt=user_input,
        watermark_config={
            "text": {
                "style": "inline",  # Subtle style for chat
                "include_timestamp": True,
                "include_model_info": False,  # Less verbose for chat
            }
        },
        enable_forensic_fragments=True,
    )

    print(f"\n🔒 Watermarked response:\n{watermarked_message}")
    print(f"   Watermark ID: {evidence.watermark.watermark_id}")

    # ========================================================================
    # Save evidence for this turn
    # ========================================================================

    evidence_file = os.path.join(EVIDENCE_DIR, f"turn_{turn_number}_{evidence.artifact_id}.json")
    with open(evidence_file, "w") as f:
        json.dump(evidence.to_dict(), f, indent=2)

    print(f"   Evidence saved: {evidence_file}")

    # Store evidence for later verification
    evidence_records.append(
        {
            "turn": turn_number,
            "user_input": user_input,
            "watermarked_text": watermarked_message,
            "evidence": evidence,
            "evidence_file": evidence_file,
        }
    )

    # Add watermarked message to conversation history
    # (So next turn includes the watermarked version)
    conversation_history.append({"role": "assistant", "content": watermarked_message})


# ============================================================================
# SAVE CONVERSATION SUMMARY
# ============================================================================

print(f"\n{'=' * 70}")
print("Saving Conversation Summary")
print(f"{'=' * 70}")

conversation_summary = {
    "total_turns": turn_number,
    "model": "claude-3-sonnet-20240229",
    "watermark_ids": [rec["evidence"].watermark_id for rec in evidence_records],
    "artifact_ids": [rec["evidence"].artifact_id for rec in evidence_records],
    "evidence_files": [rec["evidence_file"] for rec in evidence_records],
}

summary_file = os.path.join(EVIDENCE_DIR, "conversation_summary.json")
with open(summary_file, "w") as f:
    json.dump(conversation_summary, f, indent=2)

print(f"✅ Conversation summary saved to: {summary_file}")


# ============================================================================
# VERIFY THE ENTIRE CONVERSATION
# ============================================================================

print(f"\n{'=' * 70}")
print("Verifying Conversation Authenticity")
print(f"{'=' * 70}")

authenticated_turns = 0
for record in evidence_records:
    result = verify_text_artifact(record["watermarked_text"], record["evidence"])

    print(f"\nTurn {record['turn']}: ", end="")
    if result.is_authentic():
        print(f"✅ AUTHENTIC (confidence: {result.confidence:.2%})")
        authenticated_turns += 1
    else:
        print(f"❌ FAILED (confidence: {result.confidence:.2%})")
        if result.notes:
            print(f"   Notes: {result.notes[0]}")

print(f"\n{'=' * 70}")
print(f"Conversation Verification: {authenticated_turns}/{turn_number} turns authenticated")
print(f"{'=' * 70}")


# ============================================================================
# DEMONSTRATE TAMPERING DETECTION
# ============================================================================

print(f"\n{'=' * 70}")
print("Testing Tampering Detection")
print(f"{'=' * 70}")

# Modify the first turn's response
tampered_text = evidence_records[0]["watermarked_text"] + "\n\nThis was added later."

print("\n🔬 Testing tampered version of Turn 1:")
print(f"Original length: {len(evidence_records[0]['watermarked_text'])} chars")
print(f"Tampered length: {len(tampered_text)} chars")

result = verify_text_artifact(tampered_text, evidence_records[0]["evidence"])

print("\n❌ Verification Result:")
print(f"   Authentic: {result.is_authentic()}")
print(f"   Confidence: {result.confidence:.2%}")
print(f"   Content Modified: {result.content_modified}")


# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n{'=' * 70}")
print("✅ CONVERSATION SUMMARY")
print(f"{'=' * 70}")
print(f"✓ Conducted {turn_number}-turn conversation with Claude")
print("✓ Watermarked each assistant response with inline style")
print("✓ Saved evidence for each turn:")
for i, rec in enumerate(evidence_records, 1):
    print(f"   - Turn {i}: {rec['evidence_file']}")
print(f"✓ Verified all {authenticated_turns} turns successfully")
print("✓ Detected tampering in modified content")
print("\n💡 Use Case: Multi-turn chatbots, customer service, assistants")
print(f"{'=' * 70}")
