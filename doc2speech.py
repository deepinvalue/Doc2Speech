import os
import re
import json
import argparse
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from pydub import AudioSegment
from openai._client import OpenAI
from epub_handler import read_epub, list_chapters, extract_chapter_content


def load_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)

def user_confirmation():
    while True:
        user_input = input("Do you want to continue with the TTS conversion? [Y/n]: ").lower().strip()
        if user_input in ['', 'yes', 'y']:
            return True
        elif user_input in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' (or press enter for default), or 'no'.")   

def is_url(path):
    return path.startswith('http://') or path.startswith('https://')

def get_content(input_path, user_agent):
    if is_url(input_path):
        import requests
        headers = {}
        if user_agent:
            headers['User-Agent'] = user_agent        
        response = requests.get(input_path, headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.text
    elif input_path.endswith('.epub'):
        book = read_epub(input_path)
        if book is not None:
            chapters = list_chapters(book)
            print("Available documents:")
            for i, (title, _) in enumerate(chapters, start=1):
                print(f"{i}: {title}")
            while True:
                doc_number = int(input("Enter the number of the document to process: "))
                if doc_number-1 not in range(len(chapters)):
                    print(f"Document number must between 1 and {len(chapters)}.")
                    continue
                break
            chapter_id = chapters[doc_number-1][1]
            return extract_chapter_content(book, chapter_id)
    else:
        return Path(input_path).read_text()

def clean_html_text(html_content, excluded_tags, excluded_classes, excluded_ids):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove specified tags
    for tag in excluded_tags:
        for element in soup.find_all(tag):
            element.decompose()
    # Remove elements with specified classes
    for class_name in excluded_classes:
        for element in soup.find_all(class_=class_name):
            element.decompose()
    # Remove elements with specified IDs
    for element_id in excluded_ids:
        element = soup.find(id=element_id)
        if element:
            element.decompose()            
    return soup.get_text()

def calculate_cost(text_length, price_per_1k_chars):
    return price_per_1k_chars * text_length / 1000

def process_text_to_speech(client, text, tts_model, voice, chunk_size, output_dir):
    def split_text(text):
        chunks = []
        while text:
            if len(text) <= chunk_size:
                chunks.append(text)
                break
            split_index = max(text.rfind('.', 0, chunk_size) + 1, text.rfind(' ', 0, chunk_size))
            chunk, text = text[:split_index], text[split_index:]
            chunks.append(chunk)
        return chunks

    def process_chunk(chunk, index):
        speech_file_path = output_dir / f'speech_chunk_{index}.mp3'
        response = client.audio.speech.create(model=tts_model, voice=voice, input=chunk)
        response.stream_to_file(speech_file_path)
        return speech_file_path

    audio_chunks = []
    for index, chunk in enumerate(tqdm(split_text(text), desc="Processing Text Chunks", unit="chunk")):
        audio_chunks.append(process_chunk(chunk, index)) 
    combined_audio = AudioSegment.empty()
    for file_path in audio_chunks:
        combined_audio += AudioSegment.from_mp3(file_path)
        os.remove(file_path)
    return combined_audio

def main():
    parser = argparse.ArgumentParser(description='Process HTML file to speech.')
    parser.add_argument('input', help='Path to the input file (HTML or text)')
    parser.add_argument('-o', '--output-dir', default=Path(__file__).parent / 'output', help='Path to the output directory')
    parser.add_argument('--clean-html', type=bool, default=True, help='Whether to clean HTML content and remove extra whitespace (default: True)')
    parser.add_argument('--config', default='config.json', help='Path to the configuration file')
    args = parser.parse_args()

    config = load_config(args.config)
    client = OpenAI(api_key=config['api_key'])

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch content from URL, Epub file, or local text file
    input_content = get_content(args.input, config.get('user_agent', ''))

    if args.clean_html:
        clean_text = clean_html_text(input_content, config['excluded_tags'], config['excluded_classes'], config['excluded_ids']).strip()
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)
        clean_text = re.sub(r'\s\s+', ' ', clean_text)
    else:
        clean_text = input_content.strip()        

    total_cost = calculate_cost(len(clean_text), config['price_per_1k_chars'])
    print(f"Estimated Cost: {total_cost:.3f}$")

    if user_confirmation():
        audio = process_text_to_speech(client, clean_text, config['tts_model'], config['voice'], config['max_character_limit'], output_dir)
        output_file = output_dir / f"{Path(args.input).stem}.{config['audio_format']}"
        audio.export(output_file, format=config['audio_format'])
        print(f"TTS conversion finished successfully. File saved to {output_file}")
    else:
        print("TTS conversion canceled.")

if __name__ == '__main__':
    main()
