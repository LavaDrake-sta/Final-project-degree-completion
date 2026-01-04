"""
יצירת תמונות באנגלית - פתרון מהיר לבעיית ה-OCR
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_simple_english_images():
    """יצירת תמונות פשוטות באנגלית שה-OCR יקרא בקלות"""

    test_dir = "data/test_images"
    os.makedirs(test_dir, exist_ok=True)

    # תמונות פשוטות באנגלית
    simple_docs = [
        {
            'filename': 'simple_id.png',
            'lines': [
                'ID CARD',
                '',
                'Name: John Cohen',
                'ID Number: 123456789',
                'Phone: 052-1234567',
                'Email: john@gmail.com'
            ]
        },
        {
            'filename': 'simple_bank.png',
            'lines': [
                'BANK STATEMENT',
                '',
                'Account Holder: David Rosen',
                'ID: 555666777',
                'Account: 1234567890',
                'Phone: 050-9876543'
            ]
        },
        {
            'filename': 'simple_medical.png',
            'lines': [
                'MEDICAL FORM',
                '',
                'Patient: Sarah Levi',
                'ID: 987654321',
                'Doctor: Dr. Abraham',
                'Phone: 03-1234567'
            ]
        },
        {
            'filename': 'simple_contact.png',
            'lines': [
                'CONTACT INFO',
                '',
                'Anna Mizrahi',
                'Mobile: 054-9876543',
                'Email: anna@company.co.il',
                'Address: 88 Ben Gurion St'
            ]
        },
        {
            'filename': 'simple_credit.png',
            'lines': [
                'CREDIT CARD',
                '',
                'Bank Leumi',
                '4580 1234 5678 9012',
                'Rachel Goldman',
                'Expires: 12/28'
            ]
        }
    ]

    created_files = []

    for doc in simple_docs:
        try:
            img = create_clean_english_image(doc['lines'])
            filepath = os.path.join(test_dir, doc['filename'])
            img.save(filepath)
            created_files.append(filepath)
            print(f"✅ Created: {doc['filename']}")
        except Exception as e:
            print(f"❌ Error: {e}")

    return created_files

def create_clean_english_image(lines):
    """יצירת תמונה נקייה באנגלית"""

    # הגדרות
    width, height = 600, 400
    background = (255, 255, 255)  # לבן
    text_color = (0, 0, 0)        # שחור

    # יצירת תמונה
    img = Image.new('RGB', (width, height), background)
    draw = ImageDraw.Draw(img)

    # פונט
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        title_font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
        title_font = font

    # כתיבת הטקסט
    y = 40
    for i, line in enumerate(lines):
        if line.strip():
            # כותרת ראשונה יותר גדולה
            current_font = title_font if i == 0 else font
            draw.text((30, y), line, fill=text_color, font=current_font)
        y += 35

    # מסגרת
    draw.rectangle([(10, 10), (width-10, height-10)], outline=(100, 100, 100), width=2)

    return img

def create_numbers_only_test():
    """תמונה עם מספרים בלבד - הכי קל ל-OCR"""

    lines = [
        'TEST NUMBERS',
        '',
        '123456789',
        '052-1234567',
        '03-9876543',
        '4580-1234-5678-9012'
    ]

    img = create_clean_english_image(lines)
    filepath = "data/test_images/numbers_only.png"
    img.save(filepath)
    print(f"✅ Created numbers test: numbers_only.png")
    return filepath

def create_mixed_test():
    """תמונה מעורבת - טקסט ומספרים"""

    lines = [
        'PERSONAL DATA',
        '',
        'Name: Jacob Israeli',
        'ID: 123456789',
        'Phone: 050-1234567',
        'Email: jacob@email.com',
        'Account: 9876543210'
    ]

    img = create_clean_english_image(lines)
    filepath = "data/test_images/mixed_test.png"
    img.save(filepath)
    print(f"✅ Created mixed test: mixed_test.png")
    return filepath

if __name__ == "__main__":
    print("🖼️ Creating simple English test images")
    print("=" * 40)

    # יצירת תמונות פשוטות
    created = create_simple_english_images()

    # תמונות נוספות לבדיקה
    numbers_file = create_numbers_only_test()
    mixed_file = create_mixed_test()

    created.extend([numbers_file, mixed_file])

    print(f"\n✅ Created {len(created)} test images:")
    for file in created:
        print(f"   📄 {file}")

    print(f"\n🚀 Now test with OCR:")
    print(f"   streamlit run src/ui/streamlit_app.py")

    print(f"\n💡 These images should work much better with OCR!")
    print(f"   All text is left-to-right English")
    print(f"   Clear fonts and good contrast")