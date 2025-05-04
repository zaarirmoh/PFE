import pandas as pd
df = pd.read_excel("/home/walid-bench/Downloads/2SC bilan annuel IASD VF 2022-2023.xls")
print(df.columns.tolist())

print(df.head(10))
