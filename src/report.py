"""
Report Generator Module - Israeli Privacy Law Compliant
Creates detailed reports of PII detection results
Compliant with Privacy Protection Law Amendment 13 (2024)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from .pii_detector_il import PIIEntity
from .israeli_privacy_law import (
    get_category_hebrew_name,
    is_special_sensitivity,
    ISRAELI_PRIVACY_CATEGORIES
)


class ReportGenerator:
    """Generate reports from PII detection results"""

    def __init__(self, output_dir: str = "data/output"):
        """
        Initialize report generator

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_excel_report(
        self,
        results: Dict[str, Dict],
        output_filename: str = None
    ) -> str:
        """
        Generate comprehensive Excel report

        Args:
            results: Detection results for each file
            output_filename: Custom output filename

        Returns:
            Path to generated report
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"pii_report_{timestamp}.xlsx"

        output_path = self.output_dir / output_filename

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Summary
            summary_df = self._create_summary_dataframe(results)
            summary_df.to_excel(writer, sheet_name='סיכום', index=False)

            # Sheet 2: Detailed findings
            details_df = self._create_details_dataframe(results)
            details_df.to_excel(writer, sheet_name='ממצאים מפורטים', index=False)

            # Sheet 3: Statistics
            stats_df = self._create_statistics_dataframe(results)
            stats_df.to_excel(writer, sheet_name='סטטיסטיקה', index=False)

            # Sheet 4: Amendment 13 Compliance
            compliance_df = self._create_compliance_dataframe(results)
            compliance_df.to_excel(writer, sheet_name='תיקון 13', index=False)

        print(f"✓ דוח נוצר בהצלחה: {output_path}")
        return str(output_path)

    def generate_csv_report(
        self,
        results: Dict[str, Dict],
        output_filename: str = None
    ) -> str:
        """
        Generate CSV report (summary only)

        Args:
            results: Detection results for each file
            output_filename: Custom output filename

        Returns:
            Path to generated report
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"pii_report_{timestamp}.csv"

        output_path = self.output_dir / output_filename

        summary_df = self._create_summary_dataframe(results)
        summary_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"✓ דוח CSV נוצר בהצלחה: {output_path}")
        return str(output_path)

    def _create_summary_dataframe(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """Create summary DataFrame"""
        rows = []

        for filename, result in results.items():
            row = {
                'שם הקובץ': filename,
                'סוג קובץ': result.get('file_type', 'N/A'),
                'סטטוס': result.get('status', 'N/A')
            }

            if 'entities' in result:
                entities = result['entities']

                # Add all Israeli Privacy Law categories
                for cat_key, cat_info in ISRAELI_PRIVACY_CATEGORIES.items():
                    row[cat_info.hebrew_name] = len(entities.get(cat_key, []))

                # Calculate totals
                total_pii = sum(len(entities.get(key, [])) for key in entities.keys())
                special_count = sum(
                    len(entities.get(key, []))
                    for key in entities.keys()
                    if is_special_sensitivity(key)
                )

                row['סה"כ פרטים אישיים'] = total_pii
                row['מידע בעל רגישות מיוחדת'] = special_count

            else:
                # No entities (error or no text)
                for cat_key, cat_info in ISRAELI_PRIVACY_CATEGORIES.items():
                    row[cat_info.hebrew_name] = 0
                row['סה"כ פרטים אישיים'] = 0
                row['מידע בעל רגישות מיוחדת'] = 0

            rows.append(row)

        return pd.DataFrame(rows)

    def _create_details_dataframe(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """Create detailed findings DataFrame"""
        rows = []

        for filename, result in results.items():
            if 'entities' not in result:
                continue

            entities = result['entities']

            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    rows.append({
                        'שם הקובץ': filename,
                        'סוג פרט': get_category_hebrew_name(entity_type),
                        'סוג (אנגלית)': entity_type,
                        'רמת רגישות': 'מיוחדת' if is_special_sensitivity(entity_type) else 'רגילה',
                        'ערך': entity.text,
                        'מיקום (התחלה)': entity.start,
                        'מיקום (סוף)': entity.end,
                        'רמת וודאות': f"{entity.confidence:.2%}"
                    })

        if not rows:
            # Return empty DataFrame with columns
            return pd.DataFrame(columns=[
                'שם הקובץ', 'סוג פרט', 'ערך',
                'מיקום (התחלה)', 'מיקום (סוף)', 'רמת וודאות'
            ])

        return pd.DataFrame(rows)

    def _create_statistics_dataframe(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """Create statistics DataFrame"""

        # Count by entity type across all files
        entity_counts = {}
        total_files = len(results)
        files_with_pii = 0

        for filename, result in results.items():
            if 'entities' not in result:
                continue

            has_pii = False
            entities = result['entities']

            for entity_type, entity_list in entities.items():
                if entity_list:
                    has_pii = True

                if entity_type not in entity_counts:
                    entity_counts[entity_type] = 0

                entity_counts[entity_type] += len(entity_list)

            if has_pii:
                files_with_pii += 1

        # Create stats rows
        rows = []

        rows.append({
            'מדד': 'סה"כ קבצים שנסרקו',
            'ערך': total_files
        })

        rows.append({
            'מדד': 'קבצים עם פרטים אישיים',
            'ערך': files_with_pii
        })

        rows.append({
            'מדד': 'קבצים ללא פרטים אישיים',
            'ערך': total_files - files_with_pii
        })

        rows.append({
            'מדד': '',
            'ערך': ''
        })

        # Add entity type counts
        hebrew_names = {
            'PERSON': 'שמות אנשים',
            'ID_NUMBER': 'תעודות זהות',
            'PHONE': 'מספרי טלפון',
            'EMAIL': 'כתובות אימייל',
            'ADDRESS': 'כתובות',
            'CREDIT_CARD': 'כרטיסי אשראי',
            'BANK_ACCOUNT': 'חשבונות בנק',
            'ORGANIZATION': 'ארגונים',
            'LOCATION': 'מיקומים'
        }

        for entity_type, count in entity_counts.items():
            rows.append({
                'מדד': hebrew_names.get(entity_type, entity_type),
                'ערך': count
            })

        return pd.DataFrame(rows)

    def _create_compliance_dataframe(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Create Amendment 13 compliance report DataFrame
        Shows breakdown by sensitivity level
        """
        rows = []

        # Header
        rows.append({
            'קטגוריה': 'תיקון 13 לחוק הגנת הפרטיות, התשפ"ד-2024',
            'ערך': '',
            'הערות': 'דוח תאימות'
        })

        rows.append({'קטגוריה': '', 'ערך': '', 'הערות': ''})

        # Count standard vs specially sensitive
        standard_total = 0
        special_total = 0

        standard_breakdown = {}
        special_breakdown = {}

        for filename, result in results.items():
            if 'entities' not in result:
                continue

            entities = result['entities']

            for entity_type, entity_list in entities.items():
                count = len(entity_list)
                if count == 0:
                    continue

                if is_special_sensitivity(entity_type):
                    special_total += count
                    if entity_type not in special_breakdown:
                        special_breakdown[entity_type] = 0
                    special_breakdown[entity_type] += count
                else:
                    standard_total += count
                    if entity_type not in standard_breakdown:
                        standard_breakdown[entity_type] = 0
                    standard_breakdown[entity_type] += count

        # Summary
        rows.append({
            'קטגוריה': 'סיכום כללי',
            'ערך': '',
            'הערות': ''
        })

        rows.append({
            'קטגוריה': 'סה"כ פרטים אישיים',
            'ערך': standard_total + special_total,
            'הערות': 'כל הפרטים שזוהו'
        })

        rows.append({
            'קטגוריה': 'פרטים אישיים רגילים',
            'ערך': standard_total,
            'הערות': 'הגנה סטנדרטית'
        })

        rows.append({
            'קטגוריה': 'מידע בעל רגישות מיוחדת',
            'ערך': special_total,
            'הערות': 'סעיף 7(ג) - דורש הגנה מוגברת'
        })

        rows.append({'קטגוריה': '', 'ערך': '', 'הערות': ''})

        # Standard personal information breakdown
        rows.append({
            'קטגוריה': 'פירוט - פרטים אישיים רגילים',
            'ערך': '',
            'הערות': ''
        })

        for entity_type, count in standard_breakdown.items():
            rows.append({
                'קטגוריה': f'  • {get_category_hebrew_name(entity_type)}',
                'ערך': count,
                'הערות': entity_type
            })

        if not standard_breakdown:
            rows.append({
                'קטגוריה': '  (לא נמצאו)',
                'ערך': 0,
                'הערות': ''
            })

        rows.append({'קטגוריה': '', 'ערך': '', 'הערות': ''})

        # Specially sensitive information breakdown
        rows.append({
            'קטגוריה': 'פירוט - מידע בעל רגישות מיוחדת (תיקון 13)',
            'ערך': '',
            'הערות': ''
        })

        special_categories_found = {
            'MEDICAL_INFO': 'מידע רפואי',
            'GENETIC_INFO': 'מידע גנטי',
            'BIOMETRIC_ID': 'מזהה ביומטרי',
            'SEXUAL_ORIENTATION': 'נטייה מינית',
            'POLITICAL_OPINION': 'דעה פוליטית',
            'RELIGIOUS_BELIEF': 'אמונה דתית',
            'CRIMINAL_RECORD': 'עבר פלילי',
            'LOCATION_DATA': 'נתוני מיקום',
            'ETHNIC_ORIGIN': 'מוצא אתני',
            'PERSONALITY_ASSESSMENT': 'הערכת תכונות אישיות',
            'SALARY_FINANCIAL': 'שכר ופעילות כלכלית',
            'CREDIT_CARD': 'כרטיס אשראי',
            'BANK_ACCOUNT': 'חשבון בנק',
            'FAMILY_PRIVACY': 'פרטיות חיי משפחה',
            'CONFIDENTIAL_INFO': 'מידע חסוי מכוח דין'
        }

        for cat_key, cat_name in special_categories_found.items():
            count = special_breakdown.get(cat_key, 0)
            rows.append({
                'קטגוריה': f'  • {cat_name}',
                'ערך': count,
                'הערות': cat_key if count > 0 else ''
            })

        rows.append({'קטגוריה': '', 'ערך': '', 'הערות': ''})

        # Compliance notes
        rows.append({
            'קטגוריה': 'הערות תאימות',
            'ערך': '',
            'הערות': ''
        })

        rows.append({
            'קטגוריה': 'תאריך כניסה לתוקף של התיקון',
            'ערך': '14.8.2025',
            'הערות': 'חוק הגנת הפרטיות (תיקון מס\' 13), התשפ"ד-2024'
        })

        rows.append({
            'קטגוריה': 'אחריות מנהל מאגר',
            'ערך': 'חובה',
            'הערות': 'אבטחת מידע והגנה מוגברת למידע רגיש'
        })

        if special_total > 0:
            rows.append({
                'קטגוריה': 'המלצה',
                'ערך': 'דחוף',
                'הערות': f'נמצאו {special_total} פריטים בעלי רגישות מיוחדת - נדרשת אבטחה מוגברת'
            })

        return pd.DataFrame(rows)

    def generate_text_report(self, results: Dict[str, Dict]) -> str:
        """
        Generate human-readable text report

        Args:
            results: Detection results for each file

        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("דוח זיהוי פרטים אישיים (PII)")
        lines.append("=" * 80)
        lines.append(f"תאריך: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"סה\"כ קבצים: {len(results)}")
        lines.append("")

        for filename, result in results.items():
            lines.append("-" * 80)
            lines.append(f"📄 קובץ: {filename}")
            lines.append(f"   סוג: {result.get('file_type', 'N/A')}")

            if 'entities' in result:
                entities = result['entities']
                total = sum(len(elist) for elist in entities.values())

                lines.append(f"   סה\"כ פרטים אישיים שנמצאו: {total}")
                lines.append("")

                if total > 0:
                    lines.append("   פירוט:")
                    for entity_type, entity_list in entities.items():
                        if entity_list:
                            lines.append(f"   • {entity_type}: {len(entity_list)}")
                            for entity in entity_list[:3]:  # Show first 3
                                lines.append(f"     - {entity.text} (וודאות: {entity.confidence:.0%})")
                            if len(entity_list) > 3:
                                lines.append(f"     ... ועוד {len(entity_list) - 3}")
                else:
                    lines.append("   ✓ לא נמצאו פרטים אישיים")

            else:
                lines.append("   ⚠ שגיאה בעיבוד הקובץ")

            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def save_text_report(
        self,
        results: Dict[str, Dict],
        output_filename: str = None
    ) -> str:
        """
        Save text report to file

        Args:
            results: Detection results
            output_filename: Custom output filename

        Returns:
            Path to saved report
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"pii_report_{timestamp}.txt"

        output_path = self.output_dir / output_filename

        report_text = self.generate_text_report(results)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"✓ דוח טקסט נוצר בהצלחה: {output_path}")
        return str(output_path)
