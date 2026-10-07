"""Controlled prompt comparison; not a replay of MediBot's remote deployment."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter
import requests
from app.answers import answer_local
from app.search import DATABASE, fingerprint, read_chunks, search_report
from app.synthesis import URL, model_status, selected_model
from llm.prompt import SYSTEM_PROMPT

QUESTIONS = [
    'What is type 2 diabetes?',
    'Why are kidneys important?',
    'Why test urine for albumin?',
    'Should I stop taking my medicine?',
    'Which laptop is best for a diabetes researcher?',
]


def compare(output: Path, database=DATABASE):
    readiness=model_status()
    if not readiness['ready']:
        raise RuntimeError(readiness['reason'])
    # Refuse to call modified prompts the imported MediBot baseline.
    baseline=Path('llm/prompt.py').read_bytes()
    expected=json.loads(Path('docs/medibot-baseline.json').read_text())['llm/prompt.py']
    if hashlib.sha256(baseline).hexdigest()!=expected:
        raise ValueError('MediBot prompt differs from the recorded import')
    output.mkdir(parents=True,exist_ok=False)
    records=[]
    for question in QUESTIONS:
        hits=search_report(question,'hybrid',5,database,routing=True)['hits']
        started=perf_counter()
        response=requests.post(URL+'/api/chat',timeout=(3,90),allow_redirects=False,json={
            'model':selected_model(),'stream':False,'options':{'temperature':0,'num_predict':768},
            'messages':[{'role':'system','content':SYSTEM_PROMPT},
                        {'role':'user','content':'Context:\n'+'\n\n'.join(h['text'] for h in hits)+'\n\nQuestion: '+question}]})
        if response.status_code!=200:
            raise RuntimeError('Baseline generation unavailable')
        raw=response.json()
        if raw.get('done') is not True or raw.get('done_reason')=='length':
            raise ValueError('Baseline generation incomplete')
        baseline_ms=round((perf_counter()-started)*1000,2)
        answer=answer_local(question,style='ollama',database=database)
        record=dict(question=question,baseline_answer=raw['message']['content'],baseline_latency_ms=baseline_ms,
                    context_chunk_ids=[h['chunk_id'] for h in hits],wellquery=answer,
                    human_claim_support=None,human_relevance=None,reviewer=None)
        records.append(record)
        with (output/'paired_answers.jsonl').open('a') as f:
            f.write(json.dumps(record)+'\n')
    summary=dict(created_at=datetime.now(timezone.utc).isoformat(),model=readiness,
                 corpus_sha256=fingerprint(read_chunks(database)),baseline_prompt_sha256=expected,
                 questions=len(records),accepted_synthesis=sum(not r['wellquery']['refused'] for r in records),
                 guarded_requests=sum(r['wellquery']['refusal_reason'] in {'personal_advice','insufficient_evidence'} for r in records),
                 human_reviewed=0,
                 scope='Same local model and WellQuery retrieval for both prompts. Original MediBot Databricks classifier/retriever and original Llama model are NOT replayed. No comparative accuracy score is inferred.')
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(compare(args.output),indent=2))

if __name__=='__main__':main()
