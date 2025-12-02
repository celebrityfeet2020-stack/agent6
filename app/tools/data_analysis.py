"""Data Analysis Tool - Pandas + Matplotlib"""
from langchain_core.tools import BaseTool
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

class DataAnalysisTool(BaseTool):
    name: str = "data_analysis"
    description: str = """Analyze data and create visualizations.
    Input format: operation|data_path|params
    Operations: summary, plot, query
    Example: summary|/tmp/data.csv or plot|/tmp/data.csv|column_name"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|')
            operation = parts[0].strip()
            data_path = parts[1].strip()
            params = parts[2].strip() if len(parts) > 2 else None
            
            df = pd.read_csv(data_path)
            
            if operation == "summary":
                return str(df.describe())
            elif operation == "plot":
                plt.figure(figsize=(10, 6))
                df[params].plot()
                plt.savefig('/tmp/plot.png')
                return f"Plot saved to /tmp/plot.png"
            elif operation == "query":
                result = df.query(params)
                return str(result)
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            return f"Data Analysis Error: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
