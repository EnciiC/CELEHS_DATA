"""Friendly guidance around retrieval, without inventing dataset information."""

import re


TOPICS = {
    'RA': ('rheumatoid arthritis (RA)', r'\bra\b|rheumatoid arthritis'),
    'MS': ('multiple sclerosis (MS)', r'\bms\b|multiple sclerosis'),
    'VINCI': ('VINCI heart failure', r'\bvinci\b'),
    'VA': ('VA/KDI', r'\bva\b|\bkdi\b'),
    'MIMIC': ('MIMIC', r'\bmimic(?:-iv|-iii)?\b'),
}


def valid_topic(topic):
    if not isinstance(topic, str): return None
    if topic.startswith('query:'):
        return topic if re.fullmatch(r'[A-Za-z][A-Za-z0-9 ()_-]{0,68}', topic[6:]) else None
    parts = topic.split(':')
    return topic if parts[0] in TOPICS and (len(parts) == 1 or len(parts) == 2 and parts[1] in {'MGB','UPMC'}) else None


def mentioned_topic(query):
    q = query.lower()
    for key, (_, pattern) in TOPICS.items():
        if re.search(pattern, q):
            site = ':MGB' if re.search(r'\bmgb\b', q) else ':UPMC' if re.search(r'\bupmc\b', q) else ''
            return key + site
    return None


def topic_name(topic):
    if topic.startswith('query:'): return topic[6:]
    parts = topic.split(':')
    return TOPICS[parts[0]][0] + (' from ' + parts[1] if len(parts) > 1 else '')


def choices(previous=None, labels=None):
    previous = previous or []
    labels = labels or {}
    if previous:
        label = ' and '.join(labels[i] for i in previous)
        return [{'label':'Show monthly columns', 'query':f'Show {label} monthly columns'},
                {'label':'Show fake rows', 'query':f'Show sample rows for {label} monthly counts'},
                {'label':'Browse datasets', 'view':'browse'}]
    return [{'label':'Find IBD data', 'query':'Where can I find IBD data?'},
            {'label':'Explore AD data', 'query':'What AD data do we have?'},
            {'label':'Browse datasets', 'view':'browse'}]


def guide(kind, paragraphs, actions, previous=None, pending=None):
    return {'engine':'guide', 'model':None, 'intent':kind,
            'answer':'\n\n'.join(paragraphs), 'intro':paragraphs[0],
            'messages':paragraphs[1:], 'actions':actions, 'datasets':[], 'sources':[], 'warning':None,
            'context_dataset_ids':previous or [], 'pending_topic':pending}


def opening(query, previous, labels, pending=None, handle_pending=True):
    q = query.lower().strip(' \t\n.!?,')
    pending = valid_topic(pending)
    if re.search(r'\bfake\b|\bsynthetic\b', q) and re.search(r'most effective|effectiveness|treatment effect|clinical conclusions?|causal effect|predict.*(?:disease|risk|outcome)|(?:infer|estimate|evaluate|determine).*(?:treatment|risk|association)', q):
        return guide('synthetic_limit', ['Fake rows cannot tell us which treatment is effective or support clinical conclusions.',
                     'These values were generated to show file structure. They do not preserve real treatment effects or clinical relationships.'],
                     [{'label':'Show fake IBD monthly rows','query':'Show sample rows for IBD monthly counts'},
                      {'label':'Browse documented datasets','view':'browse'}], previous, pending)
    greeting = r'(?:hi|hello|hey|greetings|good morning|good afternoon|good evening)(?: there)?(?: everyone)?'
    if re.fullmatch(greeting, q) or q in {'how are you', "how's it going"}:
        return guide('greeting', ['Hi! What would you like to explore—IBD, AD, or a research question?'], choices(previous, labels), previous, pending)
    if re.fullmatch(r'(?:thanks|thank you|thank you very much|thanks a lot)(?: for (?:your |the )?help)?', q):
        return guide('thanks', ["You're welcome! What would you like to look at next?"], choices(previous, labels), previous, pending)
    if re.fullmatch(r'(?:ok|okay|sure|yes|please)', q):
        return guide('clarification', ['Which next step would you like?'], choices(previous, labels), previous, pending)
    if re.search(r'what can you do|how (?:do i|can i) use (?:this|the) (?:demo|tool)|^help(?: me)?$', q):
        return guide('help', ['I can help you find file locations, compare columns, read original READMEs, and view fake sample rows.',
                             'Start with a dataset name or a research question. This demo currently covers MGB IBD, MGB AD and UPMC AD.'], choices(previous, labels), previous, pending)
    if re.search(r'(?:what|which) (?:information|documentation|details|files).*(?:need|collect|provide|add)|how (?:do i|can i|to).*(?:add|include).*dataset', q):
        topic = mentioned_topic(query) or pending
        name = topic_name(topic) if topic else 'a new dataset'
        return guide('documentation_help', [f'To add {name}, collect the README, current contact, storage location, and a short description of the files.',
                     'For each file, include column names, column meanings and types, and what one row represents. Note any access restrictions.',
                     'For a preview, provide generated fake rows—not real patient records. Adding documents is a separate preparation step; this chat does not upload or add them automatically.'],
                     choices(), previous, topic)
    if handle_pending and pending and not re.search(r'\bibd\b|\bad\b|alzheimer|inflammatory bowel', q) and re.search(r'\b(it|its|that|those|these|o2|eris|monthly|daily|rows|columns|where)\b|what about', q) and not mentioned_topic(query):
        return unavailable(query, topic=pending)
    return None


def unavailable(query, topic=None):
    topic = valid_topic(topic) or mentioned_topic(query)
    if topic:
        name = topic_name(topic)
        return guide('unavailable', [f"I don't have documentation for {name} loaded yet, so I can't verify its file locations or recommend a cohort from it.",
                     'It may exist elsewhere in the lab. Would you like a checklist for adding it, or would you like to explore the available AD and IBD examples?'],
                     [{'label':'What information should I collect?', 'query':f'What information do you need to add {name} as a dataset?'},
                      {'label':'Explore AD instead', 'query':'What AD data do we have?'},
                      {'label':'Explore IBD instead', 'query':'What IBD data do we have?'}], pending=topic)
    if re.search(r'\bupmc\b', query.lower()) and re.search(r'\bibd\b|inflammatory bowel', query.lower()):
        return guide('unavailable', ["UPMC IBD is not loaded in this demo. I can show you MGB IBD, or the AD data from MGB and UPMC. Which would help?"], choices())
    return guide('clarification', ["Could you tell me the disease, site, or kind of data you're interested in?",
                 'For example: monthly IBD counts, AD data on O2, or the columns in a specific file.'], choices())


def semantic_guidance(route, query):
    subject = route['subject'].strip(' .?') or 'the requested data'
    if route['mode'] == 'not_documented':
        pending = mentioned_topic(query) or valid_topic('query:' + subject)
        paragraphs = [f"I can't confirm {subject} based on the documentation currently loaded. That doesn't mean the lab has no such data."]
        paragraphs.append(route['clarification'] or 'Do you mean a dedicated cohort, or particular diagnoses, medications or measurements in EHR data?')
        actions = [{'label':'What should I collect?', 'query':f'What information do you need to add {subject} as a dataset?'},
                   {'label':'Browse current datasets', 'view':'browse'}]
        return guide('not_documented', paragraphs, actions, pending=pending)
    if route['mode'] == 'out_of_scope':
        return guide('out_of_scope', ['This demo helps find and understand lab datasets. What dataset or research topic would you like to explore?'], choices())
    return guide('clarification', [route['clarification'] or 'Which disease, site, or kind of data do you mean?'], choices())
