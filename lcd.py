import hashlib
import requests
import time
import aiohttp
import asyncio

# Cache dictionary for storing OCR results
cache = {}

# Function to compute file hash
def compute_file_hash(filename):
    with open(filename, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

# Caching for OCR.space
def ocr_space_file_with_cache(filename, api_key):
    file_hash = compute_file_hash(filename)
    if file_hash in cache:
        print("Returning cached result")
        return cache[file_hash]

    result = ocr_space_file(filename, api_key)
    cache[file_hash] = result
    return result

# Basic OCR.space function without modifications
def ocr_space_file(filename, api_key):
    url = 'https://api.ocr.space/parse/image'
    payload = {'isOverlayRequired': False, 'apikey': api_key, 'language': 'eng'}
    with open(filename, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files, data=payload)
    return response.json()

# Exponential backoff for API calls
def backoff_retry(func):
    def wrapper(*args, **kwargs):
        attempts = 3
        delay = 1
        for i in range(attempts):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                print(f"API call failed: {e}, retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
        return None
    return wrapper

# Asynchronous call to OpenAI
async def ask_chatgpt_async(question, openai_api_key):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}',
        'messages': [{'role': 'user', 'content': question}]
    }
    payload = {
        'model': 'gpt-3.5-turbo',
        'prompt': question,
        'max_tokens': 150
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            return await response.json()

# Main function to orchestrate the calls
def main(filename, question, ocr_api_key, openai_api_key):
    # OCR with caching
    ocr_result = ocr_space_file_with_cache(filename, ocr_api_key)
    print("OCR Result:", ocr_result)

    # Extract the necessary text
    if 'ParsedResults' in ocr_result and len(ocr_result['ParsedResults']) > 0:
        parsed_text = ocr_result['ParsedResults'][0].get('ParsedText', '')
        print("Extracted Text:", parsed_text)
    else:
        print("No text found or error in OCR")
        return

    # Using asyncio to call ChatGPT asynchronously with the parsed text
    loop = asyncio.get_event_loop()
    chatgpt_response = loop.run_until_complete(ask_chatgpt_async(parsed_text, openai_api_key))
    print("ChatGPT Response:", chatgpt_response)

# Example usage
if __name__ == "__main__":
    filename = '/home/jasalat/text.jpg'
    question = "Solve this question or atleast make sense of it"
    ocr_api_key = ""
    openai_api_key = ""
    main(filename, question, ocr_api_key, openai_api_key)
