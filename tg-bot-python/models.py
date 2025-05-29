from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker


# === Подключение к MySQL ===
db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME", "mfc_bot")

DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(DATABASE_URL, echo=False)

Base = declarative_base()
Session = sessionmaker(bind=engine)


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())

    appointments = relationship("Appointment", back_populates="user")

    @classmethod
    def get_by_telegram_id(cls, telegram_id):
        session = Session()
        try:
            user = session.query(cls).filter_by(telegram_id=telegram_id).first()
            return user
        finally:
            session.close()

    @classmethod
    def get_or_create(cls, telegram_id, username=None, first_name=None):
        session = Session()
        try:
            user = session.query(cls).filter_by(telegram_id=telegram_id).first()

            if not user:
                user = cls(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name
                )
                session.add(user)
                session.commit()
                session.refresh(user)

            return user
        finally:
            session.close()


class Appointment(Base):
    """Модель записи на прием"""
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    branch_id = Column(Integer, nullable=False)
    service_id = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)
    reminder_minutes = Column(Integer, nullable=False)
    status = Column(String(50), default='active')  # 'active', 'cancelled', 'completed'
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="appointments")

    @classmethod
    def get_active_by_user(cls, user_id):
        session = Session()
        try:
            now = datetime.now()
            appointment = session.query(cls).filter(
                cls.user_id == user_id,
                cls.status == 'active',
                cls.datetime > now
            ).first()
            return appointment
        finally:
            session.close()

    @classmethod
    def create(cls, user_id, branch_id, service_id, datetime, reminder_minutes, status='active'):
        session = Session()
        try:
            appointment = cls(
                user_id=user_id,
                branch_id=branch_id,
                service_id=service_id,
                datetime=datetime,
                reminder_minutes=reminder_minutes,
                status=status
            )
            session.add(appointment)
            session.commit()
            session.refresh(appointment)
            return appointment
        finally:
            session.close()

    def update_status(self, new_status):
        session = Session()
        try:
            appointment = session.query(Appointment).filter_by(id=self.id).first()
            if appointment:
                appointment.status = new_status
                session.commit()
                self.status = new_status
        finally:
            session.close()


def init_db():
    """Инициализация базы данных (создание таблиц)"""
    try:
        Base.metadata.create_all(engine)
        print("✅ База данных успешно инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        raise