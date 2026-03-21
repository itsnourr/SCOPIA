"""
Unit tests for Evidence Correlator tool
Tests scoring logic, determinism, edge cases, and database integration
"""

import pytest
import numpy as np
from typing import List, Dict, Any

from app.tools.evidence_correlator import (
    extract_evidence_context,
    score_suspects,
    correlate_and_persist,
    _tokenize,
    _keyword_features,
    _vector_similarity,
    _hybrid_score,
    pretty_rankings,
    W_SIM,
    W_KW,
    W_DECISIVE,
    DECISIVE_HIT_VALUE,
    DECISIVE_TERMS
)
from app.db import add_case, add_suspect, add_text
from app.db.dao import get_analysis_results
from app.rag import build_case_index, reset_vectorstore



@pytest.fixture(scope="function")
def test_case():
    """Create a test case"""
    case = add_case(
        title="Evidence Correlator Test Case",
        description="Test case for evidence correlation"
    )
    yield case


@pytest.fixture(scope="function")
def suspects_with_profiles(test_case):
    """
    Create 3 suspects with different profiles
    Designed to test different scoring scenarios
    """


    suspect1 = add_suspect(
        case_id=test_case.id,
        name="Robert Chen",
        profile_text="Known burglar with history of breaking and entering. "
                    "Previously convicted for theft. Often works alone.",
        metadata_json={
            "age": 34,
            "vehicle": "red Honda Civic",
            "known_vehicles": ["red Honda Civic", "black motorcycle"],
            "occupation": "Unemployed"
        }
    )
    


    suspect2 = add_suspect(
        case_id=test_case.id,
        name="Maria Santos",
        profile_text="Former security specialist with expertise in alarm systems. "
                    "Recently fired from security company. Financial difficulties. "
                    "Knows how to bypass security measures.",
        metadata_json={
            "age": 29,
            "vehicle": "blue Toyota Camry",
            "occupation": "Unemployed (former security)",
            "workplace": "SecureMax Security"
        }
    )
    


    suspect3 = add_suspect(
        case_id=test_case.id,
        name="James O'Connor",
        profile_text="Restaurant manager with no criminal record. "
                    "Works regular hours. Family man with two children.",
        metadata_json={
            "age": 45,
            "vehicle": "white minivan",
            "occupation": "Restaurant Manager",
            "workplace": "Olive Garden"
        }
    )
    
    return [suspect1, suspect2, suspect3]


@pytest.fixture(scope="function")
def evidence_documents(test_case, suspects_with_profiles):
    """
    Create evidence documents with decisive terms and suspect mentions
    Designed to favor suspect1 (Robert Chen) with decisive evidence
    """

    text1 = add_text(
        case_id=test_case.id,
        source_type="report",
        title="Forensic Analysis Report",
        content="Fingerprints recovered from the safe match database records for Robert Chen. "
               "DNA evidence also confirms his presence at the scene. The suspect's "
               "fingerprints were found on both the door handle and the safe."
    )
    

    text2 = add_text(
        case_id=test_case.id,
        source_type="witness",
        title="Security Guard Statement",
        content="The alarm system was professionally disabled. Someone with knowledge "
               "of security systems bypassed the motion sensors. The method used "
               "suggests expertise in security technology and alarm systems."
    )
    

    text3 = add_text(
        case_id=test_case.id,
        source_type="witness",
        title="Neighbor Witness Statement",
        content="I saw a red Honda Civic parked near the alley around 2am. "
               "Robert Chen was seen in the area earlier that evening. "
               "The car matched the description of vehicles associated with recent burglaries."
    )
    

    text4 = add_text(
        case_id=test_case.id,
        source_type="report",
        title="Crime Scene Analysis",
        content="Evidence of forceful entry through rear window. Glass broken from outside. "
               "Method consistent with previous burglary cases. Suspect used tools to "
               "pry open the window frame before entry."
    )
    

    text5 = add_text(
        case_id=test_case.id,
        source_type="report",
        title="Timeline Analysis",
        content="Crime occurred between 2:00 AM and 3:30 AM based on security footage timestamps. "
               "No visible faces captured on camera due to masks worn by suspects."
    )
    
    return [text1, text2, text3, text4, text5]


