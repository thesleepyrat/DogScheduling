from flask import Flask, request, render_template, send_file
import pandas as pd
import os
import tempfile
from scheduler import space_runs_min_gap_hard, find_max_feasible_gap

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

        max_gap_setting = 8  # maximum gap to try (adjust if you want)
        time_limit_per_try = 10  # seconds for binary search tries

        for sheet_name, df in all_sheets.items():
            try:
                max_gap = find_max_feasible_gap(df, max_gap=max_gap_setting, min_gap=1, time_limit=time_limit_per_try)
                print(f"Using min_gap={max_gap} for sheet {sheet_name}")
                processed_df = space_runs_min_gap_hard(df, min_gap=max_gap)
                if processed_df is None:
                    failed_sheets.append(sheet_name)
                else:
                    processed_sheets[sheet_name] = processed_df
            except Exception as e:
                print(f"Error processing sheet '{sheet_name}': {e}")
                failed_sheets.append(sheet_name)

        if not processed_sheets:
            return render_template("index.html", error="Scheduling failed for all sheets. Try adjusting your data or settings.")

        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "processed_schedule.xlsx")

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in processed_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=True)

        msg = None
        if failed_sheets:
            msg = f"Scheduling failed for sheets: {', '.join(failed_sheets)}. Other sheets processed successfully."

        # Pass the message to your template if you want (not shown here)
        # Or just return file directly
        return send_file(
            output_path,
            as_attachment=True,
            download_name="processed_schedule.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
