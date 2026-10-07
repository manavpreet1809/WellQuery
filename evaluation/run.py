"""Compare retrieval configurations and export answers for human review."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
from app.search import DATABASE, MODEL, REVISION, fingerprint, read_chunks, search_report
from app.answers import answer_local
from app.routing import route_question

CONFIGS = [('keyword',False),('vector',False),('hybrid',False),('hybrid',True)]


def load_questions(path: Path, include_drafts: bool = False) -> list[dict]:
    """Default to reviewed questions; reject empty or inconsistent datasets."""
    all_items = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len({q['id'] for q in all_items}) != len(all_items):
        raise ValueError('Duplicate question IDs')
    groups = {}
    for q in all_items:
        if type(q.get('verified')) is not bool:
            raise ValueError('Every question requires an explicit boolean verified flag')
        if q['split'] not in {'development','test'} or q['expected'] not in {'answer','emergency','personal_advice','injection','insufficient_evidence'}:
            raise ValueError('Invalid split or expected outcome')
        if not q.get('question','').strip() or len(q['question']) > 1000:
            raise ValueError('Invalid question')
        if q['expected'] == 'answer' and not q.get('relevant'):
            raise ValueError('Answerable questions require relevant sections')
        if q['expected_route'] not in {'drug','condition','all'}:
            raise ValueError('Invalid expected route')
        if q['verified'] and not q.get('reviewer'):
            raise ValueError('Verified questions require reviewer attribution')
        if q['group'] in groups and groups[q['group']] != q['split']:
            raise ValueError('Paraphrase groups cannot cross splits')
        groups[q['group']] = q['split']
    items = [q for q in all_items if include_drafts or q['verified']]
    if not items:
        raise ValueError('No human-verified questions. Review the dataset or use --include-drafts for development only.')
    return items


def retrieval_metrics(hits: list[dict], relevant: list[dict], k: int = 5) -> dict:
    """Recall counts distinct relevant sections, not repeated overlapping chunks."""
    expected = {(r['document_id'],r['section_path']) for r in relevant}
    if not expected:
        raise ValueError('Relevance labels required')
    seen = set()
    first = 0
    for rank, hit in enumerate(hits[:k],1):
        key = (hit['document_id'],hit['section_path'])
        if key in expected:
            seen.add(key)
            first = first or rank
    return {'recall_at_5':len(seen)/len(expected), 'reciprocal_rank_at_5':1/first if first else 0}


def percentile95(values):
    """Nearest-rank p95, including small evaluation sets."""
    import math
    return sorted(values)[max(0,math.ceil(len(values)*.95)-1)]


def run(questions: list[dict], database: Path, output: Path, *, include_answers=True) -> dict:
    """Write per-query evidence and provenance; do not infer claim correctness."""
    corpus = read_chunks(database)
    sections = {(h['document_id'],h['section_path']) for h in corpus}
    for q in questions:
        if any((r['document_id'],r['section_path']) not in sections for r in q['relevant']):
            raise ValueError(f'Relevance label absent from corpus: {q["id"]}')
    rows, reviews = [], []
    for q in questions:
        if q['expected'] == 'answer':
            for mode,routing in CONFIGS:
                report=search_report(q['question'],mode,5,database,routing=routing)
                rows.append(dict(id=q['id'],split=q['split'],verified=q['verified'],
                                 configuration=mode+('+routing' if routing else ''),
                                 **retrieval_metrics(report['hits'],q['relevant']),
                                 latency_ms=report['latency_ms']))
        if include_answers:
            answer=answer_local(q['question'],database=database)
            actual=answer['refusal_reason'] if answer['refused'] else 'answer'
            reviews.append(dict(id=q['id'],split=q['split'],verified=q['verified'],question=q['question'],
                                expected=q['expected'],actual=actual,behaviour_match=actual==q['expected'],
                                expected_route=q['expected_route'],rule_route=route_question(q['question'])['category'],
                                answer=answer['answer'],citations=answer['citations'],
                                quote_validity=all(c['quote'] in next(h['text'] for h in answer['citations'] if h['chunk_id']==c['source_id']) for c in answer['claims']) if answer['claims'] else None,
                                human_claim_support=None,human_relevance=None,reviewer=None))
    summary = {'label':'DRAFT DEVELOPMENT RESULTS' if any(not q['verified'] for q in questions) else 'HUMAN-VERIFIED QUESTION SET',
               'created_at':datetime.now(timezone.utc).isoformat(), 'model':MODEL, 'model_revision':REVISION,
               'corpus_sha256':fingerprint(corpus),
               'implementation_sha256':hashlib.sha256(b''.join(p.read_bytes() for p in sorted(Path('app').glob('*.py')))+Path(__file__).read_bytes()).hexdigest(),
               'question_count':len(questions),
               'verified_question_count':sum(q['verified'] for q in questions), 'configurations':{},
               'limitations':['Question verification does not establish answer correctness.',
                              'Exact support quotes do not establish semantic entailment.',
                              'First vector request may include model loading; timings are not controlled benchmarks.',
                              'Results from this narrow corpus do not establish clinical safety.']}
    try:
        summary['git_sha']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        summary['working_tree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip())
    except subprocess.CalledProcessError:
        summary['git_sha']=None
    for split in ('development','test'):
        for mode,routing in CONFIGS:
            name=mode+('+routing' if routing else '')
            selected=[r for r in rows if r['configuration']==name and r['split']==split]
            if selected:
                summary['configurations'][split+'/'+name]=dict(n=len(selected),
                    recall_at_5=statistics.mean(r['recall_at_5'] for r in selected),
                    mrr_at_5=statistics.mean(r['reciprocal_rank_at_5'] for r in selected),
                    p95_ms=percentile95([r['latency_ms'] for r in selected]))
    summary['behaviour_checks']={}
    for outcome in sorted({r['expected'] for r in reviews}):
        group=[r for r in reviews if r['expected']==outcome]
        summary['behaviour_checks'][outcome]={'n':len(group),'match_rate':statistics.mean(r['behaviour_match'] for r in group)}
    summary['rule_route_accuracy']=statistics.mean(r['rule_route']==r['expected_route'] for r in reviews) if reviews else None
    failures = []
    for row in rows:
        if row['recall_at_5'] < 1:
            failures.append(dict(kind='retrieval_miss', **row))
    for review in reviews:
        if not review['behaviour_match']:
            failures.append(dict(kind='behaviour_mismatch', id=review['id'],
                                 expected=review['expected'], actual=review['actual']))
        if review['rule_route'] != review['expected_route']:
            failures.append(dict(kind='route_mismatch', id=review['id'],
                                 expected=review['expected_route'], actual=review['rule_route']))
    summary['failure_counts'] = {kind: sum(f['kind'] == kind for f in failures)
                                for kind in ('retrieval_miss', 'behaviour_mismatch', 'route_mismatch')}
    output.mkdir(parents=True,exist_ok=False)
    (output/'failures.jsonl').write_text(''.join(json.dumps(f)+'\n' for f in failures))
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if rows:
        with (output/'retrieval.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (output/'answer_review.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in reviews))
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--questions',type=Path,default=Path('evaluation/questions.jsonl'))
    parser.add_argument('--database',type=Path,default=DATABASE)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--include-drafts',action='store_true')
    parser.add_argument('--retrieval-only',action='store_true')
    args=parser.parse_args()
    try:
        questions=load_questions(args.questions,args.include_drafts)
        output=args.output or Path('evaluation/results')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        summary=run(questions,args.database,output,include_answers=not args.retrieval_only)
        summary['questions_sha256']=hashlib.sha256(args.questions.read_bytes()).hexdigest()
        (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps({'label':summary['label'],'questions':len(questions),'output':str(output)}))
    except (ValueError,RuntimeError,OSError) as exc:
        parser.exit(1,f'Evaluation failed: {exc}\n')

if __name__=='__main__':main()