@pytest.fixture(scope="function")
def indexed_case(test_case, suspects_with_profiles, evidence_documents):
    """Case with suspects and indexed evidence"""

    build_case_index(test_case.id, force_rebuild=True)
    yield test_case






def test_tokenize_basic():
    """Test basic tokenization"""
    tokens = _tokenize("John's fingerprints were found!")
    
    assert 'john' in tokens
    assert 'fingerprints' in tokens
    assert 'were' in tokens
    assert 'found' in tokens
    assert "john's" not in tokens


def test_tokenize_punctuation():
    """Test tokenization removes punctuation"""
    tokens = _tokenize("DNA, fingerprints... weapon!")
    
    assert 'dna' in tokens
    assert 'fingerprints' in tokens
    assert 'weapon' in tokens
    assert ',' not in tokens
    assert '...' not in tokens


def test_tokenize_unicode():
    """Test tokenization handles unicode"""
    tokens = _tokenize("Café résumé naïve")
    
    assert 'café' in tokens
    assert 'résumé' in tokens
    assert 'naïve' in tokens






def test_keyword_features_name_hits():
    """Test keyword features detect name mentions"""
    texts = [
        "Robert Chen was seen at the scene",
        "Chen's fingerprints were found"
    ]
    
    features = _keyword_features(texts, "Robert Chen", [])
    
    assert features['name_hits'] >= 1
    assert features['keyword_score'] > 0


def test_keyword_features_decisive_hits():
    """Test keyword features detect decisive terms"""
    texts = [
        "Fingerprints recovered from scene",
        "DNA evidence confirms suspect presence",
        "Weapon found with suspect's prints"
    ]
    
    features = _keyword_features(texts, "Unknown Suspect", [])
    
    assert 'fingerprints' in features['decisive_hits']
    assert 'dna' in features['decisive_hits']
    assert 'weapon' in features['decisive_hits']
    assert len(features['decisive_hits']) == 3


def test_keyword_features_extra_terms():
    """Test keyword features count extra terms"""
    texts = [
        "Red Honda Civic seen at scene",
        "Vehicle parked near alley"
    ]
    
    features = _keyword_features(texts, "Suspect", ["red Honda Civic", "vehicle"])
    
    assert features['term_hits'] > 0


def test_keyword_features_empty_evidence():
    """Test keyword features with no evidence"""
    features = _keyword_features([], "Suspect", [])
    
    assert features['name_hits'] == 0
    assert features['term_hits'] == 0
    assert features['decisive_hits'] == []
    assert features['keyword_score'] == 0.0






def test_vector_similarity_basic():
    """Test vector similarity computation"""
    profile = "Known burglar with history of theft"
    texts = [
        "Burglary at jewelry store",
        "Suspect has criminal record for theft"
    ]
    
    result = _vector_similarity(profile, texts)
    
    assert 'sims' in result
    assert 'base_sim' in result
    assert len(result['sims']) == 2
    assert 0.0 <= result['base_sim'] <= 1.0


def test_vector_similarity_empty_evidence():
    """Test vector similarity with no evidence"""
    profile = "Test profile"
    
    result = _vector_similarity(profile, [])
    
    assert result['sims'] == []
    assert result['base_sim'] == 0.0


def test_vector_similarity_top_3_averaging():
    """Test that base_sim uses top-3 average when >=3 docs"""
    profile = "Security expert"
    texts = [
        "Security system professionally disabled",
        "Alarm bypass shows expertise",
        "Security knowledge evident",
        "Random unrelated text about weather"
    ]
    
    result = _vector_similarity(profile, texts)
    
    assert len(result['sims']) == 4

    simple_avg = sum(result['sims']) / len(result['sims'])
    top3_avg = sum(sorted(result['sims'], reverse=True)[:3]) / 3
    
    assert abs(result['base_sim'] - top3_avg) < 0.01






