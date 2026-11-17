import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { pg, closeDatabases, queryCh } from '../src/lib/database.ts';
import { migrate } from '../scripts/migrate.ts';
import { seedTest } from '../scripts/seed-test.ts';
import { experienceFixture } from '../src/lib/experience-fixture.ts';
import { registerStudy, publishEnvelope, createSnapshot } from '../src/lib/experience-publication.ts';
import { fingerprint, flushExperienceOutbox } from '../src/lib/experience-store.ts';
import { retainRaw } from '../src/lib/raw-store.ts';
import { searchExperience, readExperience } from '../src/lib/experience-retrieval.ts';
import { recordPlan, recordCheckpoint, recordAttempt, recordAttemptEvent, recordBarrier } from '../src/lib/experience-routing.ts';
import { experienceCollections } from '../src/lib/experience-views.ts';
import { recordData } from '../src/lib/analytics.ts';
import { exactFilter } from '../src/lib/record-query.ts';
if(process.env.OBS_TESTING!=='1' || !process.env.CLICKHOUSE_DATABASE?.endsWith('_test')) throw Error('Isolated test databases required');
const prefix='experience-'+randomUUID(),scope={projectId:'qa-project',experimentId:prefix};
const {source,envelope}=experienceFixture(prefix),db=pg();
const exclusions={taskIds:[],leakageGroups:[]},configurationHash=fingerprint({fixture:prefix});
const config={schemaVersion:1,mode:'frozen_memory',sourceCommit:'fixture-only',policyVersion:'fixture-policy',allowedArms:['HRM','LPM'],allowedSplits:['memory_build'],exclusionRegistryHash:fingerprint(exclusions),exclusions,repositoryCutoffs:[],maxSnapshotMembers:100,publicDependencyEventIds:[],embedding:null,retrieval:{taskPacketTokens:4000,subtaskPacketTokens:2500,candidatesPerGranularity:20,allowCandidates:true},modelExecution:{enabled:false,readinessHash:null,maximumInvocations:1,maximumTokens:100,maximumElapsedSeconds:60}};
before(async()=>{
 await migrate();await seedTest();await registerStudy(scope,config);
 await db`INSERT INTO tasks(id,project_id,title) VALUES(${source.taskId},'qa-project','Experience integration fixture')`;
 const versions:Record<string,number>={};
 for(const id of source.eventIds){const [v]=await db`INSERT INTO event_versions(id,payload_hash,event_time) VALUES(${id},'fixture','2026-11-17T00:00:00Z') RETURNING version`;versions[id]=Number(v.version);}
 const binding={codex_home:'/fixture/nonexistent',account_hash:'b'.repeat(64),auth_mode:'chatgpt'};
 const snapshot={turns:[],prompt_context:[],steps:[],subscription_binding:binding,coverage:source.coverage};
 const job=prefix+':base-job';
 await db`INSERT INTO analysis_jobs(id,task_id,operation,status,model,snapshot_hash,snapshot) VALUES(${job},${source.taskId},'fixture','completed','gpt-6-luna',${source.snapshotHash},${db.json(snapshot)})`;
 await db`INSERT INTO analyses(id,task_id,job_id,snapshot_hash,summary,result) VALUES(${source.analysisId},${source.taskId},${job},${source.snapshotHash},'Fixture only',${db.json({...source.analysis as object,source_versions:versions})})`;
 for(const [i,[id,eventIds]] of Object.entries(source.subtaskOwners).entries())await db`INSERT INTO subtasks(id,analysis_id,position,title,category,event_ids) VALUES(${id},${source.analysisId},${i},'Fixture','implement',${eventIds})`;
 const answer=await retainRaw(Buffer.from(JSON.stringify(envelope)),'experience-fixture',prefix);
 await db`INSERT INTO experience_jobs(project_id,experiment_id,id,analysis_id,snapshot_hash,configuration_hash,source_binding,input,invocation_id,status,measurement_origin,artifacts) VALUES(${scope.projectId},${scope.experimentId},${envelope.analysisRevisionId},${source.analysisId},${source.snapshotHash},${configurationHash},${db.json(binding)},'{}',${envelope.annotationInvocationId},'completed','fixture',${db.json({'answer.json':answer.id})})`;
});
after(closeDatabases);
function query(overrides:Record<string,unknown>={}){return {...scope,taskInstanceId:'new-public-task',workItemId:null,planRevisionId:null,phase:'user_task',goal:'cancellation',publicContextSummary:'',languages:['TypeScript'],frameworkConstraints:[],relevantPaths:[],relevantSymbols:[],requiredTools:['Bash'],acceptanceCriteria:[],errorSignature:null,repositoryStateHash:'c'.repeat(64),memorySnapshotId:prefix+':snapshot',availableBeforeSequence:0,retrievalPolicyVersion:'fixture-policy',arm:'HRM',sourceRepository:'fixture/repository',sourceBaseCommit:'fixture-base',excludedLeakageGroups:[],excludedTaskIds:[],mode:'frozen_memory',retrievalMode:'lexical',...overrides};}
test('publication preserves accepted v2 and retains exactly one immutable revision',async()=>{
 const a=await publishEnvelope(scope,envelope,configurationHash),b=await publishEnvelope(scope,envelope,configurationHash);assert.equal(a.id,b.id);assert.equal(b.status,'retained');
 await assert.rejects(db`UPDATE experience_versions SET admission='publicly_supported' WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId}`,/immutable/);
 await assert.rejects(publishEnvelope(scope,{...envelope,availableBeforeSequence:1},configurationHash),/retained model output/);
});
test('lexical retrieval, bounded reads and identical-query cache use a frozen snapshot',async()=>{
 await createSnapshot(scope,{id:prefix+':snapshot',arm:'HRM',watermark:0,versionIds:[fingerprint([prefix+':procedure',1])]});
 const a=await searchExperience(scope,query());assert.equal(a.packet.experiences.length,1);assert.equal(a.modelCalls,0);
 const b=await searchExperience(scope,query());assert.equal(b.cacheHit,true);
 const nodeHit=await searchExperience(scope,query({goal:'Add cancellation to document import parsing',phase:'plan_node'}));assert.equal(nodeHit.packet.experiences.length,1);
 assert.equal((await readExperience(scope,query(),[fingerprint([prefix+':procedure',1])])).experiences.length,1);
 const empty=await searchExperience(scope,query({goal:'zzzznonexistent'}));assert.equal(empty.packet.experiences.length,0);
});
test('future, wrong arm, same instance, lineage and repository chronology fail before ranking',async()=>{
 await assert.rejects(searchExperience(scope,query({availableBeforeSequence:1})),/watermark/);
 await assert.rejects(searchExperience(scope,query({arm:'LPM'})),/Wrong-arm/);
 for(const changes of [{taskInstanceId:source.taskId},{excludedLeakageGroups:[prefix+':family']},{sourceBaseCommit:'future-commit'},{languages:['Python']},{requiredTools:[]}]){
  const r=await searchExperience(scope,query(changes));assert.equal(r.packet.experiences.length,0);assert.ok(Object.keys(r.exclusions).length);
 }
 await assert.rejects(readExperience(scope,query({projectId:'another-project'}),[fingerprint([prefix+':procedure',1])]),/Invalid scoped/);
});
test('derived facts reconcile without duplicating native usage',async()=>{
 const before=await queryCh<{n:string}>('SELECT count() AS n FROM events FINAL');
 while(await flushExperienceOutbox()){}
 await flushExperienceOutbox();
 const facts=await queryCh<{n:string}>('SELECT count() AS n FROM experience_facts FINAL WHERE project_id={project:String} AND experiment_id={experiment:String} AND kind=\'experience\'',{project:scope.projectId,experiment:scope.experimentId});assert.equal(Number(facts[0].n),1);
 assert.deepEqual(await queryCh('SELECT count() AS n FROM events FINAL'),before);
});
test('experience tables support search, pagination, exact filters and every column sort',async()=>{
 const uiScope={project:'qa-project',workspace:'',range:'all',timezone:'UTC'},q={search:'',filters:{},sort:null,direction:1 as const,offset:0,limit:2},extra=new URLSearchParams({study:scope.experimentId});
 for(const kind of experienceCollections){
  const page=await recordData(kind,uiScope,q,extra);assert.ok(page.columns.length,kind);assert.ok(page.rows.length<=2);
  assert.equal((await recordData(kind,uiScope,{...q,search:'zzzznonexistent'},extra)).total,0);
  for(const c of page.columns){for(const direction of [1,-1] as const)await recordData(kind,uiScope,{...q,sort:c.key,direction},extra);
   if(!page.rows.length)continue;const first=page.rows[0],digest=(first.__filterDigests as Record<string,string>)[c.key];
   const yes=await recordData(kind,uiScope,{...q,filters:{[c.key]:exactFilter(first[c.key],false,digest)}},extra),no=await recordData(kind,uiScope,{...q,filters:{[c.key]:exactFilter(first[c.key],true,digest)}},extra);assert.equal(yes.total+no.total,page.total,kind+'.'+c.key);
  }
 }
});
test('concurrent attempt ownership, terminal immutability and publication barriers',async()=>{
 const planId=prefix+':plan',nodeId=prefix+':node',task='new-public-task';
 const node={nodeId,planRevisionId:planId,parentWorkItemId:task,goal:'Public fixture',dependsOn:[],preconditions:[],acceptanceCriteria:[{id:'criterion',description:'Public fixture check',publicCheck:null}],relevantPaths:[],relevantSymbols:[],allowedWritePaths:['source.ts'],expectedArtifacts:[],publicVerificationCommands:[],estimatedDifficulty:'routine',delegationSuitability:'bounded',supersedesNodeIds:[]};
 await recordPlan(scope,{planRevisionId:planId,taskInstanceId:task,previousRevisionId:null,nodes:[node],continuedNodeIds:[],cancelledNodeIds:[],contextHash:'d'.repeat(64),plannerInvocationId:'fixture-plan'});
 const cp={checkpointId:prefix+':checkpoint',taskInstanceId:task,planNodeId:nodeId,baseCommit:'base',repositoryStateHash:'a'.repeat(64),contractHash:fingerprint(node),environmentDigest:'fixture',sourceManifestHash:'b'.repeat(64),artifactArchiveId:'fixture',dependencyArtifactIds:[],toolConfigurationHash:'c'.repeat(64),visibleContextHash:'d'.repeat(64)};
 await recordCheckpoint(scope,cp);
 const base={taskInstanceId:task,planNodeId:nodeId,planRevisionId:planId,checkpointId:cp.checkpointId,executorId:'fixture-small',arm:'HRM',ordinal:0};
 const raced=await Promise.allSettled(['a','b'].map(id=>recordAttempt(scope,{...base,attemptId:prefix+':attempt-'+id})));
 assert.equal(raced.filter(r=>r.status==='fulfilled').length,1);
 const [owned]=await db`SELECT id FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='attempt'`;
 const fallback={...base,attemptId:prefix+':fallback',ordinal:1};
 await assert.rejects(recordAttempt(scope,fallback),/completed public failure/);
 const event={attemptId:owned.id,taskInstanceId:task,arm:'HRM',status:'public_failure',artifactId:'retained-fixture',verificationId:null,integrationId:null,trigger:'explicit_unresolved_requirement',artifactCheck:{passed:true,changed_paths:[],invalid_paths:[],repository_state_hash:'a'.repeat(64),includes_adds_deletes_modes_and_links:true},completionReport:null,usageInvocationId:'fixture'};
 await recordAttemptEvent(scope,event);await assert.rejects(recordAttemptEvent(scope,{...event,status:'uncertain'}),/immutable/);
 await recordAttempt(scope,fallback);
 await assert.rejects(recordBarrier(scope,{id:prefix+':bad-barrier',arm:'HRM',taskInstanceId:task,sequence:1,attemptIds:[owned.id]}),/every assignment/);
 await recordAttemptEvent(scope,{...event,attemptId:fallback.attemptId});
 await recordBarrier(scope,{id:prefix+':barrier',arm:'HRM',taskInstanceId:task,sequence:1,attemptIds:[owned.id,fallback.attemptId]});
 await assert.rejects(recordAttempt(scope,{...base,attemptId:prefix+':late-attempt',planNodeId:nodeId,ordinal:0}));
});
test('stale source versions invalidate retrieval and cached eligibility',async()=>{
 await db`UPDATE event_versions SET payload_hash='changed',version=DEFAULT WHERE id=${source.eventIds[0]}`;
 const result=await searchExperience(scope,query());assert.equal(result.packet.experiences.length,0);assert.equal(result.exclusions.stale_source,1);
 await assert.rejects(publishEnvelope(scope,envelope,configurationHash),/Stale source/);
});
