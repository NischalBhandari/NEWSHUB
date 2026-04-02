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