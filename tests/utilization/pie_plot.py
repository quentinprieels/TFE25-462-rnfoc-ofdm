import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib as mpl

import sys
sys.path.append('/usr/local/lib/python3.10/site-packages')  # Make sure pyfunctionthon find the rfnoc_ofdm package

from rfnoc_ofdm.plotting import colors, classical, use_latex

new_colors = [colors["line7"], colors["line2"], colors["line3"], colors["line4"], colors["line5"], colors["line6"], colors["line1"]]

results_file = "block_resource.csv"
df = pd.read_csv(results_file)

def create_pie_chart(data: pd.DataFrame, level: int, column: str, exclude: list[str] = None) -> None:
    # Filder the data by level
    filtered_data = data[data['level'] == level]
    
    # Apply the exclude list if provided
    if exclude is not None:
        filtered_data = filtered_data[~filtered_data['module'].isin(exclude)]
    
    # Check that thre are data
    if filtered_data.empty:
        print(f"No data found for level {level} with the given exclude list.")
        return
    
    # Sort the data for visualization
    filtered_data = filtered_data.sort_values(by=column, ascending=False)
    
    # Extract the data and labels
    values = filtered_data[column].values
    labels = filtered_data['module'].values
    
    # Aggregate the data if they are taken less than 5%
    total = np.sum(values)
    threshold = 0.04
    
    small_indices =[i for i, value in enumerate(values) if value / total < threshold]
    if len(small_indices) > 3:
        # Group small slices into "Others"
        mask = np.ones(len(values), dtype=bool)
        mask[small_indices] = False
        
        # Keep main slices
        main_values = values[mask]
        main_labels = labels[mask]
        
        # Create "Others" slice
        others_value = values[~mask].sum()
        
        # Combine main slices and "Others"
        plot_values = np.append(main_values, others_value)
        plot_labels = np.append(main_labels, ["Others"])
    else:
        plot_values = values
        plot_labels = labels
    
    
    # Create the pie chart
    plt.figure(figsize=classical)
    use_latex()
    plt.pie(plot_values, autopct='%1.1f%%', startangle=90, colors=new_colors, labels=None)
    # plt.axis('equal')
   
   
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, facecolor=new_colors[i % len(new_colors)], label=plot_labels[i])
        for i in range(len(plot_labels))
    ]
    plt.legend(handles=legend_elements, loc='upper center', 
               bbox_to_anchor=(0.5, 0), ncol=min(2, len(plot_labels)), frameon=False)
    plt.tight_layout()
    

create_pie_chart(df, level=0, column='Total LUTs', exclude=['Stream endpoint 0', 'Stream endpoint 1', "RFNoC bloc DDC", "RFNoC bloc DUC", "RFNoC bloc Radio"])
plt.savefig("level_0_rfnoc.pdf", bbox_inches='tight')
plt.close()

create_pie_chart(df, level=1, column='Total LUTs')
plt.savefig("level_1_rfnoc_schmidl_cox.pdf", bbox_inches='tight')
plt.close()

create_pie_chart(df, level=2, column='Total LUTs')
plt.savefig("level_2_metric_calculator.pdf", bbox_inches='tight')
plt.close()