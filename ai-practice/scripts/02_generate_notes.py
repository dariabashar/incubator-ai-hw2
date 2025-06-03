#!/usr/bin/env python3
"""
02_generate_notes.py - Part 2 Generate 10 Exam Notes

This script generates exactly ten bite-sized revision notes in JSON format,
enforcing a schema with Structured Output using Pydantic models.
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Note(BaseModel):
    """Pydantic model for a single study note."""
    id: int = Field(..., ge=1, le=10, description="Note ID between 1 and 10")
    heading: str = Field(..., max_length=100, description="Concise heading for the note")
    summary: str = Field(..., max_length=150, description="Brief summary of the concept")
    page_ref: Optional[int] = Field(None, description="Page number in source PDF")

class NotesResponse(BaseModel):
    """Container for the list of notes."""
    notes: List[Note] = Field(..., min_length=10, max_length=10, description="Exactly 10 study notes")

def get_assistant_id():
    """Load the assistant ID from the bootstrap script."""
    assistant_file = Path("assistant_id.json")
    if not assistant_file.exists():
        print("Assistant not found. Please run 00_bootstrap.py first.")
        return None
    
    with open(assistant_file, 'r') as f:
        data = json.load(f)
        return data.get("assistant_id")

def generate_notes_with_assistant(client, assistant_id):
    """Generate notes using the assistant with file_search capability."""
    print("🔍 Generating notes using assistant with file search...")
    
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add message to thread
    message_content = (
        "Please analyze the uploaded study materials and create exactly 10 concise revision notes. "
        "Each note should have a clear heading, a brief summary (max 150 characters), and ideally a page reference. "
        "Focus on the most important concepts that would help prepare for an exam. "
        "\n\nIMPORTANT: Respond with ONLY a valid JSON object, no additional text or markdown formatting. "
        "Use this exact structure:\n"
        '{"notes": [{"id": 1, "heading": "Topic Name", "summary": "Brief explanation", "page_ref": 1}, ...]}'
    )
    
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_content
    )
    
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion
    while run.status in ['queued', 'in_progress']:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(f"Status: {run.status}...")
        
    if run.status == 'completed':
        # Get messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        # Find the assistant's response
        for message in messages.data:
            if message.role == "assistant":
                content = message.content[0].text.value
                print(" Notes generated successfully!")
                return content
    
    print(f"Run failed with status: {run.status}")
    return None

def generate_notes_with_chat(client):
    """Generate notes using chat completions with JSON mode."""
    print("🔍 Generating notes using chat completions with JSON mode...")
    
    system_prompt = (
        "You are a study summarizer. "
        "Return exactly 10 unique notes that will help prepare for the exam. "
        "Each note should have an id (1-10), heading, summary (max 150 chars), and optional page_ref. "
        "Respond *only* with valid JSON matching this schema: "
        '{"notes": [{"id": 1, "heading": "Topic Name", "summary": "Brief explanation", "page_ref": 1}]} '
        "Focus on key mathematical concepts, theorems, and formulas."
    )
    
    user_prompt = (
        "Generate 10 concise study notes for calculus basics. "
        "Include topics like derivatives, integrals, limits, theorems, and key formulas. "
        "Make each note practical for exam preparation."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating notes: {e}")
        return None

def validate_and_save_notes(notes_json_str, output_file="exam_notes.json"):
    """Validate notes against Pydantic schema and save to file."""
    try:
        # Clean the response - remove markdown code blocks if present
        cleaned_json = notes_json_str.strip()
        
        # Remove markdown JSON code blocks
        if cleaned_json.startswith("```json"):
            # Find the start and end of the JSON block
            start_idx = cleaned_json.find("```json") + 7
            end_idx = cleaned_json.rfind("```")
            if end_idx > start_idx:
                cleaned_json = cleaned_json[start_idx:end_idx].strip()
        elif cleaned_json.startswith("```"):
            # Handle generic code blocks
            start_idx = cleaned_json.find("```") + 3
            end_idx = cleaned_json.rfind("```")
            if end_idx > start_idx:
                cleaned_json = cleaned_json[start_idx:end_idx].strip()
        
        # Remove any leading text before the JSON
        if cleaned_json.find("{") > 0:
            cleaned_json = cleaned_json[cleaned_json.find("{"):]
        
        # Parse JSON
        data = json.loads(cleaned_json)
        
        # Validate with Pydantic
        notes_response = NotesResponse(**data)
        
        print(f"Successfully validated {len(notes_response.notes)} notes!")
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Notes saved to {output_file}")
        
        # Display notes
        print("\n📚 Generated Exam Notes:")
        print("=" * 50)
        
        for note in notes_response.notes:
            print(f"\n{note.id}. {note.heading}")
            print(f"   📝 {note.summary}")
            if note.page_ref:
                print(f"   📄 Page: {note.page_ref}")
        
        return notes_response.notes
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        print("Raw response (first 500 chars):", notes_json_str[:500])
        print("\nCleaned response (first 300 chars):", cleaned_json[:300] if 'cleaned_json' in locals() else "N/A")
        return None
    except Exception as e:
        print(f"❌ Validation error: {e}")
        print("Raw response (first 500 chars):", notes_json_str[:500])
        return None

def main():
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("📝 Exam Notes Generator")
    print("=" * 30)
    
    print("\nOptions:")
    print("1. Generate notes using assistant (with file search)")
    print("2. Generate notes using chat completions (JSON mode)")
    print("3. Exit")
    
    choice = input("\nChoose an option (1-3): ").strip()
    
    if choice == "1":
        # Use assistant with file search
        assistant_id = get_assistant_id()
        if not assistant_id:
            return
        
        notes_content = generate_notes_with_assistant(client, assistant_id)
        if notes_content:
            validate_and_save_notes(notes_content)
    
    elif choice == "2":
        # Use chat completions with JSON mode
        notes_content = generate_notes_with_chat(client)
        if notes_content:
            validate_and_save_notes(notes_content)
    
    elif choice == "3":
        print("Goodbye! 👋")
    
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 