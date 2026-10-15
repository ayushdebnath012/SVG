"""Strict shared patch interface; representation-specific syntax checks stay separate."""
import ast,json,re

def validate_sequence(code):
 tokens=code.split();allowed={'line':3,'arc':5,'circle':9,'add':18,'cut':18,'intersect':18};markers={'<curve_end>','<loop_end>','<face_end>','<sketch_end>','<extrude_end>'}
 if not tokens or tokens[-1]!='<extrude_end>':raise ValueError('Incomplete sequence')
 expect=None;curves=0;loops=0;faces=0;sketch=False;features=0
 for token in tokens:
  if expect:
   if token!=expect:raise ValueError('Missing command terminator')
   expect=None
   if token=='<curve_end>':curves+=1
   if token=='<extrude_end>':features+=1;sketch=False
   continue
  if token in markers:
   if token=='<loop_end>' and curves:loops+=1;curves=0
   elif token=='<face_end>' and loops:faces+=1;loops=0
   elif token=='<sketch_end>' and faces:sketch=True;faces=0
   else:raise ValueError('Invalid marker nesting')
  else:
   parts=token.split(',');cmd=parts[0]
   if cmd not in allowed or len(parts)!=allowed[cmd]:raise ValueError('Invalid command arity')
   if any(not re.fullmatch(r'-?\d+',x) for x in parts[1:]):raise ValueError('Nonintegral coordinate')
   nums=list(map(int,parts[1:]));coordinate=nums if cmd in ['line','arc','circle'] else nums[:5]+nums[14:]
   if any(not 0<=x<=63 for x in coordinate):raise ValueError('Out-of-range 6-bit coordinate')
   if cmd in ['add','cut','intersect']:
    if not sketch:raise ValueError('Extrusion without sketch')
    if any(x not in [-1,0,1] for x in nums[5:14]):raise ValueError('Invalid rotation entry')
    expect='<extrude_end>'
   else:
    if sketch:raise ValueError('Curve after completed sketch')
    expect='<curve_end>'
 if expect or curves or loops or faces or sketch or not features:raise ValueError('Incomplete construction')
 return True

def apply(code,patch,representation):
 if not isinstance(patch,dict) or set(patch)!={'edits'} or not isinstance(patch['edits'],list):raise ValueError('Expected edits object')
 lines=code.splitlines();out=[];cursor=0
 for e in patch['edits']:
  if not isinstance(e,dict) or set(e)!={'start','delete','insert'}:raise ValueError('Invalid operation keys')
  start,delete,insert=e['start'],e['delete'],e['insert']
  if type(start)!=int or type(delete)!=int or not isinstance(insert,list):raise ValueError('Invalid operation types')
  if start<cursor or delete<0 or start+delete>len(lines) or start>len(lines):raise ValueError('Invalid original coordinates')
  if any(not isinstance(s,str) or '\n' in s or '\r' in s for s in insert):raise ValueError('Invalid inserted line')
  out+=lines[cursor:start]+insert;cursor=start+delete
 out+=lines[cursor:];result='\n'.join(out)+'\n'
 if representation=='cadquery':ast.parse(result)
 elif representation=='cad-editor-sequence':validate_sequence(result)
 else:raise ValueError('Unsupported representation')
 return result

def target_match(code,target,representation):
 if representation=='cadquery':return ast.dump(ast.parse(code))==ast.dump(ast.parse(target))
 return ' '.join(code.split())==' '.join(target.split())
