from sqlalchemy import create_engine
from config.utils import DB_URL

engine = create_engine(url=DB_URL)

