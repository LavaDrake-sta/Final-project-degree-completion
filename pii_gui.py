"""
PII Detection System - Graphical User Interface
ממשק גרפי למערכת זיהוי והסתרת פרטים אישיים
תואם לתיקון 13 לחוק הגנת הפרטיות
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
from pathlib import Path
from datetime import datetime
import threading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import the full system, fallback to simple detector
try:
    from src.pii_detector_il import IsraeliPIIDetector
    from src.israeli_privacy_law import is_special_sensitivity, get_category_hebrew_name
    from src.anonymizer import PIIAnonymizer, AnonymizationMode
    FULL_SYSTEM = True
except:
    # Use simple detector as fallback
    from run_simple import SimplePIIDetector
    FULL_SYSTEM = False


class PIIDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 מערכת זיהוי פרטים אישיים - PII Detection System")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')

        # Initialize detector
        self.detector = None
        self.anonymizer = None
        self.current_text = ""
        self.current_entities = {}

        # Create UI
        self.create_widgets()

        # Initialize detector in background
        self.init_detector()

    def create_widgets(self):
        """Create all UI widgets"""

        # Top Frame - Title and Logo
        top_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        top_frame.pack(fill=tk.X, padx=0, pady=0)
        top_frame.pack_propagate(False)

        title_label = tk.Label(
            top_frame,
            text="🧠 מערכת זיהוי והסתרת פרטים אישיים",
            font=("Arial", 18, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=10)

        subtitle_label = tk.Label(
            top_frame,
            text="⚖️ תואם לתיקון 13 לחוק הגנת הפרטיות | Compliant with Amendment 13",
            font=("Arial", 10),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        subtitle_label.pack()

        # Main container
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Panel - Input
        left_panel = tk.LabelFrame(
            main_container,
            text="📝 קלט | Input",
            font=("Arial", 12, "bold"),
            bg='white',
            padx=10,
            pady=10
        )
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # File selection
        file_frame = tk.Frame(left_panel, bg='white')
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_label = tk.Label(
            file_frame,
            text="בחר קובץ או הדבק טקסט למטה",
            font=("Arial", 10),
            bg='white',
            fg='#7f8c8d'
        )
        self.file_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            file_frame,
            text="📁 בחר קובץ",
            command=self.select_file,
            bg='#3498db',
            fg='white',
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5,
            cursor='hand2'
        ).pack(side=tk.LEFT)

        # Text input
        text_label = tk.Label(
            left_panel,
            text="טקסט לבדיקה:",
            font=("Arial", 10, "bold"),
            bg='white'
        )
        text_label.pack(anchor=tk.W)

        self.text_input = scrolledtext.ScrolledText(
            left_panel,
            wrap=tk.WORD,
            font=("Arial", 11),
            height=20
        )
        self.text_input.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # Action buttons
        button_frame = tk.Frame(left_panel, bg='white')
        button_frame.pack(fill=tk.X)

        self.detect_btn = tk.Button(
            button_frame,
            text="🔍 זהה פרטים אישיים",
            command=self.detect_pii,
            bg='#27ae60',
            fg='white',
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.detect_btn.pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            button_frame,
            text="🗑️ נקה",
            command=self.clear_all,
            bg='#e74c3c',
            fg='white',
            font=("Arial", 10, "bold"),
            padx=15,
            pady=10,
            cursor='hand2'
        ).pack(side=tk.LEFT)

        # Right Panel - Results
        right_panel = tk.LabelFrame(
            main_container,
            text="📊 תוצאות | Results",
            font=("Arial", 12, "bold"),
            bg='white',
            padx=10,
            pady=10
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Status label
        self.status_label = tk.Label(
            right_panel,
            text="⏳ מוכן לזיהוי...",
            font=("Arial", 10),
            bg='white',
            fg='#7f8c8d'
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 10))

        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            font=("Courier New", 10),
            height=20,
            bg='#ecf0f1'
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Results action buttons
        results_button_frame = tk.Frame(right_panel, bg='white')
        results_button_frame.pack(fill=tk.X)

        self.anonymize_btn = tk.Button(
            results_button_frame,
            text="🔐 הסתר פרטים",
            command=self.anonymize_text,
            bg='#9b59b6',
            fg='white',
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.anonymize_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.save_btn = tk.Button(
            results_button_frame,
            text="💾 שמור דוח",
            command=self.save_report,
            bg='#f39c12',
            fg='white',
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT)

        # Bottom status bar
        self.bottom_status = tk.Label(
            self.root,
            text="מוכן | Ready",
            font=("Arial", 9),
            bg='#34495e',
            fg='white',
            anchor=tk.W,
            padx=10
        )
        self.bottom_status.pack(fill=tk.X, side=tk.BOTTOM)

    def init_detector(self):
        """Initialize PII detector"""
        self.status_label.config(text="⏳ טוען מערכת זיהוי...")
        self.bottom_status.config(text="טוען מודול זיהוי...")

        def load():
            try:
                if FULL_SYSTEM:
                    self.detector = IsraeliPIIDetector(use_ai=False)
                    self.anonymizer = PIIAnonymizer(mode=AnonymizationMode.REPLACE)
                    mode = "מצב Regex מהיר"
                else:
                    self.detector = SimplePIIDetector()
                    mode = "מצב פשוט"

                self.root.after(0, lambda: self.status_label.config(
                    text=f"✅ מערכת מוכנה ({mode})"
                ))
                self.root.after(0, lambda: self.bottom_status.config(
                    text=f"מוכן | {mode}"
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "שגיאה",
                    f"שגיאה בטעינת המערכת:\n{str(e)}"
                ))

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def select_file(self):
        """Select file to analyze"""
        filename = filedialog.askopenfilename(
            title="בחר קובץ",
            filetypes=[
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("Word files", "*.docx"),
                ("PDF files", "*.pdf")
            ]
        )

        if filename:
            try:
                # Try to read as text
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.text_input.delete(1.0, tk.END)
                self.text_input.insert(1.0, content)
                self.file_label.config(
                    text=f"📄 {os.path.basename(filename)}",
                    fg='#27ae60'
                )
                self.bottom_status.config(text=f"נטען: {os.path.basename(filename)}")

            except Exception as e:
                messagebox.showerror(
                    "שגיאה",
                    f"לא ניתן לקרוא את הקובץ:\n{str(e)}\n\nנסה להעתיק ולהדביק את התוכן ידנית."
                )

    def detect_pii(self):
        """Detect PII in text"""
        text = self.text_input.get(1.0, tk.END).strip()

        if not text:
            messagebox.showwarning("אזהרה", "אנא הזן טקסט לבדיקה")
            return

        if not self.detector:
            messagebox.showerror("שגיאה", "המערכת עדיין לא מוכנה. אנא המתן...")
            return

        self.current_text = text
        self.detect_btn.config(state=tk.DISABLED, text="⏳ מזהה...")
        self.status_label.config(text="🔍 מזהה פרטים אישיים...")
        self.bottom_status.config(text="מעבד...")

        def detect():
            try:
                if FULL_SYSTEM:
                    entities = self.detector.detect_pii(text)
                    self.current_entities = entities
                    self.display_results_full(entities)
                else:
                    results = self.detector.detect(text)
                    self.current_entities = results
                    self.display_results_simple(results)

                self.root.after(0, lambda: self.anonymize_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "שגיאה",
                    f"שגיאה בזיהוי:\n{str(e)}"
                ))
            finally:
                self.root.after(0, lambda: self.detect_btn.config(
                    state=tk.NORMAL,
                    text="🔍 זהה פרטים אישיים"
                ))
                self.root.after(0, lambda: self.bottom_status.config(text="הושלם"))

        thread = threading.Thread(target=detect, daemon=True)
        thread.start()

    def display_results_full(self, entities):
        """Display results from full system"""
        self.results_text.delete(1.0, tk.END)

        # Count
        standard_count = 0
        special_count = 0

        for entity_type, entity_list in entities.items():
            if entity_list:
                if is_special_sensitivity(entity_type):
                    special_count += len(entity_list)
                else:
                    standard_count += len(entity_list)

        total = standard_count + special_count

        # Header
        self.results_text.insert(tk.END, "=" * 70 + "\n", 'header')
        self.results_text.insert(tk.END, "📊 תוצאות זיהוי\n", 'header')
        self.results_text.insert(tk.END, "=" * 70 + "\n\n", 'header')

        # Summary
        self.results_text.insert(tk.END, f"סה\"כ נמצאו: {total} פרטים אישיים\n", 'summary')
        self.results_text.insert(tk.END, f"  • פרטים רגילים: {standard_count}\n", 'standard')
        self.results_text.insert(tk.END, f"  • רגישות מיוחדת (תיקון 13): {special_count}\n\n", 'special')

        # Details
        if total > 0:
            self.results_text.insert(tk.END, "-" * 70 + "\n", 'separator')

            for entity_type, entity_list in entities.items():
                if entity_list:
                    is_special = is_special_sensitivity(entity_type)
                    hebrew_name = get_category_hebrew_name(entity_type)

                    icon = "⚠️ " if is_special else "✓ "
                    tag = 'special' if is_special else 'standard'

                    self.results_text.insert(tk.END, f"\n{icon}{hebrew_name} ({entity_type}):\n", tag)
                    self.results_text.insert(tk.END, f"  נמצאו: {len(entity_list)}\n")

                    for i, entity in enumerate(entity_list[:5]):
                        self.results_text.insert(tk.END, f"  {i+1}. '{entity.text}'\n")

                    if len(entity_list) > 5:
                        self.results_text.insert(tk.END, f"  ... ועוד {len(entity_list) - 5}\n")
        else:
            self.results_text.insert(tk.END, "✅ לא נמצאו פרטים אישיים\n", 'good')

        # Configure tags
        self.results_text.tag_config('header', font=('Arial', 12, 'bold'))
        self.results_text.tag_config('summary', font=('Arial', 11, 'bold'))
        self.results_text.tag_config('standard', foreground='#27ae60')
        self.results_text.tag_config('special', foreground='#e74c3c')
        self.results_text.tag_config('good', foreground='#27ae60', font=('Arial', 11, 'bold'))
        self.results_text.tag_config('separator', foreground='#7f8c8d')

        self.status_label.config(
            text=f"✅ הושלם: {total} פרטים ({special_count} רגישים)"
        )

    def display_results_simple(self, results):
        """Display results from simple detector"""
        self.results_text.delete(1.0, tk.END)

        standard = results.get('standard', [])
        special = results.get('special', [])
        total = len(standard) + len(special)

        # Header
        self.results_text.insert(tk.END, "=" * 70 + "\n", 'header')
        self.results_text.insert(tk.END, "📊 תוצאות זיהוי\n", 'header')
        self.results_text.insert(tk.END, "=" * 70 + "\n\n", 'header')

        # Summary
        self.results_text.insert(tk.END, f"סה\"כ נמצאו: {total} פרטים אישיים\n", 'summary')
        self.results_text.insert(tk.END, f"  • פרטים רגילים: {len(standard)}\n", 'standard')
        self.results_text.insert(tk.END, f"  • רגישות מיוחדת (תיקון 13): {len(special)}\n\n", 'special')

        # Standard items
        if standard:
            self.results_text.insert(tk.END, "✓ פרטים רגילים:\n", 'standard')
            seen = set()
            for item in standard:
                key = f"{item.type}:{item.text}"
                if key not in seen:
                    self.results_text.insert(tk.END, f"  • {item.type}: {item.text}\n")
                    seen.add(key)
            self.results_text.insert(tk.END, "\n")

        # Special items
        if special:
            self.results_text.insert(tk.END, "⚠️  מידע רגיש (תיקון 13):\n", 'special')
            seen = set()
            for item in special:
                key = f"{item.type}:{item.text[:30]}"
                if key not in seen:
                    preview = item.text[:60] + "..." if len(item.text) > 60 else item.text
                    self.results_text.insert(tk.END, f"  • {item.type}: {preview}\n")
                    seen.add(key)

        # Configure tags
        self.results_text.tag_config('header', font=('Arial', 12, 'bold'))
        self.results_text.tag_config('summary', font=('Arial', 11, 'bold'))
        self.results_text.tag_config('standard', foreground='#27ae60')
        self.results_text.tag_config('special', foreground='#e74c3c')

        self.status_label.config(
            text=f"✅ הושלם: {total} פרטים ({len(special)} רגישים)"
        )

    def anonymize_text(self):
        """Anonymize detected PII"""
        if not self.current_text or not self.current_entities:
            messagebox.showwarning("אזהרה", "אנא הרץ זיהוי תחילה")
            return

        try:
            if FULL_SYSTEM and self.anonymizer:
                anonymized = self.anonymizer.anonymize(self.current_text, self.current_entities)
            else:
                # Simple anonymization
                anonymized = self.current_text
                # Simple replacement - just for demo
                messagebox.showinfo(
                    "הסתרה",
                    "מצב הסתרה פשוט זמין.\nהשתמש במערכת המלאה להסתרה מתקדמת."
                )
                return

            # Show in new window
            self.show_anonymized_window(anonymized)

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בהסתרה:\n{str(e)}")

    def show_anonymized_window(self, anonymized_text):
        """Show anonymized text in new window"""
        window = tk.Toplevel(self.root)
        window.title("🔐 טקסט מוסתר")
        window.geometry("800x600")

        tk.Label(
            window,
            text="טקסט עם פרטים מוסתרים:",
            font=("Arial", 12, "bold")
        ).pack(padx=10, pady=10)

        text_widget = scrolledtext.ScrolledText(
            window,
            wrap=tk.WORD,
            font=("Arial", 11)
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        text_widget.insert(1.0, anonymized_text)

        def copy_text():
            window.clipboard_clear()
            window.clipboard_append(anonymized_text)
            messagebox.showinfo("הצלחה", "הטקסט הועתק ללוח")

        button_frame = tk.Frame(window)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="📋 העתק",
            command=copy_text,
            bg='#3498db',
            fg='white',
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="סגור",
            command=window.destroy,
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

    def save_report(self):
        """Save detection report"""
        if not self.current_entities:
            messagebox.showwarning("אזהרה", "אין תוצאות לשמירה")
            return

        filename = filedialog.asksaveasfilename(
            title="שמור דוח",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            initialfile=f"pii_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.get(1.0, tk.END))

                messagebox.showinfo("הצלחה", f"הדוח נשמר בהצלחה:\n{filename}")
                self.bottom_status.config(text=f"נשמר: {os.path.basename(filename)}")

            except Exception as e:
                messagebox.showerror("שגיאה", f"שגיאה בשמירה:\n{str(e)}")

    def clear_all(self):
        """Clear all inputs and results"""
        self.text_input.delete(1.0, tk.END)
        self.results_text.delete(1.0, tk.END)
        self.current_text = ""
        self.current_entities = {}
        self.file_label.config(text="בחר קובץ או הדבק טקסט למטה", fg='#7f8c8d')
        self.status_label.config(text="⏳ מוכן לזיהוי...")
        self.anonymize_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.bottom_status.config(text="מוכן | Ready")


def main():
    root = tk.Tk()
    app = PIIDetectorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
