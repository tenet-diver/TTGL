"""Read-only queue projection; keep the active generation module byte-for-byte frozen."""
import json
import os
import bulk_analysis as bulk


def state(store,batch_id=None,offset=0,limit=20,list_query=''):
    bulk.init(store);offset,limit=int(offset),int(limit)
    if offset<0 or not 1<=limit<=100:raise ValueError('Invalid bulk analysis page')
    with store.connection() as c:
        batch=c.execute('SELECT * FROM bulk_analysis_batches '+('WHERE id=?' if batch_id else 'ORDER BY created DESC LIMIT 1'),(batch_id,) if batch_id else ()).fetchone()
        if not batch:return {'batch':None,'protocol':bulk.process_analysis.PROTOCOL,'model':os.environ.get('TTGL_TASK_MODEL','gpt-6-luna')}
        batch=dict(batch);ident=batch['id']
        counts={r['status']:r['n'] for r in c.execute('SELECT status,count(*) n FROM bulk_analysis_items WHERE batch_id=? GROUP BY status',(ident,))}
        rows=[dict(r) for r in c.execute('''SELECT i.task_id,t.title,i.status,i.job_id,i.error,j.usage,j.model FROM bulk_analysis_items i JOIN tasks t ON t.id=i.task_id
            LEFT JOIN task_history_jobs j ON j.id=i.job_id WHERE i.batch_id=? ORDER BY i.position''',(ident,))]
        coverage=c.execute('''SELECT coalesce(sum(json_array_length(i.snapshot,'$.steps')),0),
            coalesce(sum(CASE WHEN i.status IN ('completed','unchanged') THEN json_array_length(i.snapshot,'$.steps') ELSE 0 END),0),
            coalesce(sum(CASE WHEN j.created>=? THEN json_extract(j.usage,'$.total_tokens') END),0),
            coalesce(sum(j.created>=? AND j.usage IS NULL),0)
            FROM bulk_analysis_items i LEFT JOIN task_history_jobs j ON j.id=i.job_id WHERE i.batch_id=?''',(batch['created'],batch['created'],ident)).fetchone()
    for row in rows:row['usage']=json.loads(row['usage']) if row['usage'] else None
    total=sum(counts.values());finished=sum(counts.get(key,0) for key in bulk.TERMINAL)
    from record_collection import query_records
    columns={key:(lambda row,key=key:row.get(key),False) for key in ('title','status','error')}
    columns['tokens']=(lambda row:(row.get('usage') or {}).get('total_tokens'),True)
    rows,query=query_records(rows,columns,list_query);matched=len(rows)
    offset=min(offset,max(0,(matched-1)//limit)*limit);rows=rows[offset:offset+limit]
    return dict(batch=batch,counts=counts,total=total,finished=finished,records=rows,
                pagination=dict(total=matched,offset=offset,limit=limit,query=query,next_offset=offset+limit if offset+limit<matched else None),
                coverage=dict(frozen_events=coverage[0],interpreted_events=coverage[1],known_analysis_tokens=coverage[2],jobs_missing_usage=coverage[3]),
                limitations=['One finite frozen corpus snapshot; newly arriving activity is separate. No scheduled inference or automatic retries.',
                'Outcomes, categories and intervention labels are model interpretations of bounded visible evidence, not independent grades. Long tasks use chronological blocks and sampled I/O; coverage limits are retained.',
                'Source-task measured usage stays unchanged. Analysis overhead is separate; missing usage and actual cash expense remain unknown.'])
