from app.services.chunking import chunk_page_text


def test_chunking_preserves_metadata() -> None:
    text = "networking " * 250
    chunks = chunk_page_text(text, "doc-1", "notes.pdf", 3, chunk_size=100, overlap=20)

    assert len(chunks) > 2
    assert all(chunk.document_id == "doc-1" for chunk in chunks)
    assert all(chunk.filename == "notes.pdf" for chunk in chunks)
    assert all(chunk.page == 3 for chunk in chunks)
    assert chunks[0].id == "doc-1-p3-c0"

