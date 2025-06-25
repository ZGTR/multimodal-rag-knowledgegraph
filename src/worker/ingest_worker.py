import argparse
from src.rag.vector_store import get_vectorstore
from src.kg.gremlin_client import GremlinKG
from src.bootstrap.logger import get_logger
from src.worker.strategies.youtube import YouTubeIngestStrategy
# from src.worker.strategies.twitter import TwitterIngestStrategy
# from src.worker.strategies.instagram import InstagramIngestStrategy

logger = get_logger("ingest_worker")

STRATEGY_REGISTRY = {
    'youtube': YouTubeIngestStrategy,
    # 'twitter': TwitterIngestStrategy,
    # 'instagram': InstagramIngestStrategy,
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", nargs="*", help="YouTube video IDs or URLs")
    parser.add_argument("--twitter", nargs="*", help="Twitter query terms")
    parser.add_argument("--ig", nargs="*", help="Instagram post URLs")
    args = parser.parse_args()

    vectordb = get_vectorstore()
    kg = GremlinKG()

    if args.videos:
        logger.info("[JOB] YouTube ingestion started")
        strategy = STRATEGY_REGISTRY['youtube'](vectordb=vectordb, kg=kg)
        strategy.ingest(args.videos)
        logger.info("[JOB] YouTube ingestion finished")

    # if args.twitter:
    #     logger.info("[JOB] Twitter ingestion started")
    #     strategy = STRATEGY_REGISTRY['twitter'](vectordb=vectordb, kg=kg)
    #     strategy.ingest(args.twitter)
    #     logger.info("[JOB] Twitter ingestion finished")

    # if args.ig:
    #     logger.info("[JOB] Instagram ingestion started")
    #     strategy = STRATEGY_REGISTRY['instagram'](vectordb=vectordb, kg=kg)
    #     strategy.ingest(args.ig)
    #     logger.info("[JOB] Instagram ingestion finished")

    logger.info("[JOB] IngestWorker finished successfully")

if __name__ == "__main__":
    main()
