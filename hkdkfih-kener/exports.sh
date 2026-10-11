export APP_HKDKFIH_KENER_SECRET_KEY="$(derive_entropy "${app_entropy_identifier}-secret-key")"
export APP_HKDKFIH_KENER_REDIS_PASSWORD="$(derive_entropy "${app_entropy_identifier}-redis-password")"
