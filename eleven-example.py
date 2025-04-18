# filename: tts_example.py

from dotenv import load_dotenv
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import play

def main():
    # Load environment variables from .env file (make sure .env contains ELEVENLABS_API_KEY)
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set ELEVENLABS_API_KEY in your .env file.")

    # Initialize ElevenLabs client with your API key
    client = ElevenLabs(api_key=api_key)

    # Step 1: List all voices
    voices_response = client.voices.get_all()
    voices = voices_response.voices

    # Step 2: Filter voices by language (example: English)
    preferred_language_code = "en"  # You can set to any supported ISO language code, e.g., "it" for Italian

    # Find voices supporting the preferred language
    matching_voices = [v for v in voices if preferred_language_code in v.language.lower()]

    if not matching_voices:
        print(f"No voices found for language code '{preferred_language_code}'")
        return

    # Select the first matching voice or one you prefer by name
    selected_voice = matching_voices[0]

    print(f"Selected voice: {selected_voice.name} ({selected_voice.id}) - Language: {selected_voice.language}")

    # Step 3: Convert text-to-speech using the selected voice and model
    text_to_read = "Hello from ElevenLabs text to speech API!"
    model_id = "eleven_multilingual_v2"  # Supports 29 languages - choose based on needs

    audio_data = client.text_to_speech.convert(
        text=text_to_read,
        voice_id=selected_voice.id,
        model_id=model_id,
        output_format="mp3_44100_128",  # mp3 format with 44.1kHz sample rate
    )

    # Step 4: Save audio to file
    output_file = "output_speech.mp3"
    with open(output_file, "wb") as f:
        f.write(audio_data)

    print(f"Audio saved to {output_file}")

    # Optional: play the audio if you want
    # play(audio_data)

if __name__ == "__main__":
    main()