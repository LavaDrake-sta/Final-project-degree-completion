"""
Main Application
PII Detection and Anonymization System
Compliant with Israeli Privacy Protection Law - Amendment 13 (2024)
"""

import sys
import os
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loaders import FileLoader, load_all_files
from src.pii_detector_il import IsraeliPIIDetector
from src.anonymizer import PIIAnonymizer, AnonymizationMode
from src.report import ReportGenerator
from src.israeli_privacy_law import get_category_hebrew_name, is_special_sensitivity


def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         🧠 מערכת זיהוי והסתרת פרטים אישיים (PII)              ║
    ║              AI-Powered PII Detection System                  ║
    ║                                                               ║
    ║   ⚖️  תואם לתיקון 13 לחוק הגנת הפרטיות, התשפ"ד-2024          ║
    ║      Compliant with Privacy Protection Law Amendment 13       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main application entry point"""

    print_banner()

    # Configuration
    INPUT_DIR = "data/input"
    OUTPUT_DIR = "data/output"
    ANONYMIZED_DIR = "data/output/anonymized"

    # Create directories if they don't exist
    Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(ANONYMIZED_DIR).mkdir(parents=True, exist_ok=True)

    print("\n📋 הגדרות:")
    print(f"   תיקיית קלט: {INPUT_DIR}")
    print(f"   תיקיית פלט: {OUTPUT_DIR}")
    print()

    # Step 1: Load files
    print("=" * 70)
    print("שלב 1: טעינת קבצים")
    print("=" * 70)

    try:
        loader = FileLoader()
        files_data = load_all_files(INPUT_DIR, loader)

        if not files_data:
            print("\n⚠️  לא נמצאו קבצים לעיבוד!")
            print(f"   אנא הוסף קבצים (PDF, DOCX, תמונות) לתיקייה: {INPUT_DIR}")
            return

        print(f"\n✓ נטענו {len(files_data)} קבצים בהצלחה\n")

    except Exception as e:
        print(f"\n❌ שגיאה בטעינת קבצים: {e}")
        return

    # Step 2: Initialize AI detector
    print("=" * 70)
    print("שלב 2: אתחול מודלי AI (תואם תיקון 13)")
    print("=" * 70)

    try:
        detector = IsraeliPIIDetector(use_ai=True)
        print()
    except Exception as e:
        print(f"\n⚠️  שגיאה באתחול AI: {e}")
        print("   ממשיך עם זיהוי מבוסס Regex בלבד...\n")
        detector = IsraeliPIIDetector(use_ai=False)

    # Step 3: Detect PII
    print("=" * 70)
    print("שלב 3: זיהוי פרטים אישיים")
    print("=" * 70)
    print()

    results = {}

    for filename, file_info in tqdm(files_data.items(), desc="מעבד קבצים"):
        try:
            text = file_info['text']

            if not text or len(text.strip()) == 0:
                results[filename] = {
                    'file_type': file_info['file_type'],
                    'status': 'ריק',
                    'entities': {}
                }
                continue

            # Detect PII
            entities = detector.detect_pii(text)

            # Store results
            results[filename] = {
                'file_type': file_info['file_type'],
                'status': 'בוצע',
                'text': text,
                'entities': entities
            }

            # Print summary with sensitivity breakdown
            total_pii = sum(len(elist) for elist in entities.values())
            special_count = sum(
                len(elist) for etype, elist in entities.items()
                if is_special_sensitivity(etype)
            )

            if total_pii > 0:
                print(f"  📄 {filename}: נמצאו {total_pii} פרטים אישיים", end="")
                if special_count > 0:
                    print(f" (כולל {special_count} בעלי רגישות מיוחדת)")
                else:
                    print()
            else:
                print(f"  ✓ {filename}: לא נמצאו פרטים אישיים")

        except Exception as e:
            print(f"  ❌ {filename}: שגיאה - {e}")
            results[filename] = {
                'file_type': file_info['file_type'],
                'status': f'שגיאה: {e}',
                'entities': {}
            }

    print()

    # Step 4: Anonymize texts
    print("=" * 70)
    print("שלב 4: הסתרת פרטים אישיים")
    print("=" * 70)
    print()

    anonymizer = PIIAnonymizer(mode=AnonymizationMode.REPLACE)

    for filename, result in results.items():
        if 'text' in result and 'entities' in result:
            entities = result['entities']
            total_pii = sum(len(elist) for elist in entities.values())

            if total_pii > 0:
                try:
                    # Anonymize text
                    anonymized_text = anonymizer.anonymize(
                        result['text'],
                        entities
                    )

                    # Save anonymized version
                    output_path = Path(ANONYMIZED_DIR) / f"{Path(filename).stem}_anonymized.txt"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(anonymized_text)

                    result['anonymized_text'] = anonymized_text
                    result['anonymized_file'] = str(output_path)

                    print(f"  ✓ {filename}: הוסתר ונשמר")

                except Exception as e:
                    print(f"  ❌ {filename}: שגיאה בהסתרה - {e}")

    print()

    # Step 5: Generate reports
    print("=" * 70)
    print("שלב 5: יצירת דוחות")
    print("=" * 70)
    print()

    try:
        report_gen = ReportGenerator(output_dir=OUTPUT_DIR)

        # Generate Excel report
        excel_path = report_gen.generate_excel_report(results)

        # Generate text report
        text_path = report_gen.save_text_report(results)

        print()

    except Exception as e:
        print(f"❌ שגיאה ביצירת דוחות: {e}")

    # Summary
    print("=" * 70)
    print("סיכום")
    print("=" * 70)

    total_files = len(results)
    files_with_pii = sum(
        1 for r in results.values()
        if 'entities' in r and sum(len(elist) for elist in r['entities'].values()) > 0
    )
    total_pii_items = sum(
        sum(len(elist) for elist in r['entities'].values())
        for r in results.values()
        if 'entities' in r
    )

    # Count specially sensitive items
    total_special_items = sum(
        sum(len(elist) for etype, elist in r['entities'].items() if is_special_sensitivity(etype))
        for r in results.values()
        if 'entities' in r
    )

    print(f"\n   📊 סה\"כ קבצים שעובדו: {total_files}")
    print(f"   🔍 קבצים עם פרטים אישיים: {files_with_pii}")
    print(f"   🔐 סה\"כ פרטים אישיים שזוהו: {total_pii_items}")
    print(f"   ⚠️  מתוכם בעלי רגישות מיוחדת (תיקון 13): {total_special_items}")

    if files_with_pii > 0:
        print(f"\n   📁 קבצים מוסתרים נשמרו ב: {ANONYMIZED_DIR}")

    print(f"\n   📈 דוחות נוצרו בתיקייה: {OUTPUT_DIR}")
    print()

    print("=" * 70)
    print("✨ העיבוד הושלם בהצלחה!")
    print("⚖️  המערכת תואמת לתיקון 13 לחוק הגנת הפרטיות")
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  התוכנית הופסקה על ידי המשתמש")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ שגיאה קריטית: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
