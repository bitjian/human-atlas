import type {Atlas,Concept} from './anatomy';
import {translate,displayName,type Lang} from './i18n';
type Tool={name:string;description:string;inputSchema:object;annotations:{readOnlyHint:boolean};execute:(input:unknown)=>unknown};
function record(input:unknown):Record<string,unknown>{if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Expected an object.');return input as Record<string,unknown>;}
export function atlasTools(atlas:Atlas,inspect:(concept:Concept)=>void,lang:Lang='en'):Tool[]{return [
 {name:'find_anatomy',description:translate(lang,'toolFindDescription'),inputSchema:{type:'object',properties:{query:{type:'string',minLength:1}},required:['query'],additionalProperties:false},annotations:{readOnlyHint:true},execute(input){const data=record(input);if(typeof data.query!=='string'||!data.query.trim())throw new Error(translate(lang,'toolErrorQuery'));const q=data.query.toLowerCase().trim();return atlas.concepts.filter(c=>c.name.toLowerCase().includes(q)||c.id.toLowerCase().includes(q)).slice(0,30).map(c=>({id:c.id,name:displayName(lang,c),pieces:c.elements.length}));}},
 {name:'inspect_anatomical_structure',description:translate(lang,'toolInspectDescription'),inputSchema:{type:'object',properties:{id:{type:'string'}},required:['id'],additionalProperties:false},annotations:{readOnlyHint:false},execute(input){const data=record(input);if(typeof data.id!=='string')throw new Error(translate(lang,'toolErrorId'));const concept=atlas.concepts.find(c=>c.id===data.id);if(!concept)throw new Error(translate(lang,'toolErrorMissing'));inspect(concept);return {id:concept.id,name:displayName(lang,concept),selectedPieces:concept.elements.length};}}
 ];}
export function registerAtlasTools(atlas:Atlas,inspect:(concept:Concept)=>void,lang:Lang='en'){
 const context=(document as Document&{modelContext?:{registerTool:(tool:Tool,options:{signal:AbortSignal})=>void|Promise<void>}}).modelContext;
 if(!context?.registerTool)return;const lifecycle=new AbortController();
 for(const tool of atlasTools(atlas,inspect,lang)){try{void Promise.resolve(context.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});}catch{/* Optional browser capability; the visible UI remains available. */}}
 return()=>lifecycle.abort();
}
