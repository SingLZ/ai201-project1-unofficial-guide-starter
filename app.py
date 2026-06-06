# app.py

from __future__ import annotations

import gradio as gr

from query import ask


def handle_query(question: str) -> tuple[str, str]:
    result = ask(question)

    sources = result.get("sources", [])
    source_text = "\n".join(f"• {source}" for source in sources)

    if not source_text:
        source_text = "No sources retrieved."

    return result["answer"], source_text


with gr.Blocks(title="Unofficial South San Jose Housing Guide") as demo:
    gr.Markdown("# Unofficial South San Jose Housing Guide")
    gr.Markdown(
        "Ask questions about South San Jose apartment budgets, neighborhoods, parking, safety, "
        "commute, amenities, and renter experiences. Answers are generated only from the collected documents."
    )

    question = gr.Textbox(
        label="Your question",
        placeholder="Example: What is the estimated budget for 1B1B in San Jose?",
        lines=2,
    )

    ask_button = gr.Button("Ask")

    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=6)

    ask_button.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()