"""Provider-neutral extraction boundary: propose facts, review, then persist.

An extractor is application-supplied code accepting a list of role/content
objects and returning a list of text/source_indices objects. No provider is
called unless the caller explicitly supplies and invokes that callable.
"""
import json
from .memory import string


def propose(messages, *, extractor):
    if not isinstance(messages, list) or not 1 <= len(messages) <= 100:
        raise ValueError("provide between 1 and 100 messages")
    clean = []
    for message in messages:
        if not isinstance(message, dict) or set(message) != {"role", "content"}:
            raise ValueError("messages require exactly role and content")
        if message["role"] not in ("user", "assistant"):
            raise ValueError("only user and assistant messages may be extracted")
        clean.append({"role": message["role"], "content": string(message["content"], "content", 32768)})
    if len(json.dumps(clean).encode()) > 131072:
        raise ValueError("conversation exceeds 128 KiB")
    # Copy so an extractor cannot alter provenance through mutation.
    output = extractor(json.loads(json.dumps(clean)))
    if not isinstance(output, list) or len(output) > 50:
        raise ValueError("extractor must return a list of at most 50 facts")
    proposals = []
    for fact in output:
        if not isinstance(fact, dict) or set(fact) != {"text", "source_indices"}:
            raise ValueError("facts require exactly text and source_indices")
        text = string(fact["text"], "fact text", 32768)
        indices = fact["source_indices"]
        if not isinstance(indices, list) or not indices or any(type(i) is not int or not 0 <= i < len(clean) for i in indices):
            raise ValueError("facts must reference valid source message indices")
        proposals.append({"text": text, "source_indices": sorted(set(indices)), "status": "needs_review"})
    return proposals
