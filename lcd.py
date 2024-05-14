import hashlib
import requests
import time
import aiohttp
import asyncio
import pyttsx3

# Initialize TTS engine
tts_engine = pyttsx3.init()

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

# Function to convert text to speech
def text_to_speech(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

# Main function to orchestrate the calls
async def main(file_path, question, ocr_api_key, openai_api_key):
    ocr_result = await ocr_space_file_with_cache(file_path, ocr_api_key)
    extracted_text = ocr_result['ParsedResults'][0]['ParsedText']

    response = await ask_chatgpt_async(question, openai_api_key)
    chatgpt_response = response['choices'][0]['message']['content']

    # Call text_to_speech with the response text
    text_to_speech(chatgpt_response)

if __name__ == '__main__':
    # Example usage
    file_path = 'path_to_your_image_file'
    question = 'Your question here'
    ocr_api_key = 'your_ocr_api_key'
    openai_api_key = 'your_openai_api_key'

    asyncio.run(main(file_path, question, ocr_api_key, openai_api_key))
