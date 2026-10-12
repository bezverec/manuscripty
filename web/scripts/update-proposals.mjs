import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {collectProposals} from './proposals.mjs';
export default async function updateProposals({github,context,core,publicRoot=path.resolve('web/public')}) {
 const repo=context.repo,{data:repository}=await github.rest.repos.get(repo);
 const base=repository.default_branch,branch='automation/open-proposals',file='web/public/proposals.json';
 const issues=await github.paginate(github.rest.issues.listForRepo,{...repo,state:'open',per_page:100});
 const index=await collectProposals(issues,publicRoot),content=JSON.stringify(index,null,2)+'\n';
 const {data:pulls}=await github.rest.pulls.list({...repo,state:'open',head:repo.owner+':'+branch,base});
 const previous=pulls[0],current=await fs.readFile(path.join(publicRoot,'proposals.json'),'utf8').catch(e=>{if(e.code==='ENOENT')return '';throw e;});
 // Only the index and its integrity manifest enter the tree. Issue content is never executed.
 if(content===current){
  if(previous)await github.rest.pulls.update({...repo,pull_number:previous.number,state:'closed'});
  core.info('The published index already matches open validated proposals.');return;
 }
 const {data:baseRef}=await github.rest.git.getRef({...repo,ref:'heads/'+base});
 const {data:baseCommit}=await github.rest.git.getCommit({...repo,commit_sha:baseRef.object.sha});
 const manifestPath='docs/web-source-manifest.json',manifest=JSON.parse(await fs.readFile(path.resolve(publicRoot,'../../',manifestPath),'utf8'));
 const entry=manifest.files.find(item=>item.path===file);if(!entry)throw Error('Missing proposals.json source manifest entry.');
 entry.bytes=Buffer.byteLength(content);entry.sha256=crypto.createHash('sha256').update(content).digest('hex');
 const treeFiles=[];for(const [target,text] of [[file,content],[manifestPath,JSON.stringify(manifest,null,2)+'\n']]){
  const {data:blob}=await github.rest.git.createBlob({...repo,content:text,encoding:'utf-8'});treeFiles.push({path:target,mode:'100644',type:'blob',sha:blob.sha});
 }
 const {data:tree}=await github.rest.git.createTree({...repo,base_tree:baseCommit.tree.sha,tree:treeFiles});
 let branchRef=null;try{branchRef=(await github.rest.git.getRef({...repo,ref:'heads/'+branch})).data;}catch(e){if(e.status!==404)throw e;}
 const ensurePullRequest=async()=>{if(!previous)await github.rest.pulls.create({...repo,head:branch,base,title:'Aktualizovat přehled otevřených návrhů oprav',body:'Aktualizuje proposals.json a jeho otisk ve frontendovém manifestu podle otevřených hlášení s ověřenou identitou původního podkladu. Výzkumné texty se nemění. Návrhy čekají na odborné posouzení.\n\nNasazení zůstává ruční; automatický deploy lze zvážit samostatně po schválení provozního postupu.'});};
 if(branchRef){
  const {data:old}=await github.rest.git.getCommit({...repo,commit_sha:branchRef.object.sha});
  if(old.tree.sha===tree.sha){core.info('Existing proposal branch is up to date.');await ensurePullRequest();return;}
 }
 const {data:commit}=await github.rest.git.createCommit({...repo,message:'Update open correction proposal index',tree:tree.sha,parents:[baseRef.object.sha]});
 if(branchRef)await github.rest.git.updateRef({...repo,ref:'heads/'+branch,sha:commit.sha,force:true});
 else await github.rest.git.createRef({...repo,ref:'refs/heads/'+branch,sha:commit.sha});
 await ensurePullRequest();
}
