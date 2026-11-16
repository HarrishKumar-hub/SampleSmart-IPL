"""
export_tables.py — Export formatted Excel workbook and image table.

Exports comparison_table.xlsx and comparison_table.png for presentations/reports.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
import config

def export_formatted_outputs():
    csv_path = f"{config.TABLES_DIR}/comparison_table.csv"
    if not os.path.exists(csv_path):
        print("Comparison table CSV not found. Run run_all.py first.")
        return

    df = pd.read_csv(csv_path)

    # 1. Export Excel with openpyxl
    xlsx_path = f"{config.TABLES_DIR}/comparison_table.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Comparison", index=False)
        
        # Also write simulation summary if exists
        sim_path = f"{config.TABLES_DIR}/simulation_summary.csv"
        if os.path.exists(sim_path):
            pd.read_csv(sim_path).to_excel(writer, sheet_name="Simulation 500 Reps", index=False)
            
        # Also write tests if exists
        tests_path = f"{config.TABLES_DIR}/statistical_tests.csv"
        if os.path.exists(tests_path):
            pd.read_csv(tests_path).to_excel(writer, sheet_name="Statistical Tests", index=False)

    print(f"✅ Formatted Excel workbook saved → {xlsx_path}")

    # 2. Export table as a clean publication-quality PNG image
    display_df = df[["design", "n", "mean", "se_mean", "ci_lower", "ci_upper", "proportion", "RE_vs_SRS", "abs_error_mean"]].copy()
    display_df.columns = ["Design", "n", "Mean", "SE(Mean)", "95% CI Lower", "95% CI Upper", "Prop ≥ 30", "RE vs SRS", "Abs Error"]
    
    # Format columns for display
    display_df["Mean"] = display_df["Mean"].map(lambda x: f"{x:.2f}")
    display_df["SE(Mean)"] = display_df["SE(Mean)"].map(lambda x: f"{x:.4f}")
    display_df["95% CI Lower"] = display_df["95% CI Lower"].map(lambda x: f"{x:.2f}")
    display_df["95% CI Upper"] = display_df["95% CI Upper"].map(lambda x: f"{x:.2f}")
    display_df["Prop ≥ 30"] = display_df["Prop ≥ 30"].map(lambda x: f"{x:.4f}")
    display_df["RE vs SRS"] = display_df["RE vs SRS"].map(lambda x: f"{x:.4f}")
    display_df["Abs Error"] = display_df["Abs Error"].map(lambda x: f"{x:.4f}")

    fig, ax = plt.subplots(figsize=(12, 3.2), dpi=config.FIG_DPI)
    ax.axis('off')
    ax.axis('tight')

    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc='center',
        loc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.6)

    # Style header and rows
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_facecolor('#264653')
            cell.set_text_props(color='white', weight='bold')
        else:
            if i % 2 == 0:
                cell.set_facecolor('#F8F9FA')
            else:
                cell.set_facecolor('#FFFFFF')
                
    img_path = f"{config.FIGURES_DIR}/comparison_table.png"
    plt.tight_layout()
    fig.savefig(img_path, bbox_inches='tight', dpi=config.FIG_DPI)
    plt.close(fig)
    print(f"✅ Comparison table image saved → {img_path}")

if __name__ == "__main__":
    export_formatted_outputs()