def test_hybrid_score_weights():
    """Test hybrid score combines weights correctly"""

    score = _hybrid_score(base_sim=1.0, keyword_score=1.0, decisive_hits=['dna', 'fingerprints'])
    

    expected = W_SIM * 1.0 + W_KW * 1.0 + W_DECISIVE
    
    assert abs(score - expected) < 0.01


def test_hybrid_score_decisive_cap():
    """Test decisive hits are capped at W_DECISIVE"""

    many_hits = list(DECISIVE_TERMS)[:5]
    
    score = _hybrid_score(base_sim=0.0, keyword_score=0.0, decisive_hits=many_hits)
    

    assert score <= W_DECISIVE + 0.01


def test_hybrid_score_bounds():
    """Test hybrid score is bounded [0, 1]"""

    test_cases = [
        (0.0, 0.0, []),
        (1.0, 1.0, list(DECISIVE_TERMS)),
        (0.5, 0.5, ['dna']),
        (0.8, 0.2, ['fingerprints', 'weapon'])
    ]
    
    for base_sim, kw_score, hits in test_cases:
        score = _hybrid_score(base_sim, kw_score, hits)
        assert 0.0 <= score <= 1.0


def test_hybrid_score_zero_baseline():
    """Test hybrid score with no evidence"""
    score = _hybrid_score(base_sim=0.0, keyword_score=0.0, decisive_hits=[])
    
    assert score == 0.0






def test_extract_evidence_context_default_query_returns_docs(indexed_case):
    """Test extracting evidence with default query"""
    docs = extract_evidence_context(indexed_case.id, query=None, k=5)
    
    assert isinstance(docs, list)
    assert len(docs) > 0
    

    for doc in docs:
        assert 'doc_id' in doc
        assert 'text' in doc
        assert 'source_type' in doc
        assert 'score' in doc


def test_extract_evidence_context_custom_query(indexed_case):
    """Test extracting evidence with custom query"""
    docs = extract_evidence_context(
        indexed_case.id,
        query="fingerprints and DNA evidence",
        k=3
    )
    
    assert isinstance(docs, list)
    assert len(docs) > 0


def test_extract_evidence_context_no_indexed_data(test_case):
    """Test extracting evidence when case has no indexed data"""
    docs = extract_evidence_context(test_case.id, k=5)
    
    assert docs == []


def test_extract_evidence_context_large_k_capped(indexed_case):
    """Test that large k is capped by available documents"""
    docs = extract_evidence_context(indexed_case.id, k=1000)
    

    assert len(docs) < 1000






def test_score_suspects_structure_and_sorting(indexed_case, suspects_with_profiles):
    """Test suspect scoring returns correct structure and sorting"""
    docs = extract_evidence_context(indexed_case.id, k=8)
    ranked = score_suspects(indexed_case.id, docs)
    
    assert isinstance(ranked, list)
    assert len(ranked) == 3
    

    for suspect in ranked:
        assert 'suspect_id' in suspect
        assert 'suspect_name' in suspect
        assert 'score' in suspect
        assert 'matched_clues' in suspect
        assert 'components' in suspect
        assert 'contributing_docs' in suspect
        

        assert 0.0 <= suspect['score'] <= 1.0
        

        assert 'base_sim' in suspect['components']
        assert 'keyword_score' in suspect['components']
    

    for i in range(len(ranked) - 1):
        assert ranked[i]['score'] >= ranked[i+1]['score']


def test_decisive_hits_boost_scoring_cap_at_one(indexed_case, suspects_with_profiles):
    """Test that decisive hits boost scoring but cap at 1.0"""
    docs = extract_evidence_context(indexed_case.id, k=8)
    ranked = score_suspects(indexed_case.id, docs)
    

    robert = next(s for s in ranked if 'Robert' in s['suspect_name'])
    

    assert robert['components'].get('decisive_bonus', 0) > 0
    

    assert robert['score'] <= 1.0


