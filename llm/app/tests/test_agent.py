"""
Unit tests for Forensic Agent
Tests intent detection, routing, and answer generation with mocked dependencies
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.agent.forensic_agent import (
    detect_intent,
    format_context,
    answer_general,
    answer_rank_suspects,
    answer_question,
    to_markdown,
    SYSTEM_PROMPT
)






@pytest.fixture
def sample_docs():
    """Sample documents from RAG"""
    return [
        {
            'doc_id': 'T1',
            'title': 'Witness Statement - John Doe',
            'text': 'I saw a red sedan parked near the scene at approximately 3pm on Tuesday. '
                   'The driver appeared to be male, approximately 6 feet tall.',
            'source_type': 'witness',
            'score': 0.88
        },
        {
            'doc_id': 'T2',
            'title': 'Forensic Report',
            'text': 'Fingerprints recovered from the safe match database records. '
                   'DNA evidence also confirms presence at the scene.',
            'source_type': 'report',
            'score': 0.85
        },
        {
            'doc_id': 'IMG1',
            'title': 'Security Footage Analysis',
            'text': 'Security camera captured suspect in dark hoodie entering through back door at 2:45pm.',
            'source_type': 'image',
            'score': 0.79
        }
    ]


@pytest.fixture
def sample_ranked_suspects():
    """Sample ranked suspects from correlator"""
    return [
        {
            'suspect_id': 1,
            'suspect_name': 'Robert Chen',
            'score': 0.78,
            'matched_clues': [
                'Name mentioned 3 time(s) in evidence',
                'Decisive evidence: fingerprints, dna'
            ],
            'components': {
                'base_sim': 0.67,
                'keyword_score': 0.60,
                'decisive_bonus': 0.15
            },
            'contributing_docs': [
                {'doc_id': 'T2', 'title': 'Forensic Report', 'score': 0.89},
                {'doc_id': 'T1', 'title': 'Witness Statement', 'score': 0.75}
            ]
        },
        {
            'suspect_id': 2,
            'suspect_name': 'Maria Santos',
            'score': 0.52,
            'matched_clues': [
                'High profile similarity (0.71)'
            ],
            'components': {
                'base_sim': 0.71,
                'keyword_score': 0.30,
                'decisive_bonus': 0.0
            },
            'contributing_docs': [
                {'doc_id': 'T3', 'title': 'Security Analysis', 'score': 0.82}
            ]
        }
    ]


@pytest.fixture
def mock_case():
    """Mock case object"""
    case = Mock()
    case.id = 1
    case.title = "Test Case - Robbery Investigation"
    case.description = "Test case description"
    return case


@pytest.fixture
def mock_suspects():
    """Mock suspects list"""
    suspect1 = Mock()
    suspect1.id = 1
    suspect1.name = "Robert Chen"
    
    suspect2 = Mock()
    suspect2.id = 2
    suspect2.name = "Maria Santos"
    
    return [suspect1, suspect2]






def test_detect_intent_rank_suspects_variants():
    """Test intent detection for suspect ranking queries"""
    rank_queries = [
        "Who is the most likely suspect?",
        "Which suspect is guilty?",
        "Who did it?",
        "Who committed the crime?",
        "Rank the suspects",
        "Who is the prime suspect?",
        "Who is responsible for this?",
        "Which person is most likely the culprit?"
    ]
    
    for query in rank_queries:
        result = detect_intent(query)
        assert result['intent'] == 'rank_suspects', f"Failed for: {query}"
        assert result['confidence'] >= 0.8


def test_detect_intent_summarize():
    """Test intent detection for summarize queries"""
    summarize_queries = [
        "Summarize the evidence",
        "Give me an overview",
        "What happened?",
        "What do we know?",
        "What are the key points?"
    ]
    
    for query in summarize_queries:
        result = detect_intent(query)
        assert result['intent'] == 'summarize', f"Failed for: {query}"
        assert result['confidence'] >= 0.7


def test_detect_intent_timeline():
    """Test intent detection for timeline queries"""
    timeline_queries = [
        "Build a timeline",
        "What is the chronology?",
        "When did this happen?",
        "Sequence of events",
        "Timeline of the crime"
    ]
    
    for query in timeline_queries:
        result = detect_intent(query)
        assert result['intent'] == 'timeline', f"Failed for: {query}"
        assert result['confidence'] >= 0.7


def test_detect_intent_general_qa():
    """Test intent detection for general Q&A"""
    general_queries = [
        "What vehicle was used?",
        "Where was the crime committed?",
        "What evidence was found?",
        "Tell me about the fingerprints"
    ]
    
    for query in general_queries:
        result = detect_intent(query)
        assert result['intent'] == 'general_qa', f"Failed for: {query}"


def test_detect_intent_case_insensitive():
    """Test that intent detection is case insensitive"""
    queries = [
        "WHO IS THE SUSPECT?",
        "who is the suspect?",
        "Who Is The Suspect?"
    ]
    
    results = [detect_intent(q) for q in queries]
    

    assert all(r['intent'] == results[0]['intent'] for r in results)






def test_format_context_basic(sample_docs):
    """Test basic context formatting"""
    context = format_context(sample_docs)
    
    assert isinstance(context, str)
    assert len(context) > 0
    

    assert 'T1' in context
    assert 'T2' in context
    assert 'IMG1' in context
    

    assert 'Witness Statement' in context
    assert 'Forensic Report' in context
    

    assert 'witness' in context
    assert 'report' in context


def test_format_context_includes_citations(sample_docs):
    """Test that context includes proper citations"""
    context = format_context(sample_docs)
    

    assert '[T1: Witness Statement' in context
    assert '[T2: Forensic Report' in context
    assert '[IMG1: Security Footage' in context
    

    assert '0.88' in context
    assert '0.85' in context


def test_format_context_truncates_long_text(sample_docs):
    """Test that context truncates overly long documents"""

    long_doc = sample_docs[0].copy()
    long_doc['text'] = "x" * 500
    
    context = format_context([long_doc])
    

    assert '...' in context
    assert len(context) < 1000


def test_format_context_truncates_many_docs():
    """Test that context truncates when many documents provided"""

    many_docs = []
    for i in range(20):
        many_docs.append({
            'doc_id': f'T{i}',
            'title': f'Document {i}',
            'text': f'Content of document {i}' * 10,
            'source_type': 'report',
            'score': 0.8 - (i * 0.01)
        })
    
    context = format_context(many_docs, max_tokens=500)
    

    assert 'truncated' in context.lower()


def test_format_context_empty_docs():
    """Test context formatting with no documents"""
    context = format_context([])
    
    assert 'NO EVIDENCE AVAILABLE' in context


def test_format_context_keeps_minimum_docs(sample_docs):
    """Test that at least 2 docs are kept even if truncated"""
    context = format_context(sample_docs, max_tokens=50)
    

    assert 'T1' in context
    assert 'T2' in context or 'truncated' in context.lower()






@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_case_index_status')
@patch('app.agent.forensic_agent.query_documents')
@patch('app.agent.forensic_agent.build_llm')
def test_answer_general_with_docs_uses_citations(
    mock_build_llm, mock_query_docs, mock_status, mock_get_case,
    sample_docs, mock_case
):
    """Test that general Q&A uses citations from retrieved docs"""

    mock_get_case.return_value = mock_case
    mock_status.return_value = {'indexed': True, 'document_count': 5}
    mock_query_docs.return_value = sample_docs
    

    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "Based on the evidence, a red sedan was seen at the scene."
    mock_llm.invoke.return_value = mock_response
    mock_build_llm.return_value = mock_llm
    

    result = answer_general(case_id=1, query="What vehicle was used?")
    

    assert result['context_used'] is True
    assert len(result['citations']) == 3
    assert 'T1' in result['citations']
    assert 'T2' in result['citations']
    assert 'IMG1' in result['citations']
    assert isinstance(result['answer'], str)
    assert len(result['answer']) > 0


@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_case_index_status')
@patch('app.agent.forensic_agent.query_documents')
def test_answer_general_no_docs_returns_insufficient(
    mock_query_docs, mock_status, mock_get_case, mock_case
):
    """Test that Q&A returns insufficient evidence when no docs found"""

    mock_get_case.return_value = mock_case
    mock_status.return_value = {'indexed': True, 'document_count': 5}
    mock_query_docs.return_value = []
    

    result = answer_general(case_id=1, query="What happened?")
    

    assert 'Insufficient evidence' in result['answer']
    assert result['context_used'] is False
    assert len(result['citations']) == 0


@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_case_index_status')
def test_answer_general_no_indexed_evidence(mock_status, mock_get_case, mock_case):
    """Test that Q&A handles case with no indexed evidence"""

    mock_get_case.return_value = mock_case
    mock_status.return_value = {'indexed': False, 'document_count': 0}
    

    result = answer_general(case_id=1, query="Test query")
    

    assert 'Insufficient evidence' in result['answer']
    assert 'no indexed evidence' in result['answer'].lower()
    assert result['context_used'] is False


@patch('app.agent.forensic_agent.get_case')
def test_answer_general_case_not_found(mock_get_case):
    """Test that Q&A handles non-existent case"""
    mock_get_case.return_value = None
    
    result = answer_general(case_id=99999, query="Test")
    
    assert 'Error' in result['answer']
    assert 'not found' in result['answer']






@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_suspects_by_case')
@patch('app.agent.forensic_agent.extract_evidence_context')
@patch('app.agent.forensic_agent.score_suspects')
def test_answer_rank_suspects_calls_correlator_and_formats(
    mock_score, mock_extract, mock_get_suspects, mock_get_case,
    sample_docs, sample_ranked_suspects, mock_case, mock_suspects
):
    """Test that suspect ranking calls correlator and formats output"""

    mock_get_case.return_value = mock_case
    mock_get_suspects.return_value = mock_suspects
    mock_extract.return_value = sample_docs
    mock_score.return_value = sample_ranked_suspects
    

    result = answer_rank_suspects(case_id=1)
    

    assert 'answer' in result
    assert 'ranked' in result
    assert 'citations' in result
    assert 'components' in result
    

    assert len(result['ranked']) == 2
    assert result['ranked'][0]['suspect_name'] == 'Robert Chen'
    

    answer = result['answer']
    assert 'Robert Chen' in answer
    assert '0.78' in answer
    assert 'fingerprints' in answer.lower()
    assert 'CAVEAT' in answer or 'caveat' in answer
    assert 'decision support' in answer.lower()
    

    assert len(result['citations']) == 3


@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_suspects_by_case')
@patch('app.agent.forensic_agent.extract_evidence_context')
def test_answer_rank_suspects_insufficient_evidence_path(
    mock_extract, mock_get_suspects, mock_get_case,
    mock_case, mock_suspects
):
    """Test suspect ranking with no evidence"""

    mock_get_case.return_value = mock_case
    mock_get_suspects.return_value = mock_suspects
    mock_extract.return_value = []
    

    result = answer_rank_suspects(case_id=1)
    

    assert 'Insufficient evidence' in result['answer']
    assert len(result['ranked']) == 0
    assert result['components']['docs_used'] == 0


@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_suspects_by_case')
def test_answer_rank_suspects_no_suspects(mock_get_suspects, mock_get_case, mock_case):
    """Test suspect ranking when case has no suspects"""
    mock_get_case.return_value = mock_case
    mock_get_suspects.return_value = []
    
    result = answer_rank_suspects(case_id=1)
    
    assert 'Insufficient evidence' in result['answer']
    assert 'No suspects' in result['answer']
    assert len(result['ranked']) == 0


@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_suspects_by_case')
@patch('app.agent.forensic_agent.extract_evidence_context')
@patch('app.agent.forensic_agent.score_suspects')
def test_answer_rank_suspects_all_zero_scores(
    mock_score, mock_extract, mock_get_suspects, mock_get_case,
    sample_docs, mock_case, mock_suspects
):
    """Test suspect ranking when all scores are zero"""
    mock_get_case.return_value = mock_case
    mock_get_suspects.return_value = mock_suspects
    mock_extract.return_value = sample_docs
    

    zero_ranked = [
        {
            'suspect_id': 1,
            'suspect_name': 'Suspect A',
            'score': 0.0,
            'matched_clues': ['No evidence'],
            'components': {},
            'contributing_docs': []
        }
    ]
    mock_score.return_value = zero_ranked
    
    result = answer_rank_suspects(case_id=1)
    
    assert 'Insufficient evidence' in result['answer']






@patch('app.agent.forensic_agent.answer_rank_suspects')
@patch('app.agent.forensic_agent.answer_general')
def test_answer_question_routes_to_ranking(mock_general, mock_ranking):
    """Test that ranking queries route to answer_rank_suspects"""
    mock_ranking.return_value = {'answer': 'Ranked', 'ranked': []}
    
    result = answer_question(case_id=1, user_query="Who is the most likely suspect?")
    

    mock_ranking.assert_called_once()
    mock_general.assert_not_called()


@patch('app.agent.forensic_agent.answer_rank_suspects')
@patch('app.agent.forensic_agent.answer_general')
def test_answer_question_routes_to_general(mock_general, mock_ranking):
    """Test that non-ranking queries route to answer_general"""
    mock_general.return_value = {'answer': 'General answer', 'citations': []}
    
    result = answer_question(case_id=1, user_query="What vehicle was used?")
    

    mock_general.assert_called_once()
    mock_ranking.assert_not_called()


@patch('app.agent.forensic_agent.answer_rank_suspects')
@patch('app.agent.forensic_agent.answer_general')
def test_answer_question_summarize_routes_to_general(mock_general, mock_ranking):
    """Test that summarize queries route to general"""
    mock_general.return_value = {'answer': 'Summary', 'citations': []}
    
    result = answer_question(case_id=1, user_query="Summarize the evidence")
    
    mock_general.assert_called_once()
    mock_ranking.assert_not_called()






def test_to_markdown_basic():
    """Test markdown formatting of result"""
    result = {
        'answer': 'Test answer',
        'citations': ['T1', 'T2'],
        'components': {'docs_used': 2}
    }
    
    markdown = to_markdown(result)
    
    assert 'Test answer' in markdown
    assert 'T1' in markdown
    assert 'T2' in markdown
    assert 'Citations' in markdown


def test_to_markdown_with_ranked():
    """Test markdown formatting with ranked suspects"""
    result = {
        'answer': '# Suspect Rankings\n\n1. Robert Chen',
        'ranked': [{'suspect_name': 'Robert Chen', 'score': 0.78}],
        'citations': ['T1'],
        'components': {'docs_used': 5, 'suspects_analyzed': 2}
    }
    
    markdown = to_markdown(result)
    
    assert 'Robert Chen' in markdown
    assert 'Citations' in markdown
    assert 'docs_used' in markdown.lower() or 'Docs Used' in markdown


def test_to_markdown_no_citations():
    """Test markdown formatting without citations"""
    result = {
        'answer': 'No evidence found',
        'citations': []
    }
    
    markdown = to_markdown(result)
    
    assert 'No evidence found' in markdown

    assert len(result['citations']) == 0






def test_system_prompt_contains_key_instructions():
    """Test that system prompt has essential instructions"""
    assert 'forensic' in SYSTEM_PROMPT.lower()
    assert 'evidence' in SYSTEM_PROMPT.lower()
    assert 'cite' in SYSTEM_PROMPT.lower() or 'citation' in SYSTEM_PROMPT.lower()
    assert 'insufficient evidence' in SYSTEM_PROMPT.lower()
    assert 'decision support' in SYSTEM_PROMPT.lower()
    assert 'caveat' in SYSTEM_PROMPT.lower() or 'disclaimer' in SYSTEM_PROMPT.lower()






def test_format_context_handles_missing_fields():
    """Test context formatting with incomplete document data"""
    incomplete_docs = [
        {
            'doc_id': 'T1',

            'text': 'Some text',

            'score': 0.5
        },
        {

            'title': 'Document',
            'text': 'More text',
            'source_type': 'report',
            'score': 0.8
        }
    ]
    
    context = format_context(incomplete_docs)
    

    assert isinstance(context, str)
    assert len(context) > 0


def test_detect_intent_empty_query():
    """Test intent detection with empty query"""
    result = detect_intent("")
    

    assert result['intent'] == 'general_qa'


def test_detect_intent_very_long_query():
    """Test intent detection with very long query"""
    long_query = "who is the suspect " * 100
    
    result = detect_intent(long_query)
    

    assert result['intent'] == 'rank_suspects'


@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_case_index_status')
@patch('app.agent.forensic_agent.query_documents')
@patch('app.agent.forensic_agent.build_llm')
def test_answer_general_llm_error_handling(
    mock_build_llm, mock_query_docs, mock_status, mock_get_case,
    sample_docs, mock_case
):
    """Test that general Q&A handles LLM errors gracefully"""
    mock_get_case.return_value = mock_case
    mock_status.return_value = {'indexed': True, 'document_count': 5}
    mock_query_docs.return_value = sample_docs
    

    mock_llm = Mock()
    mock_llm.invoke.side_effect = Exception("API Error")
    mock_build_llm.return_value = mock_llm
    
    result = answer_general(case_id=1, query="Test")
    

    assert 'Error' in result['answer']
    assert result['context_used'] is True
    assert len(result['citations']) > 0






@patch('app.agent.forensic_agent.get_case')
@patch('app.agent.forensic_agent.get_suspects_by_case')
@patch('app.agent.forensic_agent.extract_evidence_context')
@patch('app.agent.forensic_agent.score_suspects')
def test_full_workflow_rank_suspects(
    mock_score, mock_extract, mock_get_suspects, mock_get_case,
    sample_docs, sample_ranked_suspects, mock_case, mock_suspects
):
    """Test complete workflow from query to ranked output"""

    mock_get_case.return_value = mock_case
    mock_get_suspects.return_value = mock_suspects
    mock_extract.return_value = sample_docs
    mock_score.return_value = sample_ranked_suspects
    

    query = "Who is the most likely suspect?"
    

    intent_result = detect_intent(query)
    assert intent_result['intent'] == 'rank_suspects'
    

    result = answer_rank_suspects(case_id=1)
    

    assert result['answer']
    assert len(result['ranked']) == 2
    assert result['ranked'][0]['score'] > result['ranked'][1]['score']
    assert len(result['citations']) > 0
    

    markdown = to_markdown(result)
    assert 'Robert Chen' in markdown
    assert 'caveat' in markdown.lower() or 'decision support' in markdown.lower()


def test_multiple_queries_same_intent():
    """Test that similar queries consistently return same intent"""
    queries = [
        "Who did this crime?",
        "Who committed this crime?",
        "Who is responsible for this crime?"
    ]
    
    intents = [detect_intent(q) for q in queries]
    

    assert all(i['intent'] == 'rank_suspects' for i in intents)

