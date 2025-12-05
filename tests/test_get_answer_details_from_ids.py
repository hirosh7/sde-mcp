"""
Unit tests for get_answer_details_from_ids tool.

Tests the API client method and MCP tool for retrieving question and answer
details from answer IDs.
"""
import json
import pytest  # type: ignore[import-untyped]  # pytest is in optional test dependencies
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from sde_mcp_server.api_client import SDElementsAPIClient
from sde_mcp_server.tools.surveys import get_answer_details_from_ids
from fastmcp import Context


@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing"""
    client = Mock(spec=SDElementsAPIClient)
    client._library_answers_cache = None
    return client


@pytest.fixture
def sample_library_answers():
    """Sample library answers data for testing"""
    return [
        {
            'id': 'A701',
            'text': 'Java',
            'question': 'Q100',
            'display_text': 'What programming language do you use? - Java',
            'description': 'Java programming language'
        },
        {
            'id': 'A702',
            'text': 'Python',
            'question': 'Q100',
            'display_text': 'What programming language do you use? - Python',
            'description': 'Python programming language'
        },
        {
            'id': 'A493',
            'text': 'PostgreSQL',
            'question': 'Q200',
            'display_text': 'What database do you use? - PostgreSQL',
            'description': 'PostgreSQL database'
        },
        {
            'id': 'A21',
            'text': 'Web Application',
            'question': 'Q50',
            'display_text': 'What type of application? - Web Application',
            'description': 'Web-based application'
        }
    ]


@pytest.fixture
def sample_question_details():
    """Sample question details from library/questions endpoint"""
    return {
        'Q100': {
            'id': 'Q100',
            'text': 'What programming language do you use?',
            'description': 'Select the primary programming language',
            'format': 'MC',
            'mandatory': True
        },
        'Q200': {
            'id': 'Q200',
            'text': 'What database do you use?',
            'description': 'Select the database technology',
            'format': 'MC',
            'mandatory': False
        },
        'Q50': {
            'id': 'Q50',
            'text': 'What type of application?',
            'description': 'Select the application type',
            'format': 'MC',
            'mandatory': True
        }
    }


class TestGetLibraryQuestion:
    """Tests for get_library_question API client method"""
    
    def test_get_library_question_success(self, mock_api_client):
        """Test successfully getting question details"""
        question_data = {
            'id': 'Q100',
            'text': 'What programming language do you use?',
            'description': 'Select the primary programming language',
            'format': 'MC',
            'mandatory': True
        }
        
        with patch.object(SDElementsAPIClient, 'get', return_value=question_data):
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            result = client.get_library_question('Q100')
            
            assert result == question_data
            assert result['id'] == 'Q100'
            assert result['text'] == 'What programming language do you use?'
    
    def test_get_library_question_not_found(self, mock_api_client):
        """Test getting question details when question doesn't exist"""
        from sde_mcp_server.api_client import SDElementsNotFoundError
        
        with patch.object(SDElementsAPIClient, 'get', side_effect=SDElementsNotFoundError("Question not found")):
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            
            with pytest.raises(SDElementsNotFoundError):
                client.get_library_question('Q999')


