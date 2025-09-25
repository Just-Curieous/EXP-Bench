import pandas as pd

df = pd.read_csv('exp_bench_test_modified.csv')
print('Total rows:', len(df))
print('Rows with github_url:', (df['github_url'].notna() & (df['github_url'] != '')).sum())
print('Rows with pdf_url:', (df['pdf_url'].notna() & (df['pdf_url'] != '')).sum())
print('Rows with design:', df['design'].notna().sum())

print('\nMissing github_url rows:')
missing_github = df[df['github_url'].isna() | (df['github_url'] == '')]
if not missing_github.empty:
    print(missing_github[['conference', 'paper_id', 'paper_title']].head())
else:
    print("None")

print('\nMissing pdf_url rows:')
missing_pdf = df[df['pdf_url'].isna() | (df['pdf_url'] == '')]
if not missing_pdf.empty:
    print(missing_pdf[['conference', 'paper_id', 'paper_title']].head())
else:
    print("None")