#!/usr/bin/env python3
"""
01_qna_assistant.py - Part 1 Q&A Assistant from PDFs

This script interacts with the assistant to answer study questions
by retrieving passages from uploaded PDFs and streaming responses.
"""

import os
import json
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_assistant_id():
    """Load the assistant ID from the bootstrap script."""
    assistant_file = Path("assistant_id.json")
    if not assistant_file.exists():
        print("Assistant not found. Please run 00_bootstrap.py first.")
        return None
    
    with open(assistant_file, 'r') as f:
        data = json.load(f)
        return data.get("assistant_id")

def ask_question(client, assistant_id, question):
    """Ask a question to the assistant and stream the response."""
    print(f"\n🤔 Question: {question}")
    print("=" * 60)
    
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )
    
    # Create and stream the run
    print("Assistant response:")
    
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant_id
    ) as stream:
        for event in stream:
            if event.event == 'thread.message.delta':
                if event.data.delta.content:
                    for content in event.data.delta.content:
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            print(content.text.value, end='', flush=True)
    
    print("\n")
    
    # Get the final messages to check for citations
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    # Find the assistant's response
    for message in messages.data:
        if message.role == "assistant":
            # Check for citations
            if hasattr(message, 'content') and message.content:
                for content in message.content:
                    if hasattr(content, 'text') and hasattr(content.text, 'annotations'):
                        annotations = content.text.annotations
                        if annotations:
                            print("Citations:")
                            for i, annotation in enumerate(annotations, 1):
                                if hasattr(annotation, 'file_citation'):
                                    file_citation = annotation.file_citation
                                    print(f"  [{i}] File ID: {file_citation.file_id}")
                                    if hasattr(file_citation, 'quote'):
                                        print(f"      Quote: {file_citation.quote[:100]}...")
            break
    
    return thread.id

def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get assistant ID
    assistant_id = get_assistant_id()
    if not assistant_id:
        return
    
    print(f"Using assistant: {assistant_id}")
    
    # Example questions to test
    test_questions = [
        "Which logical operation corresponds to the phrase “if and only if”?",
        "What is a tautology? Give an example.",
        "What is the difference between a universal and existential quantifier?",
        "What is the power set of {a, b}?"
    ]
    
    print("Study Q&A Assistant")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Ask a question")
        print("2. Try example questions")
        print("3. Exit")
        
        choice = input("\nChoose an option (1-3): ").strip()
        
        if choice == "1":
            question = input("\nEnter your question: ").strip()
            if question:
                ask_question(client, assistant_id, question)
        
        elif choice == "2":
            print("Testing example questions...")
            for i, question in enumerate(test_questions, 1):
                print(f"\n--- Example {i} ---")
                ask_question(client, assistant_id, question)
                
                if i < len(test_questions):
                    input("\nPress Enter to continue to next question...")
        
        elif choice == "3":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 