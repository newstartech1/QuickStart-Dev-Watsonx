import os
import pandas as pd
from flask import Flask, request, jsonify, render_template_string
from ibm_watsonx_ai.foundation_models import Model

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs('uploads', exist_ok=True)

# --- CONFIGURATION ---
API_KEY = "IBM API KEY"  # <--- Paste your API Key
PROJECT_ID = "PROJECT ID"  # <--- Paste your Project ID
# ---------------------

def get_watsonx_insight(summary):
    try:
        credentials = {
            "url": "https://us-south.ml.cloud.ibm.com", 
            "apikey": API_KEY
        }
        model = Model(
            model_id="ibm/granite-3-8b-instruct",
            credentials=credentials,
            project_id=PROJECT_ID,
            params={"max_new_tokens": 100}
        )
        prompt = f"System: You are a data expert. Analyze these CSV stats and give one brief, helpful tip. Data: {summary}"
        return model.generate_text(prompt=prompt)
    except Exception as e:
        return f"Insight: CSV parsed successfully. Rows: {summary.split(',')[0]}"

HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>QuickStart Dev | Watsonx AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white font-sans p-10">
    <div class="max-w-2xl mx-auto bg-slate-800 p-8 rounded-2xl shadow-2xl border border-slate-700">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-blue-400">QuickStart Dev</h1>
            <span class="bg-blue-900 text-blue-200 text-xs px-2 py-1 rounded">Watsonx.ai Powered</span>
        </div>
        
        <form id="uForm" class="space-y-4">
            <label class="block text-slate-400 text-sm">Upload CSV Data Agent</label>
            <input type="file" id="csvFile" accept=".csv" 
                   class="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-blue-600 file:text-white cursor-pointer">
            <button type="submit" id="btn" class="w-full bg-blue-600 hover:bg-blue-500 py-3 rounded-xl font-bold transition">Analyze & Get AI Insight</button>
        </form>

        <div id="res" class="hidden mt-8 space-y-4">
            <div class="p-4 bg-slate-900 rounded-lg border border-slate-700">
                <h2 class="text-green-400 font-bold mb-1">QuickStats</h2>
                <div id="out" class="text-slate-300"></div>
            </div>
            <div class="p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
                <h2 class="text-blue-400 font-bold mb-1">Watsonx.ai Analysis</h2>
                <p id="ai_out" class="text-slate-200 italic"></p>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('uForm').onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn');
            const fileInput = document.getElementById('csvFile');
            if(!fileInput.files[0]) return;
            
            btn.innerText = "Processing with Granite AI...";
            btn.disabled = true;

            const fd = new FormData();
            fd.append('file', fileInput.files[0]);
            
            const resp = await fetch('/upload', { method: 'POST', body: fd });
            const data = await resp.json();
            
            document.getElementById('res').classList.remove('hidden');
            document.getElementById('out').innerText = `Rows: ${data.rows} | Duplicates Found: ${data.duplicates}`;
            document.getElementById('ai_out').innerText = data.ai_insight;
            
            btn.innerText = "Analyze & Get AI Insight";
            btn.disabled = false;
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file and file.filename:
        # Fixed path handling for Windows
        folder = "uploads"
        filepath = os.path.join(folder, file.filename)
        file.save(filepath)
        
        df = pd.read_csv(filepath)
        summary = f"Rows: {len(df)}, Duplicates: {df.duplicated().sum()}, Columns: {list(df.columns)}"
        
        # Call Watsonx
        insight = get_watsonx_insight(summary)
        
        return jsonify({
            "rows": len(df),
            "duplicates": int(df.duplicated().sum()),
            "ai_insight": insight
        })
    return jsonify({"error": "No file uploaded"}), 400

if __name__ == '__main__':
    app.run(debug=True)