def test_keyword_only_vs_vector_only_tradeoff(indexed_case, suspects_with_profiles):
    """Test scoring balances keyword and vector similarity"""
    docs = extract_evidence_context(indexed_case.id, k=8)
    ranked = score_suspects(indexed_case.id, docs)
    

    robert = next(s for s in ranked if 'Robert' in s['suspect_name'])
    

    maria = next(s for s in ranked if 'Maria' in s['suspect_name'])
    

    assert robert['components']['keyword_score'] > 0
    assert maria['components']['base_sim'] > 0
    

    assert robert['score'] > maria['score']


def test_empty_evidence_returns_zero_scores_without_persist(test_case, suspects_with_profiles):
    """Test scoring with no evidence returns zeros"""
    ranked = score_suspects(test_case.id, evidence_docs=[])
    
    assert len(ranked) == 3
    

    for suspect in ranked:
        assert suspect['score'] == 0.0
        assert 'No evidence available' in suspect['matched_clues']


def test_no_suspects_returns_empty_list(indexed_case):
    """Test scoring with no suspects returns empty list"""

    docs = extract_evidence_context(indexed_case.id, k=5)
    

    empty_case = add_case("Empty Case", "No suspects")
    ranked = score_suspects(empty_case.id, docs)
    
    assert ranked == []






def test_correlate_and_persist_writes_analysis_results(indexed_case, suspects_with_profiles):
    """Test complete correlation workflow persists to database"""
    result = correlate_and_persist(indexed_case.id, query=None, k=8)
    

    assert 'case_id' in result
    assert 'query' in result
    assert 'docs_used' in result
    assert 'ranked' in result
    assert 'persisted' in result
    
    assert result['case_id'] == indexed_case.id
    assert result['docs_used'] > 0
    assert len(result['ranked']) == 3
    assert result['persisted'] is True
    

    db_results = get_analysis_results(indexed_case.id)
    assert len(db_results) == 3


def test_correlate_no_evidence_returns_error(test_case, suspects_with_profiles):
    """Test correlation with no indexed evidence returns error"""
    result = correlate_and_persist(test_case.id)
    
    assert 'error' in result
    assert result['error'] == 'insufficient_evidence'
    assert result['docs_used'] == 0
    

    db_results = get_analysis_results(test_case.id)
    assert len(db_results) == 0


def test_correlate_custom_query(indexed_case, suspects_with_profiles):
    """Test correlation with custom query"""
    result = correlate_and_persist(
        indexed_case.id,
        query="Who committed the burglary?",
        k=5
    )
    
    assert 'error' not in result
    assert result['query'] == "Who committed the burglary?"
    assert len(result['ranked']) > 0






def test_determinism_ties_sorted_by_name(test_case):
    """Test that tied scores are sorted by name for determinism"""

    suspect_a = add_suspect(
        test_case.id,
        "Alice Anderson",
        "Generic profile text for testing",
        {}
    )
    
    suspect_z = add_suspect(
        test_case.id,
        "Zachary Zhang",
        "Generic profile text for testing",
        {}
    )
    

    add_text(
        test_case.id,
        "report",
        "Test Report",
        "Generic evidence text"
    )
    

    build_case_index(test_case.id, force_rebuild=True)
    

    results = []
    for _ in range(3):
        result = correlate_and_persist(test_case.id, k=5)
        results.append(result['ranked'])
    

    for i in range(len(results) - 1):
        names1 = [s['suspect_name'] for s in results[i]]
        names2 = [s['suspect_name'] for s in results[i+1]]
        assert names1 == names2






