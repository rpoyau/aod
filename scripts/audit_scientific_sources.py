"""Rendered-source and semantic bindings used by the candidate's own suite.

Static inclusion resolves literal inputs and primitive conditional branches.
The release gate additionally checks TeX recorder and aux output from an
actual bibliography-complete build. Files outside the include graph cannot
satisfy a canonical scientific obligation.
"""
from pathlib import Path
import argparse,csv,hashlib,json,re
from functools import lru_cache

MAIN_REQUIRED=('sections/02_specific_distinction.tex','sections/04_closure_phase_wave.tex',
 'sections/05_motif_field_folding.tex','sections/06_wave_state_relational_time.tex',
 'sections/07_stokes_sadar_harmonic_boundary.tex','appendices/A_type_symbol_registry.tex',
 'appendices/B_admitted_motif_registry.tex','appendices/C_short_proofs.tex')
MANUAL_REQUIRED=('manual/sections/00_scope.tex','manual/sections/00_native_closure_wave_temporal_fixtures.tex')
CANONICAL_EQUATIONS={
 'eq:cumulative-closure-counts':r'\mathrm{bip}^{\le}_i(k)=\max(N_i^C(k)-1,0)',
 'eq:closure-phase-window':r'\mathbf1_{\{u<k_0\le v\}}',
 'eq:crown-advance':r'\operatorname{Adv}_k(h_k^+)=x_{k+1}^0',
 'eq:null-axiom':r'x=\Null,\qquadx=x,\qquad\Null\equiv\infD.',
 'eq:closure-phase':r'\Delta\Phi(C)=1_C.',
 'eq:hinge-grammar':r'M_{\varepsilon,m}=\varepsilon\,0_H(0_D)^m(-\varepsilon)',
 'eq:atomic-h1':r'E(\Qfour)=\{(u,v):d_H(u,v)=1\}',
 'eq:hinge-reflection-involution':r'\iota^2=\mathrm{id}',
 'eq:field-organization':r'F_{B,\lambda}|_k=(B,\lambda,I_B(k),\{W^{\mathrm{id}}_{B,i}\}_{i\in I_B(k)})',
 'eq:motif-grammar':r'\mathrm{Dimonon}=2\,\mathrm{Monon}\ne\mathrm{Dion}',
 'eq:phase-unit-embedding':r'\iota_{\mathrm{ref}}(n1_C)=2nh',
 'eq:reflected-leg-bound':r'(n_{\rightarrow}+n_{\leftarrow})h\ge2h=\iota_{\mathrm{ref}}(1_C)',
 'eq:equal-leg-factorization':r'\delta\phi^{\rightarrow}=\delta\phi^{\leftarrow}=\delta\phi',
 'eq:rcd-coupling':r'\RCD_{ij}(B)=RD_B(C_{ij})\bowtie_B R^{\mathrm{asym}}_{ij}(B)',
 'eq:rcd-additive-realization':r'\operatorname{dur}_{+}(RD\bowtie(r_s)_s)=RD+\sum_s r_s',
 'eq:window-clipped-rho':r'\operatorname{Compat}_{\mathcal D}(\rho^D_{ij},|\omega|^{\mathcal D}_{ij})',
 'eq:cadence-ratio':r'\frac{\Delta\operatorname{bip}_i(\omega)}{\Delta\operatorname{bip}_j(\omega)}',
 'eq:flux-types':r'\phi^{\mathrm{AFC}}_{ij}=p_i^{\mathrm{mem}}P_{ij}-p_j^{\mathrm{mem}}P_{ji}',
 'eq:causal-update':r'S^W_{F,k+1}=\mathcal U^{\SADAR}_B(S^W_{\le k},S^\times_{\le k},\mathbf A_{F,\le k})',
 'eq:fourier-transform':r'\widehat v(\chi)=\frac1N\sum_{g\in G}v(g)\overline{\chi(g)}',
 'eq:fourier-convolution-product':r'\widehat{v*w}(\chi)=N\widehat v(\chi)\widehat w(\chi)',
 'eq:fourier-parseval':r'\frac1N\sum_g|v(g)|^2=\sum_\chi|\widehat v(\chi)|^2',
 'eq:fourier-recurrence-support':r'\operatorname{supp}\widehat v\subseteq H^\perp',
}
REQUIRED_LABELS=('eq:first-anchor','eq:closure-certificate','eq:closure-trace','eq:return-identity',
 'eq:beat-reclosure','eq:wave-identity','eq:motif-admission','eq:fold-outer-closure','eq:expose-inner-lineage',
 'eq:complete-wave-state','eq:wave-update-trace','eq:coupling-trace','eq:relational-time',
 'eq:afc-stokes-used','eq:branch-hinge-rd','eq:frg-admission-order','eq:frg-identity',
 'eq:fourier-inversion','eq:fourier-orthogonality','eq:fourier-linearity',
 'eq:fourier-shift-modulation','eq:fourier-correlation-power','eq:fourier-real-symmetry',
 'eq:fourier-running-standing','eq:fourier-product-factorization')

