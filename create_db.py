from backend.app.database import Base, engine
from backend.app import models

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done.")