def test_handles_unicode_and_punctuation(test_case):
    """Test handling of unicode and punctuation in evidence/names"""
    suspect = add_suspect(
        test_case.id,
        "José María O'Connor",
        "Suspect with special characters in name",
        {}
    )
    
    text = add_text(
        test_case.id,
        "witness",
        "Witness Statement",
        "José was seen! María's car (O'Connor's vehicle) parked nearby... DNA found."
    )
    
    build_case_index(test_case.id, force_rebuild=True)
    
    result = correlate_and_persist(test_case.id)
    
    assert 'error' not in result
    assert len(result['ranked']) == 1


def test_case_not_found():
    """Test correlation with non-existent case"""
    result = correlate_and_persist(case_id=99999)
    
    assert 'error' in result
    assert result['error'] == 'case_not_found'


def test_contributing_docs_limited_to_three(indexed_case, suspects_with_profiles):
    """Test that contributing_docs is limited to top 3"""
    docs = extract_evidence_context(indexed_case.id, k=10)
    ranked = score_suspects(indexed_case.id, docs)
    
    for suspect in ranked:
        assert len(suspect['contributing_docs']) <= 3


def test_matched_clues_non_empty(indexed_case, suspects_with_profiles):
    """Test that matched_clues is always populated"""
    result = correlate_and_persist(indexed_case.id)
    
    for suspect in result['ranked']:
        assert len(suspect['matched_clues']) > 0






def test_pretty_rankings_format():
    """Test pretty_rankings formats output correctly"""
    ranked = [
        {
            'suspect_name': 'Test Suspect',
            'score': 0.85,
            'matched_clues': ['Clue 1', 'Clue 2'],
            'contributing_docs': [
                {'doc_id': 'doc1', 'title': 'Evidence 1', 'score': 0.9}
            ]
        }
    ]
    
    output = pretty_rankings(ranked)
    
    assert 'Test Suspect' in output
    assert '0.85' in output
    assert 'Clue 1' in output
    assert 'Clue 2' in output
    assert 'Evidence 1' in output


def test_pretty_rankings_empty():
    """Test pretty_rankings handles empty list"""
    output = pretty_rankings([])
    
    assert 'No suspects' in output






def test_components_sum_to_final_score(indexed_case, suspects_with_profiles):
    """Test that score components approximately sum to final score"""
    docs = extract_evidence_context(indexed_case.id, k=8)
    ranked = score_suspects(indexed_case.id, docs)
    
    for suspect in ranked:
        components = suspect['components']
        

        reconstructed = (
            W_SIM * components['base_sim'] +
            W_KW * components['keyword_score'] +
            components.get('decisive_bonus', 0)
        )
        

        assert abs(suspect['score'] - reconstructed) < 0.01


def test_zero_components_give_zero_score():
    """Test that zero components result in zero final score"""
    score = _hybrid_score(base_sim=0.0, keyword_score=0.0, decisive_hits=[])
    
    assert score == 0.0






def test_handles_very_long_evidence_text(test_case):
    """Test handling of very long evidence documents"""
    suspect = add_suspect(test_case.id, "Suspect", "Profile", {})
    

    long_text = "Evidence text. " * 700
    add_text(test_case.id, "report", "Long Report", long_text)
    
    build_case_index(test_case.id, force_rebuild=True)
    
    result = correlate_and_persist(test_case.id)
    
    assert 'error' not in result
    assert len(result['ranked']) == 1


def test_handles_many_suspects(test_case):
    """Test handling of many suspects"""

    for i in range(10):
        add_suspect(
            test_case.id,
            f"Suspect {i:02d}",
            f"Profile for suspect {i}",
            {}
        )
    
    add_text(test_case.id, "report", "Evidence", "Test evidence")
    build_case_index(test_case.id, force_rebuild=True)
    
    result = correlate_and_persist(test_case.id)
    
    assert len(result['ranked']) == 10

    for i in range(len(result['ranked']) - 1):
        assert result['ranked'][i]['score'] >= result['ranked'][i+1]['score']

