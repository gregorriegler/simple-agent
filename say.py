#!/usr/bin/env python
import pyttsx3
import sys

message = sys.argv[1] if len(sys.argv) > 1 else "help"

engine = pyttsx3.init()
engine.say(message)
engine.runAndWait()
