"""Evidence-backed local answers and conservative prototype request boundaries."""
import re
from time import perf_counter
from app.search import DATABASE, search_report, tokens

EMERGENCY = re.compile(r'\b(chest pain|can(?:not|\x27t) breathe|trouble breathing|severe bleeding|overdose|kill myself|suicidal)\b', re.I)
PERSONAL = re.compile(r'\b(diagnose me|do i have|should i (?:take|stop|start|change)|how much .{0,50}should i|what dose|my dose)\b', re.I)
INJECTION = re.compile(r'ignore (?:all |previous )?instructions|system prompt|you are now', re.I)
STOP = set('a an the what is are of to for how why do does can in and or me about tell explain'.split())

def guard(question: str) -> tuple[str, str] | None:
    """Conservative phrase rules; context, negation, and unseen phrasing are limitations."""
    if EMERGENCY.search(question):
        return 'emergency', 'If this may be an emergency, contact your local emergency services now. This prototype cannot assess emergencies.'
    if PERSONAL.search(question):
        return 'personal_advice', 'I cannot diagnose you or recommend personal medication changes. Please speak with a qualified healthcare professional.'
    if INJECTION.search(question):
        return 'injection', 'I can only help explore information in the available documents.'
    return None


def ollama_claims(question: str, evidence: list[dict]) -> dict:
    """Ask a local Ollama model for structured claims with verbatim support quotes."""
    from app.synthesis import request_claims
    return request_claims(question, evidence)


def validate_claims(payload: dict, hits: list[dict]) -> list[dict]:
    """Validate every citation and exact support quote; this is not entailment checking."""
    if not isinstance(payload, dict) or not isinstance(payload.get('claims'), list):
        raise ValueError('Missing claims')
    claims = payload['claims']
    if len(claims) > 3:
        raise ValueError('Too many claims')
    lookup = {h['chunk_id']: h for h in hits}
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError('Invalid claim')
        text, quote = claim.get('text'), claim.get('quote')
        if not isinstance(text, str) or not text.strip() or len(text) > 1200:
            raise ValueError('Invalid claim text')
        hit = lookup.get(claim.get('source_id'))
        if hit is None or not isinstance(quote, str) or len(quote.strip()) < 15 or quote not in hit['text']:
            raise ValueError('Unsupported citation quote')
        if re.search(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|tablets?)\b', text, re.I) or PERSONAL.search(text):
            raise ValueError('Blocked output')
    return claims


def answer_local(question: str, *, style: str = 'excerpts', database=DATABASE, embed=None, generate=None) -> dict:
    """Return cited excerpts by default, or explicitly selected local-model synthesis."""
    started = perf_counter()
    result = dict(question=question, route='all', confidence=0, answer='', chunks_used=0,
                  chunks=[], citations=[], claims=[], refused=True, mode='local', answer_style=style,
                  refusal_reason=None, latency_ms=0)
    def finish(reason=None):
        result['refusal_reason'] = reason
        result['latency_ms'] = round((perf_counter()-started)*1000, 2)
        return result
    blocked = guard(question)
    if blocked:
        result['answer'] = blocked[1]
        return finish(blocked[0])
    if style not in {'excerpts', 'ollama'}:
        raise ValueError('Unknown answer style')
    report = search_report(question, 'hybrid', 5, database, embed, routing=True)
    # Require lexical overlap too; vector proximity by itself is not answerability.
    meaningful = set(tokens(question)) - STOP
    hits = [h for h in report['hits'] if meaningful & (set(tokens(h['text'])) - STOP)
            and not INJECTION.search(h['text'])]
    result['route'] = report['route']['category']
    if not hits:
        result['answer'] = 'The available documents do not provide enough evidence for this question.'
        return finish('insufficient_evidence')
    if style == 'excerpts':
        ranked = []
        for hit in hits:
            for sentence in re.split(r'(?<=[.!?])\s+', hit['text']):
                overlap = len(meaningful & (set(tokens(sentence)) - STOP))
                if overlap and 15 <= len(sentence) <= 1200:
                    ranked.append((overlap, hit['chunk_id'], sentence))
        ranked.sort(key=lambda x: (-x[0], x[1]))
        claims = []
        seen = set()
        for _, key, sentence in ranked:
            if sentence not in seen:
                claims.append(dict(text=sentence, source_id=key, quote=sentence))
                seen.add(sentence)
            if len(claims) == 3:
                break
        payload = {'claims': claims}
    else:
        payload = (generate or ollama_claims)(question, [dict(chunk_id=h['chunk_id'], text=h['text']) for h in hits])
    try:
        claims = validate_claims(payload, hits)
    except (ValueError, TypeError):
        result['answer'] = 'I could not produce an answer with valid supporting evidence.'
        return finish('invalid_output')
    if not claims:
        result['answer'] = 'The available documents do not provide enough evidence for this question.'
        return finish('insufficient_evidence')
    keys = list(dict.fromkeys(c['source_id'] for c in claims))
    lookup = {h['chunk_id']: h for h in hits}
    result['chunks'] = [lookup[key] for key in keys]
    result['citations'] = [dict(n=i+1, **lookup[key]) for i,key in enumerate(keys)]
    result['claims'] = [dict(**c, citation=keys.index(c['source_id'])+1) for c in claims]
    result['answer'] = '\n'.join(f'{c["text"]} [{keys.index(c["source_id"])+1}]' for c in claims)
    result['chunks_used'] = len(keys)
    result['refused'] = False
    return finish()
