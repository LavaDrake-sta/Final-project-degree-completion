"""
PII Detection System - Main Entry Point
פרויקט גמר - זיהוי מידע אישי רגיש
"""

import sys
import os

# הוספת התיקייה הנוכחית לנתיב
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.append(src_dir)

def main():
    """פונקציה ראשית"""
    print("🔒 מערכת זיהוי מידע אישי רגיש")
    print("=" * 40)

    # בדיקה בסיסית
    try:
        # נסה לייבא מהתיקייה src
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

        from detectors.basic_detector import BasicPIIDetector
        print("✅ מודול זיהוי נטען בהצלחה")

        # בדיקה מהירה
        detector = BasicPIIDetector()
        test_text = "שלום, התעודת זהות שלי היא 123456789"
        results = detector.analyze_text(test_text)

        print(f"✅ בדיקה מהירה: {results['summary']}")

    except ImportError as e:
        print(f"❌ שגיאה בטעינת המודול: {e}")
        print("💡 פתרון: בדוק שהקובץ basic_detector.py נמצא בתיקייה src/detectors/")
        return
    except Exception as e:
        print(f"❌ שגיאה כללית: {e}")
        return

    print("\n🚀 אפשרויות הפעלה:")
    print("1. הפעל דמו: python main.py demo")
    print("2. הפעל בדיקות: python main.py test")
    print("3. ממשק משתמש: streamlit run streamlit_app.py")

    # טיפול בארגומנטים
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            run_demo()
        elif sys.argv[1] == "test":
            run_tests()

def run_demo():
    """הפעלת דמו מהיר"""
    try:
        from src.detectors.basic_detector import BasicPIIDetector

        print("\n🎯 דמו - זיהוי מידע רגיש")
        print("-" * 30)

        detector = BasicPIIDetector()

        test_cases = [
            "שלום, אני יוסי כהן ות.ז שלי 123456789",
            "התקשר אליי ב 052-1234567 או david@gmail.com",
            "יש לי חוב של 50,000 שקל בבנק",
            "הלכתי לרופא בגלל מחלה כרונית"
        ]

        for i, text in enumerate(test_cases, 1):
            print(f"\n{i}. טקסט: '{text}'")
            results = detector.analyze_text(text)
            print(f"   תוצאה: {results['summary']}")
            print(f"   רגישות: {results['overall_sensitivity'].name}")

            # הצגת פירוט הממצאים
            if results['matches']:
                for match in results['matches']:
                    print(f"   🔍 נמצא: '{match.text}' (סוג: {match.category})")

    except Exception as e:
        print(f"❌ שגיאה בדמו: {e}")

def run_tests():
    """הפעלת בדיקות בסיסיות"""
    print("\n🧪 מפעיל בדיקות...")
    try:
        from src.detectors.basic_detector import BasicPIIDetector
        detector = BasicPIIDetector()

        # בדיקה 1: ת.ז
        result1 = detector.analyze_text("123456789")
        assert result1['total_matches'] > 0, "לא זוהתה תעודת זהות"
        print("✅ בדיקת ת.ז עברה")

        # בדיקה 2: טלפון
        result2 = detector.analyze_text("052-1234567")
        assert result2['total_matches'] > 0, "לא זוהה מספר טלפון"
        print("✅ בדיקת טלפון עברה")

        # בדיקה 3: אימייל
        result3 = detector.analyze_text("test@gmail.com")
        assert result3['total_matches'] > 0, "לא זוהה אימייל"
        print("✅ בדיקת אימייל עברה")

        print("🎉 כל הבדיקות עברו בהצלחה!")

    except Exception as e:
        print(f"❌ בדיקות נכשלו: {e}")

if __name__ == "__main__":
    main()