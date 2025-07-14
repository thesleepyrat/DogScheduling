from flask import Flask, request, render_template, send_file
import pandas as pd
import os
import tempfile
from scheduler import space_runs_min_gap_hard

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return render_template("index.html", error="Please upload a file.")

        try:
            all_sheets = pd.read_excel(file, sheet_name=None)
        except Exception:
            return render_template("index.html", error="Error reading Excel file. Please upload a valid XLSX.")

        processed_sheets = {}
        failed_sheets = []

        min_gap = 8  # You can change this or add an input field in the form if you want

        for sheet_name, df in all_sheets.items():
            try:
                processed_df = space_runs_min_gap_hard(df, min_gap=min_gap)
                if processed_df is None:
                    failed_sheets.append(sheet_name)
                else:
                    processed_sheets[sheet_name] = processed_df
            except Exception as e:
                print(f"Error processing sheet '{sheet_name}': {e}")
                failed_sheets.append(sheet_name)

        if not processed_sheets:
            return render_template("index.html", error="Scheduling failed for all sheets. Try adjusting min_gap or check your data.")

        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "processed_schedule.xlsx")

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in processed_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=True)

        msg = None
        if failed_sheets:
            msg = f"Scheduling failed for sheets: {', '.join(failed_sheets)}. Other sheets processed successfully."

        return send_file(
            output_path,
            as_attachment=True,
            download_name="processed_schedule.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return render_template("index.html")
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
