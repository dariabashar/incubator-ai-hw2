#!/usr/bin/env python3
"""
00_bootstrap.py - Create/reuse assistant with file_search

This script creates an OpenAI assistant with file_search capabilities
and uploads the course PDF(s) for knowledge retrieval.

Usage: python scripts/00_bootstrap.py.py

Docs: https://platform.openai.com/docs/api-reference/assistants
"""

import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

def main():
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Check if assistant already exists
    assistant_file = Path("assistant_id.json")
    
    if assistant_file.exists():
        with open(assistant_file, 'r') as f:
            data = json.load(f)
            assistant_id = data.get("assistant_id")
            
        print(f"Using existing assistant: {assistant_id}")
        try:
            assistant = client.beta.assistants.retrieve(assistant_id)
        except Exception as e:
            print(f"Error retrieving assistant: {e}")
            print("Creating new assistant...")
            assistant_file.unlink()  # Remove invalid assistant file
            assistant = None
    else:
        assistant = None
    
    if not assistant:
        # Upload PDF file(s) from data directory first
        data_dir = Path("data")
        pdf_files = list(data_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("No PDF files found in data/ directory")
            return
        
        # Upload files for assistants
        file_ids = []
        for pdf_file in pdf_files:
            print(f"Uploading {pdf_file.name}...")
            
            with open(pdf_file, "rb") as f:
                file_obj = client.files.create(
                    purpose="assistants",
                    file=f
                )
            file_ids.append(file_obj.id)
            print(f"Uploaded file ID: {file_obj.id}")
        
        # Create new assistant with file attachments
        assistant = client.beta.assistants.create(
            name="Study Q&A Assistant",
            instructions=(
                "You are a helpful tutor. "
                "Use the knowledge in the attached files to answer questions. "
                "Cite sources where possible."
            ),
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_stores": [{
                        "file_ids": file_ids
                    }]
                }
            }
        )
        
        # Save assistant ID for reuse
        with open(assistant_file, 'w') as f:
            json.dump({"assistant_id": assistant.id}, f)
            
        print(f"Created new assistant: {assistant.id}")
        print(f"Assistant created with {len(file_ids)} file(s)")
    
    print("Bootstrap complete!")

if __name__ == "__main__":
    main() 