import hashlib
import requests
import time
import aiohttp
import asyncio
import gi
from gtts import gTTS
import os
from concurrent.futures import ThreadPoolExecutor
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Initialize GStreamer
Gst.init(None)

executor = ThreadPoolExecutor(max_workers=1)

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
    try:
        tts = gTTS(text=text, lang='en')
        tts.save('response.mp3')
        player = Gst.ElementFactory.make("playbin", "player")
        player.set_property('uri', 'file://' + os.path.abspath('response.mp3'))
        player.set_state(Gst.State.PLAYING)
        bus = player.get_bus()
        bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
        player.set_state(Gst.State.NULL)
    except Exception as e:
        print(f"Failed to play text: {e}")

async def play_text_async(text):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, play_text, text)

# Main function to orchestrate the calls
async def main(file_path, ocr_api_key, openai_api_key):
    ocr_result = await ocr_space_file_with_cache(file_path, ocr_api_key)
    print("OCR Result:", ocr_result)  # Debugging line

    if 'ParsedResults' in ocr_result and ocr_result['ParsedResults']:
        parsed_result = ocr_result['ParsedResults'][0]

        if 'IsErroredOnProcessing' in parsed_result and parsed_result['IsErroredOnProcessing']:
            error_message = parsed_result.get('ErrorMessage', ['Unknown error'])[0]
            print(f"Error in OCR processing: {error_message}")
            await play_text_async(f"Error in OCR processing: {error_message}")
        else:
            extracted_text = parsed_result.get('ParsedText', '')
            if extracted_text:
                print("Extracted Text:", extracted_text)  # Debugging line

                response = await ask_chatgpt_async(extracted_text, openai_api_key)
                print("OpenAI API Response:", response)  # Debugging line

                if 'choices' in response and response['choices']:
                    chatgpt_response = response['choices'][0]['message']['content']
                    await play_text_async(chatgpt_response)
                else:
                    await play_text_async("There was an error with the OpenAI response.")
            else:
                print("No text found in OCR result")
                await play_text_async("No text found in OCR result")
    else:
        print("Error: No text found or error in OCR")
        await play_text_async("No text found or error in OCR.")

if __name__ == '__main__':
    # Example usage
    file_path = '/home/user/text.jpg'
    ocr_api_key = 'your_ocr_api_key'
    openai_api_key = 'your_openai_api_key'

    asyncio.run(main(file_path, ocr_api_key, openai_api_key))
