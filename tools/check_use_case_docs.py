#!/usr/bin/env python3
"""Validate bilingual Data Relay Link v2.4 use-case navigation and links.

Run: python3 tools/check_use_case_docs.py
"""

from pathlib import Path
import re,json,sys
root=Path(__file__).resolve().parents[1]
nav=json.loads((root/'docs.json').read_text())
langs={z['language']:z for z in nav['navigation']['languages']}
assert set(langs)=={'en','ko'}
names=['index','remote-ssh','lan-relay','private-web','office-allowlist','fixed-tcp-database','ubuntu-updates','github-egress','ai-readonly','bulk-onboarding','configuration-bundle','backup-recovery']
pages=[*sorted((root/'use-cases').glob('*.mdx')),*sorted((root/'ko/use-cases').glob('*.mdx'))]
assert len(pages)==24, len(pages)
errors=[]
for lang in ['en','ko']:
    n=langs[lang]
    expected=[('ko/' if lang=='ko' else '')+'use-cases/'+name for name in names]
    groups=[g for g in n['groups'] if g['group'] in ['Practical Use Cases','실습: 활용 사례']]
    assert len(groups)==1 and groups[0]['pages']==expected,(lang,groups)
    for path in expected:
        assert (root/(path+'.mdx')).is_file(),path

all_nav=[]
for lang in langs.values():
    for group in lang['groups']:
        all_nav.extend(group['pages'])
for name in all_nav:
    if not (root/(name+'.mdx')).is_file() and not (root/(name+'.md')).is_file():
        errors.append('Navigation target missing: '+name)

linkrx=re.compile(r'\]\((/[^)#\s]+)(?:#[^)]+)?\)')
linkcount=0
for page in pages+[root/'index.mdx',root/'ko/index.mdx',root/'guides/internet-access.mdx',root/'ko/guides/internet-access.mdx']:
    t=page.read_text()
    if page in pages:
        if not t.startswith('---\n'): errors.append('Bad frontmatter start: '+str(page))
        fm=t.split('---\n',2)
        if len(fm)<3 or not re.search(r'^title: .+',fm[1],re.M) or not re.search(r'^description: .+',fm[1],re.M):
            errors.append('Bad frontmatter keys: '+str(page))
        if t.count('~~~')%2: errors.append('Odd code fence: '+str(page))
        if page.name!='index.mdx' and len(re.findall(r'^## (?:Step |[1-9]단계)',t,re.M))<4:
            errors.append('Insufficient stages: '+str(page))
    for link in linkrx.findall(t):
        linkcount+=1
        cand=root/link.lstrip('/')
        if cand.is_file() or (root/(link.lstrip('/')+'.mdx')).is_file() or (root/(link.lstrip('/')+'.md')).is_file():
            continue
        errors.append('Missing internal link '+str(page.relative_to(root))+' -> '+link)

# Policy regression: the three planes have different no-policy/disable semantics.
for lang in ['guides/internet-access.mdx','ko/guides/internet-access.mdx']:
    s=(root/lang).read_text()
    if 'WHITELIST' not in s or 'DENY ALL' not in s or 'BLACKLIST / WHITELIST and Enforcement' in s:
        errors.append('Misleading internet-access policy in '+lang)
for lang in ['index.mdx','ko/index.mdx']:
    s=(root/lang).read_text()
    if '/use-cases/index' not in s: errors.append('Homepage lacks scenarios '+lang)
for p in [str(x.relative_to(root)) for x in root.rglob('*.mdx')]:
    if 'show version' in (root/p).read_text():errors.append('Deprecated show version '+p)
for p in pages:
    txt=p.read_text()
    if any(x in txt for x in ['sudo frpctl','sudo frp-create-client','set egress-profile','allow all traffic']):
        errors.append('Legacy command found '+str(p))
    if 'v2.4.0 stable' in txt or 'v2.4.0 is stable' in txt:
        errors.append('Unqualified stable claim '+str(p))
# Verify that nested policy mutations are only enabled with whitelist.
for p in pages:
    t=p.read_text()
    for m in re.findall(r'(?m)^(?:set )?(?:internet-access|ai-access) .+mode (\w+)',t):
        if m!='whitelist':errors.append('Non-WHITELIST policy '+str(p)+':'+m)

if errors:
    print('FAILED VALIDATION:',len(errors))
    print('\n'.join(errors[:80]));sys.exit(2)
print('PASS',len(all_nav),'navigation page targets')
print('PASS',len(pages),'bilingual scenarios; 12 pages per language (11 workflows + landing)')
print('PASS',linkcount,'internal markdown links from scenario + modified landing and policy pages')
print('PASS','MDX frontmatter, code fences, >=4 stages, CLI version surface and fail-closed policy semantics')