def clean(text):
    return re.sub(r'(?<!\\)%[^\n]*','',text)


def visible(text):
    text=clean(text);stack=[True];result=[];pos=0
    for m in re.finditer(r'\\(iftrue|iffalse|else|fi)\b',text):
        if all(stack):result.append(text[pos:m.start()])
        token=m[1]
        if token.startswith('if'):stack.append(token=='iftrue')
        elif token=='else':
            if len(stack)==1:raise ValueError('unbound TeX else')
            stack[-1]=not stack[-1]
        else:
            if len(stack)==1:raise ValueError('unbound TeX fi')
            stack.pop()
        pos=m.end()
    if all(stack):result.append(text[pos:])
    if len(stack)!=1:raise ValueError('unclosed TeX conditional')
    return ''.join(result)


def include_graph(root,surface='main'):
    root=Path(root).resolve();cwd=root if surface=='main' else root/'manual'
    seen=[];stack=[];pieces=[]
    def visit(p):
        p=p.resolve()
        if p in stack:raise ValueError('recursive TeX include')
        if not p.is_relative_to(root):raise ValueError('include outside source tree')
        if not p.exists():raise ValueError('missing include '+str(p))
        stack.append(p);seen.append(p.relative_to(root).as_posix())
        txt=visible(p.read_text());pieces.append((p.relative_to(root).as_posix(),txt))
        for match in re.finditer(r'\\(?:input|include)\s*\{([^}]+)\}',txt):
            arg=match[1]
            if any(s in arg for s in ('#','\\')):raise ValueError('ACTUAL_BUILD_VERIFICATION_REQUIRED: dynamic include')
            child=cwd/arg
            if not child.suffix:child=child.with_suffix('.tex')
            visit(child)
        stack.pop()
    visit(cwd/'main.tex')
    return seen,pieces


def label_map(root,surface='main'):
    files,pieces=include_graph(root,surface);result={}
    for path,text in pieces:
        for m in re.finditer(r'\\label\{([^}]+)\}',text):
            if m[1] in result:raise ValueError('duplicate active label '+m[1])
            result[m[1]]={'path':path,'position':m.start()}
    return result


def equations(root,surface='main'):
    result={}
    for path,text in include_graph(root,surface)[1]:
        for m in re.finditer(r'\\begin\{(?:equation|align|gather)\}.*?\\end\{(?:equation|align|gather)\}',text,re.S):
            for lab in re.findall(r'\\label\{([^}]+)\}',m.group()):result[lab]=m.group()
    return result


def normalize_math(t):
    return re.sub(r'\s+','',t)


