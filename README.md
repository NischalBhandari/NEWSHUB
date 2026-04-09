### RUN a module ###

```
python -m scraper.nepsealpha_com
```


### For Database ###

we are using alembic

```
pip install alembic

alembic init alembic


2. Configure DB URL in:
alembic.ini

from your_model_file import Base
target_metadata = Base.metadata


```


```
python run_pipeline.py	Full scrape + analyze
python run_pipeline.py --no-kathmandu	Skip Kathmandu Post (fetches every article individually, slow)
python run_pipeline.py --scrape-only	No analysis
python run_pipeline.py --analyze-only	Re-run analysis on existing data


```