class TestGetAnswerDetailsFromIds:
    """Tests for get_answer_details_from_ids API client method"""
    
    def test_get_answer_details_single_answer(self, sample_library_answers, sample_question_details):
        """Test getting details for a single answer ID"""
        with patch.object(SDElementsAPIClient, 'load_library_answers') as mock_load, \
             patch.object(SDElementsAPIClient, 'get_library_question') as mock_get_question:
            
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = sample_library_answers
            
            # Mock question details
            def get_question_side_effect(question_id):
                return sample_question_details.get(question_id, {})
            
            mock_get_question.side_effect = get_question_side_effect
            
            result = client.get_answer_details_from_ids(['A701'])
            
            assert 'answers' in result
            assert 'not_found' in result
            assert len(result['answers']) == 1
            assert len(result['not_found']) == 0
            
            answer = result['answers'][0]
            assert answer['id'] == 'A701'
            assert answer['text'] == 'Java'
            assert answer['question_id'] == 'Q100'
            assert answer['question_text'] == 'What programming language do you use?'
            assert 'question_description' in answer
            assert 'question_format' in answer
            assert 'question_mandatory' in answer
    
    def test_get_answer_details_multiple_answers(self, sample_library_answers, sample_question_details):
        """Test getting details for multiple answer IDs"""
        with patch.object(SDElementsAPIClient, 'load_library_answers'), \
             patch.object(SDElementsAPIClient, 'get_library_question') as mock_get_question:
            
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = sample_library_answers
            
            def get_question_side_effect(question_id):
                return sample_question_details.get(question_id, {})
            
            mock_get_question.side_effect = get_question_side_effect
            
            result = client.get_answer_details_from_ids(['A701', 'A493', 'A21'])
            
            assert len(result['answers']) == 3
            assert len(result['not_found']) == 0
            
            # Check all answers are present
            answer_ids = {a['id'] for a in result['answers']}
            assert answer_ids == {'A701', 'A493', 'A21'}
            
            # Verify question texts are populated
            for answer in result['answers']:
                assert 'question_text' in answer
                assert answer['question_text']  # Not empty
                assert 'text' in answer
                assert answer['text']  # Not empty
    
    def test_get_answer_details_not_found(self, sample_library_answers):
        """Test getting details for answer IDs that don't exist"""
        with patch.object(SDElementsAPIClient, 'load_library_answers'):
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = sample_library_answers
            
            result = client.get_answer_details_from_ids(['A999', 'A998'])
            
            assert len(result['answers']) == 0
            assert len(result['not_found']) == 2
            assert 'A999' in result['not_found']
            assert 'A998' in result['not_found']
    
    def test_get_answer_details_mixed_found_and_not_found(self, sample_library_answers, sample_question_details):
        """Test getting details with some found and some not found"""
        with patch.object(SDElementsAPIClient, 'load_library_answers'), \
             patch.object(SDElementsAPIClient, 'get_library_question') as mock_get_question:
            
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = sample_library_answers
            
            def get_question_side_effect(question_id):
                return sample_question_details.get(question_id, {})
            
            mock_get_question.side_effect = get_question_side_effect
            
            result = client.get_answer_details_from_ids(['A701', 'A999', 'A493'])
            
            assert len(result['answers']) == 2
            assert len(result['not_found']) == 1
            assert 'A999' in result['not_found']
            
            # Verify found answers
            found_ids = {a['id'] for a in result['answers']}
            assert found_ids == {'A701', 'A493'}
    
    def test_get_answer_details_empty_list(self):
        """Test getting details for empty answer ID list"""
        with patch.object(SDElementsAPIClient, 'load_library_answers'):
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = []
            
            result = client.get_answer_details_from_ids([])
            
            assert len(result['answers']) == 0
            assert len(result['not_found']) == 0
    
    def test_get_answer_details_loads_cache_if_missing(self, sample_library_answers, sample_question_details):
        """Test that library answers cache is loaded if not already loaded"""
        with patch.object(SDElementsAPIClient, 'load_library_answers') as mock_load, \
             patch.object(SDElementsAPIClient, 'get_library_question') as mock_get_question:
            
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = None  # Cache not loaded
            
            # Mock load_library_answers to set the cache
            def load_side_effect():
                client._library_answers_cache = sample_library_answers
            
            mock_load.side_effect = load_side_effect
            
            def get_question_side_effect(question_id):
                return sample_question_details.get(question_id, {})
            
            mock_get_question.side_effect = get_question_side_effect
            
            result = client.get_answer_details_from_ids(['A701'])
            
            # Verify load_library_answers was called
            mock_load.assert_called_once()
            assert len(result['answers']) == 1
    
    def test_get_answer_details_question_fetch_failure(self, sample_library_answers):
        """Test that answer details still work if question fetch fails and all fields are present with defaults"""
        from sde_mcp_server.api_client import SDElementsAPIError
        
        with patch.object(SDElementsAPIClient, 'load_library_answers'), \
             patch.object(SDElementsAPIClient, 'get_library_question', side_effect=SDElementsAPIError("API Error")):
            
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = sample_library_answers
            
            result = client.get_answer_details_from_ids(['A701'])
            
            # Should still return answer with display_text question
            assert len(result['answers']) == 1
            answer = result['answers'][0]
            assert answer['id'] == 'A701'
            assert answer['text'] == 'Java'
            # Should have question_text from display_text even if question fetch failed
            assert 'question_text' in answer
            assert answer['question_text'] == 'What programming language do you use?'
            # All question metadata fields should be present with default values
            assert 'question_description' in answer
            assert answer['question_description'] == ''  # Default when fetch fails
            assert 'question_format' in answer
            assert answer['question_format'] == ''  # Default when fetch fails
            assert 'question_mandatory' in answer
            assert answer['question_mandatory'] is False  # Default when fetch fails
    
    def test_get_answer_details_extracts_question_from_display_text(self, sample_library_answers):
        """Test that question text is extracted from display_text when question endpoint unavailable"""
        with patch.object(SDElementsAPIClient, 'load_library_answers'), \
             patch.object(SDElementsAPIClient, 'get_library_question', return_value=None):
            
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = sample_library_answers
            
            result = client.get_answer_details_from_ids(['A701'])
            
            assert len(result['answers']) == 1
            answer = result['answers'][0]
            # Should extract question from display_text
            assert answer['question_text'] == 'What programming language do you use?'