def audit(root):
    root=Path(root);mfiles,mparts=include_graph(root);ufiles,uparts=include_graph(root,'manual')
    require=lambda ok,msg: None if ok else (_ for _ in ()).throw(ValueError(msg))
    for p in MAIN_REQUIRED:require(p in mfiles,'canonical Main source not rendered: '+p)
    for p in MANUAL_REQUIRED:require(p in ufiles,'canonical Manual fixture not rendered: '+p)
    require(ufiles.index(MANUAL_REQUIRED[0])<ufiles.index(MANUAL_REQUIRED[1])<ufiles.index('manual/sections/00_dec_ledger.tex'),'Manual dependency order')
    labs=label_map(root);ulabs=label_map(root,'manual');eqs=equations(root)
    for lab in REQUIRED_LABELS:require(lab in labs,'missing canonical label '+lab)
    for lab,formula in CANONICAL_EQUATIONS.items():
        require(lab in eqs,'required equation absent from rendered graph: '+lab)
        require(normalize_math(formula) in normalize_math(eqs[lab]),'canonical equation content changed: '+lab)
    # The scope organization consumes an already defined wave identity.
    require(mfiles.index(labs['eq:wave-identity']['path'])<mfiles.index(labs['eq:field-organization']['path']),'wave identity must precede field')
    cf=labs['eq:cycle-valued-field-compression'];rd=labs['eq:cycle-rd-accessor']
    require(cf['path']==rd['path'] and cf['position']<rd['position'],'cycle object must precede scalar accessor')
    refs=[]
    for path,text in uparts:
        for lab in re.findall(r'(?<![\w:])main:((?:eq|sec|subsec|app|fig|tab):[A-Za-z0-9:_-]+)',text):
            require(lab in labs,'unresolved literal Main provenance: '+lab+' in '+path);refs.append((path,lab))
    for surf,parts,mapping in [('main',mparts,labs),('manual',uparts,ulabs)]:
        for path,text in parts:
            for lab in re.findall(r'\\(?:ref|eqref|eqnref|secref|appref|figref|tabref)\{([^}]+)\}',text):
                if '#' not in lab:require(lab in mapping,'unresolved '+surf+' reference '+lab+' in '+path)
    for p in root.rglob('*.tex'):
        text=clean(p.read_text())
        require(not re.search(r'F\s*(?:_\{[^}]+\})?\s*=\s*C\^\{\\mathrm\{ret\}',text),'parallel field-first definition '+str(p))
        require('2\\Delta\\mathrm{phase}\\ge1' not in normalize_math(text),'retained preclosure selector')
    return {'main_files':mfiles,'manual_files':ufiles,'main_labels':len(labs),'manual_labels':len(ulabs),'literal_provenance':len(refs),'equation_contracts':len(CANONICAL_EQUATIONS)}


def actual_build(root,build_root,surface):
    root=Path(root).resolve();b=Path(build_root).resolve();cwd=b if surface=='main' else b/'manual'
    fls=cwd/'main.fls';aux=cwd/'main.aux';log=cwd/'main.log'
    if not all(p.exists() for p in (fls,aux,log)):raise ValueError('missing actual build evidence')
    if re.search(r'undefined references|multiply defined|Citation .* undefined|^!|Missing character:',log.read_text(),re.M):raise ValueError('publication has unresolved source/reference/font errors')
    recorded=[]
    for line in fls.read_text().splitlines():
        if line.startswith('INPUT '):
            p=Path(line[6:]);p=p if p.is_absolute() else cwd/p
            p=p.resolve()
            if p.is_relative_to(b) and p.is_file():recorded.append(p.relative_to(b).as_posix())
    for f in include_graph(root,surface)[0]:
        if f not in recorded:raise ValueError('static include absent from actual TeX execution '+f)
        if hashlib.sha256((root/f).read_bytes()).digest()!=hashlib.sha256((b/f).read_bytes()).digest():raise ValueError('build source mismatch '+f)
    actual_labels=set(re.findall(r'\\newlabel\{([^}]+)\}',aux.read_text()))
    for lab in label_map(root,surface):
        if lab not in actual_labels:raise ValueError('source label absent from actual aux '+lab)
    return {'surface':surface,'recorded_source_files':sorted(set(recorded)),'actual_labels':len(actual_labels),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}


