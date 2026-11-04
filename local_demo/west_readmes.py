"""Read Kim Greco's WEST template without adding data files or inferred fields."""
import re


def parse_west(text):
    sections={heading.strip().rstrip(':'):body.strip() for heading,body in re.findall(
        r'^## ([^\n]+)\n(.*?)(?=^## |\Z)',text,re.M|re.S)}
    description=re.search(r'^# Dataset Title:[^\n]+\n\s*\n(.*?)(?=^## )',text,re.M|re.S).group(1).strip()
    columns=[];group=None
    for line in sections['Data Dictionary'].splitlines():
        if re.match(r'# Individual patient files:',line): group='Individual patient files'
        elif re.match(r'# Patient summary file:',line): group='Patient summary file'
        else:
            match=re.match(r'# ([A-Za-z0-9_]+) - (.+)',line)
            if match and group:columns.append({'File':group,'Column':match[1],'Meaning':match[2]})
    metadata=sections['Metadata']
    code=re.search(r'^1\. Code: (.+)',metadata,re.M).group(1)
    raw=re.search(r'^2\. External [Dd]ata \(raw data\): (.+)',metadata,re.M).group(1)
    processed=re.search(r'^3\. Data \(processed / derived from code\):\s*(.*?)(?=^4\.)',metadata,re.M|re.S).group(1).strip()
    paper=re.search(r'https://www\.nature\.com/articles/[^\s]+',metadata).group(0)
    guide=re.search(r'^2\. Guide on how to use the dataset\?\s*(.*?)(?=^3\.|\Z)',sections['Key Questions'],re.M|re.S).group(1).strip()
    count=int(re.search(r'Patient Size:\s*(\d+)',sections['Demographic Information']).group(1))
    features=re.search(r'Features:\s*(.+)',sections['Summary Statistics']).group(1).strip()
    return {'description':description,'contact':sections['Contact'].strip(),'original_sections':sections,
            'columns':columns,'code':code,'raw_source':raw,'processed':processed,'paper':paper,
            'guide':guide,'patient_count':count,'features':features}


def west_blocks(entry,requested,query=''):
    data=entry['west'];blocks=[];sources=[]
    def block(title,section,text=None,items=None,table=None,links=None):
        blocks.append({'title':title,'text':text,'items':items or [],'kind':'bullets',
                       **({'table':table} if table else {}),**({'links':links} if links else {})})
        sources.append(section)
    if requested in {'overview','research','compare'}:
        block('Cohort','Dataset Title',text=data['description'])
        block('Summary','Demographic Information / Summary Statistics',
              items=[f"Patient size: {data['patient_count']:,}",f"Features: {data['features']}"])
    if requested in {'files','compare','samples'}:
        block('Files and contents','Metadata',text=data['processed'])
    if requested in {'columns','samples'}:
        groups=['Patient summary file','Individual patient files']
        if re.search(r'patient[ _-]?summary',query,re.I):groups=['Patient summary file']
        elif re.search(r'individual patient|patient-level files|patient sequence',query,re.I):groups=['Individual patient files']
        fields=[]
        if re.search(r'mean|defined?|definition|explain',query,re.I):
            fields=[c['Column'] for c in data['columns'] if re.search(r'\b'+re.escape(c['Column'])+r'\b',query,re.I)]
        for name in groups:
            rows=[{'Column':c['Column'],'Meaning':c['Meaning']} for c in data['columns'] if c['File']==name]
            if fields:rows=[r for r in rows if r['Column'] in fields]
            if rows:block(name,'Data Dictionary',table={'columns':['Column','Meaning'],'rows':rows})
    if requested=='start':block('How to start','Key Questions, Guide on how to use the dataset',text=data['guide'])
    if requested=='code':block('Processing code','Metadata',text=data['code'])
    if requested in {'location','access'}:
        block('Raw data source','Metadata',text=data['raw_source'])
        block('Contact','Contact',text=data['contact'])
    if requested=='statistics':
        block('Patient size','Demographic Information',text=f"{data['patient_count']:,}")
        block('Cohort','Dataset Title',text=data['description'])
    if requested=='limitations':
        rows=[line.removeprefix('- ').strip() for line in data['original_sections']['Key Questions'].splitlines() if line.startswith('- Limitation:')]
        block('Dataset description','Key Questions',items=rows)
    if requested in {'overview','research','code'}:
        block('Associated paper','Metadata',links=[{'label':'Read the associated paper','url':data['paper']}])
    return blocks,sources
