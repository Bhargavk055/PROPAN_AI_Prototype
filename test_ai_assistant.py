"""Test script for the AI assistant module."""

import os
from propan_parser import parse_propan_out
from analysis import load_p4119_results, get_condition, compare_conditions
from ai_assistant import is_ai_configured, build_analysis_context, ask_ai

def main():
    print("Testing AI Assistant Module...")
    
    # Temporarily remove API keys from environment to test fallback
    original_openai = os.environ.pop("OPENAI_API_KEY", None)
    original_gemini = os.environ.pop("GEMINI_API_KEY", None)
    
    # Test 1: is_ai_configured works
    configured = is_ai_configured()
    assert configured is False, "Expected AI to be unconfigured"
    print("TEST 1 PASS: is_ai_configured() correctly reports missing key.")
    
    # Test 2: context generation works
    df, _, _ = load_p4119_results()
    cond = get_condition(df, 0.7)
    comp = compare_conditions(df, 0.5, 0.7)
    
    context = build_analysis_context(df, 0.7, cond, comp)
    assert "P4119" in context
    assert "J = 0.700" in context
    assert "USER IS COMPARING TWO CONDITIONS" in context
    print("TEST 2 PASS: Context generated successfully.")
    
    # Test 3: ask_ai fallback without API key
    response = ask_ai("What happens as J increases?", context)
    assert "AI assistant is not configured" in response
    print("TEST 3 PASS: ask_ai handles missing API key gracefully.")
    
    # Restore key if it existed
    if original_openai:
        os.environ["OPENAI_API_KEY"] = original_openai
    if original_gemini:
        os.environ["GEMINI_API_KEY"] = original_gemini
        
    print("\nALL AI TESTS PASSED")

if __name__ == "__main__":
    main()
