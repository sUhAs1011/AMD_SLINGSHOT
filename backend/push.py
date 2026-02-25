import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv(r'C:\Users\NITRO\OneDrive\Desktop\Kalpana_Mental_Health\Datasets\harm_train.csv')
engine = create_engine('postgresql://postgres:root123@localhost:5432/postgres')

df.to_sql('harm_train', engine, index = False, if_exists = 'replace')