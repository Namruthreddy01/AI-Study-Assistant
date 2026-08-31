import asyncio

from app.models.schemas import QuizSubmission


def test_retrieval_summary_generation_and_quiz(service, pdf_bytes: bytes) -> None:
    document = service.ingest_pdf("networks.pdf", pdf_bytes)

    chat = asyncio.run(service.answer_question(document["id"], "What is the OSI model?"))
    summary = asyncio.run(service.generate_summary(document["id"], "short"))
    mcqs = asyncio.run(service.generate_mcqs(document["id"], 3, "easy"))
    revision = asyncio.run(service.generate_revision(document["id"], 2, "exam"))
    score = service.score_quiz(
        QuizSubmission(
            document_id=document["id"],
            questions=mcqs.questions,
            answers={question.id: question.correct_answer for question in mcqs.questions},
        )
    )

    assert document["chunks"] >= 1
    assert chat.grounded is True
    assert chat.sources[0].page == 1
    assert summary.key_points
    assert len(mcqs.questions) == 3
    assert len(revision.questions) == 2
    assert score.score == 3
    assert score.percentage == 100


def test_no_context_returns_grounded_refusal(service, pdf_bytes: bytes) -> None:
    document = service.ingest_pdf("networks.pdf", pdf_bytes)

    response = asyncio.run(
        service.answer_question(document["id"], "Explain photosynthesis in plants")
    )

    assert response.grounded is False
    assert "couldn't find" in response.answer

