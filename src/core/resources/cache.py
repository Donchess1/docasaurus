import json
import os

import redis
from django.conf import settings

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")


class Cache:
    """
    A singleton class that provides an interface to interact with a Redis cache.

    This class manages Redis connections based on the environment (development or production)
    and provides common cache operations like setting, getting, deleting, and managing expiry.

    The class implements a singleton pattern, ensuring that only one Redis connection is maintained
    throughout the lifetime of the application, reducing unnecessary overhead from multiple connections.

    Attributes:
    -----------
    _instance : Cache
        Singleton instance of the Cache class, used to manage a single Redis connection.
    _redis : redis.Redis
        Redis client instance for interacting with the Redis server.

    Methods:
    --------
    set(key, value, ttl=3600):
        Set a value in the Redis cache for a given key with an optional time-to-live (TTL).

    get(key):
        Retrieve the value associated with a given key from the Redis cache.

    delete(key):
        Delete a key-value pair from the Redis cache.

    flush():
        Flush (clear) the entire Redis database.

    expiry_time(key):
        Get the remaining time-to-live (TTL) for a given key in seconds.

    set_expiry(key, ttl):
        Set or update the expiration time for a given key in the cache.

    Usage:
    ------
    # Creating or retrieving the singleton Cache instance
    cache = Cache()

    # Storing a value in the cache
    cache.set("banks", ["Bank A", "Bank B"])

    # Retrieving a value from the cache
    banks = cache.get("banks")

    # Deleting a value from the cache
    cache.delete("banks")

    # Flushing the entire cache
    cache.flush()

    Notes:
    ------
    - The class automatically selects the appropriate Redis connection configuration based on the
      environment (`ENVIRONMENT` variable).
    - In development, it connects to a local Redis instance, while in staging/production, it connects using
      credentials from the application settings.
    - This class should be used with context management (`with` statement) to ensure connections are
      closed properly.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Cache, cls).__new__(cls)
            msg = f"REDIS-{ENVIRONMENT.upper()} INSTANTIATED"
            print("===================================================")
            print(msg)
            print("===================================================")
            cls._instance._redis = redis.Redis(
                host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0
            )
            # cls._instance._redis = redis.Redis(
            #     host=settings.REDIS_HOST,
            #     port=settings.REDIS_PORT,
            #     password=settings.REDIS_PASSWORD,
            #     db=0,
            # )
            # cls._instance._redis = redis.StrictRedis(
            #     host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0
            # )
            # cls._instance._redis = redis.StrictRedis(
            #     host=settings.REDIS_HOST,
            #     port=settings.REDIS_PORT,
            #     password=settings.REDIS_PASSWORD,
            #     db=0,
            #     ssl=True,
            #     ssl_cert_reqs=None,
            #     decode_responses=True
            # )
        return cls._instance

    def set(self, key, value, ttl=3600):
        value = json.dumps(value)
        self._redis.set(key, value, ex=ttl)

    def get(self, key):
        data = self._redis.get(key)
        return json.loads(data) if data else None

    def delete(self, key):
        self._redis.delete(key)

    def flush(self):
        self._redis.flushdb()

    def expiry_time(self, key):
        return self._redis.ttl(key)

    def set_expiry(self, key, ttl):
        self._redis.expire(key, ttl)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._redis.connection_pool.disconnect()

    def __del__(self):
        self._redis.connection_pool.disconnect()
