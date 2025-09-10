import pandas as pd
from src.schedule_utils import df_to_date_then_studio_html_with_filters
try:
    df = pd.read_csv("data/classes.csv")
except FileNotFoundError:
    # Minimal fallback example so the site builds the first time:
    print("No Data Found.")

# 2) Build your HTML into public/index.html
df_to_date_then_studio_html_with_filters(df, "public/index.html")
print("Built public/index.html")