class TestGetAnswerDetailsFromIdsTool:
    """Tests for the MCP tool get_answer_details_from_ids"""
    
    @pytest.mark.asyncio
    async def test_tool_success(self, sample_library_answers, sample_question_details):
        """Test the MCP tool successfully returns JSON"""
        # Setup mock client with the method we want to test
        mock_client = Mock(spec=SDElementsAPIClient)
        mock_client._library_answers_cache = sample_library_answers
        
        expected_result = {
            'answers': [
                {
                    'id': 'A701',
                    'text': 'Java',
                    'question_id': 'Q100',
                    'question_text': 'What programming language do you use?',
                    'description': 'Java programming language',
                    'question_description': 'Select the primary programming language',
                    'question_format': 'MC',
                    'question_mandatory': True
                }
            ],
            'not_found': []
        }
        mock_client.get_answer_details_from_ids.return_value = expected_result
        
        with patch('sde_mcp_server.tools.surveys.api_client', None), \
             patch('sde_mcp_server.tools.surveys.init_api_client', return_value=mock_client):
            
            # Import the module to get the tool
            import sde_mcp_server.tools.surveys as surveys_module
            
            # Access the underlying function from the FastMCP FunctionTool wrapper
            # FunctionTool has a 'fn' attribute that contains the original function
            tool_func = surveys_module.get_answer_details_from_ids.fn
            
            # Create a mock context
            mock_ctx = Mock(spec=Context)
            
            # Call the underlying function
            result = await tool_func(mock_ctx, ['A701'])
            
            # Verify result is JSON
            parsed = json.loads(result)
            assert 'answers' in parsed
            assert 'not_found' in parsed
            assert len(parsed['answers']) == 1
            assert parsed['answers'][0]['id'] == 'A701'
            
            # Verify API client method was called
            mock_client.get_answer_details_from_ids.assert_called_once_with(['A701'])
    
    @pytest.mark.asyncio
    async def test_tool_multiple_answer_ids(self):
        """Test the MCP tool with multiple answer IDs"""
        mock_client = Mock(spec=SDElementsAPIClient)
        expected_result = {
            'answers': [
                {'id': 'A701', 'text': 'Java', 'question_id': 'Q100', 'question_text': 'What programming language?'},
                {'id': 'A493', 'text': 'PostgreSQL', 'question_id': 'Q200', 'question_text': 'What database?'}
            ],
            'not_found': []
        }
        mock_client.get_answer_details_from_ids.return_value = expected_result
        
        with patch('sde_mcp_server.tools.surveys.api_client', None), \
             patch('sde_mcp_server.tools.surveys.init_api_client', return_value=mock_client):
            
            import sde_mcp_server.tools.surveys as surveys_module
            tool_func = surveys_module.get_answer_details_from_ids.fn
            
            mock_ctx = Mock(spec=Context)
            result = await tool_func(mock_ctx, ['A701', 'A493'])
            
            parsed = json.loads(result)
            assert len(parsed['answers']) == 2
            mock_client.get_answer_details_from_ids.assert_called_once_with(['A701', 'A493'])
    
    @pytest.mark.asyncio
    async def test_tool_with_not_found_answers(self):
        """Test the MCP tool when some answers are not found"""
        mock_client = Mock(spec=SDElementsAPIClient)
        expected_result = {
            'answers': [
                {'id': 'A701', 'text': 'Java', 'question_id': 'Q100', 'question_text': 'What programming language?'}
            ],
            'not_found': ['A999', 'A998']
        }
        mock_client.get_answer_details_from_ids.return_value = expected_result
        
        with patch('sde_mcp_server.tools.surveys.api_client', None), \
             patch('sde_mcp_server.tools.surveys.init_api_client', return_value=mock_client):
            
            import sde_mcp_server.tools.surveys as surveys_module
            tool_func = surveys_module.get_answer_details_from_ids.fn
            
            mock_ctx = Mock(spec=Context)
            result = await tool_func(mock_ctx, ['A701', 'A999', 'A998'])
            
            parsed = json.loads(result)
            assert len(parsed['answers']) == 1
            assert len(parsed['not_found']) == 2
            assert 'A999' in parsed['not_found']
            assert 'A998' in parsed['not_found']


@pytest.mark.unit
class TestAnswerDetailsIntegration:
    """Integration-style tests that verify the full flow"""
    
    def test_full_flow_single_answer(self, sample_library_answers, sample_question_details):
        """Test the full flow from answer ID to question/answer details"""
        with patch.object(SDElementsAPIClient, 'load_library_answers'), \
             patch.object(SDElementsAPIClient, 'get_library_question') as mock_get_question:
            
            client = SDElementsAPIClient(host='https://test.sdelements.com', api_key='test-key')
            client._library_answers_cache = sample_library_answers
            
            def get_question_side_effect(question_id):
                return sample_question_details.get(question_id, {})
            
            mock_get_question.side_effect = get_question_side_effect
            
            # Test the specific use case: "What question and answer is related to answer ID A701"
            result = client.get_answer_details_from_ids(['A701'])
            
            # Verify we can answer the question
            assert len(result['answers']) == 1
            answer = result['answers'][0]
            
            # The answer should contain everything needed to answer the user's question
            assert answer['id'] == 'A701'
            assert answer['text'] == 'Java'
            assert answer['question_text'] == 'What programming language do you use?'
            assert answer['question_id'] == 'Q100'
            
            # Verify question details are included
            assert answer['question_description'] == 'Select the primary programming language'
            assert answer['question_format'] == 'MC'
            assert answer['question_mandatory'] is True

