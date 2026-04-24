import json
import sys
import os

# Add src to path to allow importing pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), 'PII_Detection_System', 'src'))

try:
    from pipeline import PIIPipeline
    print("✅ All modules loaded successfully!")
    
    # Test text
    test_text = "שלום שמי רועי ומספר תעודת הזהות שלי הוא 123456789. הכתובת שלי היא רחוב הרצל 5 תל אביב ויש לי טלפון 052-1234567."
    
    pipeline = PIIPipeline()
    
    # Simulate a file process by directly calling detector and decision engine
    print("🔍 Testing PII Detector...")
    analyzer_results = pipeline.detector.analyzer.analyze(text=test_text, entities=[], language="en")
    
    extracted_entities = []
    for res in analyzer_results:
        extracted_entities.append({
            "entity_type": res.entity_type,
            "start": res.start,
            "end": res.end,
            "score": res.score,
            "text": test_text[res.start:res.end]
        })
    extracted_entities = sorted(extracted_entities, key=lambda x: x["start"])
    
    print("\nEntities detected:")
    for ent in extracted_entities:
        print(f"  - {ent['entity_type']}: {ent['text']} (score: {ent['score']})")
        
    print("\nRisk Evaluation:")
    eval_res = pipeline.decision_engine.evaluate(extracted_entities)
    print(json.dumps(eval_res, indent=2))
    
    print("\nAnonymized Text:")
    anonymized = pipeline.detector.anonymize(test_text, analyzer_results)
    print(anonymized)
    
except Exception as e:
    print(f"❌ Error during test: {e}")
