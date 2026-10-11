# Semaphore reads these keys as base64. Hex characters are valid base64: 64 of them decode to a
# 48-byte HMAC key, 32 of them to a 24-byte AES-192 key (Semaphore accepts 16, 24 or 32 bytes).
export APP_HKDKFIH_SEMAPHORE_COOKIE_HASH="$(derive_entropy "${app_entropy_identifier}-cookie-hash")"
export APP_HKDKFIH_SEMAPHORE_COOKIE_ENCRYPTION="$(derive_entropy "${app_entropy_identifier}-cookie-encryption")"
export APP_HKDKFIH_SEMAPHORE_COOKIE_ENCRYPTION="${APP_HKDKFIH_SEMAPHORE_COOKIE_ENCRYPTION:0:32}"
export APP_HKDKFIH_SEMAPHORE_ACCESS_KEY_ENCRYPTION="$(derive_entropy "${app_entropy_identifier}-access-key-encryption")"
export APP_HKDKFIH_SEMAPHORE_ACCESS_KEY_ENCRYPTION="${APP_HKDKFIH_SEMAPHORE_ACCESS_KEY_ENCRYPTION:0:32}"
