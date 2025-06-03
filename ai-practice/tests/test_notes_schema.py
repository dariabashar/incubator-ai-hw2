#!/usr/bin/env python3
"""
test_notes_schema.py — Тесты схемы Note для дискретной математики
"""

import pytest
import json
import importlib.util
from typing import List
from pydantic import ValidationError
from pathlib import Path

# Импорт модели Note и NotesResponse из generate_notes
def import_generate_notes():
    script_path = Path(__file__).parent.parent / "scripts" / "02_generate_notes.py"
    spec = importlib.util.spec_from_file_location("generate_notes", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Note, module.NotesResponse

Note, NotesResponse = import_generate_notes()

class TestNoteSchema:
    def test_valid_note_creation(self):
        note = Note(
            id=1,
            heading="Propositional Logic",
            summary="Basic operations like AND, OR, and implications in logic.",
            page_ref=12
        )
        assert note.id == 1
        assert note.heading == "Propositional Logic"
        assert len(note.summary) <= 150

    def test_note_without_page_ref(self):
        note = Note(
            id=2,
            heading="Set Theory",
            summary="Deals with collections of objects called sets."
        )
        assert note.page_ref is None

    def test_invalid_note_id_too_low(self):
        with pytest.raises(ValidationError):
            Note(id=0, heading="Error", summary="Should fail")

    def test_invalid_note_id_too_high(self):
        with pytest.raises(ValidationError):
            Note(id=11, heading="Too high", summary="Invalid")

    def test_summary_too_long(self):
        long_summary = "x" * 200
        with pytest.raises(ValidationError):
            Note(id=1, heading="Too long", summary=long_summary)

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            Note(id=1)
        with pytest.raises(ValidationError):
            Note(id=2, heading="No summary")


class TestNotesResponse:
    def test_valid_notes_response(self):
        notes_data = [
            {"id": i, "heading": f"Topic {i}", "summary": f"Summary {i}", "page_ref": i}
            for i in range(1, 11)
        ]
        response = NotesResponse(notes=notes_data)
        assert len(response.notes) == 10

    def test_too_few_notes(self):
        with pytest.raises(ValidationError):
            NotesResponse(notes=[{"id": 1, "heading": "Only One", "summary": "Not enough"}])

    def test_too_many_notes(self):
        notes = [{"id": i, "heading": f"Topic {i}", "summary": f"Summary {i}"} for i in range(1, 12)]
        with pytest.raises(ValidationError):
            NotesResponse(notes=notes)


class TestJSONValidation:
    def test_valid_json_parsing(self):
        json_data = {
            "notes": [
                {
                    "id": i,
                    "heading": f"Discrete Topic {i}",
                    "summary": f"Summary of discrete topic {i}",
                    "page_ref": i * 5 if i % 2 == 0 else None
                } for i in range(1, 11)
            ]
        }
        notes_response = NotesResponse(**json_data)
        assert notes_response.notes[1].page_ref == 10

    def test_invalid_json_structure(self):
        with pytest.raises(ValidationError):
            NotesResponse(**{"wrong_key": [{"id": 1, "heading": "Test", "summary": "Oops"}]})

    def test_mixed_valid_invalid_notes(self):
        notes = [{"id": i, "heading": f"Topic {i}", "summary": f"Summary {i}"} for i in range(1, 10)]
        notes.append({"id": 15, "heading": "Invalid", "summary": "Invalid ID"})
        with pytest.raises(ValidationError):
            NotesResponse(notes=notes)


@pytest.fixture
def sample_notes_json():
    return {
        "notes": [
            {"id": 1, "heading": "Propositional Logic", "summary": "Truth tables and logical connectives.", "page_ref": 5},
            {"id": 2, "heading": "Predicate Logic", "summary": "Quantifiers and logical reasoning.", "page_ref": 10},
            {"id": 3, "heading": "Set Theory", "summary": "Operations on sets like union and intersection."},
            {"id": 4, "heading": "Functions", "summary": "Injective, surjective, bijective mappings.", "page_ref": 18},
            {"id": 5, "heading": "Relations", "summary": "Reflexive, symmetric, transitive properties.", "page_ref": 22},
            {"id": 6, "heading": "Counting Principles", "summary": "Product rule, permutations, and combinations.", "page_ref": 30},
            {"id": 7, "heading": "Graphs", "summary": "Vertices and edges, paths, cycles.", "page_ref": 35},
            {"id": 8, "heading": "Trees", "summary": "Hierarchical structures, spanning trees.", "page_ref": 38},
            {"id": 9, "heading": "Recursion", "summary": "Recursive definitions and mathematical induction.", "page_ref": 40},
            {"id": 10, "heading": "Boolean Algebra", "summary": "Algebraic structures for binary variables.", "page_ref": 45}
        ]
    }

def test_sample_notes_validation(sample_notes_json):
    notes_response = NotesResponse(**sample_notes_json)
    assert len(notes_response.notes) == 10
    assert notes_response.notes[0].heading == "Propositional Logic"
    assert notes_response.notes[2].page_ref is None
    assert notes_response.notes[4].page_ref == 22


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
