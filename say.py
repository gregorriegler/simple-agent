#!/usr/bin/env -S uv run --script
import sys


def say_with_piper(message):
    try:
        from piper import PiperVoice
        import pygame
        import tempfile
        import os
        import wave

        voice_obj = PiperVoice.load("en_US-lessac-medium.onnx")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            wav_path = temp_file.name

        with wave.open(wav_path, "wb") as wav_file:
            voice_obj.synthesize_wav(message, wav_file)

        pygame.mixer.init()
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)

        pygame.mixer.quit()
        os.unlink(wav_path)

        return True

    except Exception as e:
        print(f"Piper TTS error: {e}")
        return False


def parse_args():
    message = sys.argv[1]
    return message


def main():
    message = " ".join(sys.argv[1:])
    print(f"Speaking: {message[:50]}{'...' if len(message) > 50 else ''}")
    say_with_piper(message)


if __name__ == "__main__":
    main()
