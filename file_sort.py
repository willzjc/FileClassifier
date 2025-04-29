#!/usr/bin/env python3
import os
import sys
import json
import requests
import mimetypes
from pathlib import Path
from typing import Dict, Optional, Any
from api_key import API_KEY  # Import API_KEY from the new file

API_URL: str = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

SKIP_FILES: set[str] = {".DS_Store", ".localized",
                        "Thumbs.db", "desktop.ini", ".gitignore", ".gitkeep"}


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get basic information about a file that might be useful for classification."""
    file_path = Path(file_path)
    file_info: Dict[str, Any] = {
        "name": file_path.name,
        "extension": file_path.suffix,
        "size_bytes": file_path.stat().st_size,
        "mime_type": mimetypes.guess_type(str(file_path))[0] or "unknown"
    }

    # Try to extract a bit of content for text files
    if file_info["mime_type"] and file_info["mime_type"].startswith("text/"):
        try:
            with open(file_path, 'r', errors='ignore') as f:
                file_info["preview"] = f.read(1000)  # First 1000 chars
        except Exception as e:
            file_info["preview"] = f"Error reading file content: {str(e)}"

    return file_info


def suggest_name_with_llm(file_info: Dict[str, Any]) -> Optional[str]:
    """Ask the LLM for a better filename and category based on file information."""
    prompt: str = f"""
    I need a better filename, foldername, and category for this file.

    Current filename: {file_info['name']}
    File extension: {file_info['extension']}
    MIME type: {file_info['mime_type']}
    File size: {file_info['size_bytes']} bytes

    {"File preview: " + file_info['preview'] if 'preview' in file_info else ""}
    
    Please provide the following in a json string output:
    1. "fileName" : "correctFilename.ext", 
    2. "folderName" : "Suggested Folder Name",
    3. "category" : "Suggested Category"

    1. Filename
    Please suggest a clear, descriptive filename that follows these rules:
    - Keep the same file extension
    - Use Upper case camel case
    - if extension is PDF, it maybe a book title so use the official book title, and use spaced out words
    - if it's an executable, try to see what software it is, then use that software name
    - Be specific and descriptive about the content
    - Maximum 50 characters (excluding extension)
    - Return ONLY the new filename with no additional text or explanation
    
    2. Foldername
     - Similar to above, except remove any file extensions for this name
     - Do not show any versioning
     - The words have to be separated by space
     - If it's an application, just have the application, don't need to leave things like 'installer' or 'disk image' or "Mac/Windows" or "Application" etc

    3. Category
     - Suggest a category for the file based on its content, such as "Software", "Book", "Image", "Video", etc.
     - Provide a single word or short phrase.
    """

    payload: Dict[str, Any] = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response: requests.Response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data: Dict[str, Any] = response.json()

        # Extract the text from the response
        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            if "content" in response_data["candidates"][0]:
                if "parts" in response_data["candidates"][0]["content"]:
                    suggested_responses: str = response_data["candidates"][0]["content"]["parts"][0]["text"].strip(
                    )
                    # Clean up any potential formatting or quotes
                    # suggested_responses = suggested_responses.replace(
                    #     '"', '').replace("'", "").strip()
                    suggested_responses = suggested_responses.replace(
                        "```json", "").replace("```", "").replace("\n", " ")
                    return suggested_responses

        return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {str(e)}")
        return None


def suggest_category_with_llm(file_info: Dict[str, Any]) -> Optional[str]:
    """Ask the LLM for an appropriate category for the file."""
    prompt: str = f"""
    Based on the following file information, suggest an appropriate category:

    Current filename: {file_info['name']}
    File extension: {file_info['extension']}
    MIME type: {file_info['mime_type']}
    File size: {file_info['size_bytes']} bytes

    {"File preview: " + file_info['preview'] if 'preview' in file_info else ""}
    
    Please provide the category in a single word or short phrase (e.g., "Software", "Book", "Image", "Video", etc.).
    """

    payload: Dict[str, Any] = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response: requests.Response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        response_data: Dict[str, Any] = response.json()

        # Extract the text from the response
        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            if "content" in response_data["candidates"][0]:
                if "parts" in response_data["candidates"][0]["content"]:
                    category: str = response_data["candidates"][0]["content"]["parts"][0]["text"].strip(
                    )
                    return category.capitalize()  # Ensure category is capitalized

        return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API for category suggestion: {str(e)}")
        return None


def rename_files(directory_path: str, execute_actions: bool = False) -> None:
    """Process all files in the given directory and move them to a new folder based on LLM suggestions."""
    directory: Path = Path(directory_path)

    if not directory.exists() or not directory.is_dir():
        print(f"Error: {directory_path} is not a valid directory")
        return

    for file_path in directory.iterdir():
        if file_path.is_file():
            if any(skip_file_name in file_path.name for skip_file_name in SKIP_FILES):
                print(f"Skipping file: {file_path.name}")
                continue

            print(f"\nProcessing file: {file_path.name}")

            # Get file information
            file_info: Dict[str, Any] = get_file_info(str(file_path))

            # Get suggestion from LLM
            suggested_responses: Optional[str] = suggest_name_with_llm(
                file_info)

            if suggested_responses:
                try:
                    data = json.loads(suggested_responses)
                    folder_name = data["folderName"]
                    file_name = data["fileName"]

                    # Determine category folder based on file type or ask LLM
                    if file_info["mime_type"].startswith("application/"):
                        category_folder = "Software"
                    elif file_info["mime_type"] == "application/pdf":
                        category_folder = "Book"
                    else:
                        category_folder = suggest_category_with_llm(
                            file_info) or "Uncategorized"

                    if execute_actions:
                        # Create the target folder
                        target_folder: Path = directory / category_folder / folder_name
                        target_folder.mkdir(parents=True, exist_ok=True)

                        # Move and rename the file
                        new_path: Path = target_folder / file_name
                        file_path.rename(new_path)

                        print(
                            f"✓ Moved '{file_path.name}' to folder: '{target_folder}'")
                    else:
                        print(
                            f"Would move '{file_path.name}' to folder: '{target_folder}'")
                        print(f"New filename: '{file_name}'")
                        print(f"Category: '{category_folder}'")
                except (OSError, json.JSONDecodeError) as e:
                    print(
                        f"Error processing file '{file_path.name}': {str(e)}")
            else:
                print(
                    f"Couldn't get a folder name suggestion for: {file_path.name}")


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python file_sort.py <directory_path> [--execute-actions]")
        sys.exit(1)
    directory_path: str = sys.argv[1]
    execute_actions: bool = any("--execute-actions" in arg for arg in sys.argv)
    rename_files(directory_path, execute_actions)


if __name__ == "__main__":
    main()
