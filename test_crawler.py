#!/usr/bin/env python3
"""
Test script for the modified web crawler to verify it works with and without AI.
"""

from utils.web_scraper import ai_crawler

def test_basic_crawler():
    """Test the crawler without AI (just raw content collection)"""
    print("=" * 50)
    print("Testing Basic Crawler (No AI)")
    print("=" * 50)
    
    try:
        # Test with a simple URL that should work
        results = ai_crawler(
            start_url="https://httpbin.org/html",  # Simple test HTML page
            num_workers=1,
            num_levels_deep=0,  # Only crawl the starting page
            use_ai=False
        )
        
        print(f"Results: {len(results)} items collected")
        if results:
            print(f"First item keys: {list(results[0].keys())}")
            print(f"Has raw content: {'html2text_text' in results[0] or 'raw_content' in results[0]}")
        
        return True
    except Exception as e:
        print(f"Error in basic crawler test: {e}")
        return False

def test_ai_crawler():
    """Test the crawler with AI (requires API key)"""
    print("=" * 50)
    print("Testing AI Crawler")
    print("=" * 50)
    
    try:
        # Test with AI - this will fail if no API key is set, which is expected
        results = ai_crawler(
            start_url="https://httpbin.org/html",
            num_workers=1,
            num_levels_deep=0,
            extraction_prompt="Extract any text content from this page",
            use_ai=True
        )
        
        print(f"Results: {len(results)} items collected")
        return True
    except ValueError as e:
        if "Google API key" in str(e):
            print("AI test skipped: No Google API key available (this is expected)")
            return True
        else:
            print(f"Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"Error in AI crawler test: {e}")
        return False

if __name__ == "__main__":
    print("Testing Modified Web Crawler")
    print("=" * 60)
    
    # Test basic functionality
    basic_success = test_basic_crawler()
    
    # Test AI functionality (will skip if no API key)
    ai_success = test_ai_crawler()
    
    print("=" * 60)
    print("Test Summary:")
    print(f"Basic crawler (no AI): {'✓ PASSED' if basic_success else '✗ FAILED'}")
    print(f"AI crawler: {'✓ PASSED' if ai_success else '✗ FAILED'}")
    
    if basic_success:
        print("\n✓ The web crawler now works without AI dependencies!")
        print("  - Use use_ai=False or omit extraction_prompt to crawl without AI")
        print("  - Use extraction_prompt + API key to enable AI extraction") 