import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from llm.prompt import SYSTEM_PROMPT
from app.config import settings

MODEL_NAME = settings.MODEL_NAME
HF_TOKEN = settings.HF_TOKEN
MAX_NEW_TOKENS = settings.MAX_NEW_TOKENS 

_tokenizer = None # saved tokenizer
_pipe = None # saved pipeline

def load_model():
    global _tokenizer, _pipe # use globals

    if _pipe is not None:
        return

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=HF_TOKEN) # load tokenizer
    tokenizer.pad_token = tokenizer.eos_token # set pad token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, # load model
        torch_dtype=torch.float32, # use float32 for compatibility
        device_map="cpu", # run on cpu
        token=HF_TOKEN,
    )

    _pipe = pipeline(
        "text-generation", # text generation task
        model=model, # model to use
        tokenizer=tokenizer, # tokenizer to use
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=False, # no sampling
        temperature=0.0,
        return_full_text=False, # return only generated text
    )

    _tokenizer = tokenizer # save tokenizer

def build_llama_prompt(context: str, question: str) -> str:
    load_model()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    return _tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

def _normalize_chunks(chunks):
    if not chunks: # empty input
        return []
    
    if isinstance(chunks[0], str): # already strings
        return [c for c in chunks if c]
    
    if isinstance(chunks[0], dict): # dicts with "chunk_text"
        return [(c.get("chunk_text") or "") for c in chunks if (c.get("chunk_text") or "").strip()]
    
    return [str(c) for c in chunks]

def answer_with_llm(question: str, chunks) -> str:
    chunks = _normalize_chunks(chunks)

    if not chunks:
        return (
            "I could not find enough reliable information to answer that. "
            "Please consult a healthcare professional."
        )

    context = "\n\n".join(chunks) # join chunks
    prompt = build_llama_prompt(context, question) # build prompt

    try:
        return _pipe(prompt)[0]["generated_text"].strip() # generate answer
    except Exception:
        return (
            "Something went wrong while generating an answer. "
            "Please try again later or speak to a healthcare professional."
        )