#!/bin/bash
# Quick Start Script for Gemini + CIAF Watermarking Examples
# This script helps you set up and run your first example

echo "================================================"
echo "Gemini + CIAF Watermarking - Quick Start"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null
then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Check for API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY environment variable not set"
    echo ""
    echo "To get your API key:"
    echo "1. Visit: https://makersuite.google.com/app/apikey"
    echo "2. Create or copy your API key"
    echo "3. Set the environment variable:"
    echo ""
    echo "   export GEMINI_API_KEY='your-api-key-here'"
    echo ""
    echo "Or create a .env file from the template:"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your API key"
    echo ""
    read -p "Do you want to enter your API key now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        read -p "Enter your Gemini API key: " api_key
        export GEMINI_API_KEY="$api_key"
        echo "✅ API key set for this session"
    else
        echo "⚠️  Please set GEMINI_API_KEY before running examples"
        exit 1
    fi
else
    echo "✅ GEMINI_API_KEY found"
fi

echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "📚 Available Examples:"
echo ""
echo "1. Basic Text Watermarking (START HERE)"
echo "   python3 01_basic_text_watermarking.py"
echo ""
echo "2. Chat Conversation"
echo "   python3 02_chat_conversation.py"
echo ""
echo "3. Streaming Response"
echo "   python3 03_streaming_response.py"
echo ""
echo "4. Batch Processing"
echo "   python3 04_batch_processing.py"
echo ""
echo "5. Verification (run example 1 first)"
echo "   python3 05_verification.py"
echo ""
echo "================================================"
echo ""

read -p "Run the first example now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "🚀 Running 01_basic_text_watermarking.py..."
    echo ""
    python3 01_basic_text_watermarking.py
fi

echo ""
echo "💡 For more information, see README.md"
