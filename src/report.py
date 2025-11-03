"""
Report Generator Module
Creates detailed reports of PII detection results
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from .pii_detector import PIIEntity


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
                row.update({
                    'שמות אנשים': len(entities.get('PERSON', [])),
                    'תעודות זהות': len(entities.get('ID_NUMBER', [])),
                    'טלפונים': len(entities.get('PHONE', [])),
                    'אימיילים': len(entities.get('EMAIL', [])),
                    'כתובות': len(entities.get('ADDRESS', [])),
                    'כרטיסי אשראי': len(entities.get('CREDIT_CARD', [])),
                    'חשבונות בנק': len(entities.get('BANK_ACCOUNT', [])),
                    'ארגונים': len(entities.get('ORGANIZATION', [])),
                    'מיקומים': len(entities.get('LOCATION', []))
                })

                total_pii = sum(
                    len(entities.get(key, []))
                    for key in entities.keys()
                )
                row['סה"כ פרטים אישיים'] = total_pii

            else:
                # No entities (error or no text)
                row.update({
                    'שמות אנשים': 0,
                    'תעודות זהות': 0,
                    'טלפונים': 0,
                    'אימיילים': 0,
                    'כתובות': 0,
                    'כרטיסי אשראי': 0,
                    'חשבונות בנק': 0,
                    'ארגונים': 0,
                    'מיקומים': 0,
                    'סה"כ פרטים אישיים': 0
                })

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
                        'סוג פרט': entity_type,
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
