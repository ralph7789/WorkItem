with open("style_classic.qss", "r") as f:
    content = f.read()

# Replace harsh black with modern dark gray and border radius
content = content.replace("background-color: #0f172a;", "background-color: #1E1E24;")
content = content.replace("background-color: #1e293b;", "background-color: #2B2B36;")
content = content.replace("QListView#workitem_list::item {", "QListView#workitem_list::item {\n    border-radius: 8px;\n    border: 1px solid #3F3F46;")
content = content.replace("background-color: #334155;", "background-color: #373742;")
content = content.replace("color: #38bdf8;", "color: #6366F1;")

with open("style_classic.qss", "w") as f:
    f.write(content)
