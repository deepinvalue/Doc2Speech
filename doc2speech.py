import os
import re
import json
import argparse
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from pydub import AudioSegment
from openai._client import OpenAI
from epub_handler import list_html_files, extract_html_content


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
        html_files = list_html_files(input_path)
        print("Available documents:")
        for i, file_name in enumerate(html_files, start=1):
            print(f"{i}: {Path(file_name).stem}")
        while True:
            doc_number = int(input("Enter the index number of the document to process: "))
            if doc_number-1 not in range(len(html_files)):
                print(f"The number must between 1 and {len(html_files)}.")
                continue
            break     
        html_file = html_files[doc_number-1]
        return extract_html_content(input_path, html_file)               
    else:
        return Path(input_path).read_text()

def clean_html_text(html_content, root_node_selector, excluded_tags, excluded_classes, excluded_ids):
    soup = BeautifulSoup(html_content, 'html.parser')

    if root_node_selector!='':
        # Find the root node to start from
        root_node = soup.select_one(root_node_selector)
        if root_node:
            soup = root_node
        else:
            print(f"No element found for the root node selector '{root_node_selector}'. Processing the entire document.")

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

def calculate_cost(text_chunks, price_per_1k_chars):
    return sum(len(chunk) for chunk in text_chunks) * price_per_1k_chars / 1000

def split_text(text, chunk_size):
    """
    Splits the text into chunks that are at most `chunk_size` characters long,
    ideally ending with a complete sentence by looking for punctuation followed by any whitespace.
    """
    chunks = []
    pattern = re.compile(r'(?<=[.!?])\s+')
    start = 0

    while start < len(text):
        if len(text) - start <= chunk_size:
            chunks.append(text[start:])
            break
        # Find the nearest sentence end within chunk_size
        match = pattern.finditer(text[start:start+chunk_size])
        split_index = None
        for m in match:
            split_index = m.start(0)
        if split_index is not None:
            # Adjust split_index relative to the entire text
            split_index += start
            chunks.append(text[start:split_index].strip())
            start = split_index + 1
        else:
            # Fallback: split at chunk_size, trying not to break words
            split_at_space = text.rfind(' ', start, start + chunk_size)
            if split_at_space != -1:
                chunks.append(text[start:split_at_space].strip())
                start = split_at_space + 1
            else:
                # If no spaces, force split at chunk_size
                chunks.append(text[start:start+chunk_size].strip())
                start += chunk_size

    return [chunk for chunk in chunks if chunk]  # Remove empty strings, if any


def process_text_to_speech(client, text_chunks, audio_file_name, tts_model, voice, chunk_size, output_dir):
    def process_chunk(chunk, index):
        speech_file_path = output_dir / f'{audio_file_name}_part_{index}.mp3'
        response = client.audio.speech.create(model=tts_model, voice=voice, input=chunk)
        response.stream_to_file(speech_file_path)
        return speech_file_path

    audio_chunks = []
    total_characters = sum(len(chunk) for chunk in text_chunks)
    with tqdm(total=total_characters, desc="Text Conversion Progress", unit="char", unit_scale=True) as pbar:
        for index, chunk in enumerate(text_chunks):
            audio_chunks.append(process_chunk(chunk, index)) 
            pbar.update(len(chunk))
    combined_audio = AudioSegment.empty()
    for file_path in audio_chunks:
        combined_audio += AudioSegment.from_mp3(file_path)
        os.remove(file_path)
    return combined_audio

def main():
    parser = argparse.ArgumentParser(
        description='Process HTML content to speech.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input', help='Path to the input file. Supported formats: HTML, EPUB, text, or a URL.')
    parser.add_argument('--config', default='config.json', help='Path to the configuration file')
    parser.add_argument('--output-dir', '-o', default=Path(__file__).parent / 'output', help='Path to the output directory')
    parser.add_argument('--clean-html', type=bool, default=True, help='Whether to clean HTML content and remove extra whitespace')
    parser.add_argument('--root-node-selector', '-s', default='', help='CSS selector for the root node to start processing from')
    args = parser.parse_args()

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch content from URL, Epub file, or local text file
    input_content = get_content(args.input, config.get('user_agent', ''))

    if args.clean_html:
        clean_text = clean_html_text(
            input_content,
            args.root_node_selector or config.get('root_node_selector', ''), 
            config['excluded_tags'], 
            config['excluded_classes'], 
            config['excluded_ids']
        ).strip()
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)
        clean_text = re.sub(r'\s\s+', ' ', clean_text)
    else:
        clean_text = input_content.strip()        

    text_chunks = split_text(clean_text, config['max_character_limit'])

    total_cost = calculate_cost(text_chunks, config['price_per_1k_chars'])
    print(f"Estimated Cost: {total_cost:.3f}$")

    audio_file_name = Path(args.input).stem

    if user_confirmation():
        client = OpenAI(api_key=config['api_key'])
        audio = process_text_to_speech(
            client, 
            text_chunks,
            audio_file_name,
            config['tts_model'], 
            config['voice'], 
            config['max_character_limit'], 
            output_dir
        )
        output_file = output_dir / f"{audio_file_name}.{config['audio_format']}"
        audio.export(output_file, format=config['audio_format'])
        print(f"TTS conversion finished successfully. File saved to {output_file}")
    else:
        print("TTS conversion canceled.")

if __name__ == '__main__':
    main()
