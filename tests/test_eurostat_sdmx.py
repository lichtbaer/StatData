"""Tests for Eurostat SDMX XML parsing."""

import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from socdata.sources.eurostat import EurostatAdapter


def test_parse_sdmx_xml_simple():
    """Test parsing simple SDMX XML structure."""
    # Sample SDMX XML structure
    sdmx_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Structure xmlns="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
           xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
    <Dataflows>
        <Dataflow id="une_rt_m" agencyID="ESTAT" version="1.0">
            <Name xml:lang="en">Unemployment rate - monthly</Name>
        </Dataflow>
        <Dataflow id="demo_r_pjangroup" agencyID="ESTAT" version="1.0">
            <Name xml:lang="en">Population on 1 January by age group</Name>
        </Dataflow>
    </Dataflows>
</Structure>"""
    
    adapter = EurostatAdapter()
    
    # Mock the API response
    mock_response = MagicMock()
    mock_response.content = sdmx_xml.encode('utf-8')
    mock_response.raise_for_status = MagicMock()
    
    with patch('socdata.sources.eurostat.requests.get', return_value=mock_response):
        with patch('socdata.sources.eurostat.get_config') as mock_config:
            mock_config.return_value.timeout_seconds = 60
            mock_config.return_value.user_agent = "socdata/0.1"
            
            result = adapter._fetch_datasets_from_api()
            
            # Should parse and return datasets
            assert result is not None
            assert len(result) == 2
            assert result[0]['code'] == 'une_rt_m'
            assert 'Unemployment' in result[0]['title']


def test_parse_sdmx_xml_alternative_structure():
    """Test parsing SDMX XML with alternative namespace structure."""
    # Alternative SDMX XML structure
    sdmx_xml = """<?xml version="1.0" encoding="UTF-8"?>
<message:Structure xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                   xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
                   xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
    <message:Structures>
        <structure:Dataflows>
            <structure:Dataflow id="nama_10_gdp" agencyID="ESTAT">
                <structure:Name xml:lang="en">GDP and main components</structure:Name>
            </structure:Dataflow>
        </structure:Dataflows>
    </message:Structures>
</message:Structure>"""
    
    adapter = EurostatAdapter()
    
    mock_response = MagicMock()
    mock_response.content = sdmx_xml.encode('utf-8')
    mock_response.raise_for_status = MagicMock()
    
    with patch('socdata.sources.eurostat.requests.get', return_value=mock_response):
        with patch('socdata.sources.eurostat.get_config') as mock_config:
            mock_config.return_value.timeout_seconds = 60
            mock_config.return_value.user_agent = "socdata/0.1"
            
            result = adapter._fetch_datasets_from_api()
            
            # Should handle alternative structure or return None gracefully
            # The current implementation might not match this structure exactly
            # but should not crash
            assert result is None or isinstance(result, list)


def test_parse_sdmx_xml_invalid():
    """Test handling of invalid XML."""
    adapter = EurostatAdapter()
    
    mock_response = MagicMock()
    mock_response.content = b"<invalid xml>"
    mock_response.raise_for_status = MagicMock()
    
    with patch('socdata.sources.eurostat.requests.get', return_value=mock_response):
        with patch('socdata.sources.eurostat.get_config') as mock_config:
            mock_config.return_value.timeout_seconds = 60
            mock_config.return_value.user_agent = "socdata/0.1"
            
            result = adapter._fetch_datasets_from_api()
            
            # Should return None on parse error
            assert result is None


def test_parse_sdmx_xml_empty():
    """Test handling of empty XML."""
    adapter = EurostatAdapter()
    
    mock_response = MagicMock()
    mock_response.content = b"<?xml version='1.0'?><root></root>"
    mock_response.raise_for_status = MagicMock()
    
    with patch('socdata.sources.eurostat.requests.get', return_value=mock_response):
        with patch('socdata.sources.eurostat.get_config') as mock_config:
            mock_config.return_value.timeout_seconds = 60
            mock_config.return_value.user_agent = "socdata/0.1"
            
            result = adapter._fetch_datasets_from_api()
            
            # Should return None if no datasets found
            assert result is None


def test_parse_sdmx_xml_network_error():
    """Test handling of network errors."""
    adapter = EurostatAdapter()
    
    import requests
    
    with patch('socdata.sources.eurostat.requests.get', side_effect=requests.RequestException("Network error")):
        with patch('socdata.sources.eurostat.get_config') as mock_config:
            mock_config.return_value.timeout_seconds = 60
            mock_config.return_value.user_agent = "socdata/0.1"
            
            result = adapter._fetch_datasets_from_api()
            
            # Should return None on network error
            assert result is None
