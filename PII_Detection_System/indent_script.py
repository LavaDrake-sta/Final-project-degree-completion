import sys

file_path = r'c:\Users\adist\Documents\GitHub\Final-project-degree-completion\PII_Detection_System\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i in range(71): # lines 0-70
    new_lines.append(lines[i])

new_lines.append('st.sidebar.header("⚙️ הגדרות חומרה (מנוע זיהוי)")\n')
new_lines.append('compute_mode = st.sidebar.radio(\n')
new_lines.append('    "בחר את סוג המחשב שלך:",\n')
new_lines.append('    ["💻 מחשב רגיל/ישן (מערכת בסיסית ומהירה)", "🚀 מחשב חדש/חזק (מערכת AI חכמה)"]\n')
new_lines.append(')\n\n')
new_lines.append('st.write("---")\n\n')

new_lines.append('if "מחשב רגיל" in compute_mode:\n')
new_lines.append('    st.info("מופעל מצב ביצועים קלים: חיפוש מהיר המבוסס על תבניות (ללא AI כבד).")\n')
new_lines.append('    tab1, tab2, tab3 = st.tabs(["📝 טקסט", "🖼️ תמונה", "📄 PDF"])\n\n')

# lines 74 to 194 is basic tabs (index 74 is with tab1)
for i in range(74, 195):
    new_lines.append('    ' + lines[i])

new_lines.append('\nelse:\n')
new_lines.append('    st.info("מופעל מצב ביצועים גבוהים: מנוע AI מתקדם מופעל לצורך ניתוח עמוק.")\n')
new_lines.append('    tab4, = st.tabs(["🤖 AI Pipeline (Presidio)"])\n\n')

# lines 195 to 263 is AI tab (index 195 is # טאב AI Pipeline)
for i in range(195, 263):
    new_lines.append('    ' + lines[i])

# lines 263 to end
for i in range(263, len(lines)):
    new_lines.append(lines[i])

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('File successfully updated!')
