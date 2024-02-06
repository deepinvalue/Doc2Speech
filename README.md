# Doc2Speech

Doc2Speech is a Python-based tool that converts EPUBs, webpages, and HTML documents into natural-sounding speech. It leverages OpenAI's advanced Text-to-Speech (TTS) model and is specifically designed to handle the character limit constraints of the API, ensuring a seamless and natural flow of speech.

## Features

- **Convert HTML to Speech**: Turns any HTML content into natural-sounding audio.
- **Direct URL Processing**: Capable of directly fetching and converting HTML content from URLs.
- **EPUB Support**: Directly converts chapters from EPUB documents.
- **OpenAI's TTS Model**: Utilizes the latest in TTS technology for high-quality speech synthesis.
- **Character Limit Management**: Smartly segments texts at sentence boundaries to respect OpenAI's character limits without disrupting the narrative flow.
- **Customizable Content Processing**: Ability to exclude specific HTML tags, classes, or IDs.
- **Estimated Cost Calculation**: Provides an estimated cost calculation for using OpenAI's TTS API.

## Getting Started

### Prerequisites

Ensure you have Python 3.x installed on your system. The following Python libraries are required:

- BeautifulSoup4
- OpenAI Python client
- pydub
- tqdm
- requests
- ebooklib

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/deepinvalue/Doc2Speech.git
   ```
2. Navigate to the cloned directory and install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
## Configuration

Rename `config.json.sample` to `config.json` and update it as follows:

- `api_key`: Your OpenAI API key.
- `tts_model`: The TTS model to use ("tts-1", "tts-1-hd").
- `voice`: The voice model for TTS ("alloy", "echo", "fable", "onyx", "nova", "shimmer").
- `audio_format`: Desired audio format for the output ("mp3", "opus", "aac", "flac").
- `excluded_tags`: List of HTML tags to exclude from text conversion (e.g., ["pre", "header", "nav"]).
- `excluded_classes`: List of HTML classes to exclude (e.g., ["class1", "class2"]).
- `excluded_ids`: List of HTML element IDs to exclude (e.g., ["id1", "id2"]).
- `price_per_1k_chars`: The price per 1000 characters for using the OpenAI TTS API.
- `max_character_limit`: The maximum number of characters to process in a single TTS request.
- `user_agent`: Custom user agent string for directly fetching web content, if empty defaults to system's user agent.

## Usage

   ```bash
   python doc2speech.py <input-file-or-url> -o <output-directory>
   ```
   Options:

   - `<input-file-or-url>`: Path to the HTML file or URL.
   - `<output-directory>`: Directory where the output audio file will be saved.

## Future Enhancements

- [x] Addition of EPUB file support.
- [ ] Expansion of audio format support beyond MP3.

## Contributing

Contributions are welcome. Please feel free to fork the repository and submit pull requests.
