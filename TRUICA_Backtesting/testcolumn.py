import pandas as pd
def main():
    df = pd.read_csv('gbpusd.csv')
    print(df.columns)
