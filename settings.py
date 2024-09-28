# settings.py

import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key')
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_FILE = os.getenv('LOG_FILE', 'C:/Users/Aneesh S/OneDrive/Desktop/Sen-Net/SenNet/SenNet.log')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///development.db')

class ProductionConfig(Config):
    """Production configuration."""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///production.db')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///testing.db')