def audit_conservation(rows,expected_bindings,root):
    """Bind each reviewed source item to its precise construction destination.

    expected_bindings is the reviewed source-to-construct map, not a caller's
    edited inventory. Hash/reference existence alone never supplies this check.
    """
    indexes={s:label_map(root,s) for s in ('main','manual')};seen=set()
    for row in rows:
        sid=row['source_id']
        if sid in seen:raise ValueError('duplicate conservation source '+sid)
        seen.add(sid)
        if sid not in expected_bindings:raise ValueError('unreviewed source item '+sid)
        wanted=expected_bindings[sid]
        if row['source_content_sha256']!=wanted['source_content_sha256']:raise ValueError('source content binding changed '+sid)
        destinations=json.loads(row['destinations_json'])
        if destinations!=wanted['destinations']:raise ValueError('source mapped to unrelated scientific construction '+sid)
        for d in destinations:
            if indexes[d['surface']].get(d['label'],{}).get('path')!=d['path']:raise ValueError('inactive conservation destination '+sid)
        if row['proof_correspondence']!=wanted['proof_correspondence']:raise ValueError('changed premise correspondence '+sid)
        for key in ('disposition','correction_id'):
            if key in wanted and row.get(key)!=wanted[key]:raise ValueError('changed conservation disposition '+sid)
        if wanted.get('destination_content_sha256'):
            for d,expected in zip(destinations,wanted['destination_content_sha256']):
                actual=hashlib.sha256(scientific_unit(root,d['path'],d['label']).encode()).hexdigest()
                if actual!=expected:raise ValueError('reviewed scientific content changed '+sid+' at '+d['label'])
    if seen!=set(expected_bindings):raise ValueError('undisposed scientific source items')
    return len(seen)


@lru_cache(maxsize=None)
def scientific_unit(root,path,label):
    text=visible((Path(root)/path).read_text());pos=text.index('\\label{'+label+'}')
    block=re.compile(r'\\\[.*?\\\]|\\begin\{(equation\*?|align\*?|gather\*?|figure\*?|table\*?|longtable|definition|theorem|proposition|lemma|proof)\}.*?\\end\{\1\}',re.S)
    blocks=[m for m in block.finditer(text) if m.start()<=pos<m.end()]
    if blocks:return min(blocks,key=lambda m:m.end()-m.start()).group()
    headings=list(re.finditer(r'\\(section|subsection|subsubsection|paragraph)\*?(?:\[[^]]*\])?\{',text))
    before=[m for m in headings if m.start()<=pos];selected=before[-1] if before else None
    levels={'section':1,'subsection':2,'subsubsection':3,'paragraph':4}
    start=selected.start() if selected else max(0,text.rfind('\n\n',0,pos))
    level=levels[selected[1]] if selected else 4
    end=min((m.start() for m in headings if m.start()>pos and levels[m[1]]<=level),default=len(text))
    return text[start:end].strip()


def fixture_conservation(destination='eq:closure-phase',root=None):
    root=Path(root) if root else Path(__file__).resolve().parents[1]
    audit(root)
    expected={'source:one-phase':{'source_content_sha256':'declared-one-phase-source',
        'destinations':[{'surface':'main','path':'sections/04_closure_phase_wave.tex','label':'eq:closure-phase'}],
        'proof_correspondence':'one certified closure contributes one phase'}}
    row={'source_id':'source:one-phase','source_content_sha256':'declared-one-phase-source',
         'destinations_json':json.dumps([dict(expected['source:one-phase']['destinations'][0],label=destination,
            path=label_map(root)[destination]['path'])]),
         'proof_correspondence':expected['source:one-phase']['proof_correspondence']}
    return {'rendered':True,'canonical_bindings':audit_conservation([row],expected,root)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--build-root');p.add_argument('--conservation');p.add_argument('--reviewed-bindings');a=p.parse_args()
    result=audit(a.root)
    if a.build_root:result['actual_build']=[actual_build(a.root,a.build_root,s) for s in ('main','manual')]
    if a.conservation:
        if not a.reviewed_bindings:raise ValueError('reviewed semantic bindings required')
        with open(a.conservation,newline='') as f:rows=list(csv.DictReader(f))
        binding=json.loads(Path(a.reviewed_bindings).read_text())
        result['conserved_source_items']=audit_conservation(rows,binding['bindings'],a.root)
    print(json.dumps(result,indent=2))
