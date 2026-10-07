"""Auditable request boundaries for a narrow educational prototype, not triage."""
import re
import unicodedata

EMERGENCY = re.compile(
    r'\b(chest pain|can(?:not|\x27t) breathe|(?:trouble|difficulty|struggling) (?:with )?breathing|'
    r'struggling to (?:breathe|get air)|gasping for (?:air|breath)|severe bleeding|'
    r'bleeding (?:will not|won\x27t) stop|overdose|(?:too many|too much) (?:\w+ ){0,2}(?:pills|tablets|insulin|medicine)|'
    r'kill myself|suicidal|end my life)\b', re.I)
PERSONAL = re.compile(
    r'\b(diagnose me|do i have|should i (?:take|stop|start|change|increase|reduce)|'
    r'how much .{0,50}should i|what dose|my dose|'
    r'(?:dose|dosage).{0,50}(?:for me|my (?:body|weight|age))|'
    r'can i (?:stop|double|increase|reduce).{0,30}(?:medicine|medication|insulin|dose)|'
    r'(?:tell|give) me.{0,30}(?:dose|dosage)|am i (?:diabetic|having))\b', re.I)
INJECTION = re.compile(
    r'ignore (?:all |previous )?instructions|system prompt|you are now|'
    r'(?:disregard|override|bypass).{0,30}(?:rules|instructions|safeguards)|'
    r'(?:reveal|print|show).{0,30}(?:hidden instructions|confidential configuration|api keys|secrets)', re.I)
OFF_TOPIC = re.compile(
    r'\b(laptop|smartphone|stock price|cryptocurrency|bitcoin|football|weather|'
    r'(?:write|implement|debug).{0,30}(?:poem|essay|code|algorithm|program)|book (?:a )?flight|restaurant|video game)\b', re.I)


def normalize(text: str) -> str:
    return unicodedata.normalize('NFKC', text).replace('’', "'")


def has_emergency(text: str) -> bool:
    """Ignore only explicit symptom denials immediately before an occurrence.

    A later affirmative symptom still triggers. This deliberately does not try to
    infer clinical context or interpret broad, ambiguous negation.
    """
    for match in EMERGENCY.finditer(text):
        prefix=text[:match.start()]
        denied=re.search(r"\b(?:no|without|(?:do not|don't|does not|doesn't) have)\s+(?:(?:any|current)\s+)?$",prefix,re.I)
        if not denied:
            return True
    return False


def guard(question: str) -> tuple[str, str] | None:
    text=normalize(question)
    if has_emergency(text):
        return 'emergency', 'If this may be an emergency, contact your local emergency services now. This prototype cannot assess emergencies.'
    if PERSONAL.search(text):
        return 'personal_advice', 'I cannot diagnose you or recommend personal medication changes. Please speak with a qualified healthcare professional.'
    if INJECTION.search(text):
        return 'injection', 'I can only help explore information in the available documents.'
    if OFF_TOPIC.search(text):
        return 'insufficient_evidence', 'This collection covers diabetes, kidney health, and general medicine information. It does not provide evidence for that request.'
    return None
