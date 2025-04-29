# File Sort

A Python utility that uses Google's Gemini AI to intelligently organize files by suggesting appropriate filenames, folder names, and categories.

## Features

- Analyzes files using their name, extension, MIME type, and content preview
- Suggests meaningful filenames and folder organization
- Categorizes files based on their type and content
- Preview mode to see suggestions without making changes
- Execution mode to actually rename and organize files

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/file_sort.git
   cd file_sort
   ```

2. Install the required dependencies:
   ```
   pip install requests
   ```

3. Create an API key file:
   
   Create a file named `api_key.py` in the project directory with the following content:
   ```python
   API_KEY = "your_gemini_api_key_here"
   ```
   
   You can obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

## Usage

### Preview Mode (Default)

To see suggested changes without actually moving files:

```
python file_sort.py /path/to/directory
```

### Execution Mode

To apply the suggested changes and reorganize files:

```
python file_sort.py /path/to/directory --execute-actions
```

## How It Works

1. The script examines each file in the specified directory
2. File information (name, extension, MIME type, size, and preview of content for text files) is gathered
3. This information is sent to Google's Gemini AI with a prompt to suggest a better name and organization
4. The AI returns suggestions in JSON format with:
   - `fileName`: A more descriptive filename
   - `folderName`: An appropriate folder name
   - `category`: A high-level category for the file
5. Based on these suggestions, files are organized into category folders and subfolders, with improved filenames

## Skipped Files

The script automatically skips system files like `.DS_Store`, `.localized`, `Thumbs.db`, and `.gitignore`.

## Examples

```
$ python file_sort.py ~/Downloads
Processing file: IMG_20230615_123456.jpg
Would move 'IMG_20230615_123456.jpg' to folder: 'Photos/Summer Vacation 2023'
New filename: 'BeachSunset.jpg'
Category: 'Images'

$ python file_sort.py ~/Downloads --execute-actions
Processing file: IMG_20230615_123456.jpg
✓ Moved 'IMG_20230615_123456.jpg' to folder: 'Photos/Summer Vacation 2023'
```

## License

[MIT License](LICENSE)
