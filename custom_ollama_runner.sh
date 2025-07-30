#!/bin/bash
# Custom runner for Ollama to control memory usage

# Smaller context and batch size to reduce VRAM usage
# Optimal values may vary depending on your GPU and desired performance
CTX_SIZE=2048
BATCH_SIZE=256

# Get the model path from the arguments
MODEL_PATH=""
for arg in "$@"; do
    if [[ $arg == --model ]]; then
        MODEL_PATH=$(echo "$@" | awk -F'--model ' '{print $2}' | awk '{print $1}')
        break
    fi
done

if [ -z "$MODEL_PATH" ]; then
    echo "Error: --model argument not found."
    exit 1
fi

# Run Ollama with the custom parameters
/usr/local/bin/ollama runner --model "$MODEL_PATH" --ctx-size $CTX_SIZE --batch-size $BATCH_SIZE --n-gpu-layers 32

