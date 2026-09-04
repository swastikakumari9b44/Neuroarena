from database import Base, engine
from models import TrainingSession, TrainingMetric

TrainingMetric.__table__.drop(engine, checkfirst=True)
TrainingSession.__table__.drop(engine, checkfirst=True)
Base.metadata.create_all(bind=engine)
print("done")