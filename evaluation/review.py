"""Export review packets and apply explicit human decisions to a new dataset."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from evaluation.run import load_questions
from app.search import DATABASE, read_chunks


def digest(path: Path) -> str:
    """Identify the exact file version being reviewed."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path, text: str) -> None:
    """Never overwrite a dataset or completed review by default."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        handle.write(text)


def export_packet(questions: Path, output: Path, database: Path = DATABASE) -> dict:
    """Include proposed labels and source evidence; leave all decisions blank."""
    items = load_questions(questions, include_drafts=True)
    corpus = read_chunks(database)
    reviews = []
    for q in items:
        relevant = {(r['document_id'],r['section_path']) for r in q['relevant']}
        evidence = [h for h in corpus if (h['document_id'],h['section_path']) in relevant]
        if relevant - {(h['document_id'],h['section_path']) for h in evidence}:
            raise ValueError(f'Missing review evidence: {q["id"]}')
        reviews.append(dict(id=q['id'], question_snapshot=q, evidence=evidence,
                            decision=None, reviewer='', notes=''))
    packet = dict(version=1, dataset_sha256=digest(questions), items=reviews,
                  instructions='A human reviewer must inspect each question, label, and source. Set decision to approve or reject and record reviewer and notes. Leave unreviewed decisions null. Fix labels in the source dataset and re-export before approval. This packet is not a cryptographic identity or authorship guarantee.')
    write_new(output,json.dumps(packet,indent=2)+'\n')
    return {'questions':len(items),'reviewed':0}


def apply_packet(questions: Path, packet_path: Path, output: Path) -> dict:
    """Validate a packet and write a separate dataset, preserving unreviewed items."""
    items = load_questions(questions, include_drafts=True)
    packet = json.loads(packet_path.read_text())
    if packet.get('version') != 1 or packet.get('dataset_sha256') != digest(questions):
        raise ValueError('Stale or unsupported review packet; export again')
    reviews = packet['items']
    ids = [r['id'] for r in reviews]
    if len(set(ids)) != len(ids) or set(ids) != {q['id'] for q in items}:
        raise ValueError('Review IDs must match the dataset exactly, without duplicates')
    by_id = {r['id']:r for r in reviews}
    changed = 0
    for q in items:
        review = by_id[q['id']]
        if review['question_snapshot'] != q:
            raise ValueError('Question snapshot changed; correct the source dataset and re-export')
        decision = review.get('decision')
        if decision is None:
            continue
        if decision not in {'approve','reject'}:
            raise ValueError('Decision must be approve, reject, or null')
        if not isinstance(review.get('reviewer'),str) or not review['reviewer'].strip():
            raise ValueError('A reviewer is required for every decision')
        if not isinstance(review.get('notes'),str) or not review['notes'].strip():
            raise ValueError('Review notes are required for every decision')
        q.update(verified=decision=='approve', reviewer=review['reviewer'].strip(),
                 review_notes=review['notes'].strip(), reviewed_at=datetime.now(timezone.utc).isoformat(),
                 review_decision=decision)
        changed += 1
    if not changed:
        raise ValueError('No review decisions were supplied')
    write_new(output,''.join(json.dumps(q)+'\n' for q in items))
    return {'decisions_applied':changed,'verified_questions':sum(q['verified'] for q in items),
            'output':str(output),'original_modified':False}


def summarize_answers(path: Path) -> dict:
    """Summarize only explicit human judgments, showing their coverage and denominator."""
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate answer review IDs')
    counts = {key:0 for key in ('supported','unsupported','uncertain')}
    relevant = 0
    reviewed_answers = 0
    reviewed_refusals = 0
    total_answers = sum(r['actual']=='answer' for r in rows)
    for r in rows:
        support, relevance = r.get('human_claim_support'), r.get('human_relevance')
        if support is None and relevance is None:
            continue
        if not isinstance(r.get('reviewer'),str) or not r['reviewer'].strip():
            raise ValueError('Human judgments require reviewer attribution')
        if relevance not in {'relevant','irrelevant','uncertain'}:
            raise ValueError('human_relevance must be relevant, irrelevant, or uncertain')
        if r['actual'] != 'answer':
            if support != 'not_applicable':
                raise ValueError('Refusals must use not_applicable for claim support')
            reviewed_refusals += 1
            continue
        if support not in counts:
            raise ValueError('Answer support must be supported, unsupported, or uncertain')
        reviewed_answers += 1
        counts[support] += 1
        relevant += relevance=='relevant'
    return dict(total_responses=len(rows), total_answers=total_answers, reviewed_answers=reviewed_answers,
                reviewed_refusals=reviewed_refusals, support_counts=counts,
                supported_fraction_of_reviewed_answers=counts['supported']/reviewed_answers if reviewed_answers else None,
                relevant_fraction_of_reviewed_answers=relevant/reviewed_answers if reviewed_answers else None,
                review_file_sha256=digest(path),
                note='Human judgments are self-attributed, not clinically certified. Unreviewed answers are excluded from quality fractions; inspect coverage.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest='command',required=True)
    export=subs.add_parser('export')
    export.add_argument('--questions',type=Path,default=Path('evaluation/questions.jsonl'))
    export.add_argument('--database',type=Path,default=DATABASE)
    export.add_argument('--output',type=Path,required=True)
    apply=subs.add_parser('apply')
    apply.add_argument('--questions',type=Path,default=Path('evaluation/questions.jsonl'))
    apply.add_argument('--packet',type=Path,required=True)
    apply.add_argument('--output',type=Path,required=True)
    summarize=subs.add_parser('summarize-answers')
    summarize.add_argument('path',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='export': result=export_packet(args.questions,args.output,args.database)
        elif args.command=='apply': result=apply_packet(args.questions,args.packet,args.output)
        else: result=summarize_answers(args.path)
        print(json.dumps(result,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(1,f'Review failed: {exc}\n')

if __name__=='__main__':main()
