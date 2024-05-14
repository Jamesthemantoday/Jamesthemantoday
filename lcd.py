import hashlib
import requests
import time
import aiohttp
import asyncio
import gi
from gtts import gTTS
import os
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Initialize GStreamer
Gst.init(None)

# Function to perform OCR with caching
async def ocr_space_file_with_cache(file_path, api_key):
    file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
    cache = {}

    if file_hash in cache:
        return cache[file_hash]
    else:
        result = await backoff_retry(ocr_space_file, file_path, api_key)
        cache[file_hash] = result
        return result

# Function to call OCR.space API
async def ocr_space_file(file_path, api_key):
    url = 'https://api.ocr.space/parse/image'
    payload = {'isOverlayRequired': False, 'apikey': api_key}
    with open(file_path, 'rb') as f:
        r = requests.post(url, files={file_path: f}, data=payload)
    return r.json()

# Exponential backoff mechanism for API calls
async def backoff_retry(func, *args, **kwargs):
    max_retries = 5
    delay = 1

    for i in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise e

# Asynchronous call to OpenAI API
async def ask_chatgpt_async(question, openai_api_key):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }
    payload = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': question}],
        'max_tokens': 150
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            return await response.json()

# Function to convert text to speech using gTTS and GStreamer
def play_text(text):
    tts = gTTS(text=text, lang='en')
    tts.save('response.mp3')
    # Set up a simple GStreamer pipeline to play audio
    player = Gst.ElementFactory.make("playbin", "player")
    player.set_property('uri', 'file://' + os.path.abspath('response.mp3'))
    player.set_state(Gst.State.PLAYING)
    # Wait until error or EOS
    bus = player.get_bus()
    bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
    # Free resources
    player.set_state(Gst.State.NULL)

# Main function to orchestrate the calls
async def main(file_path, question, ocr_api_key, openai_api_key):
    ocr_result = await ocr_space_file_with_cache(file_path, ocr_api_key)

    # Check if 'ParsedResults' key exists in the OCR result
    if 'ParsedResults' in ocr_result and ocr_result['ParsedResults']:
        extracted_text = ocr_result['ParsedResults'][0]['ParsedText']
        response = await ask_chatgpt_async(question, openai_api_key)
        chatgpt_response = response['choices'][0]['message']['content']

        # Call play_text with the response text
        play_text(chatgpt_response)
    else:
        print("Error: 'ParsedResults' key not found in OCR response")
        play_text("There was an error processing the OCR result.")

if __name__ == '__main__':
    # Example usage
    file_path = '/home/jasalat/text.jpg'
    question = 'Solve this question or at least explain it briefly'
    ocr_api_key = ''
    openai_api_key = ''

    asyncio.run(main(file_path, question, ocr_api_key, openai_api_key))
