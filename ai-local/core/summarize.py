from __future__ import annotations

from typing import Dict, List

from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.text_rank import TextRankSummarizer


def summarize_texts(pages: List[Dict[str, str]], question: str, sentences: int = 5) -> str:
    texts = [page.get("text", "") for page in pages if page.get("text")]
    if not texts:
        return ""
    combined = "\n".join(texts)
    parser = PlaintextParser.from_string(combined, Tokenizer("french"))
    summarizer = TextRankSummarizer()
    summary_sentences = summarizer(parser.document, sentences)
    summary = " ".join(str(sentence) for sentence in summary_sentences)
    if not summary:
        return combined[:500]
    return summary

