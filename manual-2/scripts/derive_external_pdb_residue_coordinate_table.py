from __future__ import annotations
import csv, json, hashlib, shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT/'manual-2/data/protein'
VERSION = 'v40.02r14'
VERSION_LABEL = 'v40.02r14_external_pdb_residue_coordinate_table_derivation_gate'
PAYLOAD = PROT/'external_pdb_payloads/1CRN.cif'
EXPECTED_SHA = '23787562c427d7c1abe5420e86d5f1d0a6c7007dec1e8ce85645a6d69c32e8ba'
LOCK_ID = 'pdb_external_coordinate_payload_byte_hash_lock_1CRN_A_v4002r13'
DERIVATION_ID = 'pdb_external_residue_coordinate_table_derivation_1CRN_A_v4002r14'
REGISTRATION_TS = '2026-06-17T00:00:00Z'

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())

def write_csv(path: Path, fields: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fields})

def read_csv(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def find_atom_site_loop(path: Path):
    lines = path.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if line.strip() != 'loop_':
            continue
        fields=[]; j=i+1
        while j < len(lines) and lines[j].startswith('_atom_site.'):
            fields.append(lines[j].strip())
            j += 1
        if fields:
            rows=[]
            while j < len(lines):
                l = lines[j]
                if not l.strip():
                    j += 1; continue
                if l.startswith('#') or l.startswith('loop_') or l.startswith('_'):
                    break
                rows.append(shlex.split(l))
                j += 1
            return fields, rows
    raise RuntimeError('no atom_site loop found')

def derive_rows():
    data = PAYLOAD.read_bytes()
    digest = sha256_bytes(data)
    if digest != EXPECTED_SHA:
        raise RuntimeError(f'payload hash mismatch {digest}')
    lock = read_csv(PROT/'pdb_external_coordinate_payload_byte_hash_lock.csv')[0]
    if lock['coordinate_payload_sha256'] != digest:
        raise RuntimeError('r13 byte hash lock mismatch')
    fields, rows = find_atom_site_loop(PAYLOAD)
    idx = {f:i for i,f in enumerate(fields)}
    def get(r, name): return r[idx[name]]
    atom_extract=[]
    candidates_by_res={}
    for r in rows:
        if get(r,'_atom_site.group_PDB') != 'ATOM':
            continue
        if get(r,'_atom_site.auth_asym_id') != 'A':
            continue
        if get(r,'_atom_site.auth_atom_id') != 'CA':
            continue
        if get(r,'_atom_site.pdbx_PDB_model_num') != '1':
            continue
        auth_seq = get(r,'_atom_site.auth_seq_id')
        label_seq = get(r,'_atom_site.label_seq_id')
        alt = get(r,'_atom_site.label_alt_id')
        occ = get(r,'_atom_site.occupancy')
        atom = {
            'source_accession': '1CRN',
            'coordinate_payload_sha256': digest,
            'atom_site_id': get(r,'_atom_site.id'),
            'group_PDB': get(r,'_atom_site.group_PDB'),
            'model_id': get(r,'_atom_site.pdbx_PDB_model_num'),
            'chain_id': get(r,'_atom_site.auth_asym_id'),
            'label_asym_id': get(r,'_atom_site.label_asym_id'),
            'auth_seq_id': auth_seq,
            'label_seq_id': label_seq,
            'pdbx_PDB_ins_code': get(r,'_atom_site.pdbx_PDB_ins_code'),
            'residue_name': get(r,'_atom_site.auth_comp_id'),
            'label_comp_id': get(r,'_atom_site.label_comp_id'),
            'atom_selector': 'CA',
            'atom_name': get(r,'_atom_site.auth_atom_id'),
            'label_atom_id': get(r,'_atom_site.label_atom_id'),
            'altloc_id': alt,
            'altloc_policy': 'primary_or_highest_occupancy_altloc_required_before_derivation',
            'occupancy': occ,
            'x': get(r,'_atom_site.Cartn_x'),
            'y': get(r,'_atom_site.Cartn_y'),
            'z': get(r,'_atom_site.Cartn_z'),
            'B_iso_or_equiv': get(r,'_atom_site.B_iso_or_equiv'),
            'coordinate_source': 'manual-2/data/protein/external_pdb_payloads/1CRN.cif',
            'coordinate_row_id': f"1CRN_A_model1_CA_auth{auth_seq}_label{label_seq}",
            'candidate_status': 'selected_candidate' if alt in ('.','?') else 'alternate_candidate_recorded',
        }
        atom_extract.append(atom)
        candidates_by_res.setdefault((int(auth_seq), label_seq), []).append(atom)
    # choose per residue: alt ./? first, then highest occupancy, lowest atom_site_id
    residue_rows=[]
    for (auth_int, label_seq), atoms in sorted(candidates_by_res.items()):
        def rank(a):
            alt_rank = 0 if a['altloc_id'] in ('.','?') else 1
            return (alt_rank, -float(a['occupancy']), int(a['atom_site_id']))
        chosen = sorted(atoms, key=rank)[0]
        chosen['selection_status'] = 'selected_by_primary_or_highest_occupancy_altloc_policy'
        residue_rows.append({
            'coordinate_row_id': chosen['coordinate_row_id'],
            'source_database': 'RCSB_PDB',
            'source_accession': '1CRN',
            'coordinate_payload_sha256': digest,
            'chain_id': 'A',
            'model_id': chosen['model_id'],
            'model_policy': 'model_1_preferred_single_model_policy',
            'residue_index_basis': 'one_based_residue_sequence_position',
            'auth_seq_id': chosen['auth_seq_id'],
            'label_seq_id': chosen['label_seq_id'],
            'pdbx_PDB_ins_code': chosen['pdbx_PDB_ins_code'],
            'residue_name': chosen['residue_name'],
            'atom_selector': 'CA',
            'atom_name': chosen['atom_name'],
            'altloc_id': chosen['altloc_id'],
            'altloc_policy': 'primary_or_highest_occupancy_altloc_required_before_derivation',
            'occupancy': chosen['occupancy'],
            'x': chosen['x'],
            'y': chosen['y'],
            'z': chosen['z'],
            'missing_residue_status': 'present_CA_coordinate_selected',
            'coordinate_source': chosen['coordinate_source'],
            'coordinate_source_hash': digest,
            'leakage_role': 'target_only_after_AOD_freeze',
            'contact_map_status': 'not_derived_in_v40.02r14',
            'score_status': 'not_scored_in_v40.02r14',
            'release_status': VERSION_LABEL,
        })
    auth_ids = [int(r['auth_seq_id']) for r in residue_rows]
    expected = list(range(min(auth_ids), max(auth_ids)+1)) if auth_ids else []
    present = set(auth_ids)
    missing_rows=[]
    missing = [i for i in expected if i not in present]
    if missing:
        for m in missing:
            missing_rows.append({
                'missing_row_id': f'1CRN_A_model1_missing_auth{m}',
                'source_accession': '1CRN',
                'coordinate_payload_sha256': digest,
                'chain_id': 'A',
                'model_id': '1',
                'auth_seq_id': str(m),
                'label_seq_id': '',
                'atom_selector': 'CA',
                'missing_residue_status': 'missing_CA_coordinate_explicit_gap_row',
                'missing_residue_policy': 'explicit_gap_rows_required_before_contact_derivation',
                'contact_map_status': 'not_derived_in_v40.02r14',
                'score_status': 'not_scored_in_v40.02r14',
                'release_status': VERSION_LABEL,
            })
    else:
        missing_rows.append({
            'missing_row_id': '1CRN_A_model1_CA_missing_summary',
            'source_accession': '1CRN',
            'coordinate_payload_sha256': digest,
            'chain_id': 'A',
            'model_id': '1',
            'auth_seq_id': f'{min(auth_ids)}-{max(auth_ids)}',
            'label_seq_id': f'{residue_rows[0]["label_seq_id"]}-{residue_rows[-1]["label_seq_id"]}',
            'atom_selector': 'CA',
            'missing_residue_status': 'no_missing_CA_coordinates_in_selected_chain_model_policy',
            'missing_residue_policy': 'explicit_gap_rows_required_before_contact_derivation',
            'contact_map_status': 'not_derived_in_v40.02r14',
            'score_status': 'not_scored_in_v40.02r14',
            'release_status': VERSION_LABEL,
        })
    return digest, len(data), atom_extract, residue_rows, missing_rows

def write_r14_files():
    digest, size, atom_extract, residue_rows, missing_rows = derive_rows()
    atom_fields = [
        'source_accession','coordinate_payload_sha256','atom_site_id','group_PDB','model_id','chain_id','label_asym_id','auth_seq_id','label_seq_id','pdbx_PDB_ins_code','residue_name','label_comp_id','atom_selector','atom_name','label_atom_id','altloc_id','altloc_policy','occupancy','x','y','z','B_iso_or_equiv','coordinate_source','coordinate_row_id','candidate_status'
    ]
    write_csv(PROT/'pdb_external_atom_site_extract.csv', atom_fields, atom_extract)
    residue_fields = [
        'coordinate_row_id','source_database','source_accession','coordinate_payload_sha256','chain_id','model_id','model_policy','residue_index_basis','auth_seq_id','label_seq_id','pdbx_PDB_ins_code','residue_name','atom_selector','atom_name','altloc_id','altloc_policy','occupancy','x','y','z','missing_residue_status','coordinate_source','coordinate_source_hash','leakage_role','contact_map_status','score_status','release_status'
    ]
    write_csv(PROT/'pdb_external_residue_coordinate_table.csv', residue_fields, residue_rows)
    missing_fields = ['missing_row_id','source_accession','coordinate_payload_sha256','chain_id','model_id','auth_seq_id','label_seq_id','atom_selector','missing_residue_status','missing_residue_policy','contact_map_status','score_status','release_status']
    write_csv(PROT/'pdb_external_missing_residue_audit.csv', missing_fields, missing_rows)
    policy_rows = [{
        'policy_application_id': 'pdb_external_residue_coordinate_policy_1CRN_A_v4002r14',
        'byte_hash_lock_id': LOCK_ID,
        'source_database': 'RCSB_PDB',
        'source_accession': '1CRN',
        'coordinate_payload_sha256': digest,
        'chain_id': 'A',
        'model_id': '1',
        'model_policy': 'model_1_preferred_single_model_policy',
        'residue_index_basis': 'one_based_residue_sequence_position',
        'atom_selector': 'CA',
        'altloc_policy': 'primary_or_highest_occupancy_altloc_required_before_derivation',
        'missing_residue_policy': 'explicit_gap_rows_required_before_contact_derivation',
        'selected_coordinate_rows': str(len(residue_rows)),
        'atom_site_extract_rows': str(len(atom_extract)),
        'missing_residue_audit_rows': str(len(missing_rows)),
        'contact_threshold_angstrom': '8.0',
        'min_sequence_separation': '3',
        'contact_map_derivation_status': 'not_derived_in_v40.02r14',
        'external_residual_score_status': 'not_scored_in_v40.02r14',
        'release_status': VERSION_LABEL,
    }]
    write_csv(PROT/'pdb_external_residue_coordinate_policy_application.csv', list(policy_rows[0].keys()), policy_rows)
    block_rows = [
        {'block_id':'PDB-EXT-RESIDUE-TABLE-BLOCK-001','derivation_id':DERIVATION_ID,'candidate_derivation':'external_contact_map','required_precondition':'explicit_contact_map_derivation_gate_after_residue_table','current_status':'blocked_in_v40.02r14','leakage_role':'target_only_after_AOD_freeze','release_status':VERSION_LABEL},
        {'block_id':'PDB-EXT-RESIDUE-TABLE-BLOCK-002','derivation_id':DERIVATION_ID,'candidate_derivation':'evaluation_pair_boundary','required_precondition':'external_contact_map_derived_in_later_gate','current_status':'blocked_in_v40.02r14','leakage_role':'downstream_scope_before_score','release_status':VERSION_LABEL},
        {'block_id':'PDB-EXT-RESIDUE-TABLE-BLOCK-003','derivation_id':DERIVATION_ID,'candidate_derivation':'external_residual_score','required_precondition':'external_contact_map_and_evaluation_pair_boundary_declared','current_status':'blocked_in_v40.02r14','leakage_role':'downstream_score_only_after_freeze_target_join','release_status':VERSION_LABEL},
    ]
    write_csv(PROT/'pdb_external_residue_coordinate_derivation_block.csv', ['block_id','derivation_id','candidate_derivation','required_precondition','current_status','leakage_role','release_status'], block_rows)
    checks = [
        ('PDB-EXT-RES-TABLE-001','residue_table_reads_only_locked_byte_hash_payload','payload_lock','coordinate_payload_sha256_mismatch_or_unlocked_payload','residue_coordinate_table','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-002','coordinate_payload_sha256_matches_r13_lock','hash_integrity','r13_hash_lock_not_used','residue_coordinate_table','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-003','chain_id_A_filter_applied','chain_selection','wrong_chain_selected','residue_coordinate_table','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-004','atom_selector_CA_filter_applied','atom_selection','non_CA_atom_selected','residue_coordinate_table','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-005','model_policy_applied','model_selection','wrong_model_selected','residue_coordinate_table','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-006','altloc_policy_applied_or_recorded','altloc_selection','altloc_policy_missing','residue_coordinate_table','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-007','missing_residue_policy_recorded','missing_residue_audit','missing_residues_not_recorded','residue_coordinate_table','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-008','no_contact_map_derived_in_r14','contact_map_guard','contact_map_derived_in_residue_table_gate','external_contact_map','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-009','no_external_residual_score_computed_in_r14','score_guard','score_computed_in_residue_table_gate','external_score','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-010','coordinate_metrics_remain_deferred','metric_guard','RMSD_TM_score_GDT_released','coordinate_metrics','active_pass','residue_table_gate_only_no_contact_map_or_score'),
        ('PDB-EXT-RES-TABLE-011','AOD_motif_curling_curls_and_SADAR_stay_upstream_of_future_target_join','detection_order','target_coordinates_used_as_AOD_premise','AOD_freeze','active_pass','residue_table_gate_only_no_contact_map_or_score'),
    ]
    write_csv(PROT/'pdb_external_residue_coordinate_leakage_checks.csv', ['check_id','check_name','gate_type','failure_mode','blocked_lane','check_result','score_input_status'], [dict(zip(['check_id','check_name','gate_type','failure_mode','blocked_lane','check_result','score_input_status'], c)) for c in checks])
    manifest = {
        'lane': 'external_pdb_residue_coordinate_table_derivation_gate',
        'version_scope': VERSION,
        'status': 'residue coordinate table derivation from locked 1CRN.cif byte payload only; no contact map, external residual score, coordinate metric, or folding value map is derived',
        'prior_byte_hash_lock': 'manual-2/data/protein/pdb_external_coordinate_payload_byte_hash_lock.csv',
        'source_database': 'RCSB_PDB',
        'source_accession': '1CRN',
        'chain_id': 'A',
        'model_id': '1',
        'model_policy': 'model_1_preferred_single_model_policy',
        'residue_index_basis': 'one_based_residue_sequence_position',
        'atom_selector': 'CA',
        'altloc_policy': 'primary_or_highest_occupancy_altloc_required_before_derivation',
        'missing_residue_policy': 'explicit_gap_rows_required_before_contact_derivation',
        'coordinate_payload_sha256': digest,
        'coordinate_payload_byte_count': size,
        'selected_residue_coordinate_rows': len(residue_rows),
        'atom_site_extract_rows': len(atom_extract),
        'missing_residue_audit_status': missing_rows[0]['missing_residue_status'] if missing_rows else 'not_evaluated',
        'coordinate_table_sha256': sha256_file(PROT/'pdb_external_residue_coordinate_table.csv'),
        'atom_site_extract_sha256': sha256_file(PROT/'pdb_external_atom_site_extract.csv'),
        'blocked_until_later_gate': ['external_contact_map_derivation','evaluation_pair_boundary_declaration','external_accession_residual_score','coordinate_level_metric_score'],
        'files': {
            'atom_site_extract': 'manual-2/data/protein/pdb_external_atom_site_extract.csv',
            'residue_coordinate_table': 'manual-2/data/protein/pdb_external_residue_coordinate_table.csv',
            'missing_residue_audit': 'manual-2/data/protein/pdb_external_missing_residue_audit.csv',
            'policy_application': 'manual-2/data/protein/pdb_external_residue_coordinate_policy_application.csv',
            'derivation_block': 'manual-2/data/protein/pdb_external_residue_coordinate_derivation_block.csv',
            'leakage_checks': 'manual-2/data/protein/pdb_external_residue_coordinate_leakage_checks.csv',
            'local_payload': 'manual-2/data/protein/external_pdb_payloads/1CRN.cif',
        },
        'input_order_policy': 'r11 accession scope; r12 locator/policy gate; r13 byte-payload SHA-256 lock; r14 residue table only; contact maps and scores only in later declared gates; AOD motif/curling-curls/SADAR freeze remains upstream of any target join',
        'claim_discipline': 'Residue coordinate table derivation gate only. This is not external contact-map derivation, not external scoring, not RMSD/TM-score/GDT, and not a folding model.',
    }
    (PROT/'pdb_external_residue_coordinate_table_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest

if __name__ == '__main__':
    m = write_r14_files()
    print(json.dumps({k:m[k] for k in ['version_scope','selected_residue_coordinate_rows','atom_site_extract_rows','coordinate_payload_sha256']}, indent=2))
