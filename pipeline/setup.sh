#!/bin/sh
# Einmal pro Session: Stimme + piper installieren
set -e
pip install --break-system-packages -q piper-tts numpy pillow 2>/dev/null
mkdir -p /tmp/voice
[ -f /tmp/voice/de-thorsten-low.onnx ] || curl -sSL https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-de-thorsten-low.tar.gz | tar xz -C /tmp/voice
echo setup-ok
