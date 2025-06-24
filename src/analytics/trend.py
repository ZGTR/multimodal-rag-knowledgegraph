import pandas as pd
from sqlalchemy import create_engine
import umap
import matplotlib.pyplot as plt
from src.config.settings import settings

def load_monthly_centroids():
    engine = create_engine(settings.vectordb_uri)
    query = """
    SELECT date_trunc('month', created_at) AS month,
           AVG(embedding) AS centroid
    FROM content_chunks
    GROUP BY 1
    ORDER BY 1;
    """
    return pd.read_sql_query(query, engine)

def plot_umap(df):
    reducer = umap.UMAP(metric='cosine')
    coords = reducer.fit_transform(list(df['centroid']))
    plt.figure(figsize=(8,6))
    plt.scatter(coords[:,0], coords[:,1])
    for (x,y), label in zip(coords, df['month'].dt.strftime('%Y-%m')):
        plt.text(x, y, label)
    plt.title("Topic drift map")
    plt.show()

if __name__ == "__main__":
    df = load_monthly_centroids()
    plot_umap(df)
