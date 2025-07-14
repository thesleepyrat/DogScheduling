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
            # Read all sheets as dict of DataFrames
            all_sheets = pd.read_excel(file, sheet_name=None)
        except Exception:
            return render_template("index.html", error="Error reading Excel file. Please upload a valid XLSX.")

        processed_sheets = {}

        for sheet_name, df in all_sheets.items():
            processed_df = space_runs_min_gap_hard(df)
            if processed_df is None:
                return render_template("index.html", error=f"Scheduling failed for sheet '{sheet_name}'.")
            processed_sheets[sheet_name] = processed_df

        # Save processed sheets to a temporary XLSX file
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "processed_schedule.xlsx")

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in processed_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=True)

        return send_file(
            output_path,
            as_attachment=True,
            download_name="processed_schedule.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
