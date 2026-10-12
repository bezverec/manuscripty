import path from 'node:path';
import {parseIssue,validateProposal,proposalType,VALIDATION_MARKER} from './proposals.mjs';
export default async function validateIssue({github,context,core,publicRoot=path.resolve('web/public')}) {
 const repo=context.repo,issue_number=context.payload.issue.number;
 const {data:issue}=await github.rest.issues.get({...repo,issue_number});
 const type=proposalType(issue);if(!type){core.info('Issue is not one correction proposal type.');return;}
 let problem=null;try{await validateProposal(parseIssue(issue.body,type),type,publicRoot);}catch(e){problem=String(e.message).slice(0,500).replaceAll('@','＠');}
 const comments=await github.paginate(github.rest.issues.listComments,{...repo,issue_number,per_page:100});
 const previous=comments.find(c=>c.user?.login==='github-actions[bot]'&&c.body?.includes(VALIDATION_MARKER));
 if(problem){
  const body=VALIDATION_MARKER+'\nNávrh zatím nelze propojit s publikovaným podkladem: '+problem+'\n\nOpravte pole formuláře nebo vložte celý export do pole proposal_json. Kontrola neposuzuje správnost čtení.';
  if(!previous)await github.rest.issues.createComment({...repo,issue_number,body});
  else if(previous.body!==body)await github.rest.issues.updateComment({...repo,comment_id:previous.id,body});
  if(!issue.labels.some(l=>(typeof l==='string'?l:l.name)==='needs-info'))await github.rest.issues.addLabels({...repo,issue_number,labels:['needs-info']});
 }else if(previous){
  const body=VALIDATION_MARKER+'\nIdentita návrhu odpovídá publikovanému podkladu. Správnost opravy stále čeká na odborné posouzení.';
  if(previous.body!==body)await github.rest.issues.updateComment({...repo,comment_id:previous.id,body});
  if(issue.labels.some(l=>(typeof l==='string'?l:l.name)==='needs-info'))await github.rest.issues.removeLabel({...repo,issue_number,name:'needs-info'});
 }
}
