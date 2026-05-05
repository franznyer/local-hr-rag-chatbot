"""Prompt templates for the HR RAG pipeline."""

HR_SYSTEM_PROMPT = """Tu es un assistant RH expert et professionnel.
Tu réponds UNIQUEMENT en te basant sur les documents RH fournis dans le contexte.

Règles strictes :
1. N'invente JAMAIS d'information absente du contexte.
2. Si la réponse n'est pas dans le contexte, réponds : "Je n'ai pas trouvé cette information dans les documents RH disponibles."
3. Cite toujours les sources entre parenthèses après chaque information importante, ex. : (Source : politique_conges.pdf).
4. Réponds en français, de façon claire, structurée et professionnelle.
5. Si la question est ambiguë, demande une clarification.
"""

RAG_USER_TEMPLATE = """Contexte documentaire (extraits des documents RH) :
---
{context}
---

Question : {question}

Réponds en te basant exclusivement sur les extraits ci-dessus. Cite les sources."""


def build_rag_prompt(question: str, context_chunks: list) -> str:
    """Assemble the context block and inject it into the prompt template."""
    if not context_chunks:
        context = "Aucun document pertinent trouvé."
    else:
        parts = []
        for chunk in context_chunks:
            parts.append(
                f"[Source : {chunk['source']} | Pertinence : {chunk['score']:.0%}]\n{chunk['text']}"
            )
        context = "\n\n".join(parts)

    return RAG_USER_TEMPLATE.format(context=context, question=question)
