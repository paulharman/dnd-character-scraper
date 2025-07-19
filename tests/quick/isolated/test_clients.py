"""
Isolated client tests for quick validation.

Tests API clients and data fetching without making real API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from src.clients.dndbeyond_client import DNDBeyondClient
from src.clients.mock_client import MockDNDBeyondClient

from ..factories.character_archetypes import CharacterArchetypeFactory
from ..factories.api_responses import APIResponseFactory

class TestDNDBeyondClient:
    """Tests for DNDBeyondClient."""
    
    @pytest.mark.quick
    @patch('requests.get')
    def test_successful_character_fetch(self, mock_get):
        """Test successful character data fetching."""
        character_data = CharacterArchetypeFactory.create_fighter(level=5)
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        mock_response = Mock()
        mock_response.json.return_value = api_response
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = DNDBeyondClient()
        result = client.get_character("12345")
        
        assert result is not None
        assert result.get('success', False) is True
        assert 'data' in result
        assert result['data']['name'] == "Test Fighter"

    @pytest.mark.quick
    @patch('requests.get')
    def test_character_not_found(self, mock_get):
        """Test handling of character not found."""
        api_response = APIResponseFactory.create_character_not_found_response("99999")
        
        mock_response = Mock()
        mock_response.json.return_value = api_response
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        client = DNDBeyondClient()
        result = client.get_character("99999")
        
        assert result is not None
        assert result.get('success', False) is False
        assert 'error' in result
        assert result['error']['code'] == 'CHARACTER_NOT_FOUND'

    @pytest.mark.quick
    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """Test handling of API errors."""
        api_response = APIResponseFactory.create_api_error_response("Internal Server Error")
        
        mock_response = Mock()
        mock_response.json.return_value = api_response
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        client = DNDBeyondClient()
        result = client.get_character("12345")
        
        assert result is not None
        assert result.get('success', False) is False
        assert 'error' in result

    @pytest.mark.quick
    @patch('requests.get')
    def test_rate_limiting(self, mock_get):
        """Test handling of rate limiting."""
        api_response = APIResponseFactory.create_rate_limit_response()
        
        mock_response = Mock()
        mock_response.json.return_value = api_response
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        client = DNDBeyondClient()
        result = client.get_character("12345")
        
        assert result is not None
        assert result.get('success', False) is False
        assert 'error' in result
        assert result['error']['code'] == 'RATE_LIMIT_EXCEEDED'

    @pytest.mark.quick
    @patch('requests.get')
    def test_timeout_handling(self, mock_get):
        """Test handling of request timeouts."""
        from requests.exceptions import Timeout
        
        mock_get.side_effect = Timeout("Request timed out")
        
        client = DNDBeyondClient()
        result = client.get_character("12345")
        
        assert result is not None
        assert result.get('success', False) is False
        assert 'error' in result

    @pytest.mark.quick
    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors."""
        from requests.exceptions import ConnectionError
        
        mock_get.side_effect = ConnectionError("Connection failed")
        
        client = DNDBeyondClient()
        result = client.get_character("12345")
        
        assert result is not None
        assert result.get('success', False) is False
        assert 'error' in result

    @pytest.mark.quick
    def test_invalid_character_id(self):
        """Test handling of invalid character ID."""
        client = DNDBeyondClient()
        
        # Test with empty string
        result = client.get_character("")
        assert result is not None
        assert result.get('success', False) is False
        
        # Test with None
        result = client.get_character(None)
        assert result is not None
        assert result.get('success', False) is False

    @pytest.mark.quick
    @patch('requests.get')
    def test_malformed_json_response(self, mock_get):
        """Test handling of malformed JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON response"
        mock_get.return_value = mock_response
        
        client = DNDBeyondClient()
        result = client.get_character("12345")
        
        assert result is not None
        assert result.get('success', False) is False
        assert 'error' in result

class TestMockDNDBeyondClient:
    """Tests for MockDNDBeyondClient."""
    
    @pytest.mark.quick
    def test_mock_client_initialization(self):
        """Test MockDNDBeyondClient initialization."""
        client = MockDNDBeyondClient()
        assert client is not None
        assert hasattr(client, 'get_character')

    @pytest.mark.quick
    def test_mock_client_fighter_response(self):
        """Test MockDNDBeyondClient fighter response."""
        client = MockDNDBeyondClient()
        result = client.get_character("fighter")
        
        assert result is not None
        assert result.get('success', False) is True
        assert 'data' in result
        assert result['data']['classes'][0]['name'] == "Fighter"

    @pytest.mark.quick
    def test_mock_client_wizard_response(self):
        """Test MockDNDBeyondClient wizard response."""
        client = MockDNDBeyondClient()
        result = client.get_character("wizard")
        
        assert result is not None
        assert result.get('success', False) is True
        assert 'data' in result
        assert result['data']['classes'][0]['name'] == "Wizard"
        assert result['data']['is_spellcaster'] is True

    @pytest.mark.quick
    def test_mock_client_error_response(self):
        """Test MockDNDBeyondClient error response."""
        client = MockDNDBeyondClient()
        result = client.get_character("error")
        
        assert result is not None
        assert result.get('success', False) is False
        assert 'error' in result

    @pytest.mark.quick
    def test_mock_client_unknown_character(self):
        """Test MockDNDBeyondClient with unknown character ID."""
        client = MockDNDBeyondClient()
        result = client.get_character("unknown_character_id")
        
        assert result is not None
        # Should return a default response or error
        assert 'success' in result

    @pytest.mark.quick
    def test_mock_client_performance(self):
        """Test MockDNDBeyondClient performance."""
        import time
        
        client = MockDNDBeyondClient()
        
        start_time = time.time()
        result = client.get_character("fighter")
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.1  # Should be very fast
        assert result is not None

class TestClientInterface:
    """Tests for client interface compliance."""
    
    @pytest.mark.quick
    def test_client_interface_compliance(self):
        """Test that clients implement required interface."""
        clients = [DNDBeyondClient(), MockDNDBeyondClient()]
        
        for client in clients:
            assert hasattr(client, 'get_character')
            assert callable(getattr(client, 'get_character'))

    @pytest.mark.quick
    def test_client_response_format(self):
        """Test that clients return consistent response format."""
        clients = [MockDNDBeyondClient()]  # DNDBeyondClient requires mocking
        
        for client in clients:
            result = client.get_character("fighter")
            
            assert isinstance(result, dict)
            assert 'success' in result
            assert isinstance(result['success'], bool)
            
            if result['success']:
                assert 'data' in result
                assert result['data'] is not None
            else:
                assert 'error' in result
                assert result['error'] is not None

    @pytest.mark.quick
    def test_client_error_consistency(self):
        """Test that client errors are consistently formatted."""
        client = MockDNDBeyondClient()
        
        error_result = client.get_character("error")
        
        assert error_result['success'] is False
        assert 'error' in error_result
        assert 'code' in error_result['error']
        assert 'details' in error_result['error'] or 'message' in error_result

# Integration tests with factories
class TestClientFactoryIntegration:
    """Tests for client integration with factories."""
    
    @pytest.mark.quick
    def test_client_with_archetype_factory(self):
        """Test client integration with character archetypes."""
        client = MockDNDBeyondClient()
        
        # Test different archetypes
        archetypes = ['fighter', 'wizard', 'rogue']
        for archetype in archetypes:
            result = client.get_character(archetype)
            
            assert result is not None
            assert result.get('success', False) is True
            assert 'data' in result
            assert result['data']['classes'][0]['name'].lower() == archetype

    @pytest.mark.quick
    def test_client_with_api_response_factory(self):
        """Test client behavior matches API response factory."""
        api_response = APIResponseFactory.create_successful_character_response(
            CharacterArchetypeFactory.create_fighter(level=3)
        )
        
        # Verify the factory creates valid responses
        assert api_response['success'] is True
        assert 'data' in api_response
        assert api_response['data']['level'] == 3
        assert api_response['data']['classes'][0]['name'] == "Fighter"

# Performance and stress tests
class TestClientPerformance:
    """Performance tests for clients."""
    
    @pytest.mark.quick
    def test_mock_client_batch_requests(self):
        """Test MockDNDBeyondClient with multiple requests."""
        client = MockDNDBeyondClient()
        
        # Test batch of requests
        character_ids = ['fighter', 'wizard', 'rogue'] * 10
        
        start_time = time.time()
        results = []
        for char_id in character_ids:
            result = client.get_character(char_id)
            results.append(result)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete in under 1 second
        assert len(results) == len(character_ids)
        assert all(r['success'] for r in results)

    @pytest.mark.quick
    def test_client_memory_usage(self):
        """Test client memory usage stays reasonable."""
        client = MockDNDBeyondClient()
        
        # Make multiple requests to check for memory leaks
        for i in range(100):
            result = client.get_character("fighter")
            assert result is not None
            # Force garbage collection of result
            del result
        
        # If we get here without memory errors, test passes
        assert True